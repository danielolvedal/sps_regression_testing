param(
    [Parameter(Mandatory = $true)]
    [string]$Text,
    [switch]$ClearLine,
    [switch]$NoSubmit,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')
$stateDir = if ($env:COPILOT_ADMIN_RUNNER_STATE_DIR) { $env:COPILOT_ADMIN_RUNNER_STATE_DIR } else { Join-Path $repoRoot 'tmp\copilot_admin_runner_state' }
$queueDir = Join-Path $stateDir 'node-pty-copilot-input-queue'
$null = New-Item -ItemType Directory -Path $queueDir -Force
$statePath = Join-Path $stateDir 'node-pty-copilot-session.json'
$inputId = [guid]::NewGuid().ToString('N')

$sessionRunning = $false
if (Test-Path $statePath) {
    $state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
    if ($state.wrapper_pid -and (Get-Process -Id $state.wrapper_pid -ErrorAction SilentlyContinue)) {
        $sessionRunning = $true
    }
}
if (-not $DryRun -and -not $sessionRunning) {
    throw "No running node-pty Copilot session was found. Start one with .\runtime\start-copilot-admin-node-pty-window.ps1 or use -DryRun."
}

$request = [ordered]@{
    input_id = $inputId
    created_at = (Get-Date).ToUniversalTime().ToString('o')
    text = if ($ClearLine) { "$([char]21)$Text" } else { $Text }
    display_text = $Text
    clear_line = [bool]$ClearLine
    submit = -not [bool]$NoSubmit
}
$fileName = 'input-{0}-{1}.json' -f (Get-Date).ToUniversalTime().ToString('yyyyMMddHHmmssfff'), ([guid]::NewGuid().ToString('N'))
$filePath = Join-Path $queueDir $fileName
if (-not $DryRun) {
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($filePath, ($request | ConvertTo-Json -Depth 10), $utf8NoBom)
}

[ordered]@{
    status = if ($DryRun) { 'dry_run' } else { 'queued' }
    input_id = $inputId
    input_path = if ($DryRun) { $null } else { $filePath }
    queue_dir = $queueDir
    state_dir = $stateDir
    state_path = $statePath
    session_state_exists = Test-Path $statePath
    session_running = $sessionRunning
    text_length = $Text.Length
    clear_line = [bool]$ClearLine
    submit = -not [bool]$NoSubmit
    dry_run = [bool]$DryRun
} | ConvertTo-Json -Depth 10
