param(
    [int]$Port = 9222,
    [switch]$ReuseExisting = $true
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..\tools\source\browser_collaboration')) 'Start-CollaborativeBrowserSession.ps1'
& $scriptPath -Url 'https://sps-stage.europark.local/CustomerService' -Port $Port -ReuseExisting:$ReuseExisting
