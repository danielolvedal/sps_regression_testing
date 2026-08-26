# Migrated DS checkout requires fresh login despite active assisted session

## Status

`verified`

## Affected Environment

- Customer Service Stage: `https://sps-stage.europark.local/EditContract/Overview`
- Service Portal Stage checkout: `https://web-stage.europark.local/garage/checkout/{saleId}`

## Related Test Case

- `regression-serviceportal-nytt-kontrakt-migrated-ds`
- Catalog key: `B`

## Summary

After the assisted-login flow and migrated DS selection succeed, the service portal reaches checkout on `web-stage`, but the resulting checkout view renders `Fel`, `Inloggning krävs`, and `Logga in med BankID` instead of continuing in the expected logged-in checkout state.

## Reproduction Steps

1. Complete test `A` and confirm the user is logged in on `https://web-stage.europark.local/myaccount/index`.
2. In `Admin -> Migrate DS`, select `47184 | Malmen 14, Möllevångsgatan 42 garage A | Migrated`.
3. In the service portal, search for `Malmen 14, Möllevångsgatan 42 garage A`.
4. Open the matching parking, click `Hyr plats`, choose the saleable product, keep today's start date, and click `Nästa`.
5. Inspect the resulting checkout page.

## Actual Result

- The flow reaches a `web-stage` checkout URL on each reproduction.
- Checkout renders `Fel` and `Inloggning krävs`.
- The page prompts the user to `Logga in med BankID`.
- The checkout still exposes logged-in/assisted-session indicators, including a `Logga ut` link and hidden prefilled `CustomerModel.IdentificationNumber = 740130-0608`.

## Expected Result

The migrated DS flow should continue into a valid logged-in checkout state where the assisted user remains authenticated and can proceed with the checkout verification required by the regression chain.

## Reproducibility

- **Number of runs:** `3`
- **Same outcome each time:** `yes`
- **Notes:** Each reproduction reached a distinct checkout URL on `web-stage` before showing the same login defect.

## Technical Observations

- The DS routing itself remained on the intended `web-stage` host.
- The previously verified migrated candidate still exposed a saleable product and advanced to checkout.
- The defect appeared after `Nästa`, which means the failure happened after DS selection and product selection, not during search or detail navigation.

## Evidence and Artifacts

- Screenshots:
  - None saved in this rerun
- URLs:
  - `https://sps-stage.europark.local/EditContract/Overview?contractId=H-47184-000025049`
  - `https://web-stage.europark.local/garage/details/cfce7585-2612-5b55-5376-fe19d5a04c04`
  - `https://web-stage.europark.local/garage/checkout/{saleId}`
- Other:
  - Verified within regression run `20260826v2`

## Recommendation to Developers

Investigate why the migrated DS checkout step drops into a BankID login requirement after `Nästa` even though the assisted session still appears partially present. The defect currently blocks the normal handoff from regression `B` to regression `G`.
