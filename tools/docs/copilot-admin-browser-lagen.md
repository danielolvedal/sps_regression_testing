# Copilot-admin browserlägen

Detta dokument skiljer uttryckligen mellan **manuell synlig browser för användaren** och **automationsbrowser för tester** i Copilot-admin-flödet.

## Varför separationen behövs

Två olika browserroller används i repositoryt:

1. **Synlig användar-/agentsession** för manuellt frontendarbete mot Copilot-admins localhost-UI.
2. **Isolerad testbrowser** för automatiserad real-E2E och annan reproducerbar automation.

Om samma browser, debug-port eller profil återanvänds för båda rollerna riskerar vi att:

- blanda användarens arbete med testautomation
- återöppna fel sida, till exempel stage i stället för localhost-admin-UI
- återanvända fel debug-port
- mäta fel latens eftersom fel browser eller fel session observeras

## Fastställda portar och roller

| Roll | URL | Browser debug-port | Kommentar |
| --- | --- | --- | --- |
| Copilot-admin localhost UI, manuellt synlig | `http://127.0.0.1:8765/` | `9223` | Dedikerad synlig browser för användaren och agenten när arbetet gäller Copilot-admin-frontend. |
| Stage/Kundtjänst shared browser | `https://sps-stage.europark.local/CustomerService` | `9222` | Standardbrowser för stage-arbete, inloggning och gemensam UI-observation i SPS. |
| Automatiserad real-E2E | normalt `http://127.0.0.1:8877/` | `9322` | Endast för automation; ska inte återanvändas som manuell arbetsbrowser. |

## Portanalys

- `8765` är **Copilot-admin backend/UI-porten**, inte browserns debug-port.
- `8766` används normalt av **host-runner API** i den lokala admin-uppsättningen.
- `9222` är redan etablerad som **stage/shared browser** och ska inte vara default för localhost-admin-UI.
- `9223` är därför vald som default för **synlig localhost-admin-browser** för att hålla den skild från både stage (`9222`) och automation (`9322`).
- `9322` är reserverad för **real-E2E-automation** enligt repo-reglerna och ska inte användas för manuellt arbete.

Den viktiga slutsatsen är att `http://127.0.0.1:8765/` är rätt **URL** för lokal Copilot-admin när backenden kör, men **inte** rätt port för browser-debugging. Browsern ska använda en separat debug-port.

## Manuellt frontendarbete mot Copilot-admin

När användaren och agenten ska arbeta tillsammans i Copilot-admin-frontend ska den synliga browsern startas via:

```powershell
.\runtime\start-collaborative-copilot-admin-browser.ps1
```

Detta skript:

- öppnar `http://127.0.0.1:8765/`
- använder debug-port `9223` som default
- återanvänder samma browser på `9223` om den redan kör
- håller rollen separat från stage-browsern och testautomation

Om backenden inte redan är startad varnar skriptet, men öppnar fortfarande sidan så att användaren tydligt ser vilken yta som avses.

## När stage-browsern ska användas i stället

När arbetet gäller stage-systemet, Kundtjänstportalen, inloggning eller annan gemensam SPS-UI-observation ska följande skript användas:

```powershell
.\runtime\start-collaborative-stage-browser.ps1
```

Det skriptet är fortfarande standard för stage-arbete och använder normalt debug-port `9222`.

## När automationsbrowsern ska användas

När målet är reproducerbar testautomation eller real-E2E ska den dedikerade testkedjan användas:

```powershell
.\runtime\docker\copilot-admin\test-real-visible-e2e.ps1
```

Den kedjan ska:

- använda isolerad runner-state under `tmp\copilot_admin_control_plane\real_visible_e2e\runner_state`
- hålla Copilot-hjälparen separat från användarens produktionssession
- använda egen browserisolering, normalt på debug-port `9322`

Den browsern är **inte** den manuella arbetsytan för frontendutveckling eller användarsamarbete.

## Regler för framtida agenter

- För **manuellt Copilot-admin-frontendarbete**: använd `runtime\start-collaborative-copilot-admin-browser.ps1`.
- För **stage-/systemarbete**: använd `runtime\start-collaborative-stage-browser.ps1`.
- För **automatiserade real-E2E-tester**: använd `runtime\docker\copilot-admin\test-real-visible-e2e.ps1`.
- Blanda inte browserprofiler eller debug-portar mellan dessa tre lägen utan ett uttryckligt, dokumenterat skäl.
