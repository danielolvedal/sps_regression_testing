param(
    [switch]$PreflightOnly,
    [switch]$SkipWinget
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$runnerDir = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\tools\source\copilot_admin_runner') | Select-Object -First 1).Path
$scriptPath = Join-Path $runnerDir 'Install-StartToolDependencies.ps1'
& $scriptPath -PreflightOnly:$PreflightOnly -SkipWinget:$SkipWinget
