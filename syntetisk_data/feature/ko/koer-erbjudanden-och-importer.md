# Koer, erbjudanden och importer

## Dokument-ID

koer-erbjudanden-och-importer

## Syfte

Beskriver hur kunder placeras i kö, hur erbjudanden hanteras och hur manuella eller automatiska importflöden verkar fungera.

## Status

Initial syntetisk modell.

## Scope / avgränsning

Omfattar kölistor, kömedlemmar, erbjudanden, kundimport och standardmallar.

## Källor

- `raw_data\kundtjanst-funktioner-data.json`
- `raw_data\kundtjanst-funktioner-legacy-data.json`
- `raw_data\SPS Funktionsträd.txt`
- `raw_data\SPS_function_spec_en.xlsx`
- `raw_data\Uthyrning Upplärning.docx`

## Relaterade dokument

- `lifecycle\kontraktets-livscykel.md`
- `feature\kontrakt\uppsagning-och-avslut.md`

## Funktioner i scope

- `Köhantering\Visa alla köande`
- `Köhantering\Alla ködeltagare` (stage)
- `Köhantering\Visa kö för garage`
- `Köhantering\Sök kö för användare` (stage)
- `Köhantering\Visa erbjudanden`
- `Köhantering\Automatisk kundimport`
- `Köhantering\Lägg till kund i kölista` (legacy)
- `Köhantering\Standardmallar` (legacy)

## Hur området fungerar

Köhanteringen verkar vara en central motor för att fylla lediga platser. Systemet kan visa köer per garage, individuella kömedlemmar och skapade erbjudanden. Legacy-materialet visar dessutom mallar för kundkommunikation vid kö-/importflöden.

## Primära arbetsflöden

1. Lägg till kund i kö eller importera kunder
2. Följ köposition och kontaktdata
3. Skapa erbjudande när plats blir tillgänglig
4. Följ accept/avslag/utgång
5. Efter uppsägning: kontrollera kölista och kontakta nästa kund

## Data, objekt och regler

- Q-kontrakt representerar väntande kunder enligt funktionsspecen
- köposter verkar vara kopplade till DS, garage eller specifik produkt/plats
- standardmallar i legacy antyder mallstyrd kommunikation för import och erbjudande

## UI, menyer och navigering

Stage har mer utbruten vy för kömedlemmar och användarsökning. Legacy har i stället tydligare manuell köläggning och standardmallar i samma område.

## Integrationer och beroenden

- e-post/SMS-kommunikation
- kontraktsskapande när erbjudande accepteras
- importkällor (`Ej verifierat`)

## Valideringar, fel och edge cases

- olika miljöer har olika menystruktur för samma område
- erbjudande- och importstatus behöver sannolikt följas i flera steg
- `Ej verifierat`: exakt affärsregel för prioritering och utgångstid

## Bilder och visuellt underlag

Saknas. Bör kompletteras med kölista, erbjudandevy och legacy-standardmallar.

## Kunskapsluckor / ej verifierat

- fullständig modell för köprioritet och regler
- detaljerna i automatisk kundimport

## Öppna frågor

- Ska standardmallarna brytas ut till eget syntetiskt dokument för kökommunikation?
