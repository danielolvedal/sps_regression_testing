from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from multiprocessing.connection import Client, Listener
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_DIR = REPO_ROOT / "runtime"
TEST_DIR = REPO_ROOT / "testing" / "regression_test"
REPORTS_DIR = REPO_ROOT / "test_reports"
QUEUE_DIR = REPO_ROOT / "tmp" / "copilot_admin_queue"
LOG_DIR = REPO_ROOT / "tmp" / "copilot_admin_runner_logs"
STATE_DIR = Path(os.environ.get("COPILOT_ADMIN_RUNNER_STATE_DIR", REPO_ROOT / "tmp" / "copilot_admin_runner_state")).resolve()
CATALOG_PATH = TEST_DIR / "regression-test-catalog.md"
GRAPH_PATH = TEST_DIR / "regression-test-dependencies.mmd"
NODE_PTY_STATE_PATH = STATE_DIR / "node-pty-copilot-session.json"
NODE_PTY_WINDOW_STATE_PATH = STATE_DIR / "node-pty-copilot-window.json"
NODE_PTY_INPUT_QUEUE_DIR = STATE_DIR / "node-pty-copilot-input-queue"
BROWSER_STATE_PATH = STATE_DIR / "collaborative-browser-session.json"
NODE_PTY_START_WINDOW_SCRIPT = (
    RUNTIME_DIR / "windows" / "copilot-admin" / "node-pty" / "start-copilot-admin-node-pty-window.ps1"
)
NODE_PTY_SEND_INPUT_SCRIPT = (
    RUNTIME_DIR / "windows" / "copilot-admin" / "node-pty" / "send-copilot-admin-node-pty-input.ps1"
)
START_BROWSER_SCRIPT = RUNTIME_DIR / "start-collaborative-stage-browser.ps1"
BRIDGE_CHOICES = ("http-api", "file-queue", "named-pipe")

COMMAND_TEMPLATES = {
    "run-regression-all": {
        "label": "Kor regressionstest",
        "template": "kor regressionstest",
        "mode": "Regression Mode",
        "arguments": [],
    },
    "run-regression-by-key": {
        "label": "Kor regressionstest per catalog key",
        "template": "kor regressionstest {catalog_key}",
        "mode": "Regression Mode",
        "arguments": ["catalog_key"],
    },
    "enter-learning-mode": {
        "label": "Ga in i Learning Mode",
        "template": "ga in i learning mode for regressionstest {catalog_key}",
        "mode": "Learning Mode",
        "arguments": ["catalog_key"],
    },
    "update-regression-test": {
        "label": "Uppdatera regressionstest",
        "template": "uppdatera regressionstest {catalog_key}",
        "mode": "Learning Mode",
        "arguments": ["catalog_key"],
    },
    "verify-bridge-session": {
        "label": "Verifiera samma Copilot-session",
        "template": (
            "Verifiera Copilot-admin bridge-session {verification_id}: skapa katalogen "
            "tmp\\copilot_admin_bridge_verification om den saknas och skriv filen "
            "tmp\\copilot_admin_bridge_verification\\{verification_id}.json med timestamp, "
            "verification_id, repository root som du ser den, current working directory och texten "
            "'same Copilot CLI session received bridge command'. Andra inga andra filer."
        ),
        "mode": "Bridge Verification",
        "arguments": ["verification_id"],
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def to_rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("/", "\\")


def log_path(log_dir: Path = LOG_DIR) -> Path:
    return log_dir / f"runner-{datetime.now(timezone.utc).strftime('%Y%m%d')}.jsonl"


def log_event(
    event: str,
    bridge: str,
    details: dict[str, Any] | None = None,
    log_dir: Path = LOG_DIR,
    level: str = "info",
    trace_id: str | None = None,
    session_id: str | None = None,
    job_id: str | None = None,
    status: str | None = None,
) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    safe_details = details or {}
    record = {
        "timestamp": utc_now(),
        "level": level,
        "component": "host-runner",
        "event_id": uuid.uuid4().hex,
        "event": event,
        "trace_id": trace_id or safe_details.get("trace_id"),
        "session_id": session_id or safe_details.get("session_id"),
        "job_id": job_id or safe_details.get("job_id"),
        "status": status or safe_details.get("status"),
        "bridge": bridge,
        "pid": os.getpid(),
        "repo_root": str(REPO_ROOT),
        "details": safe_details,
    }
    with log_path(log_dir).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def request_summary(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "action": request.get("action"),
        "command_id": request.get("command_id"),
        "catalog_key": request.get("catalog_key"),
        "verification_id": request.get("verification_id"),
    }


def response_summary(payload: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {"keys": sorted(payload.keys())}
    if "regression_catalog" in payload:
        summary["regression_catalog_count"] = len(payload["regression_catalog"])
    if "latest_report" in payload and payload["latest_report"]:
        summary["latest_report_run_id"] = payload["latest_report"].get("run_id")
        summary["latest_report_test_count"] = len(payload["latest_report"].get("tests", []))
    if "mermaid" in payload:
        summary["mermaid_length"] = len(payload["mermaid"])
    if "commands" in payload:
        summary["command_count"] = len(payload["commands"])
    if "command_id" in payload:
        summary["command_id"] = payload.get("command_id")
        summary["catalog_key"] = payload.get("catalog_key")
        summary["verification_id"] = payload.get("verification_id")
        summary["mode"] = payload.get("mode")
    if "status" in payload:
        summary["status"] = payload.get("status")
    if "error" in payload:
        summary["error"] = payload.get("error")
    return summary


def split_markdown_row(line: str) -> list[str]:
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|"):
        text = text[:-1]

    cells: list[str] = []
    buffer: list[str] = []
    in_code = False
    for char in text:
        if char == "`":
            in_code = not in_code
            buffer.append(char)
            continue
        if char == "|" and not in_code:
            cells.append("".join(buffer).strip())
            buffer = []
            continue
        buffer.append(char)
    cells.append("".join(buffer).strip())
    return cells


def parse_catalog() -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    text = CATALOG_PATH.read_text(encoding="utf-8")
    for line in text.splitlines():
        if not line.startswith("| `"):
            continue
        cells = split_markdown_row(line)
        if len(cells) != 5:
            continue
        entries.append(
            {
                "catalog_key": cells[0].strip("`"),
                "dependency": cells[1].strip("`"),
                "test_id": cells[2].strip("`"),
                "summary": cells[3],
                "file": cells[4].strip("`"),
            }
        )
    return entries


def list_runtime_scripts() -> list[str]:
    return sorted(
        [path.name for path in RUNTIME_DIR.glob("*.ps1")],
        key=str.casefold,
    )


def read_json_file(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {
            "status": "unreadable",
            "path": str(path),
            "error": "Invalid JSON.",
        }


def is_process_running(pid: Any) -> bool:
    try:
        process_id = int(pid)
    except (TypeError, ValueError):
        return False
    if process_id <= 0:
        return False
    if os.name == "nt":
        completed = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                f"if (Get-Process -Id {process_id} -ErrorAction SilentlyContinue) {{ exit 0 }} else {{ exit 1 }}",
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return completed.returncode == 0
    try:
        os.kill(process_id, 0)
        return True
    except OSError:
        return False


def stop_process(pid: Any, timeout_seconds: int = 30) -> bool:
    try:
        process_id = int(pid)
    except (TypeError, ValueError):
        return True
    if process_id <= 0 or not is_process_running(process_id):
        return True
    if os.name == "nt":
        subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                f"Stop-Process -Id {process_id} -Force -ErrorAction SilentlyContinue",
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    else:
        os.kill(process_id, signal.SIGTERM)
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if not is_process_running(process_id):
            return True
        time.sleep(0.25)
    return not is_process_running(process_id)


def run_powershell_script(script: Path, args: list[str] | None = None, timeout_seconds: int = 60, env: dict[str, str] | None = None) -> dict[str, Any]:
    command = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script),
    ]
    command.extend(args or [])
    completed = subprocess.run(
        command,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
        env=env,
    )
    return {
        "exit_code": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "command": command,
    }


def json_from_stdout(result: dict[str, Any]) -> dict[str, Any] | None:
    stdout = result.get("stdout") or ""
    if not stdout:
        return None
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\})\s*$", stdout, re.S)
        if not match:
            return None
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None


