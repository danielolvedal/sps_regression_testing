# Regression Summary

## Run Metadata

- **Run ID:** `20260826v2`
- **Date:** `2026-08-26`
- **Environment:** `sps-stage.europark.local` and `web-stage.europark.local`
- **Executed by:** `GitHub Copilot CLI`
- **Scope:** `A, B, C, D, E, F`

## Test Summary

| Test ID | Test Name | Status | Brief Outcome | Detail |
| --- | --- | --- | --- | --- |
| `regression-kontrakt-anna-serviceportal-login` | A - Anna assisted login to service portal | `passed` | Assisted login ended on `https://web-stage.europark.local/myaccount/index` for `Anna Walldén`, with the related contract tab still open in stage. | `-` |
| `regression-serviceportal-nytt-kontrakt-migrated-ds` | B - New contract via migrated DS | `failed` | Migrated DS `47184 | Malmen 14, Möllevångsgatan 42 garage A` reached checkout three times, but checkout rendered `Fel` / `Inloggning krävs` with BankID prompt instead of a valid logged-in continuation. | `RegressionError01\report.md` |
| `regression-serviceportal-nytt-kontrakt-non-migrated-ds` | C - New contract via non-migrated DS | `failed` | Non-migrated DS `900540 | Spiran 9, S:t Persgatan 95` consistently routed the user to legacy details instead of a supported stage flow. | `RegressionError02\report.md` |
| `regression-document-index-coverage` | D - Document index coverage | `passed` | `.\runtime\test-document-index.ps1` passed and confirmed that all tracked persistent files are indexed. | `-` |
| `regression-kallinventering-coverage` | E - Raw-data traceability coverage | `passed` | `.\runtime\test-kallinventering-coverage.ps1` passed and confirmed raw-data coverage plus downstream traceability. | `-` |
| `regression-regression-dependency-synchronization` | F - Regression dependency synchronization | `passed` | `.\runtime\test-regression-dependencies.ps1` passed and confirmed synchronization across test metadata, catalog, and Mermaid. | `-` |

## Not Executed

- `G` checkout verification and create contract was not executed in this run because `B` ended on a verified checkout login defect rather than the clean checkout state that `G` requires.
