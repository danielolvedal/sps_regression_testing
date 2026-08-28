from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = REPO_ROOT / "tmp" / "copilot_admin_control_plane" / "project-controlled-copilot-sessions.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_registry() -> dict[str, Any]:
    if not REGISTRY_PATH.is_file():
        return {"version": 1, "updated_at": utc_now(), "sessions": []}
    try:
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        data = {"version": 1, "updated_at": utc_now(), "sessions": []}
    if not isinstance(data, dict):
        data = {"version": 1, "updated_at": utc_now(), "sessions": []}
    sessions = data.get("sessions")
    if not isinstance(sessions, list):
        data["sessions"] = []
    data.setdefault("version", 1)
    data["updated_at"] = data.get("updated_at") or utc_now()
    return data


def _save_registry(data: dict[str, Any]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {**data, "updated_at": utc_now()}
    last_error: Exception | None = None
    for attempt in range(5):
        tmp_path = REGISTRY_PATH.with_suffix(f".{attempt}.tmp")
        try:
            tmp_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            tmp_path.replace(REGISTRY_PATH)
            return
        except OSError as exc:
            last_error = exc
            time.sleep(0.05 * (attempt + 1))
        finally:
            tmp_path.unlink(missing_ok=True)
    if last_error:
        raise last_error


def registry_path() -> Path:
    return REGISTRY_PATH


def list_sessions(*, active_only: bool = False) -> list[dict[str, Any]]:
    sessions = _load_registry().get("sessions", [])
    if not active_only:
        return sessions
    return [session for session in sessions if session.get("status") not in {"stopped", "terminated"}]


def upsert_session(
    session_key: str,
    *,
    kind: str,
    source: str,
    status: str,
    control_method: str | None = None,
    state_dir: str | None = None,
    state_path: str | None = None,
    window_state_path: str | None = None,
    wrapper_pid: int | None = None,
    launcher_pid: int | None = None,
    process_id: int | None = None,
    hidden: bool | None = None,
    visible_window_expected: bool | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    data = _load_registry()
    sessions = data["sessions"]
    now = utc_now()
    entry = next((item for item in sessions if item.get("session_key") == session_key), None)
    if entry is None:
        entry = {
            "session_key": session_key,
            "kind": kind,
            "source": source,
            "started_at": now,
        }
        sessions.append(entry)
    updates = {
        "kind": kind,
        "source": source,
        "status": status,
        "control_method": control_method,
        "state_dir": state_dir,
        "state_path": state_path,
        "window_state_path": window_state_path,
        "wrapper_pid": wrapper_pid,
        "launcher_pid": launcher_pid,
        "process_id": process_id,
        "hidden": hidden,
        "visible_window_expected": visible_window_expected,
        "note": note,
        "updated_at": now,
    }
    for key, value in updates.items():
        if value is not None:
            entry[key] = value
    if status not in {"stopped", "terminated"}:
        entry.pop("stopped_at", None)
    _save_registry(data)
    return entry


def mark_session_stopped(session_key: str, *, status: str = "stopped") -> dict[str, Any]:
    data = _load_registry()
    sessions = data["sessions"]
    now = utc_now()
    entry = next((item for item in sessions if item.get("session_key") == session_key), None)
    if entry is None:
        entry = {
            "session_key": session_key,
            "kind": "unknown",
            "source": "unknown",
            "started_at": now,
        }
        sessions.append(entry)
    entry["status"] = status
    entry["updated_at"] = now
    entry["stopped_at"] = now
    _save_registry(data)
    return entry


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage SPS project-controlled Copilot session registry.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    upsert = subparsers.add_parser("upsert", help="Create or update a project-controlled session entry.")
    upsert.add_argument("--session-key", required=True)
    upsert.add_argument("--kind", required=True)
    upsert.add_argument("--source", required=True)
    upsert.add_argument("--status", required=True)
    upsert.add_argument("--control-method")
    upsert.add_argument("--state-dir")
    upsert.add_argument("--state-path")
    upsert.add_argument("--window-state-path")
    upsert.add_argument("--wrapper-pid", type=int)
    upsert.add_argument("--launcher-pid", type=int)
    upsert.add_argument("--process-id", type=int)
    upsert.add_argument("--hidden", choices=("true", "false"))
    upsert.add_argument("--visible-window-expected", choices=("true", "false"))
    upsert.add_argument("--note")

    stopped = subparsers.add_parser("mark-stopped", help="Mark a project-controlled session as stopped.")
    stopped.add_argument("--session-key", required=True)
    stopped.add_argument("--status", default="stopped")

    listing = subparsers.add_parser("list", help="List session entries from the registry.")
    listing.add_argument("--active-only", action="store_true")

    path_cmd = subparsers.add_parser("path", help="Return the registry path.")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    if args.command == "upsert":
        payload = upsert_session(
            args.session_key,
            kind=args.kind,
            source=args.source,
            status=args.status,
            control_method=args.control_method,
            state_dir=args.state_dir,
            state_path=args.state_path,
            window_state_path=args.window_state_path,
            wrapper_pid=args.wrapper_pid,
            launcher_pid=args.launcher_pid,
            process_id=args.process_id,
            hidden={"true": True, "false": False}.get(args.hidden),
            visible_window_expected={"true": True, "false": False}.get(args.visible_window_expected),
            note=args.note,
        )
    elif args.command == "mark-stopped":
        payload = mark_session_stopped(args.session_key, status=args.status)
    elif args.command == "list":
        payload = {
            "registry_path": str(registry_path()),
            "sessions": list_sessions(active_only=args.active_only),
        }
    else:
        payload = {"registry_path": str(registry_path())}
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
