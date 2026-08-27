param(
    [switch]$PreflightOnly,
    [switch]$SkipWinget
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

& (Join-Path $PSScriptRoot 'windows\copilot-admin\install_tool.ps1') -PreflightOnly:$PreflightOnly -SkipWinget:$SkipWinget
