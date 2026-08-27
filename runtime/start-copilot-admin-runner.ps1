param(
    [string]$HostAddress = '127.0.0.1',
    [int]$Port = 8765
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

& (Join-Path $PSScriptRoot 'windows\copilot-admin\bridge\start-copilot-admin-runner.ps1') -HostAddress $HostAddress -Port $Port
