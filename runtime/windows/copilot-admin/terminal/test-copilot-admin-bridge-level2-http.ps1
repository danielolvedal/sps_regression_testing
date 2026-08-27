param(
    [string]$RunnerUrl = 'http://127.0.0.1:8765',
    [string]$VerificationId = "http-level2-$((Get-Date).ToString('yyyyMMdd-HHmmss'))",
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

$encodedId = [uri]::EscapeDataString($VerificationId)
$response = Invoke-WebRequest -UseBasicParsing "$RunnerUrl/commands/verify-bridge-session?verification_id=$encodedId" | ConvertFrom-Json

$terminalParams = @{
    Prompt = $response.prompt
    CountdownSeconds = $CountdownSeconds
    Bridge = 'http-api'
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
