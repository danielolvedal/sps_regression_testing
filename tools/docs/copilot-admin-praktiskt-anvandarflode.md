# Copilot-admin - praktiskt användarflöde

Detta dokument beskriver hur SPS-regressionsprojektet ska användas i praktiken när Windows host runner och en tunn Docker-control-plane finns på plats.

## Grundprincip

Control plane ska vara en administrativ yta runt arbetet, inte en ersättning för den gemensamma Copilot-sessionen eller den synliga browsern.

Den praktiska modellen är därför:

1. Windows-värden äger Copilot CLI, PowerShell, runtime-skript och den synliga browsern.
2. Docker-control-plane visar status, rapporter, Mermaid-graf, loggar och standardiserade kommandon.
3. Användaren och Copilot fortsätter att samarbeta i en gemensam Copilot CLI-session på Windows.
4. Den synliga browsern fortsätter att vara ett separat gemensamt fönster där användaren kan logga in och där Copilot kan läsa/styra via debug-port.

## Föreslaget startflöde för användaren

### 1. Öppna projektet

Användaren öppnar en terminal i SPS-repositoryts rotkatalog, oavsett om den ligger under exempelvis `C:\Copilot_projects\SPS` eller `C:\Apcoa-Git\SPS`.

```powershell
cd <SPS-rot>
```

### 2. Starta Copilot CLI

Användaren startar Copilot CLI i samma terminalmiljö som ska vara den gemensamma operatörssessionen.

Det är här användaren kan skriva fria instruktioner, följa Copilots resonemang och bekräfta saker som inte ska automatiseras.

### 3. Starta den synliga samarbetsbrowsern när UI-arbete behövs

```powershell
.\runtime\start-collaborative-stage-browser.ps1
```

Browsern är synlig för användaren. Användaren loggar själv in när Microsoft-inloggning krävs. Copilot ska vänta minst 5 minuter på inloggning innan sessionen klassas som blockerad.

### 4. Starta host runner

```powershell
.\runtime\start-copilot-admin-runner.ps1
```

Host runnern kör på Windows-sidan och exponerar status, rapporter, Mermaid-graf och standardiserade kommandoobjekt.

### 5. Starta Docker-control-plane

När control plane finns implementerad startas den separat, till exempel via ett framtida runtime-skript.

Exempel på målkommando:

```powershell
.\runtime\start-copilot-admin-control-plane.ps1
```

Control plane ska då visa en lokal webbsida, exempelvis `http://localhost:<port>`.

### 6. Arbeta från två ytor

| Yta | Syfte |
| --- | --- |
| Copilot CLI-terminal | Gemensam operatörssession där användaren och Copilot för dialog och där Copilot utför arbete. |
| Synlig browser | Gemensam testyta där användaren kan logga in och Copilot kan observera/styra UI. |
| Web control plane | Administrativ vy för status, rapporter, Mermaid-graf, loggar och standardiserade åtgärder. |

## Viktig avgränsning för Copilot-sessionen

I första fungerande versionen ska Copilot-sessionen **inte** flyttas in i webgränssnittet.

Skälet är att projektets fungerande arbetssätt bygger på att användaren och Copilot delar en faktisk Windows-terminal och en faktisk synlig browser. Ett webbaserat terminalfönster inuti Docker riskerar att skapa en annan session än den som äger browsern, PowerShell-kontexten och användarens inloggning.

Första säkra målbilden är därför:

- webben visar färdiga kommandon och åtgärder
- host runnern kan returnera ett standardiserat prompt-/kommandoobjekt
- användaren eller en kontrollerad host-side-brygga för in kommandot i Copilot CLI-sessionen
- faktisk testkörning och dokumentändring sker fortfarande i den gemensamma Copilot CLI-sessionen

Senare kan projektet utvärdera om en terminalnära brygga kan mata kommandon direkt till Copilot CLI utan att bryta samarbetsmodellen.

