# Regressionstest - Kundtjänst svensk lokalisering och terminologi

Detta regressionstest verifierar att Kundtjänstportalens samtliga menyer och öppningsbara sidor i stage använder god svensk UI-text. Testet ska identifiera alla engelska, blandade eller andra utländska uttryck i det statiska kundtjänstgränssnittet och ange exakt var de finns samt vad de ska översättas eller normaliseras till på svenska.

## Test-ID

regression-kundtjanst-svensk-lokalisering-och-terminologi

## Catalog Key

`H`

## Summary

Audit every Customer Service Center menu and page in stage for non-Swedish UI text and Swedish terminology consistency.

## Dependencies

- none

## Typ

Manuellt/shared-browser-test i synlig Kundtjänstportal-session.

## Miljö

- Kundtjänstportalen stage: `https://sps-stage.europark.local/CustomerService`
- Primär rådatakälla: `raw_data\kundtjanst-funktioner-data.json`
- Stödjande menyöversikt: `manuals\csc_user_manuals\Kundtjänst - funktioner.md`
- Terminologistöd: `syntetisk_data\common\ordlista-och-namnstandard.md`

## Förutsättningar

- Synlig delad browser ska vara startad via `.\runtime\start-collaborative-stage-browser.ps1`.
- Användaren ska vara inloggad i Kundtjänstportalen.
- Agenten ska kunna läsa och styra samma browser-session.
- Agenten ska läsa aktuell menylista från `raw_data\kundtjanst-funktioner-data.json` före körning så att testet följer senaste inventerade menystruktur.

## Syfte

Verifiera att Kundtjänstportalen kan användas som en svenskspråkig arbetsportal utan engelska, blandade eller andra utländska UI-uttryck i navigering, rubriker, formulär, tabeller, knappar, statusmeddelanden, felmeddelanden, rapportcontainrar eller andra statiska texter.

Rapporten från testet ska inte visa hur svenska ord översätts till engelska. Den ska visa motsatsen: vilka ord och uttryck i hela Kundtjänstgränssnittet som inte är på god svenska, exakt var de ligger i portalen och vilken svensk text som ska användas i stället. Testet ska också upptäcka när samma affärsbegrepp används inkonsekvent och rekommendera en svensk standardterm.

## Omfattning

Testet ska omfatta alla menygrupper och menyval i aktuell stage-inventering:

| Menygrupp | Antal menyval i rådata | Exempel på risk för språk-/termkonflikt |
| --- | ---: | --- |
| Kontrakt | 8 | `Old Search Method`, `VRMer`, `garage`, blandning av kontrakt-/avtalsbegrepp |
| STP-tjänster | 5 | engelska STP-etiketter, `Old Search Method`, blandning av STP och svensk tjänsteterminologi |
| Rapporter | 34 | engelska rapportnamn, stavfel som `Repot`, rapportnamn utan svensk målterm |
| Garage | 7 | `Garage`, `DS`, `CarPark`, `BA` och blandad audit trail-text |
| Produkt | 4 | `Product Template`, `Package`, `Reklambanner` |
| Köhantering | 6 | `Queue`, `Waiting list`, `offer`, blandning av kö- och erbjudandetermer |
| Nyckelhantering | 3 | `Key Inventory`, `Manage Key Types`, `CarPark Key Settings` |
| Loggar | 4 | `Audit trail`, `Backend Process Events`, `Oktavius` |
| Gemensamma inställningar | 8 | `Notification Templates`, `Contract Termination Reasons`, `KPI/CPI` |
| Templates | 3 | engelsk mallterminologi och dubbelplacering av mallfunktioner |
| Admin | 31 | engelska adminverktyg, interna systemnamn och blandade menyval |
| Användarmeny | 2 | profil- och utloggningsetiketter |

Om rådata har fler eller färre menyval vid körning ska agenten följa rådata och dokumentera avvikelsen mot tabellen ovan.

## Definitioner

