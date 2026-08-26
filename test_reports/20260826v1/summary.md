# Regression Summary

## Run Metadata

- **Run ID:** `20260826v1`
- **Date:** `2026-08-26`
- **Environment:** `sps-stage.europark.local` and `web-stage.europark.local`
- **Executed by:** `GitHub Copilot CLI`
- **Scope:** `A, B, C, D, E, F, G`

## Test Summary

| Test ID | Test Name | Status | Brief Outcome | Detail |
| --- | --- | --- | --- | --- |
| `regression-kontrakt-anna-serviceportal-login` | A - Anna assisted login to service portal | `passed` | Expired Anna contract `H-47184-000025049` opened in stage and assisted login landed on `https://web-stage.europark.local/myaccount/index`. | `-` |
| `regression-serviceportal-nytt-kontrakt-migrated-ds` | B - New contract via migrated DS | `passed` | Migrated DS `47184 | Malmen 14, Möllevångsgatan 42 garage A` reached checkout in logged-in state with prefilled identification number. | `-` |
| `regression-serviceportal-nytt-kontrakt-non-migrated-ds` | C - New contract via non-migrated DS | `failed` | Non-migrated DS `900540 | Spiran 9, S:t Persgatan 95` consistently routed the user to legacy details instead of a supported stage flow. | `RegressionError01\report.md` |
| `regression-document-index-coverage` | D - Document index coverage | `passed` | `.\runtime\test-document-index.ps1` passed and confirmed that all tracked persistent files are indexed. | `-` |
| `regression-kallinventering-coverage` | E - Raw-data traceability coverage | `passed` | `.\runtime\test-kallinventering-coverage.ps1` passed and confirmed raw-data coverage plus downstream traceability. | `-` |
| `regression-regression-dependency-synchronization` | F - Regression dependency synchronization | `passed` | `.\runtime\test-regression-dependencies.ps1` passed and confirmed synchronization across test metadata, catalog, and Mermaid. | `-` |
| `regression-serviceportal-checkout-verify-and-create-contract` | G - Checkout verification and create contract | `failed` | Checkout repeatedly rendered `SEK NaN/månad inkl. moms` and an empty notification method dropdown for the migrated DS flow. | `RegressionError02\report.md` |
