# Regressionstest - serviceportal checkoutverifiering och skapa kontrakt

Detta regressionstest verifierar checkout-steget efter `B`, inklusive förifyllda kunduppgifter, prissammanfattning, avgifter, avtalsgodkännande och att kontrakt faktiskt kan skapas.

## Test-ID

regression-serviceportal-checkout-verify-and-create-contract

## Catalog Key

`G`

## Summary

Start from the checkout page created by B, verify checkout and contract creation, and retry the full B -> G flow across at least ten migrated DS candidates before treating a stage failure as a confirmed regression.

## Dependencies

- `B` / `regression-serviceportal-nytt-kontrakt-migrated-ds`

## Typ

Manuellt/shared-browser-test i synlig serviceportal-session.

## Miljö

- Kundtjänstportalen stage: `https://sps-stage.europark.local/EditContract/`
- Serviceportalen stage: `https://web-stage.europark.local/garage/checkout/`

## Förutsättningar

- Test `A` och därefter test `B` ska vara genomförda.
- Agenten ska stå på checkout-sidan som öppnades i slutet av `B`.
- Agenten ska ha åtkomst till motsvarande `EditContract`-vy i Kundtjänstportalen för den användare och det kontrakt som användes i `A`.

## Syfte

Verifiera att checkout-sidan återanvänder korrekt kunddata från SPS, att sammanfattning och kostnader stämmer med det som valdes i `B`, att avtalsgodkännande fungerar och att användaren kan skapa kontrakt och få en bekräftelse.

Eftersom testet körs i stage får ett misslyckande på en enskild parkering inte automatiskt klassas som regression. Om checkout eller kontraktsskapande inte passerar ska agenten gå tillbaka till `B`, välja ett annat DS med status `Migrated`, skapa en ny checkout och köra hela `G` igen. Testet ska använda minst **10 olika migrerade DS-kandidater** innan ett återkommande fel klassas som verifierat regressionsfel. Detta krävs för att skilja systemfel från DS-specifika konfigurationsfel, till exempel saknad produkt, saknad plats, felaktig taxa eller annan stage-data.

Akka-garagen ska prioriteras som kandidater när de finns med status `Migrated`, eftersom de sannolikt har köpbara platser och därför är bra kontrollkandidater som bör kunna passera.

## DS-omprövningsregel

När `G` inte passerar för den checkout som skapades av `B` ska körningen hanteras enligt följande:

1. Dokumentera aktuell DS-kandidat, produkt, checkout-URL, feltext och vilket kontrollsteg som föll.
2. Klassificera observationen preliminärt som en av:
   - `candidate configuration` om felet rimligen kan bero på parkeringens stage-konfiguration, till exempel ingen köpbar produkt, ingen ledig plats, saknad avgift, tom aviseringsmetod eller lokal prisanomali
   - `potential regression` om felet ser systemiskt ut, till exempel samma valideringsfel, `NaN`, tappad session eller utebliven bekräftelse trots komplett checkoutdata
3. Gå tillbaka till test `B`, välj en ny och tidigare oprövad DS-kandidat med status `Migrated`, och skapa en ny checkout.
4. Kör hela `G` igen från den nya checkout-sidan.
5. Fortsätt tills något av följande inträffar:
   - ett DS passerar hela `B -> G`, vilket visar att det tidigare felet sannolikt var kandidat-/konfigurationsbundet
   - minst 10 olika migrerade DS-kandidater har prövats och samma blockerande fel eller samma felkategori kvarstår
   - färre än 10 rimliga migrerade kandidater kan hittas, vilket ska markeras som blockerat eller otillräckligt underlag, inte som verifierat regressionsfel

Ett developer-facing fel i `test_reports` får skapas först när minst 10 olika migrerade DS-kandidater har prövats med samma blockerande utfall eller samma systemiska felkategori. De tre reproduktionerna enligt rapporteringsstandarden ska i så fall göras på denna 10-DS-baseline, inte genom att klicka om samma checkout för samma DS tre gånger.

## Teststeg

