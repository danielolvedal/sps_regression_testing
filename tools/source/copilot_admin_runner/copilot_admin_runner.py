from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from multiprocessing.connection import Client, Listener
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_DIR = REPO_ROOT / "runtime"
TEST_DIR = REPO_ROOT / "testing" / "regression_test"
REPORTS_DIR = REPO_ROOT / "test_reports"
QUEUE_DIR = REPO_ROOT / "tmp" / "copilot_admin_queue"
LOG_DIR = REPO_ROOT / "tmp" / "copilot_admin_runner_logs"
CATALOG_PATH = TEST_DIR / "regression-test-catalog.md"
GRAPH_PATH = TEST_DIR / "regression-test-dependencies.mmd"
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
) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": utc_now(),
        "event_id": uuid.uuid4().hex,
        "event": event,
        "bridge": bridge,
        "pid": os.getpid(),
        "repo_root": str(REPO_ROOT),
        "details": details or {},
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
    return {
        "generated_at": utc_now(),
        "repo_root": str(REPO_ROOT),
        "runtime_scripts": list_runtime_scripts(),
        "regression_catalog": parse_catalog(),
        "latest_report": parse_latest_summary(),
        "supported_bridges": list(BRIDGE_CHOICES),
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

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
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
                if parsed.path.startswith("/commands/"):
                    command_id = parsed.path.rsplit("/", 1)[-1]
                    catalog_key = None
                    verification_id = None
                    if "catalog_key=" in parsed.query:
                        for pair in parsed.query.split("&"):
                            if pair.startswith("catalog_key="):
                                catalog_key = pair.split("=", 1)[1]
                    if "verification_id=" in parsed.query:
                        for pair in parsed.query.split("&"):
                            if pair.startswith("verification_id="):
                                verification_id = pair.split("=", 1)[1]
                    payload = handle_request(
                        {
                            "action": "command-template",
                            "command_id": command_id,
                            "catalog_key": catalog_key,
                            "verification_id": verification_id,
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
