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
    [string]$Bridge = 'unknown',
    [string]$VerificationId
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
$logDir = Join-Path $repoRoot 'tmp\copilot_admin_runner_logs'
$null = New-Item -ItemType Directory -Path $logDir -Force
$logPath = Join-Path $logDir ("terminal-input-{0}.jsonl" -f (Get-Date).ToUniversalTime().ToString('yyyyMMdd'))
if (-not $BoundWindowPath) {
    $BoundWindowPath = Join-Path $repoRoot 'tmp\copilot_admin_runner_state\bound-copilot-terminal.json'
}

function Write-TerminalInputLog {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Event,
        [hashtable]$Details = @{}
    )

    $record = [ordered]@{
        timestamp = (Get-Date).ToUniversalTime().ToString('o')
        event_id = [guid]::NewGuid().ToString('N')
        event = $Event
        bridge = $Bridge
        pid = $PID
        repo_root = $repoRoot.Path
        verification_id = $VerificationId
        details = $Details
    }
    Add-Content -Path $logPath -Value ($record | ConvertTo-Json -Depth 10 -Compress) -Encoding UTF8
}

function Get-ForegroundWindowTitle {
    if (-not ('CopilotAdminRunner.NativeWindow' -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.Text;
using System.Runtime.InteropServices;

namespace CopilotAdminRunner
{
    public static class NativeWindow
    {
        [DllImport("user32.dll")]
        public static extern IntPtr GetForegroundWindow();

        [DllImport("user32.dll", CharSet = CharSet.Unicode)]
        public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);

        [DllImport("user32.dll")]
        public static extern bool IsWindow(IntPtr hWnd);

        [DllImport("user32.dll")]
        public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

        [DllImport("user32.dll")]
        public static extern bool SetForegroundWindow(IntPtr hWnd);

        [DllImport("user32.dll", CharSet = CharSet.Unicode)]
        public static extern bool PostMessage(IntPtr hWnd, uint msg, IntPtr wParam, IntPtr lParam);
    }
}
'@
    }

    $handle = [CopilotAdminRunner.NativeWindow]::GetForegroundWindow()
    $builder = New-Object System.Text.StringBuilder 1024
    $null = [CopilotAdminRunner.NativeWindow]::GetWindowText($handle, $builder, $builder.Capacity)
    $builder.ToString()
}

function Get-WindowTitleByHandle {
    param([IntPtr]$Handle)

    $builder = New-Object System.Text.StringBuilder 1024
    $null = [CopilotAdminRunner.NativeWindow]::GetWindowText($Handle, $builder, $builder.Capacity)
    $builder.ToString()
}

function Get-BoundWindow {
    if (-not (Test-Path $BoundWindowPath)) {
        throw "Bound Copilot terminal window was not found. Run .\runtime\bind-copilot-admin-terminal.ps1 first, or use -UseForegroundWindow for diagnostic tests."
    }

    $state = Get-Content $BoundWindowPath -Raw | ConvertFrom-Json
    $handle = [IntPtr]([int64]$state.window_handle)
    if (-not [CopilotAdminRunner.NativeWindow]::IsWindow($handle)) {
        throw "Bound Copilot terminal window handle is no longer valid. Re-run .\runtime\bind-copilot-admin-terminal.ps1."
    }

    [ordered]@{
        handle = $handle
        state = $state
        current_title = Get-WindowTitleByHandle -Handle $handle
    }
}

$sha256 = [System.Security.Cryptography.SHA256]::Create()
try {
    $promptHash = [System.BitConverter]::ToString(
        $sha256.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($Prompt))
    ).Replace('-', '').ToLowerInvariant()
} finally {
    $sha256.Dispose()
}

$startTitle = Get-ForegroundWindowTitle
$boundWindow = $null
if ($UseBoundWindow) {
    $boundWindow = Get-BoundWindow
}
Write-TerminalInputLog -Event 'terminal_input_requested' -Details @{
    dry_run = [bool]$DryRun
    armed = [bool]$Arm
    submit = [bool]$Submit
    clear_existing_input = -not [bool]$PreserveExistingInput
    use_bound_window = [bool]$UseBoundWindow
    delivery_mode = $DeliveryMode
    bound_window_path = $BoundWindowPath
    bound_window_title = if ($boundWindow) { $boundWindow.current_title } else { $null }
    countdown_seconds = $CountdownSeconds
    prompt_length = $Prompt.Length
    prompt_sha256 = $promptHash
    foreground_window_title_at_start = $startTitle
}

if ($DryRun) {
    $result = [ordered]@{
        status = 'dry-run'
        bridge = $Bridge
        verification_id = $VerificationId
        prompt = $Prompt
        prompt_sha256 = $promptHash
        log_path = $logPath
        foreground_window_title_at_start = $startTitle
        use_bound_window = [bool]$UseBoundWindow
        delivery_mode = $DeliveryMode
        bound_window_title = if ($boundWindow) { $boundWindow.current_title } else { $null }
        clear_existing_input = -not [bool]$PreserveExistingInput
        note = 'DryRun did not write clipboard, clear input, paste text, or press Enter.'
    }
    Write-TerminalInputLog -Event 'terminal_input_dry_run_completed' -Details @{
        prompt_sha256 = $promptHash
    }
    $result | ConvertTo-Json -Depth 10
    exit 0
}

