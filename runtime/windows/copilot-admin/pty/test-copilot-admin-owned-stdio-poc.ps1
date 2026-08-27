param(
    [int]$TimeoutSeconds = 20
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\tools\source\copilot_admin_runner')) 'Start-OwnedCopilotSessionPoc.ps1'
powershell -NoProfile -ExecutionPolicy Bypass -File $scriptPath -Mode RedirectedVersionProbe -TimeoutSeconds $TimeoutSeconds
