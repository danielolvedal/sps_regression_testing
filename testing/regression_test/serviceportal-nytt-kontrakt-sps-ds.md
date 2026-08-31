# Regressionstest - serviceportalen nytt kontrakt via SPS-DS

Detta regressionstest verifierar att en användare som redan loggats in via assisted login kan använda DS-routinglistan från `J`, välja ett DS som finns i SPS, söka efter motsvarande parkering i serviceportalen och fortsätta till kontraktsskapandet utan att tappa inloggat läge.

## Test-ID

regression-serviceportal-nytt-kontrakt-sps-ds

## Catalog Key

`K`

## Summary

Start from the logged-in service portal page created by A, use J's DS routing inventory as the SPS-DS source, and verify the new-contract flow for that parking.

## Dependencies

- `A` / `regression-kontrakt-anna-serviceportal-login`
- `J` / `regression-ds-routing-inventory-sps-vs-legacy`

## Typ

Manuellt/shared-browser-test i synlig serviceportal-session med DS-urval från gemensam routinginventering.

## Miljö

- Kundtjänstportalen stage: `https://sps-stage.europark.local/CustomerService`
- Startpunkt: `https://web-stage.europark.local/myaccount/index`
- Förväntad portalmiljö: `web-stage.europark.local`
- DS-routinglista: `raw_data\ds-routing-inventory.json`
- Mänsklig DS-översikt: `syntetisk_data\common\ds-routing-index.md`

## Förutsättningar

- Föregående regression `kontrakt-sok-anna-serviceportal-login.md` ska vara genomförd eller motsvarande assisted login ska vara aktiv. A ger endast den inloggade serviceportal-sessionen.
- Regression `J` ska vara genomförd så att `raw_data\ds-routing-inventory.json` finns och innehåller aktuell DS-routing för stage. J är den styrande förutsättningen för K:s DS-urval.
- Agenten ska ha en delad synlig browser-session där serviceportalen redan är öppen för den aktuella användaren på `https://web-stage.europark.local/myaccount/index`.
- Agenten ska använda DS-kandidater från routinglistan, inte välja kandidater från `Admin -> Migrate DS`.

## Syfte

Verifiera att användaren från sin redan inloggade serviceportalsida kan klicka på `Nytt kontrakt`, välja ett DS som enligt `J` finns i SPS (`routing: "sps-stage"`), använda parkeringsnamnet från listan i serviceportalen och komma vidare i nytt kontrakt-flödet i fortsatt inloggat läge med personnummer förifyllt.

Detta test kompletterar `B`: `B -> G` kontrollerar kontraktsskapande på migrerade siter/DS från `Admin -> Migrate DS`, medan `K -> G` kontrollerar kontraktsskapande på DS som finns i SPS enligt `J`.

## Kandidaturval

Kandidater ska väljas från `raw_data\ds-routing-inventory.json`, alltså output från `J`, med följande filter:

1. `routing` ska vara `sps-stage`.
2. `dsName` ska vara ifyllt och tillräckligt specifikt för att kunna sökas i serviceportalen.
3. Kandidater med tydligt upphörda, testmässiga eller generiska namn ska undvikas om bättre kandidater finns.
4. Kandidater som i tidigare körning har visat köpbar produkt eller ledig plats ska prioriteras.
5. `existsInMigrationReference` och `migrationStatus` får dokumenteras, men får inte styra urvalet för `K`. Styrande signal är `routing: "sps-stage"` från `J`.

Om routinglistan saknas, är äldre än rimligt för aktuell testperiod eller saknar `sps-stage`-kandidater ska `J` köras eller uppdateras innan `K` körs.

## Iterationsregel

Om ett valt SPS-DS inte har någon köpbar produkt eller ledig plats ska testet inte underkännas direkt. I stället ska agenten dokumentera observationen, välja nästa tidigare oprövade `sps-stage`-kandidat från `raw_data\ds-routing-inventory.json` och försöka igen.

Testet ska först markeras som underkänt när:

- flera rimliga `sps-stage`-kandidater har prövats utan att det går att nå den avsedda verifieringspunkten, eller
- ett verkligt regressionsfel observeras, till exempel tappad inloggning, legacy-routing för en kandidat som `J` klassificerat som `sps-stage`, eller saknat förifyllt personnummer.

## Teststeg

1. Utgå från slutläget i test `A`, där användaren redan är inloggad på `https://web-stage.europark.local/myaccount/index`.
2. Öppna `raw_data\ds-routing-inventory.json` och välj första rimliga, tidigare oprövade kandidat med `routing: "sps-stage"`.
3. Dokumentera kandidatens `dsNumber`, `dsName`, `selectedDropdownText`, `landingUrl`, `existsInMigrationReference` och eventuell `migrationStatus`.
4. Klicka på `Nytt kontrakt` i serviceportalen.
5. Använd kandidatens `dsName` som huvudsaklig sökterm i serviceportalens sökfält.
6. Om `dsName` är tomt eller inte ger verifierbar träff ska kandidaten hoppas över och nästa `sps-stage`-kandidat väljas.
7. Identifiera resultatkortet som motsvarar valt DS.
8. Klicka på garaget/parkeringen med rätt namn.
9. Kontrollera att detaljsidan stannar inom `web-stage.europark.local` och inte länkar vidare via `/lgcy/` eller legacy-host.
10. Klicka på `Hyr plats`.
11. Kontrollera om det finns en köpbar produkt eller ledig plats.
12. Om ingen köpbar produkt eller ledig plats finns:
    - dokumentera DS-kandidaten och observationen
    - välj nästa tidigare oprövade `sps-stage`-kandidat från routinglistan
    - upprepa stegen från sökningen i serviceportalen
