# Regression summary

| Test | Status | Outcome |
| --- | --- | --- |
| `regression-ds-routing-inventory-sps-vs-legacy` | passed | Collected 8,211 raw dropdown rows from the SPS Customer Service DS autocomplete, deduplicated them into 2,348 unique DS entries, and classified all entries through Create New Contract step 1: 136 route to SPS-stage, 2,212 route to legacy-stage, 0 were not found, and 0 were blocked. The machine-readable inventory is `raw_data\ds-routing-inventory.json`; the human-readable index is `syntetisk_data\common\ds-routing-index.md`. |
