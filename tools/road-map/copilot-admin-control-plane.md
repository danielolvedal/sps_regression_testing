# Roadmap - Copilot-admin för SPS-regression

Detta roadmap-dokument beskriver hur SPS-repositoryt kan utvecklas till en administrerbar kontrollmiljö runt Copilot CLI, dokumentstyrda regressionstester och delad browser-session.

## Målbild

Användaren ska kunna arbeta i samma grundflöde som idag, men med ett kompletterande administrativt lager som gör det lättare att:

- starta definierade regressioner
- välja miljö, roll och DS-scope
- visa loggar
- visa rapporter
- visa Mermaid-grafen för testberoenden
- skicka standardiserade kommandon till Copilot
- följa körstatus och historik

## Arkitekturprincip

Adminmiljön bör delas i två delar:

1. **Docker control plane** för UI, metadata, historik och visualisering
2. **Windows host runner** för browser, PowerShell och Copilot CLI

Detta är den viktigaste avgränsningen i hela roadmapen.

## Fas 1 - Normalisera dokument och metadata

### Mål

Göra nuvarande SPS-repo till tydlig primär källa för regressionstestning.

### Leverabler

- sammanslagen dokumentation från `sps-regression-server`
- en enhetlig modell för:
  - test-ID
  - beroenden
  - körläge
  - miljö
  - roll
  - DS-scope
- identifiering av vilka promptmallar och operatörskommandon som ska stödjas

### Utfall

En stabil informationsmodell som adminlagret kan bygga vidare på.

## Fas 2 - Lokal runner och kommandobrygga

### Mål

Skapa ett host-side kontrakt som kan exekvera samma saker som användaren gör manuellt idag.

### Leverabler

- Windows-runner för:
  - start av browser-session
  - start av runtime-skript
  - läsning av rapporter
  - anrop av Copilot CLI
- standardiserade kommandoobjekt för exempelvis:
  - `kör regressionstest`
  - `kör regressionstest A`
  - `gå in i learning mode`
  - `uppdatera regressionstest B`
- loggformat för körning, stdout/stderr och status

### Utfall

Control plane kan starta arbete utan att själv äga browsern eller terminalsessionen.

## Fas 3 - Första administrativa ytan

### Mål

Leverera ett minimalt men praktiskt gränssnitt för daglig användning.

### Leverabler

- dashboard för senaste körningar
- vy för testkatalog
- vy för Mermaid-beroenden
- vy för rapporter i `test_reports`
- vy för färdiga promptmallar
- enkel loggvisning

### Utfall

Operatören får nytta direkt utan att hela plattformen måste vara färdig.

## Fas 4 - Miljöer, roller och körpolicy

### Mål

Göra det möjligt att välja och validera rätt kontext före körning.

### Leverabler

- miljöregister
- roll-/identitetsregister
- DS-policyer
- tydlig märkning av production/stage
- regler för vilka tester som får köras var

### Utfall

Adminlagret blir säkrare och mindre beroende av manuell kunskap.

## Fas 5 - Delat testbibliotek och synk

### Mål

Stödja återanvändbara testdefinitioner över flera installationer.

### Leverabler

- katalogmodell för delat testbibliotek
- import/synk till lokal körmiljö
- revisionshantering för testdefinitioner
- visning av lokala kontra delade versioner

### Utfall

Samma test kan underhållas centralt och användas lokalt med spårbar revision.

## Fas 6 - Utökad analys och stödytor

### Mål

Komplettera den operativa körningen med bättre analys- och reviewstöd.

### Leverabler

- filtrerbar körhistorik
- bättre felsummering
- artefaktöversikt för rapporter och skärmdumpar
- sammanställning av återkommande felmönster
- eventuell AI-assisterad sammanfattning av körresultat

### Utfall

Plattformen blir ett faktiskt driftverktyg, inte bara en samling skript.

## Fas 7 - Avancerade framtidssteg

Följande är möjliga senare steg, men ska inte blockera de tidigare faserna:

- API-regressioner
- schemalagda körningar
- djupare security administration
- avancerad AI-planering
- AI-baserad visuell analys
- bredare multi-role-orkestrering

## Första rekommenderade implementation

Om arbetet ska börja direkt är den bästa första leveransen:

1. ett litet metadataformat för test/miljö/roll
2. en Windows-runner som kan köra standardiserade Copilot-/runtime-kommandon
3. en enkel Docker-hostad UI som visar:
   - testkatalog
   - körstatus
   - rapporter
   - Mermaid-graf
   - färdiga kommandoknappar

Det ger hög nytta tidigt och passar den arbetsmodell som redan fungerar i praktiken.
