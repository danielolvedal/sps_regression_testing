from __future__ import annotations

import base64
import json
import os
import shutil
import socket
import struct
import subprocess
import sys
import threading
import time
import unittest
from pathlib import Path
from urllib.request import Request, urlopen


os.environ.setdefault("COPILOT_ADMIN_ENV", "test")
REPO_ROOT = Path(__file__).resolve().parents[4]
BACKEND_DIR = REPO_ROOT / "tools" / "source" / "copilot_admin_control_plane" / "backend"
sys.path.insert(0, str(BACKEND_DIR))
import app  # noqa: E402


class CdpClient:
    def __init__(self, websocket_url: str):
        if not websocket_url.startswith("ws://"):
            raise ValueError(f"Unsupported websocket URL: {websocket_url}")
        host_port, path = websocket_url.removeprefix("ws://").split("/", 1)
        host, port_text = host_port.rsplit(":", 1)
        self.socket = socket.create_connection((host, int(port_text)), timeout=10)
        self.socket.settimeout(1)
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        request = (
            f"GET /{path} HTTP/1.1\r\n"
            f"Host: {host_port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.socket.sendall(request.encode("ascii"))
        headers = self.socket.recv(4096)
        if b" 101 " not in headers.split(b"\r\n", 1)[0]:
            raise RuntimeError(f"CDP websocket upgrade failed: {headers!r}")
        self.next_id = 1

    def close(self) -> None:
        self.socket.close()

    def command(self, method: str, params: dict | None = None) -> dict:
        message_id = self.next_id
        self.next_id += 1
        self._send(json.dumps({"id": message_id, "method": method, "params": params or {}}).encode("utf-8"))
        deadline = time.time() + 60
        while time.time() < deadline:
            payload = self._recv()
            if not payload:
                continue
            message = json.loads(payload.decode("utf-8"))
            if message.get("id") == message_id:
                if "error" in message:
                    raise AssertionError(json.dumps(message["error"], ensure_ascii=False))
                return message.get("result", {})
        raise TimeoutError(f"Timed out waiting for CDP response to {method}.")

    def _send(self, payload: bytes) -> None:
        mask = os.urandom(4)
        header = bytearray([0x81])
        length = len(payload)
        if length < 126:
            header.append(0x80 | length)
        elif length < 65536:
            header.extend([0x80 | 126, *struct.pack("!H", length)])
        else:
            header.extend([0x80 | 127, *struct.pack("!Q", length)])
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        self.socket.sendall(bytes(header) + mask + masked)

    def _recv_exact(self, size: int) -> bytes:
        data = b""
        while len(data) < size:
            try:
                chunk = self.socket.recv(size - len(data))
            except socket.timeout:
                if data:
                    continue
                return b""
            if not chunk:
                raise ConnectionError("CDP websocket closed.")
            data += chunk
        return data

    def _recv(self) -> bytes:
        header = self._recv_exact(2)
        if not header:
            return b""
        first, second = header
        opcode = first & 0x0F
        length = second & 0x7F
        if length == 126:
            length = struct.unpack("!H", self._recv_exact(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", self._recv_exact(8))[0]
        mask = self._recv_exact(4) if second & 0x80 else b""
        payload = self._recv_exact(length)
        if mask:
            payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        if opcode == 0x8:
            return b""
        if opcode == 0x9:
            return b""
        return payload


class FrontendBrowserE2ETests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.test_state_dir = REPO_ROOT / "tmp" / "copilot_admin_control_plane" / f"frontend-browser-e2e-state-{int(time.time() * 1000)}"
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
        cls.server = app.make_server("127.0.0.1", 0, app.ControlPlaneBackend(REPO_ROOT))
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
        self.inject_host_state()

    def request(self, method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=data,
            method=method,
            headers={"Content-Type": "application/json", "X-Trace-Id": "frontend-browser-e2e"},
        )
        with urlopen(req, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def inject_host_state(self) -> None:
        queue_dir = REPO_ROOT / "tmp" / "copilot_admin_control_plane" / "browser-e2e-input-queue"
        self.request(
            "POST",
            "/api/test/inject-host-state",
            {
                "host_runner_state": {"status": "ok", "capabilities": ["browser-e2e"]},
                "copilot_state": {
                    "status": "running",
                    "session_id": "browser-e2e-copilot",
                    "input_queue_dir": str(queue_dir),
                    "input_queue": {"pending": 0},
                    "user_input_required": False,
                    "visible_window_expected": True,
                    "last_output_tail": "Browser E2E Copilot session is running.",
                },
                "browser_state": {"status": "running", "browser_id": "browser-e2e", "debug_port": 9222},
            },
        )

    def find_browser(self) -> Path:
        candidates = [
            Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
            Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
            Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
            Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        ]
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        self.fail("Neither Chrome nor Edge is installed for browser E2E.")

    def free_port(self) -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])

    def launch_browser(self) -> tuple[subprocess.Popen, CdpClient, Path]:
        debug_port = self.free_port()
        profile = REPO_ROOT / "tmp" / "copilot_admin_control_plane" / f"browser-e2e-profile-{int(time.time() * 1000)}"
        shutil.rmtree(profile, ignore_errors=True)
        profile.mkdir(parents=True, exist_ok=True)
        browser = self.find_browser()
        process = subprocess.Popen(
            [
                str(browser),
                "--headless=new",
                "--disable-gpu",
                "--no-first-run",
                "--no-default-browser-check",
                f"--remote-debugging-port={debug_port}",
                f"--user-data-dir={profile}",
                "about:blank",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.time() + 15
        websocket_url = None
        while time.time() < deadline:
            try:
                with urlopen(f"http://127.0.0.1:{debug_port}/json/list", timeout=1) as response:
                    tabs = json.loads(response.read().decode("utf-8"))
                websocket_url = next(tab["webSocketDebuggerUrl"] for tab in tabs if tab.get("type") == "page")
                break
            except Exception:
                time.sleep(0.2)
        if websocket_url is None:
            process.terminate()
            self.fail("Browser did not expose a CDP page target.")
        return process, CdpClient(websocket_url), profile

    def test_ai_console_renders_prompt_box_like_console(self) -> None:
        self.request(
            "POST",
            "/api/test/inject-host-state",
            {
                "copilot_state": {
                    "status": "running",
                    "session_id": "browser-e2e-copilot",
                    "input_queue_dir": str(REPO_ROOT / "tmp" / "copilot_admin_control_plane" / "browser-e2e-input-queue"),
                    "input_queue": {"pending": 0},
                    "user_input_required": True,
                    "user_input_reason": "interactive_choice_prompt",
                    "visible_window_expected": True,
                    "last_output_tail": "C:\\Copilot_projects\\SPS [⎇ master*]                                                                                                  Session: 1390.31 AIC used \n╻▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄\n┃\n╹▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀\n v1.0.82 downloaded · run /restart to apply · ← open sidebar · / commands · ? help · tab next tab                                          Auto → GPT-5.6 Terra ",
                }
            },
        )
        process, cdp, profile = self.launch_browser()
        try:
            cdp.command("Runtime.enable")
            cdp.command("Page.enable")
            cdp.command("Page.navigate", {"url": f"http://127.0.0.1:{self.port}/"})
            for _ in range(50):
                ready = cdp.command("Runtime.evaluate", {"expression": "document.readyState", "returnByValue": True}).get("result", {}).get("value")
                if ready == "complete":
                    break
                time.sleep(0.1)
            verification = cdp.command(
                "Runtime.evaluate",
                {
                    "expression": r"""
(async () => {
  const failures = [];
  const q = (id) => document.querySelector(`[data-testid="${id}"]`);
  const waitFor = async (predicate, message, timeout = 7000) => {
    const started = Date.now();
    while (Date.now() - started < timeout) {
      if (await predicate()) return;
      await new Promise((resolve) => setTimeout(resolve, 100));
    }
    failures.push(message);
  };
  q("nav-ai-console").click();
  await waitFor(() => q("view-ai-console").classList.contains("active"), "AI console view did not open.");
  await waitFor(() => q("ai-console-output").querySelector(".copilot-prompt-box"), "Prompt box was not rendered.");
  const output = q("ai-console-output");
  return {
    failures,
    hasPromptBox: Boolean(output.querySelector(".copilot-prompt-box")),
    hasCursor: Boolean(output.querySelector(".copilot-prompt-cursor")),
    hasFooter: output.textContent.includes("v1.0.82 downloaded"),
    noRawBars: !output.textContent.includes("▄▄▄▄") && !output.textContent.includes("▀▀▀▀"),
  };
})()
""",
                    "awaitPromise": True,
                    "returnByValue": True,
                },
            )
            if "exceptionDetails" in verification:
                self.fail(json.dumps(verification["exceptionDetails"], ensure_ascii=False))
            value = verification.get("result", {}).get("value", {})
            self.assertEqual([], value.get("failures"), "\n".join(value.get("failures", [])))
            self.assertTrue(value.get("hasPromptBox"))
            self.assertTrue(value.get("hasCursor"))
            self.assertTrue(value.get("hasFooter"))
            self.assertTrue(value.get("noRawBars"))
        finally:
            cdp.close()
            process.terminate()
            process.wait(timeout=10)
            shutil.rmtree(profile, ignore_errors=True)

    def test_frontend_in_real_browser(self) -> None:
        process, cdp, profile = self.launch_browser()
        try:
            cdp.command("Runtime.enable")
            cdp.command("Page.enable")
            cdp.command(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": """
window.__copilotAdminE2eErrors = [];
window.addEventListener("error", (event) => window.__copilotAdminE2eErrors.push(event.message));
window.addEventListener("unhandledrejection", (event) => window.__copilotAdminE2eErrors.push(String(event.reason && (event.reason.stack || event.reason.message || event.reason))));
""",
                },
            )
            cdp.command("Page.navigate", {"url": f"http://127.0.0.1:{self.port}/"})
            for _ in range(50):
                ready = cdp.command(
                    "Runtime.evaluate",
                    {"expression": "document.readyState", "returnByValue": True},
                ).get("result", {}).get("value")
                if ready == "complete":
                    break
                time.sleep(0.1)
            script = r"""
(async () => {
  const failures = [];
  const assert = (condition, message) => { if (!condition) failures.push(message); };
  const q = (id) => document.querySelector(`[data-testid="${id}"]`);
  const e = (id) => q(id) || document.getElementById(id);
  const waitFor = async (predicate, message, timeout = 7000) => {
    const started = Date.now();
    while (Date.now() - started < timeout) {
      if (await predicate()) return;
      await new Promise((resolve) => setTimeout(resolve, 100));
    }
    failures.push(message);
  };
  await waitFor(() => q("regression-item") && e("card-copilot").textContent.includes("running"), "Dashboard, status and regression catalog did not render.");
  if (window.__copilotAdminE2eErrors?.length) failures.push(`Browser errors: ${window.__copilotAdminE2eErrors.join(" | ")}`);
  assert(q("view-dashboard").classList.contains("active"), "Dashboard view should be active on load.");
  assert(q("status-diode").className.includes("status-red"), "Initial status diode should be red.");
  assert(e("card-browser").textContent.includes("running"), "Dashboard should show browser status.");
  assert(q("copilot-window-visible-toggle").checked, "Copilot engine window should be visible by default.");
  q("copilot-window-visible-toggle").click();
  q("copilot-window-visible-toggle").dispatchEvent(new Event("change", { bubbles: true }));
  assert(!q("copilot-window-visible-toggle").checked, "Copilot window visibility toggle should switch to hidden mode.");
  q("start-session-button").click();
  await waitFor(async () => {
    const jobs = (await fetch("/api/jobs").then((r) => r.json())).jobs;
    return jobs.some((job) => job.type === "session_start" && job.payload && job.payload.hidden_window === true);
  }, "Session start should send hidden_window=true when the UI toggle is off.");
  q("copilot-window-visible-toggle").click();
  q("copilot-window-visible-toggle").dispatchEvent(new Event("change", { bubbles: true }));
  assert(q("copilot-window-visible-toggle").checked, "Copilot window visibility toggle should switch back to visible mode.");

  q("nav-ai-console").click();
  await waitFor(() => q("view-ai-console").classList.contains("active"), "AI console view did not open.");
  await waitFor(() => q("ai-console-output").textContent.includes("Browser E2E Copilot session is running."), "AI console should show transcript output.");
  assert(getComputedStyle(q("ai-console-output")).whiteSpace.startsWith("pre"), "AI console should preserve terminal whitespace for screen-snapshot mirroring.");
  assert(q("ai-console-output").querySelector(".copilot-line"), "AI console should render transcript lines as styled blocks.");
  assert(q("ai-console-status").textContent.includes("running"), "AI console should show running status.");
  assert(q("ai-console-status").className.includes("semantic-green"), "Running Copilot status should be a green verified badge.");
  assert(q("copilot-window-mode").className.includes("semantic-green"), "Visible Copilot engine badge should be green only when running state confirms it.");
  assert(q("ai-console-model").textContent.includes("ej verifierad"), "Copilot model badge should not claim the configured startup model until verified.");
  assert(!q("ai-console-model").className.includes("semantic-green"), "Unverified Copilot model badge must not be green.");
  assert(q("ai-console-permissions").textContent.includes("ej verifierad"), "Copilot permissions badge should be explicit when not verified.");
  assert(!q("ai-console-permissions").className.includes("semantic-green"), "Unverified permissions badge must not be green.");
  assert(q("ai-console-input").placeholder === "Skriv din prompt här", "AI input placeholder should be user-facing.");
  assert(!document.body.textContent.includes("Ingen fokuskonflikt"), "AI console should not show developer-only focus comments.");
  await fetch("/api/test/inject-host-state", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ copilot_state: { status: "not_running", running: false, user_input_required: false, last_output_tail: "" } })
  });
  await waitFor(() => q("ai-console-output").textContent.includes("Disconnected - please wait until Copilot is online"), "Disconnected AI console should show explicit empty state.");
  assert(q("ai-console-output").querySelector(".disconnected"), "Disconnected empty state should have dedicated styling.");
  await fetch("/api/test/inject-host-state", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      copilot_state: {
        status: "running",
        session_id: "browser-e2e-copilot",
        input_queue_dir: "C:\\\\Copilot_projects\\\\SPS\\\\tmp\\\\copilot_admin_control_plane\\\\browser-e2e-input-queue",
        input_queue: { pending: 0 },
        user_input_required: false,
        visible_window_expected: true,
        last_output_tail: "Browser E2E Copilot session is running."
      }
    })
  });
  await waitFor(() => q("ai-console-output").textContent.includes("Browser E2E Copilot session is running."), "AI console should reconnect to transcript output.");
  q("ai-console-input").value = "browser e2e console input";
  q("ai-console-input").dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
  await waitFor(() => q("ai-console-input").value === "", "AI console input should clear after queued send.");
  await waitFor(async () => {
    const consoleState = await fetch("/api/ai-console").then((r) => r.json());
    return consoleState.input_queue && consoleState.input_queue.pending >= 1;
  }, "AI console input was not queued through backend.");
  q("ai-console-send-esc").click();
  q("ai-console-send-tab").click();
  await waitFor(async () => {
    const consoleState = await fetch("/api/ai-console").then((r) => r.json());
    return consoleState.input_queue && consoleState.input_queue.pending >= 3;
  }, "AI console special keys should be queued through backend.");
  await fetch("/api/test/inject-host-state", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      copilot_state: {
        status: "user_input_required",
        session_id: "browser-e2e-copilot",
        input_queue_dir: "C:\\\\Copilot_projects\\\\SPS\\\\tmp\\\\copilot_admin_control_plane\\\\browser-e2e-input-queue",
        input_queue: { pending: 0 },
        user_input_required: true,
        user_input_reason: "confirmation_prompt",
        last_output_tail: "Browser E2E transcript updated after AI console input.\n$ErrorActionPreference='Stop'; $targets = Invoke-WebRequest -UseBasicParsing '' -Ti…\n╭────╮\n│ Run safe host-runner smoke tests │\n│ Do you want to run this command? │\n│ ❯ 1. Yes │\n│ 2. No │\n│ 3. Other (type your answer) │\n│ ↑/↓ to navigate · enter to select · tab next · ctrl+d decline · esc to cancel │\n╰────╯\nv1.0.82 downloaded · run /restart to apply · ← open sidebar · / commands · ? help · tab next tab                                          Auto → GPT-5.6 Terra\n5s6\b7\b8\b910\b1\b2\b3\b4\b5\b6\b7\b8\b9 2m 0\b1\b2  Current Pull requests"
      }
    })
  });
  await waitFor(() => q("ai-console-output").textContent.includes("transcript updated"), "AI console should refresh transcript output.");
  assert(q("ai-console-output").textContent.includes("Current Pull requests"), "AI console should preserve real content after timer redraw artifacts.");
  assert(!q("ai-console-output").textContent.includes("192939") && !q("ai-console-output").textContent.includes("5s6"), "AI console should suppress timer redraw artifact lines.");
  assert(!q("ai-console-output").textContent.includes("\b"), "AI console should not show raw terminal backspace characters.");
  assert(q("ai-console-output").querySelector(".copilot-prompt-box"), "AI console should render the mirrored prompt area as a prompt box.");
  assert(q("ai-console-output").querySelector(".copilot-prompt-cursor"), "AI console should render a visible prompt cursor.");
  assert(q("ai-console-output").textContent.includes("v1.0.82 downloaded"), "AI console should keep the prompt footer/help text.");
  await waitFor(() => !q("ai-console-interaction").hidden, "Interactive choice panel should be shown when Copilot waits for a selection.");
  assert(q("ai-console-ready").textContent.includes("Svar"), "AI console readiness badge should switch to response mode.");
  assert(q("ai-console-send").textContent.includes("svar"), "AI console primary send action should reflect response mode.");
  assert(q("ai-console-input").placeholder.includes("väntar på ett svar"), "AI console placeholder should explain interactive response mode.");
  assert(q("ai-console-hint").textContent.includes("väntar på ett val"), "AI console hint should explain the selection state.");
  const quickOptions = Array.from(document.querySelectorAll("[data-interactive-option-index]"));
  assert(quickOptions.length >= 2, "Interactive choice prompt should render quick option buttons.");
  assert(quickOptions.some((button) => button.textContent.includes("Yes")), "Interactive choice panel should expose Yes.");
  const noButton = quickOptions.find((button) => button.textContent.includes("No"));
  assert(noButton, "Interactive choice panel should expose No.");
  noButton.click();
  await waitFor(async () => {
    const consoleState = await fetch("/api/ai-console").then((r) => r.json());
    return consoleState.input_queue && consoleState.input_queue.pending >= 4;
  }, "Interactive quick-select should queue a raw choice response.");

  q("nav-dashboard").click();
  q("testing-mode-button").click();
  await waitFor(() => e("mode-label").textContent.includes("testing"), "Mode controls did not update mode label.");
  assert(q("status-diode").className.includes("status-yellow"), "Running mode job should turn status diode yellow.");

  q("nav-manualer").click();
  await waitFor(() => q("view-manualer").classList.contains("active"), "Manuals view did not open.");
  await waitFor(() => document.querySelector("[data-manual-id]"), "Manual list did not render.");
  assert(q("manuals-count-pill").textContent.includes("manualer"), "Manual hero should summarize available manuals.");
  const openManualButton = document.querySelector("[data-manual-id]");
  assert(openManualButton, `Open-manual button missing; manual HTML: ${document.getElementById("manual-list").innerHTML}`);
  if (openManualButton) openManualButton.click();
  await waitFor(() => q("manual-reader").innerHTML.includes("<h1>"), "Manual reader did not render Markdown.");
  assert(q("manual-reader").textContent.includes("Kundtjänst") || q("manual-reader").textContent.includes("CSC"), "Manual reader should show CSC manual content from repository.");

  q("nav-regressioner").click();
  await waitFor(() => q("view-regressioner").classList.contains("active"), "Regression view did not open.");
  assert(document.querySelectorAll("[data-testid='regression-item']").length >= 1, "Regression catalog did not render.");
  const runItemButton = document.querySelector("[data-run-test-id]");
  assert(runItemButton, `Regression item button missing; list HTML: ${document.getElementById("regression-list").innerHTML}`);
  assert(runItemButton && runItemButton.dataset.runTestId.includes("regression-"), "Regression item button should carry backend test_id.");
  q("run-selected-regression-button").click();
  await waitFor(async () => (await fetch("/api/jobs").then((r) => r.json())).jobs.length >= 2, "Regression job was not created.");
  const jobs = (await fetch("/api/jobs").then((r) => r.json())).jobs;
  await fetch("/api/test/inject-host-state", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      job_updates: jobs.map((job) => ({
        job_id: job.job_id,
        status: job.type === "run_regression" ? "completed_unopened" : "completed_opened",
        output_tail: "Browser E2E updated this job."
      }))
    })
  });
  q("nav-jobb").click();
  await waitFor(() => document.querySelector("[data-job-id]"), "Job list did not render.");
  const openJobButton = document.querySelector("[data-job-id]");
  assert(openJobButton, `Open-job button missing; job HTML: ${document.getElementById("job-list").innerHTML}`);
  if (openJobButton) openJobButton.click();

  q("nav-rapporter").click();
  await waitFor(() => document.querySelector("[data-report-id]"), "Report list did not render.");
  const openReportButton = document.querySelector("[data-report-id]");
  assert(openReportButton, `Open-report button missing; report HTML: ${document.getElementById("report-list").innerHTML}`);
  if (openReportButton) openReportButton.click();
  await waitFor(() => q("report-reader").innerHTML.includes("<h1>"), "Report reader did not render Markdown.");
  await waitFor(() => q("report-reader").querySelector("table"), "Report reader did not render Markdown table.");
  assert(q("report-reader").textContent.includes("RegressionError01"), "Report reader should render Markdown link text.");

  q("nav-mermaid").click();
  await waitFor(() => q("mermaid-canvas").querySelector("svg"), "Mermaid SVG harness graph did not render.");
  assert(q("mermaid-canvas").textContent.includes("A: End on logged-in service portal page"), "Mermaid graph should render node descriptions, not only node ids.");
  assert(q("mermaid-canvas").textContent.includes("F: Validate regression dependency sync"), "Mermaid graph should render standalone described nodes.");
  const canvas = q("mermaid-canvas");
  const viewport = q("mermaid-viewport");
  const initialTransform = canvas.style.transform;
  q("mermaid-zoom-in").click();
  assert(canvas.style.transform !== initialTransform && canvas.style.transform.includes("scale("), "Mermaid zoom should update transform.");
  viewport.dispatchEvent(new PointerEvent("pointerdown", { clientX: 10, clientY: 20, pointerId: 1, bubbles: true }));
  viewport.dispatchEvent(new PointerEvent("pointermove", { clientX: 80, clientY: 65, pointerId: 1, bubbles: true }));
  viewport.dispatchEvent(new PointerEvent("pointerup", { pointerId: 1, bubbles: true }));
  assert(canvas.style.transform.includes("translate(70px, 45px)"), "Mermaid pointer drag should pan canvas.");
  viewport.scrollLeft = 120;
  viewport.scrollTop = 240;
  viewport.dispatchEvent(new Event("scroll"));
  q("mermaid-fit").click();
  assert(canvas.style.transform.includes("scale(0."), "Mermaid fit should reduce scale for a large graph.");
  q("mermaid-reset").click();
  assert(canvas.style.transform.includes("translate(0px, 0px) scale(1)"), "Mermaid reset should restore default transform.");
  q("mermaid-search").value = "B";
  q("mermaid-search").dispatchEvent(new Event("input"));
  assert(document.querySelectorAll(".graph-node.dimmed").length > 0, "Mermaid search should dim non-matching nodes.");

  q("nav-loggar").click();
  const frontendLog = q("frontend-log").textContent;
  for (const event of ["page_view", "button_clicked", "ai_console_refreshed", "job_created", "job_opened", "report_opened", "mermaid_zoom_changed", "mermaid_pan_changed", "mermaid_scroll_changed", "mermaid_search_changed"]) {
    assert(frontendLog.includes(`"event":"${event}"`), `Frontend log should contain ${event}.`);
  }
  return { failures, logLines: frontendLog.split("\n").filter(Boolean).length };
})()
"""
            result = cdp.command("Runtime.evaluate", {"expression": script, "awaitPromise": True, "returnByValue": True})
            if "exceptionDetails" in result:
                self.fail(json.dumps(result["exceptionDetails"], ensure_ascii=False))
            value = result.get("result", {}).get("value", {})
            self.assertIsInstance(value, dict, json.dumps(result, ensure_ascii=False))
            self.assertEqual([], value.get("failures"), "\n".join(value.get("failures", [])))
            self.assertGreaterEqual(value.get("logLines", 0), 10)
        finally:
            cdp.close()
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            shutil.rmtree(profile, ignore_errors=True)

    def test_ai_console_falls_back_to_polling_when_sse_stalls(self) -> None:
        process, cdp, profile = self.launch_browser()
        try:
            cdp.command("Runtime.enable")
            cdp.command("Page.enable")
            cdp.command(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": """
