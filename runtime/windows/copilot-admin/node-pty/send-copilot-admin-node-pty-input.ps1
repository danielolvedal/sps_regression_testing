param(
    [Parameter(Mandatory = $true)]
    [string]$Text,
    [switch]$ClearLine,
    [switch]$NoSubmit,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')
$stateDir = if ($env:COPILOT_ADMIN_RUNNER_STATE_DIR) { $env:COPILOT_ADMIN_RUNNER_STATE_DIR } else { Join-Path $repoRoot 'tmp\copilot_admin_runner_state' }
$runner = Join-Path $repoRoot 'tools\source\copilot_admin_runner\copilot_admin_runner.py'
$arguments = @($runner, 'copilot-input', '--text', $Text)
if ($NoSubmit) { $arguments += '--no-submit' }
if ($ClearLine) { $arguments += '--clear-line' }
if ($DryRun) { $arguments += '--dry-run' }
python @arguments