def queue_status(queue_dir: Path = NODE_PTY_INPUT_QUEUE_DIR) -> dict[str, Any]:
    queue_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(path.name for path in queue_dir.iterdir() if path.is_file())
    return {
        "queue_dir": str(queue_dir),
        "pending": len([name for name in files if name.endswith(".json")]),
        "done": len([name for name in files if name.endswith(".json.done")]),
        "invalid": len([name for name in files if name.endswith(".json.invalid")]),
        "skipped": len([name for name in files if name.endswith(".json.skipped")]),
        "latest_files": files[-10:],
    }


def copilot_session_status() -> dict[str, Any]:
    state = read_json_file(NODE_PTY_STATE_PATH) or {}
    window_state = read_json_file(NODE_PTY_WINDOW_STATE_PATH) or {}
    wrapper_pid = state.get("wrapper_pid")
    launcher_pid = window_state.get("launcher_pid")
    wrapper_running = is_process_running(wrapper_pid)
    launcher_running = is_process_running(launcher_pid)
    status = state.get("status") if wrapper_running else "not_running"
    visible_window_expected = bool(window_state.get("visible_window_expected", not bool(window_state.get("hidden"))))
    return {
        "status": status,
        "running": wrapper_running,
        "visible_window_expected": visible_window_expected and (launcher_running or wrapper_running),
        "startup_model": state.get("startup_model") or window_state.get("startup_model"),
        "startup_allow_all": bool(state.get("startup_allow_all") or window_state.get("startup_allow_all")),
        "startup_commands_sent": bool(state.get("startup_commands_sent")),
        "wrapper_pid": wrapper_pid,
        "launcher_pid": launcher_pid,
        "state_path": str(NODE_PTY_STATE_PATH),
        "window_state_path": str(NODE_PTY_WINDOW_STATE_PATH),
        "updated_at": state.get("updated_at"),
        "started_at": state.get("started_at"),
        "log_path": state.get("log_path") or str(log_path()),
        "user_input_required": bool(state.get("user_input_required")),
        "user_input_reason": state.get("user_input_reason"),
        "transcript_path": state.get("transcript_path"),
        "last_output_tail": state.get("last_output_tail", ""),
        "last_injected_text": state.get("last_injected_text", ""),
        "last_injected_at": state.get("last_injected_at"),
        "input_queue": {**queue_status(), **(state.get("input_queue_status") or {})},
        "raw_state": state if state.get("status") == "unreadable" else None,
    }


def start_copilot_session(
    restart_existing: bool = False,
    log_input: bool = False,
    startup_model: str | None = "gpt-5-mini",
    allow_all: bool = True,
    hidden_window: bool = False,
) -> dict[str, Any]:
    args: list[str] = []
    if restart_existing:
        args.append("-RestartExisting")
    if log_input:
        args.append("-LogInput")
    if startup_model:
        args.extend(["-StartupModel", startup_model])
    if allow_all:
        args.append("-AllowAll")
    if hidden_window:
        args.append("-Hidden")
    env = os.environ.copy()
    env["COPILOT_ADMIN_RUNNER_STATE_DIR"] = str(STATE_DIR)
    result = run_powershell_script(NODE_PTY_START_WINDOW_SCRIPT, args, timeout_seconds=45, env=env)
    payload = json_from_stdout(result) or {}
    status = "started" if result["exit_code"] == 0 else "failed"
    log_event(
        "copilot_session_start_requested",
        "host-runner",
        {"restart_existing": restart_existing, "log_input": log_input, "hidden_window": hidden_window, "exit_code": result["exit_code"]},
        status=status,
    )
    return {
        "status": status,
        "start_result": payload,
        "stderr": result["stderr"],
        "copilot_session": copilot_session_status(),
    }


