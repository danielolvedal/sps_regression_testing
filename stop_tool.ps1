[CmdletBinding()]
param(
    [string]$HostName = '127.0.0.1',
    [int]$BackendPort = 8765,
    [int]$HostRunnerPort = 8766,
    [int]$BrowserPort = 9222,
    [int]$TimeoutSeconds = 30,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = $PSScriptRoot
$hostRunnerUrl = "http://$HostName`:$HostRunnerPort"
$backendUrl = "http://$HostName`:$BackendPort"
$stateDir = Join-Path $repoRoot 'tmp\copilot_admin_control_plane\start_tool'
$statePath = Join-Path $stateDir 'latest.json'
$runnerStateDir = Join-Path $repoRoot 'tmp\copilot_admin_runner_state'
$runnerScript = Join-Path $repoRoot 'runtime\invoke-copilot-admin-host-runner.ps1'
$registryScript = Join-Path $repoRoot 'tools\source\copilot_admin_runner\project_session_registry.py'
$registryPath = Join-Path $repoRoot 'tmp\copilot_admin_control_plane\project-controlled-copilot-sessions.json'

function Test-JsonEndpoint {
    param([Parameter(Mandatory = $true)][string]$Uri)
    try {
        Invoke-RestMethod -Uri $Uri -Method GET -TimeoutSec 2 | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Read-JsonFile {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }
    try {
        return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
    } catch {
        throw "Could not parse JSON from $Path. $($_.Exception.Message)"
    }
}

function Get-OptionalProperty {
    param(
        $Object,
        [Parameter(Mandatory = $true)][string]$Name
    )
    if ($null -eq $Object) {
        return $null
    }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) {
        return $null
    }
    return $property.Value
}

function Stop-RecordedProcess {
    param(
        [Parameter(Mandatory = $true)][string]$ProcessName,
        [int]$ProcessId,
        [int]$TimeoutSeconds = 30
    )
    if (-not $ProcessId) {
        return $false
    }
    $process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if (-not $process) {
        return $false
    }
    $targets = New-Object 'System.Collections.Generic.List[int]'
    $visited = New-Object 'System.Collections.Generic.HashSet[int]'
    function Add-Descendants {
        param([int]$TargetProcessId)
        if (-not $visited.Add($TargetProcessId)) {
            return
        }
        foreach ($child in @(Get-CimInstance Win32_Process -Filter "ParentProcessId = $TargetProcessId" -ErrorAction SilentlyContinue)) {
            Add-Descendants -TargetProcessId ([int]$child.ProcessId)
        }
        $targets.Add($TargetProcessId)
    }
    Add-Descendants -TargetProcessId $ProcessId
    foreach ($targetProcessId in $targets) {
        Stop-Process -Id $targetProcessId -Force -ErrorAction SilentlyContinue
    }
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline -and (Get-Process -Id $ProcessId -ErrorAction SilentlyContinue)) {
        Start-Sleep -Milliseconds 250
    }
    if (Get-Process -Id $ProcessId -ErrorAction SilentlyContinue) {
        throw "Could not stop $ProcessName process PID $ProcessId."
    }
    return $true
}

function Stop-CompatibleListenerProcesses {
    param(
        [Parameter(Mandatory = $true)][string]$ExpectedCommandSubstring,
        [Parameter(Mandatory = $true)][string]$ProcessName,
        [int]$TimeoutSeconds = 30
    )

    $listeners = @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess } | Select-Object OwningProcess, LocalPort)
    $results = @()
    foreach ($group in ($listeners | Group-Object -Property OwningProcess)) {
        $ownerPid = [int]$group.Name
        $owner = Get-CimInstance Win32_Process -Filter "ProcessId=$ownerPid" -ErrorAction SilentlyContinue
        if (-not $owner) {
            continue
        }
        $commandLine = [string]$owner.CommandLine
        if (-not $commandLine.Contains($ExpectedCommandSubstring)) {
            continue
        }
        $ports = @($group.Group | Sort-Object LocalPort | ForEach-Object { [int]$_.LocalPort })
        $stopped = Stop-RecordedProcess -ProcessName $ProcessName -ProcessId $ownerPid -TimeoutSeconds $TimeoutSeconds
        $results += [ordered]@{
            status = if ($stopped) { 'stopped' } else { 'not_running' }
            process_id = $ownerPid
            local_ports = $ports
        }
    }
    return @($results)
}

