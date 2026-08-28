from __future__ import annotations

import argparse
import base64
import ctypes
import json
import mimetypes
import os
import re
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import parse_qs, unquote, urlparse

sys.path.insert(0, str((Path(__file__).resolve().parents[2] / "copilot_admin_runner").resolve()))
from transport_db import enqueue_input, get_session_state, latest_trace_events, queue_snapshot, record_trace_event, transport_db_path, upsert_session_state


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
NODE_PTY_STATE_DIR = Path(
    os.environ.get("COPILOT_ADMIN_RUNNER_STATE_DIR", REPO_ROOT / "tmp" / "copilot_admin_runner_state")
).resolve()
NODE_PTY_STATE_PATH = NODE_PTY_STATE_DIR / "node-pty-copilot-session.json"
NODE_PTY_WINDOW_STATE_PATH = NODE_PTY_STATE_DIR / "node-pty-copilot-window.json"
NODE_PTY_SESSION_ID = os.environ.get("COPILOT_ADMIN_RUNNER_SESSION_ID", "node-pty-copilot")
STATE_DIR = REPO_ROOT / "tmp" / "copilot_admin_control_plane" / "state"
LOG_DIR = REPO_ROOT / "tmp" / "copilot_admin_control_plane" / "logs"
JOBS_PATH = STATE_DIR / "jobs.json"
HOST_STATE_PATH = STATE_DIR / "injected-host-state.json"
MODE_PATH = STATE_DIR / "current-mode.json"
BACKEND_VERSION = "0.1.0"
DEFAULT_CONSOLE_TAIL_BYTES = 12000
MAX_CONSOLE_DELTA_BYTES = 65536
DEFAULT_HOST_RUNNER_URL = "http://127.0.0.1:8766"
CONSOLE_EVENT_POLL_SECONDS = 0.03
FRONTEND_ROUTES = {
    "dashboard": "dashboard",
    "manualer": "manualer",
    "ai-console": "ai-console",
    "ai-konsolen": "ai-console",
    "regressioner": "regressioner",
    "mermaid": "mermaid",
    "rapporter": "rapporter",
    "jobb": "jobb",
    "loggar": "loggar",
}
JOB_STATUSES = {
    "queued",
    "running",
    "user_input_required",
    "completed_unopened",
    "completed_opened",
    "failed",
}
ACTIVE_STATUSES = {"queued", "running", "user_input_required"}
AI_CONSOLE_STANDARD_INSTRUCTION = (
    "Om instruktionen är oklar eller otydlig ställ klargörande frågor, "
    "om instruktionen påverkar befintliga tester måste användaren informeras om konsekvenserna av den ändringen."
)


def current_transport_db_path() -> Path:
    return transport_db_path(NODE_PTY_STATE_DIR)


def host_runner_url() -> str | None:
    env_name = os.environ.get("COPILOT_ADMIN_ENV", "").lower()
    if env_name in {"test", "testing"} and os.environ.get("COPILOT_ADMIN_ALLOW_TEST_HOST_RUNNER") != "1":
        return None
    value = os.environ.get("COPILOT_ADMIN_HOST_RUNNER_URL", "").strip().rstrip("/")
    if value:
        return value
    if os.environ.get("COPILOT_ADMIN_DISABLE_DEFAULT_HOST_RUNNER") == "1":
        return None
    return os.environ.get("COPILOT_ADMIN_DEFAULT_HOST_RUNNER_URL", DEFAULT_HOST_RUNNER_URL).strip().rstrip("/") or None


def is_test_env(value: str | None = None) -> bool:
    return (value if value is not None else os.environ.get("COPILOT_ADMIN_ENV", "")).lower() in {"test", "testing"}


def normalize_mode(value: Any) -> str | None:
    text = str(value or "").strip().lower().replace("_", " ")
    if text in {"learning", "learning mode"}:
        return "learning"
    if text in {"testing", "testing mode"}:
        return "testing"
    return None


