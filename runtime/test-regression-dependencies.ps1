Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..\tools\source\document_index_validation')) 'validate_regression_dependencies.py'
python $scriptPath
