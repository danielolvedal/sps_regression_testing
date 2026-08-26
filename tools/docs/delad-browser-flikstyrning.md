# Delad browser - flikstyrning i samma fönster

Detta dokument beskriver hur agenten öppnar **en ny flik i samma delade browserfönster** i stället för att råka skapa ett nytt fönster. Detta är viktigt för testning där användaren och agenten ska arbeta i samma synliga session.

## Bakgrund

När agenten öppnar en sida via browserns övergripande target-API kan resultatet bli ett **nytt fönster**. För samarbets- och testflöden är det fel beteende när målet är att lägga till en flik i det befintliga InPrivate/Incognito-fönstret.

## Korrekt metod

Ny flik i samma fönster ska öppnas från en **befintlig sidtarget** i den delade sessionen, inte från browserns övergripande target.

Metoden är:

1. Läs targets från debug-porten, normalt `http://127.0.0.1:9222/json/list`
2. Välj en befintlig SPS-sidtarget i det delade fönstret
3. Anslut till sidans `webSocketDebuggerUrl`
4. Kör `Runtime.evaluate` med:
   - `window.open('<url>', '_blank')`
   - `userGesture = true`
5. Verifiera därefter via target-listan att den nya fliken faktiskt skapades

## Varför detta fungerar

`window.open(..., '_blank')` körs i kontexten för en redan öppen sida i det delade fönstret. Därför skapas en ny flik i samma browserfönster, vilket bevarar samarbetsläget mellan användare och agent.

## Viktig skillnad mot fel metod

| Metod | Resultat |
| --- | --- |
| `Target.createTarget` via browser-target | Riskerar att skapa nytt fönster |
| `Runtime.evaluate` + `window.open(..., '_blank')` på befintlig sidtarget | Skapar ny flik i samma fönster |

## Script och runtime

| Syfte | Källkod | Runtime |
| --- | --- | --- |
| Öppna ny flik i delad browser | `tools\source\browser_collaboration\Open-SharedBrowserTab.ps1` | `runtime\open-shared-browser-tab.ps1` |

## Exempel

```powershell
.\runtime\open-shared-browser-tab.ps1 -Url "https://sps-stage-legacy.europark.local/"
```

## Användning i testning

Den här funktionen ska användas när ett test kräver:

- flera SPS-miljöer öppna samtidigt
- jämförelse mellan stage och stage legacy
- parallell manuell och agentstyrd navigation
- flera arbetsytor i samma synliga browserfönster

## Verifiering

Efter fliköppning ska agenten verifiera att target-listan innehåller både den ursprungliga SPS-sidan och den nya fliken. Om ny flik inte syns i target-listan är uppgiften inte klar.
