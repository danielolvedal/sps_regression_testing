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
    "nav-manualer",
    "view-manualer",
    "manuals-hero",
    "manuals-sections",
    "manuals-section-csc",
    "manuals-section-serviceportal",
    "manuals-section-clients",
    "copilot-window-visible-toggle",
    "nav-ai-console",
    "view-ai-console",
    "ai-console",
    "ai-console-output",
    "ai-console-input",
    "ai-console-send",
    "ai-console-send-esc",
    "ai-console-send-tab",
    "copilot-start-session-button",
    "ai-console-status",
    "copilot-window-mode",
    "ai-console-model",
    "ai-console-permissions",
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
    "ai_console_refreshed",
    "ai_console_input_sent",
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
    "/api/ai-console",
    "/api/ai-console/events",
    "/api/ai-console/input",
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
    $Failures.Add("Missing AI console clear-line payload.")
}
if (-not $Js.Contains("Disconnected - please wait until Copilot is online")) {
    $Failures.Add("Missing disconnected AI console empty state.")
}
if (-not $Js.Contains("setSemanticBadge")) {
    $Failures.Add("Missing semantic AI console badge renderer.")
}
if (-not $Js.Contains("new EventSource") -or -not $Js.Contains("connectAiConsoleEvents")) {
    $Failures.Add("Missing Server-Sent Events integration for low-latency AI console output.")
}
if (-not $Js.Contains("client_sent_at")) {
    $Failures.Add("Missing client-side input latency timestamp.")
}

foreach ($Phrase in @("status-red", "status-yellow", "status-green", "semantic-green", "semantic-yellow", "semantic-red", "semantic-gray", "mermaid-viewport", "markdown-reader", "ai-console-output", "ai-console-form", "ai-console-special-actions")) {
    if (-not $Css.Contains($Phrase)) {
        $Failures.Add("Missing CSS affordance: $Phrase")
    }
}
foreach ($Phrase in @("manuals-grid", "manuals-card", "manuals-hero")) {
    if (-not $Css.Contains($Phrase)) {
        $Failures.Add("Missing Manualer CSS affordance: $Phrase")
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
