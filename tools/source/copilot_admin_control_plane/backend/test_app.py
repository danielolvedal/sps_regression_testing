from __future__ import annotations

import json
import os
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

os.environ.setdefault("COPILOT_ADMIN_ENV", "test")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import app


class BackendSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = app.make_server("127.0.0.1", 0, app.APP)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()

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

        req = Request(f"http://127.0.0.1:{self.port}/app.js", method="GET")
        with urlopen(req, timeout=5) as response:
            js = response.read().decode("utf-8")
            status = response.status
        self.assertEqual(status, 200)
        self.assertIn("/api/status", js)

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

    def test_frontend_log_ingestion(self) -> None:
        status, response = self.request("POST", "/api/frontend/events", {"event": "page_view", "trace_id": "frontend-trace"})
        self.assertEqual(status, 202)
        self.assertTrue(response["accepted"])
        self.assertEqual(response["trace_id"], "test-trace")

    def test_copilot_console_reads_injected_state_and_queues_local_input(self) -> None:
        queue_dir = app.REPO_ROOT / "tmp" / "copilot_admin_control_plane" / "backend-console-test-queue"
        queue_dir.mkdir(parents=True, exist_ok=True)
        for path in queue_dir.glob("*.json*"):
            path.unlink()
        self.request(
            "POST",
            "/api/test/inject-host-state",
            {
                "copilot_state": {
                    "status": "running",
                    "running": True,
                    "input_queue_dir": str(queue_dir),
                    "input_queue": {"pending": 0},
                    "last_output_tail": "Console transcript from injected state.",
                    "user_input_required": True,
                    "user_input_reason": "confirmation_prompt",
                }
            },
        )

        status, console = self.request("GET", "/api/copilot/console")
        self.assertEqual(status, 200)
        self.assertTrue(console["running"])
        self.assertTrue(console["user_input_required"])
        self.assertIn("Console transcript", console["transcript_tail"])

        status, queued = self.request("POST", "/api/copilot/input", {"text": "svara ja"})
        self.assertEqual(status, 202)
        self.assertTrue(queued["accepted"])
        self.assertEqual(queued["target"], "local-node-pty")
        queue_files = list(queue_dir.glob("*.json"))
        self.assertEqual(1, len(queue_files))
        queued_body = json.loads(queue_files[0].read_text(encoding="utf-8"))
        self.assertEqual("svara ja", queued_body["text"])
        self.assertTrue(queued_body["clear_line"])

        status, tab_queued = self.request("POST", "/api/copilot/input", {"text": "\t", "submit": False, "clear_line": False})
        self.assertEqual(status, 202)
        self.assertTrue(tab_queued["accepted"])
        queue_bodies = [json.loads(path.read_text(encoding="utf-8")) for path in queue_dir.glob("*.json")]
        self.assertTrue(any(body["text"] == "\t" and body["clear_line"] is False and body["submit"] is False for body in queue_bodies))

    def test_copilot_console_supports_cursor_based_transcript_polling(self) -> None:
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
        status, first = self.request("GET", "/api/copilot/console?limit=1024")
        self.assertEqual(status, 200)
        self.assertEqual(first["transcript"]["mode"], "tail")
        self.assertIn("line-2", first["transcript"]["text"])
        cursor = first["transcript"]["next_cursor"]

        with transcript.open("a", encoding="utf-8") as handle:
            handle.write("line-3\n")
        status, second = self.request("GET", f"/api/copilot/console?cursor={cursor}&limit=1024")
        self.assertEqual(status, 200)
        self.assertEqual(second["transcript"]["mode"], "delta")
        self.assertEqual(second["transcript"]["text"].replace("\r\n", "\n"), "line-3\n")
        self.assertGreater(second["transcript"]["next_cursor"], cursor)

    def test_copilot_console_rejects_empty_or_unavailable_input(self) -> None:
        self.request("POST", "/api/test/reset", {})
        with self.assertRaises(HTTPError) as empty_ctx:
            self.request("POST", "/api/copilot/input", {"text": "   "})
        self.assertEqual(empty_ctx.exception.code, 400)

        self.request("POST", "/api/test/inject-host-state", {"copilot_state": {"status": "missing"}})
        with self.assertRaises(HTTPError) as missing_ctx:
            self.request("POST", "/api/copilot/input", {"text": "hello"})
        self.assertEqual(missing_ctx.exception.code, 409)

    def test_test_environment_does_not_fallback_to_live_node_pty_state(self) -> None:
        self.request("POST", "/api/test/reset", {})
        status, console = self.request("GET", "/api/copilot/console")
        self.assertEqual(status, 200)
        self.assertEqual(console["status"], "missing")
        self.assertNotIn("tmp\\copilot_admin_runner_state", str(console.get("source", "")))

        with self.assertRaises(HTTPError) as missing_ctx:
            self.request("POST", "/api/copilot/input", {"text": "must-not-reach-production-queue"})
        self.assertEqual(missing_ctx.exception.code, 409)

    def test_local_node_pty_state_requires_live_wrapper_process(self) -> None:
        previous_env = os.environ.get("COPILOT_ADMIN_ENV")
        previous_state_path = app.NODE_PTY_STATE_PATH
        previous_state_dir = app.NODE_PTY_STATE_DIR
        previous_window_state_path = app.NODE_PTY_WINDOW_STATE_PATH
        state_dir = app.REPO_ROOT / "tmp" / "copilot_admin_control_plane" / "backend-stale-state-test"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_path = state_dir / "node-pty-copilot-session.json"
        window_state_path = state_dir / "node-pty-copilot-window.json"
        queue_dir = state_dir / "queue"
        queue_dir.mkdir(exist_ok=True)
        state_path.write_text(
            json.dumps(
                {
                    "status": "running",
                    "running": True,
                    "wrapper_pid": 99999999,
                    "input_queue_dir": str(queue_dir),
                    "last_output_tail": "stale transcript",
                }
            ),
            encoding="utf-8",
        )
        window_state_path.write_text(json.dumps({"visible_window_expected": True}), encoding="utf-8")
        os.environ["COPILOT_ADMIN_ENV"] = "development"
        app.NODE_PTY_STATE_DIR = state_dir
        app.NODE_PTY_STATE_PATH = state_path
        app.NODE_PTY_WINDOW_STATE_PATH = window_state_path
        try:
            backend = app.ControlPlaneBackend(app.REPO_ROOT)
            console = backend.copilot_console()
            self.assertEqual(console["status"], "not_running")
            self.assertFalse(console["running"])
            self.assertFalse(console["visible_window_expected"])
            with self.assertRaises(app.ApiError) as ctx:
                backend.send_copilot_console_input({"text": "must-not-queue"})
            self.assertEqual(ctx.exception.status_code, 409)
            self.assertEqual([], list(queue_dir.glob("*.json")))
        finally:
            if previous_env is None:
                os.environ.pop("COPILOT_ADMIN_ENV", None)
            else:
                os.environ["COPILOT_ADMIN_ENV"] = previous_env
            app.NODE_PTY_STATE_DIR = previous_state_dir
            app.NODE_PTY_STATE_PATH = previous_state_path
            app.NODE_PTY_WINDOW_STATE_PATH = previous_window_state_path

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

                status, hidden_session_job = local_request("POST", "/api/session/start", {"hidden_window": True})
                self.assertEqual(status, 201)
                self.assertEqual(hidden_session_job["dispatch"]["target"], "host-runner")
                session_start_calls = [call for call in calls if call["method"] == "POST" and call["path"] == "/api/session/start"]
                self.assertTrue(session_start_calls)
                self.assertTrue(session_start_calls[-1]["body"]["hidden_window"])

                status, input_job = local_request("POST", "/api/jobs", {"type": "custom", "prompt": "smoke"})
                self.assertEqual(status, 201)
                self.assertEqual(input_job["status"], "running")
                self.assertEqual(input_job["dispatch"]["response"]["status"], "queued")

                status, console = local_request("GET", "/api/copilot/console")
                self.assertEqual(status, 200)
                self.assertEqual(console["status"], "running")

                status, console_input = local_request("POST", "/api/copilot/input", {"text": "frontend console smoke"})
                self.assertEqual(status, 202)
                self.assertTrue(console_input["accepted"])
                self.assertEqual(console_input["target"], "host-runner")
                input_calls = [call for call in calls if call["method"] == "POST" and call["path"] == "/copilot/input"]
                self.assertTrue(input_calls)
                self.assertEqual(input_calls[-1]["body"]["text"], "frontend console smoke")
                self.assertTrue(input_calls[-1]["body"]["clear_line"])

                status, esc_input = local_request("POST", "/api/copilot/input", {"text": "\u001b", "submit": False, "clear_line": False})
                self.assertEqual(status, 202)
                self.assertTrue(esc_input["accepted"])
                self.assertEqual(input_calls[-1]["body"]["text"], "frontend console smoke")
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


if __name__ == "__main__":
    unittest.main()
