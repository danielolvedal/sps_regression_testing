# Summary

| Test | Status | Outcome |
| --- | --- | --- |
| `regression-serviceportal-nytt-kontrakt-migrated-ds` | passed | Migrated DS `47184 | Malmen 14, Möllevångsgatan 42 garage A | Migrated` was found, the web-stage garage details page opened, a saleable product was selected, and checkout loaded with the user still logged in and identification prefilled. |
| `regression-serviceportal-checkout-verify-and-create-contract` | failed | Checkout customer data matched the SPS contract/address source, but checkout rendered `SEK NaN`, had no notification method options, did not visibly show a service/setup fee, and contract creation was blocked by `CustomerModel.PhoneNumber har ett felaktigt värde`. See [RegressionError01](RegressionError01/report.md). |
