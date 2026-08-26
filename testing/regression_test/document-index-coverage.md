# Regressionstest - dokumentindexets täckning

Detta test säkerställer att alla beständiga dokument och datafiler som ska vara sökbara för en agent också finns upptagna i `dokument_index\index.md`.

## Test-ID

regression-document-index-coverage

## Catalog Key

`D`

## Summary

Validate document index coverage for all tracked persistent documentation and data files.

## Dependencies

- none

## Varför testet är kritiskt

Om ett dokument inte finns i indexet riskerar en agent att aldrig hitta materialet, även om filen finns i repositoryt. Därför är detta ett blockerande och obligatoriskt regressionstest för nya eller ändrade dokument.

## Vad som kontrolleras

Testet verifierar att alla filer med dokument- eller dataformat i repositoryt finns refererade i indexet:

- `*.md`
- `*.mmd`
- `*.txt`
- `*.json`
- `*.pdf`
- `*.docx`
- `*.xlsx`

## Undantag

- filer under `tmp`
- tomma målkataloger där inga dokument ännu finns, som `manuals\user_manuals` och `manuals\client_manuals`

## Körning

```powershell
.\runtime\test-document-index.ps1
```

## Förväntat resultat

- Testet ska returnera exit code `0` när allt är korrekt indexerat.
- Testet ska returnera exit code `1` och lista saknade sökvägar när något dokument saknas i indexet.

## Arbetsregel

Varje gång ett beständigt dokument eller en beständig datafil skapas, ändras, flyttas eller tas bort ska:

1. filen placeras i rätt katalog
2. posten läggas till i `dokument_index\index.md`
3. detta regressionstest alltid köras

Om ändringen gäller `raw_data` ska även `.\runtime\test-kallinventering-coverage.ps1` köras.
