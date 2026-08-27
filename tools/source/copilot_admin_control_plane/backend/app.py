from __future__ import annotations

import argparse
import base64
import ctypes
import json
import mimetypes
import os
import re
import threading
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import parse_qs, unquote, urlparse


REPO_ROOT = Path(os.environ.get("SPS_REPO_ROOT", Path(__file__).resolve().parents[4])).resolve()
FRONTEND_DIR = Path(
    os.environ.get(
        "COPILOT_ADMIN_FRONTEND_DIR",
        REPO_ROOT / "tools" / "source" / "copilot_admin_control_plane" / "frontend",
    )
).resolve()
TEST_DIR = REPO_ROOT / "testing" / "regression_test"
REPORTS_DIR = REPO_ROOT / "test_reports"
CATALOG_PATH = TEST_DIR / "regression-test-catalog.md"
MERMAID_PATH = TEST_DIR / "regression-test-dependencies.mmd"
NODE_PTY_STATE_DIR = REPO_ROOT / "tmp" / "copilot_admin_runner_state"
NODE_PTY_STATE_PATH = NODE_PTY_STATE_DIR / "node-pty-copilot-session.json"
NODE_PTY_WINDOW_STATE_PATH = NODE_PTY_STATE_DIR / "node-pty-copilot-window.json"
STATE_DIR = REPO_ROOT / "tmp" / "copilot_admin_control_plane" / "state"
LOG_DIR = REPO_ROOT / "tmp" / "copilot_admin_control_plane" / "logs"
JOBS_PATH = STATE_DIR / "jobs.json"
HOST_STATE_PATH = STATE_DIR / "injected-host-state.json"
MODE_PATH = STATE_DIR / "current-mode.json"
BACKEND_VERSION = "0.1.0"
DEFAULT_CONSOLE_TAIL_BYTES = 12000
MAX_CONSOLE_DELTA_BYTES = 65536
JOB_STATUSES = {
    "queued",
    "running",
    "user_input_required",
    "completed_unopened",
    "completed_opened",
    "failed",
}
ACTIVE_STATUSES = {"queued", "running", "user_input_required"}


def host_runner_url() -> str | None:
    if os.environ.get("COPILOT_ADMIN_ENV", "").lower() == "test" and os.environ.get("COPILOT_ADMIN_ALLOW_TEST_HOST_RUNNER") != "1":
        return None
    value = os.environ.get("COPILOT_ADMIN_HOST_RUNNER_URL", "").strip().rstrip("/")
    return value or None


def is_test_env(value: str | None = None) -> bool:
    return (value if value is not None else os.environ.get("COPILOT_ADMIN_ENV", "")).lower() in {"test", "testing"}


def normalize_mode(value: Any) -> str | None:
    text = str(value or "").strip().lower().replace("_", " ")
    if text in {"learning", "learning mode"}:
        return "learning"
    if text in {"testing", "testing mode"}:
        return "testing"
    return None


class ApiError(Exception):
    def __init__(self, status_code: int, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.details = details or {}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel_path(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT)).replace("/", "\\")


def ensure_child(root: Path, candidate: Path) -> Path:
    resolved_root = root.resolve()
    resolved_candidate = candidate.resolve()
    if resolved_candidate != resolved_root and resolved_root not in resolved_candidate.parents:
        raise ApiError(400, "Path escapes allowed root.")
    return resolved_candidate


def split_markdown_row(line: str) -> list[str]:
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|"):
        text = text[:-1]
    cells: list[str] = []
    buf: list[str] = []
    in_code = False
    for char in text:
        if char == "`":
            in_code = not in_code
            buf.append(char)
        elif char == "|" and not in_code:
            cells.append("".join(buf).strip())
            buf = []
        else:
            buf.append(char)
    cells.append("".join(buf).strip())
    return cells


def report_id_for(path: Path) -> str:
    rel = rel_path(path)
    token = base64.urlsafe_b64encode(rel.encode("utf-8")).decode("ascii").rstrip("=")
    return token


def path_for_report_id(report_id: str) -> Path:
    try:
        padded = report_id + "=" * (-len(report_id) % 4)
        rel = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
    except Exception as exc:
        raise ApiError(400, "Invalid report_id.") from exc
    if Path(rel).is_absolute() or ".." in Path(rel).parts:
        raise ApiError(400, "Invalid report path.")
    path = ensure_child(REPORTS_DIR, REPO_ROOT / rel)
    if not path.is_file() or path.suffix.lower() != ".md":
        raise ApiError(404, "Report not found.")
    return path


