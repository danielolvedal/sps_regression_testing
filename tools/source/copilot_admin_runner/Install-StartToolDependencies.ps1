[CmdletBinding()]
param(
    [switch]$PreflightOnly,
    [switch]$SkipWinget
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
$nodePtyResolverPath = Join-Path $repoRoot 'runtime\windows\copilot-admin\node-pty\Resolve-NodePtyTooling.ps1'
. $nodePtyResolverPath

$nodePtyInstallScript = Join-Path $repoRoot 'runtime\install-copilot-admin-node-pty-poc.ps1'
$nodePtyPackagePath = Join-Path $repoRoot 'tools\source\copilot_admin_runner\node_pty_poc\node_modules\node-pty'
$windowsPowerShellPath = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'

function Refresh-ProcessPath {
    $machinePath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    $combined = @($machinePath, $userPath) | Where-Object { $_ }
    if ($combined.Count -gt 0) {
        $env:Path = ($combined -join ';')
    }
}

function Invoke-ExternalCommand {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$Arguments = @()
    )

    $output = & $FilePath @Arguments 2>&1 | Out-String
    $exitCode = if ($null -ne $LASTEXITCODE) { [int]$LASTEXITCODE } else { 0 }
    [pscustomobject]@{
        ExitCode = $exitCode
        Output = $output.Trim()
    }
}

function Resolve-WingetCommand {
    $command = Get-Command winget -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $candidate = Join-Path $env:LOCALAPPDATA 'Microsoft\WindowsApps\winget.exe'
    if (Test-Path $candidate) {
        return $candidate
    }

    return $null
}

