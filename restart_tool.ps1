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
    [int]$StopTimeoutSeconds = 30,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = $PSScriptRoot
$stopScript = Join-Path $repoRoot 'stop_tool.ps1'
$startScript = Join-Path $repoRoot 'start_tool.ps1'
$statePath = Join-Path $repoRoot 'tmp\copilot_admin_control_plane\start_tool\latest.json'

function Read-JsonFile {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Could not find state file: $Path"
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

# Ensure tool_error_logs exists and export for child scripts to inherit
$logsDir = Join-Path $repoRoot 'tool_error_logs'
if (-not (Test-Path $logsDir)) { New-Item -Path $logsDir -ItemType Directory -Force | Out-Null }
$env:TOOL_ERROR_LOG_DIR = $logsDir

$stopArguments = @{
    HostName = $HostName
    BackendPort = $BackendPort
    HostRunnerPort = $HostRunnerPort
    BrowserPort = $BrowserPort
    TimeoutSeconds = $StopTimeoutSeconds
    DryRun = $DryRun
}

& $stopScript @stopArguments

if ($DryRun) {
    $startDryRunArguments = @{
        HostName = $HostName
        BackendPort = $BackendPort
        HostRunnerPort = $HostRunnerPort
        BrowserPort = $BrowserPort
        StartupModel = $StartupModel
        StartCopilotSession = $StartCopilotSession
        RestartExisting = $RestartExisting
        HideCopilotWindow = $HideCopilotWindow
        OpenUiInSharedBrowser = $OpenUiInSharedBrowser
        DryRun = $true
    }
    & $startScript @startDryRunArguments
        # Remove inherited env var in dry-run path
        Remove-Item Env:\TOOL_ERROR_LOG_DIR -ErrorAction SilentlyContinue
        exit 0
    }

    $stopState = Read-JsonFile -Path $statePath
$stopStatus = [string](Get-OptionalProperty -Object $stopState -Name 'status')
if ($stopStatus -ne 'stopped') {
    throw "restart_tool.ps1 aborted because stop_tool.ps1 did not finish cleanly. Reported status: $stopStatus. See $statePath for details."
}

$startArguments = @{
    HostName = $HostName
    BackendPort = $BackendPort
    HostRunnerPort = $HostRunnerPort
    BrowserPort = $BrowserPort
    StartupModel = $StartupModel
    StartCopilotSession = $StartCopilotSession
    RestartExisting = $RestartExisting
    HideCopilotWindow = $HideCopilotWindow
    OpenUiInSharedBrowser = $OpenUiInSharedBrowser
    DryRun = $false
}

Write-Host 'Regression tool suite starting - please wait'
& $startScript @startArguments
# Clean up TOOL_ERROR_LOG_DIR from environment after restart sequence
Remove-Item Env:\TOOL_ERROR_LOG_DIR -ErrorAction SilentlyContinue
