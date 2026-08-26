# Regressionstest - serviceportalen nytt kontrakt via migrated DS

Detta regressionstest verifierar att en användare som redan loggats in via assisted login kan identifiera ett migrerat DS i adminflödet, söka efter motsvarande parkeringsnamn i serviceportalen och fortsätta till kontraktsskapandet utan att tappa inloggat läge.

## Test-ID

regression-serviceportal-nytt-kontrakt-migrated-ds

## Catalog Key

`B`

## Summary

Start from the logged-in service portal page created by A, click Nytt kontrakt, then find a migrated DS through Admin -> Migrate DS and verify the new-contract flow for that parking.

## Dependencies

- `A` / `regression-kontrakt-anna-serviceportal-login`

## Typ

Manuellt/shared-browser-test i synlig serviceportal-session.

## Miljö

- Kundtjänstportalen stage: `https://sps-stage.europark.local/CustomerService`
- Startpunkt: `https://web-stage.europark.local/myaccount/index`
- Förväntad portalmiljö: `web-stage.europark.local`

## Förutsättningar

- Föregående regression `kontrakt-sok-anna-serviceportal-login.md` ska vara genomförd eller motsvarande assisted login ska vara aktiv.
- Agenten ska ha en delad synlig browser-session där serviceportalen redan är öppen för den aktuella användaren på `https://web-stage.europark.local/myaccount/index`.
- Agenten ska kunna gå tillbaka till Kundtjänstportalen i samma delade session för att läsa `Admin -> Migrate DS`.

## Syfte

Verifiera att användaren från sin redan inloggade serviceportalsida kan klicka på `Nytt kontrakt`, identifiera ett DS med migration status `Migrated`, använda parkeringsnamnet från det DS:t i serviceportalen och komma vidare i nytt kontrakt-flödet i fortsatt inloggat läge med personnummer förifyllt.

## Iterationsregel

Om ett valt DS inte har någon köpbar produkt eller ledig plats ska testet inte underkännas direkt. I stället ska agenten dokumentera observationen, gå tillbaka till `Admin -> Migrate DS`, välja en ny kandidat med status `Migrated` och försöka igen.

Testet ska först markeras som underkänt när:

- flera rimliga `Migrated`-kandidater har prövats utan att det går att nå den avsedda verifieringspunkten, eller
- ett verkligt regressionsfel observeras, till exempel tappad inloggning, legacy-routing eller saknat förifyllt personnummer.

## Teststeg

1. Utgå från slutläget i test `A`, där användaren redan är inloggad på `https://web-stage.europark.local/myaccount/index`.
2. Klicka på `Nytt kontrakt`.
3. Gå tillbaka till Kundtjänstportalen.
4. Öppna `Admin -> Migrate DS`.
5. Sök fram ett DS med migration status `Migrated`.
6. Läs av DS-namnet i formatet `[nummer] [NAMN]`.
7. Extrahera endast delen efter det inledande numret och använd bara `NAMN` som sökterm.
8. Gå tillbaka till serviceportalfliken för nytt kontrakt.
9. Sök parkering på det extraherade `NAMN`-värdet.
10. Identifiera resultatkortet som motsvarar det DS som valdes i `Migrate DS`.
11. Klicka på garaget/parkeringen med rätt namn.
12. Klicka på `Hyr plats`.
13. Kontrollera om det finns en köpbar produkt eller ledig plats.
14. Om ingen köpbar produkt eller ledig plats finns:
    - dokumentera DS-kandidaten och observationen
    - gå tillbaka till `Admin -> Migrate DS`
    - välj en annan kandidat med status `Migrated`
    - upprepa stegen från sökningen i serviceportalen
15. Om en köpbar produkt eller ledig plats finns, välj den.
16. Välj inga tilläggstjänster.
17. Säkerställ att önskat startdatum är idag.
18. Klicka på `Nästa`.
19. Kontrollera att användaren fortfarande är inloggad.
20. Kontrollera att personnummer är förifyllt.

## Förväntat resultat

- Ett DS med migration status `Migrated` ska kunna väljas i `Admin -> Migrate DS`.
- DS-namnet ska kunna återanvändas som sökterm i serviceportalen när den inledande siffran utelämnas.
- Flödet ska stanna inom rätt serviceportal-/stage-miljö.
- Minst en av de prövade `Migrated`-kandidaterna ska ge en köpbar produkt eller ledig plats, eller så ska avsaknaden dokumenteras som kandidatobservation och testet iterera vidare.
- Användaren ska efter `Nästa` fortfarande vara inloggad.
- Personnummer ska vara förifyllt på nästa steg.

## Slutläge

- Aktiv flik: checkout-sidan i serviceportalen
- URL-mönster: `https://web-stage.europark.local/garage/checkout/{saleId}`
- Detta slutläge är startläget för `G`

## Exekveringsgenvägar

