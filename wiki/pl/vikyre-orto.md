# Oprava vikýřů z ortofota (PL pilot)

> Sources: GUGiK ORTO WMS StandardResolution/TrueOrtho, GML LoD2 1465, LAZ 12pts/m2 2025
> Raw: [vikyre](../../raw/pl/2026-11-22-vikyre.md)
> Updated: 2026-11-22

## Overview

Automaticka oprava Geoflow vikýřů fůzi ortofoto + LiDAR: orto diktuje relativni
geometrii (pocet v rade, roztec, pravoúhlost vuci okapu), LiDAR absolutni vysky
(median svahu/podtypu). Boolean cleanup v Blenderu (headless) dosadi ciste
hranoly misto 'jehel'. Overeno na budove ID-1465 (Varšava).

## Co plati pro tento dum

- Neni true-orto: TrueOrtho WMS pro okno vraci prazdno; pouzito klasicke orto
  10 cm/px (WMS BBOX v poradi N,E; radek 0 = sever, overeno vegetaci).
- Klasicke orto ma mirny zastin; detekce z orta se pouziva prevazne relativne
  (rada/roztec/pocet), kotveni a vysky z LiDARu.
- Prekryv render/pl_dormers_overlay.png sedi presne na vikýřích (opraveno
  22.11. vecer: radek 0 = sever, ne jih).
- GML GT svahy jsou ~5 m mimo mracno 2025 (jina epocha) — jako prior zamitnuty.
- Vysledek: 5 vikýřů (2+3 po svazich, z toho 1 velky podtyp), bias <=0.25 m,
  RMSE jadra 0.52->0.56 m (strom venezmenen, regularita je zisk), nm=1 (vnitrni).
- Vstupy: `buildings_pl/<FID>/body.las`, `data_pl/dormers.json`, `data_pl/warszawa_orto_200m.tif`
- Skripty: `scripts/pl_orto_fix.py` (overeni okna) -> `scripts/pl_dormers_fix.py`
  (regularizace + graft + overlay) -> `scripts/pl_boolean.py` (Blender CSG) ->
  `scripts/blender_validate.py` (finale + render).
- Vystupy: `output/pl_geof/<FID>/model_bool.obj`, `model_final.obj` (gitignored,
  reprodukovatelne), rendery `render/pl_*.png` (verzovane).

## See Also

- [Merici zaznam](../../raw/pl/2026-11-22-vikyre.md)
- [Pilotni vysledky](../pipeline/vysledky-pilot.md)