## Praktiska case som ska validera designen

### Case 1 - Lära Copilot ett nytt test

Mål: användaren ska kunna starta Learning Mode för ett nytt eller befintligt test utan att formulera hela prompten manuellt.

Praktiskt flöde:

1. Användaren öppnar control plane.
2. Användaren väljer `Learning Mode`.
3. Användaren väljer befintligt test eller anger att ett nytt test ska skapas.
4. Control plane visar vilken browser/session som används och vilken miljö rollen gäller.
5. Control plane genererar ett standardiserat Copilot-kommando.
6. Kommandot skickas till eller kopieras in i den gemensamma Copilot CLI-sessionen.
7. Copilot följer Learning Mode-reglerna: uppdaterar testdefinitioner och kataloger, men skapar inte rapport i `test_reports`.
8. Efter ändring körs obligatoriska dokument-/regressionstest beroende på vilka filer som ändrats.

Första POC-status: runnern har redan kommandomall för `enter-learning-mode`, men saknar ännu full modell för att skapa nytt test-ID, miljö, roll och DS-scope.

### Case 2 - Visa Mermaid-diagram över testberoenden

Mål: användaren ska kunna förstå beroenden mellan regressionstester utan att öppna markdownfiler.

Praktiskt flöde:

1. Control plane anropar host runnerns graph-funktion.
2. Host runnern läser `testing\regression_test\regression-test-dependencies.mmd`.
3. Webgränssnittet renderar Mermaid-grafen.
4. Användaren kan klicka eller läsa test-ID och se relaterad testdefinition.

Första POC-status: `runtime\render-regression-graph.ps1` returnerar redan Mermaid-källan.

### Case 3 - Följa testningen i ett webbfönster

Mål: användaren ska kunna följa vad som händer utan att läsa all terminaloutput.

Praktiskt flöde:

1. Copilot startar eller fortsätter regressionstestet i CLI-sessionen.
2. Host runnern skriver strukturerad körstatus, loggrad, aktivt test, vänteläge och rapportpekare.
3. Control plane pollar eller prenumererar på host runner-status.
4. Webgränssnittet visar:
   - aktivt test
   - senaste loggrad
   - om Copilot väntar på användarinloggning
   - länkar till rapporter och felrapporter
   - aktuell browser-session/debug-port om relevant

Första POC-status: runnern kan läsa senaste rapport och returnera status, men har ännu inte live-jobblogg eller aktiv Copilot-körstatus.

### Case 4 - Gemensam browser där användaren kan logga in

Mål: användaren ska kunna logga in i samma browser som Copilot använder för testobservation.

Praktiskt flöde:

1. Användaren eller Copilot startar browsern via `runtime\start-collaborative-stage-browser.ps1`.
2. Browsern öppnas synligt på Windows-värden.
3. Användaren loggar in manuellt om Microsoft-inloggning visas.
4. Copilot använder debug-porten för att läsa och styra samma browser.
5. Control plane visar bara status och instruktioner; den äger inte browsern.

Första POC-status: browsermodellen finns redan och är dokumenterad. Control plane behöver bara visa sessionens status och tydliga instruktioner, inte ersätta browsern.

## Slutsats för nästa implementation

Innan Docker-control-plane byggs vidare ska projektet låsa en användarprocess med tre separata ytor:

1. Copilot CLI-terminalen som gemensam arbets- och beslutsyta.
2. Den synliga browsern som gemensam inloggnings- och testyta.
3. Web control plane som administrativ översikt och standardiseringsyta.

Det innebär att nästa tekniska steg inte bör vara ett stort web UI direkt. Nästa steg bör vara att definiera host-runnerns processkontrakt för:

- Learning Mode-kommandon
- körstatus och live-logg
- browser-sessionstatus
- Mermaid- och rapportlänkar
- hur ett webbaserat kommando blir en kontrollerad Copilot CLI-instruktion