window.__copilotAdminE2eErrors = [];
window.addEventListener("error", (event) => window.__copilotAdminE2eErrors.push(event.message));
window.addEventListener("unhandledrejection", (event) => window.__copilotAdminE2eErrors.push(String(event.reason && (event.reason.stack || event.reason.message || event.reason))));
class FakeOpenOnlyEventSource {
  constructor(url) {
    this.url = url;
    this.listeners = new Map();
    setTimeout(() => this.#emit("open", { type: "open" }), 0);
  }
  addEventListener(type, handler) {
    if (!this.listeners.has(type)) this.listeners.set(type, []);
    this.listeners.get(type).push(handler);
  }
  removeEventListener(type, handler) {
    const handlers = this.listeners.get(type) || [];
    this.listeners.set(type, handlers.filter((item) => item !== handler));
  }
  close() {}
  #emit(type, event) {
    for (const handler of this.listeners.get(type) || []) handler(event);
  }
}
window.EventSource = FakeOpenOnlyEventSource;
""",
                },
            )
            cdp.command("Page.navigate", {"url": f"http://127.0.0.1:{self.port}/"})
            for _ in range(50):
                ready = cdp.command(
                    "Runtime.evaluate",
                    {"expression": "document.readyState", "returnByValue": True},
                ).get("result", {}).get("value")
                if ready == "complete":
                    break
                time.sleep(0.1)

            initial = cdp.command(
                "Runtime.evaluate",
                {
                    "expression": r"""
