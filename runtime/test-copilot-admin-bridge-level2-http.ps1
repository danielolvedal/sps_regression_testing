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

$arguments = @{
    RunnerUrl = $RunnerUrl
    VerificationId = $VerificationId
    CountdownSeconds = $CountdownSeconds
}
foreach ($switchName in @('Submit', 'Arm', 'DryRun', 'PreserveExistingInput', 'UseForegroundWindow', 'BackgroundWindow')) {
    if (Get-Variable -Name $switchName -ValueOnly) {
        $arguments[$switchName] = $true
    }
}
& (Join-Path $PSScriptRoot 'windows\copilot-admin\terminal\test-copilot-admin-bridge-level2-http.ps1') @arguments
