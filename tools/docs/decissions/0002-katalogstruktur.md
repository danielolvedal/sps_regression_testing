# 0002 - Fast katalogstruktur

## Status

Beslutad

## Beslut

Projektet ska använda den katalogstruktur som beskrivs i `tools\docs\katalogstruktur.md`.

## Skäl

- AI-agenter måste snabbt hitta rätt material
- rådata, syntetisk data, runtime och färdiga manualer behöver skiljas åt
- temporära filer måste begränsas till en enda plats
- verktygskällkod och verktygsdokumentation ska ligga under ett gemensamt tydligt `tools`-träd

## Konsekvenser

- nya artefakter ska placeras i befintliga kataloger
- `dokument_index\index.md` måste uppdateras när nya dokument tillkommer
- `AGENTS.md` ska styra agenter till indexet och strukturen
