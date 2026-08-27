param(
    [int]$CountdownSeconds = 8,
    [switch]$DryRun,
    [string]$StatePath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$arguments = @{
    CountdownSeconds = $CountdownSeconds
}
if ($DryRun) {
    $arguments.DryRun = $true
}
if ($StatePath) {
    $arguments.StatePath = $StatePath
}
& (Join-Path $PSScriptRoot 'windows\copilot-admin\terminal\bind-copilot-admin-terminal.ps1') @arguments
