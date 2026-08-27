# Regression Run 2026-08-27 v1

Scope: Regression Mode execution of `regression-serviceportal-nytt-kontrakt-migrated-ds` (Catalog Key B) followed by `regression-serviceportal-checkout-verify-and-create-contract` (Catalog Key G).

Environment: SPS stage with a visible shared Edge browser session, Kundtjänstportalen at `sps-stage.europark.local`, and service portal at `web-stage.europark.local`.

Purpose: Verify that an assisted-login customer can start a new contract for a migrated DS, reach checkout without losing the logged-in session, and complete checkout contract creation.
