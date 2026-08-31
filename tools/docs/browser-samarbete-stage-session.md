# Browser-samarbete i stage-sessioner

Detta dokument fastställer hur en SPS-session ska startas när arbetet kräver inloggning, UI-analys eller gemensam handläggning i Kundtjänstportalen.

> För **Copilot-admins localhost-UI** används inte detta stage-skript som förstahandsval. Se `tools\docs\copilot-admin-browser-lagen.md` och `runtime\start-collaborative-copilot-admin-browser.ps1` för den separata synliga admin-browsern.

## Mål

Vi ska kunna:

- öppna en **synlig** webbläsarsession som användaren själv ser
- låta användaren logga in eller klicka i samma fönster
- låta agenten läsa sidans state och styra samma session via browser-debugging
- återanvända samma metod som standard när en ny SPS-genomgång startar

## Fastställd arbetsmodell

1. Starta en ny **Edge/Chrome-session i InPrivate/Incognito-läge**.
2. Sessionen ska vara **synlig för användaren** och använda **remote debugging**.
3. Agenten kopplar upp sig mot browserns debug-endpoint och läser/styr sidan programmässigt.
4. Användaren kan under tiden själv logga in, klicka på länkar och fylla i formulär.
5. Agenten använder därefter samma session för inventering, analys, test och dokumentproduktion.

## Centrala skript

| Syfte | Källkod | Runtime |
| --- | --- | --- |
| Starta synlig samarbetsbrowser | `tools\source\browser_collaboration\Start-CollaborativeBrowserSession.ps1` | `runtime\start-collaborative-stage-browser.ps1` |
| Öppna ny flik i samma fönster | `tools\source\browser_collaboration\Open-SharedBrowserTab.ps1` | `runtime\open-shared-browser-tab.ps1` |
| Inventera Kundtjänst-menyer | `tools\source\browser_collaboration\Invoke-KundtjanstMenuInventory.ps1` | `runtime\inventory-kundtjanst-menus.ps1` |
| Generera CSC-manual från insamlad data | `tools\source\documentation_generation\generate_kundtjanst_function_doc.py` | `runtime\generate-kundtjanst-function-doc.ps1` |
| Verifiera dokumentindex | `tools\source\document_index_validation\validate_document_index.py` | `runtime\test-document-index.ps1` |

## Standardflöde för varje ny UI-session

### 1. Starta browsern

```powershell
.\runtime\start-collaborative-stage-browser.ps1
```

Detta ska öppna SPS i ett nytt synligt browserfönster, använda separat profil i `tmp` och aktivera debug-port så att agenten kan läsa och styra sessionen.

### 2. Låt användaren logga in

Om sessionen kräver inloggning gör användaren detta själv i den synliga browsern. Det är den föredragna modellen för stage-/interna miljöer där användaren redan har korrekt åtkomst.

Om sessionen blir stående på Microsoft-inloggning ska agenten vänta minst **5 minuter** så att användaren hinner slutföra inloggningen innan sessionen markeras som blockerad eller behandlas som misslyckad inloggning.

### 3. Genomför analys/inventering

När användaren är inne i systemet kan agenten läsa aktuell sida, följa navigation, extrahera menyer/formulär/tabeller/fel och producera dokumentation baserat på faktisk UI-observation.

### 3a. Öppna fler flikar i samma fönster

Om test eller analys kräver fler miljöer i samma synliga browserfönster ska agenten öppna nya flikar via:

```powershell
.\runtime\open-shared-browser-tab.ps1 -Url "https://sps-stage-legacy.europark.local/"
```

Detaljerad metodik finns i `tools\docs\delad-browser-flikstyrning.md`.

### 4. Spara rådata

Rå browserextraktion ska sparas i `raw_data`, till exempel `raw_data\kundtjanst-funktioner-data.json`.

### 5. Generera dokumentation

```powershell
.\runtime\generate-kundtjanst-function-doc.ps1
```

Detta ska skapa eller uppdatera `manuals\csc_user_manuals\Kundtjänst - funktioner.md`.

## Viktiga regler

- Browsern ska vara **synlig**, inte headless.
- Tillfälliga browser-profiler och temporära filer ska ligga i `tmp`.
- Runtime-skript ska vara körbara direkt utan att agenten måste uppfinna arbetsflödet på nytt.
- Källkod ska ligga under `tools\source`; körklara entrypoints ska ligga under `runtime`.
- Man ska i första hand läsa UI-state via debuggränssnittet, inte via manuella skärmbildstolkningar.
- Länkar som riskerar att logga ut användaren eller byta till extern miljö ska hanteras medvetet i inventeringsskript.
