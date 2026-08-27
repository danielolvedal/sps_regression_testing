[CmdletBinding()]
param(
    [string]$HostName = "127.0.0.1",
    [int]$Port = 8765,
    [string]$HostRunnerUrl = ""
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
$env:SPS_REPO_ROOT = $repoRoot.Path
$env:COPILOT_ADMIN_FRONTEND_DIR = (Join-Path $repoRoot "tools\source\copilot_admin_control_plane\frontend")
$env:COPILOT_ADMIN_BACKEND_HOST = $HostName
$env:COPILOT_ADMIN_BACKEND_PORT = [string]$Port
if ($HostRunnerUrl) {
    $env:COPILOT_ADMIN_HOST_RUNNER_URL = $HostRunnerUrl
}
python (Join-Path $repoRoot "tools\source\copilot_admin_control_plane\backend\app.py") --host $HostName --port $Port
