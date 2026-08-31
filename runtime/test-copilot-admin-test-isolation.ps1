[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$productionQueue = Join-Path $repoRoot 'tmp\copilot_admin_runner_state\node-pty-copilot-input-queue'
$productionDb = Join-Path $repoRoot 'tmp\copilot_admin_runner_state\copilot-admin-transport.sqlite'
$countQueueEntriesScript = @'
import sqlite3
import sys

conn = sqlite3.connect(sys.argv[1])
cur = conn.execute("select count(*) from input_queue where status in ('queued', 'claimed', 'sent')")
print(cur.fetchone()[0])
conn.close()
'@
$before = 0
if (Test-Path -LiteralPath $productionDb) {
    $before = [int](& python -c $countQueueEntriesScript $productionDb)
}

$previousEnv = $env:COPILOT_ADMIN_ENV
$env:COPILOT_ADMIN_ENV = 'test'
try {
    python -m unittest tools.source.copilot_admin_control_plane.backend.test_app
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    & (Join-Path $repoRoot 'runtime\docker\copilot-admin\test-e2e-dev.ps1')
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    $realDryRun = & (Join-Path $repoRoot 'runtime\docker\copilot-admin\test-real-visible-e2e.ps1') -DryRun | ConvertFrom-Json
    if (-not [bool]$realDryRun.would_start_hidden_isolated_copilot_helper) {
        throw 'Real E2E dry-run must declare that it starts a hidden isolated Copilot helper.'
    }
    if (-not [bool]$realDryRun.would_keep_collaborative_browser_visible) {
        throw 'Real E2E dry-run must keep the collaborative browser visible.'
    }
    if (-not [string]$realDryRun.isolated_runner_state_dir) {
        throw 'Real E2E dry-run must expose an isolated runner state directory.'
    }
    if (-not ([string]$realDryRun.isolated_runner_state_dir).Contains('tmp\copilot_admin_control_plane\real_visible_e2e\runner_state')) {
        throw "Real E2E isolated state directory is unexpected: $($realDryRun.isolated_runner_state_dir)"
    }

    $after = 0
    if (Test-Path -LiteralPath $productionDb) {
        $after = [int](& python -c $countQueueEntriesScript $productionDb)
    }
    $newProductionQueueEntries = [int]$after - [int]$before
    if ($newProductionQueueEntries -gt 0) {
        throw "Test isolation failed: validation wrote to production Copilot input queue database: $productionDb"
    }

    [ordered]@{
        status = 'passed'
        production_queue = $productionQueue
        production_queue_db = $productionDb
        production_queue_new_entry_count = $newProductionQueueEntries
        real_e2e_hidden_copilot_helper = [bool]$realDryRun.would_start_hidden_isolated_copilot_helper
        real_e2e_collaborative_browser_visible = [bool]$realDryRun.would_keep_collaborative_browser_visible
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
