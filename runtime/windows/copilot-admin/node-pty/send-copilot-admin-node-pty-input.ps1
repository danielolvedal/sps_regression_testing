param(
    [Parameter(Mandatory = $true)]
    [string]$Text,
    [switch]$NoSubmit
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')
$queueDir = Join-Path $repoRoot 'tmp\copilot_admin_runner_state\node-pty-copilot-input-queue'
$null = New-Item -ItemType Directory -Path $queueDir -Force

$request = [ordered]@{
    created_at = (Get-Date).ToUniversalTime().ToString('o')
    text = $Text
    submit = -not [bool]$NoSubmit
}
$fileName = 'input-{0}-{1}.json' -f (Get-Date).ToUniversalTime().ToString('yyyyMMddHHmmssfff'), ([guid]::NewGuid().ToString('N'))
$filePath = Join-Path $queueDir $fileName
$request | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $filePath -Encoding UTF8

[ordered]@{
    status = 'queued'
    input_path = $filePath
    queue_dir = $queueDir
    text = $Text
    submit = -not [bool]$NoSubmit
} | ConvertTo-Json -Depth 10
