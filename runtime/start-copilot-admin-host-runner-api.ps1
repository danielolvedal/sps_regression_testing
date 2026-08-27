param(
    [string]$HostAddress = '127.0.0.1',
    [int]$Port = 8766
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

& (Join-Path $PSScriptRoot 'windows\copilot-admin\host-runner\start-copilot-admin-host-runner-api.ps1') -HostAddress $HostAddress -Port $Port
