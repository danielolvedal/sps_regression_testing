# Regressionstest - kontraktssökning Anna till serviceportal-login

Detta regressionstest verifierar att Kundtjänstportalen kan öppna ett avslutat/utgånget Anna-kontrakt i stage utan att falla tillbaka till legacy, och att användarens serviceportal kan öppnas via Actions i en ny flik.

## Test-ID

regression-kontrakt-anna-serviceportal-login

## Catalog Key

`A`

## Summary

Find a user via contract search and end on that user's logged-in service portal page through assisted login.

## Dependencies

- none

## Typ

Manuellt/shared-browser-test i synlig stage-session.

## Miljö

- Kundtjänstportalen stage: `https://sps-stage.europark.local/CustomerService`
- Serviceportalen stage: `https://web-stage.europark.local/myaccount/index`

## Förutsättningar

- Synlig delad browser ska vara startad via `.\runtime\start-collaborative-stage-browser.ps1`
- Användaren ska vara inloggad i Kundtjänstportalen
- Agenten ska kunna läsa och styra samma browser-session

## Syfte

Verifiera att sökflödet för kontrakt fungerar i nya stage, att kontraktslänken inte skickar användaren till legacy och att användarlogin till serviceportalen öppnas i en ny flik med korrekt stage-URL så att nästa test kan ta vid där.

## Teststeg

1. Gå till `Kontrakt`.
2. Gå vidare till `Sök`.
3. Sök på `Anna`.
4. Vänta tills resultatlistan har laddat klart.
5. Identifiera en rad för `Anna` där slutdatum har passerat dagens datum.
6. Klicka på kontraktsnummerlänken för den raden.
7. Kontrollera URL:
   - testet ska stanna i nya stage-miljön
   - om länken öppnar legacy: gå tillbaka och välj en annan `Anna`
8. När kontraktssidan är öppen, scrolla till sektionen `Users`.
9. Under relevant användare, öppna `Actions`.
10. Klicka på knappen som loggar in som användaren i serviceportalen.
11. Kontrollera att en **ny flik** öppnas.
12. Kontrollera att den nya fliken öppnas på:
    - `https://web-stage.europark.local/myaccount/index`
    - eller samma URL med tillåtna query-parametrar efter grundpathen

## Förväntat resultat

- Minst ett Anna-kontrakt ska gå att öppna i nya stage utan legacy-fallback.
- `Actions` för användaren ska innehålla login-funktion till serviceportalen.
- Serviceportalen ska öppnas i **ny flik** på stage-domänen.
- Testet ska avslutas med att användaren står inloggad på `https://web-stage.europark.local/myaccount/index`.

## Slutläge

- Aktiv flik: kundens inloggade serviceportal
- URL: `https://web-stage.europark.local/myaccount/index`
- Detta slutläge är startläget för `B` och `C`

## Exekveringsgenvägar

- I `Quick Search` är det **kontraktssökningen** som ska användas: fältet `SearchTerm` med knappen `btnSearch`.
- Fältet `UserSearchInput` hör till den separata användarsökningen och ska inte användas för detta test.
- Resultaten renderas inline på samma sida `Search\QuickSearch`; agenten behöver alltså normalt inte vänta på sidnavigering, bara på att resultatraderna fylls.
- Börja med en `Anna`-rad som tydligt visar ett passerat slutdatum i kolumnen `Slutdatum`; undvik rader där kolumnerna verkar feljusterade.
- `Users` är kollapsad som standard och måste öppnas via knappen `usersBtn` innan action-ikonerna blir synliga.
- Om browsern visar Microsoft-inloggning under flödet ska agenten låta användaren arbeta färdigt i minst **5 minuter** innan körningen stoppas eller klassas som loginfel.

## Tekniska observationer

- Serviceportal-login i användarlistan triggas av funktionen `SetAssistedLogin(userId)`.
- Den funktionen POST:ar till `/EditContract/SetUserAssistedLogin` och öppnar därefter en ny flik via `window.open(...)`.
- Den första öppnade URL:en kan vara `https://web-stage.europark.local/account/assistedLogin/{token}`, men testet ska verifiera att slutmålet landar på `https://web-stage.europark.local/myaccount/index`.
- Ny flik/popup kan kräva riktig browser-gesture; om ett vanligt scriptklick inte öppnar fliken måste agenten använda en metod som räknas som user gesture i browsern.
- Regression Mode-observation 2026-08-31: efter assisted login räcker det inte att manuellt navigera en ny eller befintlig serviceportalflik till `/myaccount/index`; sådan direktnavigering kan landa på `Account/Login` eller tappa Anna-läget. A är först etablerat när en responsiv `web-stage`-flik faktiskt visar `Anna Walldén` och `Mitt Parkeringskonto`.
- Regression Mode-observation 2026-08-31: om en `web-stage`-target slutar svara via debuggränssnittet efter misslyckad automation ska den inte användas som A-slutläge. Be användaren trigga assisted login igen och verifiera en ny responsiv target innan efterföljande tester startas.

## Felutfall

Testet ska markeras som underkänt om något av följande inträffar:

- inga Anna-resultat laddas
- inga Anna-rader med passerat slutdatum kan användas
- kontraktsnummerlänken leder till legacy för alla testbara Anna-rader
- `Users` eller `Actions` saknas på kontraktssidan
- serviceportal-login öppnas inte
- serviceportal-login öppnas i samma flik i stället för ny flik
- serviceportal-login öppnas mot annan miljö än `web-stage.europark.local`

## Bevis / dokumentation

Dokumentera minst:

- vilken Anna-rad som användes
- vilken kontrakts-URL som öppnades
- vilken serviceportal-URL som öppnades
- om fallback till legacy observerades för någon kandidat

## Senast verifierad körning

- **Datum:** 2026-08-26
- **Körläge:** Regression Mode
- **Sökväg:** `Kontrakt -> Sök`
- **Sökterm:** `Anna`
- **Verifierad kandidat:** `Anna Walldén`
- **Öppnad kontrakts-URL:** `https://sps-stage.europark.local/EditContract/Overview?contractId=H-47184-000025049`
- **Utfall för miljökontroll:** stannade i nya stage, ingen legacy-fallback för vald kandidat
- **Öppnad serviceportal-URL:** `https://web-stage.europark.local/myaccount/index`
- **Notering:** serviceportal-login lyckades efter att `Users` öppnats och assisted-login triggat ny flik med riktig browser-gesture; tab-targeten landade direkt på `Mitt Parkeringskonto`
- **Senaste blockerade försök:** 2026-08-31 kunde Anna-kontraktet öppnas i nya stage, men automationen kunde inte etablera en responsiv assisted-login-flik som kvarstod på `web-stage.europark.local/myaccount/index`. Följdtesterna `K` och `G` startades därför inte som giltig regression.

## Relaterade dokument

- `tools\docs\browser-samarbete-stage-session.md`
- `tools\docs\delad-browser-flikstyrning.md`
- `tools\docs\regressionstest-arbetsmodell.md`
- `testing\regression_test\README.md`
