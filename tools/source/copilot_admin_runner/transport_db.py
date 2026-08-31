from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


TRANSPORT_DB_FILENAME = "copilot-admin-transport.sqlite"
_INITIALIZED_DB_PATHS: set[str] = set()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def transport_db_path(state_dir: Path) -> Path:
    return state_dir / TRANSPORT_DB_FILENAME


def _bool_to_int(value: Any) -> int:
    return 1 if bool(value) else 0


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    payload = dict(row)
    for key in ("clear_line", "submit"):
        if key in payload and payload[key] is not None:
            payload[key] = bool(payload[key])
    if payload.get("details_json"):
        payload["details"] = json.loads(payload["details_json"])
    return payload


def _int_to_bool_fields(payload: dict[str, Any], field_names: tuple[str, ...]) -> dict[str, Any]:
    for key in field_names:
        if key in payload and payload[key] is not None:
            payload[key] = bool(payload[key])
    return payload


def _session_row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    payload = json.loads(row["payload_json"]) if row["payload_json"] else {}
    if not isinstance(payload, dict):
        payload = {}
    payload.setdefault("session_id", row["session_id"])
    payload.setdefault("updated_at", row["updated_at"])
    payload.setdefault("status", row["status"])
    payload.setdefault("wrapper_pid", row["wrapper_pid"])
    payload.setdefault("launcher_pid", row["launcher_pid"])
    payload.setdefault("visible_window_expected", row["visible_window_expected"])
    payload.setdefault("user_input_required", row["user_input_required"])
    payload.setdefault("last_output_chunk_at", row["last_output_chunk_at"])
    payload.setdefault("last_output_sequence", row["last_output_sequence"])
    payload.setdefault("last_input_job_id", row["last_input_job_id"])
    payload.setdefault("transcript_path", row["transcript_path"])
    return _int_to_bool_fields(
        payload,
        (
            "visible_window_expected",
            "hidden",
            "running",
            "input_logging_enabled",
            "user_input_required",
            "last_injected_submit",
            "last_injected_clear_line",
            "startup_allow_all_requested",
            "startup_allow_all",
            "startup_commands_sent",
            "allow_all_verified",
            "model_verified",
            "directory_trust_requested",
            "directory_trust_verified",
        ),
    )


@contextmanager
def connect(db_path: Path) -> Iterator[sqlite3.Connection]:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path, timeout=5.0, isolation_level=None, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=NORMAL")
    connection.execute("PRAGMA busy_timeout=5000")
    db_key = str(db_path.resolve())
    if db_key not in _INITIALIZED_DB_PATHS:
        _init_schema(connection)
        _INITIALIZED_DB_PATHS.add(db_key)
    try:
        yield connection
    finally:
        connection.close()


def _init_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS input_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            input_id TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            source TEXT NOT NULL,
            status TEXT NOT NULL,
            text TEXT NOT NULL,
            display_text TEXT,
            clear_line INTEGER NOT NULL DEFAULT 0,
            submit INTEGER NOT NULL DEFAULT 1,
            job_id TEXT,
            trace_id TEXT,
            client_sent_at TEXT,
            backend_accepted_at TEXT,
            backend_queued_at TEXT,
            host_runner_received_at TEXT,
            host_runner_queued_at TEXT,
            claimed_at TEXT,
            claimed_by TEXT,
            pty_write_at TEXT,
            completed_at TEXT,
            error_message TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_input_queue_status_created
            ON input_queue (status, created_at, id);
        CREATE INDEX IF NOT EXISTS idx_input_queue_trace
            ON input_queue (trace_id, created_at, id);
        CREATE INDEX IF NOT EXISTS idx_input_queue_job
            ON input_queue (job_id, created_at, id);

        CREATE TABLE IF NOT EXISTS trace_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            trace_id TEXT,
            job_id TEXT,
            component TEXT NOT NULL,
            event TEXT NOT NULL,
            status TEXT,
            details_json TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_trace_events_trace_created
            ON trace_events (trace_id, created_at, id);
        CREATE INDEX IF NOT EXISTS idx_trace_events_job_created
            ON trace_events (job_id, created_at, id);
        CREATE INDEX IF NOT EXISTS idx_trace_events_component_event_created
            ON trace_events (component, event, created_at, id);

        CREATE TABLE IF NOT EXISTS session_state (
            session_id TEXT PRIMARY KEY,
            updated_at TEXT NOT NULL,
            status TEXT NOT NULL,
            wrapper_pid INTEGER,
            launcher_pid INTEGER,
            visible_window_expected INTEGER,
            user_input_required INTEGER,
            last_output_chunk_at TEXT,
            last_output_sequence INTEGER,
            last_input_job_id TEXT,
            transcript_path TEXT,
            payload_json TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_session_state_status_updated
            ON session_state (status, updated_at);
        """
    )
    connection.execute(
        "INSERT OR REPLACE INTO metadata (key, value) VALUES ('schema_version', '2')"
    )


def enqueue_input(
    db_path: Path,
    *,
    source: str,
    text: str,
    display_text: str | None = None,
    clear_line: bool = False,
    submit: bool = True,
    job_id: str | None = None,
    trace_id: str | None = None,
    client_sent_at: str | None = None,
    backend_accepted_at: str | None = None,
    backend_queued_at: str | None = None,
    host_runner_received_at: str | None = None,
    host_runner_queued_at: str | None = None,
    input_id: str | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    record = {
        "input_id": input_id or uuid.uuid4().hex,
        "created_at": created_at or utc_now(),
        "source": source,
        "status": "queued",
        "text": text,
        "display_text": display_text if display_text is not None else text,
        "clear_line": _bool_to_int(clear_line),
        "submit": _bool_to_int(submit),
        "job_id": job_id,
        "trace_id": trace_id,
        "client_sent_at": client_sent_at,
        "backend_accepted_at": backend_accepted_at,
        "backend_queued_at": backend_queued_at,
        "host_runner_received_at": host_runner_received_at,
        "host_runner_queued_at": host_runner_queued_at,
    }
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO input_queue (
                input_id, created_at, source, status, text, display_text, clear_line, submit,
                job_id, trace_id, client_sent_at, backend_accepted_at, backend_queued_at,
                host_runner_received_at, host_runner_queued_at
            ) VALUES (
                :input_id, :created_at, :source, :status, :text, :display_text, :clear_line, :submit,
                :job_id, :trace_id, :client_sent_at, :backend_accepted_at, :backend_queued_at,
                :host_runner_received_at, :host_runner_queued_at
            )
            """,
            record,
        )
        row = connection.execute(
            "SELECT * FROM input_queue WHERE input_id = ?",
            (record["input_id"],),
        ).fetchone()
    return _row_to_dict(row) or record


