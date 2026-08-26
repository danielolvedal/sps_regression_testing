param(
    [Parameter(Mandatory = $true)]
    [string]$Url,
    [int]$Port = 9222,
    [string]$SourcePageUrlPrefix = 'https://sps-stage.europark.local/'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..\tools\source\browser_collaboration')) 'Open-SharedBrowserTab.ps1'
& $scriptPath -Url $Url -Port $Port -SourcePageUrlPrefix $SourcePageUrlPrefix
