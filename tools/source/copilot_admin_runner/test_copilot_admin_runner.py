from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import copilot_admin_runner as runner


class CopilotAdminRunnerTests(unittest.TestCase):
    def test_node_pty_startup_uses_permissions_allow_all_command_and_clears_line(self) -> None:
        source = (Path(__file__).resolve().parent / "node_pty_poc" / "node_pty_poc.mjs").read_text(encoding="utf-8")

        self.assertIn("const PERMISSION_ALLOW_ALL_COMMAND = '/permissions allow-all';", source)
        self.assertIn("function sendStartupCommand(term, command)", source)
        self.assertIn("term.write('\\x15');", source)
        self.assertIn("sendStartupCommand(term, PERMISSION_ALLOW_ALL_COMMAND);", source)
        self.assertNotIn("term.write('/allow-all\\r');", source)

    def test_window_launcher_script_cleans_up_stale_launcher_without_restart_flag(self) -> None:
        source = (
            Path(__file__).resolve().parents[3]
            / "runtime"
            / "windows"
            / "copilot-admin"
            / "node-pty"
            / "start-copilot-admin-node-pty-window.ps1"
        ).read_text(encoding="utf-8")

        self.assertIn("$wrapperStillRunning = $false", source)
        self.assertIn("if (-not $RestartExisting -and $wrapperStillRunning)", source)
        self.assertIn('Stop-Process -Id $existingSession.launcher_pid -Force', source)

    def test_enqueue_copilot_input_writes_sqlite_queue_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            queue_dir = Path(tmp_dir)
            transport_db = queue_dir / "transport.sqlite"
            with (
                mock.patch.object(runner, "NODE_PTY_INPUT_QUEUE_DIR", queue_dir),
                mock.patch.object(runner, "TRANSPORT_DB_PATH", transport_db),
                mock.patch.object(runner, "copilot_session_status", return_value={"running": True}),
                mock.patch.object(runner, "log_event"),
            ):
                result = runner.enqueue_copilot_input(
                    "hej",
                    clear_line=True,
                    submit=True,
                    trace_id="trace-1",
                    job_id="job-1",
                )

            self.assertTrue(transport_db.exists())
            conn = sqlite3.connect(transport_db)
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM input_queue ORDER BY id").fetchall()
            conn.close()
            self.assertEqual(1, len(rows))
            queue_payload = dict(rows[0])
            self.assertEqual("\x15hej", queue_payload["text"])
            self.assertEqual("hej", queue_payload["display_text"])
            self.assertEqual(1, queue_payload["clear_line"])
            self.assertEqual("queued", result["status"])

    def test_read_json_file_retries_transient_invalid_json(self) -> None:
        file_path = Path("C:\\temp\\runner-state.json")
        with mock.patch.object(Path, "is_file", return_value=True), mock.patch.object(
            Path,
            "read_text",
            side_effect=["{", '{"status":"running"}'],
        ):
            result = runner.read_json_file(file_path)

        self.assertEqual("running", result["status"])

    def test_copilot_session_status_reads_sqlite_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            state_dir = Path(tmp_dir)
            transport_db = state_dir / "copilot-admin-transport.sqlite"
            runner.upsert_session_state(
                transport_db,
                {
                    "session_id": runner.NODE_PTY_SESSION_ID,
                    "status": "running",
                    "wrapper_pid": 1234,
                    "launcher_pid": 5678,
                    "visible_window_expected": True,
                    "startup_allow_all": True,
                    "allow_all_verified": True,
                    "last_output_tail": "sqlite state",
                },
                session_id=runner.NODE_PTY_SESSION_ID,
            )
            with (
                mock.patch.object(runner, "TRANSPORT_DB_PATH", transport_db),
                mock.patch.object(runner, "is_process_running", side_effect=lambda pid: pid == 1234 or pid == 5678),
            ):
                result = runner.copilot_session_status()

            self.assertEqual("running", result["status"])
            self.assertEqual(str(transport_db), result["state_path"])
            self.assertEqual("sqlite", result["state_storage"])
            self.assertEqual("sqlite state", result["last_output_tail"])

    def test_stop_browser_session_returns_not_owned_for_untracked_running_browser(self) -> None:
        with (
            mock.patch.object(runner, "browser_session_status", return_value={"running": True, "status": "running", "port": 9222}),
            mock.patch.object(runner, "read_json_file", return_value={}),
            mock.patch.object(runner, "resolve_browser_process_id", return_value=None),
            mock.patch.object(runner, "stop_process", return_value=False),
            mock.patch.object(runner, "get_browser_debug_info", return_value={"Browser": "Edge"}),
            mock.patch.object(runner, "log_event"),
        ):
            result = runner.stop_browser_session(port=9222, timeout_seconds=0)

        self.assertEqual("not_owned", result["status"])
        self.assertIn("No owned browser processId was recorded", result["note"])
