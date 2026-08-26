# Regressionstest - serviceportalen nytt kontrakt via non-migrated DS

Detta regressionstest verifierar att en användare som redan loggats in via assisted login kan identifiera ett DS som inte är migrerat i adminflödet, söka efter motsvarande parkeringsnamn i serviceportalen och köpa en produkt.

## Test-ID

regression-serviceportal-nytt-kontrakt-non-migrated-ds

## Catalog Key

`C`

## Summary

Start from the logged-in service portal page created by A, click Nytt kontrakt, then find a non-migrated DS through Admin -> Migrate DS and verify that a product can be purchased for that parking.

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

Verifiera att användaren från sin redan inloggade serviceportalsida kan klicka på `Nytt kontrakt`, identifiera ett DS som inte är migrerat, använda parkeringsnamnet från det DS:t i serviceportalen och genomföra ett köpflöde för en produkt.

## Iterationsregel

Om ett valt DS inte har någon köpbar produkt eller ledig plats ska testet inte underkännas direkt. I stället ska agenten dokumentera observationen, gå tillbaka till `Admin -> Migrate DS`, välja en ny kandidat som inte är `Migrated` och försöka igen.

Testet ska först markeras som underkänt när:

- flera rimliga icke-migrerade kandidater har prövats utan att det går att nå den avsedda verifieringspunkten, eller
- ett verkligt regressionsfel observeras, till exempel tappad inloggning, legacy-routing eller saknat förifyllt personnummer.

## Teststeg

1. Utgå från slutläget i test `A`, där användaren redan är inloggad på `https://web-stage.europark.local/myaccount/index`.
2. Klicka på `Nytt kontrakt`.
3. Gå tillbaka till Kundtjänstportalen.
4. Öppna `Admin -> Migrate DS`.
5. Sök fram ett DS som inte har migration status `Migrated`.
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
    - välj en annan kandidat som inte är `Migrated`
    - upprepa stegen från sökningen i serviceportalen
15. Om en köpbar produkt eller ledig plats finns, välj den.
16. Välj inga tilläggstjänster.
17. Säkerställ att önskat startdatum är idag.
18. Klicka på `Nästa`.
19. Kontrollera att användaren fortfarande är inloggad.
20. Kontrollera att personnummer är förifyllt.

## Förväntat resultat

- Ett DS som inte är migrerat ska kunna väljas i `Admin -> Migrate DS`.
- DS-namnet ska kunna återanvändas som sökterm i serviceportalen när den inledande siffran utelämnas.
- Minst en av de prövade icke-migrerade kandidaterna ska ge en köpbar produkt eller ledig plats, eller så ska avsaknaden dokumenteras som kandidatobservation och testet iterera vidare.
- Flödet ska stanna inom rätt serviceportal-/stage-miljö.
- Användaren ska efter `Nästa` fortfarande vara inloggad.
- Personnummer ska vara förifyllt på nästa steg.

## Exekveringsgenvägar

- På `Mitt Parkeringskonto` leder länken `Nytt kontrakt` till startsidan `https://web-stage.europark.local/`.
- Sökfältet på startsidan är `addressSearch` och sökknappen är `searchButton`.
- I `Admin -> Migrate DS` ska kandidaten väljas utifrån att migration status inte är `Migrated`.
- Sökfältet i `Admin -> Migrate DS` är DataTables-fältet `input[type="search"][aria-controls="tblMigration"]`.
- När DS visas som `[nummer] [NAMN]` ska bara `NAMN` användas i serviceportalens sökfält, inte numret.
- Korta eller generiska namn kan ge geosök-drivna träffar i närliggande områden i stället för exakt DS-match; kontrollera alltid att första matchande kortet verkligen motsvarar DS-namnet från `Migrate DS`.
- För kandidaten `Spiran 9, S:t Persgatan 95` visar både namnlänken och CTA:n `Hyr plats` redan i resultatlistan samma `href` med `/lgcy/garage/details/...`; det gör det snabbt att förhandsverifiera legacy-routing innan detaljsidan följs.

## Tekniska observationer

- Valet av DS är en explicit del av testet och ska dokumenteras i varje körning.
- Testet ska bekräfta att ett icke-migrerat DS fortfarande går att använda för köpflödet i serviceportalen.
- Om flera liknande resultat visas i serviceportalen ska valet matchas mot namnet från `Migrate DS`, inte mot en godtycklig träff.
- Ingen produkt till försäljning är i sig inte ett regressionsfel; det kan vara en konfigurationsfråga på det specifika DS:t.
- Observerad kandidat 2026-08-26: `900540 | Spiran 9, S:t Persgatan 95 | Not Migrated` gav en tydlig match i serviceportalens resultatlista, men länken pekade på `/lgcy/garage/details/...`.
- Verifierad regression 2026-08-26: när träffen för `900540 | Spiran 9, S:t Persgatan 95 | Not Migrated` klickades vidare routades sidan till `https://hyra-legacy-stage.europark.local//garage/details/4d19a78b-9c55-451c-8a6c-1a7070fddd17`.
- Återverifiering 2026-08-26: samma `href` observerades konsekvent både på garagenamnet och på `Hyr plats`, och när länken följdes stannade felet på samma legacy-host i tre av tre reproduktioner.
- Observerad kandidat 2026-08-26: `1205 | Bålsta C | Not Migrated` gav ingen verifierad matchande resultatrad; sökningen drev i stället till generiska träffar i Kungsängen/Järfälla.

## Felutfall

Testet ska markeras som underkänt om något av följande inträffar:

- inget DS som inte är `Migrated` kan identifieras i `Admin -> Migrate DS`
- DS-namnet kan inte översättas till en användbar serviceportal-sökning
- ingen verifierbar resultatpost i serviceportalen motsvarar valt DS efter rimlig iteration
- `Nytt kontrakt` tappar den inloggade användarsessionen
- vald parkering routas till legacy/annan host
- flera rimliga icke-migrerade kandidater saknar köpbar produkt eller ledig plats och testet kan därför inte nå verifieringspunkten
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
- **Status:** failed
- **Kandidat i Admin -> Migrate DS:** `900540 | Spiran 9, S:t Persgatan 95 | Not Migrated`
- **Sökterm i serviceportalen:** `Spiran 9, S:t Persgatan 95`
- **Resultatutfall:** tydlig träff i resultatlistan i samtliga försök
- **Routeutfall:** underkänt; både garagenamnet och `Hyr plats` visade href `https://web-stage.europark.local/lgcy/garage/details/4d19a78b-9c55-451c-8a6c-1a7070fddd17`, och följd navigation landade på `https://hyra-legacy-stage.europark.local//garage/details/4d19a78b-9c55-451c-8a6c-1a7070fddd17`
- **Reproducerbarhet:** verifierad tre gånger med samma utfall i samma regressionskörning
- **Sessionåterställning:** serviceportalfliken återställdes efter körningen till `https://web-stage.europark.local/myaccount/index` i fortsatt inloggat läge
- **Rapportstatus:** ingen ny slutrapport skapad i denna körning

## Relaterade dokument

- `testing\regression_test\kontrakt-sok-anna-serviceportal-login.md`
- `testing\regression_test\regression-test-catalog.md`
- `tools\docs\regressionstest-arbetsmodell.md`
- `tools\docs\browser-samarbete-stage-session.md`
