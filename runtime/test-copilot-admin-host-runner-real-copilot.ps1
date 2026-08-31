param(
    [switch]$RestartExisting,
    [switch]$LogInput,
    [string]$StartupModel = 'auto',
    [switch]$AllowAll = $true,
    [int]$StartupTimeoutSeconds = 45,
    [int]$StopTimeoutSeconds = 20
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path $PSScriptRoot 'windows\copilot-admin\host-runner\test-copilot-admin-host-runner-real-copilot.ps1'
& $scriptPath -RestartExisting:$RestartExisting -LogInput:$LogInput -StartupModel $StartupModel -AllowAll:$AllowAll -StartupTimeoutSeconds $StartupTimeoutSeconds -StopTimeoutSeconds $StopTimeoutSeconds
