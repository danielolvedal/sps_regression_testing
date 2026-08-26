# Non-migrated DS routes to legacy details

## Status

`verified`

## Affected Environment

- Customer Service Stage: `https://sps-stage.europark.local/Migration`
- Service Portal Stage: `https://web-stage.europark.local/`
- Observed legacy target: `https://hyra-legacy-stage.europark.local/`

## Related Test Case

- `regression-serviceportal-nytt-kontrakt-non-migrated-ds`
- Catalog key: `C`

## Summary

The non-migrated DS candidate `900540 | Spiran 9, S:t Persgatan 95 | Not Migrated` can be found in `Admin -> Migrate DS`, but the matching service-portal result routes into the legacy rental host instead of staying in the intended stage purchase flow.

## Reproduction Steps

1. Complete test `A` and reach the logged-in page `https://web-stage.europark.local/myaccount/index`.
2. Open `Admin -> Migrate DS` in Customer Service Stage.
3. Search for DS `900540` and confirm `Spiran 9, S:t Persgatan 95` has status `Not Migrated`.
4. In the service portal, start `Nytt kontrakt`.
5. Search for `Spiran 9, S:t Persgatan 95`.
6. Observe the matching result entry and continue into the result.

## Actual Result

- The matching result exposes the route `https://web-stage.europark.local/lgcy/garage/details/4d19a78b-9c55-451c-8a6c-1a7070fddd17`.
- Click-through navigation lands on `https://hyra-legacy-stage.europark.local//garage/details/4d19a78b-9c55-451c-8a6c-1a7070fddd17`.

## Expected Result

The selected non-migrated DS should remain within the supported stage flow needed by regression test `C`, without routing into the legacy rental host.

## Reproducibility

- **Number of runs:** `3`
- **Same outcome each time:** `yes`
- **Notes:** The same DS candidate and the same search term were used in all three reproductions.

## Technical Observations

- Customer Service Stage consistently showed the DS row as `900540 | Spiran 9, S:t Persgatan 95 | Not Migrated`.
- The service-portal result remained discoverable, but the route itself was legacy-oriented.
- This is distinct from the allowed “no saleable product” iteration case because the failure occurs before product validation.

## Evidence and Artifacts

- Screenshots:
  - `screenshot-01.png`
- URLs:
  - `https://sps-stage.europark.local/Migration`
  - `https://web-stage.europark.local/garage/map?lat=58.5866165&lng=16.1885895&pageNum=1&pageSize=4`
  - `https://web-stage.europark.local/lgcy/garage/details/4d19a78b-9c55-451c-8a6c-1a7070fddd17`
  - `https://hyra-legacy-stage.europark.local//garage/details/4d19a78b-9c55-451c-8a6c-1a7070fddd17`
- Other:
  - Reproduced within regression run `20260826v1`

## Recommendation to Developers

Review how non-migrated DS search results are mapped in the stage service portal and remove the legacy fallback for candidates that are expected to participate in the current contract-purchase flow.
