# Customer Service Center English Translation Consistency Failure

## Status

Failed, verified through three reproductions with the same outcome.

## Affected environment

- Customer Service Center stage
- Base URL: `https://sps-stage.europark.local/CustomerService`
- Shared browser: visible Edge session on remote debugging port `9222`
- Baseline menu data: `raw_data\kundtjanst-funktioner-data.json`
- Baseline `capturedAt`: `2026-08-26T09:19:00`

## Related test case

`testing\regression_test\kundtjanst-english-translation-consistency.md`

## Summary

The Customer Service Center stage UI is not consistently translated to English. The run inspected all 12 menu groups, 115 menu items and 115 opened pages from the current navigation baseline. The same failure pattern was reproduced in three live inventory runs: Swedish menu labels, Swedish page headings, Swedish field labels, Swedish button text, Swedish table text, and mixed Swedish/English terminology remain visible throughout CSC.

No pages were blocked or unreachable during the third reproduction.

## Reproduction steps

1. Start or reuse the shared stage browser with `.\runtime\start-collaborative-stage-browser.ps1`.
2. Open `https://sps-stage.europark.local/CustomerService`.
3. Confirm that the Customer Service Center stage page is loaded in the shared browser session.
4. Run the live menu and page inventory to a temporary output file, without writing to `raw_data`.
5. Repeat the inventory two more times from the Customer Service Center start page.
6. Compare visible navigation labels and first-render page UI text against the expected English-only and canonical-terminology rules in test H.

## Actual result

The UI contains untranslated Swedish and mixed-language text in navigation and first-rendered pages. The third reproduction produced 2,095 untranslated or mixed UI findings. The complete finding list is stored in `untranslated-and-mixed-ui-findings.csv`.

| Menu group | Menu items inspected | Menu text findings | Page text findings | Blocked pages |
| --- | ---: | ---: | ---: | ---: |
| Admin | 31 | 17 | 726 | 0 |
| Daniel Olvedal | 2 | 0 | 22 | 0 |
| Garage | 7 | 6 | 155 | 0 |
| Gemensamma inställningar | 8 | 6 | 204 | 0 |
| Kontrakt | 8 | 8 | 247 | 0 |
| Köhantering | 6 | 7 | 178 | 0 |
| Loggar | 4 | 3 | 98 | 0 |
| Nyckelhantering | 3 | 1 | 46 | 0 |
| Produkt | 4 | 3 | 107 | 0 |
| Rapporter | 34 | 20 | 0 | 0 |
| STP-tjänster | 5 | 5 | 147 | 0 |
| Templates | 3 | 2 | 87 | 0 |

Representative examples:

| Location | Observed text | Recommended English term |
| --- | --- | --- |
| Navigation group | `Kontrakt` | `Contract` |
| Navigation item | `Sök` | `Search` |
| Navigation item | `Sätt upp nytt kontrakt` | `Create new contract` |
| Navigation group | `STP-tjänster` | `Short-term parking services` |
| Navigation item | `Översiktlig statistik för engångsparkering` | `One-time parking overview statistics` |
| Navigation group | `Rapporter` | `Reports` |
| Navigation item | `SPS - 1C - Kölista och Lediga platser` | `SPS - 1C - Queue list and available spaces` |
| Navigation group | `Köhantering` | `Queue management` |
| Navigation item | `Automatisk kundimport` | `Automatic customer import` |
| Page heading | `Sök efter användare` | `Search for user` |
| Page field | `Välj ett DS-nummer` | `Select DS number` |
| Page button | `Nästa steg` | `Next step` |

Terminology conflicts were also observed. The complete conflict table is stored in `term-conflicts.csv`.

| Concept | Observed variants | Recommended canonical term |
| --- | --- | --- |
| Customer Service Center | `Kundtjänstportalen`; `CustomerService` | `Customer Service Center` |
| Contract | `Kontrakt`; `contract`; contract-related Swedish labels | `Contract` |
| Short-term parking contract | `STP-tjänster`; `korttidsavtal`; `engångsparkering`; `Receptionsservice kontrakt` | `Short-term parking contract` |
| DS / Car park / Garage | `DS`; `garage`; `Garage`; `CarPark`; `Car park` | `DS / Car park`, or `Garage` only for an actual garage object |
| VRM | `VRMer`; `VRM-pool` | `VRM` |
| Queue | `Köhantering`; `köande`; `ködeltagare`; `Queue Tick Tack Toe` | `Queue`, `Queue member`, `Offer` |
| Product template | `Produktmall`; `Paketmallar`; `Product Template List`; `Package` | `Product template`, `Package template` |
| Property owner / Landlord / Operator | `Fastighetsägare`; `Hyresvärd`; `Operatör`; English variants | `Property owner`, `Landlord`, `Operator` |

## Expected result

All visible static Customer Service Center UI labels in navigation and opened pages should be in English, and comparable business concepts should use the same canonical English term consistently.

## Reproducibility

Reproduced 3/3 times on 2026-08-28:

| Run | Evidence file | Outcome |
| --- | --- | --- |
| 1 | `live-inventory-r1.json` | Failed with untranslated Swedish and mixed terminology |
| 2 | `live-inventory-r2.json` | Failed with the same untranslated Swedish and mixed terminology pattern |
| 3 | `live-inventory-r3.json` | Failed with the same untranslated Swedish and mixed terminology pattern |

## Technical observations

- The live navigation matched the expected scale from the raw baseline: 12 menu groups and 115 menu items were available for inspection.
- No business-data mutation actions were submitted. Pages with potentially mutating actions were only opened and inspected in their first rendered state.
- No inspected page was blocked by login or an unreachable URL in the third reproduction.
- The inventory script leaves the active tab on the last inspected page, so each reproduction should reopen `https://sps-stage.europark.local/CustomerService` before starting the next run.

## Evidence and artifacts

- `live-inventory-r1.json`
- `live-inventory-r2.json`
- `live-inventory-r3.json`
- `untranslated-and-mixed-ui-findings.csv`
- `term-conflicts.csv`

## Recommendation to developers

Treat this as a broad localization and terminology consistency defect. Start with the navigation/menu resource layer because it exposes the largest visible mismatch immediately, then align shared page titles, form labels, button text and table copy to the canonical English terminology defined by test H. After the navigation and shared resources are corrected, rerun the full test to identify remaining page-specific translation gaps.
