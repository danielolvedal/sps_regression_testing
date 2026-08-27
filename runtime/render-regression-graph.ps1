Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

& (Join-Path $PSScriptRoot 'windows\copilot-admin\bridge\render-regression-graph.ps1')
