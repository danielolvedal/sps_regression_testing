from __future__ import annotations

import json
import sys
import threading
import time
import unittest
from pathlib import Path
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parents[4]
BACKEND_DIR = REPO_ROOT / "tools" / "source" / "copilot_admin_control_plane" / "backend"
FRONTEND_DIR = REPO_ROOT / "tools" / "source" / "copilot_admin_control_plane" / "frontend"
sys.path.insert(0, str(BACKEND_DIR))
import app  # noqa: E402


class ControlPlaneDevE2ETests(unittest.TestCase):
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

    def setUp(self) -> None:
        self.request("POST", "/api/test/reset", {})

    def request(self, method: str, path: str, payload: dict | None = None, trace_id: str = "e2e-trace") -> tuple[int, dict]:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=data,
            method=method,
            headers={"Content-Type": "application/json", "X-Trace-Id": trace_id},
        )
        with urlopen(req, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def inject_running_host_state(self) -> None:
        queue_dir = REPO_ROOT / "tmp" / "copilot_admin_control_plane" / "e2e-input-queue"
        payload = {
            "host_runner_state": {"status": "ok", "capabilities": ["node-pty", "browser", "dry-run"]},
            "copilot_state": {
                "status": "running",
                "session_id": "e2e-copilot-session",
                "input_queue_dir": str(queue_dir),
                "user_input_required": False,
                "last_output_tail": "E2E injected Copilot session is running.",
            },
            "browser_state": {
                "status": "running",
                "browser_id": "e2e-browser",
                "debug_port": 9222,
                "user_visible": True,
                "requires_login": True,
            },
        }
        self.request("POST", "/api/test/inject-host-state", payload)

    def test_startup_api_and_frontend_static_contract(self) -> None:
        html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
        js = (FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
        for hook in [
            'data-testid="start-session-button"',
            'data-testid="view-copilot"',
            'data-testid="copilot-console-output"',
            'data-testid="copilot-console-input"',
            'data-testid="status-diode"',
            'data-testid="mermaid-viewport"',
            'data-testid="report-reader"',
            'data-testid="frontend-log"',
        ]:
            self.assertIn(hook, html)
        for endpoint in [
            "/api/session/start",
            "/api/session/copilot",
            "/api/session/browser",
            "/api/copilot/console",
            "/api/copilot/input",
            "/api/regression/mermaid",
            "/api/frontend/events",
        ]:
            self.assertIn(endpoint, js)

        status, health = self.request("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(health["status"], "ok")

        self.inject_running_host_state()
        started = time.perf_counter()
        status, session_job = self.request("POST", "/api/session/start", {})
        elapsed = time.perf_counter() - started
        self.assertEqual(status, 201)
        self.assertLess(elapsed, 1.0, "session start API must return before waiting for Copilot work")
        self.assertEqual(session_job["type"], "session_start")
        self.assertEqual(session_job["status"], "running")
        self.assertTrue(session_job["dispatch"]["dispatched"])

    def test_status_diode_job_lifecycle_and_mode_switching(self) -> None:
        self.inject_running_host_state()

        for mode in ["learning", "testing"]:
            status, job = self.request("POST", "/api/copilot/mode", {"mode": mode}, trace_id=f"e2e-{mode}")
            self.assertEqual(status, 201)
            self.assertEqual(job["status"], "running")
            self.assertIn(f"{mode} mode", job["prompt"])
            status, aggregate = self.request("GET", "/api/status")
            self.assertEqual(status, 200)
            self.assertEqual(aggregate["mode"], mode)
            self.assertEqual(aggregate["status_diode"], "yellow")

        self.request("POST", "/api/test/reset", {})
        self.inject_running_host_state()
        status, job = self.request("POST", "/api/regression/run", {"scope": "selected", "test_id": "regression-document-index-coverage"})
        self.assertEqual(status, 201)
        self.assertEqual(job["status"], "running")
        self.assertIn("regression-document-index-coverage", job["prompt"])

        self.request("POST", "/api/test/inject-host-state", {"job_updates": [{"job_id": job["job_id"], "status": "completed_unopened", "result": {"summary": "E2E completed"}}]})
        status, aggregate = self.request("GET", "/api/status")
        self.assertEqual(status, 200)
        self.assertEqual(aggregate["status_diode"], "green")

        status, opened = self.request("POST", f"/api/jobs/{job['job_id']}/open", {})
        self.assertEqual(status, 200)
        self.assertEqual(opened["status"], "completed_opened")
        status, aggregate = self.request("GET", "/api/status")
        self.assertEqual(status, 200)
        self.assertEqual(aggregate["status_diode"], "red")

    def test_mermaid_reports_user_input_required_and_log_correlation(self) -> None:
        status, catalog = self.request("GET", "/api/regression/tests")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(catalog["count"], 7)
        status, mermaid = self.request("GET", "/api/regression/mermaid")
        self.assertEqual(status, 200)
        self.assertRegex(mermaid["mermaid"].lower(), r"(graph|flowchart)")
        self.assertGreaterEqual(mermaid["bytes"], 100)

        status, reports = self.request("GET", "/api/reports")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(reports["count"], 1)
        status, report = self.request("GET", f"/api/reports/{reports['reports'][0]['report_id']}")
        self.assertEqual(status, 200)
        self.assertIn("markdown", report)

        trace_id = "e2e-log-correlation"
        self.request("POST", "/api/frontend/events", {"event": "button_clicked", "trace_id": trace_id, "user_action": "run_selected_regression"}, trace_id=trace_id)
        self.inject_running_host_state()
        status, job = self.request("POST", "/api/regression/run", {"scope": "all"}, trace_id=trace_id)
        self.assertEqual(status, 201)
        self.request("POST", "/api/test/inject-host-state", {"job_updates": [{"job_id": job["job_id"], "status": "user_input_required", "output_tail": "Copilot asks for workspace trust."}]})
        status, aggregate = self.request("GET", "/api/status")
        self.assertEqual(status, 200)
        self.assertEqual(aggregate["status_diode"], "yellow")
        self.assertEqual(aggregate["latest_job"]["status"], "user_input_required")

        log_files = sorted((REPO_ROOT / "tmp" / "copilot_admin_control_plane" / "logs").glob("backend-*.jsonl"))
        self.assertTrue(log_files)
        combined = "\n".join(path.read_text(encoding="utf-8") for path in log_files)
        self.assertIn(trace_id, combined)
        self.assertIn("frontend", combined)
        self.assertIn("job_created", combined)

    def test_copilot_console_contract_input_and_logs(self) -> None:
        self.inject_running_host_state()
        status, console = self.request("GET", "/api/copilot/console", trace_id="console-e2e")
        self.assertEqual(status, 200)
        self.assertEqual(console["status"], "running")
        self.assertIn("E2E injected Copilot session", console["transcript_tail"])
        self.assertIsNone(console["model_hint"])
        self.assertFalse(console["model_verified"])
        self.assertIsNone(console["permissions_hint"])
        self.assertFalse(console["permissions_verified"])

        started = time.perf_counter()
        status, queued = self.request("POST", "/api/copilot/input", {"text": "console e2e input"}, trace_id="console-e2e")
        elapsed = time.perf_counter() - started
        self.assertEqual(status, 202)
        self.assertLess(elapsed, 1.0, "console input API must not wait for Copilot response")
        self.assertTrue(queued["accepted"])
        self.assertEqual(queued["target"], "local-node-pty")
        queue_dir = REPO_ROOT / "tmp" / "copilot_admin_control_plane" / "e2e-input-queue"
        queue_files = list(queue_dir.glob("*.json"))
        self.assertTrue(queue_files)
        self.assertTrue(json.loads(queue_files[-1].read_text(encoding="utf-8"))["clear_line"])

        log_files = sorted((REPO_ROOT / "tmp" / "copilot_admin_control_plane" / "logs").glob("backend-*.jsonl"))
        self.assertTrue(log_files)
        combined = "\n".join(path.read_text(encoding="utf-8") for path in log_files)
        self.assertIn("console-e2e", combined)
        self.assertIn("copilot_console_input_sent", combined)


if __name__ == "__main__":
    unittest.main()