1. Utgå från slutläget i test `B`, där checkout-sidan redan är öppen för den första migrerade DS-kandidaten.
2. Öppna eller återanvänd motsvarande `EditContract`-vy i Kundtjänstportalen för samma användare.
3. Kontrollera att `Personnummer/Organisationsnummer` är förifyllt i checkout.
4. Kontrollera att följande fält i checkout matchar uppgifterna i `EditContract`:
   - förnamn
   - efternamn
   - land
   - gatuadress
   - postnummer
   - ort/stad
   - e-post
   - telefonnummer
5. Om en uppgift saknas i `EditContract` ska motsvarande uppgift också saknas i checkout; den får inte vara godtyckligt ifylld.
6. Kontrollera att produktsammanfattningen i checkout motsvarar det val som gjordes i `B`.
7. Kontrollera att priset i checkout stämmer med den produkt som valdes i `B`.
8. Kontrollera att sidan visar en serviceavgift eller uppläggningsavgift.
9. Kontrollera att månadskostnaden är korrekt.
10. Kontrollera att sidan visar hur mycket som ska betalas första månaden, inklusive månadsavgift och service-/uppläggningsavgift.
11. Kontrollera att sidan visar numeriska priser och att `SEK` inte följs av `NaN`.
12. Kontrollera att det finns minst en aviseringsmetod att välja i dropdownen.
13. Kontrollera att kontraktets startdatum är dagens datum.
14. Godkänn Apcoas avtalsvillkor.
15. Klicka på `Skapa kontrakt`.
16. Vänta tills kontraktet antingen skapas och en bekräftelsesida visas, eller tills ett tydligt felutfall visas.
17. Om ett fel visas eller om användaren inte kommer vidare:
    - ta skärmdump på felet
    - dokumentera exakt feltext, URL, DS-kandidat, produkt och observerat tillstånd
    - gå tillbaka till test `B`, välj en ny migrerad DS-kandidat och kör om hela flödet till en ny checkout
    - fortsätt tills minst 10 olika migrerade DS-kandidater har prövats, eller tills ett DS passerar hela flödet
    - skapa inte en utvecklarvänlig felrapport i `test_reports` förrän 10 olika DS-kandidater visar samma blockerande utfall eller samma systemiska felkategori

## Förväntat resultat

- Checkout-sidan ska visa korrekt förifyllda kunduppgifter från SPS.
- Fält som saknar källa i `EditContract` ska inte vara felaktigt eller godtyckligt ifyllda i checkout.
- Produktsammanfattning och pris ska motsvara valet i `B`.
- Service-/uppläggningsavgift ska vara tydligt redovisad.
- Sidan ska visa korrekt månadskostnad och första månadsbetalning.
- Priserna ska vara numeriska och inte innehålla `NaN`.
- Det ska finnas minst en aviseringsmetod att välja.
- Startdatum ska vara dagens datum.
- `Skapa kontrakt` ska leda vidare till en bekräftelse utan blockerande fel.
- Om första valda DS inte passerar ska minst en senare migrerad DS-kandidat kunna passera, eller så ska minst 10 olika migrerade DS-kandidater visa samma systemiska fel innan testet klassas som verifierat regressionsfel.

## Startläge

- Aktiv flik: checkout-sidan från `B`
- URL-mönster: `https://web-stage.europark.local/garage/checkout/{saleId}`
- Detta startläge kräver kedjan `A -> B -> G`

## Exekveringsgenvägar

- I tidigare verifierade körningar användes användaren `Anna Walldén` och migrated DS `47184 | Malmen 14, Möllevångsgatan 42 garage A`.
- Checkout-URL får ett nytt `saleId` när `B` körs om; testet ska därför följa flödet från `B` i stället för att lita på en hårdkodad checkout-URL.
- Vid omprövning ska varje DS få en ny rad i kandidatloggen med DS-nummer, DS-namn, migration status, serviceportalens sökterm, vald produkt, checkout-URL, utfall och felkategori.
- Prioritera Akka-garagen som kontrollkandidater om de är markerade som `Migrated`, eftersom de troligen har köpbara platser och ska vara mindre känsliga för kandidatkonfiguration.
- Jämförelsen mot Kundtjänstportalen ska i första hand göras mot `Kontraktsammanfattning` och övriga kundfält i `EditContract`.
- Om checkout visar dolda eller automatiskt satta värden ska dessa också dokumenteras när de påverkar resultatet, till exempel dolda identifieringsfält.

## Tekniska observationer

