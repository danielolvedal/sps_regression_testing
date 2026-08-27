param(
    [switch]$LogInput,
    [string]$StartupModel = 'gpt-5-mini',
    [switch]$AllowAll = $true
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'Resolve-NodePtyTooling.ps1')
$node = Resolve-NodePtyCommand -Name node
$env:COPILOT_CLI_PATH = Resolve-CopilotCliCommand
$packageDir = Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\tools\source\copilot_admin_runner\node_pty_poc')
$scriptPath = Join-Path $packageDir 'node_pty_poc.mjs'
if (-not (Test-Path (Join-Path $packageDir 'node_modules\node-pty'))) {
    throw "node-pty is not installed. Run .\runtime\windows\copilot-admin\node-pty\install-copilot-admin-node-pty-poc.ps1 first."
}
$arguments = @($scriptPath, 'interactive-copilot')
if ($LogInput) {
    $arguments += '--log-input'
}
if ($StartupModel) {
    $arguments += @('--startup-model', $StartupModel)
}
if ($AllowAll) {
    $arguments += '--allow-all'
}
& $node @arguments
