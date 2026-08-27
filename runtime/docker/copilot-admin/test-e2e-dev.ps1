[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
$env:SPS_REPO_ROOT = $repoRoot.Path
$env:COPILOT_ADMIN_ENV = "test"
python -m unittest (Join-Path $repoRoot "tools\source\copilot_admin_control_plane\e2e\test_control_plane_dev_e2e.py")
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
python -m unittest (Join-Path $repoRoot "tools\source\copilot_admin_control_plane\e2e\test_frontend_browser_e2e.py")
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
