param(
    [Parameter(Mandatory = $true)]
    [string]$Text,
    [switch]$ClearLine,
    [switch]$NoSubmit,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

& (Join-Path $PSScriptRoot 'windows\copilot-admin\node-pty\send-copilot-admin-node-pty-input.ps1') -Text $Text -ClearLine:$ClearLine -NoSubmit:$NoSubmit -DryRun:$DryRun
