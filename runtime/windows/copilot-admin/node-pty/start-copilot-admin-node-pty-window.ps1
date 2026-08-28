param(
    [switch]$LogInput,
    [switch]$RestartExisting,
    [int]$CloseTimeoutSeconds = 30,
    [string]$StartupModel = 'auto',
    [switch]$AllowAll = $true,
    [switch]$Hidden,
    [int]$TerminalColumns = 160,
    [int]$TerminalRows = 42
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')
$sessionScript = Join-Path $PSScriptRoot 'start-copilot-admin-node-pty-session.ps1'
$registryScript = Join-Path $repoRoot 'tools\source\copilot_admin_runner\project_session_registry.py'
$registryPath = Join-Path $repoRoot 'tmp\copilot_admin_control_plane\project-controlled-copilot-sessions.json'
$stateDir = if ($env:COPILOT_ADMIN_RUNNER_STATE_DIR) { $env:COPILOT_ADMIN_RUNNER_STATE_DIR } else { Join-Path $repoRoot 'tmp\copilot_admin_runner_state' }
$transportDbPath = Join-Path $stateDir 'copilot-admin-transport.sqlite'
$statePath = "$transportDbPath#session_state"
$windowStatePath = "$transportDbPath#session_state"
$powershell = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
$sessionKey = "node-pty::$stateDir"

function Read-OptionalJsonFile {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }
    try {
        return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
    } catch {
        return $null
    }
}

function Get-RegisteredNodePtySession {
    $registry = Read-OptionalJsonFile -Path $registryPath
    if (-not $registry) {
        return $null
    }
    $sessions = @($registry.sessions)
    foreach ($session in $sessions) {
        if (-not $session) {
            continue
        }
        if ([string]$session.session_key -eq $sessionKey) {
            return $session
        }
    }
    return $null
}

function Update-ProjectSessionRegistry {
    param(
        [Parameter(Mandatory = $true)][ValidateSet('upsert', 'mark-stopped')][string]$Action,
        [string]$Status,
        [int]$LauncherPid
    )
    $arguments = @($registryScript)
    if ($Action -eq 'upsert') {
        $arguments += @(
            'upsert',
            '--session-key', $sessionKey,
            '--kind', 'node-pty',
            '--source', 'runtime\windows\copilot-admin\node-pty\start-copilot-admin-node-pty-window.ps1',
            '--status', $Status,
            '--control-method', 'runner-state',
            '--state-dir', $stateDir,
            '--state-path', $statePath,
            '--window-state-path', $windowStatePath,
            '--hidden', ($(if ($Hidden) { 'true' } else { 'false' })),
            '--visible-window-expected', ($(if ($Hidden) { 'false' } else { 'true' }))
        )
        if ($LauncherPid) {
            $arguments += @('--launcher-pid', [string]$LauncherPid)
        }
    } else {
        $arguments += @('mark-stopped', '--session-key', $sessionKey)
    }
    python @arguments | Out-Null
}

if ($true) {
    $existingSession = Get-RegisteredNodePtySession
    if ($existingSession -and $existingSession.wrapper_pid) {
        $existingProcess = Get-Process -Id $existingSession.wrapper_pid -ErrorAction SilentlyContinue
        if ($existingProcess) {
            if (-not $RestartExisting) {
                throw "An existing node-pty Copilot wrapper is still running with PID $($existingSession.wrapper_pid). Close that window first, or re-run with -RestartExisting."
            }

            Stop-Process -Id $existingSession.wrapper_pid -Force
            $deadline = (Get-Date).AddSeconds($CloseTimeoutSeconds)
            while ((Get-Date) -lt $deadline -and (Get-Process -Id $existingSession.wrapper_pid -ErrorAction SilentlyContinue)) {
                Start-Sleep -Milliseconds 250
            }

            if (Get-Process -Id $existingSession.wrapper_pid -ErrorAction SilentlyContinue) {
                throw "The existing node-pty Copilot wrapper PID $($existingSession.wrapper_pid) did not close within $CloseTimeoutSeconds seconds. Close the window manually before continuing."
            }
            Update-ProjectSessionRegistry -Action 'mark-stopped'
        }
    }
}

