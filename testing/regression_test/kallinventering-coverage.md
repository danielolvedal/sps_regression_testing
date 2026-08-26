# Regressionstest - källinventeringens täckning

Detta test säkerställer att `syntetisk_data\common\kallinventering.md` alltid täcker aktuellt innehåll i `raw_data` **och** spårar påverkan vidare in i `syntetisk_data`.

## Test-ID

regression-kallinventering-coverage

## Catalog Key

`E`

## Summary

Validate raw-data coverage and downstream synthetic-data traceability in kallinventering.md.

## Dependencies

- none

## Varför testet är kritiskt

Om ett nytt rådatadokument läggs till utan att källinventeringen uppdateras blir det syntetiska lagret snabbt missvisande. Då riskerar en agent att välja fel källor eller missa bättre underlag trots att filen finns i repositoryt.

## Vad som kontrolleras

Testet verifierar att alla spårade filer i `raw_data` täcks av `## Källor` i `syntetisk_data\common\kallinventering.md`.

Testet verifierar också att varje råkälla i tabellen under `## Data, objekt och regler` har:

- ett dokumenterat analysutfall
- antingen utpekade syntetiska dokument eller en explicit markering att ingen ytterligare påverkan fanns
- fungerande spårbarhet från råkällan till de syntetiska dokument som påstås vara uppdaterade

Följande filformat ingår:

- `*.md`
- `*.txt`
- `*.json`
- `*.pdf`
- `*.docx`
- `*.xlsx`

Testet tillåter wildcard-mönster i källinventeringen, exempelvis `raw_data\SPS Funktionsträd*.txt`, men faller om:

- en fil finns i `raw_data` utan motsvarande källreferens
- en källreferens i `kallinventering.md` inte längre matchar någon fil
- en råkälla saknar analysutfall
- ett utpekat syntetiskt dokument inte finns eller inte refererar till råkällan

## Körning

```powershell
.\runtime\test-kallinventering-coverage.ps1
```

## Förväntat resultat

- Testet ska returnera exit code `0` när `kallinventering.md` är uppdaterad.
- Testet ska returnera exit code `1` och lista avvikelser när `raw_data` och källinventeringen har glidit isär.

## Arbetsregel

Varje gång en fil i `raw_data` skapas, ändras, flyttas eller tas bort ska:

1. `syntetisk_data\common\kallinventering.md` uppdateras
2. påverkan på relevanta syntetiska dokument analyseras och dokumenteras
3. berörda dokument under `syntetisk_data` uppdateras
4. detta regressionstest alltid köras
5. dokumentindex-testet också köras eftersom filuppsättningen i repositoryt har ändrats
