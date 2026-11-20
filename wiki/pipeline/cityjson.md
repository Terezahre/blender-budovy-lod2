# CityJSON výstup a cesta do Blenderu

> Sources: vlastní měření, 2026-11-21
> Raw: [cityjson](../../raw/pipeline/2026-11-21-cityjson.md)
> Updated: 2026-11-21

## Overview

Výstupním formátem je CityJSON 2.0 (EPSG:5514) s LoD 1.2/1.3/2.2; do Blenderu vede přes `cjio lod_filter 2.2` (bez filtru se vyvezou všechny LoD přes sebe). Roundtrip je geometricky 1:1.

## Detaily

- CityJSONWriter z instalace neumí 6 parametrů z bundlovaného flowchartu — flowchart je ořezán, matematika stejná.
- CRS v http formě (cjio neumí urn formu); Blender nemá nativní CityJSON import, most je oficiální `cjio` (+ `triangle`).
- `scripts/run_cityjson.py` přeběhne všech 9 budov najednou: geof → cjio → Blender (vše manifold 0).
- Finále: 7× `*_LOD2_SJTSK.json` + validovaný OBJ v `output/final/`.

## See Also

- [Skutečný Geoflow běh](../geoflow/skutecny-beh.md)
- [Pilotní výsledky](vysledky-pilot.md)
