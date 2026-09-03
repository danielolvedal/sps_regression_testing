[CmdletBinding()]
param(
    [string]$HostName = '127.0.0.1',
    [int]$BackendPort = 8765,
    [int]$HostRunnerPort = 8766,
    [int]$BrowserPort = 9222,
    [string]$StartupModel = 'auto',
    [switch]$StartCopilotSession,
    [switch]$RestartExisting,
    [switch]$HideCopilotWindow,
    [switch]$OpenUiInSharedBrowser,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = $PSScriptRoot
$hostRunnerUrl = "http://$HostName`:$HostRunnerPort"
$backendUrl = "http://$HostName`:$BackendPort"
$uiUrl = "$backendUrl/"
$runId = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$stateDir = Join-Path $repoRoot 'tmp\copilot_admin_control_plane\start_tool'
$null = New-Item -ItemType Directory -Path $stateDir -Force
$statePath = Join-Path $stateDir 'latest.json'

# Tool infrastructure logs (stdout/stderr from detached processes) go to tool_error_logs
$logsDir = if ($env:TOOL_ERROR_LOG_DIR) { $env:TOOL_ERROR_LOG_DIR } else { Join-Path $repoRoot 'tool_error_logs' }
if (-not (Test-Path $logsDir)) { New-Item -Path $logsDir -ItemType Directory -Force | Out-Null }
$hostRunnerOut = Join-Path $logsDir "host-runner-$runId.out.log"
$hostRunnerErr = Join-Path $logsDir "host-runner-$runId.err.log"
$backendOut = Join-Path $logsDir "backend-$runId.out.log"
$backendErr = Join-Path $logsDir "backend-$runId.err.log"

function Test-JsonEndpoint {
    param([Parameter(Mandatory = $true)][string]$Uri)
    try {
        Invoke-RestMethod -Uri $Uri -Method GET -TimeoutSec 2 | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Stop-RecordedProcess {
    param(
        [Parameter(Mandatory = $true)][string]$ProcessName,
        [int]$ProcessId
    )
    if (-not $ProcessId) {
        return $false
    }
    $process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if (-not $process) {
        return $false
    }
    Stop-Process -Id $ProcessId -Force
    $deadline = (Get-Date).AddSeconds(10)
    while ((Get-Date) -lt $deadline -and (Get-Process -Id $ProcessId -ErrorAction SilentlyContinue)) {
        Start-Sleep -Milliseconds 250
    }
    if (Get-Process -Id $ProcessId -ErrorAction SilentlyContinue) {
        throw "Could not stop stale $ProcessName process PID $ProcessId."
    }
    return $true
}

function Stop-BackendPortOwnerIfCompatible {
    $listener = Get-NetTCPConnection -LocalAddress $HostName -LocalPort $BackendPort -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $listener -or -not $listener.OwningProcess) {
        return $false
    }
    $ownerPid = [int]$listener.OwningProcess
    $owner = Get-CimInstance Win32_Process -Filter "ProcessId=$ownerPid" -ErrorAction SilentlyContinue
    if (-not $owner -or -not ([string]$owner.CommandLine).Contains('tools\source\copilot_admin_control_plane\backend\app.py')) {
        throw "A process is listening on $backendUrl but it is not the recorded Copilot-admin backend. PID: $ownerPid. CommandLine: $($owner.CommandLine)"
    }
    return Stop-RecordedProcess -ProcessName 'Copilot-admin backend' -ProcessId $ownerPid
}

function Wait-JsonEndpoint {
    param(
        [Parameter(Mandatory = $true)][string]$Uri,
        [int]$TimeoutSeconds = 45
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $lastError = $null
    while ((Get-Date) -lt $deadline) {
        try {
            return Invoke-RestMethod -Uri $Uri -Method GET -TimeoutSec 5
        } catch {
            $lastError = $_.Exception.Message
            Start-Sleep -Milliseconds 500
        }
    }
    throw "Timed out waiting for $Uri. Last error: $lastError"
}

function Start-DetachedPowerShell {
    param(
        [Parameter(Mandatory = $true)][string]$Command,
        [Parameter(Mandatory = $true)][string]$StdOut,
        [Parameter(Mandatory = $true)][string]$StdErr
    )
    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($Command))
    Start-Process -FilePath (Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe') `
        -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-EncodedCommand', $encoded) `
        -WorkingDirectory $repoRoot `
        -RedirectStandardOutput $StdOut `
        -RedirectStandardError $StdErr `
        -WindowStyle Hidden `
        -PassThru
}

if ($DryRun) {
    [ordered]@{
        status = 'dry_run'
        ui_url = $uiUrl
        host_runner_url = $hostRunnerUrl
        backend_url = $backendUrl
        browser_port = $BrowserPort
        startup_model = $StartupModel
        allow_all = $true
        session_start_requested = [bool]$StartCopilotSession
        session_start_policy = if ($StartCopilotSession) { 'start-tool-fresh-copilot' } else { 'ai-console-on-demand-fresh-copilot' }
        copilot_window_mode = if ($HideCopilotWindow) { 'hidden' } else { 'visible' }
        singleton_policy = 'Copilot session starts fresh by default; browser session may reuse existing owned admin browser. For visible localhost admin UI work use runtime\start-collaborative-copilot-admin-browser.ps1 instead of the stage browser or automation browser'
        visible_admin_browser_script = '.\runtime\start-collaborative-copilot-admin-browser.ps1'
    } | ConvertTo-Json -Depth 10
    Write-Host "Regression tool suite started - Graphical interface at: $uiUrl"
    exit 0
}

$hostRunnerStarted = $false
$backendStarted = $false
$hostRunnerProcess = $null
$backendProcess = $null
$previousState = $null
if (Test-Path $statePath) {
    try {
        $previousState = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
    } catch {
        $previousState = $null
    }
}

if (-not (Test-JsonEndpoint "$hostRunnerUrl/health")) {
    $hostRunnerCommand = @"
Set-Location -LiteralPath '$repoRoot'
& '.\runtime\start-copilot-admin-host-runner-api.ps1' -HostAddress '$HostName' -Port $HostRunnerPort
"@
    $hostRunnerProcess = Start-DetachedPowerShell -Command $hostRunnerCommand -StdOut $hostRunnerOut -StdErr $hostRunnerErr
    $hostRunnerStarted = $true
}
$null = Wait-JsonEndpoint "$hostRunnerUrl/health" 45

$backendHealthOk = Test-JsonEndpoint "$backendUrl/api/health"
$backendConsoleOk = Test-JsonEndpoint "$backendUrl/api/ai-console?limit=1"
if ($backendHealthOk -and -not $backendConsoleOk) {
    if ($previousState -and $previousState.backend_pid) {
        $null = Stop-RecordedProcess -ProcessName 'Copilot-admin backend' -ProcessId ([int]$previousState.backend_pid)
    }
    if (Test-JsonEndpoint "$backendUrl/api/health") {
        $null = Stop-BackendPortOwnerIfCompatible
    }
    if (Test-JsonEndpoint "$backendUrl/api/health") {
        throw "A stale backend is still listening on $backendUrl and does not expose /api/ai-console."
    }
    $backendHealthOk = $false
}

if (-not $backendHealthOk) {
    $frontendDir = Join-Path $repoRoot 'tools\source\copilot_admin_control_plane\frontend'
    $backendCommand = @"
Set-Location -LiteralPath '$repoRoot'
`$env:SPS_REPO_ROOT = '$repoRoot'
`$env:COPILOT_ADMIN_FRONTEND_DIR = '$frontendDir'
`$env:COPILOT_ADMIN_HOST_RUNNER_URL = '$hostRunnerUrl'
`$env:COPILOT_ADMIN_HOST_RUNNER_TIMEOUT_SECONDS = '90'
& '.\runtime\docker\copilot-admin\start-backend.ps1' -HostName '$HostName' -Port $BackendPort -HostRunnerUrl '$hostRunnerUrl'
"@
    $backendProcess = Start-DetachedPowerShell -Command $backendCommand -StdOut $backendOut -StdErr $backendErr
    $backendStarted = $true
}
$null = Wait-JsonEndpoint "$backendUrl/api/health" 45

$status = Invoke-RestMethod -Method GET -Uri "$backendUrl/api/status" -TimeoutSec 15
if ($OpenUiInSharedBrowser) {
    try {
        & (Join-Path $repoRoot 'runtime\open-shared-browser-tab.ps1') -Url $uiUrl -Port $BrowserPort -SourcePageUrlPrefix ''
    } catch {
        Write-Warning "The tool started, but opening the UI in the shared browser failed: $($_.Exception.Message)"
    }
}

$sessionJob = $null
if ($StartCopilotSession) {
    $sessionBody = @{
        restart_existing = $true
        startup_model = $StartupModel
        hidden_window = [bool]$HideCopilotWindow
    }
    $sessionJob = Invoke-RestMethod -Method POST -Uri "$backendUrl/api/session/start" -ContentType 'application/json' -Body ($sessionBody | ConvertTo-Json -Depth 5) -Headers @{ 'X-Trace-Id' = 'start-tool' } -TimeoutSec 120
    $status = Invoke-RestMethod -Method GET -Uri "$backendUrl/api/status" -TimeoutSec 15
}

$state = [ordered]@{
    status = 'started'
    started_at = (Get-Date).ToUniversalTime().ToString('o')
    ui_url = $uiUrl
    host_runner_url = $hostRunnerUrl
    backend_url = $backendUrl
    browser_port = $BrowserPort
    startup_model = $StartupModel
    allow_all = $true
    session_start_requested = [bool]$StartCopilotSession
    session_start_policy = if ($StartCopilotSession) { 'start-tool-fresh-copilot' } else { 'ai-console-on-demand-fresh-copilot' }
    copilot_window_mode = if ($HideCopilotWindow) { 'hidden' } else { 'visible' }
    singleton_policy = 'Copilot session starts fresh by default; browser session may reuse existing owned admin browser. For visible localhost admin UI work use runtime\start-collaborative-copilot-admin-browser.ps1 instead of the stage browser or automation browser'
    visible_admin_browser_script = '.\runtime\start-collaborative-copilot-admin-browser.ps1'
    admin_ui_opened_in_shared_browser = [bool]$OpenUiInSharedBrowser
    host_runner_started_by_script = $hostRunnerStarted
    backend_started_by_script = $backendStarted
    host_runner_pid = if ($hostRunnerProcess) { $hostRunnerProcess.Id } else { $null }
    backend_pid = if ($backendProcess) { $backendProcess.Id } else { $null }
    session_job_id = if ($sessionJob) { $sessionJob.job_id } else { $null }
    session_job_status = if ($sessionJob) { $sessionJob.status } else { 'not_requested' }
    copilot_status = $status.copilot_session.status
    browser_status = $status.browser_session.status
    logs = [ordered]@{
        host_runner_stdout = $hostRunnerOut
        host_runner_stderr = $hostRunnerErr
        backend_stdout = $backendOut
        backend_stderr = $backendErr
    }
}
$state | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $statePath -Encoding UTF8

Write-Host "Regression tool suite started - Graphical interface at: $uiUrl"