def abandon_active_inputs(db_path: Path, *, reason: str, claimed_by: str | None = None) -> int:
    params: list[Any] = [utc_now(), reason]
    where = "status IN ('queued', 'claimed')"
    if claimed_by is not None:
        where += " AND claimed_by = ?"
        params.append(claimed_by)
    with connect(db_path) as connection:
        cursor = connection.execute(
            f"""
            UPDATE input_queue
            SET status = 'abandoned',
                completed_at = ?,
                error_message = COALESCE(error_message, ?)
            WHERE {where}
            """,
            tuple(params),
        )
        return int(cursor.rowcount or 0)


def claim_next_input(db_path: Path, *, consumer_id: str) -> dict[str, Any] | None:
    with connect(db_path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            """
            SELECT * FROM input_queue
            WHERE status = 'queued'
            ORDER BY created_at ASC, id ASC
            LIMIT 1
            """
        ).fetchone()
        if row is None:
            connection.commit()
            return None
        claimed_at = utc_now()
        connection.execute(
            """
            UPDATE input_queue
            SET status = 'claimed',
                claimed_at = ?,
                claimed_by = ?
            WHERE input_id = ?
            """,
            (claimed_at, consumer_id, row["input_id"]),
        )
        claimed_row = connection.execute(
            "SELECT * FROM input_queue WHERE input_id = ?",
            (row["input_id"],),
        ).fetchone()
        connection.commit()
    return _row_to_dict(claimed_row)


def update_input_status(
    db_path: Path,
    *,
    input_id: str,
    status: str,
    pty_write_at: str | None = None,
    error_message: str | None = None,
    claimed_by: str | None = None,
) -> dict[str, Any] | None:
    assignments = ["status = ?", "completed_at = ?"]
    params: list[Any] = [status, utc_now()]
    if pty_write_at is not None:
        assignments.append("pty_write_at = ?")
        params.append(pty_write_at)
    if error_message is not None:
        assignments.append("error_message = ?")
        params.append(error_message)
    if claimed_by is not None:
        assignments.append("claimed_by = ?")
        params.append(claimed_by)
    params.append(input_id)
    with connect(db_path) as connection:
        connection.execute(
            f"UPDATE input_queue SET {', '.join(assignments)} WHERE input_id = ?",
            tuple(params),
        )
        row = connection.execute(
            "SELECT * FROM input_queue WHERE input_id = ?",
            (input_id,),
        ).fetchone()
    return _row_to_dict(row)