13. Om en köpbar produkt eller ledig plats finns, välj den.
14. Välj inga tilläggstjänster.
15. Säkerställ att önskat startdatum är idag.
16. Klicka på `Nästa`.
17. Kontrollera att användaren fortfarande är inloggad.
18. Kontrollera att personnummer är förifyllt.

## Förväntat resultat

- Minst ett DS med `routing: "sps-stage"` ska kunna väljas från `raw_data\ds-routing-inventory.json`.
- DS-namnet ska kunna återanvändas som sökterm i serviceportalen.
- Vald parkering ska stanna i nya serviceportal-/stage-miljön och inte routa till legacy.
- Minst en av de prövade `sps-stage`-kandidaterna ska ge en köpbar produkt eller ledig plats, eller så ska avsaknaden dokumenteras som kandidatobservation och testet iterera vidare.
- Användaren ska efter `Nästa` fortfarande vara inloggad.
- Personnummer ska vara förifyllt på nästa steg.

## Slutläge

- Aktiv flik: checkout-sidan i serviceportalen
- URL-mönster: `https://web-stage.europark.local/garage/checkout/{saleId}`
- Detta slutläge är startläget för `G` i kedjan `A -> J -> K -> G`.

## Exekveringsgenvägar

- På `Mitt Parkeringskonto` leder länken `Nytt kontrakt` till startsidan `https://web-stage.europark.local/`.
- Sökfältet på startsidan är `addressSearch` och sökknappen är `searchButton`.
- Läs kandidater maskinellt från `raw_data\ds-routing-inventory.json` när möjligt och använd `syntetisk_data\common\ds-routing-index.md` för snabb manuell översikt.
- Serviceportalens sökterm ska i första hand vara `dsName`. `dsNumber` ska inte användas som enda sökterm om inte testaren uttryckligen verifierar att serviceportalen stöder det för aktuell kandidat.
- Om flera liknande resultat visas i serviceportalen ska valet matchas mot `dsName` och, när möjligt, mot informationen i `selectedDropdownText` från routinglistan.
- Kandidater med `landingUrl` under `https://sps-stage.europark.local/CustomerService/CreateNewContractStep2` är prioriterade eftersom `J` redan har verifierat att de stannar i SPS i Kundtjänstflödet.

## Tekniska observationer

- Valet av DS är en explicit del av testet och ska dokumenteras i varje körning.
- Testet ska utgå från `routing: "sps-stage"` i `J`:s output, inte från `Admin -> Migrate DS`.
- `Admin -> Migrate DS` är bara referensdata i detta test och får inte användas för att filtrera bort DS som är upplagda direkt i SPS.
- Ingen produkt till försäljning är i sig inte ett regressionsfel; det kan vara en konfigurationsfråga på det specifika DS:t.
- Om en kandidat som `J` klassificerat som `sps-stage` ändå routar till `/lgcy/` eller legacy-host i serviceportalen ska observationen dokumenteras som potentiell routingregression eller skillnad mellan Kundtjänstflöde och serviceportalflöde.

## Felutfall

Testet ska markeras som underkänt om något av följande inträffar:

- `raw_data\ds-routing-inventory.json` saknas eller saknar användbara `sps-stage`-kandidater
- ingen verifierbar resultatpost i serviceportalen motsvarar rimliga `sps-stage`-kandidater
- `Nytt kontrakt` tappar den inloggade användarsessionen
- vald parkering routas till legacy/annan host trots att `J` klassificerat DS som `sps-stage`
- flera rimliga `sps-stage`-kandidater saknar köpbar produkt eller ledig plats och testet kan därför inte nå verifieringspunkten
- `Nästa` inte kan genomföras i rätt inloggat läge
- personnummer inte är förifyllt på nästa steg

## Bevis / dokumentation

Dokumentera minst:

- path och `capturedAt` för den DS-routinglista som användes
- vilket DS som valdes från `raw_data\ds-routing-inventory.json`
- kandidatens `routing`, `landingUrl`, `existsInMigrationReference` och eventuell `migrationStatus`
- vilken serviceportal-sökterm som användes
- om kandidaten saknade köpbar produkt eller ledig plats
- vilken start-URL som användes
- vilket garage- eller parkeringskort som valdes
- vilken detalj-URL som öppnades
- om användaren fortfarande var inloggad
- om personnummer var förifyllt

## Senast verifierad körning

- **Datum:** Ej verifierad efter skapande.
- **Körläge:** Learning Mode
- **Status:** Testdefinition skapad för kedjan `A -> J -> K -> G`.

## Relaterade dokument

- `testing\regression_test\kontrakt-sok-anna-serviceportal-login.md`
- `testing\regression_test\ds-routing-inventory-sps-vs-legacy.md`
- `testing\regression_test\serviceportal-checkout-verifiering-och-skapa-kontrakt.md`
- `testing\regression_test\regression-test-catalog.md`
- `tools\docs\regressionstest-arbetsmodell.md`
- `tools\docs\browser-samarbete-stage-session.md`
