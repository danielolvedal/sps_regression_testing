# Kundtjänst - funktioner

Analysen bygger på en live-genomgång av **stage-miljön** i Kundtjänstportalen den **2026-08-26T09:19:00**. Dokumentet beskriver vad varje menyval verkar göra utifrån faktisk navigering, synliga formulär, tabeller, knappar och felmeddelanden i UI:t.

## Omfattning

- Unika menyfunktioner genomgångna: **115**
- Metod: automatisk genomklickning av samtliga toppmenyer i den inloggade stage-sessionen
- Notering: flera poster under **Rapporter** öppnar en Power BI-container utan att exponerat detaljinnehåll kunde läsas från sidan. Där dokumenteras främst rapportens avsedda område och om länken såg frisk ut.

## Menyöversikt

| Meny | Antal funktioner |
| --- | ---: |
| Kontrakt | 8 |
| STP-tjänster | 5 |
| Rapporter | 34 |
| Garage | 7 |
| Produkt | 4 |
| Köhantering | 6 |
| Nyckelhantering | 3 |
| Loggar | 4 |
| Gemensamma inställningar | 8 |
| Templates | 3 |
| Admin | 31 |
| Användarmeny | 2 |

## Kontrakt

| Funktion | URL/path | Vad den gör | Viktiga element i vyn | Status i stage |
| --- | --- | --- | --- | --- |
| Sök | `/CustomerService` | Snabbsökning för kontrakt, kunder, DS, VRM och dokument i samma vy. Visar träfflistor direkt med länkar för redigering, VRM-hantering och dokument. | Rubriker: Kundtjänstportalen Daniel.Olvedal@apcoa.se, Betalningsmetoder | OK vid öppning i stage. |
| Sätt upp nytt kontrakt | `/CustomerService/CreateNewContract` | Startar flödet för att skapa ett nytt kontrakt genom att välja DS/anläggning. Första steget är DS-val innan vidare kontraktsuppgifter anges. | Rubriker: Skapa kontrakt - steg 1 Fält/filter: Välj ett DS-nummer, Här kommer en Google Maps-integration i framtiden, Filtrering ("all" eller "new" Åtgärder: Nästa steg | OK vid öppning i stage. |
| Ändra ett kontrakt | `/EditContract` | Startpunkt för att öppna ett befintligt kontrakt för ändring. Användaren anger kontraktsnummer och går vidare till redigeringsflödet. | Rubriker: Redigera kontrakt Fält/filter: Kontraktsnummer Åtgärder: Nästa steg | OK vid öppning i stage. |
| Ändra pris på ett kontrakt | `/CustomerService/EditContractPrice` | Ändrar priset på ett enskilt kontrakt. Stöd finns för procentuell höjning, fast belopp, KPI-baserad höjning och nytt fast pris. | Rubriker: Ändra priset på ett kontrakt Fält/filter: Kontraktsnummer, Ändringsdatum, Höjningsmetod Åtgärder: Ändra | OK vid öppning i stage. |
| Skapa kontrakt utfrån mall | `/document/CreatePrintContractFromTemplate` | Skapar/skriv ut kontraktsdokument från en vald mall. Vyn kombinerar kontraktsnummer med mallval och kan skapa PDF. | Rubriker: Skapa kontrakt utifrån mall, Created Contract Document Fält/filter: Kontraktsnummer, Kontraktsmallens namn Åtgärder: Skapa PDF, Rensa | OK vid öppning i stage. |
| Lägg till/ta bort VRMer för ett kontrakt | `/CustomerService/UpdateVrmsOnContract` | Uppdaterar registreringsnummer kopplade till ett kontrakt. Flödet utgår från kontraktsnummer och leder vidare till VRM-hantering. | Rubriker: Uppdatera VRMer på ett kontrakt Fält/filter: Kontraktsnumret Åtgärder: Nästa steg | OK vid öppning i stage. |
| Översikt av garage | `/CustomerService/GarageOverviewSelect` | Öppnar garageöversikt via valt DS-nummer. Används som startpunkt för att se status och innehåll i en anläggning. | Rubriker: Översikt av garage Fält/filter: Välj ett DS-nummer Åtgärder: Nästa steg | OK vid öppning i stage. |
| Old Search Method | `/Search` | Äldre kontraktssökning med separata sökingångar för kund, DS och dokument. Ger bred träfflista men verkar vara en legacy-vy jämfört med Quick Search. | Rubriker: Sök kontrakt, Sök efter användare Fält/filter: org.nr., E-post, Telefonnummer Kolumner: Kontraktsnummer, Kundnamn, Startdatum, Slutdatum Åtgärder: Visa, Sök, Visa | OK vid öppning i stage. |

## STP-tjänster

| Funktion | URL/path | Vad den gör | Viktiga element i vyn | Status i stage |
| --- | --- | --- | --- | --- |
| Skapa nytt korttidsavtal | `/ShortTermParking/NewContractStep1` | Startar skapande av korttidsavtal för engångs-/korttidsparkering. Första steget är att ange DS för den parkering avtalet ska gälla. | Rubriker: Skapa kontrakt - steg 1 - DS info Fält/filter: DS-numret till den parkering du vill skapa ett kontrakt för Åtgärder: Nästa steg | OK vid öppning i stage. |
| Redigera korttidsavtal | `/ShortTermParking/EditContractStep1` | Öppnar befintligt korttidsavtal för ändring. Sker via kontraktsnummer. | Rubriker: Redigera kontrakt Fält/filter: Kontraktsnummer Åtgärder: Nästa steg | OK vid öppning i stage. |
| Old Search Method | `/Search` | Återanvänder den äldre sökvyn även för STP-flöden. Kan användas för att hitta kontrakt före vidare handläggning. | Rubriker: Sök kontrakt, Sök efter användare Fält/filter: org.nr., E-post, Telefonnummer Kolumner: Kontraktsnummer, Kundnamn, Startdatum, Slutdatum Åtgärder: Visa, Sök, Visa | OK vid öppning i stage. |
| Översiktlig statistik för engångsparkering | `/OneTimeParking/GetOverviewStatistics` | Visar sökbar statistik för engångsparkering och kan exportera rådata till Excel. Tabellen är filtrerbar på bland annat DS, kund, VRM och starttid. | Rubriker: Översiktlig statistik för engångsparkering Fält/filter: Input Kolumner: DS Number, DS, Kund, VRM Åtgärder: Sök, Skapa Excel-fil på rådata | OK vid öppning i stage. |
| Receptionsservice kontrakt | `/ContractReport/GetReceptionServiceContracts` | Listar receptionsservicekontrakt och låter användaren söka på kontrakt eller DS. Vyn visar start/slutdatum, kund och servicetyp. | Rubriker: Lista på Receptionsservice kontrakt Fält/filter: Kontrakt eller DS nummer Kolumner: Kontrakt, Startdatum, Slutdatum, DS Åtgärder: Sök | OK vid öppning i stage. |

## Rapporter

| Funktion | URL/path | Vad den gör | Viktiga element i vyn | Status i stage |
| --- | --- | --- | --- | --- |
| OP - 8D Stage | `/powerbi/loadbireport?report=PBI_OP_8D_%20NEW_LAYOUT` | Öppnar Power BI-rapporten **OP - 8D Stage** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Öppnar Power BI-rapport/container. |
| SPS - 2C - Kontraktöversikt | `/powerbi/loadbireport?report=PBI_SPS_Internal_Overview_contracts` | Öppnar Power BI-rapporten **SPS - 2C - Kontraktöversikt** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Öppnar Power BI-rapport/container. |
| FIN - 3E - Control Fees & Customer Compensation Report (COOP) | `/powerbi/loadbireport?report=PBI_FIN_COOP` | Öppnar Power BI-rapporten **FIN - 3E - Control Fees & Customer Compensation Report (COOP)** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Öppnar Power BI-rapport/container. |
| OP - 1A - Occupancy Rate Repot NEW | `/powerbi/loadbireport?report=PBI_SPS_Internal_Occupancy` | Öppnar Power BI-rapporten **OP - 1A - Occupancy Rate Repot NEW** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Fel i stage: Power BI-rapporten saknas eller pekar på ogiltigt ReportID/workspace. |
| OP - 4E - kW förbrukning | `/powerbi/loadbireport?report=PBI_EVC_kW` | Öppnar Power BI-rapporten **OP - 4E - kW förbrukning** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Öppnar Power BI-rapport/container. |
| FIN - 5E - Resultatrapport | `/powerbi/loadbireport?report=PBI_FIN_5E_Resultat` | Öppnar Power BI-rapporten **FIN - 5E - Resultatrapport** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Öppnar Power BI-rapport/container. |
| FIN - 2E - COREM | `/powerbi/loadbireport?report=PBI_FIN_Corem` | Öppnar Power BI-rapporten **FIN - 2E - COREM** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Öppnar Power BI-rapport/container. |
| OP - New Business rapporten | `/powerbi/loadbireport?report=PBI_NB_report` | Öppnar Power BI-rapporten **OP - New Business rapporten** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Öppnar Power BI-rapport/container. |
| 5 - SPS Contracts SPS-BC_Prod | `/powerbi/loadbireport?report=PBI%20-%20SPS%2FBC` | Öppnar Power BI-rapporten **5 - SPS Contracts SPS-BC_Prod** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Öppnar Power BI-rapport/container. |
| OP - X400 - Triangeln Beläggningsgrad | `/powerbi/loadbireport?report=PBI_Internal_Triangeln_Occupancy%20` | Öppnar Power BI-rapporten **OP - X400 - Triangeln Beläggningsgrad** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Öppnar Power BI-rapport/container. |
| SPS - 1C - Kölista och Lediga platser | `/powerbi/loadbireport?report=PBI_SPS_Internal_Quelist` | Öppnar Power BI-rapporten **SPS - 1C - Kölista och Lediga platser** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Öppnar Power BI-rapport/container. |
| SPS- 1F - Kontraktsöversikt med kontaktuppgifter | `/powerbi/loadbireport?report=PBI_SPS_Internal_Contactinfo` | Öppnar Power BI-rapporten **SPS- 1F - Kontraktsöversikt med kontaktuppgifter** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Fel i stage: Power BI-rapporten saknas eller pekar på ogiltigt ReportID/workspace. |
| SPS - 2D - Översikt Betalautomater | `/powerbi/loadbireport?report=PBI_SPS_Internal_Overview_paymachines` | Öppnar Power BI-rapporten **SPS - 2D - Översikt Betalautomater** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Öppnar Power BI-rapport/container. |
| FIN - 1E - Intäktskontroll | `/powerbi/loadbireport?report=PBI_FIN_Intaktskontroll` | Öppnar Power BI-rapporten **FIN - 1E - Intäktskontroll** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Öppnar Power BI-rapport/container. |
| FIN - 7E - Jernhusen - kontrakt och procensatser per DS och konto | `/powerbi/loadbireport?report=PBI_Internal_Jernhusen` | Öppnar Power BI-rapporten **FIN - 7E - Jernhusen - kontrakt och procensatser per DS och konto** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Öppnar Power BI-rapport/container. |
| OP - 1D - NK solution report | `/powerbi/loadbireport?report=PBI_OP_NK_Solution` | Öppnar Power BI-rapporten **OP - 1D - NK solution report** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Öppnar Power BI-rapport/container. |
| OP - 1 - TPS Prebooking Report_Prod | `/powerbi/loadbireport?report=1%20-%20TPS%20%20Prebooking%20Report_Prod` | Öppnar Power BI-rapporten **OP - 1 - TPS Prebooking Report_Prod** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Öppnar Power BI-rapport/container. |
| Report to audit the payments and events from EPMP | `/powerbi/loadbireport?report=PBI%20-%20Silver%20Audit%20Report` | Öppnar Power BI-rapporten **Report to audit the payments and events from EPMP** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Fel i stage: Power BI-rapporten saknas eller pekar på ogiltigt ReportID/workspace. |
| SALES - Park & Go Dashboard FIKTIV | `/powerbi/loadbireport?report=PBI_FAKE_ParknGO_Dashboard_Internal` | Öppnar Power BI-rapporten **SALES - Park & Go Dashboard FIKTIV** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Öppnar Power BI-rapport/container. |
| FIN - 8E - LOCUM Redovisning | `/powerbi/loadbireport?report=PBI_FIN_Locum` | Öppnar Power BI-rapporten **FIN - 8E - LOCUM Redovisning** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Öppnar Power BI-rapport/container. |
| FIN - 12E - NB Contract Deviation Report | `/powerbi/loadbireport?report=PBI_Internal_Contract_Deciation` | Öppnar Power BI-rapporten **FIN - 12E - NB Contract Deviation Report** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Öppnar Power BI-rapport/container. |
| FIN - 14E - Sales By DS | `/powerbi/loadbireport?report=PBI_SalesDS` | Öppnar Power BI-rapporten **FIN - 14E - Sales By DS** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Öppnar Power BI-rapport/container. |
| SALES- Park & Go rapport FIKTIV | `/powerbi/loadbireport?report=PBI_FAKE_ParknGO_Internal` | Öppnar Power BI-rapporten **SALES- Park & Go rapport FIKTIV** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Öppnar Power BI-rapport/container. |
| OP - 8D - Park & Go Statistik | `/powerbi/loadbireport?report=PBI_PG_Internal` | Öppnar Power BI-rapporten **OP - 8D - Park & Go Statistik** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Fel i stage: Power BI-rapporten saknas eller pekar på ogiltigt ReportID/workspace. |
| OP - 9 TMS Rapport | `/powerbi/loadbireport?report=PBI_TMS` | Öppnar Power BI-rapporten **OP - 9 TMS Rapport** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Öppnar Power BI-rapport/container. |
| SPS - 2B - Platsstatus - Översikt av garage | `/powerbi/loadbireport?report=PBI_SPS_Internal_platsstatus` | Öppnar Power BI-rapporten **SPS - 2B - Platsstatus - Översikt av garage** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Öppnar Power BI-rapport/container. |
| FIN - 10E - Invoice Info Vaskaronan | `/powerbi/loadbireport?report=PBI_FIN_Invoice_vasakronan` | Öppnar Power BI-rapporten **FIN - 10E - Invoice Info Vaskaronan** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Öppnar Power BI-rapport/container. |
| OP - 8xd - Park & Go beläggningsgrad | `/powerbi/loadbireport?report=PBI_PG_occupancy_Internal` | Öppnar Power BI-rapporten **OP - 8xd - Park & Go beläggningsgrad** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Fel i stage: Power BI-rapporten saknas eller pekar på ogiltigt ReportID/workspace. |
| OP - 7 - Uppföljning Kontrollavgifter | `/powerbi/loadbireport?report=PBI_OP_KA` | Öppnar Power BI-rapporten **OP - 7 - Uppföljning Kontrollavgifter** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Fel i stage: Power BI-rapporten saknas eller pekar på ogiltigt ReportID/workspace. |
| FIN - 6E - JÄRVA Redovisning | `/powerbi/loadbireport?report=PBI_FIN_Jarva` | Öppnar Power BI-rapporten **FIN - 6E - JÄRVA Redovisning** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Öppnar Power BI-rapport/container. |
| SPS - 1B - Fastighetsägare, zoner och områden | `/powerbi/loadbireport?report=PBI_SPS_Internal_zoner` | Öppnar Power BI-rapporten **SPS - 1B - Fastighetsägare, zoner och områden** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Öppnar Power BI-rapport/container. |
| VSP CP Report | `/powerbi/loadbireport?report=PBI_VSP_CPReport` | Öppnar Power BI-rapporten **VSP CP Report** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Öppnar Power BI-rapport/container. |
| OP - 3R - Översikt Hotell/Receptionstjänsten | `/powerbi/loadbireport?report=PBI-SPS_Internal_servicecontracts` | Öppnar Power BI-rapporten **OP - 3R - Översikt Hotell/Receptionstjänsten** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Öppnar Power BI-rapport/container. |
| SPS - 4 - Fastighetsägare, Hyresvärd och Operatör | `/powerbi/loadbireport?report=PBI_SPS_Internal_PropOwnLandlordOperator` | Öppnar Power BI-rapporten **SPS - 4 - Fastighetsägare, Hyresvärd och Operatör** i inbäddad rapportvy. | Power BI-vy via rapportnyckel. | Öppnar Power BI-rapport/container. |

## Garage

| Funktion | URL/path | Vad den gör | Viktiga element i vyn | Status i stage |
| --- | --- | --- | --- | --- |
| Ändra pris på flera kontrakt på ett DS | `/CustomerService/BatchEditContractPrice` | Massuppdaterar pris på flera kontrakt inom ett DS. Utgår från DS-nummer och har avancerade sök-/filtermöjligheter. | Rubriker: Ändra priset för flera kontrakt i ett DS, Advance Search Fält/filter: DS-numret, Search Text Åtgärder: Nästa steg, Search, Clear All | OK vid öppning i stage. |
| Avsluta alla kontrakt på ett DS | `/CustomerService/EndAllContractsInDs` | Massavslutar samtliga kontrakt i en anläggning. Kräver DS-nummer och gemensamt avslutsdatum. | Rubriker: Avsluta alla kontrakt i ett DS Fält/filter: DS-numret för vilket du vill avsluta alla kontrakt för, Datumet som alla kontrakt skall avslutas på Åtgärder: Nästa steg | OK vid öppning i stage. |
| Lägg till DS | `/Garage/CreateNewDS` | Startar guiden för att skapa ett nytt garage/DS. Första steget är att ange nytt DS-nummer. | Rubriker: Skapa ett nytt garage, steg 1 Fält/filter: DS-numret för det nya garaget Åtgärder: Nästa steg | OK vid öppning i stage. |
| Sök DS | `/Garage/EditGarageInformationNew` | Öppnar ett befintligt DS för redigering av garageinformation. Vyn används för ändring av anläggningsdata. | Rubriker: Ändra information om ett garage Fält/filter: Välj ett DS-nummer Åtgärder: Nästa steg | OK vid öppning i stage. |
| Visa betalautomater per DS | `/Garage/PaymentMachinebyDS` | Söker fram betalautomater per DS eller BA-nummer. Tomt sökfält visar hela anläggningsregistret enligt sidtexten. | Rubriker: Visa betalautomater per DS Fält/filter: Skriv in BA nummer eller lämna fältet tomt Åtgärder: Starta sökning | OK vid öppning i stage. |
| Registrera eller kontrollera BA i lagret | `/Garage/BAInformationDS` | Avsedd för lagerhantering/kontroll av BA-enheter. I stage returnerar sidan för närvarande ett modell-/view-fel i stället för funktionellt innehåll. | Rubriker: Server Error in '/' Application., The model item passed into the dictionary is of type 'System.Linq.Enumerable+WhereSelectListIterator`2[Apcoa.Entities.PaymentMachineStorage,apcoa_csc_frontend.ViewModels.ConfigureGarage.GarageBAStorageViewModel]', but this dictionary requires a model item of type 'System.Collections.Generic.IEnumerable`1[Apcoa.Common.DTOs.BAStorage]'. | Fel i stage: sidan returnerar serverfel. |
| Audit trail - Garage informations | `/Garage/GetAuditTrail` | Visar audit trail för ändringar i garage och parkeringsstruktur. Kan filtreras på händelse, DS, datum och användare samt exporteras till Excel. | Rubriker: CarPark Audit Trail Fält/filter: Event:, DS Number, Updated On: Kolumner: Händelse, DS-nummer, Uppdaterad på, Uppdaterad av Åtgärder: Search, Ladda ned Excel-fil | OK vid öppning i stage. |

## Produkt

| Funktion | URL/path | Vad den gör | Viktiga element i vyn | Status i stage |
| --- | --- | --- | --- | --- |
| Produktmall | `/Product/GetProductTemplate` | Administrerar produktmallar. Listan visar bland annat BC-kod, skattenivå, köavgiftsflagga och tillståndsschema. | Rubriker: Produktmallar Fält/filter: Visa 10 25 50 100 rader, Sök: Kolumner: Produktmall, BC-kod, Skattenivå %, Köavgifter tillämpliga Åtgärder: Skapa en ny produktmall | OK vid öppning i stage. |
| Paketmallar | `/Product/GetPackageTemplate` | Administrerar paketmallar och visar hur de används. Tabellen listar paketnamn, antal produktmallar samt avgifts-/momsrelaterad information. | Rubriker: Product Template List, Package Usage Details Fält/filter: Visa 10 25 50 100 rader, Sök: Kolumner: Name, Description, DS Number, Garage Name Åtgärder: Close, Close, Skapa paketmall | OK vid öppning i stage. |
| Reklambanner | `/Product/Banners` | Administrerar reklambanners för kundgränssnitt eller kampanjytor. Stöd finns för att skapa ny banner och se status per bannerplacering. | Rubriker: Reklam banners Fält/filter: Show 10 25 50 100 entries, Search: Kolumner: Fana, Plats för reklam, Status, Hantering Åtgärder: Skapa ny reklambanner | OK vid öppning i stage. |
| Audit trail - Products and packages | `/Product/GetAuditTrail` | Visar ändringshistorik för produkter och paket. Filtrering sker på händelse, datum och användare. | Rubriker: Products Audit Trail Fält/filter: Event:, Updated On:, Updated By: Kolumner: Händelse, Garage namn, Uppdaterad på, Uppdaterad av Åtgärder: Search, Details, Details | OK vid öppning i stage. |

## Köhantering

| Funktion | URL/path | Vad den gör | Viktiga element i vyn | Status i stage |
| --- | --- | --- | --- | --- |
| Visa alla köande | `/Queuing/ShowAllQueues` | Visar samtliga köer i systemet. Tabellen innehåller namn, DS, garage, skapandedatum, månadsavgifter och antal kömedlemmar. | Rubriker: Alla köer Fält/filter: Search:, Poster per sida: Kolumner: Namn, DS-nummer, Garagenamn, Kö skapad datum Åtgärder: Nästa | OK vid öppning i stage. |
| Alla ködeltagare | `/Queuing/ShowAllMembers` | Visar kömedlemmar över alla köer. Innehåller köposition, identitet, kontaktuppgifter och åtgärder som erbjudande eller borttagning. | Rubriker: Alla kömedlemmar Kolumner: Köposition, Datum när kunden började köa, Identifikationsnummer, Namn Åtgärder: Sök, Uppdatera, Q-900921-000134779 | OK vid öppning i stage. |
| Visa kö för garage | `/Queuing/SearchQueueForGarage` | Söker fram köer kopplade till ett specifikt DS. Flödet startar med val av DS. | Rubriker: Sök kö för garage Fält/filter: Välj ett DS-nummer Åtgärder: Nästa steg | OK vid öppning i stage. |
| Sök kö för användare | `/Queuing/SearchQueueForUser` | Söker fram köhistorik eller aktiva köer för en användare. Flödet startar med användarsökning. | Rubriker: Sök kö för användare Fält/filter: Sök användare Åtgärder: Nästa steg | OK vid öppning i stage. |
| Visa erbjudanden | `/Queuing/ShowOffers` | Visar alla utskickade köerbjudanden. Listan innehåller mottagare, kontaktuppgifter, DS, garage och erbjudandestatus/händelser. | Rubriker: Alla köerbjudanden Fält/filter: Show: Kolumner: Name, Email, Phone Number, DS Number Åtgärder: Search, Reset, Nästa ➡ | OK vid öppning i stage. |
| Automatisk kundimport | `/Queuing/XpertParkingSessions` | Administrerar kundimportsessioner till kölistor. Vyn innehåller sessionnamn, välkomstfraser, villkor och möjlighet att skapa nya importlänkar. | Rubriker: kundimportlänk Fält/filter: Show 10 25 50 100 entries, Search: Kolumner: Session namn, Välkomstfras, Boarding Phrase, Villkor Åtgärder: Skapa | OK vid öppning i stage. |

## Nyckelhantering

| Funktion | URL/path | Vad den gör | Viktiga element i vyn | Status i stage |
| --- | --- | --- | --- | --- |
| Key Inventory | `/Key` | Avsedd som nyckelregister/inventarie. Sidan kraschar i stage innan inventarielistan kan visas. | Rubriker: Server Error in '/' Application., Value cannot be null. Parameter name: source | Fel i stage: sidan returnerar serverfel. |
| Manage Key Types | `/Key/GetKeyTypes` | Administrerar typer av nycklar/taggar/fjärrkontroller. Man kan skapa, ändra och ta bort nyckeltyper. | Rubriker: Key Types Kolumner: Name, Action Åtgärder: Create New, No, Yes | OK vid öppning i stage. |
| CarPark Key Settings | `/Key/CarParkKeySettings` | Konfigurerar nyckelinställningar per DS. Flödet börjar med DS-val, sannolikt för att koppla nyckelregler till anläggning. | Fält/filter: DS-numret, Här kommer en Google Maps-integration i framtiden, Filtrering ("all" eller "new" Åtgärder: Nästa steg | OK vid öppning i stage. |

## Loggar

| Funktion | URL/path | Vad den gör | Viktiga element i vyn | Status i stage |
| --- | --- | --- | --- | --- |
| Oktavius valideringslogg | `/Log/GetOktaviusLogOnVrm` | Hämtar Oktavius-logg per VRM, tidsspann och DS. Används för felsökning av valideringar kopplade till registreringsnummer. | Rubriker: Hämta Oktaviuslog Fält/filter: Vrm, Time Span From, Time Span To Åtgärder: Hämta | OK vid öppning i stage. |
| Kontraktssynkroniseringsloggar | `/Log/GetContractSyncLogs` | Visar synkloggar för kontrakt mot Business Central och EPMP. Har filter för DS, kontrakt, åtgärdstyp och fel-only samt knapp för att pusha om misslyckade kontrakt. | Rubriker: Visa Contract Sync, Show Logs for contract: Fält/filter: Enter DS Number, Enter Contract Number, Select Action Type Kolumner: IncidentID, Datum, Tid, Objekt Åtgärder: Hämta, Push All Failed Contracts, Tillbaka | OK vid öppning i stage. |
| Audit trail - Contract parking | `/AuditTrail/GetAuditTrail` | Visar ändringshistorik för kontrakt och kontraktsparkering. Kan filtreras på händelse, kontrakt, DS, garage och datum samt exporteras. | Rubriker: Audit Trail Fält/filter: Event:, Contract Number:, Garage DS: Kolumner: Händelse, Kontraktsnummer, DS nummer, Garage namn Åtgärder: Search, Ladda ned Excel-fil | OK vid öppning i stage. |
| Backend Process Events | `/CustomerService/ProcessEvents?eventType=0` | Övervakar backendjobb och processhändelser. Visar skapad tid, status, klar-tid, progress och eventtyp. | Rubriker: Backend Processes Kolumner: Created On, Status, Completed On, Progress % Åtgärder: Back | OK vid öppning i stage. |

## Gemensamma inställningar

| Funktion | URL/path | Vad den gör | Viktiga element i vyn | Status i stage |
| --- | --- | --- | --- | --- |
| Tillståndsscheman | `/Product/PermitSchedules` | Administrerar tillståndsscheman och giltighetstider. Vyn innehåller dagliga/veckovisa/årliga tider samt CRUD för schemarader. | Rubriker: NUVARANDE TILLSTÅNDSTIDER (NAMN), Yearly valid time Fält/filter: Show 10 25 50 100 entries, Search:, januari Kolumner: Name, Actions, From, To Åtgärder: Lägg till tillståndsschemarad, Load, Edit | OK vid öppning i stage. |
| Skattesatser | `/Product/GetTaxRates` | Administrerar momsmallar/skattesatser. Visar namn, momsprocent och stöd för att lägga till, ändra eller ta bort. | Rubriker: Befintliga momsmallar Kolumner: Namn, Moms i procent, Action Åtgärder: Lägg till skattesats, Ändra, Ta bort | OK vid öppning i stage. |
| BC-koder | `/Product/GetBCCodes` | Administrerar Business Central-koder och deras egenskaper. Listan visar namn, beskrivning, avgiftstyp, servicetyp och aktiv-status. | Rubriker: Befintliga Bc-Koder Kolumner: Name, Description, FeeType, ServiceType Åtgärder: Skapa BC-kod, Ändra, Ta bort | OK vid öppning i stage. |
| Notification Templates | `/NotificationEvent/NotificationTemplate` | Administrerar notifieringsmallar för händelser i systemet. Listan visar event, kontraktsfilter, mallnamn, version, typ och publicering. | Fält/filter: Visa 10 25 50 100 rader, Sök: Kolumner: Event, Contract Filter, Template Name, Version Åtgärder: Add New Template | OK vid öppning i stage. |
| Administrera fastighetsägare/hyresvärd/operatör för ett DS | `/CustomerService/ManageCarParkEntities` | Kopplar eller ändrar fastighetsägare, hyresvärd och operatör för en anläggning. Utgår från DS-nummer. | Rubriker: Hantera hyresvärd m.m. i garage Åtgärder: Hämta | OK vid öppning i stage. |
| Uppdatera KPI | `/CustomerService/UpdateCpi` | Avsedd för uppdatering av KPI/CPI-värden som används i prislogik. Sidan returnerar null-reference-liknande fel i stage och kunde inte granskas funktionellt. | Rubriker: Server Error in '/' Application., Value cannot be null. Parameter name: value | Fel i stage: sidan returnerar serverfel. |
| Definiera Allmänna helgdagar | `/Garage/AddPublicHolidays` | Administrerar helgdagar och stödjer kopiering mellan år. Vyn visar datum, typ och beskrivning samt har knappar för kopiering och sparning. | Rubriker: Allmänna helgdagar Fält/filter: Visa 10 25 50 100 rader, Sök:, Copy From Year Kolumner: Description, Datum, Type, Redigera Radera Åtgärder: Copy Holidays, Spara | OK vid öppning i stage. |
| Contract Termination Reasons | `/ContractTerminationReason` | Administrerar orsaker för kontraktsuppsägning. Listan innehåller reason/description och stöd för att lägga till och redigera. | Fält/filter: Visa 10 25 50 100 rader, Sök: Kolumner: Reason, Description, Edit Åtgärder: Add New | OK vid öppning i stage. |

## Templates

| Funktion | URL/path | Vad den gör | Viktiga element i vyn | Status i stage |
| --- | --- | --- | --- | --- |
| Notification Templates | `/NotificationEvent/NotificationTemplate` | Samma template-register som under Gemensamma inställningar. Används för hantering och publicering av notifieringsmallar. | Fält/filter: Visa 10 25 50 100 rader, Sök: Kolumner: Event, Contract Filter, Template Name, Version Åtgärder: Add New Template | OK vid öppning i stage. |
| Skapa nya kontraktsmallsrader | `/CustomerService/ContractTemplateEditor` | Editor för kontraktsmallsrader och innehållsblock. Stöd finns för text, länkar, typografi/färgval och utskrift/preview. | Rubriker: Skapa nya kontraktsmallsrader, Rubrik 1 Fält/filter: Kontraktsmallens namn, Inneheållet i kontraktsmallen, Visningstext Åtgärder: Open Sans, Genomskinlig, Återställ till standard | OK vid öppning i stage. |
| Skapa ny kontraktsmall | `/CustomerService/CreateContractTemplate` | Skapar en ny övergripande kontraktsmall. Vyn visar befintliga mallar och tillgängliga fält/variabler. | Rubriker: Skapa kontraktsmall, Mallens namn Åtgärder: Skapa mall | OK vid öppning i stage. |

## Admin

| Funktion | URL/path | Vad den gör | Viktiga element i vyn | Status i stage |
| --- | --- | --- | --- | --- |
| Pusha ett kontrakt till Business Central | `/CustomerService/PushContractToBusinessCentral` | Startar om synkning av ett enskilt kontrakt till Business Central. Visar samtidigt historik/loggar för tidigare försök. | Rubriker: Push single contract to Business Central Fält/filter: Enter Contract Number, Visa 10 25 50 100 rader Kolumner: EventID, Datum, Tid, Objekt Åtgärder: Pusha, Refresh | OK vid öppning i stage. |
| Pusha alla contract i ett DS till Business Central | `/CustomerService/PushDSContractsToBusinessCentral` | Startar om synkning av alla kontrakt inom ett DS till Business Central. Visar tidigare sync-event och fel per körning. | Rubriker: Pusha All kontrakt in DS till BusinessCentral Fält/filter: Ds, Visa 10 25 50 100 rader Kolumner: EventID, Datum, Tid, Objekt Åtgärder: Pusha, Refresh | OK vid öppning i stage. |
| Pusha samtliga kontrakt till Business Central | `/CustomerService/PushAllContractsToBusinessCentral` | Masspushar alla kontrakt till Business Central. Är en bred administrativ återkörning med logglista på samma sida. | Rubriker: Pusha alla kontrakt till BusinessCentral Fält/filter: Visa 10 25 50 100 rader Kolumner: EventID, Datum, Tid, Objekt Åtgärder: Pusha, Refresh | OK vid öppning i stage. |
| Pusha samtliga kontrakt till Park&GO | `/CustomerService/PushAllContractsToEPMP` | Masspushar kontrakt till EPMP/Park&GO. Visar progress per DS med pending/total contracts. | Rubriker: Pusha alla kontrakt till EPMP Fält/filter: Sök: Kolumner: DS, Pending Contracts, Total Contracts, Progress Åtgärder: Pusha | OK vid öppning i stage. |
| Skapa en ny VRM-pool för ett kontrakt | `/CustomerService/CreateNewVrmPoolOnContract` | Bryter ut ett kontrakt till en ny VRM-pool. Sidan beskriver att kontrakt flyttas till den nya poolen tillsammans med valda VRMer. | Rubriker: Skapa en ny VRM pool för ett kontrakt, kontrakten kommer att flyttas till den nya poolen Fält/filter: Kontraktsnummer, VRMer i poolen Åtgärder: Skapa ny VRM-pool | OK vid öppning i stage. |
| Slå ihop VRM-poolerna för ett kontrakt | `/CustomerService/MergeVrmPools` | Slår ihop flera kontrakts VRM-pooler. Kräver kontrakt, nytt poolnamn och beskrivning. | Rubriker: Slå ihop flera kontrakts VRM-pooler Fält/filter: Kontrakts som skall slås ihop, VRM-poolens namn, Beskrivning av VRM-poolen Åtgärder: Slå ihop | OK vid öppning i stage. |
| Peka om ett kontrakt till en annan VRM-pool | `/CustomerService/PointToNewVrmPool` | Flyttar ett kontrakt till en befintlig VRM-pool. Utgår från kontraktsnummer och vald pool. | Rubriker: Peka om ett kontrakt till en ny VRM-pool Fält/filter: Kontraktsnumret, VRM-poolen Åtgärder: Peka om | OK vid öppning i stage. |
| Se kontrakt på VRM-pool | `/Search/SeeContractsOnVrmPool` | Visar vilka kontrakt som ligger på en viss VRM-pool. Sökbar tabell med pool och kontraktsnummer. | Rubriker: Se kontrakt på VRM-pool Fält/filter: Ange VRM-poolen, Visa 10 25 50 100 rader, Sök: Kolumner: VRM-pool, Kontraktsnummer Åtgärder: Sök | OK vid öppning i stage. |
| Hantera VRM-pooler på kund | `/Search/ManagePoolsOnLegalEntity` | Visar och administrerar VRM-pooler per kund. Stöd finns för att slå samman pooler, öppna kontrakt och redigera poolkopplingar. | Rubriker: Hantera VRM-pooler på kund, Slå samman VRM-pooler Fält/filter: Sök på en kund, Visa 10 25 50 100 rader, Sök: Kolumner: Kund, Person-/Org. nr, VRM-pool, Redigera VRM-pool Åtgärder: Sök, Slå samman | OK vid öppning i stage. |
| Audit | `/Audit` | Exporterar auditdata till CSV. Användaren väljer teckenkodning innan filen hämtas. | Rubriker: Audit, Tryck på knappen nedan för att hämta filen Fält/filter: CsvFormat Åtgärder: Hämta fil | OK vid öppning i stage. |
| API Users Settings | `/ExternalAPIUsers` | Administrerar externa API-användare och tokenperioder. Listan visar kund, token-start, token-expiry och åtkomsthantering. | Rubriker: External API Users Fält/filter: Visa 10 25 50 100 rader, Sök: Kolumner: Customer Name, Token Start Date, Token expiry date, Token and access Management | OK vid öppning i stage. |
| Wallboard Messages | `/CustomerService/WallBoardMessage` | Administrerar meddelanden som visas på wallboard/interna ytor. Listan innehåller meddelandetyp, start/slutdatum, aktiv-flagga och redigering. | Rubriker: WallBoard Messages, Glöm inte möte varje vardag kl 15.00 Fält/filter: 2020-05-12, 2020-05-14, 2020-06-30 Kolumner: Message, Message type, Start Date, End Date | OK vid öppning i stage. |
| Schemaläggaren | `/Scheduler` | Avsedd för schemaläggningsöversikt eller jobbhantering. Sidan ger serverfel i stage och kunde inte granskas vidare. | Rubriker: Server Error in '/' Application., Object reference not set to an instance of an object. | Fel i stage: sidan returnerar serverfel. |
| Konfigurationer för schemalagda uppgifter | `/Scheduler/ScheduledTasks` | Visar cron-konfiguration för schemalagda uppgifter. Listan innehåller nyckel, cron-uttryck, beskrivning, nästa körning och typ. | Rubriker: Scheduled Tasks Kolumner: Key, Cron Expression, Description, Next Run | OK vid öppning i stage. |
| Running microservices and scheduled task | `/SysDaemonsStatus` | Visar driftstatus för mikrotjänster och schemalagda jobb. Innehåller adress, port, aktiv-status, heartbeat och senaste fel. | Rubriker: SysDaemons, Repeat Schedule Jobs Fält/filter: Visa 10 25 50 100 rader Kolumner: Name, Address, Port, Active | OK vid öppning i stage. |
| PBI Reports | `/PowerBi/GetPBIReports` | Administrerar Power BI-rapportdefinitioner i SPS. Listan visar report key, beskrivning, workspace-id, report-id och rapporttyp. | Rubriker: Power BI Reports Fält/filter: Visa 10 25 50 100 rader, Sök: Kolumner: ReportKey, ReportDescription, WorkSpaceId, ReportId Åtgärder: Add New Report, No, Yes | OK vid öppning i stage. |
| Migrate DS | `/Migration` | Verktyg för migrering av anläggningar från legacy till SPS. Listan visar kontraktsvolymer och migrationsstatus, men stage kunde inte läsa in car parks just nu. | Rubriker: Car Park Migration, Car Parks Fält/filter: Show 5 10 20 50 entries, Search: Kolumner: DS Number, Name, Active Contracts, InActive Contracts Åtgärder: Resume Migration, Resume Migration, View Result | Delvis fel i stage: sidan öppnas men data kunde inte laddas. |
| Kontraktsimport | `/ContractImport/ContractImportsList` | Visar och startar kontraktsimporter. Stöd finns för ny import, fortsättning av pågående import och visning/radering av körningar. | Rubriker: Contract Imports Fält/filter: Status, Page size Kolumner: Created Date, DS Number, Package, User Åtgärder: Starta ny import, View, Delete | OK vid öppning i stage. |
| My Active Directory Profile | `/ADProfile/GetProfile` | Hämtar en användares AD-profil direkt från Active Directory. Visar gruppmedlemskap och förklarar att datat inte lagras i SPS. | Rubriker: Get Active Directory Profile Fält/filter: UserName, Password, * This information is not stored in SPS. It is coming directly from Active Directory Kolumner: Sr., Group Member List Åtgärder: Get Profile | OK vid öppning i stage. |
| Administrera attribut | `/Product/GetParkingSpaceAttributeGroup` | Administrerar attributgrupper för parkeringsplatser. Visar gruppnamn, val-läge, visningsprioritet och CRUD-åtgärder. | Rubriker: Lägg till grupp för attribut, Lista över attributgrupper för parkeringsplatser Fält/filter: Visa 10 25 50 100 rader, Sök: Kolumner: Grupp namn, Gruppläge, Visningsprioritet, Handlingar Åtgärder: Close, Lägg till attributgrupp, Ändra | OK vid öppning i stage. |
| Queue Tick Tack Toe | `/Garage/TickTackToeForQueue` | Specialvy för kömatris per DS. Endast DS-sökning framgår i första steget. | Fält/filter: DsNumber Åtgärder: Sök | OK vid öppning i stage. |
| Queue Import | `/` | Länk till separat queue-import-tjänst. I denna session gick extern adress inte att nå. |  | Ej öppnad automatiskt av säkerhets-/sessionskäl. |
| Tech Tool | `/tech-tool/auth/csc-handoff?REDACTED` | Länk vidare till separat tekniskt verktyg via CSC-handoff. Sidan vidarebefordrar användaren till intern stage-domän för FlowField/tech-tool. |  | Vidarelänkar till separat internt verktyg. |
| Company Administrator | `/LegalEntity/LoadMyCompany` | Detaljvy för juridiska personer/bolag med adress- och kontaktpersonshantering. Visar rollflaggor som landlord/property owner/customer och låter användaren spara ändringar. | Rubriker: Organisation Detail, 776439-7777 - Apcoa Parking Sverige AB Fält/filter: HasSignedGdprAgreement, IsLandlord, IsPropertyOwner Kolumner: Name, Email, Phone, Mobile Åtgärder: Add New Address, Spara ändringar, Create New | OK vid öppning i stage. |
| Customers | `/LegalEntity/LegalEntities` | Söker fram kunder/juridiska personer. Resultatlistan visar personnummer, namn, företagsflagga och Sales Force-id. | Rubriker: Kunder Fält/filter: Kundens namn eller org/personnummer, Visa 10 25 50 100 rader Kolumner: Personnummer, Namn, Eller företagskund, Sales Force Id Åtgärder: Sök | OK vid öppning i stage. |
| Fastighetsägare | `/LegalEntity/Landlords` | Söker fram fastighetsägare/hyresvärdar. Resultatlistan visar person-/organisationsnummer och namn. | Rubriker: Fastighetsägare Fält/filter: Fastighetsägare namn eller org/personnummer, Visa 10 25 50 100 rader Kolumner: Personnummer, Namn Åtgärder: Sök | OK vid öppning i stage. |
| CPS Dashboard | `/CPS` | Dashboard för hantering av personalparkeringstillstånd (CPS). Stöd finns för organisationshantering, verifieringar och allokering av DS. | Rubriker: CPS - Hantering av personalparkeringstillstånd, Organisationer Fält/filter: Verifiera aktivt kontrakt, Verifiera accessprofil, Verifiera aktivt person Kolumner: Namn, Administratörer, Arbetsplatser Åtgärder: Information om organisationer, Skapa ny organisation, Ta bort | OK vid öppning i stage. |
| Lista på identiteter | `/CPS/IdentityList` | Visar identiteter inom CPS. Listan kan filtreras och visar person, organisation, arbetsplats och företag. | Rubriker: CPS Identiteter Fält/filter: Visa 10 25 50 100 rader, Sök: Kolumner: Förnamn, Efternamn, E-post, Organisation Åtgärder: Filtrera | OK vid öppning i stage. |
| Lista på externa tjänsteföretag | `/CPS/ExternalProviderList` | Visar externa tjänsteföretag i CPS. I stage syntes minst en leverantör i en enkel namnlista. | Rubriker: Alla externa tjänsteföretag Kolumner: Namn | OK vid öppning i stage. |
| Lista på fil importer | `/CPS/FileImportList` | Avsedd för CPS-relaterade filimporter. I stage svarade länken med 404. | Rubriker: Server Error in '/' Application., The resource cannot be found. | Fel i stage: sidan returnerar serverfel. |
| ThirdPartySales Dashboard | `/TPS` | Dashboard för tredjepartsparkeringar/TPS-kunder. Listan visar kundnamn, slug, kontaktnummer och aktiv-status samt stöd för att skapa/redigera kunder. | Rubriker: TPS - Hantering av tredjeparts parkeringar, Kunder Kolumner: Id, Namn, Slug, Kontaktnummer Åtgärder: Information om kunderna, Skapa ny kund, Ändra | OK vid öppning i stage. |

## Användarmeny

| Funktion | URL/path | Vad den gör | Viktiga element i vyn | Status i stage |
| --- | --- | --- | --- | --- |
| My Active Directory Profile | `/ADProfile/GetProfile` | Samma profilvy som i Admin men nås även via användarmenyn. Hämtar AD-profil och gruppmedlemskap för vald användare. | Rubriker: Get Active Directory Profile Fält/filter: UserName, Password, * This information is not stored in SPS. It is coming directly from Active Directory Kolumner: Sr., Group Member List Åtgärder: Get Profile | OK vid öppning i stage. |
| Logga ut | `/ApcoaAccount/LogOut` | Loggar ut användaren via Microsoft-konto/Azure AD. Länken öppnar Microsofts logout-flöde. |  | Ej öppnad automatiskt av säkerhets-/sessionskäl. |

## Observerade brister i stage

- **Rapporter -> OP - 1A - Occupancy Rate Repot NEW**: Fel i stage: Power BI-rapporten saknas eller pekar på ogiltigt ReportID/workspace.
- **Rapporter -> SPS- 1F - Kontraktsöversikt med kontaktuppgifter**: Fel i stage: Power BI-rapporten saknas eller pekar på ogiltigt ReportID/workspace.
- **Rapporter -> Report to audit the payments and events from EPMP**: Fel i stage: Power BI-rapporten saknas eller pekar på ogiltigt ReportID/workspace.
- **Rapporter -> OP - 8D - Park & Go Statistik**: Fel i stage: Power BI-rapporten saknas eller pekar på ogiltigt ReportID/workspace.
- **Rapporter -> OP - 8xd - Park & Go beläggningsgrad**: Fel i stage: Power BI-rapporten saknas eller pekar på ogiltigt ReportID/workspace.
- **Rapporter -> OP - 7 - Uppföljning Kontrollavgifter**: Fel i stage: Power BI-rapporten saknas eller pekar på ogiltigt ReportID/workspace.
- **Garage -> Registrera eller kontrollera BA i lagret**: Fel i stage: sidan returnerar serverfel.
- **Nyckelhantering -> Key Inventory**: Fel i stage: sidan returnerar serverfel.
- **Gemensamma inställningar -> Uppdatera KPI**: Fel i stage: sidan returnerar serverfel.
- **Admin -> Schemaläggaren**: Fel i stage: sidan returnerar serverfel.
- **Admin -> Migrate DS**: Delvis fel i stage: sidan öppnas men data kunde inte laddas.
- **Admin -> Lista på fil importer**: Fel i stage: sidan returnerar serverfel.

## Slutsats

Kundtjänstportalen är bred och täcker kontrakt, korttidsavtal, rapportering, garage-/produktadministration, köhantering, nycklar, loggar, globala inställningar, mallhantering samt ett stort antal avancerade adminverktyg. Den här genomgången ger en komplett menyinventering och kan användas som grund för vidare funktionsdokumentation, processkartor eller utbildningsmaterial.
