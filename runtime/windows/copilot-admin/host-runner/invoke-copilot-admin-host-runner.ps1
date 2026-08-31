param(
    [Parameter(Mandatory = $true)]
    [ValidateSet(
        'status',
        'copilot-status',
        'copilot-start',
        'copilot-stop',
        'copilot-input',
        'browser-status',
        'browser-start',
        'browser-stop',
        'session-start',
        'session-stop'
    )]
    [string]$Action,
    [string]$Text,
    [switch]$NoSubmit,
    [switch]$DryRun,
    [switch]$RestartExisting,
    [switch]$LogInput,
    [string]$StartupModel = 'auto',
    [switch]$AllowAll = $true,
    [switch]$HiddenWindow,
    [int]$Port = 9222,
    [int]$TimeoutSeconds = 30
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')
$runner = Join-Path $repoRoot 'tools\source\copilot_admin_runner\copilot_admin_runner.py'
$arguments = @($runner, $Action)

switch ($Action) {
    'copilot-start' {
        if ($RestartExisting) { $arguments += '--restart-existing' }
        if ($LogInput) { $arguments += '--log-input' }
        if ($StartupModel) { $arguments += @('--startup-model', $StartupModel) }
        if (-not $AllowAll) { $arguments += '--no-allow-all' }
        if ($HiddenWindow) { $arguments += '--hidden-window' }
    }
    'copilot-stop' {
        $arguments += @('--timeout-seconds', $TimeoutSeconds)
    }
    'copilot-input' {
        if (-not $Text) {
            throw '-Text is required for copilot-input.'
        }
        $arguments += @('--text', $Text)
        if ($NoSubmit) { $arguments += '--no-submit' }
        if ($DryRun) { $arguments += '--dry-run' }
    }
    'browser-status' {
        $arguments += @('--port', $Port)
    }
    'browser-start' {
        $arguments += @('--port', $Port)
        if ($DryRun) { $arguments += '--dry-run' }
    }
    'browser-stop' {
        $arguments += @('--port', $Port, '--timeout-seconds', $TimeoutSeconds)
    }
    'session-start' {
        $arguments += @('--port', $Port)
        if ($RestartExisting) { $arguments += '--restart-existing' }
        if ($LogInput) { $arguments += '--log-input' }
        if ($StartupModel) { $arguments += @('--startup-model', $StartupModel) }
        if (-not $AllowAll) { $arguments += '--no-allow-all' }
        if ($HiddenWindow) { $arguments += '--hidden-window' }
        if ($DryRun) { $arguments += '--dry-run' }
    }
    'session-stop' {
        $arguments += @('--port', $Port, '--timeout-seconds', $TimeoutSeconds)
    }
}

python @arguments
