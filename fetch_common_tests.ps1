<#
fetch_common_tests.ps1
Usage: .\fetch_common_tests.ps1 [-Remote <url|name>] [-Branch <branch>] [-Path <testing>] [-Destination <testing>] [-Install:$true/$false]

This script fetches the test artifacts (default 'testing') from the given remote/branch and copies them into the repo's testing/ folder.
#>
param(
    [string]$Remote = 'origin',
    [string]$Branch = 'main',
    [string]$Path = 'testing',
    [string]$Destination = 'testing',
    [switch]$Install = $true
)

function Write-Log { param($m) Write-Host "[fetch_common_tests] $m" }

$cwd = Resolve-Path .
$temp = Join-Path $env:TEMP ("fetch_tests_" + [guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $temp | Out-Null

# Resolve remote URL similar to update_tool
$remoteUrl = $null
try {
    $isGit = (git rev-parse --is-inside-work-tree 2>$null) -ne $null
} catch { $isGit = $false }

if ($isGit -and $Remote -ne '' ) {
    try {
        $remoteUrl = (git remote get-url $Remote) -join ''
        Write-Log "Resolved remote '$Remote' => $remoteUrl"
    } catch {
        Write-Log "Could not resolve remote '$Remote' in current repo. If this is not a git repo, supply a full URL as -Remote." 
    }
}

if (-not $remoteUrl) {
    if ($Remote -match '^(https?:|git@)') {
        $remoteUrl = $Remote
        Write-Log "Using provided remote URL: $remoteUrl"
    }
}

if (-not $remoteUrl) {
    Write-Log "ERROR: Could not determine remote URL. Either run this from a git repo with remote '$Remote' or provide a URL with -Remote 'git@...' or 'https://...'"
    Remove-Item -Recurse -Force $temp
    exit 1
}

# Try sparse-checkout for the specific testing path
$cloned = $false
try {
    Write-Log "Attempting shallow clone with sparse-checkout for path '$Path'"
    git clone --no-checkout --filter=blob:none --depth 1 --branch $Branch $remoteUrl "$temp" 2>&1 | Write-Output
    Push-Location $temp
    git sparse-checkout init --cone 2>&1 | Write-Output
    git sparse-checkout set $Path 2>&1 | Write-Output
    git checkout --progress --force 2>&1 | Write-Output
    Pop-Location
    $cloned = $true
    Write-Log "Sparse checkout succeeded"
} catch {
    Write-Log "Sparse-checkout approach failed, falling back to full shallow clone: $_"
    if (Test-Path $temp) { Remove-Item -Recurse -Force $temp; New-Item -ItemType Directory -Path $temp | Out-Null }
    try {
        git clone --depth 1 --branch $Branch $remoteUrl "$temp" 2>&1 | Write-Output
        $cloned = $true
        Write-Log "Full shallow clone succeeded"
    } catch {
        Write-Log "Full clone failed: $_"
        Remove-Item -Recurse -Force $temp
        exit 1
    }
}

$src = Join-Path $temp $Path
$dst = Join-Path $cwd $Destination
if (-not (Test-Path $src)) { Write-Log "ERROR: Path '$Path' not found in remote repo."; Remove-Item -Recurse -Force $temp; exit 1 }

if (Test-Path $dst) { Write-Log "Removing existing destination $dst"; Remove-Item -Recurse -Force $dst }
New-Item -ItemType Directory -Path (Split-Path $dst -Parent) -Force | Out-Null
Copy-Item -Path $src -Destination $dst -Recurse -Force

# Optionally run npm install for test tools
if ($Install) {
    Write-Log "Install-on-fetch enabled. Running npm install where package.json is present under $dst"
    $dirs = Get-ChildItem -Path $dst -Recurse -Directory -Force -ErrorAction SilentlyContinue | Where-Object { Test-Path (Join-Path $_.FullName 'package.json') }
    if (Test-Path (Join-Path $dst 'package.json')) { $dirs = ,(Get-Item $dst) + $dirs }
    foreach ($d in $dirs) {
        $dpath = $d.FullName
        Write-Log "Running npm install in $dpath"
        Push-Location $dpath
        if (Get-Command npm -ErrorAction SilentlyContinue) { npm install --no-audit --no-fund 2>&1 | Write-Output } else { Write-Log "npm not found in PATH; skipping install in $dpath" }
        Pop-Location
    }
}

Remove-Item -Recurse -Force $temp
Write-Log "fetch_common_tests: Done."