- På `Mitt Parkeringskonto` leder länken `Nytt kontrakt` till startsidan `https://web-stage.europark.local/`.
- Sökfältet på startsidan är `addressSearch` och sökknappen är `searchButton`.
- I `Admin -> Migrate DS` ska sökningen först användas för att hitta kandidater med rätt migration status innan serviceportalflödet fortsätter.
- Sökfältet i `Admin -> Migrate DS` är DataTables-fältet `input[type="search"][aria-controls="tblMigration"]`.
- När DS visas som `[nummer] [NAMN]` ska bara `NAMN` användas i serviceportalens sökfält, inte numret.
- Om flera liknande resultat visas i serviceportalen ska valet matchas mot namnet från `Migrate DS`, inte mot en godtycklig träff.
- Verifierad kandidat 2026-08-26: `47184 | Malmen 14, Möllevångsgatan 42 garage A | Migrated`.

## Tekniska observationer

- Valet av DS är nu en explicit del av testet och ska dokumenteras i varje körning.
- Testet ska utgå från att `Migrated` är den styrande signalen i adminvyn, inte från ett hårdkodat objektnamn.
- Ingen produkt till försäljning är i sig inte ett regressionsfel; det kan vara en konfigurationsfråga på det specifika DS:t.
- Verifierad observation 2026-08-26: `Malmen 14, Möllevångsgatan 42 garage A` använde `web-stage`-route `https://web-stage.europark.local/garage/details/cfce7585-2612-5b55-5376-fe19d5a04c04` och gick vidare till checkout utan att tappa sessionen.
- På checkout-sidan var `CustomerModel_IdentificationNumber` förifyllt som dolt fält med värdet `740130-0608`.
- Blockerande observation 2026-08-26: tre reproduktioner med kandidaten `47184 | Malmen 14, Möllevångsgatan 42 garage A | Migrated` nådde unika checkout-URL:er men renderade samtidigt `Fel` / `Inloggning krävs` och `Logga in med BankID`, trots att `web-stage`-hosten behöll `Logga ut`-länken samt förifyllda kundfält och dolt `CustomerModel.IdentificationNumber = 740130-0608`. Använd denna kombination för att skilja ett verkligt checkout-regressionsfel från ren utloggning eller fel kandidat.

## Felutfall

Testet ska markeras som underkänt om något av följande inträffar:

- inget DS med status `Migrated` kan identifieras i `Admin -> Migrate DS`
- DS-namnet kan inte översättas till en användbar serviceportal-sökning
- `Nytt kontrakt` tappar den inloggade användarsessionen
- vald parkering routas till legacy/annan host
- flera rimliga `Migrated`-kandidater saknar köpbar produkt eller ledig plats och testet kan därför inte nå verifieringspunkten
- `Nästa` inte kan genomföras i rätt inloggat läge
- personnummer inte är förifyllt på nästa steg

## Bevis / dokumentation

Dokumentera minst:

- vilket DS som valdes i `Admin -> Migrate DS`
- vilken migration status som observerades
- vilket parkeringsnamn som extraherades från `[nummer] [NAMN]`
- om kandidaten saknade köpbar produkt eller ledig plats
- vilken start-URL som användes
- vilket garage- eller parkeringskort som valdes
- vilken detalj-URL som öppnades
- om användaren fortfarande var inloggad
- om personnummer var förifyllt

## Senast verifierad körning

- **Datum:** 2026-08-26
- **Körläge:** Regression Mode
- **Start-URL:** `https://web-stage.europark.local/myaccount/index`
- **Valt DS i Admin -> Migrate DS:** `47184 | Malmen 14, Möllevångsgatan 42 garage A | Migrated`
- **Sökterm i serviceportalen:** `Malmen 14, Möllevångsgatan 42 garage A`
- **Öppnad detalj-URL:** `https://web-stage.europark.local/garage/details/cfce7585-2612-5b55-5376-fe19d5a04c04`
- **Produktutfall:** godkänt, minst en köpbar produkt fanns tillgänglig
- **Vald produkt:** `Oreserverad plats, Dygnet runt, Nyttotillstånd` för `SEK 530 / månad inkl. moms`
- **Nästa steg-utfall:** godkänt, checkout öppnades på `https://web-stage.europark.local/garage/checkout/7bfe2d4d-3833-4397-bfbd-3a35e793d352`
- **Inloggningsutfall:** godkänt, användaren var fortfarande inloggad som `Anna Walldén`
- **Personnummerutfall:** godkänt, `740130-0608` var förifyllt via `CustomerModel_IdentificationNumber`
- **Historisk kontrast:** `Malmen 14, Möllevångsgatan 42 garage B` routades tidigare till legacy och tappade sessionen

## Relaterade dokument

- `testing\regression_test\kontrakt-sok-anna-serviceportal-login.md`
- `testing\regression_test\regression-test-catalog.md`
- `tools\docs\regressionstest-arbetsmodell.md`
- `tools\docs\browser-samarbete-stage-session.md`
