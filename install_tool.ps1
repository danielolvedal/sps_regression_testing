param(
    [switch]$PreflightOnly,
    [switch]$SkipWinget
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

& (Join-Path $PSScriptRoot 'runtime\install_tool.ps1') -PreflightOnly:$PreflightOnly -SkipWinget:$SkipWinget
