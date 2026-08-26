# Regression Run 20260826v2

## Scope

This run executed the following documented regression tests in `testing\regression_test`:

- `A` assisted login to the customer service portal user view
- `B` migrated DS new-contract flow
- `C` non-migrated DS new-contract flow
- `D` document index coverage
- `E` raw-data traceability coverage
- `F` regression dependency synchronization

Test `G` was not executed in this run because test `B` did not end on the clean checkout state required by `G`; it ended on a verified checkout login defect instead.

## Environment

- Customer Service Stage: `https://sps-stage.europark.local/`
- Service Portal Stage: `https://web-stage.europark.local/`
- Shared visible browser session via remote debugging on port `9222`

## Purpose

The purpose of this package is to preserve the outcome of the 2026-08-26 regression execution after the shared-browser login wait rule was updated. The run includes all passed tests and all defects that were verified through repeated reproduction.