if (-not $Arm) {
    Write-TerminalInputLog -Event 'terminal_input_rejected_not_armed' -Details @{
        prompt_sha256 = $promptHash
    }

    if ($DeliveryMode -eq 'BackgroundPostMessage' -and -not $UseBoundWindow) {
        Write-TerminalInputLog -Event 'terminal_input_rejected_unbound_background' -Details @{
            prompt_sha256 = $promptHash
        }
        throw 'BackgroundPostMessage requires -UseBoundWindow. Bind the Copilot terminal first.'
    }
    throw 'Refusing terminal input because -Arm was not provided. Use -DryRun for non-interactive validation.'
}

[Console]::Error.WriteLine('')
[Console]::Error.WriteLine('Copilot-admin terminal input adapter is armed.')
[Console]::Error.WriteLine('Focus the existing visible Copilot CLI terminal now if no bound window is configured.')
[Console]::Error.WriteLine("The prompt will be pasted in $CountdownSeconds seconds.")
if ($Submit) {
    [Console]::Error.WriteLine('Submit mode is ON: Enter will also be sent after paste.')
} else {
    [Console]::Error.WriteLine('Submit mode is OFF: only paste will be sent; you must press Enter manually.')
}
if ($PreserveExistingInput) {
    [Console]::Error.WriteLine('Existing input preservation is ON: prompt will be appended at the current cursor position.')
} else {
    [Console]::Error.WriteLine('Existing input preservation is OFF: Ctrl+U and Ctrl+K will clear the active input line before paste.')
}
if ($UseBoundWindow) {
    [Console]::Error.WriteLine(("Bound window mode is ON: target is '{0}'." -f $boundWindow.current_title))
} else {
    [Console]::Error.WriteLine('Bound window mode is OFF: target is whichever window is foreground after countdown.')
}
[Console]::Error.WriteLine(("Delivery mode: {0}." -f $DeliveryMode))

for ($remaining = $CountdownSeconds; $remaining -gt 0; $remaining--) {
    [Console]::Error.WriteLine(("{0}..." -f $remaining))
    Start-Sleep -Seconds 1
}

Set-Clipboard -Value $Prompt

$targetTitle = $null
if ($DeliveryMode -eq 'BackgroundPostMessage') {
    $targetTitle = Get-WindowTitleByHandle -Handle $boundWindow.handle
    if (-not $PreserveExistingInput) {
        $null = [CopilotAdminRunner.NativeWindow]::PostMessage($boundWindow.handle, 0x0102, [IntPtr]21, [IntPtr]0)
        Start-Sleep -Milliseconds 100
        $null = [CopilotAdminRunner.NativeWindow]::PostMessage($boundWindow.handle, 0x0102, [IntPtr]11, [IntPtr]0)
        Start-Sleep -Milliseconds 100
    }
    foreach ($char in $Prompt.ToCharArray()) {
        $null = [CopilotAdminRunner.NativeWindow]::PostMessage($boundWindow.handle, 0x0102, [IntPtr][int][char]$char, [IntPtr]0)
        Start-Sleep -Milliseconds 2
    }
    if ($Submit) {
        Start-Sleep -Milliseconds 250
        $null = [CopilotAdminRunner.NativeWindow]::PostMessage($boundWindow.handle, 0x0102, [IntPtr]13, [IntPtr]0)
    }
} else {
    if ($UseBoundWindow) {
        $null = [CopilotAdminRunner.NativeWindow]::ShowWindow($boundWindow.handle, 5)
        Start-Sleep -Milliseconds 200
        $null = [CopilotAdminRunner.NativeWindow]::SetForegroundWindow($boundWindow.handle)
        Start-Sleep -Milliseconds 500
        $targetTitle = Get-ForegroundWindowTitle
    } else {
        $targetTitle = Get-ForegroundWindowTitle
    }

    $shell = New-Object -ComObject WScript.Shell
    if (-not $PreserveExistingInput) {
        $shell.SendKeys('^u')
        Start-Sleep -Milliseconds 100
        $shell.SendKeys('^k')
        Start-Sleep -Milliseconds 100
    }
    $shell.SendKeys('^v')
    if ($Submit) {
        Start-Sleep -Milliseconds 250
        $shell.SendKeys('{ENTER}')
    }
}

$result = [ordered]@{
    status = 'sent'
    bridge = $Bridge
    verification_id = $VerificationId
    submit = [bool]$Submit
    clear_existing_input = -not [bool]$PreserveExistingInput
    prompt_sha256 = $promptHash
    log_path = $logPath
    foreground_window_title_at_start = $startTitle
    foreground_window_title_at_send = $targetTitle
    use_bound_window = [bool]$UseBoundWindow
    delivery_mode = $DeliveryMode
    bound_window_title = if ($boundWindow) { $boundWindow.current_title } else { $null }
    note = if ($DeliveryMode -eq 'BackgroundPostMessage') { 'Prompt was sent with PostMessage to the bound window after the countdown.' } else { 'Prompt was pasted into the foreground window after the countdown.' }
}
Write-TerminalInputLog -Event 'terminal_input_sent' -Details @{
    submit = [bool]$Submit
    clear_existing_input = -not [bool]$PreserveExistingInput
    prompt_sha256 = $promptHash
    foreground_window_title_at_send = $targetTitle
    use_bound_window = [bool]$UseBoundWindow
    delivery_mode = $DeliveryMode
    bound_window_title = if ($boundWindow) { $boundWindow.current_title } else { $null }
}
$result | ConvertTo-Json -Depth 10