function Invoke-RunnerStop {
    param(
        [Parameter(Mandatory = $true)][ValidateSet('copilot-stop', 'browser-stop')][string]$Action,
        [Parameter(Mandatory = $true)][string]$StateDir,
        [int]$Port,
        [int]$TimeoutSeconds = 30
    )
    $arguments = @{
        Action = $Action
        TimeoutSeconds = $TimeoutSeconds
    }
    if ($Action -eq 'browser-stop') {
        $arguments.Port = $Port
    }
    $previousStateDir = $env:COPILOT_ADMIN_RUNNER_STATE_DIR
    # Ensure tool_error_logs exists and inherit if provided
    $logsDir = if ($env:TOOL_ERROR_LOG_DIR) { $env:TOOL_ERROR_LOG_DIR } else { Join-Path $repoRoot 'tool_error_logs' }
    if (-not (Test-Path $logsDir)) { New-Item -Path $logsDir -ItemType Directory -Force | Out-Null }

    try {
        $env:COPILOT_ADMIN_RUNNER_STATE_DIR = $StateDir
        $raw = & $runnerScript @arguments | Out-String
    } finally {
        if ($null -eq $previousStateDir) {
            Remove-Item Env:\COPILOT_ADMIN_RUNNER_STATE_DIR -ErrorAction SilentlyContinue
        } else {
            $env:COPILOT_ADMIN_RUNNER_STATE_DIR = $previousStateDir
        }
    }

    # Persist raw runner script output to tool_error_logs for debugging
    try {
        $timestamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
        $runnerLog = Join-Path $logsDir ("runner-$Action-$timestamp.log")
        $raw | Out-File -FilePath $runnerLog -Encoding UTF8
    } catch {
        Write-Verbose "Failed to write runner raw output to log: $_"
    }

    if (-not $raw.Trim()) {
        throw "No JSON was returned from $runnerScript for action $Action."
    }
    try {
        return $raw | ConvertFrom-Json
    } catch {
        throw "Could not parse JSON returned from $runnerScript for action $Action. Raw output: $raw"
    }
}

function Update-ProjectSessionRegistry {
    param(
        [Parameter(Mandatory = $true)][string]$SessionKey,
        [Parameter(Mandatory = $true)][ValidateSet('stopped', 'terminated')][string]$Status
    )
    python $registryScript mark-stopped --session-key $SessionKey --status $Status | Out-Null
}

function Get-RegisteredSessionByStateDir {
    param([Parameter(Mandatory = $true)][string]$StateDir)
    $registry = Read-JsonFile -Path $registryPath
    if (-not $registry) {
        return $null
    }
    foreach ($session in @($registry.sessions)) {
        if (-not $session) {
            continue
        }
        if (([string](Get-OptionalProperty -Object $session -Name 'state_dir')) -eq $StateDir) {
            return $session
        }
    }
    return $null
}

function Get-ProjectControlledSessions {
    $sessions = @()
    $registry = Read-JsonFile -Path $registryPath
    $registrySessions = @()
    if ($registry) {
        $registrySessions = @(Get-OptionalProperty -Object $registry -Name 'sessions')
    }
    foreach ($session in $registrySessions) {
        if (-not $session) {
            continue
        }
        $status = [string](Get-OptionalProperty -Object $session -Name 'status')
        if ($status -in @('stopped', 'terminated')) {
            continue
        }
        $sessions += $session
    }

    foreach ($candidateDir in @(
        (Join-Path $repoRoot 'tmp\copilot_admin_runner_state'),
        (Join-Path $repoRoot 'tmp\copilot_admin_control_plane\real_visible_e2e\runner_state')
    )) {
        $transportDbPath = Join-Path $candidateDir 'copilot-admin-transport.sqlite'
        if (-not (Test-Path -LiteralPath $transportDbPath)) {
            continue
        }
        $alreadyTracked = @($sessions | Where-Object {
            ([string](Get-OptionalProperty -Object $_ -Name 'state_dir')) -eq $candidateDir -and
            ([string](Get-OptionalProperty -Object $_ -Name 'control_method')) -eq 'runner-state'
        }).Count -gt 0
        if ($alreadyTracked) {
            continue
        }
        $sessions += [pscustomobject]@{
            session_key = "node-pty::$candidateDir"
            kind = 'node-pty'
            source = 'stop_tool fallback'
            status = 'discovered'
            control_method = 'runner-state'
            state_dir = $candidateDir
            state_path = $transportDbPath
            window_state_path = $transportDbPath
        }
    }

    return @($sessions)
}

