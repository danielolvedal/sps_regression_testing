# Regressionstest - Wallboard Messages layout och acknowledge

Detta regressionstest verifierar att Admin-funktionen `Wallboard Messages` kan skapa sex aktiva meddelanden med layouttyperna `FullScreen`, `HalfScreen` och `OneThirdScreen`, att de blir synliga via `Stage`-länken i Kundtjänstportalen och att ett meddelande med `Acknowledge` verkligen kräver explicit kvittens.

## Test-ID

regression-wallboard-messages-layout-och-acknowledge

## Catalog Key

`I`

## Summary

Create six active wallboard messages in Admin, verify FullScreen, HalfScreen and OneThirdScreen rendering in Stage, and confirm that one message requires acknowledge.

## Dependencies

- none

## Typ

Manuellt/shared-browser-test i synlig stage-session.

## Miljö

- Kundtjänstportalen stage: `https://sps-stage.europark.local/CustomerService`
- Wallboard-lista: `https://sps-stage.europark.local/CustomerService/WallBoardMessage`
- Skapa-formulär: `https://sps-stage.europark.local/CustomerService/AddWallBoardMessage`

## Förutsättningar

- Synlig delad browser ska vara startad via `.\runtime\start-collaborative-stage-browser.ps1`.
- Användaren ska vara inloggad i Kundtjänstportalen.
- Agenten ska kunna läsa och styra samma browser-session.
- Körningen ska ha exklusiv kontroll över nya `Wallboard Messages` under testperioden så att inga andra samtidigt skapar liknande testmeddelanden.
- Testet ska använda en unik körmarkör, till exempel `WB-I-YYYYMMDD-HHMM`, inbakad i alla sex meddelandetexter.

## Syfte

Verifiera att Admin -> `Wallboard Messages` fortfarande fungerar som operativt verktyg för att lägga ut aktiva meddelanden till stage-portalen, att samtliga tre layouttyper verkligen renderas i Stage och att acknowledge-funktionen inte bara sparas i adminlistan utan också påverkar slutanvändarvyn.

Detta test är muterande och ska därför också städa efter sig så att stage inte lämnas med kvarhängande testmeddelanden.

## Testdata

1. Bestäm en unik körmarkör, till exempel `WB-I-20260828-1545`.
2. Sätt `startdatum` till dagens datum för alla sex meddelanden.
3. Välj ett slumpat `Slutdatum` i intervallet **idag till idag + 7 dagar** och använd samma datum för alla sex meddelanden i den här körningen.
4. Skapa följande sex meddelanden:

| Ordning | Identifierare i meddelandetext | Message Type | Active | Acknowledge |
| --- | --- | --- | --- | --- |
| 1 | `WB-I-...-FS1` | `FullScreen` | Ja | Nej |
| 2 | `WB-I-...-HS1` | `HalfScreen` | Ja | Nej |
| 3 | `WB-I-...-HS2` | `HalfScreen` | Ja | Nej |
| 4 | `WB-I-...-OT1` | `OneThirdScreen` | Ja | Nej |
| 5 | `WB-I-...-OT2` | `OneThirdScreen` | Ja | **Ja** |
| 6 | `WB-I-...-OT3` | `OneThirdScreen` | Ja | Nej |

5. Varje meddelandetext ska börja med sin unika identifierare på första raden så att den går att känna igen både i adminlistan och på Stage-sidan.

## Teststeg

1. Öppna `Admin -> Wallboard Messages`.
2. Kontrollera att listvyn visar kolumnerna `Message`, `Message type`, `Start Date`, `End Date`, `Active`, `Edit` och `Details`.
3. Förbered körmarkör och slumpat slutdatum enligt **Testdata**.
4. Skapa meddelandena ett i taget:
   - öppna skapa-länken för nytt wallboardmeddelande
   - kontrollera att formuläret innehåller `Message`, `BackGroundColor`, `startdatum`, `Slutdatum`, `Message Type`, `Active` och `Acknowledge`
   - skriv en kort testtext i `Message` där första raden är den unika identifieraren, till exempel `WB-I-20260828-1545-FS1`
   - välj lämplig layout enligt tabellen i **Testdata**
   - sätt `startdatum` till idag
   - sätt `Slutdatum` till det slumpade datumet inom sju dagar
   - markera `Active`
   - markera `Acknowledge` endast för `OT2`
   - klicka `Spara`
5. Efter varje sparning:
   - verifiera att listan åter öppnas
   - lokalisera den nyskapade raden via den unika identifieraren
   - verifiera att `Message type`, `Start Date`, `End Date` och `Active` motsvarar inmatningen
6. När alla sex meddelanden är skapade, klicka `Stage` längst upp till vänster för att gå till `https://sps-stage.europark.local/CustomerService`.
7. Uppdatera sidan vid behov tills de nya aktiva meddelandena börjar renderas.
8. Verifiera att alla sex identifierare kan observeras på Stage under den naturliga renderingen, antingen samtidigt eller via sidans normala växling/omrendering.
9. Verifiera layoutkraven:
   - `FS1` ska någon gång renderas som ensam `FullScreen`-yta
   - `HS1` och `HS2` ska någon gång renderas som två samtidiga `HalfScreen`-ytor med likvärdig delning av meddelandeområdet
   - `OT1`, `OT2` och `OT3` ska någon gång renderas som tre samtidiga `OneThirdScreen`-ytor med likvärdig delning av meddelandeområdet
