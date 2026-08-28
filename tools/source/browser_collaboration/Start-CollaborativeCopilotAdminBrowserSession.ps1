param(
    [string]$HostName = '127.0.0.1',
    [int]$BackendPort = 8765,
    [ValidateSet('auto', 'edge', 'chrome')]
    [string]$Browser = 'auto',
    [int]$BrowserPort = 9223,
    [string]$ProfileDir,
    [switch]$ReuseExisting = $true,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
$uiUrl = "http://$HostName`:$BackendPort/"
$healthUrl = "http://$HostName`:$BackendPort/api/health"
$stageDebugPort = 9222
$automationDebugPort = 9322
$scriptPath = Join-Path $PSScriptRoot 'Start-CollaborativeBrowserSession.ps1'

function Test-Endpoint([string]$Url) {
    try {
        Invoke-RestMethod -Method GET -Uri $Url -TimeoutSec 2 | Out-Null
        return $true
    } catch {
        return $false
    }
}

$backendReachable = Test-Endpoint -Url $healthUrl

if ($BrowserPort -eq $BackendPort) {
    throw "Browser debug port $BrowserPort collides with the Copilot-admin backend port $BackendPort. Use a separate debug port such as 9223."
}

if ($BrowserPort -eq $stageDebugPort) {
    Write-Warning "Browser debug port $BrowserPort is the normal shared stage-browser port. For the Copilot-admin localhost UI, port 9223 is recommended to keep the browser roles separate."
}

if ($BrowserPort -eq $automationDebugPort) {
    Write-Warning "Browser debug port $BrowserPort is reserved for automated real-E2E. For visible user collaboration on the Copilot-admin localhost UI, port 9223 is recommended."
}

if ($DryRun) {
    [ordered]@{
        status = 'dry_run'
        mode = 'visible_user_browser'
        ui_url = $uiUrl
        health_url = $healthUrl
        backend_reachable = $backendReachable
        browser = $Browser
        browser_debug_port = $BrowserPort
        profile_dir = if ($ProfileDir) { $ProfileDir } else { Join-Path $repoRoot "tmp\browser-profile-$BrowserPort" }
        distinction = [ordered]@{
            manual_frontend_work = 'Use this script for visible user/agent work against the localhost Copilot-admin UI.'
            shared_stage_browser = 'Use runtime\start-collaborative-stage-browser.ps1 for stage/system UI work, normally on debug port 9222.'
            automation_real_e2e = 'Use runtime\docker\copilot-admin\test-real-visible-e2e.ps1 for automated testing, which keeps a hidden Copilot helper and its own browser isolation.'
        }
    } | ConvertTo-Json -Depth 10
    return
}

if (-not $backendReachable) {
    Write-Warning "Copilot-admin backend did not answer on $healthUrl. The browser will still open $uiUrl, but the page may remain unavailable until the backend is started."
}

$result = & $scriptPath -Url $uiUrl -Browser $Browser -Port $BrowserPort -ProfileDir $ProfileDir -ReuseExisting:$ReuseExisting
$parsed = $result | ConvertFrom-Json

[ordered]@{
    mode = 'visible_user_browser'
    ui_url = $uiUrl
    health_url = $healthUrl
    backend_reachable = $backendReachable
    browser_debug_port = $BrowserPort
    intended_use = 'Visible user/agent browser for manual Copilot-admin frontend work on localhost.'
    not_for = 'Automated real-E2E runs should use their own isolated browser flow instead of this browser.'
    browser = $parsed.browser
    browserPath = $parsed.browserPath
    port = $parsed.port
    processId = $parsed.processId
    profileDir = $parsed.profileDir
    startUrl = $parsed.startUrl
    debugVersionEndpoint = $parsed.debugVersionEndpoint
    debugTargetsEndpoint = $parsed.debugTargetsEndpoint
    webSocketDebuggerUrl = $parsed.webSocketDebuggerUrl
    launched = $parsed.launched
} | ConvertTo-Json -Depth 10
