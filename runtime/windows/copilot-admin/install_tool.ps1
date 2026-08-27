param(
    [switch]$PreflightOnly,
    [switch]$SkipWinget
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\tools\source\copilot_admin_runner')) 'Install-StartToolDependencies.ps1'
& $scriptPath -PreflightOnly:$PreflightOnly -SkipWinget:$SkipWinget