10. Verifiera acknowledge-beteendet för `OT2`:
    - identifiera meddelandet med markören `...-OT2`
    - kontrollera att Stage kräver en explicit acknowledge-handling för just detta meddelande
    - om UI:t visar en knapp eller länk för acknowledge ska den behöva användas innan meddelandet anses kvitterat
    - om meddelandet försvinner eller släpper igenom visningen först efter explicit kvittens ska detta dokumenteras som korrekt beteende
    - om inget särskilt acknowledge-krav syns trots att meddelandet sparats med `Acknowledge` ska testet underkännas
11. Dokumentera vilka av de sex identifierarna som observerades samtidigt och vilka som krävde siduppdatering eller väntan innan de syntes.
12. Gå tillbaka till `Admin -> Wallboard Messages`.
13. Städa efter testet genom att öppna samtliga sex skapade meddelanden och göra dem inaktiva:
    - avmarkera `Active` och spara
    - om systemet inte accepterar detta, sätt `Slutdatum` till ett passerat datum och spara
14. Gå tillbaka till `Stage`, uppdatera sidan och verifiera att de sex testidentifierarna inte längre renderas som aktiva meddelanden.

## Förväntat resultat

- Det ska gå att skapa sex nya wallboardmeddelanden i stage utan formulär- eller sparfel.
- Adminlistan ska visa korrekt `Message type`, datumintervall och `Active=True` för varje nytt meddelande innan städning.
- `FullScreen`, `HalfScreen` och `OneThirdScreen` ska alla ha observerbar effekt i Stage-vyn.
- Samtliga sex meddelanden ska gå att spåra via sina unika identifierare i både adminlistan och Stage-visningen.
- Meddelandet `OT2` ska kräva explicit acknowledge i Stage; en passiv render utan kvittenskrav är fel.
- Efter städning ska inga av testets sex identifierare längre vara aktiva i Stage.

## Slutläge

- Aktiv flik: Kundtjänstportalen stage eller `Wallboard Messages`-listan.
- Alla sex testmeddelanden ska vara deaktiverade eller på annat sätt avslutade så att stage lämnas ren från testets aktiva wallboardinnehåll.

## Exekveringsgenvägar

- Skapa-sidan kan öppnas via den namnlösa add-länken i listan eller direkt med `https://sps-stage.europark.local/CustomerService/AddWallBoardMessage` om ikonen är svår att hitta.
- `Message`-fältet är en rich-text-editor ovanpå textarea `#Message`; använd helst enkel plain text utan formatering så att identifieraren blir lätt att hitta igen.
- `Message Type` ligger i `#ddlWallboardType` och de observerade alternativen är exakt `FullScreen`, `HalfScreen` och `OneThirdScreen`.
- `Active` motsvarar checkbox `#isActive` och `Acknowledge` motsvarar checkbox `#isAcknowledgeMessage`.
- Spara-knappen är en submit-kontroll med texten `Spara`.
- Om acknowledge-meddelandet blockerar delar av Stage för tidigt ska detta dokumenteras, men testet får inte markeras som godkänt förrän både layoutkraven och acknowledge-kravet har verifierats.

## Rapportkrav

Rapporten för en faktisk `Regression Mode`-körning ska minst dokumentera:

- körmarkör
- valt slumpat slutdatum
- vilka sex identifierare som skapades
- vilka identifierare som observerades i Stage
- hur `FullScreen`, `HalfScreen` och `OneThirdScreen` faktiskt renderades
- exakt hur acknowledge-beteendet för `OT2` såg ut
- hur städningen genomfördes och verifierades

## Tekniska observationer

- Listvyn öppnas på `/CustomerService/WallBoardMessage`.
- Skapa-formuläret öppnas på `/CustomerService/AddWallBoardMessage`.
- Live-observation 2026-08-28 visade formulärfälten `Message`, `BackGroundColor`, `startdatum`, `Slutdatum`, `Message Type`, `Active` och `Acknowledge`.
- Live-observation 2026-08-28 visade att `Stage`-länken i övre vänstra hörnet pekar på `/CustomerService`.
- Wallboard-listan innehåller redan äldre meddelanden i stagemiljön; unika testidentifierare är därför nödvändiga för säker verifiering och städning.

## Felutfall

Testet ska markeras som underkänt om något av följande inträffar:

- skapaformuläret saknar något av de förväntade fälten
- något av de sex meddelandena inte går att spara
- adminlistan inte visar korrekt `Message type`, datum eller `Active`-status för ett sparat meddelande
- någon av layouttyperna `FullScreen`, `HalfScreen` eller `OneThirdScreen` inte kan observeras i Stage
- någon av de sex identifierarna aldrig blir observerbar i Stage trots aktivt datumintervall och uppdatering
- `OT2` inte kräver explicit acknowledge
- städningen misslyckas så att ett eller flera testmeddelanden lämnas aktiva

## Bevis / dokumentation

Dokumentera minst:

- skärmbild eller tydlig observation från adminlistan efter skapande
- skärmbild eller tydlig observation av `FullScreen`, `HalfScreen` och `OneThirdScreen` i Stage
- skärmbild eller tydlig observation av acknowledge-kravet för `OT2`
- skärmbild eller tydlig observation som visar att testmeddelandena inte längre är aktiva efter städning

## Senast verifierad körning

- **Status:** Ännu inte verifierad i `Regression Mode`
- **Skapad/uppdaterad i:** `Learning Mode`
- **Datum:** 2026-08-28

## Relaterade dokument

- `testing\regression_test\README.md`
- `testing\regression_test\regression-test-catalog.md`
- `testing\regression_test\regression-test-dependencies.mmd`
- `tools\docs\browser-samarbete-stage-session.md`
- `tools\docs\regressionstest-arbetsmodell.md`
- `manuals\csc_user_manuals\Kundtjänst - funktioner.md`
