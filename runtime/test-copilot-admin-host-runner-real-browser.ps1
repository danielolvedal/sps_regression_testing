param(
    [int]$Port = 9322,
    [int]$StartupTimeoutSeconds = 30,
    [int]$StopTimeoutSeconds = 20
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path $PSScriptRoot 'windows\copilot-admin\host-runner\test-copilot-admin-host-runner-real-browser.ps1'
& $scriptPath -Port $Port -StartupTimeoutSeconds $StartupTimeoutSeconds -StopTimeoutSeconds $StopTimeoutSeconds
