param(
    [int]$CountdownSeconds = 8,
    [switch]$DryRun,
    [string]$StatePath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
if (-not $StatePath) {
    $StatePath = Join-Path $repoRoot 'tmp\copilot_admin_runner_state\bound-copilot-terminal.json'
}
$stateDir = Split-Path -Parent $StatePath
$null = New-Item -ItemType Directory -Path $stateDir -Force

if (-not ('CopilotAdminRunner.WindowBinding' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Text;
using System.Runtime.InteropServices;

namespace CopilotAdminRunner
{
    public static class WindowBinding
    {
        [DllImport("user32.dll")]
        public static extern IntPtr GetForegroundWindow();

        [DllImport("user32.dll", CharSet = CharSet.Unicode)]
        public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);

        [DllImport("user32.dll")]
        public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
    }
}
'@
}

function Get-WindowTitle {
    param([IntPtr]$Handle)

    $builder = New-Object System.Text.StringBuilder 1024
    $null = [CopilotAdminRunner.WindowBinding]::GetWindowText($Handle, $builder, $builder.Capacity)
    $builder.ToString()
}

[Console]::Error.WriteLine('')
[Console]::Error.WriteLine('Copilot-admin terminal binding is armed.')
[Console]::Error.WriteLine('Focus the existing visible Copilot CLI terminal now.')
[Console]::Error.WriteLine("The foreground window will be captured in $CountdownSeconds seconds.")
for ($remaining = $CountdownSeconds; $remaining -gt 0; $remaining--) {
    [Console]::Error.WriteLine(("{0}..." -f $remaining))
    Start-Sleep -Seconds 1
}

$handle = [CopilotAdminRunner.WindowBinding]::GetForegroundWindow()
$processId = 0
$null = [CopilotAdminRunner.WindowBinding]::GetWindowThreadProcessId($handle, [ref]$processId)
$title = Get-WindowTitle -Handle $handle

$payload = [ordered]@{
    status = if ($DryRun) { 'dry-run' } else { 'bound' }
    captured_at = (Get-Date).ToUniversalTime().ToString('o')
    repo_root = $repoRoot.Path
    window_handle = $handle.ToInt64()
    process_id = [int64]$processId
    window_title = $title
    state_path = $StatePath
    note = if ($DryRun) { 'DryRun did not write binding state.' } else { 'Future terminal input can target this window handle.' }
}

if (-not $DryRun) {
    $payload | ConvertTo-Json -Depth 10 | Set-Content -Path $StatePath -Encoding UTF8
}

$payload | ConvertTo-Json -Depth 10
