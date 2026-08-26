# Kundtjänst - syntetisk menykarta

Detta dokument är en AI-optimerad sammanfattning av Kundtjänstportalens menyinventering.

## Källor

- `raw_data\kundtjanst-funktioner-data.json`
- `manuals\csc_user_manuals\Kundtjänst - funktioner.md`

## Menyvolym

- Kontrakt: 8
- STP-tjänster: 5
- Rapporter: 34
- Garage: 7
- Produkt: 4
- Köhantering: 6
- Nyckelhantering: 3
- Loggar: 4
- Gemensamma inställningar: 8
- Templates: 3
- Admin: 31
- Användarmeny: 2

## Viktig observation

Admin-ytan är den största och mest varierade delen av systemet. Rapporter består huvudsakligen av Power BI-länkar, medan Kontrakt, Garage, Köhantering och Loggar innehåller tydliga arbetsvyer för daglig handläggning.

## Kända stage-problem i inventeringen

- Flera Power BI-länkar saknade giltig rapportkoppling.
- `Garage\BAInformationDS` gav serverfel.
- `Key` gav serverfel.
- `CustomerService\UpdateCpi` gav serverfel.
- `Scheduler` gav serverfel.
- `Migration` laddade inte garage-data.
- extern `Queue Import` gick inte att nå.
- `CPS\FileImportList` gav 404.
