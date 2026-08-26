# Kundtjänst - syntetisk menykarta legacy

Detta dokument är en AI-optimerad sammanfattning av menyinventeringen för `https://sps-stage-legacy.europark.local/CustomerService`.

## Källor

- `raw_data\kundtjanst-funktioner-legacy-data.json`
- `raw_data\kundtjanst-funktioner-data.json`
- `syntetisk_data\kundtjanst-menykarta.md`

## Menyvolym

- Kontrakt: 10
- Rapporter: 42
- Garage: 22
- Köhantering: 6
- Nyckelhantering: 3
- Loggar: 4
- Dokument: 1
- Templates: 1
- Admin: 29
- Användarmeny: 2

## Viktig observation

Legacy-portalen är mer drift- och administrationsorienterad än nya stage-portalen. Framför allt är **Garage**-menyn betydligt större, flera STP-funktioner ligger under **Kontrakt**, och flera funktioner som i nya portalen ligger under **Gemensamma inställningar** eller **Produkt** ligger i legacy direkt under **Garage** eller **Admin**.

## Tydliga strukturskillnader mot nya stage

- **Garage är mycket bredare i legacy** med egna funktioner för zoner, platser, fysiska egenskaper, garageadresser, standardvärden, hyresprodukter och tilläggsprodukter.
- **Rapporter är bredare i legacy** och innehåller även operativa listor som `Förvaltarrapport`, `Kundunderhållsrapport`, `Noll-priskontrakt`, `KPI-baserade kontrakt`, `Procenthöjda kontrakt` och `Produkttyper i ett DS`.
- **STP är inte en egen toppmeny i legacy**; `Skapa nytt korttidsavtal` och `Redigera korttidsavtal` ligger under `Kontrakt`.
- **Legacy har en separat Dokument-meny** med `Visa kontraktsdokument`.
- **Templates/Gemensamma inställningar är mindre utbrutna i legacy**; bara `Notification Templates` finns som egen template-meny.

## Legacy-funktioner som är särskilt viktiga

- `Garage\Administrera Område/zoner i ett garage` - DS-styrd administration av zoner och områden.
- `Garage\Administrera platser i ett garage` - platsadministration per DS.
- `Garage\Administrera fysiska egenskaper för platser` - hantering av platsers fysiska attribut.
- `Garage\Aktiva pågående sessioner` - visar pågående uppsättningssessioner som kan fortsättas eller raderas.
- `Köhantering\Standardmallar` - innehåller återanvändbara textmallar för kundimport/köflöden.
- `Dokument\Visa kontraktsdokument` - hämtar kontraktsdokument direkt via kontraktsnummer.
- `Admin\API Response Check` - testverktyg för API-svarstid.
- `Admin\Se dokumentsinformation` - visar dokumentmetadata som sändningsdatum, förfallodatum, OCR och kvar att betala.
- `Admin\SysDaemons` - driftstatus för ett stort antal backendtjänster.

## Stabilitetsobservation jämfört med nya stage

Flera ytor som gav fel i nya stage fungerade i legacy under denna genomgång:

- `CustomerService\UpdateCpi`
- `Garage\BAInformationDS`
- `Key`

Det tyder på att legacy fortfarande innehåller fungerande administrativa flöden som ännu inte är fullt stabila i nya portalen.

## Kända legacy-problem i inventeringen

Vid denna genomgång var de tydliga felen koncentrerade till vissa Power BI-länkar:

- `Rapporter\OP - 1A - Occupancy Rate Repot NEW`
- `Rapporter\SPS- 1F - Kontraktsöversikt med kontaktuppgifter`
- `Rapporter\Report to audit the payments and events from EPMP`
- `Rapporter\OP - 8D - Park & Go Statistik`
- `Rapporter\OP - 8xd - Park & Go beläggningsgrad`
- `Rapporter\OP - 7 - Uppföljning Kontrollavgifter`

## Slutsats

Legacy fungerar som en mer fullmatad operations- och administrationsyta med tyngdpunkt på garageadministration, rapporter och direkta driftverktyg. För framtida dokumentation och testning bör legacy betraktas som särskilt viktig för att förstå äldre men fortfarande fungerande arbetssätt som ännu inte fullt ut har flyttats till nya Kundtjänstportalen.
