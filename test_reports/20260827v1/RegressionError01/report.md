# Invalidated Checkout Cannot Create Contract for Migrated DS Sale Report

## Status

invalidated as a confirmed regression report under the current G-test definition. The observation remains historically useful, but it was reproduced on the same DS/checkout and does not satisfy the updated requirement to retry the full B -> G flow across at least ten distinct migrated DS candidates.

## Affected environment

- Service portal stage: `https://web-stage.europark.local`
- SPS stage: `https://sps-stage.europark.local`
- Shared browser debug port: `9222`

## Related test case

- `regression-serviceportal-checkout-verify-and-create-contract` (Catalog Key `G`)
- Dependency: `regression-serviceportal-nytt-kontrakt-migrated-ds` (Catalog Key `B`)

## Summary

The checkout page for sale `97570ef4-700a-4f84-a931-019e01442f32` loaded with the expected customer and product data, but it was not possible to create the contract. The page rendered a monthly total as `SEK NaN/månad inkl. moms`, the `NotificationMethodPackageId` dropdown had zero options, no service/setup fee was visibly itemized, and every create attempt returned the validation error `CustomerModel.PhoneNumber har ett felaktigt värde`.

Under the current G-test rules, this evidence is insufficient to prove a system regression in stage because only one migrated DS candidate was used. A valid current report must include a candidate log for at least ten distinct migrated DS candidates, preferably including Akka garages when available, unless the run is explicitly marked as blocked due to insufficient candidates.

## Reproduction steps

1. Start from the checkout reached by regression B: `https://web-stage.europark.local/garage/checkout/97570ef4-700a-4f84-a931-019e01442f32`.
2. Compare customer data against SPS contract `H-47184-000025049` in `EditContract/Overview`.
3. Observe checkout pricing and notification method controls.
4. Accept the APCOA terms and click `Skapa kontrakt`.
5. Dismiss the error dialog and repeat the create action until the same outcome has been observed three times.

## Actual result

- Customer data was prefilled and matched SPS: `740130-0608`, `Anna Walldén`, `annawallden.74@gmail.com`, `0730 91 41 65`, address `Lüneburgska vägen 1B`, `23940 Falsterbo`, country `SE/Sweden`.
- Product summary initially matched regression B: `Oreserverad plats, Dygnet runt, Nyttotillstånd` at `SEK 530 / månad inkl. moms` for `Malmen 14, Möllevångsgatan 42 garage A`.
- Rendered total showed `Totalt att betala per månad: SEK NaN/månad inkl. moms`.
- `NotificationMethodPackageId` contained `0` selectable options.
- No separate visible service/setup fee could be verified.
- After clicking `Skapa kontrakt`, the browser remained in checkout at `https://web-stage.europark.local/garage/checkout` and displayed `Fel format` / `CustomerModel.PhoneNumber har ett felaktigt värde`.

## Expected result

Checkout should show numeric totals, expose at least one notification method, clearly account for fees, accept the prefilled phone number or normalize it, and navigate to a confirmation page after `Skapa kontrakt`.

## Reproducibility

Reproduced three times on 2026-08-27 in the same checkout session. Each attempt retained the same hidden `SaleId`, kept `SEK NaN` and zero notification methods, and returned `CustomerModel.PhoneNumber har ett felaktigt värde` after submit.

## Technical observations

- Initial checkout URL: `https://web-stage.europark.local/garage/checkout/97570ef4-700a-4f84-a931-019e01442f32`.
- Post-submit URL: `https://web-stage.europark.local/garage/checkout`.
- Hidden values included `GaragePrice=530`, `InvoicePrice=0`, `OnlineFee=0`, `TotalPrice=530`, `GrandTotal=530`, and `ContractStartDate=2026-08-27 00:00:00`.
- The phone value was prefilled as `0730 91 41 65`, matching the SPS hidden `CustomerPhoneNumber` value.

## Evidence and artifacts

- Screenshot: `checkout-phone-error.png`
- SPS contract: `H-47184-000025049`
- DS candidate: `47184 | Malmen 14, Möllevångsgatan 42 garage A | Migrated`

## Recommendation to developers

Investigate checkout model binding and validation for migrated DS sales. Prioritize the notification-method population, total-price calculation that produces `NaN`, fee rendering, and phone-number validation/normalization because they jointly block contract creation despite valid prefilled SPS customer data.
