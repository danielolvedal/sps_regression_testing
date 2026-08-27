param(
    [string]$Title = 'SPS Copilot Admin Runner Owned Session',
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\tools\source\copilot_admin_runner')) 'Start-OwnedCopilotSessionPoc.ps1'
$arguments = @(
    '-NoProfile',
    '-ExecutionPolicy', 'Bypass',
    '-File', $scriptPath,
    '-Mode', 'VisibleTerminal',
    '-Title', $Title
)
if ($DryRun) {
    $arguments += '-DryRun'
}
powershell @arguments
