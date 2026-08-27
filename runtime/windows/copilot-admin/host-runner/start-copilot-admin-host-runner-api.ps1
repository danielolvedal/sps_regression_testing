param(
    [string]$HostAddress = '127.0.0.1',
    [int]$Port = 8766
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')
$runner = Join-Path $repoRoot 'tools\source\copilot_admin_runner\copilot_admin_runner.py'

python $runner http-server --host $HostAddress --port $Port
