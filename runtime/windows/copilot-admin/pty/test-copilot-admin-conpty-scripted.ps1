param(
    [string]$Command = 'cmd.exe',
    [string[]]$Arguments = @('/d', '/c', 'echo conpty-scripted-ok'),
    [string[]]$SendLine = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\tools\source\copilot_admin_runner')) 'owned_copilot_pty.py'
$cmd = @($scriptPath, 'scripted')
foreach ($line in $SendLine) {
    $cmd += @('--send-line', $line)
}
$cmd += @('--', $Command)
$cmd += $Arguments
python @cmd
