from __future__ import annotations

import json
from collections import OrderedDict, defaultdict
from pathlib import Path
from urllib.parse import parse_qsl, urlparse


REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = REPO_ROOT / "raw_data" / "kundtjanst-funktioner-data.json"
OUT_PATH = REPO_ROOT / "manuals" / "csc_user_manuals" / "Kundtjänst - funktioner.md"


GROUP_ORDER = [
    "Kontrakt",
    "STP-tjänster",
    "Rapporter",
    "Garage",
    "Produkt",
    "Köhantering",
    "Nyckelhantering",
    "Loggar",
    "Gemensamma inställningar",
    "Templates",
    "Admin",
    "Daniel Olvedal",
]


CUSTOM = {
    ("Kontrakt", "Sök"): (
        "Snabbsökning för kontrakt, kunder, DS, VRM och dokument i samma vy.",
        "Visar träfflistor direkt med länkar för redigering, VRM-hantering och dokument.",
    ),
    ("Kontrakt", "Sätt upp nytt kontrakt"): (
        "Startar flödet för att skapa ett nytt kontrakt genom att välja DS/anläggning.",
        "Första steget är DS-val innan vidare kontraktsuppgifter anges.",
    ),
    ("Kontrakt", "Ändra ett kontrakt"): (
        "Startpunkt för att öppna ett befintligt kontrakt för ändring.",
        "Användaren anger kontraktsnummer och går vidare till redigeringsflödet.",
    ),
    ("Kontrakt", "Ändra pris på ett kontrakt"): (
        "Ändrar priset på ett enskilt kontrakt.",
        "Stöd finns för procentuell höjning, fast belopp, KPI-baserad höjning och nytt fast pris.",
    ),
    ("Kontrakt", "Skapa kontrakt utfrån mall"): (
        "Skapar/skriv ut kontraktsdokument från en vald mall.",
        "Vyn kombinerar kontraktsnummer med mallval och kan skapa PDF.",
    ),
    ("Kontrakt", "Lägg till/ta bort VRMer för ett kontrakt"): (
        "Uppdaterar registreringsnummer kopplade till ett kontrakt.",
        "Flödet utgår från kontraktsnummer och leder vidare till VRM-hantering.",
    ),
    ("Kontrakt", "Översikt av garage"): (
        "Öppnar garageöversikt via valt DS-nummer.",
        "Används som startpunkt för att se status och innehåll i en anläggning.",
    ),
    ("Kontrakt", "Old Search Method"): (
        "Äldre kontraktssökning med separata sökingångar för kund, DS och dokument.",
        "Ger bred träfflista men verkar vara en legacy-vy jämfört med Quick Search.",
    ),
    ("STP-tjänster", "Skapa nytt korttidsavtal"): (
        "Startar skapande av korttidsavtal för engångs-/korttidsparkering.",
        "Första steget är att ange DS för den parkering avtalet ska gälla.",
    ),
    ("STP-tjänster", "Redigera korttidsavtal"): (
        "Öppnar befintligt korttidsavtal för ändring.",
        "Sker via kontraktsnummer.",
    ),
    ("STP-tjänster", "Old Search Method"): (
        "Återanvänder den äldre sökvyn även för STP-flöden.",
        "Kan användas för att hitta kontrakt före vidare handläggning.",
    ),
    ("STP-tjänster", "Översiktlig statistik för engångsparkering"): (
        "Visar sökbar statistik för engångsparkering och kan exportera rådata till Excel.",
        "Tabellen är filtrerbar på bland annat DS, kund, VRM och starttid.",
    ),
    ("STP-tjänster", "Receptionsservice kontrakt"): (
        "Listar receptionsservicekontrakt och låter användaren söka på kontrakt eller DS.",
        "Vyn visar start/slutdatum, kund och servicetyp.",
    ),
    ("Garage", "Ändra pris på flera kontrakt på ett DS"): (
        "Massuppdaterar pris på flera kontrakt inom ett DS.",
        "Utgår från DS-nummer och har avancerade sök-/filtermöjligheter.",
    ),
    ("Garage", "Avsluta alla kontrakt på ett DS"): (
        "Massavslutar samtliga kontrakt i en anläggning.",
        "Kräver DS-nummer och gemensamt avslutsdatum.",
    ),
    ("Garage", "Lägg till DS"): (
        "Startar guiden för att skapa ett nytt garage/DS.",
        "Första steget är att ange nytt DS-nummer.",
    ),
    ("Garage", "Sök DS"): (
        "Öppnar ett befintligt DS för redigering av garageinformation.",
        "Vyn används för ändring av anläggningsdata.",
    ),
    ("Garage", "Visa betalautomater per DS"): (
        "Söker fram betalautomater per DS eller BA-nummer.",
        "Tomt sökfält visar hela anläggningsregistret enligt sidtexten.",
    ),
    ("Garage", "Registrera eller kontrollera BA i lagret"): (
        "Avsedd för lagerhantering/kontroll av BA-enheter.",
        "I stage returnerar sidan för närvarande ett modell-/view-fel i stället för funktionellt innehåll.",
    ),
    ("Garage", "Audit trail - Garage informations"): (
        "Visar audit trail för ändringar i garage och parkeringsstruktur.",
        "Kan filtreras på händelse, DS, datum och användare samt exporteras till Excel.",
    ),
    ("Produkt", "Produktmall"): (
        "Administrerar produktmallar.",
        "Listan visar bland annat BC-kod, skattenivå, köavgiftsflagga och tillståndsschema.",
    ),
    ("Produkt", "Paketmallar"): (
        "Administrerar paketmallar och visar hur de används.",
        "Tabellen listar paketnamn, antal produktmallar samt avgifts-/momsrelaterad information.",
    ),
    ("Produkt", "Reklambanner"): (
        "Administrerar reklambanners för kundgränssnitt eller kampanjytor.",
        "Stöd finns för att skapa ny banner och se status per bannerplacering.",
    ),
    ("Produkt", "Audit trail - Products and packages"): (
        "Visar ändringshistorik för produkter och paket.",
        "Filtrering sker på händelse, datum och användare.",
    ),
    ("Köhantering", "Visa alla köande"): (
        "Visar samtliga köer i systemet.",
        "Tabellen innehåller namn, DS, garage, skapandedatum, månadsavgifter och antal kömedlemmar.",
    ),
    ("Köhantering", "Alla ködeltagare"): (
        "Visar kömedlemmar över alla köer.",
        "Innehåller köposition, identitet, kontaktuppgifter och åtgärder som erbjudande eller borttagning.",
    ),
    ("Köhantering", "Visa kö för garage"): (
        "Söker fram köer kopplade till ett specifikt DS.",
        "Flödet startar med val av DS.",
    ),
    ("Köhantering", "Sök kö för användare"): (
        "Söker fram köhistorik eller aktiva köer för en användare.",
        "Flödet startar med användarsökning.",
    ),
    ("Köhantering", "Visa erbjudanden"): (
        "Visar alla utskickade köerbjudanden.",
        "Listan innehåller mottagare, kontaktuppgifter, DS, garage och erbjudandestatus/händelser.",
    ),
    ("Köhantering", "Automatisk kundimport"): (
        "Administrerar kundimportsessioner till kölistor.",
        "Vyn innehåller sessionnamn, välkomstfraser, villkor och möjlighet att skapa nya importlänkar.",
    ),
    ("Nyckelhantering", "Key Inventory"): (
        "Avsedd som nyckelregister/inventarie.",
        "Sidan kraschar i stage innan inventarielistan kan visas.",
    ),
    ("Nyckelhantering", "Manage Key Types"): (
        "Administrerar typer av nycklar/taggar/fjärrkontroller.",
        "Man kan skapa, ändra och ta bort nyckeltyper.",
    ),
    ("Nyckelhantering", "CarPark Key Settings"): (
        "Konfigurerar nyckelinställningar per DS.",
        "Flödet börjar med DS-val, sannolikt för att koppla nyckelregler till anläggning.",
    ),
    ("Loggar", "Oktavius valideringslogg"): (
        "Hämtar Oktavius-logg per VRM, tidsspann och DS.",
        "Används för felsökning av valideringar kopplade till registreringsnummer.",
    ),
    ("Loggar", "Kontraktssynkroniseringsloggar"): (
        "Visar synkloggar för kontrakt mot Business Central och EPMP.",
        "Har filter för DS, kontrakt, åtgärdstyp och fel-only samt knapp för att pusha om misslyckade kontrakt.",
    ),
    ("Loggar", "Audit trail - Contract parking"): (
        "Visar ändringshistorik för kontrakt och kontraktsparkering.",
        "Kan filtreras på händelse, kontrakt, DS, garage och datum samt exporteras.",
    ),
    ("Loggar", "Backend Process Events"): (
        "Övervakar backendjobb och processhändelser.",
        "Visar skapad tid, status, klar-tid, progress och eventtyp.",
    ),
    ("Gemensamma inställningar", "Tillståndsscheman"): (
        "Administrerar tillståndsscheman och giltighetstider.",
        "Vyn innehåller dagliga/veckovisa/årliga tider samt CRUD för schemarader.",
    ),
    ("Gemensamma inställningar", "Skattesatser"): (
        "Administrerar momsmallar/skattesatser.",
        "Visar namn, momsprocent och stöd för att lägga till, ändra eller ta bort.",
    ),
    ("Gemensamma inställningar", "BC-koder"): (
        "Administrerar Business Central-koder och deras egenskaper.",
        "Listan visar namn, beskrivning, avgiftstyp, servicetyp och aktiv-status.",
    ),
    ("Gemensamma inställningar", "Notification Templates"): (
        "Administrerar notifieringsmallar för händelser i systemet.",
        "Listan visar event, kontraktsfilter, mallnamn, version, typ och publicering.",
    ),
    ("Gemensamma inställningar", "Administrera fastighetsägare/hyresvärd/operatör för ett DS"): (
        "Kopplar eller ändrar fastighetsägare, hyresvärd och operatör för en anläggning.",
        "Utgår från DS-nummer.",
    ),
    ("Gemensamma inställningar", "Uppdatera KPI"): (
        "Avsedd för uppdatering av KPI/CPI-värden som används i prislogik.",
        "Sidan returnerar null-reference-liknande fel i stage och kunde inte granskas funktionellt.",
    ),
    ("Gemensamma inställningar", "Definiera Allmänna helgdagar"): (
        "Administrerar helgdagar och stödjer kopiering mellan år.",
        "Vyn visar datum, typ och beskrivning samt har knappar för kopiering och sparning.",
    ),
    ("Gemensamma inställningar", "Contract Termination Reasons"): (
        "Administrerar orsaker för kontraktsuppsägning.",
        "Listan innehåller reason/description och stöd för att lägga till och redigera.",
    ),
    ("Templates", "Notification Templates"): (
        "Samma template-register som under Gemensamma inställningar.",
        "Används för hantering och publicering av notifieringsmallar.",
    ),
    ("Templates", "Skapa nya kontraktsmallsrader"): (
        "Editor för kontraktsmallsrader och innehållsblock.",
        "Stöd finns för text, länkar, typografi/färgval och utskrift/preview.",
    ),
    ("Templates", "Skapa ny kontraktsmall"): (
        "Skapar en ny övergripande kontraktsmall.",
        "Vyn visar befintliga mallar och tillgängliga fält/variabler.",
    ),
    ("Admin", "Pusha ett kontrakt till Business Central"): (
        "Startar om synkning av ett enskilt kontrakt till Business Central.",
        "Visar samtidigt historik/loggar för tidigare försök.",
    ),
    ("Admin", "Pusha alla contract i ett DS till Business Central"): (
        "Startar om synkning av alla kontrakt inom ett DS till Business Central.",
        "Visar tidigare sync-event och fel per körning.",
    ),
    ("Admin", "Pusha samtliga kontrakt till Business Central"): (
        "Masspushar alla kontrakt till Business Central.",
        "Är en bred administrativ återkörning med logglista på samma sida.",
    ),
    ("Admin", "Pusha samtliga kontrakt till Park&GO"): (
        "Masspushar kontrakt till EPMP/Park&GO.",
        "Visar progress per DS med pending/total contracts.",
    ),
    ("Admin", "Skapa en ny VRM-pool för ett kontrakt"): (
        "Bryter ut ett kontrakt till en ny VRM-pool.",
        "Sidan beskriver att kontrakt flyttas till den nya poolen tillsammans med valda VRMer.",
    ),
    ("Admin", "Slå ihop VRM-poolerna för ett kontrakt"): (
        "Slår ihop flera kontrakts VRM-pooler.",
        "Kräver kontrakt, nytt poolnamn och beskrivning.",
    ),
    ("Admin", "Peka om ett kontrakt till en annan VRM-pool"): (
        "Flyttar ett kontrakt till en befintlig VRM-pool.",
        "Utgår från kontraktsnummer och vald pool.",
    ),
    ("Admin", "Se kontrakt på VRM-pool"): (
        "Visar vilka kontrakt som ligger på en viss VRM-pool.",
        "Sökbar tabell med pool och kontraktsnummer.",
    ),
    ("Admin", "Hantera VRM-pooler på kund"): (
        "Visar och administrerar VRM-pooler per kund.",
        "Stöd finns för att slå samman pooler, öppna kontrakt och redigera poolkopplingar.",
    ),
    ("Admin", "Audit"): (
        "Exporterar auditdata till CSV.",
        "Användaren väljer teckenkodning innan filen hämtas.",
    ),
    ("Admin", "API Users Settings"): (
        "Administrerar externa API-användare och tokenperioder.",
        "Listan visar kund, token-start, token-expiry och åtkomsthantering.",
    ),
    ("Admin", "Wallboard Messages"): (
        "Administrerar meddelanden som visas på wallboard/interna ytor.",
        "Listan innehåller meddelandetyp, start/slutdatum, aktiv-flagga och redigering.",
    ),
    ("Admin", "Schemaläggaren"): (
        "Avsedd för schemaläggningsöversikt eller jobbhantering.",
        "Sidan ger serverfel i stage och kunde inte granskas vidare.",
    ),
    ("Admin", "Konfigurationer för schemalagda uppgifter"): (
        "Visar cron-konfiguration för schemalagda uppgifter.",
        "Listan innehåller nyckel, cron-uttryck, beskrivning, nästa körning och typ.",
    ),
    ("Admin", "Running microservices and scheduled task"): (
        "Visar driftstatus för mikrotjänster och schemalagda jobb.",
        "Innehåller adress, port, aktiv-status, heartbeat och senaste fel.",
    ),
    ("Admin", "PBI Reports"): (
        "Administrerar Power BI-rapportdefinitioner i SPS.",
        "Listan visar report key, beskrivning, workspace-id, report-id och rapporttyp.",
    ),
    ("Admin", "Migrate DS"): (
        "Verktyg för migrering av anläggningar från legacy till SPS.",
        "Listan visar kontraktsvolymer och migrationsstatus, men stage kunde inte läsa in car parks just nu.",
    ),
    ("Admin", "Kontraktsimport"): (
        "Visar och startar kontraktsimporter.",
        "Stöd finns för ny import, fortsättning av pågående import och visning/radering av körningar.",
    ),
    ("Admin", "My Active Directory Profile"): (
        "Hämtar en användares AD-profil direkt från Active Directory.",
        "Visar gruppmedlemskap och förklarar att datat inte lagras i SPS.",
    ),
    ("Admin", "Administrera attribut"): (
        "Administrerar attributgrupper för parkeringsplatser.",
        "Visar gruppnamn, val-läge, visningsprioritet och CRUD-åtgärder.",
    ),
    ("Admin", "Queue Tick Tack Toe"): (
        "Specialvy för kömatris per DS.",
        "Endast DS-sökning framgår i första steget.",
    ),
    ("Admin", "Queue Import"): (
        "Länk till separat queue-import-tjänst.",
        "I denna session gick extern adress inte att nå.",
    ),
    ("Admin", "Tech Tool"): (
        "Länk vidare till separat tekniskt verktyg via CSC-handoff.",
        "Sidan vidarebefordrar användaren till intern stage-domän för FlowField/tech-tool.",
    ),
    ("Admin", "Company Administrator"): (
        "Detaljvy för juridiska personer/bolag med adress- och kontaktpersonshantering.",
        "Visar rollflaggor som landlord/property owner/customer och låter användaren spara ändringar.",
    ),
    ("Admin", "Customers"): (
        "Söker fram kunder/juridiska personer.",
        "Resultatlistan visar personnummer, namn, företagsflagga och Sales Force-id.",
    ),
    ("Admin", "Fastighetsägare"): (
        "Söker fram fastighetsägare/hyresvärdar.",
        "Resultatlistan visar person-/organisationsnummer och namn.",
    ),
    ("Admin", "CPS Dashboard"): (
        "Dashboard för hantering av personalparkeringstillstånd (CPS).",
        "Stöd finns för organisationshantering, verifieringar och allokering av DS.",
    ),
    ("Admin", "Lista på identiteter"): (
        "Visar identiteter inom CPS.",
        "Listan kan filtreras och visar person, organisation, arbetsplats och företag.",
    ),
    ("Admin", "Lista på externa tjänsteföretag"): (
        "Visar externa tjänsteföretag i CPS.",
        "I stage syntes minst en leverantör i en enkel namnlista.",
    ),
    ("Admin", "Lista på fil importer"): (
        "Avsedd för CPS-relaterade filimporter.",
        "I stage svarade länken med 404.",
    ),
    ("Admin", "ThirdPartySales Dashboard"): (
        "Dashboard för tredjepartsparkeringar/TPS-kunder.",
        "Listan visar kundnamn, slug, kontaktnummer och aktiv-status samt stöd för att skapa/redigera kunder.",
    ),
    ("Daniel Olvedal", "My Active Directory Profile"): (
        "Samma profilvy som i Admin men nås även via användarmenyn.",
        "Hämtar AD-profil och gruppmedlemskap för vald användare.",
    ),
    ("Daniel Olvedal", "Logga ut"): (
        "Loggar ut användaren via Microsoft-konto/Azure AD.",
        "Länken öppnar Microsofts logout-flöde.",
    ),
}


