param(
    [string]$Url = 'https://sps-stage.europark.local/CustomerService',
    [ValidateSet('auto', 'edge', 'chrome')]
    [string]$Browser = 'auto',
    [int]$Port = 9222,
    [string]$ProfileDir,
    [switch]$ReuseExisting
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
if (-not $ProfileDir) {
    $ProfileDir = Join-Path $repoRoot "tmp\browser-profile-$Port"
}

function Get-DebugInfo([int]$DebugPort) {
    try {
        $version = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$DebugPort/json/version" -TimeoutSec 2
        return $version.Content | ConvertFrom-Json
    } catch {
        return $null
    }
}

function Resolve-BrowserPath([string]$RequestedBrowser) {
    $entries = @(
        @{ Name = 'edge'; Path = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe' },
        @{ Name = 'edge'; Path = 'C:\Program Files\Microsoft\Edge\Application\msedge.exe' },
        @{ Name = 'chrome'; Path = 'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe' },
        @{ Name = 'chrome'; Path = 'C:\Program Files\Google\Chrome\Application\chrome.exe' }
    )

    $registryKeys = @(
        @{ Name = 'edge'; Key = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe' },
        @{ Name = 'edge'; Key = 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe' },
        @{ Name = 'chrome'; Key = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe' },
        @{ Name = 'chrome'; Key = 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe' }
    )

    foreach ($entry in $registryKeys) {
        if (Test-Path $entry.Key) {
            $item = Get-ItemProperty $entry.Key
            $path = $item.'(default)'
            if ($path) {
                $entries += @{ Name = $entry.Name; Path = $path }
            }
        }
    }

    $filtered = $entries | Where-Object {
        ($RequestedBrowser -eq 'auto' -or $_.Name -eq $RequestedBrowser) -and
        (Test-Path $_.Path)
    } | Select-Object -First 1

    if (-not $filtered) {
        throw "Could not find a supported browser for '$RequestedBrowser'."
    }

    return $filtered
}

$existing = Get-DebugInfo -DebugPort $Port
if ($existing) {
    if (-not $ReuseExisting) {
        throw "Remote debugging port $Port is already in use. Re-run with -ReuseExisting or choose another -Port."
    }

    [pscustomobject]@{
        browser = $existing.Browser
        browserPath = $null
        port = $Port
        processId = $null
        profileDir = $ProfileDir
        startUrl = $Url
        debugVersionEndpoint = "http://127.0.0.1:$Port/json/version"
        debugTargetsEndpoint = "http://127.0.0.1:$Port/json/list"
        webSocketDebuggerUrl = $existing.webSocketDebuggerUrl
        launched = $false
    } | ConvertTo-Json -Depth 6
    return
}

$browserInfo = Resolve-BrowserPath -RequestedBrowser $Browser
New-Item -ItemType Directory -Force -Path $ProfileDir | Out-Null

$arguments = @(
    '--new-window',
    "--remote-debugging-port=$Port",
    "--user-data-dir=$ProfileDir",
    $Url
)

if ($browserInfo.Name -eq 'edge') {
    $arguments = @('--inprivate') + $arguments
} else {
    $arguments = @('--incognito') + $arguments
}

$process = Start-Process -FilePath $browserInfo.Path -ArgumentList $arguments -PassThru

$debugInfo = $null
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    Start-Sleep -Milliseconds 500
    $debugInfo = Get-DebugInfo -DebugPort $Port
    if ($debugInfo) {
        break
    }
}

if (-not $debugInfo) {
    throw "The browser started, but the debugging endpoint on port $Port did not become available."
}

[pscustomobject]@{
    browser = $debugInfo.Browser
    browserPath = $browserInfo.Path
    port = $Port
    processId = $process.Id
    profileDir = $ProfileDir
    startUrl = $Url
    debugVersionEndpoint = "http://127.0.0.1:$Port/json/version"
    debugTargetsEndpoint = "http://127.0.0.1:$Port/json/list"
    webSocketDebuggerUrl = $debugInfo.webSocketDebuggerUrl
    launched = $true
} | ConvertTo-Json -Depth 6
