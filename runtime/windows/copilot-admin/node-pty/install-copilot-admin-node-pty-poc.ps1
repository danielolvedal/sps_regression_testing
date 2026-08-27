Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$resolverPath = Join-Path $PSScriptRoot 'Resolve-NodePtyTooling.ps1'
. $resolverPath

try {
    $node = Resolve-NodePtyCommand -Name node
    $npm = Resolve-NodePtyCommand -Name npm
} catch {
    throw @"
npm was not found in PATH.

Install Node.js LTS first, then re-run this script.

Suggested command if winget is available:
  winget install OpenJS.NodeJS.LTS

After installation, open a new PowerShell window and run:
  cd <SPS-root>
  .\runtime\install-copilot-admin-node-pty-poc.ps1
"@
}

$nodeDir = Split-Path -Parent $node
$env:PATH = "$nodeDir;$env:PATH"

$packageDir = Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\tools\source\copilot_admin_runner\node_pty_poc')
Push-Location $packageDir
try {
    & $npm install
    if ($LASTEXITCODE -ne 0) {
        throw "npm install failed with exit code $LASTEXITCODE."
    }
} finally {
    Pop-Location
}