def normalize_group(name: str) -> str:
    return "Användarmeny" if name == "Daniel Olvedal" else name


def unique_pages(data: dict) -> list[dict]:
    seen: OrderedDict[tuple[str, str, str], dict] = OrderedDict()
    for page in data["pages"]:
        key = (page["group"], page["menuText"], page["menuHref"])
        if key not in seen:
            seen[key] = page
    return list(seen.values())


def status_for(page: dict) -> str:
    title = page.get("pageTitle") or ""
    snippet = page.get("snippet") or ""
    alerts = " | ".join(page.get("alerts") or [])
    url = page.get("pageUrl") or ""
    if "Skipped by inventory rules." in alerts:
        return "Ej öppnad automatiskt av säkerhets-/sessionskäl."
    if url.startswith("chrome-error://"):
        return "Fel i stage/externt system: länken kunde inte nås."
    if "Server Error in '/'" in snippet or "Server Error in '/'" in title:
        return "Fel i stage: sidan returnerar serverfel."
    if "No reports were found" in alerts or "No report with the given ReportID" in alerts:
        return "Fel i stage: Power BI-rapporten saknas eller pekar på ogiltigt ReportID/workspace."
    if "Could not load car parks right now" in alerts:
        return "Delvis fel i stage: sidan öppnas men data kunde inte laddas."
    if page["group"] == "Rapporter":
        return "Öppnar Power BI-rapport/container."
    if "Loggar in via CSC" in snippet:
        return "Vidarelänkar till separat internt verktyg."
    return "OK vid öppning i stage."


