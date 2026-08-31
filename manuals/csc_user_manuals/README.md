# CSC-manualer

Detta bibliotek innehåller färdiga manualer för Kundtjänst/CSC som bygger på `syntetisk_data` och kompletterar den mer tekniska menyinventeringen i `Kundtjänst - funktioner.md`.

## Läsordning

1. `Kundtjänst - kontrakt och avtal.md`
2. `Kundtjänst - köer, uppsägning och kundflöden.md`
3. `Kundtjänst - anläggningar, produkter och access.md`
4. `Kundtjänst - rapporter, loggar och administration.md`
5. `Kundtjänst - funktioner.md` vid behov av meny-för-meny-uppslag

## Manualerna i paketet

| Manual | Huvudfokus | Primära syntetiska källor |
| --- | --- | --- |
| `Kundtjänst - kontrakt och avtal.md` | Skapa, söka, ändra, prissätta och dokumentera kontrakt | `syntetisk_data\lifecycle\kontraktets-livscykel.md`, `syntetisk_data\feature\kontrakt\*.md` |
| `Kundtjänst - köer, uppsägning och kundflöden.md` | Köer, erbjudanden, uppsägning, efterarbete och kundnära kanalflöden | `syntetisk_data\feature\ko\koer-erbjudanden-och-importer.md`, `syntetisk_data\feature\kontrakt\uppsagning-och-avslut.md`, `syntetisk_data\feature\kanaler\serviceportalen-sales-channel-och-saas.md` |
| `Kundtjänst - anläggningar, produkter och access.md` | DS, garage, produkter, paket, nycklar, VRM och access | `syntetisk_data\feature\garage\garage-ds-setup-och-platser.md`, `syntetisk_data\feature\produkter\produkter-paket-och-tillstandstider.md`, `syntetisk_data\feature\nycklar\nycklar-access-och-anpr.md`, `syntetisk_data\feature\kontrakt\vrm-och-kontraktsdokument.md` |
| `Kundtjänst - rapporter, loggar och administration.md` | Rapporter, audit, drift, masterdata och tvärgående regler | `syntetisk_data\feature\rapporter\rapporter-och-powerbi.md`, `syntetisk_data\feature\loggar\loggar-audit-och-drift.md`, `syntetisk_data\feature\organisation\kunder-fastighetsagare-cps-tps.md`, `syntetisk_data\crosscutting\juridik-efterlevnad-ekonomi-och-integrationer.md` |

## Viktigt om verifieringsgrad

- Manualerna använder svenska normaliserade rubriker men nämner verkliga UI-namn när de behövs för igenkänning.
- Där underlaget ännu inte är fullständigt live-verifierat markeras detta uttryckligen som `Ej fullverifierat`.
- `Kundtjänst - funktioner.md` är fortsatt bästa uppslagskälla när exakt menytext, URL eller stage-status behöver bekräftas.

## Relaterade dokument

- `manuals\csc_user_manuals\Kundtjänst - funktioner.md`
- `syntetisk_data\index.md`
- `syntetisk_data\common\ordlista-och-namnstandard.md`
