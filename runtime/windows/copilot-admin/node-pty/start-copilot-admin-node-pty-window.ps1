param(
    [switch]$LogInput,
    [switch]$RestartExisting,
    [int]$CloseTimeoutSeconds = 30
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')
$sessionScript = Join-Path $PSScriptRoot 'start-copilot-admin-node-pty-session.ps1'
$statePath = Join-Path $repoRoot 'tmp\copilot_admin_runner_state\node-pty-copilot-session.json'
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

Remove-Item -LiteralPath $statePath -ErrorAction SilentlyContinue
$transcriptPath = Join-Path $repoRoot 'tmp\copilot_admin_runner_state\node-pty-copilot-session-output.txt'
$inputTranscriptPath = Join-Path $repoRoot 'tmp\copilot_admin_runner_state\node-pty-copilot-session-input.txt'
Remove-Item -LiteralPath $transcriptPath -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $inputTranscriptPath -ErrorAction SilentlyContinue

$command = @"
Set-Location -LiteralPath '$($repoRoot.Path)'
& '$sessionScript'$(if ($LogInput) { ' -LogInput' } else { '' })
Write-Host ''
Write-Host 'Copilot node-pty session ended. Press Enter to close this window.'
Read-Host | Out-Null
"@

$encodedCommand = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($command))
$process = Start-Process -FilePath $powershell -ArgumentList @(
    '-NoProfile',
    '-ExecutionPolicy', 'Bypass',
    '-EncodedCommand', $encodedCommand
) -PassThru -WindowStyle Normal

$deadline = (Get-Date).AddSeconds(20)
while ((Get-Date) -lt $deadline -and -not (Test-Path $statePath)) {
    Start-Sleep -Milliseconds 250
}

[ordered]@{
    status = if (Test-Path $statePath) { 'started' } else { 'started_state_pending' }
    launcher_pid = $process.Id
    state_path = $statePath
    session_command = $sessionScript
    input_logging_enabled = [bool]$LogInput
    restart_existing = [bool]$RestartExisting
    note = 'A visible PowerShell window should now contain the node-pty-owned Copilot CLI session.'
} | ConvertTo-Json -Depth 10
