param(
    [switch]$LogInput,
    [switch]$RestartExisting,
    [int]$CloseTimeoutSeconds = 30,
    [string]$StartupModel = '',
    [switch]$AllowAll = $true,
    [switch]$Hidden
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')
$sessionScript = Join-Path $PSScriptRoot 'start-copilot-admin-node-pty-session.ps1'
$stateDir = if ($env:COPILOT_ADMIN_RUNNER_STATE_DIR) { $env:COPILOT_ADMIN_RUNNER_STATE_DIR } else { Join-Path $repoRoot 'tmp\copilot_admin_runner_state' }
$statePath = Join-Path $stateDir 'node-pty-copilot-session.json'
$windowStatePath = Join-Path $stateDir 'node-pty-copilot-window.json'
$powershell = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'

if (Test-Path $statePath) {
    $existingState = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
    if ($existingState.wrapper_pid) {
        $existingProcess = Get-Process -Id $existingState.wrapper_pid -ErrorAction SilentlyContinue
        if ($existingProcess) {
            if (-not $RestartExisting) {
                throw "An existing node-pty Copilot wrapper is still running with PID $($existingState.wrapper_pid). Close that window first, or re-run with -RestartExisting."
            }

            Stop-Process -Id $existingState.wrapper_pid -Force
            $deadline = (Get-Date).AddSeconds($CloseTimeoutSeconds)
            while ((Get-Date) -lt $deadline -and (Get-Process -Id $existingState.wrapper_pid -ErrorAction SilentlyContinue)) {
                Start-Sleep -Milliseconds 250
            }

            if (Get-Process -Id $existingState.wrapper_pid -ErrorAction SilentlyContinue) {
                throw "The existing node-pty Copilot wrapper PID $($existingState.wrapper_pid) did not close within $CloseTimeoutSeconds seconds. Close the window manually before continuing."
            }
        }
    }
}

if (Test-Path $windowStatePath) {
    $existingWindowState = Get-Content -LiteralPath $windowStatePath -Raw | ConvertFrom-Json
    if ($existingWindowState.launcher_pid) {
        $existingLauncher = Get-Process -Id $existingWindowState.launcher_pid -ErrorAction SilentlyContinue
        if ($existingLauncher) {
            if (-not $RestartExisting) {
                throw "An existing node-pty launcher window is still running with PID $($existingWindowState.launcher_pid). Close that window first, or re-run with -RestartExisting."
            }
            Stop-Process -Id $existingWindowState.launcher_pid -Force
        }
    }
}

Remove-Item -LiteralPath $statePath -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $windowStatePath -ErrorAction SilentlyContinue
$transcriptPath = Join-Path $stateDir 'node-pty-copilot-session-output.txt'
$inputTranscriptPath = Join-Path $stateDir 'node-pty-copilot-session-input.txt'
Remove-Item -LiteralPath $transcriptPath -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $inputTranscriptPath -ErrorAction SilentlyContinue

$command = @"
Set-Location -LiteralPath '$($repoRoot.Path)'
`$env:COPILOT_ADMIN_RUNNER_STATE_DIR = '$stateDir'
& '$sessionScript'$(if ($LogInput) { ' -LogInput' } else { '' })$(if ($StartupModel) { " -StartupModel '$StartupModel'" } else { '' })$(if ($AllowAll) { ' -AllowAll' } else { '' })
Write-Host ''
Write-Host 'Copilot node-pty session ended. Press Enter to close this window.'
Read-Host | Out-Null
"@

$encodedCommand = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($command))
$process = Start-Process -FilePath $powershell -ArgumentList @(
    '-NoProfile',
    '-ExecutionPolicy', 'Bypass',
    '-EncodedCommand', $encodedCommand
) -PassThru -WindowStyle $(if ($Hidden) { 'Hidden' } else { 'Normal' })

$windowState = [ordered]@{
    status = 'launcher_started'
    started_at = (Get-Date).ToUniversalTime().ToString('o')
    updated_at = (Get-Date).ToUniversalTime().ToString('o')
    launcher_pid = $process.Id
    state_path = $statePath
    state_dir = $stateDir
    session_command = $sessionScript
    input_logging_enabled = [bool]$LogInput
    startup_model = $StartupModel
    startup_allow_all = [bool]$AllowAll
    hidden = [bool]$Hidden
    visible_window_expected = -not [bool]$Hidden
}
$null = New-Item -ItemType Directory -Path (Split-Path -Parent $windowStatePath) -Force
$windowState | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $windowStatePath -Encoding UTF8

$deadline = (Get-Date).AddSeconds(20)
while ((Get-Date) -lt $deadline -and -not (Test-Path $statePath)) {
    Start-Sleep -Milliseconds 250
}

[ordered]@{
    status = if (Test-Path $statePath) { 'started' } else { 'started_state_pending' }
    launcher_pid = $process.Id
    state_path = $statePath
    window_state_path = $windowStatePath
    session_command = $sessionScript
    input_logging_enabled = [bool]$LogInput
    startup_model = $StartupModel
    startup_allow_all = [bool]$AllowAll
    hidden = [bool]$Hidden
    visible_window_expected = -not [bool]$Hidden
    restart_existing = [bool]$RestartExisting
    note = if ($Hidden) { 'The node-pty-owned Copilot CLI session is running in a hidden helper process. Use the frontend AI console for input/output.' } else { 'A visible PowerShell window should now contain the node-pty-owned Copilot CLI session.' }
} | ConvertTo-Json -Depth 10
