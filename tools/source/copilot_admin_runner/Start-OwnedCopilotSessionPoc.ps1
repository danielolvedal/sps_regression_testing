param(
    [ValidateSet('VisibleTerminal', 'RedirectedVersionProbe', 'NonInteractivePromptDryRun')]
    [string]$Mode = 'VisibleTerminal',
    [string]$Title = 'SPS Copilot Admin Runner Owned Session',
    [string]$Prompt = 'Svara exakt: owned-copilot-poc-ok',
    [int]$TimeoutSeconds = 20,
    [switch]$DryRun,
    [string]$StatePath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
$logDir = Join-Path $repoRoot 'tmp\copilot_admin_runner_logs'
$stateDir = Join-Path $repoRoot 'tmp\copilot_admin_runner_state'
$registryScript = Join-Path $PSScriptRoot 'project_session_registry.py'
$null = New-Item -ItemType Directory -Path $logDir -Force
$null = New-Item -ItemType Directory -Path $stateDir -Force
if (-not $StatePath) {
    $StatePath = Join-Path $stateDir 'owned-copilot-session-poc.json'
}
$logPath = Join-Path $logDir ("owned-copilot-poc-{0}.jsonl" -f (Get-Date).ToUniversalTime().ToString('yyyyMMdd'))
$sessionKey = "owned-terminal-poc::$StatePath"

function Write-OwnedCopilotLog {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Event,
        [hashtable]$Details = @{}
    )

    $record = [ordered]@{
        timestamp = (Get-Date).ToUniversalTime().ToString('o')
        event_id = [guid]::NewGuid().ToString('N')
        event = $Event
        mode = $Mode
        pid = $PID
        repo_root = $repoRoot.Path
        details = $Details
    }
    $line = ($record | ConvertTo-Json -Depth 10 -Compress) + [Environment]::NewLine
    $encoding = New-Object System.Text.UTF8Encoding $false
    for ($attempt = 1; $attempt -le 5; $attempt++) {
        try {
            [System.IO.File]::AppendAllText($logPath, $line, $encoding)
            return
        } catch {
            if ($attempt -eq 5) {
                throw
            }
            Start-Sleep -Milliseconds (50 * $attempt)
        }
    }
}

function Get-CopilotCommand {
    $command = Get-Command copilot -ErrorAction Stop
    $command.Source
}

function Invoke-RedirectedProcess {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FileName,
        [string[]]$Arguments
    )

    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $FileName
    $startInfo.Arguments = ($Arguments | ForEach-Object {
        if ($_ -match '[\s"]') {
            '"' + ($_ -replace '"', '\"') + '"'
        } else {
            $_
        }
    }) -join ' '
    $startInfo.WorkingDirectory = $repoRoot.Path
    $startInfo.UseShellExecute = $false
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.CreateNoWindow = $true

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo
    $null = $process.Start()
    if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
        $process.Kill()
        throw "Process timed out after $TimeoutSeconds seconds."
    }

    [ordered]@{
        exit_code = $process.ExitCode
        stdout = $process.StandardOutput.ReadToEnd()
        stderr = $process.StandardError.ReadToEnd()
    }
}

$copilotPath = Get-CopilotCommand
Write-OwnedCopilotLog -Event 'owned_copilot_poc_started' -Details @{
    mode = $Mode
    dry_run = [bool]$DryRun
    copilot_path = $copilotPath
    state_path = $StatePath
}

if ($Mode -eq 'RedirectedVersionProbe') {
    $probe = Invoke-RedirectedProcess -FileName $copilotPath -Arguments @('--version')
    $result = [ordered]@{
        status = if ($probe.exit_code -eq 0) { 'passed' } else { 'failed' }
        mode = $Mode
        copilot_path = $copilotPath
        exit_code = $probe.exit_code
        stdout = $probe.stdout
        stderr = $probe.stderr
        log_path = $logPath
        conclusion = 'Runner can own stdout/stderr for non-interactive Copilot CLI commands. This does not prove a collaborative visible interactive PTY.'
    }
    Write-OwnedCopilotLog -Event 'redirected_version_probe_completed' -Details @{
        exit_code = $probe.exit_code
        stdout_length = $probe.stdout.Length
        stderr_length = $probe.stderr.Length
    }
    $result | ConvertTo-Json -Depth 10
    exit 0
}

if ($Mode -eq 'NonInteractivePromptDryRun') {
    $result = [ordered]@{
        status = 'dry-run'
        mode = $Mode
        copilot_path = $copilotPath
        repo_root = $repoRoot.Path
        command = @($copilotPath, '-p', $Prompt)
        log_path = $logPath
        conclusion = 'copilot -p can be evaluated later for runner-owned non-interactive work, but it is not a collaborative visible session.'
    }
    Write-OwnedCopilotLog -Event 'non_interactive_prompt_dry_run_completed' -Details @{
        prompt_length = $Prompt.Length
    }
    $result | ConvertTo-Json -Depth 10
    exit 0
}

$escapedRepo = $repoRoot.Path.Replace("'", "''")
$escapedTitle = $Title.Replace("'", "''")
$command = @"
`$Host.UI.RawUI.WindowTitle = '$escapedTitle'
Set-Location '$escapedRepo'
Write-Host 'Starting Copilot CLI in runner-owned visible terminal POC...'
Write-Host 'This validates collaboration visibility, not direct stdin/stdout ownership.'
copilot
"@

if ($DryRun) {
    $result = [ordered]@{
        status = 'dry-run'
        mode = $Mode
        title = $Title
        copilot_path = $copilotPath
        repo_root = $repoRoot.Path
        command = $command
        state_path = $StatePath
        log_path = $logPath
        conclusion = 'DryRun did not start a visible terminal.'
    }
    Write-OwnedCopilotLog -Event 'visible_terminal_dry_run_completed' -Details @{
        title = $Title
    }
    $result | ConvertTo-Json -Depth 10
    exit 0
}

$process = Start-Process -FilePath 'powershell.exe' -ArgumentList @(
    '-NoExit',
    '-NoProfile',
    '-ExecutionPolicy', 'Bypass',
    '-Command', $command
) -WorkingDirectory $repoRoot.Path -PassThru

$state = [ordered]@{
    status = 'started'
    mode = $Mode
    title = $Title
    shell_process_id = $process.Id
    copilot_path = $copilotPath
    repo_root = $repoRoot.Path
    state_path = $StatePath
    log_path = $logPath
    limitation = 'The session is visible and collaborative, but stdin/stdout are owned by the terminal, not redirected to the runner. Use terminal binding/input adapter for commands.'
}
$state | ConvertTo-Json -Depth 10 | Set-Content -Path $StatePath -Encoding UTF8
python $registryScript upsert --session-key $sessionKey --kind 'owned-terminal-poc' --source 'tools\source\copilot_admin_runner\Start-OwnedCopilotSessionPoc.ps1' --status 'started' --control-method 'process-id' --state-path $StatePath --process-id ([string]$process.Id) --note 'visible owned terminal Copilot POC' | Out-Null
Write-OwnedCopilotLog -Event 'visible_terminal_started' -Details @{
    title = $Title
    shell_process_id = $process.Id
}
$state | ConvertTo-Json -Depth 10
