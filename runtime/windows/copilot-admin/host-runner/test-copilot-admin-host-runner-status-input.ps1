Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')
$runner = Join-Path $repoRoot 'tools\source\copilot_admin_runner\copilot_admin_runner.py'

$status = python $runner copilot-status | ConvertFrom-Json
if (-not $status.state_path) {
    throw 'copilot-status did not return a state_path.'
}
if (-not $status.input_queue) {
    throw 'copilot-status did not return input_queue status.'
}

$input = python $runner copilot-input --text 'copilot-admin-host-runner-smoke' --no-submit --dry-run | ConvertFrom-Json
if ($input.status -ne 'dry_run') {
    throw "Expected dry_run input status, got '$($input.status)'."
}
if (-not $input.input.input_id) {
    throw 'Dry-run input did not return an input_id.'
}
if ($input.input.input_path) {
    throw 'Dry-run input unexpectedly wrote a queue file.'
}

[ordered]@{
    status = 'passed'
    copilot_session_status = $status.status
    input_status = $input.status
    checked_at = (Get-Date).ToUniversalTime().ToString('o')
} | ConvertTo-Json -Depth 10
