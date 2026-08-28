# Summary

| Test | Status | Outcome |
| --- | --- | --- |
| `regression-serviceportal-nytt-kontrakt-migrated-ds` | passed | Migrated DS `47184 | Malmen 14, Möllevångsgatan 42 garage A | Migrated` was found, the web-stage garage details page opened, a saleable product was selected, and checkout loaded with the user still logged in and identification prefilled. |
| `regression-serviceportal-checkout-verify-and-create-contract` | invalidated | Historical observation only. The failure was reproduced on the same DS/checkout and does not satisfy the current requirement to retry the full B -> G flow across at least ten distinct migrated DS candidates before classifying a stage failure as a confirmed regression. See [RegressionError01](RegressionError01/report.md). |
