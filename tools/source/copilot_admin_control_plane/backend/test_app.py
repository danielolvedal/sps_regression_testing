from __future__ import annotations

import json
import os
import shutil
import sqlite3
import sys
import threading
import time
import unittest
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, build_opener
from urllib.request import Request, urlopen

os.environ.setdefault("COPILOT_ADMIN_ENV", "test")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import app


AI_CONSOLE_STANDARD_INSTRUCTION = (
    "Om instruktionen är oklar eller otydlig ställ klargörande frågor, "
    "om instruktionen påverkar befintliga tester måste användaren informeras om konsekvenserna av den ändringen."
)


class BackendSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.test_state_dir = app.REPO_ROOT / "tmp" / "copilot_admin_control_plane" / f"backend-unittest-state-{uuid.uuid4().hex}"
        cls.test_state_dir.mkdir(parents=True, exist_ok=True)
        cls.previous_state_dir = app.STATE_DIR
        cls.previous_jobs_path = app.JOBS_PATH
        cls.previous_host_state_path = app.HOST_STATE_PATH
        cls.previous_mode_path = app.MODE_PATH
        cls.previous_log_dir = app.LOG_DIR
        cls.previous_node_pty_state_dir = app.NODE_PTY_STATE_DIR
        cls.previous_node_pty_state_path = app.NODE_PTY_STATE_PATH
        cls.previous_node_pty_window_state_path = app.NODE_PTY_WINDOW_STATE_PATH
        app.STATE_DIR = cls.test_state_dir
        app.JOBS_PATH = cls.test_state_dir / "jobs.json"
        app.HOST_STATE_PATH = cls.test_state_dir / "injected-host-state.json"
        app.MODE_PATH = cls.test_state_dir / "current-mode.json"
        app.LOG_DIR = cls.test_state_dir / "logs"
        app.NODE_PTY_STATE_DIR = cls.test_state_dir / "runner-state"
        app.NODE_PTY_STATE_DIR.mkdir(parents=True, exist_ok=True)
        app.NODE_PTY_STATE_PATH = app.NODE_PTY_STATE_DIR / "node-pty-copilot-session.json"
        app.NODE_PTY_WINDOW_STATE_PATH = app.NODE_PTY_STATE_DIR / "node-pty-copilot-window.json"
        cls.backend = app.ControlPlaneBackend(app.REPO_ROOT)
        cls.server = app.make_server("127.0.0.1", 0, cls.backend)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        app.STATE_DIR = cls.previous_state_dir
        app.JOBS_PATH = cls.previous_jobs_path
        app.HOST_STATE_PATH = cls.previous_host_state_path
        app.MODE_PATH = cls.previous_mode_path
        app.LOG_DIR = cls.previous_log_dir
        app.NODE_PTY_STATE_DIR = cls.previous_node_pty_state_dir
        app.NODE_PTY_STATE_PATH = cls.previous_node_pty_state_path
        app.NODE_PTY_WINDOW_STATE_PATH = cls.previous_node_pty_window_state_path
        shutil.rmtree(cls.test_state_dir, ignore_errors=True)

    def setUp(self) -> None:
        self.request("POST", "/api/test/reset", {})

    def request(self, method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=data,
            method=method,
            headers={"Content-Type": "application/json", "X-Trace-Id": "test-trace"},
        )
        with urlopen(req, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def test_health_catalog_mermaid_and_reports(self) -> None:
        status, health = self.request("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(health["status"], "ok")
        self.assertIn("frontend_dir", health["configuration"])

        status, catalog = self.request("GET", "/api/regression/tests")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(catalog["count"], 1)
        self.assertIn("catalog_key", catalog["tests"][0])
        csc_translation_test = next(
            test for test in catalog["tests"]
            if test["test_id"] == "regression-kundtjanst-english-translation-consistency"
        )
        self.assertEqual("H", csc_translation_test["catalog_key"])
        self.assertEqual(
            "testing\\regression_test\\kundtjanst-english-translation-consistency.md",
            csc_translation_test["file_path"],
        )
        self.assertEqual("ui-regression", csc_translation_test["test_type"])
        self.assertEqual([], csc_translation_test["dependency_keys"])
        self.assertEqual([], csc_translation_test["dependency_test_ids"])
        self.assertEqual("none", csc_translation_test["dependency_mode"])

        status, mermaid = self.request("GET", "/api/regression/mermaid")
        self.assertEqual(status, 200)
        self.assertRegex(mermaid["mermaid"].lower(), r"(graph|flowchart)")

        status, reports = self.request("GET", "/api/reports")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(reports["count"], 1)
        status, report = self.request("GET", f"/api/reports/{reports['reports'][0]['report_id']}")
        self.assertEqual(status, 200)
        self.assertIn("markdown", report)

    def test_frontend_assets_are_served(self) -> None:
        req = Request(f"http://127.0.0.1:{self.port}/", method="GET")
        with urlopen(req, timeout=5) as response:
            html = response.read().decode("utf-8")
            status = response.status
        self.assertEqual(status, 200)
        self.assertIn("SPS Copilot-admin", html)
        self.assertIn("COPILOT_ADMIN_FRONTEND", html)

        req = Request(f"http://127.0.0.1:{self.port}/app.js", method="GET")
        with urlopen(req, timeout=5) as response:
            js = response.read().decode("utf-8")
            status = response.status
        self.assertEqual(status, 200)
        self.assertIn("/api/status", js)

    def test_frontend_routes_redirect_to_latest_version(self) -> None:
        class NoRedirect(HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
                return None

        opener = build_opener(NoRedirect)
        with self.assertRaises(HTTPError) as redirect_ctx:
            opener.open(Request(f"http://127.0.0.1:{self.port}/mermaid", method="GET"), timeout=5)
        self.assertEqual(redirect_ctx.exception.code, 302)
        location = redirect_ctx.exception.headers["Location"]
        self.assertRegex(location, r"^/mermaid/v[0-9a-f]+$")

        with self.assertRaises(HTTPError) as stale_ctx:
            opener.open(Request(f"http://127.0.0.1:{self.port}/Regressioner/stale-version", method="GET"), timeout=5)
        self.assertEqual(stale_ctx.exception.code, 302)
        self.assertRegex(stale_ctx.exception.headers["Location"], r"^/regressioner/v[0-9a-f]+$")

        with urlopen(Request(f"http://127.0.0.1:{self.port}{location}", method="GET"), timeout=5) as response:
            html = response.read().decode("utf-8")
        self.assertEqual(response.status, 200)
        self.assertIn('"route":"mermaid"', html)
        self.assertIn('"routeVersion":"', html)
        self.assertIn('href="/styles.css"', html)
        self.assertIn('src="/app.js"', html)

    def test_job_lifecycle_and_control_api(self) -> None:
        self.request("POST", "/api/test/reset", {})
        status, job = self.request("POST", "/api/jobs", {"type": "custom", "prompt": "smoke"})
        self.assertEqual(status, 201)
        self.assertIn(job["status"], {"queued", "running"})

        self.request("POST", "/api/test/inject-host-state", {"job_updates": [{"job_id": job["job_id"], "status": "completed_unopened", "result": {"ok": True}}]})
        status, updated = self.request("GET", f"/api/jobs/{job['job_id']}")
        self.assertEqual(status, 200)
        self.assertEqual(updated["status"], "completed_unopened")

        status, aggregate = self.request("GET", "/api/status")
        self.assertEqual(status, 200)
        self.assertEqual(aggregate["status_diode"], "green")

        status, opened = self.request("POST", f"/api/jobs/{job['job_id']}/open", {})
        self.assertEqual(status, 200)
        self.assertEqual(opened["status"], "completed_opened")

    def test_selected_regression_prompt_uses_test_id(self) -> None:
        self.request("POST", "/api/test/reset", {})
        status, catalog = self.request("GET", "/api/regression/tests")
        self.assertEqual(status, 200)
        test = catalog["tests"][0]
        status, job = self.request("POST", "/api/regression/run", {"scope": "selected", "test_id": test["test_id"]})
        self.assertEqual(status, 201)
        self.assertIn(test["test_id"], job["prompt"])
        self.assertIn(test["catalog_key"], job["prompt"])

    def test_catalog_dependencies_do_not_include_the_current_test(self) -> None:
        status, catalog = self.request("GET", "/api/regression/tests")
        self.assertEqual(status, 200)
        tests_by_key = {test["catalog_key"]: test for test in catalog["tests"]}
        self.assertEqual(["B"], tests_by_key["G"]["dependency_keys"])
        self.assertNotIn("G", tests_by_key["G"]["dependencies"])

    def test_frontend_log_ingestion(self) -> None:
        status, response = self.request("POST", "/api/frontend/events", {"event": "page_view", "trace_id": "frontend-trace"})
        self.assertEqual(status, 202)
        self.assertTrue(response["accepted"])
        self.assertEqual(response["trace_id"], "test-trace")

    def test_ai_console_reads_injected_state_and_queues_local_input(self) -> None:
        queue_dir = app.REPO_ROOT / "tmp" / "copilot_admin_control_plane" / f"backend-console-test-queue-{uuid.uuid4().hex}"
        queue_dir.mkdir(parents=True, exist_ok=True)
        queue_db = queue_dir / "transport.sqlite"
        self.request(
            "POST",
            "/api/test/inject-host-state",
            {
                "copilot_state": {
                    "status": "running",
                    "running": True,
                    "input_queue_dir": str(queue_dir),
                    "input_queue_db_path": str(queue_db),
                    "input_queue": {"pending": 0},
                    "last_output_tail": "Console transcript from injected state.",
                    "user_input_required": True,
                    "user_input_reason": "confirmation_prompt",
                }
            },
        )

        status, console = self.request("GET", "/api/ai-console")
        self.assertEqual(status, 200)
        self.assertTrue(console["running"])
        self.assertTrue(console["user_input_required"])
        self.assertIn("Console transcript", console["transcript_tail"])

        status, queued = self.request("POST", "/api/ai-console/input", {"text": "svara ja"})
        self.assertEqual(status, 202)
        self.assertTrue(queued["accepted"])
        self.assertEqual(queued["target"], "local-node-pty")
        conn = sqlite3.connect(queue_db)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM input_queue ORDER BY id").fetchall()
        self.assertEqual(1, len(rows))
        queued_body = dict(rows[0])
        self.assertTrue(queued_body["text"].startswith("svara ja\n\nStandardinstruktion: "))
        self.assertIn(AI_CONSOLE_STANDARD_INSTRUCTION, queued_body["text"])
        self.assertEqual(1, queued_body["clear_line"])

        status, tab_queued = self.request("POST", "/api/ai-console/input", {"text": "\t", "submit": False, "clear_line": False})
        self.assertEqual(status, 202)
        self.assertTrue(tab_queued["accepted"])
        status, help_queued = self.request("POST", "/api/ai-console/input", {"text": "/help"})
        self.assertEqual(status, 202)
        self.assertTrue(help_queued["accepted"])
        queue_bodies = [dict(row) for row in conn.execute("SELECT * FROM input_queue ORDER BY id").fetchall()]
        conn.close()
        self.assertTrue(any(body["text"] == "\t" and body["clear_line"] == 0 and body["submit"] == 0 for body in queue_bodies))
        self.assertTrue(any(body["text"] == "/help" and body["submit"] == 1 for body in queue_bodies))

    def test_ai_console_does_not_verify_permissions_from_requested_policy_only(self) -> None:
        self.request(
            "POST",
            "/api/test/inject-host-state",
            {
                "copilot_state": {
                    "status": "running",
                    "running": True,
                    "startup_allow_all": True,
                    "startup_commands_sent": True,
                    "startup_model": "auto",
                    "input_queue_dir": str(app.REPO_ROOT / "tmp" / "copilot_admin_control_plane" / "backend-policy-test-queue"),
                }
            },
        )
        status, console = self.request("GET", "/api/ai-console")
        self.assertEqual(status, 200)
        self.assertFalse(console["permissions_verified"])
        self.assertEqual(console["permissions_hint"], "allow-all")
        self.assertFalse(console["model_verified"])
        self.assertIsNone(console["model_hint"])
        self.assertEqual(console["configured_model"], "auto")
        self.assertEqual(console["project_name"], "SPS")
        self.assertFalse(console["command_ready"])

        self.request(
            "POST",
            "/api/test/inject-host-state",
            {
                "copilot_state": {
                    "status": "running",
                    "running": True,
                    "allow_all_verified": True,
                    "permissions_hint": "allow-all",
                    "input_queue_dir": str(app.REPO_ROOT / "tmp" / "copilot_admin_control_plane" / "backend-policy-test-queue"),
                }
            },
        )
        status, verified = self.request("GET", "/api/ai-console")
        self.assertEqual(status, 200)
        self.assertTrue(verified["permissions_verified"])
        self.assertEqual(verified["permissions_hint"], "allow-all")
        self.assertTrue(verified["command_ready"])

    def test_ai_console_supports_cursor_based_transcript_polling(self) -> None:
        transcript = app.REPO_ROOT / "tmp" / "copilot_admin_control_plane" / "backend-console-transcript.txt"
        transcript.parent.mkdir(parents=True, exist_ok=True)
        transcript.write_text("line-1\nline-2\n", encoding="utf-8")
        self.request(
            "POST",
            "/api/test/inject-host-state",
            {
                "copilot_state": {
                    "status": "running",
                    "running": True,
                    "transcript_path": str(transcript),
                    "input_queue_dir": str(transcript.parent / "backend-console-cursor-queue"),
                }
            },
        )
        status, first = self.request("GET", "/api/ai-console?limit=1024")
        self.assertEqual(status, 200)
        self.assertEqual(first["transcript"]["mode"], "tail")
        self.assertIn("line-2", first["transcript"]["text"])
        cursor = first["transcript"]["next_cursor"]

        with transcript.open("a", encoding="utf-8") as handle:
            handle.write("line-3\n")
        status, second = self.request("GET", f"/api/ai-console?cursor={cursor}&limit=1024")
        self.assertEqual(status, 200)
        self.assertEqual(second["transcript"]["mode"], "delta")
        self.assertEqual(second["transcript"]["text"].replace("\r\n", "\n"), "line-3\n")
        self.assertGreater(second["transcript"]["next_cursor"], cursor)

    def test_ai_console_event_stream_delta_within_200ms(self) -> None:
        transcript = app.REPO_ROOT / "tmp" / "copilot_admin_control_plane" / "backend-console-sse-transcript.txt"
        transcript.parent.mkdir(parents=True, exist_ok=True)
        transcript.write_text("ready\n", encoding="utf-8")
        cursor = transcript.stat().st_size
        self.request(
            "POST",
            "/api/test/inject-host-state",
            {
                "copilot_state": {
                    "status": "running",
                    "running": True,
                    "transcript_path": str(transcript),
                    "input_queue_dir": str(transcript.parent / "backend-console-sse-queue"),
                }
            },
        )
        req = Request(f"http://127.0.0.1:{self.port}/api/ai-console/events?cursor={cursor}&limit=1024", method="GET")
        with urlopen(req, timeout=5) as response:
            deadline = time.perf_counter() + 2.0
            while time.perf_counter() < deadline:
                if response.readline().decode("utf-8") == "\n":
                    break
            started = time.perf_counter()
            with transcript.open("a", encoding="utf-8") as handle:
                handle.write("sse-delta-line\n")
            payload = ""
            while time.perf_counter() - started < 2.0:
                line = response.readline().decode("utf-8")
                if line.startswith("data: "):
                    payload += line.removeprefix("data: ").strip()
                    if "sse-delta-line" in payload:
                        break
            elapsed = time.perf_counter() - started
        self.assertIn("sse-delta-line", payload)
        self.assertLess(elapsed, 0.2, "console SSE delta must arrive within 200 ms")

    def test_ai_console_rejects_empty_or_unavailable_input(self) -> None:
        self.request("POST", "/api/test/reset", {})
        with self.assertRaises(HTTPError) as empty_ctx:
            self.request("POST", "/api/ai-console/input", {"text": "   "})
        self.assertEqual(empty_ctx.exception.code, 400)

        self.request("POST", "/api/test/inject-host-state", {"copilot_state": {"status": "missing"}})
        with self.assertRaises(HTTPError) as missing_ctx:
            self.request("POST", "/api/ai-console/input", {"text": "hello"})
        self.assertEqual(missing_ctx.exception.code, 409)

    def test_test_environment_does_not_fallback_to_live_node_pty_state(self) -> None:
        self.request("POST", "/api/test/reset", {})
        status, console = self.request("GET", "/api/ai-console")
        self.assertEqual(status, 200)
        self.assertEqual(console["status"], "missing")
        self.assertNotIn("tmp\\copilot_admin_runner_state", str(console.get("source", "")))

        with self.assertRaises(HTTPError) as missing_ctx:
            self.request("POST", "/api/ai-console/input", {"text": "must-not-reach-production-queue"})
        self.assertEqual(missing_ctx.exception.code, 409)

    def test_read_json_file_retries_transient_invalid_json(self) -> None:
        file_path = app.REPO_ROOT / "tmp" / "copilot_admin_control_plane" / "transient-read.json"
        with mock.patch.object(Path, "is_file", return_value=True), mock.patch.object(
            Path,
            "read_text",
            side_effect=["{", '{"status":"running"}'],
        ):
            result = app.read_json_file(file_path, {})

        self.assertEqual("running", result["status"])

    def test_local_node_pty_sqlite_state_requires_live_wrapper_process(self) -> None:
        previous_env = os.environ.get("COPILOT_ADMIN_ENV")
        previous_disable_default_runner = os.environ.get("COPILOT_ADMIN_DISABLE_DEFAULT_HOST_RUNNER")
        previous_state_dir = app.NODE_PTY_STATE_DIR
        state_dir = app.REPO_ROOT / "tmp" / "copilot_admin_control_plane" / f"backend-stale-state-test-{uuid.uuid4().hex}"
        state_dir.mkdir(parents=True, exist_ok=True)
        queue_dir = state_dir / "queue"
        queue_dir.mkdir(exist_ok=True)
        queue_db = state_dir / "transport.sqlite"
        app.HOST_STATE_PATH.unlink(missing_ok=True)
        transport_db = state_dir / "copilot-admin-transport.sqlite"
        app.upsert_session_state(
            transport_db,
            {
                "session_id": app.NODE_PTY_SESSION_ID,
                "status": "running",
                "running": True,
                "wrapper_pid": 99999999,
                "launcher_pid": 99999998,
                "visible_window_expected": True,
                "input_queue_dir": str(queue_dir),
                "input_queue_db_path": str(queue_db),
                "trace_db_path": str(transport_db),
                "last_output_tail": "stale transcript",
            },
            session_id=app.NODE_PTY_SESSION_ID,
        )
        os.environ["COPILOT_ADMIN_ENV"] = "development"
        os.environ["COPILOT_ADMIN_DISABLE_DEFAULT_HOST_RUNNER"] = "1"
        app.NODE_PTY_STATE_DIR = state_dir
        try:
            backend = app.ControlPlaneBackend(app.REPO_ROOT)
            console = backend.ai_console()
            self.assertEqual(console["status"], "not_running")
            self.assertFalse(console["running"])
            self.assertFalse(console["visible_window_expected"])
            with self.assertRaises(app.ApiError) as ctx:
                backend.send_ai_console_input({"text": "must-not-queue"})
            self.assertEqual(ctx.exception.status_code, 409)
            self.assertTrue(queue_db.exists())
            conn = sqlite3.connect(queue_db)
            count = conn.execute("SELECT COUNT(*) FROM input_queue").fetchone()[0]
            conn.close()
            self.assertEqual(0, count)
        finally:
            if previous_env is None:
                os.environ.pop("COPILOT_ADMIN_ENV", None)
            else:
                os.environ["COPILOT_ADMIN_ENV"] = previous_env
            if previous_disable_default_runner is None:
                os.environ.pop("COPILOT_ADMIN_DISABLE_DEFAULT_HOST_RUNNER", None)
            else:
                os.environ["COPILOT_ADMIN_DISABLE_DEFAULT_HOST_RUNNER"] = previous_disable_default_runner
            app.NODE_PTY_STATE_DIR = previous_state_dir

    def test_report_path_traversal_rejected(self) -> None:
        with self.assertRaises(HTTPError) as ctx:
            self.request("GET", "/api/reports/..%5Csecret.md")
        self.assertEqual(ctx.exception.code, 400)

    def test_real_host_runner_status_and_dispatch(self) -> None:
        calls: list[dict] = []

        class FakeRunner(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args) -> None:  # noqa: A002
                return

            def send_payload(self, payload: dict, status: int = 200) -> None:
                encoded = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

            def do_GET(self) -> None:  # noqa: N802
                calls.append({"method": "GET", "path": self.path})
                self.send_payload(
                    {
                        "status": "ok",
                        "host_runner": {"status": "ok"},
                        "copilot_session": {"status": "running", "input_queue": {"pending": 0}},
                        "browser_session": {"status": "running", "port": 9222},
                    }
                )

            def do_POST(self) -> None:  # noqa: N802
                length = int(self.headers.get("Content-Length", "0") or "0")
                body = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
                calls.append({"method": "POST", "path": self.path, "body": body})
                if self.path == "/api/session/start":
                    self.send_payload({"status": "started", "copilot": {"status": "started"}, "browser": {"status": "started"}})
                elif self.path == "/copilot/input":
                    self.send_payload({"status": "queued", "input": {"input_id": "fake-input"}})
                else:
                    self.send_payload({"error": "not found"}, 404)

        runner = ThreadingHTTPServer(("127.0.0.1", 0), FakeRunner)
        runner_thread = threading.Thread(target=runner.serve_forever, daemon=True)
        runner_thread.start()
        previous = os.environ.get("COPILOT_ADMIN_HOST_RUNNER_URL")
        previous_allow_test_runner = os.environ.get("COPILOT_ADMIN_ALLOW_TEST_HOST_RUNNER")
        os.environ["COPILOT_ADMIN_HOST_RUNNER_URL"] = f"http://127.0.0.1:{runner.server_address[1]}"
        os.environ["COPILOT_ADMIN_ALLOW_TEST_HOST_RUNNER"] = "1"
        try:
            backend = app.ControlPlaneBackend(app.REPO_ROOT)
            server = app.make_server("127.0.0.1", 0, backend)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()

            def local_request(method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
                data = None if payload is None else json.dumps(payload).encode("utf-8")
                req = Request(
                    f"http://127.0.0.1:{server.server_address[1]}{path}",
                    data=data,
                    method=method,
                    headers={"Content-Type": "application/json", "X-Trace-Id": "real-runner-test"},
                )
                with urlopen(req, timeout=5) as response:
                    return response.status, json.loads(response.read().decode("utf-8"))

            try:
                local_request("POST", "/api/test/reset", {})
                status, aggregate = local_request("GET", "/api/status")
                self.assertEqual(status, 200)
                self.assertEqual(aggregate["host_runner"]["status"], "ok")
                self.assertEqual(aggregate["copilot_session"]["status"], "running")
                self.assertEqual(aggregate["browser_session"]["status"], "running")

                status, session_job = local_request("POST", "/api/session/start", {})
                self.assertEqual(status, 201)
                self.assertEqual(session_job["status"], "running")
                self.assertEqual(session_job["dispatch"]["target"], "host-runner")
                session_start_calls = [call for call in calls if call["method"] == "POST" and call["path"] == "/api/session/start"]
                self.assertTrue(session_start_calls)
                self.assertTrue(session_start_calls[-1]["body"]["restart_existing"])

                status, hidden_session_job = local_request("POST", "/api/session/start", {"hidden_window": True})
                self.assertEqual(status, 201)
                self.assertEqual(hidden_session_job["dispatch"]["target"], "host-runner")
                session_start_calls = [call for call in calls if call["method"] == "POST" and call["path"] == "/api/session/start"]
                self.assertTrue(session_start_calls)
                self.assertTrue(session_start_calls[-1]["body"]["hidden_window"])
                self.assertTrue(session_start_calls[-1]["body"]["restart_existing"])

                status, input_job = local_request("POST", "/api/jobs", {"type": "custom", "prompt": "smoke"})
                self.assertEqual(status, 201)
                self.assertEqual(input_job["status"], "running")
                self.assertEqual(input_job["dispatch"]["response"]["status"], "queued")

                status, console = local_request("GET", "/api/ai-console")
                self.assertEqual(status, 200)
                self.assertEqual(console["status"], "running")

                status, console_input = local_request("POST", "/api/ai-console/input", {"text": "frontend ai-console smoke"})
                self.assertEqual(status, 202)
                self.assertTrue(console_input["accepted"])
                self.assertEqual(console_input["target"], "host-runner")
                input_calls = [call for call in calls if call["method"] == "POST" and call["path"] == "/copilot/input"]
                self.assertTrue(input_calls)
                self.assertTrue(input_calls[-1]["body"]["text"].startswith("frontend ai-console smoke\n\nStandardinstruktion: "))
                self.assertIn(AI_CONSOLE_STANDARD_INSTRUCTION, input_calls[-1]["body"]["text"])
                self.assertTrue(input_calls[-1]["body"]["clear_line"])
                self.assertIn("trace_id", input_calls[-1]["body"])
                self.assertIn("backend_accepted_at", input_calls[-1]["body"])

                status, esc_input = local_request("POST", "/api/ai-console/input", {"text": "\u001b", "submit": False, "clear_line": False})
                self.assertEqual(status, 202)
                self.assertTrue(esc_input["accepted"])
                self.assertTrue(input_calls[-1]["body"]["text"].startswith("frontend ai-console smoke\n\nStandardinstruktion: "))
                input_calls = [call for call in calls if call["method"] == "POST" and call["path"] == "/copilot/input"]
                self.assertEqual(input_calls[-1]["body"]["text"], "\u001b")
                self.assertFalse(input_calls[-1]["body"]["submit"])
                self.assertFalse(input_calls[-1]["body"]["clear_line"])
            finally:
                server.shutdown()
                server.server_close()
        finally:
            runner.shutdown()
            runner.server_close()
            if previous is None:
                os.environ.pop("COPILOT_ADMIN_HOST_RUNNER_URL", None)
            else:
                os.environ["COPILOT_ADMIN_HOST_RUNNER_URL"] = previous
            if previous_allow_test_runner is None:
                os.environ.pop("COPILOT_ADMIN_ALLOW_TEST_HOST_RUNNER", None)
            else:
                os.environ["COPILOT_ADMIN_ALLOW_TEST_HOST_RUNNER"] = previous_allow_test_runner

    def test_session_start_job_fails_when_host_runner_start_fails(self) -> None:
        class FakeRunner(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args) -> None:  # noqa: A002
                return

            def send_payload(self, payload: dict, status: int = 200) -> None:
                encoded = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

            def do_GET(self) -> None:  # noqa: N802
                self.send_payload(
                    {
                        "status": "ok",
                        "host_runner": {"status": "ok"},
                        "copilot_session": {"status": "not_running", "input_queue": {"pending": 0}},
                        "browser_session": {"status": "running", "port": 9222},
                    }
                )

            def do_POST(self) -> None:  # noqa: N802
                length = int(self.headers.get("Content-Length", "0") or "0")
                _body = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
                if self.path == "/api/session/start":
                    self.send_payload(
                        {
                            "status": "failed",
                            "copilot": {"status": "failed", "stderr": "stale launcher"},
                            "browser": {"status": "started"},
                        }
                    )
                else:
                    self.send_payload({"error": "not found"}, 404)

        runner = ThreadingHTTPServer(("127.0.0.1", 0), FakeRunner)
        runner_thread = threading.Thread(target=runner.serve_forever, daemon=True)
        runner_thread.start()
        previous = os.environ.get("COPILOT_ADMIN_HOST_RUNNER_URL")
        previous_allow_test_runner = os.environ.get("COPILOT_ADMIN_ALLOW_TEST_HOST_RUNNER")
        os.environ["COPILOT_ADMIN_HOST_RUNNER_URL"] = f"http://127.0.0.1:{runner.server_address[1]}"
        os.environ["COPILOT_ADMIN_ALLOW_TEST_HOST_RUNNER"] = "1"
        try:
            backend = app.ControlPlaneBackend(app.REPO_ROOT)
            status, session_job = self.request("POST", "/api/session/start", {})
            self.assertEqual(status, 201)
            self.assertEqual(session_job["status"], "failed")
            self.assertFalse(session_job["dispatch"]["dispatched"])
            self.assertIn("stale launcher", session_job["dispatch"]["reason"])
        finally:
            runner.shutdown()
            runner.server_close()
            if previous is None:
                os.environ.pop("COPILOT_ADMIN_HOST_RUNNER_URL", None)
            else:
                os.environ["COPILOT_ADMIN_HOST_RUNNER_URL"] = previous
            if previous_allow_test_runner is None:
                os.environ.pop("COPILOT_ADMIN_ALLOW_TEST_HOST_RUNNER", None)
            else:
                os.environ["COPILOT_ADMIN_ALLOW_TEST_HOST_RUNNER"] = previous_allow_test_runner


if __name__ == "__main__":
    unittest.main()
