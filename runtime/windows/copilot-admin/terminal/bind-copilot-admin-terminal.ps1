param(
    [int]$CountdownSeconds = 8,
    [switch]$DryRun,
    [string]$StatePath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\tools\source\copilot_admin_runner')) 'Bind-CopilotTerminalWindow.ps1'
$arguments = @(
    '-NoProfile',
    '-ExecutionPolicy', 'Bypass',
    '-File', $scriptPath,
    '-CountdownSeconds', $CountdownSeconds
)
if ($DryRun) {
    $arguments += '-DryRun'
}
if ($StatePath) {
    $arguments += @('-StatePath', $StatePath)
}
powershell @arguments
