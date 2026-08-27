[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$productionQueue = Join-Path $repoRoot 'tmp\copilot_admin_runner_state\node-pty-copilot-input-queue'
$before = @()
if (Test-Path -LiteralPath $productionQueue) {
    $before = @(Get-ChildItem -LiteralPath $productionQueue -File | Select-Object -ExpandProperty Name)
}

$previousEnv = $env:COPILOT_ADMIN_ENV
$env:COPILOT_ADMIN_ENV = 'test'
try {
    python -m unittest tools.source.copilot_admin_control_plane.backend.test_app
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    & (Join-Path $repoRoot 'runtime\docker\copilot-admin\test-e2e-dev.ps1')
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    $realDryRun = & (Join-Path $repoRoot 'runtime\docker\copilot-admin\test-real-visible-e2e.ps1') -DryRun | ConvertFrom-Json
    if (-not [bool]$realDryRun.would_start_visible_isolated_copilot) {
        throw 'Real E2E dry-run must declare that it starts a visible isolated Copilot session.'
    }
    if (-not [string]$realDryRun.isolated_runner_state_dir) {
        throw 'Real E2E dry-run must expose an isolated runner state directory.'
    }
    if (-not ([string]$realDryRun.isolated_runner_state_dir).Contains('tmp\copilot_admin_control_plane\real_visible_e2e\runner_state')) {
        throw "Real E2E isolated state directory is unexpected: $($realDryRun.isolated_runner_state_dir)"
    }

    $after = @()
    if (Test-Path -LiteralPath $productionQueue) {
        $after = @(Get-ChildItem -LiteralPath $productionQueue -File | Select-Object -ExpandProperty Name)
    }
    $newProductionQueueFiles = @($after | Where-Object { $before -notcontains $_ })
    if ($newProductionQueueFiles.Count -gt 0) {
        throw "Test isolation failed: validation wrote to production Copilot input queue: $($newProductionQueueFiles -join ', ')"
    }

    [ordered]@{
        status = 'passed'
        production_queue = $productionQueue
        production_queue_new_file_count = $newProductionQueueFiles.Count
        real_e2e_visible_copilot = [bool]$realDryRun.would_start_visible_isolated_copilot
        real_e2e_isolated_state_dir = [string]$realDryRun.isolated_runner_state_dir
        real_e2e_browser_port = [int]$realDryRun.browser_port
    } | ConvertTo-Json -Depth 10
} finally {
    if ($null -eq $previousEnv) {
        Remove-Item Env:\COPILOT_ADMIN_ENV -ErrorAction SilentlyContinue
    } else {
        $env:COPILOT_ADMIN_ENV = $previousEnv
    }
}