def stop_copilot_session(timeout_seconds: int = 30) -> dict[str, Any]:
    before = copilot_session_status()
    stopped_wrapper = stop_process(before.get("wrapper_pid"), timeout_seconds)
    stopped_launcher = stop_process(before.get("launcher_pid"), timeout_seconds)
    after = copilot_session_status()
    status = "stopped" if stopped_wrapper and stopped_launcher and not after["running"] else "blocked"
    if status == "stopped":
        state = read_json_file(NODE_PTY_STATE_PATH) or {}
        window_state = read_json_file(NODE_PTY_WINDOW_STATE_PATH) or {}
        stopped_at = utc_now()
        if state:
            state.update({"status": "stopped", "stopped_at": stopped_at, "updated_at": stopped_at})
            NODE_PTY_STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
        if window_state:
            window_state.update({"status": "stopped", "stopped_at": stopped_at, "updated_at": stopped_at})
            NODE_PTY_WINDOW_STATE_PATH.write_text(json.dumps(window_state, indent=2, ensure_ascii=False), encoding="utf-8")
        after = copilot_session_status()
    log_event(
        "copilot_session_stop_requested",
        "host-runner",
        {"before": {k: before.get(k) for k in ("wrapper_pid", "launcher_pid", "running")}, "after": after},
        level="warn" if status == "blocked" else "info",
        status=status,
    )
    return {
        "status": status,
        "stopped_wrapper": stopped_wrapper,
        "stopped_launcher": stopped_launcher,
        "copilot_session": after,
    }


def enqueue_copilot_input(text: str, submit: bool = True, dry_run: bool = False, clear_line: bool = False) -> dict[str, Any]:
    session = copilot_session_status()
    if not dry_run and not session.get("running"):
        log_event(
            "job_failed",
            "host-runner",
            {"reason": "copilot_session_not_running", "submit": submit},
            level="warn",
            status="failed",
        )
        return {
            "status": "failed",
            "error": "No running node-pty Copilot session was found.",
            "copilot_session": session,
        }
    args = ["-Text", text]
    if not submit:
        args.append("-NoSubmit")
    if clear_line:
        args.append("-ClearLine")
    if dry_run:
        args.append("-DryRun")
    env = os.environ.copy()
    env["COPILOT_ADMIN_RUNNER_STATE_DIR"] = str(STATE_DIR)
    result = run_powershell_script(NODE_PTY_SEND_INPUT_SCRIPT, args, timeout_seconds=15, env=env)
    payload = json_from_stdout(result) or {}
    status = payload.get("status", "failed" if result["exit_code"] else "queued")
    log_event(
        "job_dispatched" if not dry_run else "job_dispatch_dry_run",
        "host-runner",
        {"submit": submit, "dry_run": dry_run, "clear_line": clear_line, "exit_code": result["exit_code"], "input_id": payload.get("input_id")},
        status=status,
    )
    return {
        "status": status,
        "input": payload,
        "stderr": result["stderr"],
        "copilot_session": copilot_session_status(),
    }


def get_browser_debug_info(port: int = 9222) -> dict[str, Any] | None:
    try:
        import urllib.request

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2) as response:
            body = response.read().decode("utf-8")
        return json.loads(body)
    except Exception:
        return None


def browser_session_status(port: int | None = None) -> dict[str, Any]:
    state = read_json_file(BROWSER_STATE_PATH) or {}
    effective_port = int(port or state.get("port") or 9222)
    debug_info = get_browser_debug_info(effective_port)
    return {
        "status": "running" if debug_info else "not_running",
        "running": bool(debug_info),
        "port": effective_port,
        "state_path": str(BROWSER_STATE_PATH),
        "debug_version_endpoint": f"http://127.0.0.1:{effective_port}/json/version",
        "debug_targets_endpoint": f"http://127.0.0.1:{effective_port}/json/list",
        "browser": debug_info.get("Browser") if debug_info else state.get("browser"),
        "webSocketDebuggerUrl": debug_info.get("webSocketDebuggerUrl") if debug_info else state.get("webSocketDebuggerUrl"),
        "last_start": state,
    }


def start_browser_session(port: int = 9222, reuse_existing: bool = True, dry_run: bool = False) -> dict[str, Any]:
    args = ["-Port", str(port)]
    if reuse_existing:
        args.append("-ReuseExisting")
    if dry_run:
        return {
            "status": "dry_run",
            "script": str(START_BROWSER_SCRIPT),
            "args": args,
            "browser_session": browser_session_status(port),
        }
    log_event("browser_session_start_requested", "host-runner", {"port": port, "reuse_existing": reuse_existing})
    result = run_powershell_script(START_BROWSER_SCRIPT, args, timeout_seconds=45)
    payload = json_from_stdout(result) or {}
    if result["exit_code"] == 0 and payload:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        payload["status"] = "running"
        payload["started_at"] = payload.get("started_at") or utc_now()
        payload["updated_at"] = utc_now()
        BROWSER_STATE_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    status = "started" if result["exit_code"] == 0 else "failed"
    log_event(
        "browser_session_started" if status == "started" else "job_failed",
        "host-runner",
        {"port": port, "exit_code": result["exit_code"], "stderr": result["stderr"]},
        level="error" if status == "failed" else "info",
        status=status,
    )
    return {
        "status": status,
        "start_result": payload,
        "stderr": result["stderr"],
        "browser_session": browser_session_status(port),
    }


