param(
    [Parameter(Mandatory = $true)]
    [string]$Action,
    [string]$Text,
    [switch]$NoSubmit,
    [switch]$DryRun,
    [switch]$RestartExisting,
    [switch]$LogInput,
    [string]$StartupModel = 'auto',
    [switch]$AllowAll = $true,
    [switch]$HiddenWindow,
    [int]$Port = 9222,
    [int]$TimeoutSeconds = 30
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path $PSScriptRoot 'windows\copilot-admin\host-runner\invoke-copilot-admin-host-runner.ps1'
$arguments = @{
    Action = $Action
    Port = $Port
    TimeoutSeconds = $TimeoutSeconds
}
if ($Text) { $arguments.Text = $Text }
if ($NoSubmit) { $arguments.NoSubmit = $true }
if ($DryRun) { $arguments.DryRun = $true }
if ($RestartExisting) { $arguments.RestartExisting = $true }
if ($LogInput) { $arguments.LogInput = $true }
if ($StartupModel) { $arguments.StartupModel = $StartupModel }
if ($AllowAll) { $arguments.AllowAll = $true }
if ($HiddenWindow) { $arguments.HiddenWindow = $true }

& $scriptPath @arguments
