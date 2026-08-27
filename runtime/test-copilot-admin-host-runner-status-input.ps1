Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path $PSScriptRoot 'windows\copilot-admin\host-runner\test-copilot-admin-host-runner-status-input.ps1'
& $scriptPath
