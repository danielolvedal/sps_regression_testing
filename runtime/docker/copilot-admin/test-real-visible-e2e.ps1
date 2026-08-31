[CmdletBinding()]
param(
    [int]$HostRunnerPort = 8876,
    [int]$BackendPort = 8877,
    [int]$BrowserPort = 9322,
    [int]$TimeoutSeconds = 180,
    [switch]$RestartExisting,
    [switch]$ShowTestCopilotWindow,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
$runner = Join-Path $repoRoot 'tools\source\copilot_admin_runner\copilot_admin_runner.py'
$backend = Join-Path $repoRoot 'tools\source\copilot_admin_control_plane\backend\app.py'
$frontend = Join-Path $repoRoot 'tools\source\copilot_admin_control_plane\frontend'
$e2eDir = Join-Path $repoRoot 'tools\source\copilot_admin_control_plane\e2e'
$playwrightScript = Join-Path $e2eDir 'real_visible_playwright_e2e.mjs'
$tmpDir = Join-Path $repoRoot 'tmp\copilot_admin_control_plane\real_visible_e2e'
$isolatedRunnerStateDir = Join-Path $tmpDir 'runner_state'
$artifactPath = Join-Path $tmpDir 'real-visible-e2e-artifact.json'
$null = New-Item -ItemType Directory -Path $tmpDir -Force
$null = New-Item -ItemType Directory -Path $isolatedRunnerStateDir -Force

$hostRunnerUrl = "http://127.0.0.1:$HostRunnerPort"
$backendUrl = "http://127.0.0.1:$BackendPort"

if ($DryRun) {
    [ordered]@{
        status = 'dry_run'
        host_runner_url = $hostRunnerUrl
        backend_url = $backendUrl
        runner = $runner
        backend = $backend
        frontend = $frontend
        e2e_dir = $e2eDir
        playwright_script = $playwrightScript
        tmp_dir = $tmpDir
        isolated_runner_state_dir = $isolatedRunnerStateDir
        artifact_path = $artifactPath
        browser_port = $BrowserPort
        would_start_hidden_isolated_copilot_helper = -not [bool]$ShowTestCopilotWindow
        would_start_visible_isolated_copilot_test_session = [bool]$ShowTestCopilotWindow
        would_keep_collaborative_browser_visible = $true
        would_use_isolated_runner_state = $true
    } | ConvertTo-Json -Depth 10
    exit 0
}

function Invoke-JsonRequest {
    param(
        [Parameter(Mandatory = $true)][string]$Method,
        [Parameter(Mandatory = $true)][string]$Uri,
        [object]$Body = $null
    )

    $headers = @{ 'X-Trace-Id' = 'real-visible-e2e' }
    $requestTimeout = [Math]::Max(10, [Math]::Min($TimeoutSeconds, 300))
    if ($null -eq $Body) {
        return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $headers -TimeoutSec $requestTimeout
    }
    return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $headers -ContentType 'application/json' -Body ($Body | ConvertTo-Json -Depth 10) -TimeoutSec $requestTimeout
}

function Wait-JsonEndpoint {
    param(
        [Parameter(Mandatory = $true)][string]$Uri,
        [int]$Timeout = 30
    )

    $deadline = (Get-Date).AddSeconds($Timeout)
    $lastError = $null
    while ((Get-Date) -lt $deadline) {
        try {
            return Invoke-JsonRequest -Method GET -Uri $Uri
        } catch {
            $lastError = $_.Exception.Message
            Start-Sleep -Milliseconds 500
        }
    }
    throw "Timed out waiting for $Uri. Last error: $lastError"
}

$hostRunnerProcess = $null
$backendProcess = $null
$sessionStopped = $false
$previousRunnerStateDir = $env:COPILOT_ADMIN_RUNNER_STATE_DIR

try {
    $hostRunnerOut = Join-Path $tmpDir 'host-runner-api.out.log'
    $hostRunnerErr = Join-Path $tmpDir 'host-runner-api.err.log'
    $backendOut = Join-Path $tmpDir 'backend.out.log'
    $backendErr = Join-Path $tmpDir 'backend.err.log'

    $env:COPILOT_ADMIN_RUNNER_STATE_DIR = $isolatedRunnerStateDir
    $hostRunnerProcess = Start-Process -FilePath 'python' -ArgumentList @(
        $runner,
        'http-server',
        '--host', '127.0.0.1',
        '--port', [string]$HostRunnerPort
    ) -WorkingDirectory $repoRoot -RedirectStandardOutput $hostRunnerOut -RedirectStandardError $hostRunnerErr -PassThru

    $env:SPS_REPO_ROOT = $repoRoot.Path
    $env:COPILOT_ADMIN_FRONTEND_DIR = $frontend
    $env:COPILOT_ADMIN_HOST_RUNNER_URL = $hostRunnerUrl
    $env:COPILOT_ADMIN_BACKEND_HOST = '127.0.0.1'
    $env:COPILOT_ADMIN_BACKEND_PORT = [string]$BackendPort
    $env:COPILOT_ADMIN_SESSION_BROWSER_PORT = [string]$BrowserPort

    $backendProcess = Start-Process -FilePath 'python' -ArgumentList @(
        $backend,
        '--host', '127.0.0.1',
        '--port', [string]$BackendPort
    ) -WorkingDirectory $repoRoot -RedirectStandardOutput $backendOut -RedirectStandardError $backendErr -PassThru

    $null = Wait-JsonEndpoint -Uri "$hostRunnerUrl/health" -Timeout 30
    $null = Wait-JsonEndpoint -Uri "$backendUrl/api/health" -Timeout 30

    if ($RestartExisting) {
        try {
            $null = Invoke-JsonRequest -Method POST -Uri "$hostRunnerUrl/api/session/stop" -Body @{ port = $BrowserPort; timeout_seconds = 20 }
        } catch {
        }
    }

    $env:COPILOT_ADMIN_REAL_E2E_BACKEND_URL = $backendUrl
    $env:COPILOT_ADMIN_REAL_E2E_ARTIFACT = $artifactPath
    $env:COPILOT_ADMIN_EXPECTED_PROJECT = 'SPS'
    $env:COPILOT_ADMIN_REAL_E2E_SHOW_TEST_SESSION = if ($ShowTestCopilotWindow) { '1' } else { '0' }

    Push-Location $e2eDir
    try {
        node $playwrightScript
        if ($LASTEXITCODE -ne 0) {
            throw "Playwright real-visible E2E failed with exit code $LASTEXITCODE."
        }
    } finally {
        Pop-Location
    }

    $artifact = Get-Content -LiteralPath $artifactPath -Raw | ConvertFrom-Json
    $status = Invoke-JsonRequest -Method GET -Uri "$backendUrl/api/status"

    [ordered]@{
        status = [string]$artifact.status
        backend_url = $backendUrl
        host_runner_url = $hostRunnerUrl
        isolated_runner_state_dir = $isolatedRunnerStateDir
        hidden_copilot_helper = -not [bool]$ShowTestCopilotWindow
        visible_copilot_test_session = [bool]$ShowTestCopilotWindow
        collaborative_browser_visible = $true
        browser_port = $BrowserPort
        artifact_path = $artifactPath
        timings_ms = $artifact.timings_ms
        prompt = $artifact.prompt
        badges = $artifact.badges
        copilot_session = $status.copilot_session
        browser_session = $status.browser_session
        logs = [ordered]@{
            host_runner_stdout = $hostRunnerOut
            host_runner_stderr = $hostRunnerErr
            backend_stdout = $backendOut
            backend_stderr = $backendErr
        }
    } | ConvertTo-Json -Depth 20
} finally {
    try {
        $null = Invoke-JsonRequest -Method POST -Uri "$hostRunnerUrl/api/session/stop" -Body @{ port = $BrowserPort; timeout_seconds = 20 }
        $sessionStopped = $true
    } catch {
        $sessionStopped = $false
    }
    if ($backendProcess -and -not $backendProcess.HasExited) {
        Stop-Process -Id $backendProcess.Id -Force
    }
    if ($hostRunnerProcess -and -not $hostRunnerProcess.HasExited) {
        Stop-Process -Id $hostRunnerProcess.Id -Force
    }
    if ($null -eq $previousRunnerStateDir) {
        Remove-Item Env:\COPILOT_ADMIN_RUNNER_STATE_DIR -ErrorAction SilentlyContinue
    } else {
        $env:COPILOT_ADMIN_RUNNER_STATE_DIR = $previousRunnerStateDir
    }
    Remove-Item Env:\COPILOT_ADMIN_REAL_E2E_BACKEND_URL -ErrorAction SilentlyContinue
    Remove-Item Env:\COPILOT_ADMIN_REAL_E2E_ARTIFACT -ErrorAction SilentlyContinue
    Remove-Item Env:\COPILOT_ADMIN_EXPECTED_PROJECT -ErrorAction SilentlyContinue
    Remove-Item Env:\COPILOT_ADMIN_REAL_E2E_SHOW_TEST_SESSION -ErrorAction SilentlyContinue
    Remove-Item Env:\COPILOT_ADMIN_SESSION_BROWSER_PORT -ErrorAction SilentlyContinue
}
