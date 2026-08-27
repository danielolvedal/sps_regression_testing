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
        cls.server = app.make_server("127.0.0.1", 0, app.ControlPlaneBackend(REPO_ROOT))
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()

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
        profile = REPO_ROOT / "tmp" / "copilot_admin_control_plane" / "browser-e2e-profile"
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

  q("nav-copilot").click();
  await waitFor(() => q("view-copilot").classList.contains("active"), "Copilot console view did not open.");
  assert(q("copilot-console-output").textContent.includes("Browser E2E Copilot session is running."), "Copilot console should show transcript output.");
  assert(getComputedStyle(q("copilot-console-output")).whiteSpace === "normal", "Copilot console should render semantic Copilot blocks rather than a raw terminal dump.");
  assert(q("copilot-console-output").querySelector(".copilot-line"), "Copilot console should render transcript lines as styled blocks.");
  assert(q("copilot-console-status").textContent.includes("running"), "Copilot console should show running status.");
  assert(q("copilot-console-model").textContent.includes("gpt-5-mini"), "Copilot console should show startup model.");
  assert(q("copilot-console-permissions").textContent.includes("allow-all"), "Copilot console should show permission policy.");
  assert(q("copilot-console-input").placeholder === "Skriv din prompt här", "Copilot input placeholder should be user-facing.");
  assert(!document.body.textContent.includes("Ingen fokuskonflikt"), "Copilot console should not show developer-only focus comments.");
  q("copilot-console-input").value = "browser e2e console input";
  q("copilot-console-input").dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
  await waitFor(() => q("copilot-console-input").value === "", "Copilot console input should clear after queued send.");
  await waitFor(async () => {
    const consoleState = await fetch("/api/copilot/console").then((r) => r.json());
    return consoleState.input_queue && consoleState.input_queue.pending >= 1;
  }, "Copilot console input was not queued through backend.");
  q("copilot-console-send-esc").click();
  q("copilot-console-send-tab").click();
  await waitFor(async () => {
    const consoleState = await fetch("/api/copilot/console").then((r) => r.json());
    return consoleState.input_queue && consoleState.input_queue.pending >= 3;
  }, "Copilot console special keys should be queued through backend.");
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
        last_output_tail: "Browser E2E transcript updated after frontend console input.\n$ErrorActionPreference='Stop'; $targets = Invoke-WebRequest -UseBasicParsing '' -Ti…\n╭────╮\n│ Run safe host-runner smoke tests │\n│ Do you want to run this command? │\n│ ❯ 1. Yes │\n│ ↑/↓ to navigate · enter to select · esc to cancel │\n╰────╯5s6\b7\b8\b910\b1\b2\b3\b4\b5\b6\b7\b8\b9 2m 0\b1\b2  Current Pull requests"
      }
    })
  });
  await waitFor(() => q("copilot-console-output").textContent.includes("transcript updated"), "Copilot console should refresh transcript output.");
  assert(q("copilot-console-output").textContent.includes("Current Pull requests"), "Copilot console should preserve real content after timer redraw artifacts.");
  assert(!q("copilot-console-output").textContent.includes("192939") && !q("copilot-console-output").textContent.includes("5s6"), "Copilot console should suppress timer redraw artifact lines.");
  assert(!q("copilot-console-output").textContent.includes("\b"), "Copilot console should not show raw terminal backspace characters.");
  assert(!q("copilot-console-output").textContent.includes("╭") && !q("copilot-console-output").textContent.includes("│"), "Copilot console should not show raw TUI box drawing characters.");
  assert(q("copilot-console-output").querySelector(".command-truncated-label"), "Copilot console should label PTY-truncated command summaries.");
  assert(q("copilot-console-output").querySelector(".command-title"), "Copilot command prompt should render as a command card title.");
  assert(q("copilot-console-output").querySelector(".selected-option"), "Copilot selected option should render with highlight styling.");
  assert(q("copilot-console-hint").textContent === "Copilot väntar på input.", "Copilot console hint should be concise and user-facing.");

  q("nav-dashboard").click();
  q("testing-mode-button").click();
  await waitFor(() => e("mode-label").textContent.includes("testing"), "Mode controls did not update mode label.");
  assert(q("status-diode").className.includes("status-yellow"), "Running mode job should turn status diode yellow.");

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
  await waitFor(() => q("status-diode").className.includes("status-green"), "Completed unopened regression job should turn status diode green.", 7000);
  q("nav-jobb").click();
  await waitFor(() => document.querySelector("[data-job-id]"), "Job list did not render.");
  const openJobButton = document.querySelector("[data-job-id]");
  assert(openJobButton, `Open-job button missing; job HTML: ${document.getElementById("job-list").innerHTML}`);
  if (openJobButton) openJobButton.click();
  await waitFor(() => q("status-diode").className.includes("status-red"), "Opening the result should return status diode to red.");

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
  for (const event of ["page_view", "button_clicked", "mode_changed", "copilot_console_refreshed", "copilot_console_input_sent", "job_created", "job_opened", "report_opened", "mermaid_zoom_changed", "mermaid_pan_changed", "mermaid_scroll_changed", "mermaid_search_changed"]) {
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


if __name__ == "__main__":
    unittest.main()