if ($true) {
    $existingSession = Get-RegisteredNodePtySession
    if ($existingSession -and $existingSession.launcher_pid) {
        $existingLauncher = Get-Process -Id $existingSession.launcher_pid -ErrorAction SilentlyContinue
        if ($existingLauncher) {
            $wrapperStillRunning = $false
            if ($existingSession.wrapper_pid) {
                $wrapperStillRunning = [bool](Get-Process -Id $existingSession.wrapper_pid -ErrorAction SilentlyContinue)
            }
            if (-not $RestartExisting -and $wrapperStillRunning) {
                throw "An existing node-pty launcher window is still running with PID $($existingSession.launcher_pid). Close that window first, or re-run with -RestartExisting."
            }
            Stop-Process -Id $existingSession.launcher_pid -Force
            $deadline = (Get-Date).AddSeconds($CloseTimeoutSeconds)
            while ((Get-Date) -lt $deadline -and (Get-Process -Id $existingSession.launcher_pid -ErrorAction SilentlyContinue)) {
                Start-Sleep -Milliseconds 250
            }
            if (Get-Process -Id $existingSession.launcher_pid -ErrorAction SilentlyContinue) {
                throw "The existing node-pty launcher PID $($existingSession.launcher_pid) did not close within $CloseTimeoutSeconds seconds. Close the window manually before continuing."
            }
            Update-ProjectSessionRegistry -Action 'mark-stopped'
        }
    }
}

$legacyStateJsonPath = Join-Path $stateDir 'node-pty-copilot-session.json'
$legacyWindowStateJsonPath = Join-Path $stateDir 'node-pty-copilot-window.json'
Remove-Item -LiteralPath $legacyStateJsonPath -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $legacyWindowStateJsonPath -ErrorAction SilentlyContinue
$transcriptPath = Join-Path $stateDir 'node-pty-copilot-session-output.txt'
$inputTranscriptPath = Join-Path $stateDir 'node-pty-copilot-session-input.txt'
Remove-Item -LiteralPath $transcriptPath -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $inputTranscriptPath -ErrorAction SilentlyContinue

$command = @"
Set-Location -LiteralPath '$($repoRoot.Path)'
`$env:COPILOT_ADMIN_RUNNER_STATE_DIR = '$stateDir'
`$env:COPILOT_ADMIN_PROJECT_SESSION_HIDDEN = '$(if ($Hidden) { '1' } else { '0' })'
`$env:COPILOT_ADMIN_PTY_COLS = '$TerminalColumns'
`$env:COPILOT_ADMIN_PTY_ROWS = '$TerminalRows'
`$env:COPILOT_ADMIN_LAUNCHER_PID = "`$PID"
if (-not $(if ($Hidden) { '$true' } else { '$false' })) {
  try {
    `$raw = `$Host.UI.RawUI
    `$bufferSize = `$raw.BufferSize
    `$windowSize = `$raw.WindowSize
    if (`$bufferSize.Width -lt $TerminalColumns) { `$bufferSize.Width = $TerminalColumns }
    if (`$bufferSize.Height -lt ($TerminalRows + 10)) { `$bufferSize.Height = $TerminalRows + 10 }
    `$raw.BufferSize = `$bufferSize
    `$windowSize.Width = [Math]::Min($TerminalColumns, `$raw.BufferSize.Width)
    `$windowSize.Height = [Math]::Min($TerminalRows, `$raw.BufferSize.Height)
    `$raw.WindowSize = `$windowSize
  } catch {
  }
}
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

Update-ProjectSessionRegistry -Action 'upsert' -Status 'launcher_started' -LauncherPid $process.Id

$deadline = (Get-Date).AddSeconds(20)
while ((Get-Date) -lt $deadline) {
    $registered = Get-RegisteredNodePtySession
    if ($registered -and $registered.wrapper_pid) {
        break
    }
    Start-Sleep -Milliseconds 250
}

[ordered]@{
    status = if (($registered = Get-RegisteredNodePtySession) -and $registered.wrapper_pid) { 'started' } else { 'started_state_pending' }
    launcher_pid = $process.Id
    state_path = $statePath
    window_state_path = $windowStatePath
    state_db_path = $transportDbPath
    session_command = $sessionScript
    input_logging_enabled = [bool]$LogInput
    startup_model = $StartupModel
    startup_allow_all = [bool]$AllowAll
    hidden = [bool]$Hidden
    visible_window_expected = -not [bool]$Hidden
    terminal_columns = $TerminalColumns
    terminal_rows = $TerminalRows
    restart_existing = [bool]$RestartExisting
    note = if ($Hidden) { 'The node-pty-owned Copilot CLI session is running in a hidden helper process. Use the frontend AI console for input/output.' } else { 'A visible PowerShell window should now contain the node-pty-owned Copilot CLI session.' }
} | ConvertTo-Json -Depth 10
