param(
    [string]$PipeName = 'sps-copilot-admin-runner',
    [string]$VerificationId = "pipe-level2-$((Get-Date).ToString('yyyyMMdd-HHmmss'))",
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
$response = & (Join-Path $bridgeDir 'invoke-copilot-admin-pipe-request.ps1') -Action command-template -CommandId verify-bridge-session -VerificationId $VerificationId -PipeName $PipeName | ConvertFrom-Json

$terminalParams = @{
    Prompt = $response.prompt
    CountdownSeconds = $CountdownSeconds
    Bridge = 'named-pipe'
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
& (Join-Path $PSScriptRoot 'invoke-copilot-admin-terminal-input.ps1') @terminalParams
