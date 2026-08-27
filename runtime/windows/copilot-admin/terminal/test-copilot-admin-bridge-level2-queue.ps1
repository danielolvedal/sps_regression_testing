param(
    [string]$VerificationId = "queue-level2-$((Get-Date).ToString('yyyyMMdd-HHmmss'))",
    [int]$CountdownSeconds = 8,
    [switch]$Submit,
    [switch]$Arm,
    [switch]$DryRun,
    [switch]$PreserveExistingInput,
    [switch]$UseForegroundWindow,
    [switch]$BackgroundWindow
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$bridgeDir = Resolve-Path (Join-Path $PSScriptRoot '..\bridge')
$submitResult = & (Join-Path $bridgeDir 'submit-copilot-admin-queue-job.ps1') -CommandId verify-bridge-session -VerificationId $VerificationId | ConvertFrom-Json
$processResult = & (Join-Path $bridgeDir 'process-copilot-admin-queue-once.ps1') | ConvertFrom-Json
$queueResult = Get-Content $processResult.result_path -Raw | ConvertFrom-Json
$prompt = $queueResult.command_payload.prompt

$terminalParams = @{
    Prompt = $prompt
    CountdownSeconds = $CountdownSeconds
    Bridge = 'file-queue'
    VerificationId = $VerificationId
}
if ($BackgroundWindow) {
    $terminalParams.DeliveryMode = 'BackgroundPostMessage'
}
if ($Submit) {
    $terminalParams.Submit = $true
}
if ($Arm) {
    $terminalParams.Arm = $true
}
if ($DryRun) {
    $terminalParams.DryRun = $true
}
if ($PreserveExistingInput) {
    $terminalParams.PreserveExistingInput = $true
}
if (-not $UseForegroundWindow) {
    $terminalParams.UseBoundWindow = $true
}
$terminalResult = & (Join-Path $PSScriptRoot 'invoke-copilot-admin-terminal-input.ps1') @terminalParams | ConvertFrom-Json
[ordered]@{
    submit_result = $submitResult
    process_result = $processResult
    terminal_input_result = $terminalResult
} | ConvertTo-Json -Depth 20