def stop_browser_session(port: int | None = None, timeout_seconds: int = 30) -> dict[str, Any]:
    before = browser_session_status(port)
    state = read_json_file(BROWSER_STATE_PATH) or {}
    process_id = state.get("processId") or state.get("process_id")
    stopped_process = stop_process(process_id, timeout_seconds)
    effective_port = int(port or before.get("port") or 9222)
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if not get_browser_debug_info(effective_port):
            break
        time.sleep(0.25)
    after = browser_session_status(effective_port)
    if not after.get("running"):
        final_state = {
            **state,
            "status": "stopped",
            "stopped_at": utc_now(),
            "updated_at": utc_now(),
            "port": effective_port,
        }
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        BROWSER_STATE_PATH.write_text(json.dumps(final_state, indent=2, ensure_ascii=False), encoding="utf-8")
        after = browser_session_status(effective_port)
        status = "stopped"
    elif process_id:
        status = "blocked"
    else:
        status = "blocked"
    log_event(
        "browser_session_stop_requested",
        "host-runner",
        {
            "port": effective_port,
            "process_id": process_id,
            "stopped_process": stopped_process,
            "before": {"running": before.get("running"), "status": before.get("status")},
            "after": {"running": after.get("running"), "status": after.get("status")},
        },
        level="warn" if status == "blocked" else "info",
        status=status,
    )
    return {
        "status": status,
        "stopped_process": stopped_process,
        "browser_session": after,
        "note": None if process_id else "No owned browser processId was recorded; refusing to kill an unknown browser.",
    }


def start_admin_session(request: dict[str, Any]) -> dict[str, Any]:
    dry_run = bool(request.get("dry_run"))
    existing_copilot = copilot_session_status()
    if dry_run:
        copilot = {
            "status": "dry_run",
            "script": str(NODE_PTY_START_WINDOW_SCRIPT),
            "copilot_session": existing_copilot,
        }
    elif existing_copilot.get("running") and not bool(request.get("restart_existing")):
        copilot = {
            "status": "reused_existing",
            "reason": "Existing node-pty Copilot session is already running; no new Copilot window was opened.",
            "copilot_session": existing_copilot,
        }
    else:
        copilot = start_copilot_session(
            restart_existing=bool(request.get("restart_existing")),
            log_input=bool(request.get("log_input")),
            startup_model=str(request.get("startup_model") or "gpt-5-mini"),
            allow_all=not bool(request.get("no_allow_all")),
            hidden_window=bool(request.get("hidden_window")),
        )
    browser = start_browser_session(
        port=int(request.get("port") or 9222),
        reuse_existing=not bool(request.get("no_reuse_existing")),
        dry_run=dry_run,
    )
    status = "started"
    if dry_run:
        status = "dry_run"
    elif copilot.get("status") == "failed" or browser.get("status") == "failed":
        status = "failed"
    log_event("copilot_session_started", "host-runner", {"status": copilot.get("status")}, status=copilot.get("status"))
    return {
        "status": status,
        "copilot": copilot,
        "browser": browser,
        "host_status": status_payload(),
    }


def stop_admin_session(request: dict[str, Any]) -> dict[str, Any]:
    timeout_seconds = int(request.get("timeout_seconds") or 30)
    copilot = stop_copilot_session(timeout_seconds)
    browser = stop_browser_session(
        port=int(request["port"]) if request.get("port") else None,
        timeout_seconds=timeout_seconds,
    )
    status = "stopped" if copilot.get("status") == "stopped" and browser.get("status") == "stopped" else "blocked"
    log_event(
        "admin_session_stop_requested",
        "host-runner",
        {"copilot_status": copilot.get("status"), "browser_status": browser.get("status")},
        level="warn" if status == "blocked" else "info",
        status=status,
    )
    return {
        "status": status,
        "copilot": copilot,
        "browser": browser,
        "host_status": status_payload(),
    }


def latest_report_dir() -> Path | None:
    candidates: list[tuple[str, int, Path]] = []
    for path in REPORTS_DIR.iterdir():
        if not path.is_dir():
            continue
        match = re.fullmatch(r"(\d{8})v(\d+)", path.name)
        if not match:
            continue
        candidates.append((match.group(1), int(match.group(2)), path))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1]))
    return candidates[-1][2]


def parse_latest_summary() -> dict[str, Any] | None:
    report_dir = latest_report_dir()
    if not report_dir:
        return None

    summary_path = report_dir / "summary.md"
    if not summary_path.is_file():
        return {
            "run_id": report_dir.name,
            "path": to_rel(report_dir),
            "tests": [],
        }

    tests: list[dict[str, str]] = []
    for line in summary_path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| `"):
            continue
        cells = split_markdown_row(line)
        if len(cells) < 5:
            continue
        tests.append(
            {
                "test_id": cells[0].strip("`"),
                "test_name": cells[1],
                "status": cells[2].strip("`"),
                "outcome": cells[3],
                "detail": cells[4].strip("`"),
            }
        )

    return {
        "run_id": report_dir.name,
        "path": to_rel(report_dir),
        "tests": tests,
    }


def graph_payload() -> dict[str, Any]:
    return {
        "path": to_rel(GRAPH_PATH),
        "mermaid": GRAPH_PATH.read_text(encoding="utf-8"),
    }


def build_command_payload(
    command_id: str,
    catalog_key: str | None = None,
    verification_id: str | None = None,
) -> dict[str, Any]:
    if command_id not in COMMAND_TEMPLATES:
        raise ValueError(f"Unknown command template: {command_id}")

    template = COMMAND_TEMPLATES[command_id]
    args = template["arguments"]
    if "catalog_key" in args and not catalog_key:
        raise ValueError(f"Command template '{command_id}' requires --catalog-key.")
    if "verification_id" in args and not verification_id:
        raise ValueError(f"Command template '{command_id}' requires --verification-id.")

    prompt = template["template"].format(catalog_key=catalog_key, verification_id=verification_id)
    return {
        "command_id": command_id,
        "label": template["label"],
        "mode": template["mode"],
        "prompt": prompt,
        "catalog_key": catalog_key,
        "verification_id": verification_id,
    }


