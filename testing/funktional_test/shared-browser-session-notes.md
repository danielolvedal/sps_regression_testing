# Delad browser-session i funktionella tester

För funktionella tester är det viktigt att agenten kan öppna flera SPS-sidor i **samma synliga browserfönster**.

## Varför

- användaren kan se och jämföra flikarna direkt
- agenten kan styra samma session utan att skapa parallella, osynkade fönster
- stage och stage legacy kan hållas öppna samtidigt
- manuella och automatiserade teststeg kan blandas i samma pass

## Standardmetod

1. Starta den delade browsern med `.\runtime\start-collaborative-stage-browser.ps1`
2. Logga in vid behov
3. Öppna nya jämförelseflikar med `.\runtime\open-shared-browser-tab.ps1 -Url "<mål-url>"`
4. Verifiera att fliken syns i target-listan innan testet fortsätter

## Referens

- `tools\docs\delad-browser-flikstyrning.md`