def is_ai_console_special_input(text: str) -> bool:
    raw = str(text or "")
    stripped = raw.strip()
    return raw in {"\t", "\x1b"} or stripped == "\x1b" or stripped.startswith("/")


def with_ai_console_standard_instruction(text: str) -> str:
    if is_ai_console_special_input(text):
        return text
    if AI_CONSOLE_STANDARD_INSTRUCTION in text:
        return text
    return f"{text.rstrip()}\n\nStandardinstruktion: {AI_CONSOLE_STANDARD_INSTRUCTION}"


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


def write_json_atomically(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(path)
    finally:
        tmp_path.unlink(missing_ok=True)


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
    attempts = 3
    last_error: json.JSONDecodeError | None = None
    for attempt in range(attempts):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            last_error = exc
            if attempt == attempts - 1:
                raise ApiError(500, f"Invalid JSON state file: {rel_path(path)}") from exc
            time.sleep(0.02)
    raise ApiError(500, f"Invalid JSON state file: {rel_path(path)}") from last_error


def read_optional_json_file(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default


def frontend_route_version() -> str:
    paths = [FRONTEND_DIR / "index.html", FRONTEND_DIR / "app.js", FRONTEND_DIR / "styles.css"]
    latest_ns = max((path.stat().st_mtime_ns for path in paths if path.is_file()), default=0)
    return f"v{latest_ns:x}"


def normalize_frontend_route(path: str) -> tuple[str, str | None] | None:
    parts = [unquote(part).strip() for part in path.strip("/").split("/") if part.strip()]
    if not parts:
        return ("dashboard", None)
    route = FRONTEND_ROUTES.get(parts[0].casefold())
    if route is None or len(parts) > 2:
        return None
    return (route, parts[1] if len(parts) == 2 else None)


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
        write_json_atomically(JOBS_PATH, jobs)

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
            catalog_key = cells[0].strip("`")
            file_path = cells[4].strip("`")
            dependency_keys = []
            if dependency_text != "-":
                dependency_keys = [part.strip() for part in dependency_text.split("->") if part.strip() and part.strip() != catalog_key]
            entries.append(
                {
                    "catalog_key": catalog_key,
                    "dependency": dependency_text,
                    "dependencies": dependency_keys,
                    "dependency_keys": dependency_keys,
                    "test_id": cells[2].strip("`"),
                    "summary": cells[3],
                    "file": file_path,
                    "file_path": file_path,
                    "test_type": self.test_type_for(REPO_ROOT / file_path),
                }
            )
        test_id_by_key = {entry["catalog_key"]: entry["test_id"] for entry in entries}
        for entry in entries:
            entry["dependency_test_ids"] = [
                test_id_by_key[key] for key in entry["dependency_keys"] if key in test_id_by_key
            ]
            entry["dependency_mode"] = "required" if entry["dependency_keys"] else "none"
        return {"path": rel_path(CATALOG_PATH), "count": len(entries), "tests": entries}

    def test_type_for(self, path: Path) -> str:
        if not path.is_file():
            return "unknown"
        text = path.read_text(encoding="utf-8")
        match = re.search(r"^## Typ\s*$\n+(.*?)(?=^\#\# |\Z)", text, flags=re.MULTILINE | re.DOTALL)
        typ = " ".join(match.group(1).split()).lower() if match else ""
        if "ui" in typ or "shared-browser" in typ or "browser" in typ:
            return "ui-regression"
        if "struktur" in typ or "structure" in typ or "runtime" in typ:
            return "structure-regression"
        return "regression"

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
        timeout_seconds = self.host_runner_timeout_seconds(path)
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            f"{base_url}{path}",
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
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

    def host_runner_timeout_seconds(self, path: str) -> float:
        configured = os.environ.get("COPILOT_ADMIN_HOST_RUNNER_TIMEOUT_SECONDS")
        if configured:
            return float(configured)
        if path == "/api/session/start":
            return 75.0
        if path == "/status":
            return 20.0
        return 10.0

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
        elif not is_test_env(self.env) and (db_state := get_session_state(current_transport_db_path(), session_id=NODE_PTY_SESSION_ID)) is not None:
            state = dict(db_state)
            if isinstance(state, dict):
                wrapper_running = is_process_running(state.get("wrapper_pid"))
                launcher_running = is_process_running(state.get("launcher_pid"))
                state["running"] = wrapper_running
                if state.get("status") in {"running", "user_input_required"} and not wrapper_running:
                    state["status"] = "not_running"
                    state["user_input_required"] = False
                    state["user_input_reason"] = None
                if not wrapper_running and not launcher_running:
                    state["visible_window_expected"] = False
                state.setdefault("state_storage", "sqlite")
                state.setdefault("state_db_path", str(current_transport_db_path()))
                state.setdefault("state_path", str(current_transport_db_path()))
                state.setdefault("window_state_path", str(current_transport_db_path()))
                state["source"] = str(current_transport_db_path())
            else:
                state = {"status": "invalid", "source": str(current_transport_db_path())}
        elif snapshot is not None or (snapshot := self.host_runner_status_snapshot()) is not None:
            state = dict(snapshot.get("copilot_session") or {})
            state.setdefault("status", "unknown")
            state["source"] = snapshot.get("source")
        else:
            source = "test-isolated" if is_test_env(self.env) else str(current_transport_db_path())
            state = {"status": "missing", "source": source, "user_input_required": False}
        transcript_path_value = state.get("transcript_path")
        if transcript_path_value and not state.get("last_output_tail"):
            try:
                transcript_path = ensure_child(self.repo_root, Path(transcript_path_value))
                if transcript_path.is_file():
                    state["last_output_tail"] = transcript_path.read_text(encoding="utf-8", errors="replace")[-4000:]
            except Exception:
                state.setdefault("last_output_tail", "")
        state.setdefault("input_queue_db_path", str(current_transport_db_path()))
        state.setdefault("trace_db_path", str(current_transport_db_path()))
        return state

    def ai_console(self, snapshot: dict[str, Any] | None = None, query: dict[str, list[str]] | None = None) -> dict[str, Any]:
        session = self.copilot_session(snapshot)
        transcript = str(session.get("last_output_tail") or "")
        status = str(session.get("status", "unknown"))
        repo_root = str(session.get("repo_root") or self.repo_root)
        project_name = Path(repo_root).name if repo_root else None
        current_model = session.get("current_model") or session.get("model_hint")
        configured_model = session.get("startup_model")
        model_verified = bool(session.get("model_verified") or session.get("current_model"))
        directory_trust_requested = bool(session.get("directory_trust_requested"))
        directory_trust_verified = bool(session.get("directory_trust_verified"))
        permissions_allow_all_requested = bool(
            session.get("startup_allow_all_requested")
            or session.get("startup_allow_all")
            or session.get("allow_all_verified")
        )
        permissions_allow_all_verified = bool(
            session.get("permissions_allow_all")
            or session.get("allow_all_verified")
        )
        permissions_verified = permissions_allow_all_verified and (directory_trust_verified or not directory_trust_requested)
        permissions_hint = session.get("permissions_hint") or ("allow-all" if permissions_verified or permissions_allow_all_requested else None)
        command_ready = status == "running" and not bool(session.get("user_input_required")) and permissions_verified
        query = query or {}
        include_trace = str((query.get("include_trace") or ["1"])[0]).strip().lower() not in {"0", "false", "no"}
        requested_cursor = self._int_query_value(query, "cursor")
        requested_limit = self._int_query_value(query, "limit") or DEFAULT_CONSOLE_TAIL_BYTES
        limit = max(1024, min(requested_limit, MAX_CONSOLE_DELTA_BYTES))
        transcript_payload = self.read_console_transcript(session, requested_cursor, limit)
        input_queue = session.get("input_queue") or {}
        db_path_value = session.get("input_queue_db_path") or input_queue.get("db_path")
        queue_dir_value = session.get("input_queue_dir") or input_queue.get("queue_dir")
        if db_path_value:
            try:
                db_path = ensure_child(self.repo_root, Path(db_path_value))
                input_queue = {**input_queue, **queue_snapshot(db_path)}
            except Exception:
                input_queue = dict(input_queue)
        elif queue_dir_value:
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
            "transcript_path": session.get("transcript_path"),
            "last_injected_text": session.get("last_injected_text", ""),
            "last_injected_at": session.get("last_injected_at"),
            "last_input_client_sent_at": session.get("last_input_client_sent_at"),
            "last_input_backend_queued_at": session.get("last_input_backend_queued_at"),
            "last_input_host_runner_received_at": session.get("last_input_host_runner_received_at"),
            "last_input_host_runner_queued_at": session.get("last_input_host_runner_queued_at"),
            "last_input_queue_file_seen_at": session.get("last_input_queue_file_seen_at"),
            "last_input_pty_write_at": session.get("last_input_pty_write_at"),
            "last_input_trace_id": session.get("last_input_trace_id"),
            "last_input_job_id": session.get("last_input_job_id"),
            "last_output_chunk_at": session.get("last_output_chunk_at"),
            "last_output_chunk_bytes": session.get("last_output_chunk_bytes"),
            "last_output_sequence": session.get("last_output_sequence"),
            "last_output_transcript_size": session.get("last_output_transcript_size"),
            "input_queue": input_queue,
            "input_queue_db_path": session.get("input_queue_db_path") or input_queue.get("db_path"),
            "trace_db_path": session.get("trace_db_path") or str(current_transport_db_path()),
            "recent_trace_events": latest_trace_events(current_transport_db_path(), limit=10, trace_id=session.get("last_input_trace_id")) if include_trace else [],
            "source": session.get("source"),
            "repo_root": repo_root,
            "project_name": project_name,
            "project_verified": bool(project_name),
            "model_hint": current_model,
            "configured_model": configured_model,
            "model_verified": model_verified,
            "permissions_hint": permissions_hint,
            "permissions_verified": permissions_verified,
            "directory_trust_verified": directory_trust_verified,
            "command_ready": command_ready,
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
        transcript_kind = str(session.get("transcript_kind") or "")
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
        if transcript_kind == "screen_snapshot":
            text = transcript_path.read_text(encoding="utf-8", errors="replace")
            encoded = text.encode("utf-8", errors="replace")
            revision = int(session.get("last_output_sequence") or 0)
            if cursor is None:
                mode = "tail"
                payload_text = text[-limit:]
            elif cursor != revision:
                mode = "reset_tail"
                payload_text = text[-limit:]
            else:
                mode = "delta"
                payload_text = ""
            return {
                "mode": mode,
                "text": payload_text,
                "cursor": cursor,
                "next_cursor": revision,
                "size": len(encoded),
                "truncated": len(encoded) > limit,
                "source": str(transcript_path),
            }
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
        needs_reset_tail = (
            mode == "delta"
            and (
                "\b" in text
                or "\x15" in text
                or "\x1b" in text
                or re.search(r"\r(?!\n)", text) is not None
            )
        )
        if needs_reset_tail:
            read_start = max(0, size - limit)
            with transcript_path.open("rb") as handle:
                handle.seek(read_start)
                text = handle.read(limit).decode("utf-8", errors="replace")
            mode = "reset_tail"
            truncated = read_start > 0
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
                "frontend_route_version": frontend_route_version(),
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
                payload.setdefault("restart_existing", True)
                payload.setdefault("startup_model", "auto")
                payload.setdefault("port", int(os.environ.get("COPILOT_ADMIN_SESSION_BROWSER_PORT", "9222")))
                response = self.call_host_runner("POST", "/api/session/start", payload)
                dispatched = str(response.get("status") or "").lower() not in {"failed", "error", "blocked"}
                reason = None
                if not dispatched:
                    reason = (
                        response.get("error")
                        or response.get("copilot", {}).get("stderr")
                        or response.get("copilot", {}).get("status")
                        or response.get("status")
                    )
                return {"dispatched": dispatched, "target": "host-runner", "response": response, "reason": reason}
            response = self.call_host_runner("POST", "/copilot/input", {"text": job["prompt"], "job_id": job["job_id"], "trace_id": job["trace_id"]})
            return {"dispatched": response.get("status") not in {"failed", "error"}, "target": "host-runner", "response": response}

        copilot = self.copilot_session()
        db_path_value = copilot.get("input_queue_db_path") or str(current_transport_db_path())
        queue_dir_value = copilot.get("input_queue_dir")
        if (not db_path_value and not queue_dir_value) or copilot.get("status") not in {"running", "user_input_required"}:
            return {"dispatched": False, "reason": "node-pty input queue is not available"}
        request = {
            "text": job["prompt"],
            "submit": job["payload"].get("submit") is not False,
            "clear_line": bool(job["payload"].get("clear_line")),
            "job_id": job["job_id"],
            "trace_id": job["trace_id"],
            "client_sent_at": job["payload"].get("client_sent_at"),
            "backend_queued_at": job["payload"].get("backend_accepted_at") or utc_now(),
        }
        if db_path_value:
            db_path = ensure_child(self.repo_root, Path(db_path_value))
            queued = enqueue_input(
                db_path,
                source="backend-local",
                text=request["text"],
                display_text=request["text"],
                clear_line=bool(request["clear_line"]),
                submit=bool(request["submit"]),
                job_id=job["job_id"],
                trace_id=job["trace_id"],
                client_sent_at=request["client_sent_at"],
                backend_accepted_at=job["payload"].get("backend_accepted_at"),
                backend_queued_at=request["backend_queued_at"],
            )
            return {"dispatched": True, "queue_db": str(db_path), "input_id": queued["input_id"]}
        queue_dir = ensure_child(self.repo_root, Path(queue_dir_value))
        queue_dir.mkdir(parents=True, exist_ok=True)
        request_path = queue_dir / f"{utc_now().replace(':', '').replace('-', '').replace('.', '')}-{job['job_id']}.json"
        write_json_atomically(request_path, request)
        return {"dispatched": True, "queue_file": rel_path(request_path)}

    def send_ai_console_input(self, payload: dict[str, Any], trace_id: str | None = None) -> dict[str, Any]:
        raw_text = str(payload.get("text") if payload.get("text") is not None else payload.get("prompt") or "")
        if not raw_text.strip() and raw_text not in {"\t", "\x1b"}:
            raise ApiError(400, "text is required.")
        text = with_ai_console_standard_instruction(raw_text)
        submit = payload.get("submit") is not False
        job_id = payload.get("job_id") or f"console-{uuid.uuid4().hex}"
        request = {
            "job_id": job_id,
            "trace_id": trace_id or payload.get("trace_id") or uuid.uuid4().hex,
            "type": "ai_console_input",
            "prompt": text,
            "payload": {
                "text": text,
                "submit": submit,
                "clear_line": payload.get("clear_line") is not False,
                "client_sent_at": payload.get("client_sent_at"),
                "backend_accepted_at": utc_now(),
            },
        }
        record_trace_event(
            current_transport_db_path(),
            component="backend",
            event="ai_console_input_accepted",
            trace_id=request["trace_id"],
            job_id=job_id,
            status="accepted",
            details={"submit": submit, "clear_line": request["payload"]["clear_line"]},
        )
        if host_runner_url():
            response = self.call_host_runner("POST", "/copilot/input", {
                "text": text,
                "submit": submit,
                "clear_line": request["payload"]["clear_line"],
                "job_id": job_id,
                "trace_id": request["trace_id"],
                "client_sent_at": request["payload"]["client_sent_at"],
                "backend_accepted_at": request["payload"]["backend_accepted_at"],
            })
            result = {"accepted": response.get("status") not in {"failed", "error"}, "target": "host-runner", "response": response, "job_id": job_id}
        else:
            dispatch = self.dispatch_to_node_pty(request)
            result = {"accepted": bool(dispatch.get("dispatched")), "target": "local-node-pty", "response": dispatch, "job_id": job_id}
        if not result["accepted"]:
            raise ApiError(409, "AI console input could not be queued.", {"dispatch": result})
        self.log("info", "backend", "ai_console_input_sent", trace_id=request["trace_id"], job_id=job_id, status="queued", details={"submit": submit, "target": result["target"]})
        record_trace_event(
            current_transport_db_path(),
            component="backend",
            event="ai_console_input_dispatched",
            trace_id=request["trace_id"],
            job_id=job_id,
            status="queued",
            details={"target": result["target"], "response": result["response"]},
        )
        result["accepted_at"] = request["payload"]["backend_accepted_at"]
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
        if record["trace_id"]:
            record_trace_event(
                current_transport_db_path(),
                component="frontend",
                event=event,
                trace_id=record["trace_id"],
                job_id=payload.get("job_id"),
                status=payload.get("status"),
                details=payload,
            )
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


class QuietThreadingHTTPServer(ThreadingHTTPServer):
    def handle_error(self, request: Any, client_address: Any) -> None:
        exc = sys.exc_info()[1]
        if isinstance(exc, (BrokenPipeError, ConnectionAbortedError, ConnectionResetError)) or getattr(exc, "winerror", None) in {64, 10053, 10054}:
            return
        super().handle_error(request, client_address)


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

    def send_sse_event(self, event: str, payload: Any) -> None:
        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        self.wfile.write(f"event: {event}\n".encode("utf-8"))
        for line in encoded.splitlines() or [""]:
            self.wfile.write(f"data: {line}\n".encode("utf-8"))
        self.wfile.write(b"\n")
        self.wfile.flush()

    @staticmethod
    def is_client_disconnect(exc: Exception) -> bool:
        if isinstance(exc, (BrokenPipeError, ConnectionAbortedError, ConnectionResetError)):
            return True
        return getattr(exc, "winerror", None) in {64, 10053, 10054}

    def stream_ai_console_events(self, query: dict[str, list[str]]) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        cursor = self.app._int_query_value(query, "cursor")
        requested_limit = self.app._int_query_value(query, "limit") or DEFAULT_CONSOLE_TAIL_BYTES
        limit = max(1024, min(requested_limit, MAX_CONSOLE_DELTA_BYTES))
        deadline = time.time() + float(os.environ.get("COPILOT_ADMIN_CONSOLE_EVENT_STREAM_SECONDS", "300"))
        last_heartbeat = 0.0
        base_query = {"cursor": [str(cursor)], "limit": [str(limit)], "include_trace": ["0"]} if cursor is not None else {"limit": [str(limit)], "include_trace": ["0"]}
        base_console = self.app.ai_console(query=base_query)
        base_console["streamed_at"] = utc_now()
        last_console_signature = (
            base_console.get("status"),
            base_console.get("running"),
            base_console.get("updated_at"),
            base_console.get("user_input_required"),
            base_console.get("user_input_reason"),
            base_console.get("visible_window_expected"),
            base_console.get("permissions_verified"),
            base_console.get("command_ready"),
            base_console.get("project_name"),
        )
        try:
            self.send_sse_event("console", base_console)
        except Exception as exc:
            if self.is_client_disconnect(exc):
                return
            raise
        transcript = base_console.get("transcript") or {}
        if isinstance(transcript.get("next_cursor"), int):
            cursor = transcript["next_cursor"]
        while time.time() < deadline:
            current_query = {"cursor": [str(cursor)], "limit": [str(limit)], "include_trace": ["0"]} if cursor is not None else {"limit": [str(limit)], "include_trace": ["0"]}
            console = self.app.ai_console(query=current_query)
            transcript = console.get("transcript") or {}
            text = str(transcript.get("text") or "")
            next_cursor = transcript.get("next_cursor")
            console_signature = (
                console.get("status"),
                console.get("running"),
                console.get("updated_at"),
                console.get("user_input_required"),
                console.get("user_input_reason"),
                console.get("visible_window_expected"),
                console.get("permissions_verified"),
                console.get("command_ready"),
                console.get("project_name"),
            )
            try:
                if text or console_signature != last_console_signature:
                    console["streamed_at"] = utc_now()
                    self.send_sse_event("console", console)
                    last_console_signature = console_signature
                elif time.time() - last_heartbeat >= 2.0:
                    self.send_sse_event("heartbeat", {"server_timestamp": utc_now(), "streamed_at": utc_now(), "cursor": cursor})
                    last_heartbeat = time.time()
            except Exception as exc:
                if self.is_client_disconnect(exc):
                    return
                raise
            if isinstance(next_cursor, int):
                cursor = next_cursor
            time.sleep(CONSOLE_EVENT_POLL_SECONDS)

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
            frontend_route = normalize_frontend_route(path)
            if frontend_route is not None:
                self.send_frontend_route(*frontend_route)
            elif path in {"/app.js", "/styles.css"}:
                self.send_static(path.lstrip("/"))
            elif path == "/api/health":
                self.send_json(200, self.app.health())
            elif path == "/api/status":
                self.send_json(200, self.app.status())
            elif path == "/api/session/copilot":
                self.send_json(200, self.app.copilot_session())
            elif path in {"/api/ai-console", "/api/copilot/console"}:
                self.send_json(200, self.app.ai_console(query=parse_qs(parsed.query)))
            elif path in {"/api/ai-console/events", "/api/copilot/console/events"}:
                self.stream_ai_console_events(parse_qs(parsed.query))
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
            if self.is_client_disconnect(exc):
                return
            self.handle_error(exc)

    def send_redirect(self, location: str) -> None:
        encoded = b""
        self.send_response(302)
        self.send_header("Location", location)
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def send_frontend_route(self, route: str, version: str | None) -> None:
        latest_version = frontend_route_version()
        canonical_path = f"/{route}/{latest_version}"
        if version != latest_version:
            self.send_redirect(canonical_path)
            return
        self.send_index(route, latest_version)

    def send_index(self, route: str, route_version: str) -> None:
        index_path = ensure_child(FRONTEND_DIR, FRONTEND_DIR / "index.html")
        if not index_path.is_file():
            raise ApiError(404, "Frontend asset not found.")
        html = index_path.read_text(encoding="utf-8")
        config_script = (
            "<script>"
            "window.COPILOT_ADMIN_FRONTEND="
            + json.dumps({"route": route, "routeVersion": route_version}, ensure_ascii=False, separators=(",", ":"))
            + ";</script>"
        )
        html = html.replace('<link rel="stylesheet" href="styles.css" />', '<link rel="stylesheet" href="/styles.css" />')
        html = html.replace('<script type="module" src="app.js"></script>', f'{config_script}\n    <script type="module" src="/app.js"></script>')
        data = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

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
            elif path in {"/api/ai-console/input", "/api/copilot/input"}:
                self.send_json(202, self.app.send_ai_console_input(body, trace_id))
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
            if self.is_client_disconnect(exc):
                return
            self.handle_error(exc)


def make_server(host: str, port: int, app: ControlPlaneBackend = APP) -> ThreadingHTTPServer:
    server = QuietThreadingHTTPServer((host, port), Handler)
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
