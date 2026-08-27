param(
    [Parameter(Mandatory = $true)]
    [string]$Prompt,
    [int]$CountdownSeconds = 8,
    [switch]$Submit,
    [switch]$Arm,
    [switch]$DryRun,
    [switch]$PreserveExistingInput,
    [switch]$UseBoundWindow,
    [ValidateSet('ForegroundSendKeys', 'BackgroundPostMessage')]
    [string]$DeliveryMode = 'ForegroundSendKeys',
    [string]$BoundWindowPath,
    [string]$Bridge = 'manual',
    [string]$VerificationId
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\tools\source\copilot_admin_runner')) 'Invoke-TerminalInputAdapter.ps1'
$arguments = @(
    '-NoProfile',
    '-ExecutionPolicy', 'Bypass',
    '-File', $scriptPath,
    '-Prompt', $Prompt,
    '-CountdownSeconds', $CountdownSeconds,
    '-DeliveryMode', $DeliveryMode,
    '-Bridge', $Bridge
)
if ($VerificationId) {
    $arguments += @('-VerificationId', $VerificationId)
}
if ($Submit) {
    $arguments += '-Submit'
}
if ($Arm) {
    $arguments += '-Arm'
}
if ($DryRun) {
    $arguments += '-DryRun'
}
if ($PreserveExistingInput) {
    $arguments += '-PreserveExistingInput'
}
if ($UseBoundWindow) {
    $arguments += '-UseBoundWindow'
}
if ($BoundWindowPath) {
    $arguments += @('-BoundWindowPath', $BoundWindowPath)
}
powershell @arguments
