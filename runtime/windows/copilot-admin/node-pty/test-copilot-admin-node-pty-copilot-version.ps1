Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'Resolve-NodePtyTooling.ps1')
$node = Resolve-NodePtyCommand -Name node
$copilot = Resolve-CopilotCliCommand
$packageDir = Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\tools\source\copilot_admin_runner\node_pty_poc')
$scriptPath = Join-Path $packageDir 'node_pty_poc.mjs'
if (-not (Test-Path (Join-Path $packageDir 'node_modules\node-pty'))) {
    throw "node-pty is not installed. Run .\runtime\windows\copilot-admin\node-pty\install-copilot-admin-node-pty-poc.ps1 first."
}
& $node $scriptPath scripted -- $copilot --version