- Tidig Learning Mode-observation 2026-08-26: `CustomerModel_IdentificationNumber` var förifyllt med `740130-0608`.
- Tidig Learning Mode-observation 2026-08-26: förnamn, efternamn, land, adress, postnummer, ort, e-post och telefon var ifyllda i checkout.
- Tidig Learning Mode-observation 2026-08-26: dropdownen `NotificationMethodPackageId` var tom.
- Tidig Learning Mode-observation 2026-08-26: totalsammanfattningen visade `Totalt att betala per månad: SEK NaN/månad inkl. moms`.
- Tidig Learning Mode-observation 2026-08-26: service-/uppläggningsavgift kunde inte verifieras som tydligt redovisad på sidan.
- Tidig Learning Mode-observation 2026-08-26: ett försök att skapa kontrakt stannade kvar inom checkoutflödet och visade bland annat feltexten `CustomerModel.PhoneNumber har ett felaktigt värde`.
- Verifierad Regression Mode-observation 2026-08-27: efter `Skapa kontrakt` ändrades URL:en från `/garage/checkout/{saleId}` till `/garage/checkout`, men det dolda `SaleId`-fältet behöll samma GUID och checkoutdata låg kvar.
- Verifierad Regression Mode-observation 2026-08-27: samma create-fel kan reproduceras genom att stänga `OK`-dialogen, säkerställa att `TermsAndConditions` fortsatt är ikryssad och klicka `Skapa kontrakt` igen.
- Learning Mode-förtydligande 2026-08-28: ett fel på ett enskilt migrerat DS är inte längre tillräckligt för att skapa regressionsrapport. `G` måste pröva minst 10 olika migrerade DS-kandidater genom hela `B -> G`-kedjan innan ett återkommande checkout-/create-fel betraktas som verifierad regression.
- Regression Mode-observation 2026-08-28: `G` kunde inte starta eftersom `B` inte nådde checkout för 10 prövade migrerade DS-kandidater. Akka-kandidaterna `900627`, `900629`, `900631`, `900636` och `900640` gav inga Google-geocode-träffar från DS-namnet. `900624`, `900648`, `900104` och `47184` gav web-stage garageträffar men details-fetch redirectade till `/account/denied`. `900782` geokodades men gav ingen exakt serviceportalträff. Detta ska behandlas som blockerat/otillräckligt underlag för `G`, inte som verifierat G-fel, eftersom checkout aldrig nåddes.

## Felutfall

Testet ska markeras som underkänt om något av följande inträffar:

- personnummer/org.nr inte är förifyllt
- något kundfält avviker från motsvarande data i `EditContract`
- ett fält är ifyllt i checkout trots att motsvarande data saknas i `EditContract`
- produktsammanfattning eller pris inte matchar valet i `B`
- service-/uppläggningsavgift saknas eller inte går att verifiera
- månadskostnad eller första månadsbetalning inte går att verifiera
- något prisfält visar `NaN`
- dropdownen för aviseringsmetod är tom
- startdatum inte är dagens datum
- `Skapa kontrakt` leder inte till bekräftelse för minst 10 olika migrerade DS-kandidater med samma blockerande utfall eller samma systemiska felkategori
- ett valideringsfel eller annat blockerande fel hindrar att kontraktet skapas för minst 10 olika migrerade DS-kandidater med samma blockerande utfall eller samma systemiska felkategori

Följande ska inte ensamt markera `G` som verifierat regressionsfel:

- ett fel som bara observerats på en DS-kandidat
- en kandidat utan köpbar produkt eller ledig plats
- en kandidat med uppenbart DS-specifik stage-konfiguration
- färre än 10 testade migrerade DS-kandidater när felet kan vara kandidatbundet

## Bevis / dokumentation

Dokumentera minst:

- vilken checkout-URL som användes
- vilket kontrakt och vilken användare som jämfördes mot i `EditContract`
- vilka fält som matchade
- vilka fält som saknades i båda vyerna
- vilket produktval och pris som verifierades
- om aviseringsmetod fanns eller saknades
- om `NaN` förekom
- om service-/uppläggningsavgift kunde verifieras
- om kontraktsskapandet lyckades
- feltext och skärmdumpar om skapandet misslyckades
- full kandidatlogg för varje prövat migrerat DS
- antal unika DS-kandidater som prövades
- vilka kandidater som var Akka-garage eller annan förväntat köpbar kontrollkandidat
- om utfallet var DS-specifik konfigurationsavvikelse, potentiell regression, verifierad regression eller otillräckligt underlag

