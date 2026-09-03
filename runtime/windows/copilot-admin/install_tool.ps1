param(
    [switch]$PreflightOnly,
    [switch]$SkipWinget
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$runnerJoin = Join-Path $PSScriptRoot '..\..\..\tools\source\copilot_admin_runner'
$runnerDir = (Resolve-Path $runnerJoin | Select-Object -First 1).Path
$scriptPath = Join-Path $runnerDir 'Install-StartToolDependencies.ps1'

# Always run a preflight first to collect diagnostics
try {
    Write-Host 'Running preflight checks...'
    & $scriptPath -PreflightOnly:$true -SkipWinget:$SkipWinget
} catch {
    Write-Warning 'Preflight script reported errors; check tool_error_logs for details.'
}

# Show where the machine-readable report is saved and ask permission to continue
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..') | Select-Object -First 1).Path
$reportPath = Join-Path $repoRoot 'tool_error_logs\install_report.json'
$summaryPath = Join-Path $repoRoot 'tool_error_logs\install_action_summary.log'
if (Test-Path $reportPath) { Write-Host "Preflight report: $reportPath" }

if ($PreflightOnly) { Write-Host 'Preflight-only requested; not installing dependencies.'; return }

$answer = Read-Host 'Install missing dependencies now? (Y/N)'
if ($answer -notin @('Y','y','Yes','yes')) { Write-Host 'Aborting installation by user request.'; return }

# User approved — run the installer to attempt to install missing dependencies.
try {
    & $scriptPath -PreflightOnly:$false -SkipWinget:$SkipWinget
    if (Test-Path $summaryPath) { Write-Host "Install action summary: $summaryPath" }
    if (Test-Path $reportPath) { Write-Host "Final report: $reportPath" }
} catch {
    Write-Warning "Installer encountered an unexpected error: $($_.Exception.Message)"
    Write-Host "Check logs: $reportPath and $summaryPath"
}
