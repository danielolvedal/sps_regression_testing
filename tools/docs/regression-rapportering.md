# Regression Test Reporting Standard

This document defines how regression test results must be documented and stored.

## Purpose

Ensure that each eligible regression run leaves behind a traceable local result package that both AI agents and developers can use without rediscovering the same context.

This reporting standard applies to `Regression Mode`. It does not apply to `Learning Mode`, where the purpose is to develop or refine the test itself.

## Mode Rule

There are two execution modes:

- `Learning Mode`
- `Regression Mode`

In `Learning Mode`, the agent must not create or update run folders outside the local `tmp` workspace.

In `Regression Mode`, the agent may create or update run folders under the local report root according to the rules in this document.

## Storage Location

All regression reports must be stored locally under:

`tmp\regression_local\<owner>\reports`

`<owner>` should normally be the GitHub-style username for the person running or curating the regression work. Set `COPILOT_ADMIN_TEST_OWNER` when a machine account or Windows username would otherwise be ambiguous.

## Run Folder Naming

Each reported regression run must create a folder using:

`tmp\regression_local\<owner>\reports\YYYYMMDDvN`

Examples:

- `tmp\regression_local\danielolvedal\reports\20260903v1`
- `tmp\regression_local\danielolvedal\reports\20260903v2`

`vN` is used when multiple separate runs are reported on the same day.

## Mandatory Files Per Reported Run

Each reported run folder must contain at minimum:

- `summary.md` - one-line summary per test
- `README.md` - brief description of scope, environment, and purpose

## Language Requirement

All report files under the local report root must be written in clear, professional English suitable for an international development team.

## Summary Format

`summary.md` must contain one row per test with at least:

- test ID or test name
- status: `passed` or `failed`
- brief outcome
- link to the detailed defect report if the test failed and the defect is verified

If a test required candidate iteration because a selected object had no saleable product or no free spot, the summary should note that observation briefly when it is relevant for setup follow-up.

## Defect Folders

Each verified defect must get its own folder:

`tmp\regression_local\<owner>\reports\YYYYMMDDvN\RegressionErrorNN`

Examples:

- `tmp\regression_local\danielolvedal\reports\20260903v1\RegressionError01`
- `tmp\regression_local\danielolvedal\reports\20260903v1\RegressionError02`

## Verification Requirement Before Reporting

A failed regression outcome must not be written as a report package for developers until the defect has been verified through at least three iterative reproductions with the same outcome.

If the defect has not yet been verified three times, the agent must not create a failed-test report under the local report root. Instead, the agent should update the regression test definition with the latest observations and continue verification work before reporting.

## Contents of Each Defect Report

Each `RegressionErrorNN` folder must contain at minimum:

- `report.md`

The defect report must include:

1. title
2. status
3. affected environment
4. related test case
5. summary
6. reproduction steps
7. actual result
8. expected result
9. reproducibility
10. technical observations
11. evidence and artifacts
12. recommendation to developers

## Screenshots and Artifacts

If screenshots, exports, or other supporting artifacts are needed, they must be stored inside the relevant `RegressionErrorNN` folder.

Examples:

- `tmp\regression_local\danielolvedal\reports\20260903v1\RegressionError01\screenshot-01.png`
- `tmp\regression_local\danielolvedal\reports\20260903v1\RegressionError01\network-notes.md`

## Working Rule

When a regression test is executed in `Regression Mode`, the agent must:

1. update the regression test case with reusable execution learnings
2. create or update a run folder in `tmp\regression_local\<owner>\reports` for passed results and verified failed results only
3. write `summary.md`
4. create a detailed defect report for each failed test only after verification is complete

When a regression test is executed in `Learning Mode`, the agent must keep the output in the test documentation and must not generate a run package.

## Candidate Iteration Rule

For DS-driven purchase or contract-creation tests, the absence of a saleable product or free spot on one selected DS must not automatically be treated as a regression failure.

Instead, the agent must:

1. record which DS candidate was tried
2. record that no saleable product or free spot was available
3. continue the test with another suitable DS candidate when the test definition allows iteration

This observation should remain visible in the run summary or test notes so that the reviewer can decide whether the DS setup itself needs investigation.

Only after the allowed iteration has been exhausted, or a genuine product defect has been observed, should the outcome be marked as failed.

## Important Principle

A failed regression test is not ready for developer-facing reporting until the defect has been verified. Before that point, the correct place for the finding is the regression test documentation itself, not the local report root.

The same principle applies to all `Learning Mode` executions, even when the observed outcome is passed.
