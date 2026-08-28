# Regressionstest - Kundtjänst engelsk översättning och konsekvent terminologi

Detta regressionstest verifierar att Kundtjänstportalens samtliga menyer och öppningsbara sidor i stage är översatta till engelska samt att samma begrepp används konsekvent i hela CSC-webbportalen.

## Test-ID

regression-kundtjanst-english-translation-consistency

## Catalog Key

`H`

## Summary

Audit every Customer Service Center menu and page in stage for English translation coverage and consistent terminology.

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

Verifiera att CSC kan användas som en engelskspråkig arbetsportal utan svenska eller blandade etiketter i navigering, rubriker, formulär, tabeller, knappar, statusmeddelanden eller felmeddelanden. Testet ska också upptäcka om samma affärsbegrepp heter olika saker på olika platser, till exempel `DS`, `Car park`, `Garage`, `Contract`, `Agreement`, `VRM`, `License plate`, `Queue`, `Waiting list`, `Customer`, `User`, `Property owner`, `Landlord` och `Operator`.

## Omfattning

Testet ska omfatta alla menygrupper och menyval i aktuell stage-inventering:

| Menygrupp | Antal menyval i rådata | Exempel på risk för språk-/terminkonflikt |
| --- | ---: | --- |
| Kontrakt | 8 | `Kontrakt`, `Old Search Method`, `VRMer`, `garage` |
| STP-tjänster | 5 | svensk grupp med engelskt STP-begrepp och `Old Search Method` |
| Rapporter | 34 | blandning av svenska rapportnamn, engelska rapportnamn och stavfel som `Repot` |
| Garage | 7 | `Garage`, `DS`, `CarPark`, `BA` och svensk/engelsk audit trail-text |
| Produkt | 4 | `Produkt`, `Product Template`, `Package`, `Reklambanner` |
| Köhantering | 6 | `Kö`, `Queue`, `Waiting list`, `offer` |
| Nyckelhantering | 3 | `Key Inventory`, `Manage Key Types`, `CarPark Key Settings` |
| Loggar | 4 | `Loggar`, `Audit trail`, `Backend Process Events`, `Oktavius` |
| Gemensamma inställningar | 8 | `Notification Templates`, `Contract Termination Reasons`, `KPI/CPI` |
| Templates | 3 | dubbelplacering av `Notification Templates`, svensk/engelsk mallterminologi |
| Admin | 31 | blandning av svenska menyval, engelska adminverktyg och interna systemnamn |
| Användarmeny | 2 | profil- och utloggningsetiketter |

Om rådata har fler eller färre menyval vid körning ska agenten följa rådata och dokumentera avvikelsen mot tabellen ovan.

## Definitioner

- **Oöversatt text:** synlig svensk text i CSC-stage där testets mål är engelsk UI-text. Svenska personnamn, ortnamn, företagsnamn, juridiska namn och data från kund-/garageposter räknas inte som UI-översättningsfel.
- **Blandad etikett:** en enskild menytext, rubrik, knapp eller kolumn som blandar svenska och engelska utan tydlig produktorsak, till exempel `Pusha alla contract`.
- **Terminkonflikt:** samma funktionella begrepp får olika namn på olika platser utan att skillnaden är avsiktlig eller förklarad.
- **Tillåtna domänförkortningar:** `DS`, `VRM`, `STP`, `CPS`, `TPS`, `PBI`, `BC`, `BA`, `KPI`, `CPI`, `ANPR`, `EPMP`, `TMS`.
- **Tillåtna produkt-/systemnamn:** `Business Central`, `Park&GO`, `Oktavius`, `Power BI`, `ThirdPartySales`, `Tech Tool` när de används som system- eller produktnamn.

## Rekommenderad engelsk terminologi

Använd tabellen som konsistensreferens under testet. Om produktägaren senare beslutar andra måltermer ska testet uppdateras innan nästa Regression Mode-körning.

