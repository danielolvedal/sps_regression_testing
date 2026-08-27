param(
    [Parameter(Mandatory = $true)]
    [string]$Text,
    [switch]$NoSubmit
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

& (Join-Path $PSScriptRoot 'windows\copilot-admin\node-pty\send-copilot-admin-node-pty-input.ps1') -Text $Text -NoSubmit:$NoSubmit
