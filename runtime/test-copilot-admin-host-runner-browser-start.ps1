param(
    [int]$Port = 9222
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path $PSScriptRoot 'windows\copilot-admin\host-runner\test-copilot-admin-host-runner-browser-start.ps1'
& $scriptPath -Port $Port
