# Regression Run 2026-08-28 v1

## Scope

This historical run covered the obsolete `regression-kundtjanst-english-translation-consistency` objective in Regression Mode.

The run is invalidated as a Swedish localization report because the objective was inverted: it checked for an English UI instead of identifying non-Swedish Customer Service UI text and recommending Swedish corrections. The replacement test definition is `regression-kundtjanst-svensk-lokalisering-och-terminologi`.

## Environment

- Application: Customer Service Center stage
- Base URL: `https://sps-stage.europark.local/CustomerService`
- Shared browser: visible Edge session on remote debugging port `9222`
- Menu baseline: `raw_data\kundtjanst-funktioner-data.json`, `capturedAt` `2026-08-26T09:19:00`

## Purpose

Verify that every Customer Service Center menu and opened page in stage is consistently translated to English and uses consistent business terminology.