- **Icke-svensk UI-text:** synlig statisk text i CSC-stage som är på engelska eller annat språk än svenska, till exempel menytext, sidrubrik, fältetikett, knapp, kolumnrubrik, hjälprad, valideringsmeddelande eller systemgenererad status-/feltext.
- **Blandad etikett:** en enskild UI-text som blandar svenska och engelska eller annan utländsk term utan tydlig produktorsak, till exempel `Pusha alla contract`.
- **Utländskt uttryck:** ord eller fras som inte är etablerad svensk UI- eller domänterminologi i SPS-kontexten.
- **Terminkonflikt:** samma funktionella begrepp får olika namn på olika platser utan att skillnaden är avsiktlig eller förklarad.
- **God svensk UI-text:** kort, begriplig och konsekvent svensk text som passar i den faktiska UI-ytan och följer svensk böjning, sammansättning och versalisering.
- **Tillåtna domänförkortningar:** `DS`, `VRM`, `STP`, `CPS`, `TPS`, `PBI`, `BC`, `BA`, `KPI`, `CPI`, `ANPR`, `EPMP`, `TMS` när de används som etablerade domän- eller systemförkortningar och inte som ersättning för en svensk etikett där en sådan behövs.
- **Tillåtna produkt-/systemnamn:** `Business Central`, `Park&GO`, `Oktavius`, `Power BI`, `ThirdPartySales`, `Tech Tool` när de används som system- eller produktnamn. Om namnet används i en UI-etikett ska omgivande beskrivande text fortfarande vara på svenska.
- **Datainnehåll utanför scope:** personnamn, ortnamn, företagsnamn, juridiska namn, parkerings-/garageposter, rapportkoder och annan kund- eller systemdata räknas inte som språkfel när de är innehåll snarare än statisk UI-text.

## Rekommenderad svensk terminologi

Använd tabellen som konsistensreferens under testet. Om produktägaren senare beslutar andra måltermer ska testet uppdateras innan nästa Regression Mode-körning.

| Begrepp | Rekommenderad svensk UI-term | Exempel på avvikande varianter att flagga |
| --- | --- | --- |
| Kundtjänst / CSC | Kundtjänst | Customer Service Center, CustomerService utan svensk kontext |
| Kontrakt / avtal | Kontrakt | Contract, Agreement, avtal om samma objekt i CSC ska heta kontrakt |
| Korttidsavtal / STP | Korttidsavtal | STP contract, Short-term parking contract, engångsparkering när samma flöde avses |
| DS / anläggning | DS / parkeringsanläggning | Car park, Garage, CarPark när anläggning avses generellt |
| Garage | Garage | CarPark, Car Park, garage med inkonsekvent versalisering |
| Parkeringsplats | Parkeringsplats | Parking space, place, spot, plats om samma fysiska parkeringsplats avses |
| Kund | Kund | Customer, User när juridisk eller faktisk kund avses |
| Användare | Användare | User, Customer när portal-/kontoanvändare avses |
| Registreringsnummer | Registreringsnummer | VRM, License plate, registration number, VRMer om UI-ytan rymmer svensk term |
| Kö | Kö | Queue, Waiting list när samma köobjekt avses |
| Kömedlem | Kömedlem | Queue member, queuing customer, queue participant |
| Erbjudande | Erbjudande | Offer, proposal, erbjudande med inkonsekvent versalisering |
| Nyckel | Nyckel | Key, access item om fysisk nyckel avses |
| Produktmall | Produktmall | Product template, Product Template List |
| Paketmall | Paketmall | Package, Package template, Paketmallar om singular/plural används inkonsekvent |
| Reklambanner | Reklambanner | Advertisement banner, Banner, Reklam banner |
| Betalautomat | Betalautomat | Payment machine, pay machine, BA när användaren behöver begriplig etikett |
| Fastighetsägare | Fastighetsägare | Property owner, Landlord om inte juridisk roll faktiskt skiljer sig |
| Hyresvärd | Hyresvärd | Landlord, Property owner när separat hyresvärdsroll avses |
| Operatör | Operatör | Operator, Provider när operatör avses |
| Allmän helgdag | Allmän helgdag | Public holiday, Holiday, helgdag om formell UI-term behövs |
| Avslutsorsak | Avslutsorsak | Termination reason, Contract termination reason |
| Logg | Logg | Log, Logs när singular/plural används inkonsekvent i motsvarande vyer |
| Ändringshistorik | Ändringshistorik | Audit trail, Audit, change log, history om samma revisionsvy avses |
| Schemaläggare | Schemaläggare | Scheduler, Scheduled task när själva schemaläggaren avses |
| Mall | Mall | Template, Templates |
| Avisering | Avisering | Notification när användarens synliga begrepp avses |
| Meddelandemall | Meddelandemall | Notification Template, Notification Templates |
| Bakgrundsprocess | Bakgrundsprocess | Backend Process, Backend Process Events |