function Get-StateDirSummary {
    param([Parameter(Mandatory = $true)][string]$StateDir)
    $browserPath = Join-Path $StateDir 'collaborative-browser-session.json'
    $session = Get-RegisteredSessionByStateDir -StateDir $StateDir
    $browser = Read-JsonFile -Path $browserPath
    $browserPort = Get-OptionalProperty -Object $browser -Name 'port'
    return [ordered]@{
        state_dir = $StateDir
        session_status = Get-OptionalProperty -Object $session -Name 'status'
        wrapper_pid = Get-OptionalProperty -Object $session -Name 'wrapper_pid'
        launcher_pid = Get-OptionalProperty -Object $session -Name 'launcher_pid'
        browser_status = Get-OptionalProperty -Object $browser -Name 'status'
        browser_port = if ($browserPort) { [int]$browserPort } else { $BrowserPort }
        visible_window_expected = Get-OptionalProperty -Object $session -Name 'visible_window_expected'
    }
}

function Stop-ProcessControlledSession {
    param(
        [Parameter(Mandatory = $true)]$Session,
        [Parameter(Mandatory = $true)]$VisitedProcessIds,
        [int]$TimeoutSeconds = 30
    )

    $sessionKey = [string](Get-OptionalProperty -Object $Session -Name 'session_key')
    $sessionKind = [string](Get-OptionalProperty -Object $Session -Name 'kind')
    $candidatePids = @()
    foreach ($name in @('wrapper_pid', 'launcher_pid', 'process_id')) {
        $value = Get-OptionalProperty -Object $Session -Name $name
        if ($value) {
            $candidatePids += [int]$value
        }
    }

    $pidResults = @()
    foreach ($trackedProcessId in ($candidatePids | Select-Object -Unique)) {
        if ($VisitedProcessIds.Contains($trackedProcessId)) {
            $pidResults += [ordered]@{
                process_id = $trackedProcessId
                status = 'already_processed'
            }
            continue
        }
        $null = $VisitedProcessIds.Add($trackedProcessId)
        $stopped = Stop-RecordedProcess -ProcessName "Project-controlled Copilot session ($sessionKind)" -ProcessId $trackedProcessId -TimeoutSeconds $TimeoutSeconds
        $pidResults += [ordered]@{
            process_id = $trackedProcessId
            status = if ($stopped) { 'stopped' } else { 'not_running' }
        }
    }

    if (@($pidResults).Count -eq 0) {
        $status = 'not_running'
    } else {
        $status = if (@($pidResults | Where-Object { $_.status -notin @('stopped', 'not_running', 'already_processed') }).Count -eq 0) { 'stopped' } else { 'blocked' }
    }
    if ($sessionKey -and $status -in @('stopped', 'not_running')) {
        Update-ProjectSessionRegistry -SessionKey $sessionKey -Status 'stopped'
    }
    return [ordered]@{
        session_key = $sessionKey
        kind = $sessionKind
        control_method = 'process-id'
        status = $status
        stopped_processes = $pidResults
    }
}