def status_payload() -> dict[str, Any]:
    copilot = copilot_session_status()
    browser = browser_session_status()
    return {
        "generated_at": utc_now(),
        "repo_root": str(REPO_ROOT),
        "runtime_scripts": list_runtime_scripts(),
        "regression_catalog": parse_catalog(),
        "latest_report": parse_latest_summary(),
        "supported_bridges": list(BRIDGE_CHOICES),
        "host_runner": {
            "status": "ok",
            "log_path": str(log_path()),
            "state_dir": str(STATE_DIR),
        },
        "copilot_session": copilot,
        "browser_session": browser,
        "status_diode": (
            "yellow"
            if copilot.get("running") or copilot.get("user_input_required")
            else "red"
        ),
        "command_templates": [
            {
                "command_id": command_id,
                "label": definition["label"],
                "mode": definition["mode"],
                "arguments": definition["arguments"],
            }
            for command_id, definition in COMMAND_TEMPLATES.items()
        ],
    }


def ensure_queue_dirs(base_dir: Path) -> dict[str, Path]:
    jobs = base_dir / "jobs"
    processing = base_dir / "processing"
    done = base_dir / "done"
    results = base_dir / "results"
    for path in (jobs, processing, done, results):
        path.mkdir(parents=True, exist_ok=True)
    return {
        "root": base_dir,
        "jobs": jobs,
        "processing": processing,
        "done": done,
        "results": results,
    }


def queue_submit(
    base_dir: Path,
    command_id: str,
    catalog_key: str | None,
    verification_id: str | None,
) -> dict[str, Any]:
    dirs = ensure_queue_dirs(base_dir)
    payload = build_command_payload(command_id, catalog_key, verification_id)
    job_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    job = {
        "job_id": job_id,
        "created_at": utc_now(),
        "bridge": "file-queue",
        "payload": payload,
    }
    job_path = dirs["jobs"] / f"{job_id}.json"
    job_path.write_text(json.dumps(job, indent=2, ensure_ascii=False), encoding="utf-8")
    log_event(
        "queue_job_submitted",
        "file-queue",
        {
            "job_id": job_id,
            "job_path": str(job_path),
            "command": response_summary(payload),
            "queue_dir": str(base_dir),
        },
    )
    return {
        "job_id": job_id,
        "job_path": str(job_path),
        "payload": payload,
        "log_path": str(log_path()),
    }


def queue_process_once(base_dir: Path) -> dict[str, Any]:
    dirs = ensure_queue_dirs(base_dir)
    pending = sorted(dirs["jobs"].glob("*.json"), key=lambda path: path.name.casefold())
    if not pending:
        log_event("queue_idle", "file-queue", {"queue_dir": str(base_dir)})
        return {
            "status": "idle",
            "message": "No queued jobs were found.",
            "log_path": str(log_path()),
        }

    job_path = pending[0]
    processing_path = dirs["processing"] / job_path.name
    done_path = dirs["done"] / job_path.name
    result_path = dirs["results"] / job_path.name
    job_path.replace(processing_path)
    job = json.loads(processing_path.read_text(encoding="utf-8"))

    result = {
        "job_id": job["job_id"],
        "processed_at": utc_now(),
        "bridge": "file-queue",
        "command_payload": job["payload"],
        "status_snapshot": status_payload(),
        "note": "POC execution only: command payload prepared but not sent to Copilot CLI automatically.",
    }
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    processing_path.replace(done_path)
    log_event(
        "queue_job_processed",
        "file-queue",
        {
            "job_id": job["job_id"],
            "result_path": str(result_path),
            "done_path": str(done_path),
            "command": response_summary(job["payload"]),
        },
    )
    return {
        "status": "processed",
        "job_id": job["job_id"],
        "result_path": str(result_path),
        "log_path": str(log_path()),
    }


def pipe_address(pipe_name: str) -> str:
    return rf"\\.\pipe\{pipe_name}"


def build_commands_payload() -> dict[str, Any]:
    return {
        "generated_at": utc_now(),
        "commands": [
            build_command_payload(command_id) if not definition["arguments"] else {
                "command_id": command_id,
                "label": definition["label"],
                "mode": definition["mode"],
                "arguments": definition["arguments"],
                "template": definition["template"],
            } for command_id, definition in COMMAND_TEMPLATES.items()
        ]
    }


def build_health_payload() -> dict[str, Any]:
    return {
        "status": "ok",
        "generated_at": utc_now(),
        "repo_root": str(REPO_ROOT),
        "log_path": str(log_path()),
    }


def handle_request(request: dict[str, Any], bridge: str = "direct") -> dict[str, Any]:
    log_event("request_received", bridge, request_summary(request))
    action = request.get("action")
    try:
        if action == "health":
            payload = build_health_payload()
        elif action == "status":
            payload = status_payload()
        elif action == "graph":
            payload = graph_payload()
        elif action == "commands":
            payload = build_commands_payload()
        elif action == "copilot-status":
            payload = copilot_session_status()
        elif action == "copilot-start":
            payload = start_copilot_session(
                restart_existing=bool(request.get("restart_existing")),
                log_input=bool(request.get("log_input")),
                startup_model=request.get("startup_model") or "gpt-5-mini",
                allow_all=not bool(request.get("no_allow_all")),
                hidden_window=bool(request.get("hidden_window")),
            )
        elif action == "copilot-stop":
            payload = stop_copilot_session(int(request.get("timeout_seconds") or 30))
        elif action == "copilot-input":
            submit = bool(request["submit"]) if "submit" in request else not bool(request.get("no_submit"))
            payload = enqueue_copilot_input(
                str(request.get("text") or ""),
                submit=submit,
                dry_run=bool(request.get("dry_run")),
                clear_line=bool(request.get("clear_line")),
            )
        elif action == "browser-status":
            payload = browser_session_status(
                int(request["port"]) if request.get("port") else None
            )
        elif action == "browser-start":
            payload = start_browser_session(
                port=int(request.get("port") or 9222),
                reuse_existing=not bool(request.get("no_reuse_existing")),
                dry_run=bool(request.get("dry_run")),
            )
        elif action == "browser-stop":
            payload = stop_browser_session(
                port=int(request["port"]) if request.get("port") else None,
                timeout_seconds=int(request.get("timeout_seconds") or 30),
            )
        elif action == "session-start":
            payload = start_admin_session(request)
        elif action == "session-stop":
            payload = stop_admin_session(request)
        elif action == "command-template":
            payload = build_command_payload(
                request["command_id"],
                request.get("catalog_key"),
                request.get("verification_id"),
            )
        else:
            raise ValueError(f"Unknown request action: {action}")
    except Exception as exc:
        log_event(
            "request_failed",
            bridge,
            {**request_summary(request), "error": str(exc), "error_type": type(exc).__name__},
        )
        raise

    log_event("request_succeeded", bridge, {**request_summary(request), "response": response_summary(payload)})
    return payload


