param(
    [string]$HostAddress = '127.0.0.1',
    [int]$Port = 8765
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\tools\source\copilot_admin_runner')) 'copilot_admin_runner.py'
python $scriptPath http-server --host $HostAddress --port $Port
