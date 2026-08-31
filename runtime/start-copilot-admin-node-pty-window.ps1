param(
    [switch]$LogInput,
    [switch]$RestartExisting,
    [int]$CloseTimeoutSeconds = 30,
    [string]$StartupModel = 'auto',
    [switch]$AllowAll = $true,
    [switch]$Hidden
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

& (Join-Path $PSScriptRoot 'windows\copilot-admin\node-pty\start-copilot-admin-node-pty-window.ps1') -LogInput:$LogInput -RestartExisting:$RestartExisting -CloseTimeoutSeconds $CloseTimeoutSeconds -StartupModel $StartupModel -AllowAll:$AllowAll -Hidden:$Hidden