## Teststeg

1. Läs `raw_data\kundtjanst-funktioner-data.json` och bygg en körlista över alla objekt där `kind` är `group` eller `item`.
2. Starta eller anslut till den delade stage-browsern enligt förutsättningarna.
3. Öppna `https://sps-stage.europark.local/CustomerService`.
4. Om Microsoft-inloggning visas, låt användaren slutföra inloggningen och vänta minst **5 minuter** innan testet klassas som blockerat.
5. Kontrollera att alla toppmenyer i rådata finns synligt i navigationen.
6. För varje toppmeny:
   - öppna menyn
   - dokumentera synlig gruppetikett
   - kontrollera om gruppetiketten är på god svenska
   - kontrollera om gruppetiketten använder rekommenderad svensk term
7. För varje menyval i rådata:
   - öppna menygruppen
   - dokumentera synlig menytext
   - kontrollera om menytexten är på god svenska
   - kontrollera om samma svenska begrepp används konsekvent jämfört med tidigare menyval
   - klicka menyvalet om det är en intern stage-länk
   - om menyvalet är extern länk, Power BI-rapport eller öppnar ny host: dokumentera synlig länktext och landnings-URL, men skapa inga data och gör inga destruktiva åtgärder
8. På varje öppnad sida, kontrollera synliga statiska UI-texter i första renderade vyn:
   - sidtitel och huvudrubrik
   - fältetiketter och placeholders
   - knapptexter och länkar
   - tabellrubriker och DataTables-texter som `Search`, `Show entries`, pagination och tom-lista-meddelanden
   - valideringsmeddelanden och hjälprader som visas utan att spara eller skicka formulär
   - modaltitlar eller panelrubriker som visas utan att förändra data
   - rapportcontainertexter och inbäddningsfel som är synliga utan extra autentisering
9. Gör inte åtgärder som skapar, uppdaterar, raderar, importerar, skickar, pushar, avslutar kontrakt eller startar externa processer. För sådana sidor räcker det att granska öppningsvyn och icke-mutativa kontroller.
10. För varje identifierad icke-svensk eller blandad UI-text, registrera:
    - menygrupp
    - menyval
    - URL/path
    - sidtitel eller panel där felet syns
    - exakt observerad text
    - plats i vyn, till exempel meny, rubrik, knapp, fält, kolumn, placeholder, validering, felmeddelande eller rapportcontainer
    - problemtyp: `English UI text`, `mixed language`, `foreign term`, `spelling/grammar`, `terminology mismatch`
    - föreslagen svensk måltext
    - kort motivering till varför måltexten är rekommenderad
11. För varje terminkonflikt, registrera:
    - svenskt begrepp som ska normaliseras
    - alla observerade varianter
    - var varje variant finns, med menygrupp, menyval, URL/path och UI-yta
    - rekommenderad svensk standardterm
    - om varianten verkar vara produktnamn, domänförkortning eller faktiskt inkonsekvent UI-text
12. Kontrollera särskilt redan kända riskmönster:
    - `Notification Templates` förekommer under både `Gemensamma inställningar` och `Templates`
    - `Old Search Method` förekommer i flera grupper
    - `Garage`, `DS`, `CarPark` och `Car park` blandas
    - `Contract`, `Kontrakt`, `Agreement` och `contract` blandas
    - `Queue`, `Kö`, `Waiting list` och `Queue Tick Tack Toe` blandas
    - `Product Template List`, `Produktmall`, `Paketmallar` och `Package Usage Details` blandas
    - `Key Inventory`, `Manage Key Types` och andra nyckelhanteringsetiketter är på engelska
    - `Audit trail`, `Backend Process Events`, `Templates` och admin-/rapportetiketter saknar svensk UI-term
13. Avsluta med en sammanställning per menygrupp:
    - antal granskade menyval
    - antal icke-svenska UI-texter
    - antal blandade etiketter
    - antal terminkonflikter
    - blockerade eller ej nåbara sidor

## Förväntat resultat