## Senast verifierad körning

- **Datum:** 2026-08-27
- **Körläge:** Regression Mode
- **Status:** failed
- **Kedja:** `A -> B -> G`
- **Jämförd användare:** `Anna Walldén`
- **Jämfört kontrakt i Kundtjänst:** `H-47184-000025049`
- **Verifierad checkout-URL:** `https://web-stage.europark.local/garage/checkout/97570ef4-700a-4f84-a931-019e01442f32`
- **Post-submit-URL:** `https://web-stage.europark.local/garage/checkout`
- **Valt DS:** `47184 | Malmen 14, Möllevångsgatan 42 garage A | Migrated`
- **Fält som matchade EditContract:** personnummer `740130-0608`, förnamn `Anna`, efternamn `Walldén`, e-post `annawallden.74@gmail.com`, telefon `0730 91 41 65`
- **Fält som matchade adresskällan i Kundtjänst:** adress `Lüneburgska vägen 1B`, postnummer `23940`, ort `Falsterbo`, land `SE/Sweden`
- **Produkt- och prisutfall:** `Oreserverad plats, Dygnet runt, Nyttotillstånd` visades initialt i checkout med `SEK 530 / månad inkl. moms`, vilket matchade valet i `B`
- **Verifierad prisanomali:** `Totalt att betala per månad: SEK NaN/månad inkl. moms` observerades i checkout och kvarstod genom tre create-försök
- **Verifierad aviseringsanomali:** `NotificationMethodPackageId` var tom med `0` valbara alternativ
- **Avgiftsutfall:** ingen tydligt redovisad service-/uppläggningsavgift kunde verifieras i checkout; dolda värden visade bland annat `OnlineFee=0`, `TotalPrice=530` och `GrandTotal=530`
- **Skapa-kontrakt-observation:** `Skapa kontrakt` reproducerades tre gånger med samma blockerande dialog: `Fel format` / `CustomerModel.PhoneNumber har ett felaktigt värde`
- **Rapportstatus:** historisk developer-facing defect report finns under `test_reports\20260827v1\RegressionError01\report.md`, men rapporten uppfyller inte längre gällande 10-DS-krav och ska inte användas som verifierat regressionsfel utan omprövning.
- **Giltighet efter ändrad DS-regel:** Den tidigare rapporten bygger på samma DS/checkout och uppfyller inte längre kravet på minst 10 olika migrerade DS-kandidater. Den ska behandlas som historisk observation tills felet har omprövats enligt den nya DS-omprövningsregeln.

## Senaste Regression Mode-försök

- **Datum:** 2026-08-28
- **Körläge:** Regression Mode
- **Status:** Blockerat före `G`
- **Orsak:** Beroendet `B` kunde inte skapa en checkout för någon av 10 prövade migrerade DS-kandidater.
- **Kandidatlogg:** `tmp\regression-g-20260828-endpoint-candidate-log.json`
- **Prövade migrerade DS:** `900624`, `900627`, `900629`, `900631`, `900636`, `900640`, `900782`, `900648`, `900104`, `47184`
- **Akka-kandidater:** `900624`, `900627`, `900629`, `900631`, `900636`, `900640`, `900782`, `900648`
- **Observerade blockerare:** fem Akka-kandidater gav `ZERO_RESULTS` i Google-geocode från DS-namnet, en Akka-kandidat gav ingen exakt serviceportalträff, och fyra kandidater gav web-stage garageträff men details-sidan redirectade till `/account/denied`.
- **Rapporteringsbeslut:** Ingen ny `test_reports`-rapport skapades, eftersom `G` varken passerade eller nådde ett verifierat G-fel enligt Regression Mode-reglerna.

## Relaterade dokument

- `testing\regression_test\kontrakt-sok-anna-serviceportal-login.md`
- `testing\regression_test\serviceportal-nytt-kontrakt-migrated-ds.md`
- `testing\regression_test\regression-test-catalog.md`
- `tools\docs\regressionstest-arbetsmodell.md`
