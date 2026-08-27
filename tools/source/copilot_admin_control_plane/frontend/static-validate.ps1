$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Html = Get-Content -Raw -Encoding UTF8 -Path (Join-Path $Root "index.html")
$Js = Get-Content -Raw -Encoding UTF8 -Path (Join-Path $Root "app.js")
$Css = Get-Content -Raw -Encoding UTF8 -Path (Join-Path $Root "styles.css")

$RequiredTestIds = @(
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
    "frontend-log"
)

$RequiredEvents = @(
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
    "status_diode_changed"
)

$RequiredEndpoints = @(
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
    "/api/frontend/events"
)

$Failures = New-Object System.Collections.Generic.List[string]
foreach ($TestId in $RequiredTestIds) {
    if (-not $Html.Contains("data-testid=`"$TestId`"") -and -not $Js.Contains("data-testid=`"$TestId`"")) {
        $Failures.Add("Missing data-testid: $TestId")
    }
}
foreach ($Event in $RequiredEvents) {
    if (-not $Js.Contains("`"$Event`"")) {
        $Failures.Add("Missing frontend event: $Event")
    }
}
foreach ($Endpoint in $RequiredEndpoints) {
    if (-not $Js.Contains($Endpoint)) {
        $Failures.Add("Missing API endpoint integration: $Endpoint")
    }
}
if (-not $Js.Contains("hidden_window")) {
    $Failures.Add("Missing Copilot window visibility payload.")
}
if (-not $Js.Contains("clear_line")) {
    $Failures.Add("Missing Copilot console clear-line payload.")
}
foreach ($Phrase in @("status-red", "status-yellow", "status-green", "mermaid-viewport", "markdown-reader", "copilot-console-output", "copilot-console-form", "copilot-console-special-actions")) {
    if (-not $Css.Contains($Phrase)) {
        $Failures.Add("Missing CSS affordance: $Phrase")
    }
}
if (-not $Js.Contains("setInterval(refreshStatusAndJobs, POLL_MS)")) {
    $Failures.Add("Missing periodic status polling.")
}
if (-not $Js.Contains("POST") -or -not $Js.Contains("fetch")) {
    $Failures.Add("Missing async API fetch implementation.")
}

if ($Failures.Count -gt 0) {
    $Failures | ForEach-Object { Write-Error $_ }
    exit 1
}

Write-Host "Frontend static validation passed."