- Alla menygrupper och menyval från `raw_data\kundtjanst-funktioner-data.json` ska kunna granskas eller uttryckligen markeras som blockerade med orsak.
- Alla statiska UI-etiketter i CSC-stage ska vara på god svenska.
- Alla engelska, blandade eller andra utländska UI-uttryck ska rapporteras som avvikelser med exakt plats i portalen och föreslagen svensk måltext.
- Samma funktionella begrepp ska använda samma svenska term i menyer, rubriker, formulär, tabeller och knappar.
- Tillåtna domänförkortningar och produktnamn ska användas konsekvent och inte blandas med engelska böjningsformer eller otydliga hybridfraser.
- Testet ska producera en detaljerad avvikelselista som kan lämnas vidare till utveckling eller översättningsansvarig utan att mottagaren behöver öppna portalen för att förstå var felet finns.

## Slutläge

- Aktiv flik: Kundtjänstportalen stage eller sista granskade CSC-sida.
- Inga data ska ha skapats, ändrats, importerats, pushats eller raderats.

## Exekveringsgenvägar

- Menylistan behöver inte skrivas av manuellt; använd `raw_data\kundtjanst-funktioner-data.json` som checklista och verifiera den mot live-navigationen.
- För sidor som returnerar kända stage-fel ska språkgranskning av synliga felrubriker och feltext ändå göras om sidan renderar felinnehåll.
- Power BI-sidor ska granskas på CSC-ramens synliga titel, rapportnamn och fel-/containertext; själva inbäddade rapportinnehållet är bara i scope om det är läsbart utan extra autentisering.
- DataTables-standardtexter ska räknas som UI-text och ingår i språkgranskningen. Engelska standardtexter ska få svenska måltexter, till exempel `Search` -> `Sök`, `Show entries` -> `Visa poster`, `No data available in table` -> `Ingen data finns i tabellen`.
- Sidor med `Push`, `Import`, `Create`, `End`, `Delete`, `Merge`, `Point to`, `Update` eller motsvarande riskord får öppnas men inte skickas vidare.
- Om samma URL nås från flera menyer ska den granskas en gång, men alla menyer som länkar dit ska ingå i terminkonsistenskontrollen.

## Rapportkrav

Testrapporter under `test_reports` ska enligt repo-standard skrivas på formell engelska, men avvikelsedata och rekommenderade måltermer ska tydligt visa svensk måltext.

Rapporten ska minst innehålla följande tabeller:

### Finding details

| Kolumn | Krav |
| --- | --- |
| Finding ID | Stabilt löpnummer, till exempel `H-SV-001` |
| Menu group | Menygrupp där felet nås |
| Menu item | Menyval eller `Navigation group` om felet ligger på gruppnivå |
| URL/path | Exakt path eller full URL där felet syns |
| Page/panel | Sidtitel, panel, modal eller rapportcontainer |
| UI surface | Meny, rubrik, knapp, fält, placeholder, tabellkolumn, validering, felmeddelande, rapportcontainer eller annan konkret yta |
| Observed text | Exakt text som syns i portalen |
| Problem type | `English UI text`, `mixed language`, `foreign term`, `spelling/grammar` eller `terminology mismatch` |
| Recommended Swedish text | Föreslagen svensk text som ska ersätta observerad text |
| Rationale | Kort motivering, till exempel normaliserad term, grammatisk korrigering eller konsekvens mot annan UI |
| Evidence | Skärmbildsnamn, DOM-selector eller annan reproducerbar observation om sådan finns |

### Terminology consistency

| Kolumn | Krav |
| --- | --- |
| Concept | Affärsbegrepp som ska normaliseras |
| Recommended Swedish term | Svensk standardterm |
| Observed variants | Alla observerade varianter |
| Locations | Exakta menygrupper, menyval, URL/path och UI-ytor för varje variant |
| Recommendation | Vilken variant som ska ändras och till vad |

### Menu group summary

| Kolumn | Krav |
| --- | --- |
| Menu group | Granskad menygrupp |
| Menu items inspected | Antal granskade menyval |
| Non-Swedish findings | Antal engelska eller andra utländska UI-texter |
| Mixed-language findings | Antal blandade etiketter |
| Terminology findings | Antal terminkonflikter |
| Blocked pages | Antal blockerade eller ej nåbara sidor |

