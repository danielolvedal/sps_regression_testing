param(
    [Parameter(Mandatory = $true)]
    [string]$CommandId,
    [string]$CatalogKey,
    [string]$VerificationId,
    [string]$QueueDir
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\tools\source\copilot_admin_runner')) 'copilot_admin_runner.py'
$arguments = @($scriptPath, 'filequeue-submit', '--command-id', $CommandId)
if ($CatalogKey) {
    $arguments += @('--catalog-key', $CatalogKey)
}
if ($VerificationId) {
    $arguments += @('--verification-id', $VerificationId)
}
if ($QueueDir) {
    $arguments += @('--queue-dir', $QueueDir)
}
python @arguments