def read_json_file(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ApiError(500, f"Invalid JSON state file: {rel_path(path)}") from exc


def read_optional_json_file(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default


def is_process_running(pid: Any) -> bool:
    try:
        pid_int = int(pid)
    except (TypeError, ValueError):
        return False
    if pid_int <= 0:
        return False
    if os.name == "nt":
        process_query_limited_information = 0x1000
        still_active = 259
        handle = ctypes.windll.kernel32.OpenProcess(process_query_limited_information, False, pid_int)
        if not handle:
            return False
        try:
            exit_code = ctypes.c_ulong()
            if not ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return False
            return exit_code.value == still_active
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    try:
        os.kill(pid_int, 0)
    except OSError:
        return False
    return True


class ControlPlaneBackend:
    def __init__(self, repo_root: Path = REPO_ROOT):
        self.repo_root = repo_root
        self.started_at = utc_now()
        self.session_id = os.environ.get("COPILOT_ADMIN_SESSION_ID", uuid.uuid4().hex)
        self.env = os.environ.get("COPILOT_ADMIN_ENV", "development").lower()
        self._lock = threading.RLock()
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        if not JOBS_PATH.exists():
            self._write_jobs([])
        self.log("info", "backend", "backend_started", details={"repo_root": str(self.repo_root), "env": self.env})

    def log(
        self,
        level: str,
        component: str,
        event: str,
        *,
        trace_id: str | None = None,
        job_id: str | None = None,
        status: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        record = {
            "timestamp": utc_now(),
            "level": level,
            "component": component,
            "event": event,
            "trace_id": trace_id or uuid.uuid4().hex,
            "session_id": self.session_id,
            "job_id": job_id,
            "status": status,
            "details": details or {},
        }
        day = datetime.now(timezone.utc).strftime("%Y%m%d")
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with (LOG_DIR / f"backend-{day}.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record

    def _read_jobs(self) -> list[dict[str, Any]]:
        data = read_json_file(JOBS_PATH, [])
        if not isinstance(data, list):
            raise ApiError(500, "Job state is not a list.")
        return data

    def _write_jobs(self, jobs: list[dict[str, Any]]) -> None:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        tmp_path = JOBS_PATH.with_suffix(".json.tmp")
        tmp_path.write_text(json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(JOBS_PATH)

    def parse_catalog(self) -> dict[str, Any]:
        entries: list[dict[str, Any]] = []
        text = CATALOG_PATH.read_text(encoding="utf-8")
        for line in text.splitlines():
            if not line.startswith("| `"):
                continue
            cells = split_markdown_row(line)
            if len(cells) != 5:
                continue
            dependency_text = cells[1].strip("`")
            dependencies = [] if dependency_text == "-" else [part.strip() for part in dependency_text.split("->")]
            entries.append(
                {
                    "catalog_key": cells[0].strip("`"),
                    "dependency": dependency_text,
                    "dependencies": dependencies,
                    "test_id": cells[2].strip("`"),
                    "summary": cells[3],
                    "file": cells[4].strip("`"),
                }
            )
        return {"path": rel_path(CATALOG_PATH), "count": len(entries), "tests": entries}

    def mermaid(self) -> dict[str, Any]:
        text = MERMAID_PATH.read_text(encoding="utf-8")
        return {"path": rel_path(MERMAID_PATH), "bytes": len(text.encode("utf-8")), "mermaid": text}

    def list_reports(self) -> dict[str, Any]:
        reports: list[dict[str, Any]] = []
        if REPORTS_DIR.is_dir():
            for path in REPORTS_DIR.rglob("*.md"):
                if any(part == "node_modules" for part in path.parts):
                    continue
                safe = ensure_child(REPORTS_DIR, path)
                stat = safe.stat()
                run_id = next((part for part in safe.relative_to(REPORTS_DIR).parts if re.fullmatch(r"\d{8}v\d+", part)), None)
                report_type = "summary" if safe.name.lower() == "summary.md" else "error" if safe.name.lower() == "report.md" else "document"
                reports.append(
                    {
                        "report_id": report_id_for(safe),
                        "path": rel_path(safe),
                        "run_id": run_id,
                        "name": safe.name,
                        "type": report_type,
                        "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat().replace("+00:00", "Z"),
                        "bytes": stat.st_size,
                    }
                )
        reports.sort(key=lambda item: (item.get("run_id") or "", item["path"]), reverse=True)
        return {"count": len(reports), "reports": reports}

    def get_report(self, report_id: str) -> dict[str, Any]:
        path = path_for_report_id(report_id)
        content = path.read_text(encoding="utf-8")
        return {
            "report_id": report_id_for(path),
            "path": rel_path(path),
            "content_type": "text/markdown; charset=utf-8",
            "markdown": content,
            "bytes": len(content.encode("utf-8")),
        }

    def injected_host_state(self) -> dict[str, Any]:
        state = read_json_file(HOST_STATE_PATH, {}) if HOST_STATE_PATH.exists() else {}
        return state if isinstance(state, dict) else {}

    def call_host_runner(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        base_url = host_runner_url()
        if not base_url:
            raise ApiError(503, "Host runner URL is not configured.")
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            f"{base_url}{path}",
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urlopen(request, timeout=float(os.environ.get("COPILOT_ADMIN_HOST_RUNNER_TIMEOUT_SECONDS", "5"))) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            raise ApiError(exc.code, "Host runner request failed.", {"path": path, "body": exc.read().decode("utf-8", errors="replace")}) from exc
        except URLError as exc:
            raise ApiError(503, "Host runner is unavailable.", {"path": path, "reason": str(exc.reason)}) from exc
        except TimeoutError as exc:
            raise ApiError(504, "Host runner request timed out.", {"path": path}) from exc
        try:
            decoded = json.loads(body) if body else {}
        except json.JSONDecodeError as exc:
            raise ApiError(502, "Host runner returned invalid JSON.", {"path": path, "body": body[:1000]}) from exc
        if not isinstance(decoded, dict):
            raise ApiError(502, "Host runner response must be a JSON object.", {"path": path})
        return decoded

    def host_runner_status_snapshot(self) -> dict[str, Any] | None:
        if not host_runner_url():
            return None
        try:
            snapshot = self.call_host_runner("GET", "/status")
        except ApiError as exc:
            self.log("warn", "backend", "host_runner_unavailable", status="unavailable", details={"error": exc.message, "details": exc.details})
            return {"status": "unavailable", "error": exc.message, "details": exc.details, "source": host_runner_url()}
        snapshot["source"] = host_runner_url()
        return snapshot

    def copilot_session(self, snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
        injected = self.injected_host_state()
        if isinstance(injected.get("copilot_state"), dict):
            state = dict(injected["copilot_state"])
            state["source"] = "injected"
        elif snapshot is not None or (snapshot := self.host_runner_status_snapshot()) is not None:
            state = dict(snapshot.get("copilot_session") or {})
            state.setdefault("status", "unknown")
            state["source"] = snapshot.get("source")
        elif not is_test_env(self.env) and NODE_PTY_STATE_PATH.is_file():
            state = read_json_file(NODE_PTY_STATE_PATH, {})
            if isinstance(state, dict):
                state = dict(state)
                window_state = read_optional_json_file(NODE_PTY_WINDOW_STATE_PATH, {})
                if isinstance(window_state, dict):
                    state.setdefault("visible_window_expected", bool(window_state.get("visible_window_expected", not bool(window_state.get("hidden")))))
                    state.setdefault("startup_model", window_state.get("startup_model"))
                    state.setdefault("startup_allow_all", bool(window_state.get("startup_allow_all")))
                    state.setdefault("window_state_path", str(NODE_PTY_WINDOW_STATE_PATH))
                wrapper_running = is_process_running(state.get("wrapper_pid"))
                state["running"] = wrapper_running
                if state.get("status") in {"running", "user_input_required"} and not wrapper_running:
                    state["status"] = "not_running"
                    state["user_input_required"] = False
                    state["user_input_reason"] = None
                if not wrapper_running:
                    state["visible_window_expected"] = False
                state["source"] = rel_path(NODE_PTY_STATE_PATH)
            else:
                state = {"status": "invalid", "source": rel_path(NODE_PTY_STATE_PATH)}
        else:
            source = "test-isolated" if is_test_env(self.env) else rel_path(NODE_PTY_STATE_PATH)
            state = {"status": "missing", "source": source, "user_input_required": False}
        transcript_path_value = state.get("transcript_path")
        if transcript_path_value and not state.get("last_output_tail"):
            try:
                transcript_path = ensure_child(self.repo_root, Path(transcript_path_value))
                if transcript_path.is_file():
                    state["last_output_tail"] = transcript_path.read_text(encoding="utf-8", errors="replace")[-4000:]
            except Exception:
                state.setdefault("last_output_tail", "")
        return state

    def copilot_console(self, snapshot: dict[str, Any] | None = None, query: dict[str, list[str]] | None = None) -> dict[str, Any]:
        session = self.copilot_session(snapshot)
        transcript = str(session.get("last_output_tail") or "")
        status = str(session.get("status", "unknown"))
        current_model = session.get("current_model") or session.get("model_hint")
        configured_model = session.get("startup_model")
        model_verified = bool(session.get("model_verified") or session.get("current_model"))
        permissions_allow_all_verified = bool(
            session.get("permissions_allow_all")
            or session.get("allow_all_verified")
            or (session.get("startup_allow_all") and session.get("startup_commands_sent"))
        )
        permissions_hint = session.get("permissions_hint") or ("allow-all" if permissions_allow_all_verified else None)
        query = query or {}
        requested_cursor = self._int_query_value(query, "cursor")
        requested_limit = self._int_query_value(query, "limit") or DEFAULT_CONSOLE_TAIL_BYTES
        limit = max(1024, min(requested_limit, MAX_CONSOLE_DELTA_BYTES))
        transcript_payload = self.read_console_transcript(session, requested_cursor, limit)
        input_queue = session.get("input_queue") or {}
        queue_dir_value = session.get("input_queue_dir") or input_queue.get("queue_dir")
        if queue_dir_value:
            try:
                queue_dir = ensure_child(self.repo_root, Path(queue_dir_value))
                if queue_dir.is_dir():
                    files = sorted(path.name for path in queue_dir.iterdir() if path.is_file())
                    input_queue = {
                        **input_queue,
                        "queue_dir": str(queue_dir),
                        "pending": len([name for name in files if name.endswith(".json")]),
                        "done": len([name for name in files if name.endswith(".json.done")]),
                        "invalid": len([name for name in files if name.endswith(".json.invalid")]),
                        "skipped": len([name for name in files if name.endswith(".json.skipped")]),
                        "latest_files": files[-10:],
                    }
            except Exception:
                input_queue = dict(input_queue)
        return {
            "status": status,
            "running": bool(session.get("running")) or status in {"running", "user_input_required"},
            "visible_window_expected": bool(session.get("visible_window_expected")),
            "updated_at": session.get("updated_at"),
            "server_timestamp": utc_now(),
            "heartbeat": {
                "server_timestamp": utc_now(),
                "session_updated_at": session.get("updated_at"),
                "transcript_size": transcript_payload["size"],
                "next_cursor": transcript_payload["next_cursor"],
            },
            "started_at": session.get("started_at"),
            "user_input_required": bool(session.get("user_input_required")),
            "user_input_reason": session.get("user_input_reason"),
            "transcript_tail": transcript_payload["text"] or transcript[-limit:],
            "transcript": transcript_payload,
            "last_injected_text": session.get("last_injected_text", ""),
            "last_injected_at": session.get("last_injected_at"),
            "input_queue": input_queue,
            "source": session.get("source"),
            "model_hint": current_model,
            "configured_model": configured_model,
            "model_verified": model_verified,
            "permissions_hint": permissions_hint,
            "permissions_verified": permissions_allow_all_verified,
        }

    def _int_query_value(self, query: dict[str, list[str]], key: str) -> int | None:
        values = query.get(key) or []
        if not values:
            return None
        try:
            value = int(values[0])
        except (TypeError, ValueError) as exc:
            raise ApiError(400, f"{key} must be an integer.") from exc
        if value < 0:
            raise ApiError(400, f"{key} must be non-negative.")
        return value

    def read_console_transcript(self, session: dict[str, Any], cursor: int | None, limit: int) -> dict[str, Any]:
        transcript_path_value = session.get("transcript_path")
        fallback = str(session.get("last_output_tail") or "")
        if not transcript_path_value:
            encoded = fallback.encode("utf-8", errors="replace")
            return {
                "mode": "fallback_tail",
                "text": fallback[-limit:],
                "cursor": None,
                "next_cursor": len(encoded),
                "size": len(encoded),
                "truncated": len(encoded) > limit,
                "source": session.get("source"),
            }
        try:
            transcript_path = ensure_child(self.repo_root, Path(transcript_path_value))
        except Exception:
            encoded = fallback.encode("utf-8", errors="replace")
            return {
                "mode": "fallback_tail",
                "text": fallback[-limit:],
                "cursor": None,
                "next_cursor": len(encoded),
                "size": len(encoded),
                "truncated": len(encoded) > limit,
                "source": session.get("source"),
            }
        if not transcript_path.is_file():
            return {"mode": "missing", "text": "", "cursor": cursor, "next_cursor": cursor or 0, "size": 0, "truncated": False, "source": str(transcript_path)}
        size = transcript_path.stat().st_size
        if cursor is None:
            start = max(0, size - limit)
            mode = "tail"
            truncated = start > 0
        elif cursor > size:
            start = max(0, size - limit)
            mode = "reset_tail"
            truncated = True
        else:
            start = cursor
            mode = "delta"
            truncated = (size - start) > limit
        read_start = max(0, size - limit) if truncated else start
        with transcript_path.open("rb") as handle:
            handle.seek(read_start)
            text = handle.read(limit).decode("utf-8", errors="replace")
        return {
            "mode": mode,
            "text": text,
            "cursor": read_start,
            "next_cursor": size,
            "size": size,
            "truncated": truncated,
            "source": str(transcript_path),
        }

    def browser_session(self, snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
        injected = self.injected_host_state()
        if isinstance(injected.get("browser_state"), dict):
            state = dict(injected["browser_state"])
            state["source"] = "injected"
            return state
        if snapshot is not None or (snapshot := self.host_runner_status_snapshot()) is not None:
            state = dict(snapshot.get("browser_session") or {})
            state.setdefault("status", "unknown")
            state["source"] = snapshot.get("source")
            return state
        return {"status": "unknown", "debug_port": None}

    def current_mode(self) -> str:
        data = read_json_file(MODE_PATH, {}) if MODE_PATH.exists() else {}
        if isinstance(data, dict):
            return str(data.get("mode") or "unset")
        return "unset"

    def set_current_mode(self, mode: str) -> None:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        MODE_PATH.write_text(json.dumps({"mode": mode, "updated_at": utc_now()}, ensure_ascii=False, indent=2), encoding="utf-8")

    def host_runner(self, snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
        injected = self.injected_host_state()
        if isinstance(injected.get("host_runner_state"), dict):
            state = dict(injected["host_runner_state"])
            state["source"] = "injected"
            return state
        if snapshot is not None or (snapshot := self.host_runner_status_snapshot()) is not None:
            state = dict(snapshot.get("host_runner") or {})
            state.setdefault("status", snapshot.get("status", "unknown"))
            state["source"] = snapshot.get("source")
            return state
        return {"status": "unknown", "details": "Host runner integration is file-state based in this backend."}

    def status(self) -> dict[str, Any]:
        jobs = self._read_jobs()
        runner_snapshot = self.host_runner_status_snapshot()
        copilot = self.copilot_session(runner_snapshot)
        browser = self.browser_session(runner_snapshot)
        diode = "red"
        if any(job["status"] in ACTIVE_STATUSES for job in jobs):
            diode = "yellow"
        elif any(job["status"] == "completed_unopened" for job in jobs):
            diode = "green"
        latest_job = jobs[-1] if jobs else None
        return {
            "backend": {"status": "ok", "version": BACKEND_VERSION, "started_at": self.started_at, "env": self.env},
            "host_runner": self.host_runner(runner_snapshot),
            "copilot_session": copilot,
            "browser_session": browser,
            "copilot": copilot,
            "browser": browser,
            "mode": self.current_mode(),
            "status_diode": diode,
            "latest_job": latest_job,
            "unopened_results": [job for job in jobs if job["status"] == "completed_unopened"],
        }

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "version": BACKEND_VERSION,
            "started_at": self.started_at,
            "uptime_hint": "Process-local uptime starts at started_at.",
            "configuration": {
                "repo_root": str(self.repo_root),
                "env": self.env,
                "state_dir": rel_path(STATE_DIR),
                "log_dir": rel_path(LOG_DIR),
                "frontend_dir": str(FRONTEND_DIR),
            },
        }

    def build_prompt(self, job_type: str, payload: dict[str, Any]) -> str:
        if job_type == "set_mode":
            mode = normalize_mode(payload.get("mode"))
            if mode is None:
                raise ApiError(400, "mode must be 'learning' or 'testing'.")
            return f"Gå in i {mode} mode för SPS regressioner. Bekräfta kort när läget är aktivt."
        if job_type == "run_regression":
            catalog_key = payload.get("catalog_key")
            test_id = payload.get("test_id")
            if test_id and not catalog_key:
                for test in self.parse_catalog()["tests"]:
                    if test.get("test_id") == test_id:
                        catalog_key = test.get("catalog_key")
                        break
            if catalog_key:
                if test_id:
                    return f"Kör regressionstest {catalog_key} ({test_id}). Följ repositoryts Regression Mode-regler."
                return f"Kör regressionstest {catalog_key}. Följ repositoryts Regression Mode-regler."
            if test_id:
                return f"Kör regressionstest {test_id}. Följ repositoryts Regression Mode-regler."
            return "Kör befintliga regressionstester. Följ repositoryts Regression Mode-regler."
        if job_type == "session_start":
            return "Starta eller säkerställ SPS Copilot-admin host runner, node-pty Copilot-session och collaborative browser enligt repo-reglerna."
        return str(payload.get("prompt") or payload.get("command") or "").strip()

    def dispatch_to_node_pty(self, job: dict[str, Any]) -> dict[str, Any]:
        if host_runner_url():
            if job["type"] == "session_start":
                payload = dict(job["payload"])
                payload.setdefault("restart_existing", False)
                payload.setdefault("startup_model", "gpt-5-mini")
                response = self.call_host_runner("POST", "/api/session/start", payload)
                return {"dispatched": True, "target": "host-runner", "response": response}
            response = self.call_host_runner("POST", "/copilot/input", {"text": job["prompt"], "job_id": job["job_id"], "trace_id": job["trace_id"]})
            return {"dispatched": response.get("status") not in {"failed", "error"}, "target": "host-runner", "response": response}

        copilot = self.copilot_session()
        queue_dir_value = copilot.get("input_queue_dir")
        if not queue_dir_value or copilot.get("status") not in {"running", "user_input_required"}:
            return {"dispatched": False, "reason": "node-pty input queue is not available"}
        queue_dir = ensure_child(self.repo_root, Path(queue_dir_value))
        queue_dir.mkdir(parents=True, exist_ok=True)
        request_path = queue_dir / f"{utc_now().replace(':', '').replace('-', '').replace('.', '')}-{job['job_id']}.json"
        request = {
            "text": job["prompt"],
            "submit": job["payload"].get("submit") is not False,
            "clear_line": bool(job["payload"].get("clear_line")),
            "job_id": job["job_id"],
            "trace_id": job["trace_id"],
        }
        request_path.write_text(json.dumps(request, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"dispatched": True, "queue_file": rel_path(request_path)}

    def send_copilot_console_input(self, payload: dict[str, Any], trace_id: str | None = None) -> dict[str, Any]:
        text = str(payload.get("text") if payload.get("text") is not None else payload.get("prompt") or "")
        if not text.strip() and text not in {"\t", "\x1b"}:
            raise ApiError(400, "text is required.")
        submit = payload.get("submit") is not False
        job_id = payload.get("job_id") or f"console-{uuid.uuid4().hex}"
        request = {
            "job_id": job_id,
            "trace_id": trace_id or payload.get("trace_id") or uuid.uuid4().hex,
            "type": "copilot_console_input",
            "prompt": text,
            "payload": {"text": text, "submit": submit, "clear_line": payload.get("clear_line") is not False},
        }
        if host_runner_url():
            response = self.call_host_runner("POST", "/copilot/input", {"text": text, "submit": submit, "clear_line": request["payload"]["clear_line"], "job_id": job_id, "trace_id": request["trace_id"]})
            result = {"accepted": response.get("status") not in {"failed", "error"}, "target": "host-runner", "response": response, "job_id": job_id}
        else:
            dispatch = self.dispatch_to_node_pty(request)
            result = {"accepted": bool(dispatch.get("dispatched")), "target": "local-node-pty", "response": dispatch, "job_id": job_id}
        if not result["accepted"]:
            raise ApiError(409, "Copilot console input could not be queued.", {"dispatch": result})
        self.log("info", "backend", "copilot_console_input_sent", trace_id=request["trace_id"], job_id=job_id, status="queued", details={"submit": submit, "target": result["target"]})
        result["console"] = self.copilot_console()
        return result

    def create_job(self, job_type: str, payload: dict[str, Any], trace_id: str | None = None) -> dict[str, Any]:
        prompt = self.build_prompt(job_type, payload)
        if not prompt:
            raise ApiError(400, "A prompt or known job type is required.")
        with self._lock:
            jobs = self._read_jobs()
            job_id = uuid.uuid4().hex
            now = utc_now()
            job = {
                "job_id": job_id,
                "trace_id": trace_id or payload.get("trace_id") or uuid.uuid4().hex,
                "type": job_type,
                "status": "queued",
                "created_at": now,
                "updated_at": now,
                "opened_at": None,
                "payload": payload,
                "prompt": prompt,
                "dispatch": None,
                "result": None,
                "output_tail": "",
            }
            try:
                dispatch = self.dispatch_to_node_pty(job)
            except ApiError as exc:
                dispatch = {"dispatched": False, "target": "host-runner", "reason": exc.message, "details": exc.details}
            job["dispatch"] = dispatch
            if dispatch.get("dispatched"):
                job["status"] = "running"
                job["updated_at"] = utc_now()
            elif host_runner_url():
                job["status"] = "failed"
                job["updated_at"] = utc_now()
                job["result"] = {"error": dispatch.get("reason"), "details": dispatch.get("details", {})}
            jobs.append(job)
            self._write_jobs(jobs)
            if job_type == "set_mode":
                mode = normalize_mode(payload.get("mode"))
                if mode:
                    self.set_current_mode(mode)
        self.log("info", "backend", "job_created", trace_id=job["trace_id"], job_id=job_id, status=job["status"], details={"type": job_type})
        if job["status"] == "running":
            self.log("info", "backend", "job_dispatched", trace_id=job["trace_id"], job_id=job_id, status="running", details=job["dispatch"])
        return job

    def list_jobs(self, query: dict[str, list[str]]) -> dict[str, Any]:
        jobs = self._read_jobs()
        status_filter = set(query.get("status", []))
        type_filter = set(query.get("type", []))
        if status_filter:
            jobs = [job for job in jobs if job.get("status") in status_filter]
        if type_filter:
            jobs = [job for job in jobs if job.get("type") in type_filter]
        jobs.sort(key=lambda job: job.get("created_at", ""), reverse=True)
        return {"count": len(jobs), "jobs": jobs}

    def get_job(self, job_id: str) -> dict[str, Any]:
        for job in self._read_jobs():
            if job.get("job_id") == job_id:
                return job
        raise ApiError(404, "Job not found.")

    def open_job(self, job_id: str, trace_id: str | None = None) -> dict[str, Any]:
        with self._lock:
            jobs = self._read_jobs()
            for job in jobs:
                if job.get("job_id") == job_id:
                    if job["status"] == "completed_unopened":
                        job["status"] = "completed_opened"
                        job["opened_at"] = utc_now()
                        job["updated_at"] = job["opened_at"]
                        self._write_jobs(jobs)
                        self.log("info", "backend", "job_status_changed", trace_id=trace_id or job["trace_id"], job_id=job_id, status=job["status"])
                    return job
        raise ApiError(404, "Job not found.")

    def ingest_frontend_event(self, payload: dict[str, Any], trace_id: str | None = None) -> dict[str, Any]:
        event = str(payload.get("event") or "frontend_event_received")
        record = self.log(
            str(payload.get("level") or "info"),
            "frontend",
            event,
            trace_id=trace_id or payload.get("trace_id"),
            job_id=payload.get("job_id"),
            status=payload.get("status"),
            details={"frontend": payload},
        )
        self.log("info", "backend", "frontend_event_received", trace_id=record["trace_id"], job_id=payload.get("job_id"), status=payload.get("status"))
        return {"accepted": True, "trace_id": record["trace_id"]}

    def assert_test_api_allowed(self) -> None:
        if self.env not in {"development", "dev", "test", "testing"} and os.environ.get("COPILOT_ADMIN_ENABLE_TEST_API") != "true":
            raise ApiError(403, "Test/control API is disabled outside development/test.")

    def test_reset(self) -> dict[str, Any]:
        self.assert_test_api_allowed()
        with self._lock:
            self._write_jobs([])
            if HOST_STATE_PATH.exists():
                HOST_STATE_PATH.unlink()
            if MODE_PATH.exists():
                MODE_PATH.unlink()
        self.log("info", "backend", "test_state_reset")
        return {"reset": True}

    def inject_host_state(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.assert_test_api_allowed()
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        state = {"updated_at": utc_now(), **payload}
        HOST_STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        updates = payload.get("job_updates") or []
        if updates:
            with self._lock:
                jobs = self._read_jobs()
                by_id = {job.get("job_id"): job for job in jobs}
                for update in updates:
                    job_id = update.get("job_id")
                    status = update.get("status")
                    if status and status not in JOB_STATUSES:
                        raise ApiError(400, f"Invalid job status: {status}")
                    if job_id in by_id:
                        by_id[job_id].update(update)
                        by_id[job_id]["updated_at"] = utc_now()
                self._write_jobs(jobs)
        self.log("info", "backend", "host_state_injected", details={"keys": sorted(payload.keys())})
        return {"injected": True, "state_path": rel_path(HOST_STATE_PATH)}


APP = ControlPlaneBackend()


class Handler(BaseHTTPRequestHandler):
    server_version = "CopilotAdminControlPlane/0.1"

    def log_message(self, format: str, *args: Any) -> None:
        return

    @property
    def app(self) -> ControlPlaneBackend:
        return self.server.app  # type: ignore[attr-defined]

    def read_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length == 0:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ApiError(400, "Request body must be valid JSON.") from exc

    def send_json(self, status: int, payload: Any) -> None:
        encoded = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def handle_error(self, exc: Exception) -> None:
        if isinstance(exc, ApiError):
            self.send_json(exc.status_code, {"error": exc.message, "details": exc.details})
            return
        self.app.log("error", "backend", "request_failed", details={"message": str(exc)})
        self.send_json(500, {"error": "Internal server error."})

    def do_GET(self) -> None:
        try:
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/") or "/"
            if path == "/":
                self.send_static("index.html")
            elif path in {"/app.js", "/styles.css"}:
                self.send_static(path.lstrip("/"))
            elif path == "/api/health":
                self.send_json(200, self.app.health())
            elif path == "/api/status":
                self.send_json(200, self.app.status())
            elif path == "/api/session/copilot":
                self.send_json(200, self.app.copilot_session())
            elif path == "/api/copilot/console":
                self.send_json(200, self.app.copilot_console(query=parse_qs(parsed.query)))
            elif path == "/api/session/browser":
                self.send_json(200, self.app.browser_session())
            elif path == "/api/regression/tests":
                self.send_json(200, self.app.parse_catalog())
            elif path == "/api/regression/mermaid":
                self.send_json(200, self.app.mermaid())
            elif path == "/api/reports":
                self.send_json(200, self.app.list_reports())
            elif path.startswith("/api/reports/"):
                self.send_json(200, self.app.get_report(unquote(path.removeprefix("/api/reports/"))))
            elif path == "/api/jobs":
                self.send_json(200, self.app.list_jobs(parse_qs(parsed.query)))
            elif path.startswith("/api/jobs/"):
                self.send_json(200, self.app.get_job(unquote(path.removeprefix("/api/jobs/"))))
            else:
                raise ApiError(404, "Endpoint not found.")
        except Exception as exc:
            self.handle_error(exc)

    def send_static(self, relative_path: str) -> None:
        static_path = ensure_child(FRONTEND_DIR, FRONTEND_DIR / relative_path)
        if not static_path.is_file():
            raise ApiError(404, "Frontend asset not found.")
        data = static_path.read_bytes()
        content_type = mimetypes.guess_type(static_path.name)[0] or "application/octet-stream"
        if static_path.suffix.lower() in {".html", ".js", ".css"}:
            content_type += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        try:
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/") or "/"
            body = self.read_body()
            trace_id = self.headers.get("X-Trace-Id") or body.get("trace_id")
            if path == "/api/jobs":
                self.send_json(201, self.app.create_job(str(body.get("type") or "custom"), body, trace_id))
            elif path == "/api/copilot/mode":
                self.send_json(201, self.app.create_job("set_mode", body, trace_id))
            elif path == "/api/copilot/input":
                self.send_json(202, self.app.send_copilot_console_input(body, trace_id))
            elif path == "/api/regression/run":
                self.send_json(201, self.app.create_job("run_regression", body, trace_id))
            elif path == "/api/frontend/events":
                self.send_json(202, self.app.ingest_frontend_event(body, trace_id))
            elif path == "/api/test/reset":
                self.send_json(200, self.app.test_reset())
            elif path == "/api/test/inject-host-state":
                self.send_json(200, self.app.inject_host_state(body))
            elif path.startswith("/api/jobs/") and path.endswith("/open"):
                job_id = unquote(path.removeprefix("/api/jobs/").removesuffix("/open"))
                self.send_json(200, self.app.open_job(job_id, trace_id))
            elif path == "/api/session/start":
                self.send_json(201, self.app.create_job("session_start", body, trace_id))
            else:
                raise ApiError(404, "Endpoint not found.")
        except Exception as exc:
            self.handle_error(exc)


def make_server(host: str, port: int, app: ControlPlaneBackend = APP) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), Handler)
    server.app = app  # type: ignore[attr-defined]
    return server


def main() -> int:
    parser = argparse.ArgumentParser(description="Copilot-admin control plane backend")
    parser.add_argument("--host", default=os.environ.get("COPILOT_ADMIN_BACKEND_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("COPILOT_ADMIN_BACKEND_PORT", "8765")))
    args = parser.parse_args()
    server = make_server(args.host, args.port)
    APP.log("info", "backend", "backend_listening", details={"host": args.host, "port": args.port})
    print(f"Copilot-admin backend listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        APP.log("info", "backend", "backend_stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
