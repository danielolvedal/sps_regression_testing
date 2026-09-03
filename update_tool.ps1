<#
update_tool.ps1
Usage: .\update_tool.ps1 [-Remote <url|name>] [-Branch <branch>] [-Paths <"tools","runtime">] [-Install:$true/$false]

Defaults from plan: Remote=origin, Branch=main, Paths=@('tools','runtime'), Install = $true
#>
param(
    [string]$Remote = 'origin',
    [string]$Branch = 'main',
    [string[]]$Paths = @('tools','runtime'),
    [switch]$Install = $true
)

function Write-Log { param($m) Write-Host "[update_tool] $m" }

$cwd = Resolve-Path .
$temp = Join-Path $env:TEMP ("update_tool_" + [guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $temp | Out-Null

# Resolve remote URL
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

# Attempt sparse-checkout clone
$cloned = $false
try {
    Write-Log "Attempting shallow clone with sparse-checkout (filter=blob:none)"
    git clone --no-checkout --filter=blob:none --depth 1 --branch $Branch $remoteUrl "$temp" 2>&1 | Write-Output
    Push-Location $temp
    git sparse-checkout init --cone 2>&1 | Write-Output
    git sparse-checkout set $($Paths -join ' ') 2>&1 | Write-Output
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

# Copy requested paths into repository root
foreach ($p in $Paths) {
    $src = Join-Path $temp $p
    $dst = Join-Path $cwd $p
    if (-not (Test-Path $src)) {
        Write-Log "Warning: path '$p' not found in remote clone. Skipping."
        continue
    }
    Write-Log "Syncing $p -> $dst"
    if (Test-Path $dst) {
        Write-Log "Removing existing $dst"
        Remove-Item -Recurse -Force $dst
    }
    # Ensure parent exists
    $parent = Split-Path $dst -Parent
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent | Out-Null }
    Copy-Item -Path $src -Destination $dst -Recurse -Force
}

# Optionally run npm/yarn install where package.json exists
if ($Install) {
    Write-Log "Install-on-fetch enabled. Searching for package.json under synced paths."
    foreach ($p in $Paths) {
        $full = Join-Path $cwd $p
        if (-not (Test-Path $full)) { continue }
        $dirs = Get-ChildItem -Path $full -Recurse -Directory -Force -ErrorAction SilentlyContinue | Where-Object { Test-Path (Join-Path $_.FullName 'package.json') }
        # Also check the root of $full
        if (Test-Path (Join-Path $full 'package.json')) { $dirs = ,(Get-Item $full) + $dirs }
        foreach ($d in $dirs) {
            $dpath = $d.FullName
            Write-Log "Running npm install in $dpath"
            if (Test-Path (Join-Path $dpath 'package-lock.json') -or Test-Path (Join-Path $dpath 'package.json')) {
                Push-Location $dpath
                if (Get-Command npm -ErrorAction SilentlyContinue) { npm install --no-audit --no-fund 2>&1 | Write-Output } else { Write-Log "npm not found in PATH; skipping install in $dpath" }
                Pop-Location
            }
        }
    }
}

# Cleanup
Remove-Item -Recurse -Force $temp
Write-Log "update_tool: Done."