def json_stdout(payload: dict[str, Any]) -> int:
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def run_status(_: argparse.Namespace) -> int:
    return json_stdout(handle_request({"action": "status"}, "direct"))


def run_graph(_: argparse.Namespace) -> int:
    return json_stdout(handle_request({"action": "graph"}, "direct"))


def run_commands(_: argparse.Namespace) -> int:
    return json_stdout(handle_request({"action": "commands"}, "direct"))


def run_command_template(args: argparse.Namespace) -> int:
    return json_stdout(
        handle_request(
            {
                "action": "command-template",
                "command_id": args.command_id,
                "catalog_key": args.catalog_key,
                "verification_id": args.verification_id,
            },
            "direct",
        )
    )


def run_copilot_status(_: argparse.Namespace) -> int:
    return json_stdout(handle_request({"action": "copilot-status"}, "direct"))


def run_copilot_start(args: argparse.Namespace) -> int:
    return json_stdout(
        handle_request(
            {
                "action": "copilot-start",
                "restart_existing": args.restart_existing,
                "log_input": args.log_input,
                "startup_model": args.startup_model,
                "no_allow_all": args.no_allow_all,
                "hidden_window": args.hidden_window,
            },
            "direct",
        )
    )


def run_copilot_stop(args: argparse.Namespace) -> int:
    return json_stdout(
        handle_request(
            {"action": "copilot-stop", "timeout_seconds": args.timeout_seconds},
            "direct",
        )
    )


def run_copilot_input(args: argparse.Namespace) -> int:
    return json_stdout(
        handle_request(
            {
                "action": "copilot-input",
                "text": args.text,
                "no_submit": args.no_submit,
                "dry_run": args.dry_run,
                "clear_line": args.clear_line,
            },
            "direct",
        )
    )


def run_browser_status(args: argparse.Namespace) -> int:
    return json_stdout(
        handle_request({"action": "browser-status", "port": args.port}, "direct")
    )


def run_browser_start(args: argparse.Namespace) -> int:
    return json_stdout(
        handle_request(
            {
                "action": "browser-start",
                "port": args.port,
                "no_reuse_existing": args.no_reuse_existing,
                "dry_run": args.dry_run,
            },
            "direct",
        )
    )


def run_browser_stop(args: argparse.Namespace) -> int:
    return json_stdout(
        handle_request(
            {
                "action": "browser-stop",
                "port": args.port,
                "timeout_seconds": args.timeout_seconds,
            },
            "direct",
        )
    )


def run_session_start(args: argparse.Namespace) -> int:
    return json_stdout(
        handle_request(
            {
                "action": "session-start",
                "port": args.port,
                "restart_existing": args.restart_existing,
                "log_input": args.log_input,
                "startup_model": args.startup_model,
                "no_allow_all": args.no_allow_all,
                "hidden_window": args.hidden_window,
                "dry_run": args.dry_run,
            },
            "direct",
        )
    )


def run_session_stop(args: argparse.Namespace) -> int:
    return json_stdout(
        handle_request(
            {
                "action": "session-stop",
                "port": args.port,
                "timeout_seconds": args.timeout_seconds,
            },
            "direct",
        )
    )


