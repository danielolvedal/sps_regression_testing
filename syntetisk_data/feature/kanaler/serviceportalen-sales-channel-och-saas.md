# Serviceportalen, sales channel och SaaS

## Dokument-ID

serviceportalen-sales-channel-och-saas

## Syfte

Samlar den kundnära kanalbilden: hyra.apcoa.se, serviceportalen, digitala tillstånd och SaaS-/företagsupplägg.

## Status

Initial syntetisk modell med starkt dokumentunderlag men begränsad live-UI-verifiering.

## Scope / avgränsning

Omfattar främst externa/manualbaserade kanaler snarare än enbart CSC-menyerna.

## Källor

- `raw_data\251203 Manual Hyra.apcoa.se.docx`
- `raw_data\Serviceportalen Digitala tillstånd guide .pdf`
- `raw_data\SPS Funktionsträd – Komplett System.txt`
- `raw_data\SAAS services.txt`
- `raw_data\System & länkar.xlsx`

## Relaterade dokument

- `feature\kontrakt\skapa-kontrakt.md`
- `feature\nycklar\nycklar-access-och-anpr.md`
- `feature\organisation\kunder-fastighetsagare-cps-tps.md`

## Funktioner i scope

- hyra.apcoa.se
- Mina sidor / serviceportal
- digitala tillstånd
- SaaS-/B2B-upplägg

## Hur området fungerar

Hyra.apcoa.se-manualen beskriver ett digitalt kundflöde där användaren söker plats, väljer parkeringsform, skapar kontrakt och därefter använder Mina sidor för förvaltning. Funktionsträden beskriver samtidigt SaaS-scenarier där företag själva hanterar avisering i egna system medan SPS används som kontrakts- och fordonsmotor.

## Primära arbetsflöden

1. Kund söker plats eller erbjudande digitalt
2. Kund skapar kontrakt eller ställer sig i kö
3. Kund får kontrakt/inloggningsuppgifter
4. Kund hanterar tillstånd, avisering och köstatus via portal
5. I SaaS/B2B-scenarier används SPS som underliggande motor snarare än full kundportal

## Data, objekt och regler

- digitala kanaler använder kunduppgifter, platsdata, VRM och aviseringsval
- digitala tillstånd och digitala nycklar verkar kopplas till portalflöden
- SaaS-materialet är ännu svagt och bör behandlas som preliminärt

## UI, menyer och navigering

Ej fullständigt verifierat live i denna session. Underlaget är främst dokumentbaserat.

## Integrationer och beroenden

- BankID
- e-post
- Serviceportalen
- eventuella företags-/hyressystem i SaaS-fall

## Valideringar, fel och edge cases

- vissa portalregler kan vara kundtyp- eller anläggningsspecifika
- SaaS-materialet i `SAAS services.txt` är samtalsbaserat och inte tillräckligt som ensam källa

## Bilder och visuellt underlag

Saknas strukturerat. Bör kompletteras med skärmbilder från hyra.apcoa.se och serviceportalens huvudflöden.

## Kunskapsluckor / ej verifierat

- detaljerna i serviceportalens digitala tillståndsflöde
- full SaaS-objektmodell och ansvarsfördelning

## Öppna frågor

- Ska externa kanaler dokumenteras i separata syntetiska träd per målgrupp?