| Begrepp | Rekommenderad engelsk UI-term | Exempel på avvikande varianter att flagga |
| --- | --- | --- |
| Kundtjänst / CSC | Customer Service Center | Kundtjänst, CustomerService utan mellanrum |
| Kontrakt | Contract | Agreement när samma objekt avses, contract med liten bokstav i titel |
| Korttidsavtal / STP | Short-term parking contract | STP contract, korttidsavtal, engångsparkering när samma flöde avses |
| DS / anläggning | DS / Car park | Garage när DS/anläggning avses generellt, parkeringsnamn utan konsekvens |
| Garage | Garage | CarPark, Car Park, garage omväxlande i samma typ av rubrik |
| Parkeringsplats | Parking space | Place, spot, plats |
| Kund | Customer | User när juridisk/faktisk kund avses |
| Användare | User | Customer när portal-/kontoanvändare avses |
| Registreringsnummer | VRM | License plate, registration number, VRMer |
| Kö | Queue | Waiting list när samma köobjekt avses |
| Kömedlem | Queue member | Queuing customer, queue participant |
| Erbjudande | Offer | Proposal, erbjudande |
| Nyckel | Key | Access item om fysisk nyckel avses |
| Produktmall | Product template | Produktmall, Product Template List om sidans primära term skiljer sig |
| Paketmall | Package template | Package, Paketmallar utan konsekvens |
| Reklambanner | Advertisement banner | Banner, Reklam banner |
| Betalautomat | Payment machine | BA, pay machine, betalautomat |
| Fastighetsägare | Property owner | Landlord om inte juridisk roll faktiskt skiljer sig |
| Hyresvärd | Landlord | Property owner när separat hyresvärdsroll avses |
| Operatör | Operator | Provider när operatör avses |
| Allmän helgdag | Public holiday | Holiday, helgdag |
| Avslutsorsak | Termination reason | Contract termination reason, avslutsorsak |
| Logg | Log | Logs när singular/plural används inkonsekvent i motsvarande vyer |
| Audit trail | Audit trail | Audit, change log, history om samma revisionsvy avses |
| Schemaläggare | Scheduler | Scheduled task när själva schemaläggaren avses |

## Teststeg

1. Läs `raw_data\kundtjanst-funktioner-data.json` och bygg en körlista över alla objekt där `kind` är `group` eller `item`.
2. Starta eller anslut till den delade stage-browsern enligt förutsättningarna.
3. Öppna `https://sps-stage.europark.local/CustomerService`.
4. Om Microsoft-inloggning visas, låt användaren slutföra inloggningen och vänta minst **5 minuter** innan testet klassas som blockerat.
5. Kontrollera att alla toppmenyer i rådata finns synligt i navigationen.
6. För varje toppmeny:
   - öppna menyn
   - dokumentera synlig gruppetikett
   - kontrollera om gruppetiketten är engelska
   - kontrollera om gruppetiketten använder rekommenderad term
7. För varje menyval i rådata:
   - öppna menygruppen
   - dokumentera synlig menytext
   - kontrollera om menytexten är engelska
   - kontrollera om samma begrepp används konsekvent jämfört med tidigare menyval
   - klicka menyvalet om det är en intern stage-länk
   - om menyvalet är extern länk, Power BI-rapport eller öppnar ny host: dokumentera synlig länktext och landnings-URL, men skapa inga data och gör inga destruktiva åtgärder
8. På varje öppnad sida, kontrollera synliga statiska UI-texter i första renderade vyn:
   - sidtitel och huvudrubrik
   - fältetiketter och placeholders
   - knapptexter och länkar
   - tabellrubriker och DataTables-texter som `Search`, `Show entries`, pagination och tom-lista-meddelanden
   - valideringsmeddelanden och hjälprader som visas utan att spara eller skicka formulär
   - modaltitlar eller panelrubriker som visas utan att förändra data
9. Gör inte åtgärder som skapar, uppdaterar, raderar, importerar, skickar, pushar, avslutar kontrakt eller startar externa processer. För sådana sidor räcker det att granska öppningsvyn och icke-mutativa kontroller.
10. För varje identifierad svensk eller blandad UI-text, registrera:
    - menygrupp
    - menyval
    - URL/path
    - exakt observerad text
    - plats i vyn, till exempel meny, rubrik, knapp, fält, kolumn, felmeddelande
    - föreslagen engelsk term från terminologitabellen
11. För varje terminkonflikt, registrera:
    - begrepp
    - alla observerade varianter
    - var varje variant finns
    - rekommenderad canonical term
    - om varianten verkar vara produktnamn, domänförkortning eller faktiskt inkonsekvent UI-text
12. Kontrollera särskilt redan kända riskmönster:
    - `Notification Templates` förekommer under både `Gemensamma inställningar` och `Templates`
    - `Old Search Method` förekommer i flera grupper
    - `Garage`, `DS`, `CarPark` och `Car park` blandas
    - `Contract`, `Kontrakt`, `Agreement` och `contract` blandas
    - `Queue`, `Kö`, `Waiting list` och `Queue Tick Tack Toe` blandas
    - `Product Template List`, `Produktmall`, `Paketmallar` och `Package Usage Details` blandas
    - svenska menytexter förekommer i annars engelska admin- och rapportvyer
13. Avsluta med en sammanställning per menygrupp:
    - antal granskade menyval
    - antal oöversatta texter
    - antal blandade etiketter
    - antal terminkonflikter
    - blockerade eller ej nåbara sidor

## Förväntat resultat