def run_http_server(args: argparse.Namespace) -> int:
    class Handler(BaseHTTPRequestHandler):
        def _send_json(self, payload: dict[str, Any], status_code: int = 200) -> None:
            body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format: str, *args: Any) -> None:
            return

        def _query(self) -> dict[str, str]:
            parsed = urlparse(self.path)
            return {key: values[-1] for key, values in parse_qs(parsed.query).items() if values}

        def _read_json_body(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0:
                return {}
            raw = self.rfile.read(length).decode("utf-8")
            if not raw:
                return {}
            body = json.loads(raw)
            if not isinstance(body, dict):
                raise ValueError("Request body must be a JSON object.")
            return body

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            query = self._query()
            status_code = 200
            request_details = {
                "method": "GET",
                "path": parsed.path,
                "query": parsed.query,
                "client": self.client_address[0],
            }
            log_event("http_request_received", "http-api", request_details)
            try:
                if parsed.path == "/health":
                    payload = handle_request({"action": "health"}, "http-api")
                    self._send_json(payload)
                    return
                if parsed.path == "/status":
                    payload = handle_request({"action": "status"}, "http-api")
                    self._send_json(payload)
                    return
                if parsed.path == "/graph":
                    payload = handle_request({"action": "graph"}, "http-api")
                    self._send_json(payload)
                    return
                if parsed.path == "/commands":
                    payload = handle_request({"action": "commands"}, "http-api")
                    self._send_json(payload)
                    return
                if parsed.path in ("/copilot/status", "/session/copilot"):
                    payload = handle_request({"action": "copilot-status"}, "http-api")
                    self._send_json(payload)
                    return
                if parsed.path in ("/browser/status", "/session/browser"):
                    payload = handle_request({"action": "browser-status", **query}, "http-api")
                    self._send_json(payload)
                    return
                if parsed.path in ("/host/status", "/api/status"):
                    payload = handle_request({"action": "status"}, "http-api")
                    self._send_json(payload)
                    return
                if parsed.path.startswith("/commands/"):
                    command_id = parsed.path.rsplit("/", 1)[-1]
                    payload = handle_request(
                        {
                            "action": "command-template",
                            "command_id": command_id,
                            "catalog_key": query.get("catalog_key"),
                            "verification_id": query.get("verification_id"),
                        },
                        "http-api",
                    )
                    self._send_json(payload)
                    return
                status_code = 404
                payload = {"error": "Not found", "path": parsed.path}
                log_event("http_request_failed", "http-api", {**request_details, **payload})
                self._send_json(payload, status_code=status_code)
            except ValueError as exc:
                status_code = 400
                log_event("http_request_failed", "http-api", {**request_details, "error": str(exc)})
                self._send_json({"error": str(exc)}, status_code=status_code)

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            request_details = {
                "method": "POST",
                "path": parsed.path,
                "client": self.client_address[0],
            }
            log_event("http_request_received", "http-api", request_details)
            try:
                body = self._read_json_body()
                if parsed.path == "/copilot/start":
                    payload = handle_request({"action": "copilot-start", **body}, "http-api")
                    self._send_json(payload)
                    return
                if parsed.path == "/api/session/start":
                    payload = handle_request({"action": "session-start", **body}, "http-api")
                    self._send_json(payload)
                    return
                if parsed.path == "/copilot/stop":
                    payload = handle_request({"action": "copilot-stop", **body}, "http-api")
                    self._send_json(payload)
                    return
                if parsed.path == "/copilot/input":
                    payload = handle_request({"action": "copilot-input", **body}, "http-api")
                    self._send_json(payload)
                    return
                if parsed.path in ("/browser/start", "/api/session/browser/start"):
                    payload = handle_request({"action": "browser-start", **body}, "http-api")
                    self._send_json(payload)
                    return
                if parsed.path in ("/browser/stop", "/api/session/browser/stop"):
                    payload = handle_request({"action": "browser-stop", **body}, "http-api")
                    self._send_json(payload)
                    return
                if parsed.path == "/api/session/start-browser":
                    payload = handle_request({"action": "browser-start", **body}, "http-api")
                    self._send_json(payload)
                    return
                if parsed.path == "/api/session/stop":
                    payload = handle_request({"action": "session-stop", **body}, "http-api")
                    self._send_json(payload)
                    return
                payload = {"error": "Not found", "path": parsed.path}
                log_event("http_request_failed", "http-api", {**request_details, **payload})
                self._send_json(payload, status_code=404)
            except (ValueError, json.JSONDecodeError) as exc:
                log_event("http_request_failed", "http-api", {**request_details, "error": str(exc)})
                self._send_json({"error": str(exc)}, status_code=400)

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    startup = {
        "status": "listening",
        "bridge": "http-api",
        "host": args.host,
        "port": args.port,
        "health_url": f"http://{args.host}:{args.port}/health",
        "log_path": str(log_path()),
    }
    log_event("server_started", "http-api", startup)
    print(json.dumps(startup, ensure_ascii=False))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log_event("server_stopped", "http-api", {"reason": "KeyboardInterrupt"})
        return 0
    finally:
        server.server_close()


def run_filequeue_init(args: argparse.Namespace) -> int:
    dirs = ensure_queue_dirs(Path(args.queue_dir))
    log_event("queue_initialized", "file-queue", {"queue_dir": str(Path(args.queue_dir)), "log_path": str(log_path())})
    return json_stdout(
        {
            "status": "ready",
            "bridge": "file-queue",
            "paths": {name: str(path) for name, path in dirs.items()},
            "log_path": str(log_path()),
        }
    )


def run_filequeue_submit(args: argparse.Namespace) -> int:
    return json_stdout(
        queue_submit(
            Path(args.queue_dir),
            args.command_id,
            args.catalog_key,
            args.verification_id,
        )
    )


def run_filequeue_process_once(args: argparse.Namespace) -> int:
    return json_stdout(queue_process_once(Path(args.queue_dir)))


def run_pipe_server(args: argparse.Namespace) -> int:
    address = pipe_address(args.pipe_name)
    listener = Listener(address=address, family="AF_PIPE")
    startup = {
        "status": "listening",
        "bridge": "named-pipe",
        "pipe_name": args.pipe_name,
        "address": address,
        "log_path": str(log_path()),
    }
    log_event("server_started", "named-pipe", startup)
    print(json.dumps(startup, ensure_ascii=False))
    try:
        while True:
            connection = listener.accept()
            try:
                request = connection.recv()
                if not isinstance(request, dict):
                    log_event("request_failed", "named-pipe", {"error": "Requests must be JSON-like dictionaries."})
                    connection.send({"error": "Requests must be JSON-like dictionaries."})
                    continue
                connection.send(handle_request(request, "named-pipe"))
            except Exception as exc:  # explicit transport error surface
                log_event(
                    "request_failed",
                    "named-pipe",
                    {"error": str(exc), "error_type": type(exc).__name__},
                )
                connection.send({"error": str(exc)})
            finally:
                connection.close()
    except KeyboardInterrupt:
        log_event("server_stopped", "named-pipe", {"reason": "KeyboardInterrupt"})
        return 0
    finally:
        listener.close()


def run_pipe_request(args: argparse.Namespace) -> int:
    address = pipe_address(args.pipe_name)
    request: dict[str, Any] = {"action": args.action}
    if args.command_id:
        request["command_id"] = args.command_id
    if args.catalog_key:
        request["catalog_key"] = args.catalog_key
    if args.verification_id:
        request["verification_id"] = args.verification_id

    log_event("pipe_client_request", "named-pipe", {"address": address, "request": request_summary(request)})
    connection = Client(address=address, family="AF_PIPE")
    try:
        connection.send(request)
        response = connection.recv()
    finally:
        connection.close()
    if isinstance(response, dict):
        log_event("pipe_client_response", "named-pipe", {"response": response_summary(response)})
    return json_stdout(response)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="POC host runner for SPS Copilot admin workflows."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    status_parser = subparsers.add_parser("status", help="Return runner status snapshot.")
    status_parser.set_defaults(func=run_status)

    graph_parser = subparsers.add_parser("graph", help="Return raw Mermaid dependency graph.")
    graph_parser.set_defaults(func=run_graph)

    commands_parser = subparsers.add_parser("commands", help="List standardized command templates.")
    commands_parser.set_defaults(func=run_commands)

    template_parser = subparsers.add_parser(
        "command-template",
        help="Render a single standardized command prompt.",
    )
    template_parser.add_argument("--command-id", required=True)
    template_parser.add_argument("--catalog-key")
    template_parser.add_argument("--verification-id")
    template_parser.set_defaults(func=run_command_template)

    copilot_status_parser = subparsers.add_parser("copilot-status", help="Return node-pty Copilot session status.")
    copilot_status_parser.set_defaults(func=run_copilot_status)

    copilot_start_parser = subparsers.add_parser("copilot-start", help="Start a visible node-pty Copilot window.")
    copilot_start_parser.add_argument("--restart-existing", action="store_true")
    copilot_start_parser.add_argument("--log-input", action="store_true")
    copilot_start_parser.add_argument("--startup-model", default="gpt-5-mini")
    copilot_start_parser.add_argument("--no-allow-all", action="store_true")
    copilot_start_parser.add_argument("--hidden-window", action="store_true")
    copilot_start_parser.set_defaults(func=run_copilot_start)

    copilot_stop_parser = subparsers.add_parser("copilot-stop", help="Stop the active node-pty Copilot session.")
    copilot_stop_parser.add_argument("--timeout-seconds", type=int, default=30)
    copilot_stop_parser.set_defaults(func=run_copilot_stop)

    copilot_input_parser = subparsers.add_parser("copilot-input", help="Queue input for the node-pty Copilot session.")
    copilot_input_parser.add_argument("--text", required=True)
    copilot_input_parser.add_argument("--no-submit", action="store_true")
    copilot_input_parser.add_argument("--clear-line", action="store_true")
    copilot_input_parser.add_argument("--dry-run", action="store_true")
    copilot_input_parser.set_defaults(func=run_copilot_input)

    browser_status_parser = subparsers.add_parser("browser-status", help="Return collaborative browser status.")
    browser_status_parser.add_argument("--port", type=int, default=9222)
    browser_status_parser.set_defaults(func=run_browser_status)

    browser_start_parser = subparsers.add_parser("browser-start", help="Start the visible collaborative browser.")
    browser_start_parser.add_argument("--port", type=int, default=9222)
    browser_start_parser.add_argument("--no-reuse-existing", action="store_true")
    browser_start_parser.add_argument("--dry-run", action="store_true")
    browser_start_parser.set_defaults(func=run_browser_start)

    browser_stop_parser = subparsers.add_parser("browser-stop", help="Stop the owned collaborative browser.")
    browser_stop_parser.add_argument("--port", type=int, default=9222)
    browser_stop_parser.add_argument("--timeout-seconds", type=int, default=30)
    browser_stop_parser.set_defaults(func=run_browser_stop)

    session_start_parser = subparsers.add_parser("session-start", help="Start Copilot and browser host-side session.")
    session_start_parser.add_argument("--port", type=int, default=9222)
    session_start_parser.add_argument("--restart-existing", action="store_true")
    session_start_parser.add_argument("--log-input", action="store_true")
    session_start_parser.add_argument("--startup-model", default="gpt-5-mini")
    session_start_parser.add_argument("--no-allow-all", action="store_true")
    session_start_parser.add_argument("--hidden-window", action="store_true")
    session_start_parser.add_argument("--dry-run", action="store_true")
    session_start_parser.set_defaults(func=run_session_start)

    session_stop_parser = subparsers.add_parser("session-stop", help="Stop Copilot and browser host-side session.")
    session_stop_parser.add_argument("--port", type=int, default=9222)
    session_stop_parser.add_argument("--timeout-seconds", type=int, default=30)
    session_stop_parser.set_defaults(func=run_session_stop)

    http_parser = subparsers.add_parser("http-server", help="Start HTTP API POC.")
    http_parser.add_argument("--host", default="127.0.0.1")
    http_parser.add_argument("--port", type=int, default=8765)
    http_parser.set_defaults(func=run_http_server)

    queue_init_parser = subparsers.add_parser("filequeue-init", help="Initialize file queue POC.")
    queue_init_parser.add_argument("--queue-dir", default=str(QUEUE_DIR))
    queue_init_parser.set_defaults(func=run_filequeue_init)

    queue_submit_parser = subparsers.add_parser("filequeue-submit", help="Submit a file queue POC job.")
    queue_submit_parser.add_argument("--queue-dir", default=str(QUEUE_DIR))
    queue_submit_parser.add_argument("--command-id", required=True)
    queue_submit_parser.add_argument("--catalog-key")
    queue_submit_parser.add_argument("--verification-id")
    queue_submit_parser.set_defaults(func=run_filequeue_submit)

    queue_process_parser = subparsers.add_parser(
        "filequeue-process-once",
        help="Process one queued file queue POC job.",
    )
    queue_process_parser.add_argument("--queue-dir", default=str(QUEUE_DIR))
    queue_process_parser.set_defaults(func=run_filequeue_process_once)

    pipe_server_parser = subparsers.add_parser("pipe-server", help="Start named pipe POC server.")
    pipe_server_parser.add_argument("--pipe-name", default="sps-copilot-admin-runner")
    pipe_server_parser.set_defaults(func=run_pipe_server)

    pipe_request_parser = subparsers.add_parser("pipe-request", help="Send one named pipe POC request.")
    pipe_request_parser.add_argument(
        "--action",
        choices=("health", "status", "graph", "commands", "command-template"),
        required=True,
    )
    pipe_request_parser.add_argument("--pipe-name", default="sps-copilot-admin-runner")
    pipe_request_parser.add_argument("--command-id")
    pipe_request_parser.add_argument("--catalog-key")
    pipe_request_parser.add_argument("--verification-id")
    pipe_request_parser.set_defaults(func=run_pipe_request)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
