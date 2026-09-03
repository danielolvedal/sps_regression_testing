# Install preflight report

Passed: False

## Checks
- Windows + Windows PowerShell | platform | Required: True | Status: ready | Details: C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe
- WinGet | optional | Required: False | Status: ready | Details: C:\Users\epedersen-ep\AppData\Local\Microsoft\WindowsApps\winget.exe
- Python 3 | system | Required: True | Status: ready | Details: C:\Program Files\Python312\python.exe
- Python sqlite3 runtime | system | Required: True | Status: ready | Details: sqlite3=3.49.1
- Node.js LTS + npm | system | Required: True | Status: ready | Details: node=v20.19.5; npm=10.8.2
- Node.js node:sqlite runtime | system | Required: True | Status: missing | Details: Installed Node.js could not load the built-in node:sqlite module required by the PTY transport.
- Playwright e2e npm deps | repo | Required: True | Status: missing | Details: node_modules/playwright-core missing in e2e folder.
- GitHub Copilot CLI | system | Required: True | Status: ready | Details: GitHub Copilot CLI 1.0.82.
Run 'copilot update' to check for updates.
- Microsoft Edge or Google Chrome | system | Required: True | Status: ready | Details: Microsoft Edge at C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe
- node-pty repo dependency | repo | Required: True | Status: ready | Details: C:\Apcoa-Git\sps_regression_testing\tools\source\copilot_admin_runner\node_pty_poc\node_modules\node-pty

## Suggested commands
- Node.js node:sqlite runtime (missing)
    - winget upgrade --id OpenJS.NodeJS.LTS -e --accept-package-agreements --accept-source-agreements
    - If node:sqlite is still unavailable, install a newer Node.js release that includes the built-in node:sqlite module.
- Playwright e2e npm deps (missing)
    - cd "C:\Apcoa-Git\sps_regression_testing\tools\source\copilot_admin_control_plane\e2e" && npm install