function Resolve-BrowserInstallation {
    $entries = @(
        @{ Name = 'Microsoft Edge'; Path = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe' },
        @{ Name = 'Microsoft Edge'; Path = 'C:\Program Files\Microsoft\Edge\Application\msedge.exe' },
        @{ Name = 'Google Chrome'; Path = 'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe' },
        @{ Name = 'Google Chrome'; Path = 'C:\Program Files\Google\Chrome\Application\chrome.exe' }
    )

    $registryKeys = @(
        @{ Name = 'Microsoft Edge'; Key = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe' },
        @{ Name = 'Microsoft Edge'; Key = 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe' },
        @{ Name = 'Google Chrome'; Key = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe' },
        @{ Name = 'Google Chrome'; Key = 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe' }
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

    $match = $entries | Where-Object { Test-Path $_.Path } | Select-Object -First 1
    if (-not $match) {
        return $null
    }

    return [pscustomobject]@{
        Name = $match.Name
        Path = $match.Path
    }
}

function New-DependencyCheck {
    param(
        [Parameter(Mandatory = $true)][string]$Id,
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Category,
        [Parameter(Mandatory = $true)][bool]$Required,
        [Parameter(Mandatory = $true)][string]$Status,
        [Parameter(Mandatory = $true)][string]$Details,
        [string[]]$InstallCommands = @(),
        [ValidateSet('', 'winget', 'script')][string]$AutoInstallMethod = '',
        [string]$WingetId = ''
    )

    [pscustomobject]@{
        Id = $Id
        Name = $Name
        Category = $Category
        Required = $Required
        Status = $Status
        Details = $Details
        InstallCommands = $InstallCommands
        AutoInstallMethod = $AutoInstallMethod
        WingetId = $WingetId
    }
}

function Get-PreflightState {
    $checks = New-Object System.Collections.Generic.List[object]
    $pythonPath = $null
    $pythonReady = $false
    $nodePath = $null
    $npmPath = $null
    $nodeReady = $false

    $windowsHost = $env:OS -eq 'Windows_NT'
    if ($windowsHost -and (Test-Path $windowsPowerShellPath)) {
        $checks.Add((New-DependencyCheck -Id 'windows-platform' -Name 'Windows + Windows PowerShell' -Category 'platform' -Required $true -Status 'ready' -Details $windowsPowerShellPath))
    } else {
        $checks.Add((New-DependencyCheck -Id 'windows-platform' -Name 'Windows + Windows PowerShell' -Category 'platform' -Required $true -Status 'missing' -Details 'start_tool.ps1 is Windows-specific and requires powershell.exe.' -InstallCommands @('Use a supported Windows machine with Windows PowerShell 5.1 installed.')))
    }

    $winget = Resolve-WingetCommand
    if ($winget) {
        $checks.Add((New-DependencyCheck -Id 'winget' -Name 'WinGet' -Category 'optional' -Required $false -Status 'ready' -Details $winget))
    } else {
        $checks.Add((New-DependencyCheck -Id 'winget' -Name 'WinGet' -Category 'optional' -Required $false -Status 'missing' -Details 'Automatic system installs will fall back to manual commands.' -InstallCommands @('Install Microsoft App Installer to enable winget-based automatic installs.')))
    }

    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        $pythonProbe = Invoke-ExternalCommand -FilePath $pythonCommand.Source -Arguments @('-c', 'import sys; print(sys.executable)')
        if ($pythonProbe.ExitCode -eq 0) {
            $pythonPath = ($pythonProbe.Output -split "`r?`n" | Select-Object -Last 1).Trim()
            $pythonReady = $true
            $checks.Add((New-DependencyCheck -Id 'python' -Name 'Python 3' -Category 'system' -Required $true -Status 'ready' -Details $pythonPath))
        } else {
            $checks.Add((New-DependencyCheck -Id 'python' -Name 'Python 3' -Category 'system' -Required $true -Status 'missing' -Details 'python exists but could not execute a simple probe.' -InstallCommands @('winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements') -AutoInstallMethod 'winget' -WingetId 'Python.Python.3.12'))
        }
    } else {
        $checks.Add((New-DependencyCheck -Id 'python' -Name 'Python 3' -Category 'system' -Required $true -Status 'missing' -Details 'python was not found in PATH.' -InstallCommands @('winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements') -AutoInstallMethod 'winget' -WingetId 'Python.Python.3.12'))
    }

    if ($pythonReady) {
        $pythonSqliteProbe = Invoke-ExternalCommand -FilePath $pythonCommand.Source -Arguments @('-c', 'import sqlite3; print(sqlite3.sqlite_version)')
        if ($pythonSqliteProbe.ExitCode -eq 0) {
            $checks.Add((New-DependencyCheck -Id 'python-sqlite' -Name 'Python sqlite3 runtime' -Category 'system' -Required $true -Status 'ready' -Details ("sqlite3=" + (($pythonSqliteProbe.Output -split "`r?`n" | Select-Object -Last 1).Trim()))))
        } else {
            $checks.Add((New-DependencyCheck -Id 'python-sqlite' -Name 'Python sqlite3 runtime' -Category 'system' -Required $true -Status 'missing' -Details 'Python is installed but could not import sqlite3.' -InstallCommands @('winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements') -AutoInstallMethod 'winget' -WingetId 'Python.Python.3.12'))
        }
    } else {
        $checks.Add((New-DependencyCheck -Id 'python-sqlite' -Name 'Python sqlite3 runtime' -Category 'system' -Required $true -Status 'missing' -Details 'Python is unavailable, so sqlite3 support could not be verified.' -InstallCommands @('winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements') -AutoInstallMethod 'winget' -WingetId 'Python.Python.3.12'))
    }

    try {
        $nodePath = Resolve-NodePtyCommand -Name node
        $npmPath = Resolve-NodePtyCommand -Name npm
        $nodeProbe = Invoke-ExternalCommand -FilePath $nodePath -Arguments @('--version')
        $npmProbe = Invoke-ExternalCommand -FilePath $npmPath -Arguments @('--version')
        if ($nodeProbe.ExitCode -eq 0 -and $npmProbe.ExitCode -eq 0) {
            $nodeReady = $true
            $details = "node=$($nodeProbe.Output.Trim()); npm=$($npmProbe.Output.Trim())"
            $checks.Add((New-DependencyCheck -Id 'nodejs' -Name 'Node.js LTS + npm' -Category 'system' -Required $true -Status 'ready' -Details $details))
        } else {
            throw 'node or npm probe failed.'
        }
    } catch {
        $checks.Add((New-DependencyCheck -Id 'nodejs' -Name 'Node.js LTS + npm' -Category 'system' -Required $true -Status 'missing' -Details $_.Exception.Message -InstallCommands @('winget install --id OpenJS.NodeJS.LTS -e --accept-package-agreements --accept-source-agreements') -AutoInstallMethod 'winget' -WingetId 'OpenJS.NodeJS.LTS'))
    }

    if ($nodeReady) {
        $nodeSqliteProbe = Invoke-ExternalCommand -FilePath $nodePath -Arguments @('-e', 'import("node:sqlite").then(() => { console.log("node:sqlite ok"); }).catch((error) => { console.error(error.message); process.exit(1); });')
        if ($nodeSqliteProbe.ExitCode -eq 0) {
            $checks.Add((New-DependencyCheck -Id 'node-sqlite' -Name 'Node.js node:sqlite runtime' -Category 'system' -Required $true -Status 'ready' -Details 'Built-in node:sqlite module is available.'))
        } else {
            $checks.Add((New-DependencyCheck -Id 'node-sqlite' -Name 'Node.js node:sqlite runtime' -Category 'system' -Required $true -Status 'missing' -Details 'Installed Node.js could not load the built-in node:sqlite module required by the PTY transport.' -InstallCommands @('winget upgrade --id OpenJS.NodeJS.LTS -e --accept-package-agreements --accept-source-agreements', 'If node:sqlite is still unavailable, install a newer Node.js release that includes the built-in node:sqlite module.') -AutoInstallMethod 'winget' -WingetId 'OpenJS.NodeJS.LTS'))
        }
    } else {
        $checks.Add((New-DependencyCheck -Id 'node-sqlite' -Name 'Node.js node:sqlite runtime' -Category 'system' -Required $true -Status 'missing' -Details 'Node.js is unavailable, so node:sqlite support could not be verified.' -InstallCommands @('winget install --id OpenJS.NodeJS.LTS -e --accept-package-agreements --accept-source-agreements') -AutoInstallMethod 'winget' -WingetId 'OpenJS.NodeJS.LTS'))
    }

    try {
        $copilotPath = Resolve-CopilotCliCommand
        $copilotProbe = Invoke-ExternalCommand -FilePath $copilotPath -Arguments @('--version')
        if ($copilotProbe.ExitCode -eq 0) {
            $checks.Add((New-DependencyCheck -Id 'copilot-cli' -Name 'GitHub Copilot CLI' -Category 'system' -Required $true -Status 'ready' -Details $copilotProbe.Output.Trim()))
        } else {
            throw 'copilot --version failed.'
        }
    } catch {
        $checks.Add((New-DependencyCheck -Id 'copilot-cli' -Name 'GitHub Copilot CLI' -Category 'system' -Required $true -Status 'missing' -Details $_.Exception.Message -InstallCommands @('winget install --id GitHub.Copilot -e --accept-package-agreements --accept-source-agreements') -AutoInstallMethod 'winget' -WingetId 'GitHub.Copilot'))
    }

    $browser = Resolve-BrowserInstallation
    if ($browser) {
        $checks.Add((New-DependencyCheck -Id 'browser' -Name 'Microsoft Edge or Google Chrome' -Category 'system' -Required $true -Status 'ready' -Details "$($browser.Name) at $($browser.Path)"))
    } else {
        $checks.Add((New-DependencyCheck -Id 'browser' -Name 'Microsoft Edge or Google Chrome' -Category 'system' -Required $true -Status 'missing' -Details 'No supported browser installation was found.' -InstallCommands @('winget install --id Microsoft.Edge -e --accept-package-agreements --accept-source-agreements', 'winget install --id Google.Chrome -e --accept-package-agreements --accept-source-agreements') -AutoInstallMethod 'winget' -WingetId 'Microsoft.Edge'))
    }

    if (Test-Path $nodePtyPackagePath) {
        $checks.Add((New-DependencyCheck -Id 'node-pty-package' -Name 'node-pty repo dependency' -Category 'repo' -Required $true -Status 'ready' -Details $nodePtyPackagePath))
    } else {
        $checks.Add((New-DependencyCheck -Id 'node-pty-package' -Name 'node-pty repo dependency' -Category 'repo' -Required $true -Status 'missing' -Details 'node-pty is not installed in the repository yet.' -InstallCommands @('.\runtime\install-copilot-admin-node-pty-poc.ps1') -AutoInstallMethod 'script'))
    }

    $requiredFailures = @($checks | Where-Object { $_.Required -and $_.Status -ne 'ready' })
    [pscustomobject]@{
        Checks = $checks
        Passed = ($requiredFailures.Count -eq 0)
        MissingRequired = $requiredFailures
        WingetPath = $winget
    }
}

function Write-PreflightReport {
    param(
        [Parameter(Mandatory = $true)]$State,
        [string]$Title = 'Pre-flight summary'
    )

    Write-Host ''
    Write-Host $Title
    Write-Host ('-' * $Title.Length)
    $State.Checks |
        Select-Object Name, Category, Required, Status, Details |
        Format-Table -Wrap -AutoSize |
        Out-String |
        Write-Host

    $actionable = @($State.Checks | Where-Object { $_.Status -ne 'ready' -and $_.InstallCommands.Count -gt 0 })
    if ($actionable.Count -gt 0) {
        Write-Host 'Suggested commands:'
        foreach ($check in $actionable) {
            Write-Host ("- {0} [{1}]" -f $check.Name, $check.Status)
            foreach ($command in $check.InstallCommands) {
                Write-Host ("    {0}" -f $command)
            }
        }
    }
}

function Invoke-WingetInstall {
    param(
        [Parameter(Mandatory = $true)]$Check,
        [Parameter(Mandatory = $true)][string]$WingetPath
    )

    Write-Host ("Installing {0} via winget..." -f $Check.Name)
    $result = Invoke-ExternalCommand -FilePath $WingetPath -Arguments @(
        'install',
        '--id', $Check.WingetId,
        '-e',
        '--accept-package-agreements',
        '--accept-source-agreements',
        '--disable-interactivity'
    )
    Refresh-ProcessPath
    if ($result.ExitCode -ne 0) {
        Write-Warning ("winget install failed for {0}. Exit code: {1}. Output: {2}" -f $Check.Name, $result.ExitCode, $result.Output)
        return $false
    }
    return $true
}

function Invoke-RepoInstall {
    param([Parameter(Mandatory = $true)]$Check)

    if ($Check.Id -ne 'node-pty-package') {
        return $false
    }

    Write-Host 'Installing repo-local node-pty dependency...'
    try {
        & $nodePtyInstallScript
    } catch {
        Write-Warning ("Repo dependency install failed: {0}" -f $_.Exception.Message)
        return $false
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Warning ("Repo dependency install failed with exit code {0}." -f $LASTEXITCODE)
        return $false
    }
    return $true
}

Refresh-ProcessPath
$initialState = Get-PreflightState
Write-PreflightReport -State $initialState -Title 'Initial pre-flight summary'

if ($PreflightOnly) {
    if ($initialState.Passed) {
        Write-Host 'Pre-flight passed. Installation is already complete.'
        exit 0
    }
    Write-Error 'Pre-flight failed. Resolve the missing dependencies above and re-run install_tool.ps1.'
}

$systemInstallChecks = @($initialState.MissingRequired | Where-Object { $_.AutoInstallMethod -eq 'winget' })
$repoInstallChecks = @($initialState.MissingRequired | Where-Object { $_.AutoInstallMethod -eq 'script' })

if ($systemInstallChecks.Count -gt 0) {
    if ($SkipWinget) {
        Write-Warning 'Skipping winget-based system installs because -SkipWinget was requested.'
    } elseif (-not $initialState.WingetPath) {
        Write-Warning 'winget is not available, so missing system dependencies were not installed automatically.'
    } else {
        foreach ($check in $systemInstallChecks) {
            $null = Invoke-WingetInstall -Check $check -WingetPath $initialState.WingetPath
        }
    }
}

Refresh-ProcessPath
$postSystemState = Get-PreflightState
Write-PreflightReport -State $postSystemState -Title 'Post-system-install pre-flight summary'

if (($postSystemState.Checks | Where-Object { $_.Id -eq 'nodejs' -and $_.Status -eq 'ready' }).Count -gt 0) {
    $repoInstallChecks = @($postSystemState.MissingRequired | Where-Object { $_.AutoInstallMethod -eq 'script' })
    foreach ($check in $repoInstallChecks) {
        $null = Invoke-RepoInstall -Check $check
    }
} elseif (($postSystemState.Checks | Where-Object { $_.Id -eq 'node-pty-package' -and $_.Status -ne 'ready' }).Count -gt 0) {
    Write-Warning 'Skipping repo-local node-pty install because Node.js + npm is still unavailable.'
}

Refresh-ProcessPath
$finalState = Get-PreflightState
Write-PreflightReport -State $finalState -Title 'Final pre-flight summary'

if (-not $finalState.Passed) {
    Write-Error 'Installation is not complete. Fix the remaining pre-flight failures above and re-run install_tool.ps1.'
}

Write-Host 'Installation complete. start_tool.ps1 dependencies are ready.'