function Format-StopSummaryLines {
    param(
        [Parameter(Mandatory = $true)]$StateSummaries,
        [Parameter(Mandatory = $true)]$RunnerStops,
        [Parameter(Mandatory = $true)]$DirectSessionStops,
        [Parameter(Mandatory = $true)]$BackendStops,
        [Parameter(Mandatory = $true)]$HostRunnerStops,
        [Parameter(Mandatory = $true)][string]$FinalStatus,
        [Parameter(Mandatory = $true)][string]$StatePath
    )

    $lines = New-Object 'System.Collections.Generic.List[string]'
    $reportedPids = New-Object 'System.Collections.Generic.HashSet[int]'

    foreach ($summary in @($StateSummaries)) {
        if ($summary.wrapper_pid -and $reportedPids.Add([int]$summary.wrapper_pid)) {
            $lines.Add("PID $($summary.wrapper_pid) - avslutad (Copilot wrapper)")
        }
        if ($summary.launcher_pid -and $reportedPids.Add([int]$summary.launcher_pid)) {
            $lines.Add("PID $($summary.launcher_pid) - avslutad (Copilot launcher)")
        }
    }

    foreach ($sessionStop in @($DirectSessionStops)) {
        foreach ($pidResult in @((Get-OptionalProperty -Object $sessionStop -Name 'stopped_processes'))) {
            $processIdValue = Get-OptionalProperty -Object $pidResult -Name 'process_id'
            if (-not $processIdValue) {
                continue
            }
            if (-not $reportedPids.Add([int]$processIdValue)) {
                continue
            }
            $pidStatus = [string](Get-OptionalProperty -Object $pidResult -Name 'status')
            if ($pidStatus -eq 'stopped') {
                $lines.Add("PID $processIdValue - avslutad")
            } elseif ($pidStatus -eq 'not_running') {
                $lines.Add("PID $processIdValue - redan avslutad")
            }
        }
    }

    foreach ($backendStop in @($BackendStops)) {
        $processIdValue = Get-OptionalProperty -Object $backendStop -Name 'process_id'
        $ports = @((Get-OptionalProperty -Object $backendStop -Name 'local_ports'))
        $portText = if ($ports.Count -gt 0) { ($ports -join ', ') } else { [string]$BackendPort }
        if ($processIdValue) {
            $lines.Add("PID $processIdValue - avslutad (backend/webserver port $portText)")
        }
    }
    if (@($BackendStops).Count -eq 0 -or (@($BackendStops).Count -eq 1 -and [string](Get-OptionalProperty -Object $BackendStops[0] -Name 'status') -eq 'not_running')) {
        $lines.Add("Backend/webserver port $BackendPort - redan avslutad")
    }

    foreach ($hostRunnerStop in @($HostRunnerStops)) {
        $processIdValue = Get-OptionalProperty -Object $hostRunnerStop -Name 'process_id'
        $ports = @((Get-OptionalProperty -Object $hostRunnerStop -Name 'local_ports'))
        $portText = if ($ports.Count -gt 0) { ($ports -join ', ') } else { [string]$HostRunnerPort }
        if ($processIdValue) {
            $lines.Add("PID $processIdValue - avslutad (host-runner port $portText)")
        }
    }
    if (@($HostRunnerStops).Count -eq 0 -or (@($HostRunnerStops).Count -eq 1 -and [string](Get-OptionalProperty -Object $HostRunnerStops[0] -Name 'status') -eq 'not_running')) {
        $lines.Add("Host-runner port $HostRunnerPort - redan avslutad")
    }

    foreach ($runnerStop in @($RunnerStops)) {
        $browserResult = Get-OptionalProperty -Object $runnerStop -Name 'browser'
        if (-not $browserResult) {
            continue
        }
        $browserStatus = [string](Get-OptionalProperty -Object $browserResult -Name 'status')
        if ($browserStatus -ne 'not_owned') {
            continue
        }
        $browserSession = Get-OptionalProperty -Object $browserResult -Name 'browser_session'
        $portValue = Get-OptionalProperty -Object $browserSession -Name 'port'
        $portText = if ($portValue) { [string]$portValue } else { [string]$BrowserPort }
        $lines.Add("Browser port $portText - lämnad orörd (ingen ägd browserprocess registrerad)")
    }

    if ($FinalStatus -eq 'stopped') {
        $lines.Add('Alla processer associerade med projektet avslutade.')
    } else {
        $lines.Add("Vissa projektassocierade processer kunde inte avslutas. Se $StatePath för detaljer.")
    }
    $lines.Add('Skriptet avslutas.')
    return @($lines)
}

$previousState = Read-JsonFile -Path $statePath
$projectSessions = @(Get-ProjectControlledSessions)
$runnerStateDirs = @(
    $projectSessions |
        Where-Object { ([string](Get-OptionalProperty -Object $_ -Name 'control_method')) -eq 'runner-state' } |
        ForEach-Object { [string](Get-OptionalProperty -Object $_ -Name 'state_dir') } |
        Where-Object { $_ } |
        Select-Object -Unique
)
$stateSummaries = @(
    $runnerStateDirs |
        Where-Object { $_ -and ([string]$_).Trim() } |
        ForEach-Object { Get-StateDirSummary -StateDir ([string]$_) }
)
$processControlledSessions = @($projectSessions | Where-Object { ([string](Get-OptionalProperty -Object $_ -Name 'control_method')) -eq 'process-id' })

