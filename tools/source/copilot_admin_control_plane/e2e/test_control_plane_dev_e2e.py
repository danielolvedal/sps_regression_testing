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
from pathlib import Path
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parents[4]
BACKEND_DIR = REPO_ROOT / "tools" / "source" / "copilot_admin_control_plane" / "backend"
FRONTEND_DIR = REPO_ROOT / "tools" / "source" / "copilot_admin_control_plane" / "frontend"
os.environ.setdefault("COPILOT_ADMIN_ENV", "test")
sys.path.insert(0, str(BACKEND_DIR))
import app  # noqa: E402


class ControlPlaneDevE2ETests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.test_state_dir = REPO_ROOT / "tmp" / "copilot_admin_control_plane" / f"backend-dev-e2e-state-{uuid.uuid4().hex}"
        cls.test_state_dir.mkdir(parents=True, exist_ok=True)
        cls.previous_state_dir = app.STATE_DIR
        cls.previous_jobs_path = app.JOBS_PATH
        cls.previous_host_state_path = app.HOST_STATE_PATH
        cls.previous_mode_path = app.MODE_PATH
        cls.previous_log_dir = app.LOG_DIR
        cls.previous_node_pty_state_dir = app.NODE_PTY_STATE_DIR
        cls.previous_node_pty_state_path = app.NODE_PTY_STATE_PATH
        cls.previous_node_pty_window_state_path = app.NODE_PTY_WINDOW_STATE_PATH
        cls.previous_reports_dir = app.REPORTS_DIR
        cls.previous_draft_tests_dir = app.DRAFT_TESTS_DIR
        app.STATE_DIR = cls.test_state_dir
        app.JOBS_PATH = cls.test_state_dir / "jobs.json"
        app.HOST_STATE_PATH = cls.test_state_dir / "injected-host-state.json"
        app.MODE_PATH = cls.test_state_dir / "current-mode.json"
        app.LOG_DIR = cls.test_state_dir / "logs"
        app.NODE_PTY_STATE_DIR = cls.test_state_dir / "runner-state"
        app.NODE_PTY_STATE_DIR.mkdir(parents=True, exist_ok=True)
        app.NODE_PTY_STATE_PATH = app.NODE_PTY_STATE_DIR / "node-pty-copilot-session.json"
        app.NODE_PTY_WINDOW_STATE_PATH = app.NODE_PTY_STATE_DIR / "node-pty-copilot-window.json"
        app.REPORTS_DIR = cls.test_state_dir / "reports"
        (app.REPORTS_DIR / "20260903v1" / "RegressionError01").mkdir(parents=True, exist_ok=True)
        (app.REPORTS_DIR / "20260903v1" / "summary.md").write_text(
            "# Summary\n\n| Test | Status | Detail |\n| --- | --- | --- |\n| regression-draft-smoke | failed | RegressionError01 |\n",
            encoding="utf-8",
        )
        (app.REPORTS_DIR / "20260903v1" / "RegressionError01" / "report.md").write_text(
            "# RegressionError01\n\nLocal report sample.\n",
            encoding="utf-8",
        )
        app.DRAFT_TESTS_DIR = cls.test_state_dir / "regression-drafts"
        draft_dir = app.DRAFT_TESTS_DIR / "danielolvedal"
        draft_dir.mkdir(parents=True, exist_ok=True)
        (draft_dir / "draft-smoke.md").write_text(
            """# Regressionstest - draft smoke

## Test-ID

regression-draft-smoke

## Summary

Smoke-test for a per-user regression draft.

## Dependencies

- none

## Typ

Manual draft regression.

## Owner

danielolvedal
""",
            encoding="utf-8",
        )
        cls.backend = app.ControlPlaneBackend(REPO_ROOT)
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
        app.REPORTS_DIR = cls.previous_reports_dir
        app.DRAFT_TESTS_DIR = cls.previous_draft_tests_dir
        shutil.rmtree(cls.test_state_dir, ignore_errors=True)

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
        queue_dir = REPO_ROOT / "tmp" / "copilot_admin_control_plane" / f"e2e-input-queue-{uuid.uuid4().hex}"
        queue_dir.mkdir(parents=True, exist_ok=True)
        queue_db = queue_dir / "transport.sqlite"
        payload = {
            "host_runner_state": {"status": "ok", "capabilities": ["node-pty", "browser", "dry-run"]},
            "copilot_state": {
                "status": "running",
                "session_id": "e2e-copilot-session",
                "input_queue_dir": str(queue_dir),
                "input_queue_db_path": str(queue_db),
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
            'data-testid="manual-list"',
            'data-testid="manual-reader"',
            'data-testid="view-ai-console"',
            'data-testid="ai-console-output"',
            'data-testid="ai-console-input"',
            'data-testid="status-diode"',
            'data-testid="ai-console-project"',
            'data-testid="ai-console-ready"',
            'data-testid="mermaid-viewport"',
            'data-testid="report-reader"',
            'data-testid="frontend-log"',
        ]:
            self.assertIn(hook, html)
        for endpoint in [
            "/api/session/start",
            "/api/status",
            "/api/jobs",
            "/api/ai-console",
            "/api/ai-console/input",
            "/api/manuals",
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

        status, manuals = self.request("GET", "/api/manuals")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(manuals["count"], 1)
        status, manual = self.request("GET", f"/api/manuals/{manuals['manuals'][0]['manual_id']}")
        self.assertEqual(status, 200)
        self.assertIn("markdown", manual)

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

    def test_ai_console_contract_input_and_logs(self) -> None:
        self.inject_running_host_state()
        status, console = self.request("GET", "/api/ai-console", trace_id="console-e2e")
        self.assertEqual(status, 200)
        self.assertEqual(console["status"], "running")
        self.assertIn("E2E injected Copilot session", console["transcript_tail"])
        self.assertIsNone(console["model_hint"])
        self.assertFalse(console["model_verified"])
        self.assertIsNone(console["permissions_hint"])
        self.assertFalse(console["permissions_verified"])

        started = time.perf_counter()
        status, queued = self.request("POST", "/api/ai-console/input", {"text": "console e2e input"}, trace_id="console-e2e")
        elapsed = time.perf_counter() - started
        self.assertEqual(status, 202)
        self.assertLess(elapsed, 0.5, "console input API must enqueue within 500 ms")
        self.assertTrue(queued["accepted"])
        self.assertEqual(queued["target"], "local-node-pty")
        queue_db = Path(console["input_queue_db_path"])
        conn = sqlite3.connect(queue_db)
        row = conn.execute("SELECT text, clear_line FROM input_queue ORDER BY id DESC LIMIT 1").fetchone()
        conn.close()
        self.assertIsNotNone(row)
        self.assertIn("console e2e input", row[0])
        self.assertIn("Om instruktionen är oklar eller otydlig ställ klargörande frågor", row[0])
        self.assertEqual(1, row[1])

        log_files = sorted((self.test_state_dir / "logs").glob("backend-*.jsonl"))
        self.assertTrue(log_files)
        combined = "\n".join(path.read_text(encoding="utf-8") for path in log_files)
        self.assertIn("console-e2e", combined)
        self.assertIn("ai_console_input_sent", combined)


if __name__ == "__main__":
    unittest.main()