## Tekniska observationer

- Rådata från 2026-08-26 innehåller 115 öppningsbara menyfunktioner plus toppmenyer.
- Rådata visar redan blandat språk i navigeringen; detta test är därför väntat att hitta avvikelser tills CSC-portalen är fullt svensk lokaliserad.
- Det är inte ett testfel att kunddata, garage-/platsnamn, personnamn, rapportkoder eller systemnamn innehåller engelska, svenska eller interna akronymer när de är datainnehåll snarare än UI-etiketter.
- Om browsern visar Microsoft-inloggning under flödet ska agenten låta användaren arbeta färdigt i minst **5 minuter** innan körningen stoppas eller klassas som loginfel.
- Den tidigare Regression Mode-rapporten `test_reports\20260828v1\summary.md` bygger på den tidigare och felaktiga testinriktningen mot engelsk UI. Den ska inte användas som beslutsunderlag för svensk lokalisering, men kan användas som historisk indikation på var blandat språk tidigare observerades.

## Felutfall

Testet ska markeras som underkänt om något av följande inträffar:

- minst en granskad menygrupp, menytext, rubrik, fältetikett, knapp, tabellrubrik eller systemgenererad statisk text är på engelska eller annat språk än svenska
- en etikett blandar svenska och engelska utan tydlig produktorsak
- samma affärsbegrepp benämns med olika svenska, engelska eller blandade termer på jämförbara platser
- rapporten saknar exakt portalplats och föreslagen svensk måltext för en identifierad språkavvikelse
- en meny i rådata saknas i live-navigationen utan dokumenterad avsiktlig förändring
- en intern CSC-sida inte kan öppnas och det hindrar språkgranskningen av sidan
- testet inte kan täcka alla menygrupper på grund av session-, behörighets- eller inloggningsproblem

## Bevis / dokumentation

Dokumentera minst:

- datum och körläge
- vilken `capturedAt` från rådata som användes som menybaseline
- antal granskade grupper och menyval
- lista över blockerade eller ej nåbara sidor
- tabell över alla engelska, blandade eller andra utländska UI-texter
- tabell över alla terminkonflikter
- rekommenderad svensk måltext för varje språkavvikelse
- rekommenderad svensk standardterm för varje terminkonflikt
- om avvikelsen finns i meny, sidrubrik, fält, knapp, tabell, felmeddelande, rapportcontainer eller annan konkret UI-yta
- exakt URL/path och menyväg för varje avvikelse

## Senast verifierad körning

- **Datum:** Ej verifierad efter ändrat testsyfte.
- **Körläge:** Learning Mode
- **Status:** Testdefinitionen har ändrats från engelsk översättningskontroll till svensk lokaliseringskontroll. En ny Regression Mode-körning krävs innan testet har ett giltigt verifierat utfall.
- **Tidigare rapport:** `test_reports\20260828v1\summary.md` är historisk och avser den tidigare felaktiga testinriktningen.

## Återanvändbara körlärdomar

- Kör live-inventeringen till `tmp`, inte till `raw_data`, när syftet är Regression Mode-verifiering och inte ny rådatainsamling.
- Inventeringsskriptet lämnar browsern på sista öppnade sida. För reproduktion 2 och 3 ska Kundtjänst-startsidan öppnas igen innan `Invoke-KundtjanstMenuInventory.ps1` startas, annars kan skriptet sakna matchande `CustomerService`-target.
- Vid rapportering av detta test ska fullständig findings-data sparas som artefakt i felrapporten, eftersom antalet engelska, blandade eller andra utländska UI-texter kan vara mycket stort.
- Rapporten ska prioritera rättningsbarhet: varje rad ska ange portalplats, observerad text och rekommenderad svensk text. Representativa exempel räcker inte när syftet är att utvecklare ska kunna rätta portalen.

## Relaterade dokument

- `raw_data\kundtjanst-funktioner-data.json`
- `manuals\csc_user_manuals\Kundtjänst - funktioner.md`
- `syntetisk_data\kundtjanst-menykarta.md`
- `syntetisk_data\common\ordlista-och-namnstandard.md`
- `tools\docs\browser-samarbete-stage-session.md`
- `tools\docs\regressionstest-arbetsmodell.md`
- `testing\regression_test\regression-test-catalog.md`
