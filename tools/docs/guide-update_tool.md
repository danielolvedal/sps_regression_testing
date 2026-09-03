Guide: update_tool.ps1 & fetch_common_tests.ps1

Purpose
- update_tool.ps1: Syncs tooling files (tools\, runtime\ by default) from a remote git repository into this repository root.
- fetch_common_tests.ps1: Fetches the shared tests (testing\ by default) from a remote git repository and places them under testing\.

Defaults and assumptions
- Default remote: origin. If run outside a git repo, supply a full remote URL (https://... or git@...) with -Remote.
- Default branch: main
- Scripts attempt git sparse-checkout for efficiency; they fall back to a shallow full clone if necessary.
- After copy, scripts run npm install in directories that contain package.json when -Install is enabled (default).

Usage examples
- PowerShell from repository root:
  .\update_tool.ps1 -Remote "https://github.com/example/repo.git" -Branch main
  .\fetch_common_tests.ps1 -Remote "https://github.com/example/tests.git" -Branch main -Path "testing/common" -Destination "testing/common"

Notes
- If the remote repo contains vendorized node_modules with native binaries, consider the node_modules policy: vendor (include) vs install_on_fetch. Current default: install_on_fetch.
- After making persistent document changes, run:
  .\runtime\test-document-index.ps1
  .\runtime\test-kallinventering-coverage.ps1

Contact
- Add any project-specific adjustments to this guide as needed.