def path_only(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    if parsed.scheme == "chrome-error":
        return "chrome-error://chromewebdata/"
    path = parsed.path or "/"
    if parsed.query:
        keys = {key.lower() for key, _ in parse_qsl(parsed.query, keep_blank_values=True)}
        sensitive = {"token", "client_id", "post_logout_redirect_uri"}
        if keys & sensitive:
            return f"{path}?REDACTED"
        return f"{path}?{parsed.query}"
    return path


def important_bits(page: dict) -> str:
    if page["group"] == "Rapporter":
        return "Power BI-vy via rapportnyckel."
    bits = []
    headings = [h for h in (page.get("headings") or []) if h and h != "Reset Password ×"][:2]
    labels = [l for l in (page.get("labels") or []) if l][:3]
    tables = [t for t in (page.get("tableHeaders") or []) if t][:4]
    buttons = [b for b in (page.get("buttons") or []) if b and b not in {"×", "Update", "↑ Öppna Chatt"}][:3]
    if headings:
        bits.append("Rubriker: " + ", ".join(headings))
    if labels:
        bits.append("Fält/filter: " + ", ".join(labels))
    if tables:
        bits.append("Kolumner: " + ", ".join(tables))
    if buttons:
        bits.append("Åtgärder: " + ", ".join(buttons))
    return " ".join(bits)


def purpose_for(page: dict) -> str:
    key = (page["group"], page["menuText"])
    if key in CUSTOM:
        purpose, actions = CUSTOM[key]
        return f"{purpose} {actions}"
    if page["group"] == "Rapporter":
        return f"Öppnar Power BI-rapporten **{page['menuText']}** i inbäddad rapportvy."
    return "Funktionen kunde öppnas men saknar ännu manuell tolkning i dokumentgeneratorn."


def build_markdown(data: dict) -> str:
    pages = unique_pages(data)
    by_group: dict[str, list[dict]] = defaultdict(list)
    for page in pages:
        by_group[page["group"]].append(page)

    counts = {group: len(by_group[group]) for group in by_group}
    total = sum(counts.values())

    lines = [
        "# Kundtjänst - funktioner",
        "",
        f"Analysen bygger på en live-genomgång av **stage-miljön** i Kundtjänstportalen den **{data['capturedAt']}**. Dokumentet beskriver vad varje menyval verkar göra utifrån faktisk navigering, synliga formulär, tabeller, knappar och felmeddelanden i UI:t.",
        "",
        "## Omfattning",
        "",
        f"- Unika menyfunktioner genomgångna: **{total}**",
        "- Metod: automatisk genomklickning av samtliga toppmenyer i den inloggade stage-sessionen",
        "- Notering: flera poster under **Rapporter** öppnar en Power BI-container utan att exponerat detaljinnehåll kunde läsas från sidan. Där dokumenteras främst rapportens avsedda område och om länken såg frisk ut.",
        "",
        "## Menyöversikt",
        "",
        "| Meny | Antal funktioner |",
        "| --- | ---: |",
    ]

    for group in GROUP_ORDER:
        if group in counts:
            lines.append(f"| {normalize_group(group)} | {counts[group]} |")

    for group in GROUP_ORDER:
        if group not in by_group:
            continue
        lines.extend(
            [
                "",
                f"## {normalize_group(group)}",
                "",
                "| Funktion | URL/path | Vad den gör | Viktiga element i vyn | Status i stage |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for page in by_group[group]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        page["menuText"].replace("|", "\\|"),
                        f"`{path_only(page.get('pageUrl') or page.get('menuHref') or '')}`",
                        purpose_for(page).replace("|", "\\|"),
                        important_bits(page).replace("|", "\\|"),
                        status_for(page).replace("|", "\\|"),
                    ]
                )
                + " |"
            )

    error_pages = [p for p in pages if "Fel i stage" in status_for(p) or "Delvis fel i stage" in status_for(p)]
    lines.extend(["", "## Observerade brister i stage", ""])
    if error_pages:
        for page in error_pages:
            lines.append(f"- **{normalize_group(page['group'])} -> {page['menuText']}**: {status_for(page)}")
    else:
        lines.append("- Inga fel noterades vid den här genomgången.")

    lines.extend(
        [
            "",
            "## Slutsats",
            "",
            "Kundtjänstportalen är bred och täcker kontrakt, korttidsavtal, rapportering, garage-/produktadministration, köhantering, nycklar, loggar, globala inställningar, mallhantering samt ett stort antal avancerade adminverktyg. Den här genomgången ger en komplett menyinventering och kan användas som grund för vidare funktionsdokumentation, processkartor eller utbildningsmaterial.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    OUT_PATH.write_text(build_markdown(data), encoding="utf-8")
    print(OUT_PATH)


if __name__ == "__main__":
    main()
