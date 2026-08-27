param(
    [string]$BaseUrl = 'https://sps-stage.europark.local/CustomerService',
    [int]$Port = 9222,
    [string]$OutFile,
    [switch]$IncludeExternal
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
if (-not $OutFile) {
    $OutFile = Join-Path $repoRoot 'raw_data\kundtjanst-funktioner-data.json'
}

Add-Type -AssemblyName System.Net.WebSockets

function Get-Json([string]$Url) {
    (Invoke-WebRequest -UseBasicParsing $Url -TimeoutSec 10).Content | ConvertFrom-Json
}

function Has-Property([object]$Object, [string]$Name) {
    $null -ne $Object -and ($Object.PSObject.Properties.Name -contains $Name)
}

function Connect-CdpPage([string]$StartUrl, [int]$DebugPort) {
    $targets = Get-Json "http://127.0.0.1:$DebugPort/json/list"
    $target = $targets | Where-Object {
        $_.type -eq 'page' -and (
            $_.url -like "$StartUrl*" -or
            $_.title -like '*Kundtjänstportalen*'
        )
    } | Select-Object -First 1

    if (-not $target) {
        throw "No matching page target found for $StartUrl on port $DebugPort."
    }

    $socket = [System.Net.WebSockets.ClientWebSocket]::new()
    $token = [Threading.CancellationToken]::None
    $socket.ConnectAsync([Uri]$target.webSocketDebuggerUrl, $token).GetAwaiter().GetResult() | Out-Null

    [pscustomobject]@{
        Socket = $socket
        Token = $token
        NextId = 0
    }
}

function Send-Cdp([object]$Client, [hashtable]$Payload) {
    $json = $Payload | ConvertTo-Json -Compress -Depth 20
    $bytes = [Text.Encoding]::UTF8.GetBytes($json)
    $segment = [ArraySegment[byte]]::new($bytes)
    $Client.Socket.SendAsync(
        $segment,
        [System.Net.WebSockets.WebSocketMessageType]::Text,
        $true,
        $Client.Token
    ).GetAwaiter().GetResult() | Out-Null
}

function Receive-Cdp([object]$Client) {
    $buffer = New-Object byte[] 1048576
    $stream = New-Object IO.MemoryStream
    do {
        $segment = [ArraySegment[byte]]::new($buffer)
        $result = $Client.Socket.ReceiveAsync($segment, $Client.Token).GetAwaiter().GetResult()
        if ($result.Count -gt 0) {
            $stream.Write($buffer, 0, $result.Count)
        }
    } while (-not $result.EndOfMessage)
    [Text.Encoding]::UTF8.GetString($stream.ToArray()) | ConvertFrom-Json
}

function Invoke-Cdp([object]$Client, [string]$Method, [hashtable]$Params = @{}) {
    $Client.NextId++
    $id = $Client.NextId
    Send-Cdp $Client @{
        id = $id
        method = $Method
        params = $Params
    }

    while ($true) {
        $msg = Receive-Cdp $Client
        if ((Has-Property $msg 'id') -and $msg.id -eq $id) {
            return $msg
        }
    }
}

function Wait-ForLoad([object]$Client, [int]$TimeoutSeconds = 20) {
    $stopwatch = [Diagnostics.Stopwatch]::StartNew()
    while ($stopwatch.Elapsed.TotalSeconds -lt $TimeoutSeconds) {
        $msg = Receive-Cdp $Client
        if ((Has-Property $msg 'method') -and $msg.method -eq 'Page.loadEventFired') {
            return
        }
    }
    throw 'Timed out waiting for Page.loadEventFired.'
}

function Get-PageState([object]$Client) {
    $expr = @'
(() => {
  const norm = (value) => (value || '').replace(/\s+/g, ' ').trim();
  const collect = (selector, mapper, limit = 30) =>
    Array.from(document.querySelectorAll(selector)).map(mapper).filter(Boolean).slice(0, limit);
  return JSON.stringify({
    title: document.title,
    url: location.href,
    headings: collect('h1,h2,h3,h4', (el) => norm(el.innerText || el.textContent), 20),
    labels: collect('label', (el) => norm(el.innerText || el.textContent), 30),
    buttons: collect('button,input[type="submit"],input[type="button"],a.btn', (el) => norm(el.innerText || el.value || el.textContent), 30),
    links: collect('a', (el) => {
      const text = norm(el.innerText || el.textContent);
      const href = el.href || '';
      if (!text || !href || href.endsWith('#')) return null;
      return { text, href };
    }, 30),
    tableHeaders: collect('th', (el) => norm(el.innerText || el.textContent), 30),
    alerts: collect('.alert, .validation-summary-errors, .field-validation-error, .text-danger', (el) => norm(el.innerText || el.textContent), 20),
    inputs: collect('input, select, textarea', (el) => {
      const label = norm(el.getAttribute('placeholder') || el.getAttribute('aria-label') || el.name || el.id || '');
      const type = (el.type || el.tagName || '').toLowerCase();
      return label ? { label, type } : null;
    }, 40),
    snippet: norm(document.body ? document.body.innerText : '').slice(0, 1500)
  });
})()
'@

    $result = Invoke-Cdp $Client 'Runtime.evaluate' @{
        expression = $expr
        returnByValue = $true
    }

    if ((Has-Property $result.result 'exceptionDetails') -and $result.result.exceptionDetails) {
        throw 'Runtime.evaluate failed while reading page state.'
    }

    $result.result.result.value | ConvertFrom-Json
}

function Get-NavigationMap([object]$Client) {
    $expr = @'
(() => {
  const norm = (value) => (value || '').replace(/\s+/g, ' ').trim();
  const records = [];
  const seen = new Set();
  document.querySelectorAll('ul.navbar-nav').forEach((ul) => {
    ul.querySelectorAll(':scope > li').forEach((li) => {
      const topLink = li.querySelector(':scope > a');
      if (!topLink) return;
      const group = norm(topLink.innerText || topLink.textContent);
      const href = topLink.href || '';
      const dropdownItems = Array.from(li.querySelectorAll(':scope ul.dropdown-menu a'));
      if (dropdownItems.length > 0) {
        const groupKey = `group|${group}`;
        if (!seen.has(groupKey)) {
          seen.add(groupKey);
          records.push({ group, text: group, href: null, kind: 'group' });
        }
        dropdownItems.forEach((child) => {
          const text = norm(child.innerText || child.textContent);
          const childHref = child.href || '';
          const key = `item|${group}|${text}|${childHref}`;
          if (text && childHref && !seen.has(key)) {
            seen.add(key);
            records.push({ group, text, href: childHref, kind: 'item' });
          }
        });
      } else if (group && href && !href.endsWith('#')) {
        const key = `item|Direktlankar|${group}|${href}`;
        if (!seen.has(key)) {
          seen.add(key);
          records.push({ group: 'Direktlankar', text: group, href, kind: 'item' });
        }
      }
    });
  });
  return JSON.stringify(records);
})()
'@

    $result = Invoke-Cdp $Client 'Runtime.evaluate' @{
        expression = $expr
        returnByValue = $true
    }

    if ((Has-Property $result.result 'exceptionDetails') -and $result.result.exceptionDetails) {
        throw 'Runtime.evaluate failed while reading navigation.'
    }

    $result.result.result.value | ConvertFrom-Json
}

function Should-InspectItem([object]$Item, [string]$BaseHost, [bool]$AllowExternal) {
    if ($Item.text -match 'Logga ut') {
        return $false
    }

    if (-not $AllowExternal) {
        $uri = [Uri]$Item.href
        if ($uri.Host -ne $BaseHost) {
            return $false
        }
    }

    return $true
}

$baseHost = ([Uri]$BaseUrl).Host
$client = $null
$client = Connect-CdpPage -StartUrl $BaseUrl -DebugPort $Port

try {
    Invoke-Cdp $client 'Page.enable' | Out-Null
    Invoke-Cdp $client 'Runtime.enable' | Out-Null

    $navigation = Get-NavigationMap $client
    $pages = New-Object System.Collections.Generic.List[object]

    foreach ($item in ($navigation | Where-Object { $_.kind -eq 'item' })) {
        if (-not (Should-InspectItem -Item $item -BaseHost $baseHost -AllowExternal:$IncludeExternal)) {
            $pages.Add([pscustomobject]@{
                group = $item.group
                menuText = $item.text
                menuHref = $item.href
                pageTitle = $null
                pageUrl = $item.href
                headings = @()
                labels = @()
                buttons = @()
                links = @()
                tableHeaders = @()
                alerts = @('Skipped by inventory rules.')
                inputs = @()
                snippet = $null
            }) | Out-Null
            continue
        }

        Write-Host "Inspecting: $($item.group) -> $($item.text)"
        try {
            Invoke-Cdp $client 'Page.navigate' @{ url = $item.href } | Out-Null
            Wait-ForLoad $client 20
            Start-Sleep -Milliseconds 500
            $state = Get-PageState $client
            $pages.Add([pscustomobject]@{
                group = $item.group
                menuText = $item.text
                menuHref = $item.href
                pageTitle = $state.title
                pageUrl = $state.url
                headings = @($state.headings)
                labels = @($state.labels)
                buttons = @($state.buttons)
                links = @($state.links)
                tableHeaders = @($state.tableHeaders)
                alerts = @($state.alerts)
                inputs = @($state.inputs)
                snippet = $state.snippet
            }) | Out-Null
        } catch {
            $pages.Add([pscustomobject]@{
                group = $item.group
                menuText = $item.text
                menuHref = $item.href
                pageTitle = $null
                pageUrl = $item.href
                headings = @()
                labels = @()
                buttons = @()
                links = @()
                tableHeaders = @()
                alerts = @("Inspection failed: $($_.Exception.Message)")
                inputs = @()
                snippet = $null
            }) | Out-Null
        }
    }

    $output = [pscustomobject]@{
        capturedAt = (Get-Date).ToString('s')
        baseUrl = $BaseUrl
        navigation = $navigation
        pages = $pages
    }

    $output | ConvertTo-Json -Depth 20 | Set-Content -Path $OutFile -Encoding UTF8
    Write-Output $OutFile
} finally {
    if ($null -ne $client -and $client.PSObject.Properties.Name -contains 'Socket') {
        $client.Socket.Dispose()
    }
}
