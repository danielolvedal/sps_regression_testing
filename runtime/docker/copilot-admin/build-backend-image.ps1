[CmdletBinding()]
param(
    [string]$ImageName = "sps-copilot-admin-backend",
    [int]$Port = 8765
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
docker build -f (Join-Path $repoRoot "tools\source\copilot_admin_control_plane\backend\Dockerfile") -t $ImageName $repoRoot
Write-Host "Run the UI/API layer with repository mounted at /workspace:"
Write-Host "docker run --rm -p ${Port}:8765 -v ${repoRoot}:/workspace $ImageName"
