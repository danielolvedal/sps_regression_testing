Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..\tools\source\documentation_generation')) 'generate_kundtjanst_function_doc.py'
python $scriptPath
