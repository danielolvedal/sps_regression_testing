param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('health', 'status', 'graph', 'commands', 'command-template')]
    [string]$Action,
    [string]$PipeName = 'sps-copilot-admin-runner',
    [string]$CommandId,
    [string]$CatalogKey,
    [string]$VerificationId
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\tools\source\copilot_admin_runner')) 'copilot_admin_runner.py'
$arguments = @($scriptPath, 'pipe-request', '--action', $Action, '--pipe-name', $PipeName)
if ($CommandId) {
    $arguments += @('--command-id', $CommandId)
}
if ($CatalogKey) {
    $arguments += @('--catalog-key', $CatalogKey)
}
if ($VerificationId) {
    $arguments += @('--verification-id', $VerificationId)
}
python @arguments
