function Resolve-NodePtyCommand {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet('node', 'npm')]
        [string]$Name
    )

    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $fileName = if ($Name -eq 'npm') { 'npm.cmd' } else { 'node.exe' }
    $candidates = @(
        (Join-Path $env:ProgramFiles "nodejs\$fileName"),
        (Join-Path ${env:ProgramFiles(x86)} "nodejs\$fileName"),
        (Join-Path $env:LOCALAPPDATA "Programs\nodejs\$fileName")
    )

    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path $candidate)) {
            return $candidate
        }
    }

    throw "$Name was not found in PATH or standard Node.js install locations."
}

function Resolve-CopilotCliCommand {
    $command = Get-Command copilot -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $wingetRoot = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Packages'
    if (Test-Path $wingetRoot) {
        $candidate = Get-ChildItem -Path $wingetRoot -Directory -Filter 'GitHub.Copilot_*' -ErrorAction SilentlyContinue |
            ForEach-Object { Join-Path $_.FullName 'copilot.exe' } |
            Where-Object { Test-Path $_ } |
            Select-Object -First 1
        if ($candidate) {
            return $candidate
        }
    }

    throw "copilot was not found in PATH or the standard WinGet package location."
}