- Alla menygrupper och menyval från `raw_data\kundtjanst-funktioner-data.json` ska kunna granskas eller uttryckligen markeras som blockerade med orsak.
- Alla statiska UI-etiketter i CSC-stage ska vara på engelska.
- Samma funktionella begrepp ska använda samma engelska term i menyer, rubriker, formulär, tabeller och knappar.
- Tillåtna domänförkortningar och produktnamn ska användas konsekvent och inte blandas med svenska böjningsformer.
- Testet ska producera en tydlig avvikelselista som kan lämnas vidare till utveckling eller översättningsansvarig.

## Slutläge

- Aktiv flik: Kundtjänstportalen stage eller sista granskade CSC-sida.
- Inga data ska ha skapats, ändrats, importerats, pushats eller raderats.

## Exekveringsgenvägar

- Menylistan behöver inte skrivas av manuellt; använd `raw_data\kundtjanst-funktioner-data.json` som checklista och verifiera den mot live-navigationen.
- För sidor som returnerar kända stage-fel ska översättning av synliga felrubriker och feltext ändå kontrolleras om sidan renderar felinnehåll.
- Power BI-sidor ska granskas på CSC-ramens synliga titel, rapportnamn och fel-/containertext; själva inbäddade rapportinnehållet är bara i scope om det är läsbart utan extra autentisering.
- DataTables-standardtexter ska räknas som UI-text och ingår i språkgranskningen.
- Sidor med `Push`, `Import`, `Create`, `End`, `Delete`, `Merge`, `Point to`, `Update` eller motsvarande riskord får öppnas men inte skickas vidare.
- Om samma URL nås från flera menyer ska den granskas en gång, men alla menyer som länkar dit ska ingå i terminkonsistenskontrollen.

## Tekniska observationer

- Rådata från 2026-08-26 innehåller 115 öppningsbara menyfunktioner plus toppmenyer.
- Rådata visar redan blandat språk i navigeringen; detta test är därför väntat att hitta avvikelser tills CSC-portalen är fullt översatt.
- Det är inte ett testfel att kunddata, garage-/platsnamn, personnamn, rapportkoder eller systemnamn innehåller svenska eller interna akronymer när de är datainnehåll snarare än UI-etiketter.
- Om browsern visar Microsoft-inloggning under flödet ska agenten låta användaren arbeta färdigt i minst **5 minuter** innan körningen stoppas eller klassas som loginfel.

## Felutfall

Testet ska markeras som underkänt om något av följande inträffar:

- minst en granskad menygrupp, menytext, rubrik, fältetikett, knapp, tabellrubrik eller systemgenererad statisk text är kvar på svenska
- en etikett blandar svenska och engelska utan tydlig produktorsak
- samma affärsbegrepp benämns med olika engelska termer på jämförbara platser
- en meny i rådata saknas i live-navigationen utan dokumenterad avsiktlig förändring
- en intern CSC-sida inte kan öppnas och det hindrar språkgranskningen av sidan
- testet inte kan täcka alla menygrupper på grund av session-, behörighets- eller inloggningsproblem

## Bevis / dokumentation

Dokumentera minst:

- datum och körläge
- vilken `capturedAt` från rådata som användes som menybaseline
- antal granskade grupper och menyval
- lista över blockerade eller ej nåbara sidor
- tabell över alla oöversatta eller blandade UI-texter
- tabell över alla terminkonflikter
- rekommenderad canonical term för varje konflikt
- om avvikelsen finns i meny, sidrubrik, fält, knapp, tabell, felmeddelande eller rapportcontainer

## Senast verifierad körning

- **Datum:** 2026-08-28
- **Körläge:** Regression Mode
- **Status:** Underkänt. Körningen granskade 12 menygrupper, 115 menyval och 115 öppnade sidor. Svenska och blandade UI-texter reproducerades i tre körningar utan blockerade sidor.
- **Rapport:** `test_reports\20260828v1\summary.md`

## Återanvändbara körlärdomar

- Kör live-inventeringen till `tmp`, inte till `raw_data`, när syftet är Regression Mode-verifiering och inte ny rådatainsamling.
- Inventeringsskriptet lämnar browsern på sista öppnade sida. För reproduktion 2 och 3 ska Kundtjänst-startsidan öppnas igen innan `Invoke-KundtjanstMenuInventory.ps1` startas, annars kan skriptet sakna matchande `CustomerService`-target.
- Vid rapportering av detta test ska fullständig findings-data sparas som artefakt i felrapporten, eftersom antalet oöversatta eller blandade UI-texter kan vara mycket stort.

## Relaterade dokument

- `raw_data\kundtjanst-funktioner-data.json`
- `manuals\csc_user_manuals\Kundtjänst - funktioner.md`
- `syntetisk_data\kundtjanst-menykarta.md`
- `syntetisk_data\common\ordlista-och-namnstandard.md`
- `tools\docs\browser-samarbete-stage-session.md`
- `tools\docs\regressionstest-arbetsmodell.md`
- `testing\regression_test\regression-test-catalog.md`