(async () => {
  const failures = [];
  const q = (id) => document.querySelector(`[data-testid="${id}"]`);
  const waitFor = async (predicate, message, timeout = 7000) => {
    const started = Date.now();
    while (Date.now() - started < timeout) {
      if (await predicate()) return;
      await new Promise((resolve) => setTimeout(resolve, 100));
    }
    failures.push(message);
  };
  q("nav-ai-console").click();
  await waitFor(() => q("view-ai-console").classList.contains("active"), "AI console view did not open.");
  await waitFor(() => q("ai-console-output").textContent.includes("Browser E2E Copilot session is running."), "Initial transcript did not render.");
  return { failures };
})()
""",
                    "awaitPromise": True,
                    "returnByValue": True,
                },
            )
            if "exceptionDetails" in initial:
                self.fail(json.dumps(initial["exceptionDetails"], ensure_ascii=False))
            initial_value = initial.get("result", {}).get("value", {})
            self.assertEqual([], initial_value.get("failures"), "\n".join(initial_value.get("failures", [])))

            self.request(
                "POST",
                "/api/test/inject-host-state",
                {
                    "copilot_state": {
                        "status": "running",
                        "session_id": "browser-e2e-copilot",
                        "input_queue_dir": str(REPO_ROOT / "tmp" / "copilot_admin_control_plane" / "browser-e2e-input-queue"),
                        "input_queue": {"pending": 0},
                        "user_input_required": False,
                        "visible_window_expected": True,
                        "last_output_tail": "Polling fallback transcript updated.",
                    }
                },
            )

            verification = cdp.command(
                "Runtime.evaluate",
                {
                    "expression": r"""
(async () => {
  const output = document.querySelector('[data-testid="ai-console-output"]');
  const started = Date.now();
  while (Date.now() - started < 7000) {
    if ((output?.textContent || "").includes("Polling fallback transcript updated.")) {
      return { updated: true, errors: window.__copilotAdminE2eErrors || [] };
    }
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  return {
    updated: false,
    text: output?.textContent || "",
    errors: window.__copilotAdminE2eErrors || [],
  };
})()
""",
                    "awaitPromise": True,
                    "returnByValue": True,
                },
            )
            if "exceptionDetails" in verification:
                self.fail(json.dumps(verification["exceptionDetails"], ensure_ascii=False))
            value = verification.get("result", {}).get("value", {})
            self.assertTrue(
                value.get("updated"),
                f"AI console did not fall back to polling when SSE stalled. Output: {value.get('text', '')}",
            )
            self.assertEqual([], value.get("errors", []), f"Browser errors: {' | '.join(value.get('errors', []))}")
        finally:
            cdp.close()
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