def queue_snapshot(db_path: Path) -> dict[str, Any]:
    with connect(db_path) as connection:
        counts = {
            row["status"]: row["count"]
            for row in connection.execute(
                "SELECT status, COUNT(*) AS count FROM input_queue GROUP BY status"
            ).fetchall()
        }
        latest = [
            {
                "input_id": row["input_id"],
                "status": row["status"],
                "job_id": row["job_id"],
                "trace_id": row["trace_id"],
                "created_at": row["created_at"],
                "claimed_at": row["claimed_at"],
                "completed_at": row["completed_at"],
            }
            for row in connection.execute(
                """
                SELECT input_id, status, job_id, trace_id, created_at, claimed_at, completed_at
                FROM input_queue
                ORDER BY id DESC
                LIMIT 10
                """
            ).fetchall()
        ]
    return {
        "db_path": str(db_path),
        "pending": int(counts.get("queued", 0)),
        "claimed": int(counts.get("claimed", 0)),
        "sent": int(counts.get("sent", 0)),
        "failed": int(counts.get("failed", 0)),
        "skipped": int(counts.get("skipped", 0)),
        "abandoned": int(counts.get("abandoned", 0)),
        "latest_items": latest,
    }


def record_trace_event(
    db_path: Path,
    *,
    component: str,
    event: str,
    trace_id: str | None = None,
    job_id: str | None = None,
    status: str | None = None,
    details: dict[str, Any] | None = None,
    event_id: str | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    record = {
        "event_id": event_id or uuid.uuid4().hex,
        "created_at": created_at or utc_now(),
        "trace_id": trace_id,
        "job_id": job_id,
        "component": component,
        "event": event,
        "status": status,
        "details_json": json.dumps(details or {}, ensure_ascii=False),
    }
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO trace_events (
                event_id, created_at, trace_id, job_id, component, event, status, details_json
            ) VALUES (
                :event_id, :created_at, :trace_id, :job_id, :component, :event, :status, :details_json
            )
            """,
            record,
        )
    return {
        "event_id": record["event_id"],
        "created_at": record["created_at"],
        "trace_id": record["trace_id"],
        "job_id": record["job_id"],
        "component": component,
        "event": event,
        "status": status,
        "details": details or {},
    }


def latest_trace_events(db_path: Path, *, limit: int = 20, trace_id: str | None = None) -> list[dict[str, Any]]:
    query = """
        SELECT event_id, created_at, trace_id, job_id, component, event, status, details_json
        FROM trace_events
    """
    params: list[Any] = []
    if trace_id:
        query += " WHERE trace_id = ?"
        params.append(trace_id)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    with connect(db_path) as connection:
        rows = connection.execute(query, tuple(params)).fetchall()
    return [_row_to_dict(row) or {} for row in rows]


def upsert_session_state(
    db_path: Path,
    state: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    payload = dict(state)
    resolved_session_id = session_id or str(payload.get("session_id") or "node-pty-copilot")
    payload["session_id"] = resolved_session_id
    payload["updated_at"] = str(payload.get("updated_at") or utc_now())
    payload.setdefault("status", "unknown")
    record = {
        "session_id": resolved_session_id,
        "updated_at": payload["updated_at"],
        "status": str(payload.get("status") or "unknown"),
        "wrapper_pid": payload.get("wrapper_pid"),
        "launcher_pid": payload.get("launcher_pid"),
        "visible_window_expected": _bool_to_int(payload.get("visible_window_expected")),
        "user_input_required": _bool_to_int(payload.get("user_input_required")),
        "last_output_chunk_at": payload.get("last_output_chunk_at"),
        "last_output_sequence": payload.get("last_output_sequence"),
        "last_input_job_id": payload.get("last_input_job_id"),
        "transcript_path": payload.get("transcript_path"),
        "payload_json": json.dumps(payload, ensure_ascii=False),
    }
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO session_state (
                session_id, updated_at, status, wrapper_pid, launcher_pid,
                visible_window_expected, user_input_required, last_output_chunk_at,
                last_output_sequence, last_input_job_id, transcript_path, payload_json
            ) VALUES (
                :session_id, :updated_at, :status, :wrapper_pid, :launcher_pid,
                :visible_window_expected, :user_input_required, :last_output_chunk_at,
                :last_output_sequence, :last_input_job_id, :transcript_path, :payload_json
            )
            ON CONFLICT(session_id) DO UPDATE SET
                updated_at = excluded.updated_at,
                status = excluded.status,
                wrapper_pid = excluded.wrapper_pid,
                launcher_pid = excluded.launcher_pid,
                visible_window_expected = excluded.visible_window_expected,
                user_input_required = excluded.user_input_required,
                last_output_chunk_at = excluded.last_output_chunk_at,
                last_output_sequence = excluded.last_output_sequence,
                last_input_job_id = excluded.last_input_job_id,
                transcript_path = excluded.transcript_path,
                payload_json = excluded.payload_json
            """,
            record,
        )
        row = connection.execute(
            "SELECT * FROM session_state WHERE session_id = ?",
            (resolved_session_id,),
        ).fetchone()
    return _session_row_to_dict(row) or payload


def get_session_state(db_path: Path, *, session_id: str = "node-pty-copilot") -> dict[str, Any] | None:
    with connect(db_path) as connection:
        row = connection.execute(
            "SELECT * FROM session_state WHERE session_id = ?",
            (session_id,),
        ).fetchone()
    return _session_row_to_dict(row)
