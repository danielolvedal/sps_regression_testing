import { readFileSync } from "node:fs";

const html = readFileSync(new URL("./index.html", import.meta.url), "utf8");
const js = readFileSync(new URL("./app.js", import.meta.url), "utf8");
const css = readFileSync(new URL("./styles.css", import.meta.url), "utf8");

const requiredTestIds = [
  "topbar",
  "left-nav",
  "status-diode",
  "view-dashboard",
  "dashboard-cards",
  "copilot-window-visible-toggle",
  "nav-copilot",
  "view-copilot",
  "copilot-console",
  "copilot-console-output",
  "copilot-console-input",
  "copilot-console-send",
  "copilot-console-send-esc",
  "copilot-console-send-tab",
  "copilot-console-status",
  "copilot-window-mode",
  "learning-mode-button",
  "testing-mode-button",
  "view-regressioner",
  "run-all-regressions-button",
  "run-selected-regression-button",
  "regression-select",
  "regression-list",
  "view-mermaid",
  "mermaid-zoom-in",
  "mermaid-zoom-out",
  "mermaid-fit",
  "mermaid-reset",
  "mermaid-search",
  "mermaid-viewport",
  "mermaid-canvas",
  "view-rapporter",
  "report-list",
  "report-reader",
  "view-jobb",
  "job-list",
  "view-loggar",
  "frontend-log",
];

const requiredEvents = [
  "page_view",
  "api_request_started",
  "api_request_completed",
  "api_request_failed",
  "button_clicked",
  "mode_changed",
  "copilot_console_refreshed",
  "copilot_console_input_sent",
  "job_created",
  "job_opened",
  "report_opened",
  "mermaid_zoom_changed",
  "mermaid_pan_changed",
  "mermaid_scroll_changed",
  "mermaid_search_changed",
  "status_diode_changed",
];

const requiredEndpoints = [
  "/api/status",
  "/api/session/start",
  "/api/session/copilot",
  "/api/session/browser",
  "/api/copilot/console",
  "/api/copilot/input",
  "/api/regression/tests",
  "/api/regression/mermaid",
  "/api/copilot/mode",
  "/api/regression/run",
  "/api/jobs",
  "/api/reports",
  "/api/frontend/events",
];

const failures = [];
for (const testId of requiredTestIds) {
  if (!html.includes(`data-testid="${testId}"`) && !js.includes(`data-testid="${testId}"`)) {
    failures.push(`Missing data-testid: ${testId}`);
  }
}
for (const event of requiredEvents) {
  if (!js.includes(`"${event}"`)) failures.push(`Missing frontend event: ${event}`);
}
for (const endpoint of requiredEndpoints) {
  if (!js.includes(endpoint)) failures.push(`Missing API endpoint integration: ${endpoint}`);
}
if (!js.includes("hidden_window")) failures.push("Missing Copilot window visibility payload.");
if (!js.includes("clear_line")) failures.push("Missing Copilot console clear-line payload.");
for (const phrase of ["status-red", "status-yellow", "status-green", "mermaid-viewport", "markdown-reader", "copilot-console-output", "copilot-console-form", "copilot-console-special-actions"]) {
  if (!css.includes(phrase)) failures.push(`Missing CSS affordance: ${phrase}`);
}
if (!js.includes("setInterval(refreshStatusAndJobs, POLL_MS)")) {
  failures.push("Missing periodic status polling.");
}
if (!js.includes("POST") || !js.includes("fetch")) {
  failures.push("Missing async API fetch implementation.");
}

if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}
console.log("Frontend static validation passed.");
