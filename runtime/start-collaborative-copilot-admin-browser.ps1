param(
    [string]$HostName = '127.0.0.1',
    [int]$BackendPort = 8765,
    [ValidateSet('auto', 'edge', 'chrome')]
    [string]$Browser = 'auto',
    [int]$BrowserPort = 9223,
    [string]$ProfileDir,
    [switch]$ReuseExisting = $true,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..\tools\source\browser_collaboration')) 'Start-CollaborativeCopilotAdminBrowserSession.ps1'
& $scriptPath -HostName $HostName -BackendPort $BackendPort -Browser $Browser -BrowserPort $BrowserPort -ProfileDir $ProfileDir -ReuseExisting:$ReuseExisting -DryRun:$DryRun
