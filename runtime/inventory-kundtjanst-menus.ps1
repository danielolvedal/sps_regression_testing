param(
    [int]$Port = 9222,
    [switch]$IncludeExternal
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..\tools\source\browser_collaboration')) 'Invoke-KundtjanstMenuInventory.ps1'
& $scriptPath -BaseUrl 'https://sps-stage.europark.local/CustomerService' -Port $Port -IncludeExternal:$IncludeExternal
