# Checkout renders invalid pricing and no notification method

## Status

`verified`

## Affected Environment

- Customer Service Stage: `https://sps-stage.europark.local/EditContract/Overview`
- Service Portal Stage checkout: `https://web-stage.europark.local/garage/checkout/{saleId}`

## Related Test Case

- `regression-serviceportal-checkout-verify-and-create-contract`
- Catalog key: `G`

## Summary

After the migrated DS flow reaches checkout, the page shows the selected product and customer data correctly, but the payment summary renders `SEK NaN/månad inkl. moms` and the notification method dropdown is empty. This breaks the checkout verification expected by regression test `G`.

## Reproduction Steps

1. Complete test `A` and log in as the assisted user.
2. Complete test `B` with migrated DS `47184 | Malmen 14, Möllevångsgatan 42 garage A | Migrated`.
3. Select `Oreserverad plats, Dygnet runt, Nyttotillstånd`.
4. Continue to checkout.
5. Compare the checkout data with Customer Service Stage `EditContract`.
6. Inspect the payment summary and the notification method dropdown.

## Actual Result

- Checkout prefilled the user information for `Anna Walldén`.
- The selected product was shown as `Oreserverad plats, Dygnet runt, Nyttotillstånd` with `SEK 530 / månad inkl. moms`.
- The summary line `Totalt att betala per månad` rendered as `SEK NaN/månad inkl. moms`.
- The dropdown `NotificationMethodPackageId` contained `0` selectable options.
- No clearly presented service/setup fee could be verified on the page.

## Expected Result

Checkout should render valid numeric totals, expose at least one notification method, and clearly present the fee breakdown required to verify the first payment and ongoing monthly cost before contract creation.

## Reproducibility

- **Number of runs:** `3`
- **Same outcome each time:** `yes`
- **Notes:** Verified on sale IDs `7bfe2d4d-3833-4397-bfbd-3a35e793d352`, `0974ca34-8d9f-4754-b46b-f7c4ffefb630`, and `931e2046-ac53-4f04-95de-a040089001ce`.

## Technical Observations

- Customer data matched the available Customer Service data:
  - identification number `740130-0608`
  - name `Anna Walldén`
  - email `annawallden.74@gmail.com`
  - phone `0730 91 41 65`
  - billing address `Lüneburgska vägen 1B`, `23940 Falsterbo`, `SE/Sweden`
- A follow-up create-contract attempt returned the browser to `https://web-stage.europark.local/garage/checkout` without a confirmation page, but that behavior was not separately triple-verified.

## Evidence and Artifacts

- Screenshots:
  - `screenshot-01.png`
- URLs:
  - `https://sps-stage.europark.local/EditContract/Overview?contractId=H-47184-000025049`
  - `https://web-stage.europark.local/garage/checkout/7bfe2d4d-3833-4397-bfbd-3a35e793d352`
  - `https://web-stage.europark.local/garage/checkout/0974ca34-8d9f-4754-b46b-f7c4ffefb630`
  - `https://web-stage.europark.local/garage/checkout/931e2046-ac53-4f04-95de-a040089001ce`
- Other:
  - Reproduced within regression run `20260826v1`

## Recommendation to Developers

Investigate the checkout pricing calculation and notification-method data binding for the migrated DS purchase flow before relying on the current stage checkout as a valid contract-creation regression target.