if ($DryRun) {
    [ordered]@{
        status = 'dry_run'
        backend_url = $backendUrl
        host_runner_url = $hostRunnerUrl
        browser_port = $BrowserPort
        timeout_seconds = $TimeoutSeconds
        state_path = $statePath
        registry_path = $registryPath
        project_sessions = $projectSessions
        runner_state_dirs = $stateSummaries
        backend_running = Test-JsonEndpoint "$backendUrl/api/health"
        host_runner_running = Test-JsonEndpoint "$hostRunnerUrl/health"
        would_stop_copilot_sessions = @($projectSessions)
        would_stop_backend_listener = [bool]@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object {
            $owner = Get-CimInstance Win32_Process -Filter "ProcessId=$($_.OwningProcess)" -ErrorAction SilentlyContinue
            $owner -and ([string]$owner.CommandLine).Contains('tools\source\copilot_admin_control_plane\backend\app.py')
        })
        would_stop_host_runner_listener = [bool]@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object {
            $owner = Get-CimInstance Win32_Process -Filter "ProcessId=$($_.OwningProcess)" -ErrorAction SilentlyContinue
            $owner -and ([string]$owner.CommandLine).Contains('tools\source\copilot_admin_runner\copilot_admin_runner.py')
        })
        previous_state = $previousState
    } | ConvertTo-Json -Depth 10
    Write-Host "Regression tool suite stop dry-run completed for: $backendUrl"
    exit 0
}

$runnerStops = @(
foreach ($summary in $stateSummaries) {
    [ordered]@{
        state_dir = $summary.state_dir
        copilot = Invoke-RunnerStop -Action 'copilot-stop' -StateDir $summary.state_dir -TimeoutSeconds $TimeoutSeconds
        browser = Invoke-RunnerStop -Action 'browser-stop' -StateDir $summary.state_dir -Port $summary.browser_port -TimeoutSeconds $TimeoutSeconds
    }
})
$visitedProcessIds = New-Object 'System.Collections.Generic.HashSet[int]'
$directSessionStops = @(
foreach ($session in $processControlledSessions) {
    Stop-ProcessControlledSession -Session $session -VisitedProcessIds $visitedProcessIds -TimeoutSeconds $TimeoutSeconds
})
$backendStops = @(Stop-CompatibleListenerProcesses -ExpectedCommandSubstring 'tools\source\copilot_admin_control_plane\backend\app.py' -ProcessName 'Copilot-admin backend' -TimeoutSeconds $TimeoutSeconds)
$hostRunnerStops = @(Stop-CompatibleListenerProcesses -ExpectedCommandSubstring 'tools\source\copilot_admin_runner\copilot_admin_runner.py' -ProcessName 'Copilot-admin host-runner' -TimeoutSeconds $TimeoutSeconds)

$status = 'stopped'
if (@($runnerStops | Where-Object { $_.copilot.status -notin @('stopped', 'not_running') }).Count -gt 0) {
    $status = 'blocked'
}
if (@($runnerStops | Where-Object { $_.browser.status -notin @('stopped', 'not_running', 'not_owned') }).Count -gt 0) {
    $status = 'blocked'
}
if (@($directSessionStops | Where-Object { $_.status -notin @('stopped', 'not_running') }).Count -gt 0) {
    $status = 'blocked'
}

$state = [ordered]@{
    previous_state = $previousState
}
$previousBrowserStatus = Get-OptionalProperty -Object $previousState -Name 'browser_status'
$previousUiUrl = Get-OptionalProperty -Object $previousState -Name 'ui_url'
$state.status = $status
$state.stopped_at = (Get-Date).ToUniversalTime().ToString('o')
$state.ui_url = $previousUiUrl
$state.backend_url = $backendUrl
$state.host_runner_url = $hostRunnerUrl
$state.browser_port = $BrowserPort
$state.session_job_status = 'stopped'
$state.copilot_status = 'not_running'
$state.browser_status = if (@($runnerStops | Where-Object { $_.browser.status -eq 'stopped' }).Count -gt 0) { 'not_running' } else { $previousBrowserStatus }
$state.stop_results = [ordered]@{
    project_sessions = $projectSessions
    runner_state_dirs = if (@($runnerStops).Count -gt 0) { $runnerStops } else { @([ordered]@{ status = 'not_running' }) }
    direct_sessions = if (@($directSessionStops).Count -gt 0) { $directSessionStops } else { @([ordered]@{ status = 'not_running' }) }
    backends = if (@($backendStops).Count -gt 0) { $backendStops } else { @([ordered]@{ status = 'not_running' }) }
    host_runners = if (@($hostRunnerStops).Count -gt 0) { $hostRunnerStops } else { @([ordered]@{ status = 'not_running' }) }
}

$null = New-Item -ItemType Directory -Path $stateDir -Force
$state | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $statePath -Encoding UTF8

$summaryLines = Format-StopSummaryLines -StateSummaries $stateSummaries -RunnerStops $runnerStops -DirectSessionStops $directSessionStops -BackendStops $backendStops -HostRunnerStops $hostRunnerStops -FinalStatus $status -StatePath $statePath
foreach ($line in $summaryLines) {
    Write-Host $line
}
