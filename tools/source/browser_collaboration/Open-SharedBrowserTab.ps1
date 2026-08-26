param(
    [Parameter(Mandatory = $true)]
    [string]$Url,
    [int]$Port = 9222,
    [string]$SourcePageUrlPrefix = 'https://sps-stage.europark.local/'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-Json([string]$TargetUrl) {
    (Invoke-WebRequest -UseBasicParsing $TargetUrl -TimeoutSec 10).Content | ConvertFrom-Json
}

function Has-Property([object]$Object, [string]$Name) {
    $null -ne $Object -and ($Object.PSObject.Properties.Name -contains $Name)
}

$targets = Get-Json "http://127.0.0.1:$Port/json/list"
$page = $targets | Where-Object {
    $_.type -eq 'page' -and $_.url -like "$SourcePageUrlPrefix*"
} | Select-Object -First 1

if (-not $page) {
    throw "No source page found for prefix '$SourcePageUrlPrefix' on port $Port."
}

Add-Type -AssemblyName System.Net.WebSockets
$ws = [System.Net.WebSockets.ClientWebSocket]::new()
$cts = [Threading.CancellationToken]::None
$ws.ConnectAsync([Uri]$page.webSocketDebuggerUrl, $cts).GetAwaiter().GetResult() | Out-Null

function Send-Cdp([hashtable]$Payload) {
    $json = $Payload | ConvertTo-Json -Compress -Depth 10
    $bytes = [Text.Encoding]::UTF8.GetBytes($json)
    $segment = [ArraySegment[byte]]::new($bytes)
    $ws.SendAsync($segment, [System.Net.WebSockets.WebSocketMessageType]::Text, $true, $cts).GetAwaiter().GetResult() | Out-Null
}

function Receive-Cdp() {
    $buffer = New-Object byte[] 65536
    $stream = New-Object IO.MemoryStream
    do {
        $segment = [ArraySegment[byte]]::new($buffer)
        $result = $ws.ReceiveAsync($segment, $cts).GetAwaiter().GetResult()
        if ($result.Count -gt 0) {
            $stream.Write($buffer, 0, $result.Count)
        }
    } while (-not $result.EndOfMessage)
    [Text.Encoding]::UTF8.GetString($stream.ToArray()) | ConvertFrom-Json
}

try {
    $expression = "window.open(" + (ConvertTo-Json $Url -Compress) + ", '_blank'); 'opened'"
    Send-Cdp @{
        id = 1
        method = 'Runtime.evaluate'
        params = @{
            expression = $expression
            returnByValue = $true
            userGesture = $true
        }
    }

    while ($true) {
        $message = Receive-Cdp
        if ((Has-Property $message 'id') -and $message.id -eq 1) {
            break
        }
    }

    Start-Sleep -Seconds 2
    $updatedTargets = Get-Json "http://127.0.0.1:$Port/json/list"
    $newPage = $updatedTargets | Where-Object {
        $_.type -eq 'page' -and $_.url -like "$Url*"
    } | Select-Object -First 1

    [pscustomobject]@{
        sourcePageTitle = $page.title
        sourcePageUrl = $page.url
        openedUrl = $Url
        targetFound = $null -ne $newPage
        targetId = if ($newPage) { $newPage.id } else { $null }
        targetTitle = if ($newPage) { $newPage.title } else { $null }
        targetUrl = if ($newPage) { $newPage.url } else { $null }
    } | ConvertTo-Json -Depth 6
} finally {
    $ws.Dispose()
}
