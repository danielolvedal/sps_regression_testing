# 0001 - Session bootstrap via synlig browser

## Status

Beslutad

## Beslut

SPS-sessioner som kräver UI-inspektion eller inloggning ska startas med en **synlig InPrivate/Incognito-browser** med aktiverad remote debugging.

## Skäl

- användaren kan logga in själv
- agenten kan analysera samma session
- modellen fungerar bra för dokumentation och funktionstest
- sessionen blir repeterbar och enkel att automatisera

## Konsekvenser

- `runtime\start-collaborative-stage-browser.ps1` blir standard-entrypoint
- tillfälliga browserprofiler ska ligga i `tmp`
- runtime och source code måste hållas i synk
