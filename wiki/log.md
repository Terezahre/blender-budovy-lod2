# Wiki Log

## [2026-11-21] ingest | Skutečný Geoflow běh 0.3.6 + srovnání
- Disposition: New
- Raw: raw/geoflow/2026-11-21-geof-run.md
- Updated: wiki/geoflow/skutecny-beh.md

## [2026-11-21] build | Three.js prohlížeč viewer_3d.html
- Disposition: New
- 7 budov Geoflow LoD2.2, geometrie vložená v HTML, S-JTSK offset v UI (2026-11-21: jen Geoflow, bez přepínače cest)

## [2026-11-21] build | Geoflow dialog (.bat + HTA JavaScript)
- Disposition: New; Update (9 rucnich parametru: planarita, complexity, raster)
- geoflow_dialog.bat + geoflow_dialog.hta: vstup, výstup, ID, profil + 9 číselných polí
- Nove globaly flowchartu: r_max_arr_complexity (400), r_raster_cellsize (0.05)

## [2026-11-21] ingest | Celomapový scan sedlovek + Geoflow-only
- Disposition: New; Update (vysledky-pilot.md)
- Raw: raw/pipeline/2026-11-21-scan-sedlovky.md
- Updated: wiki/pipeline/sedlovky.md
- Finále = 7× Geoflow LoD2.2 (B01–B04, G1–G3); vlastní cesta odstavena do output/ours/

## [2026-11-21] ingest | CityJSON výstup + Blender roundtrip
- Disposition: New
- Raw: raw/pipeline/2026-11-21-cityjson.md
- Updated: wiki/pipeline/cityjson.md
- Finále: 7× CityJSON 2.0 (EPSG:5514) + OBJ; run_cityjson.py pro všech 9 budov

## [2026-11-21] ingest | Střechy: placatění, G3 recept, globalizace CityJSON
- Disposition: New
- Raw: raw/geoflow/2026-11-21-strechy.md
- Updated: wiki/geoflow/strechy.md
- DETAIL flowchart + DETAIL_GABLE jen pro G3; G2 split negativní (ploché poloviny)

## [2026-11-21] ingest | ZABAGED footprinty (konec blobů)
- Disposition: New
- Raw: raw/pipeline/2026-11-21-zabaged.md
- Updated: wiki/pipeline/zabaged.md
- 1495 budov KRAV59; Z3 (RMSE 0.104) → 8. finální; Z1/Z2 REJECT; OSM blokováno (406)

## [2026-11-20] ingest | Data KRAV59 + Geoflow + PolyFit + Blender + pilotní výsledky
- Disposition: New
- Raw: raw/laz-dmp1g/2026-11-20-krav59-dmp1g.md
- Raw: raw/geoflow/2026-11-20-geoflow-bundle.md
- Raw: raw/polyfit/2026-11-20-polyfit-format-a-vahy.md
- Raw: raw/blender/2026-11-20-blender43-headless.md
- Raw: raw/pipeline/2026-11-20-pilot-vysledky.md
- Updated: wiki/laz-dmp1g/krav59-data.md
- Updated: wiki/laz-dmp1g/klastrovani.md
- Updated: wiki/geoflow/profily-parametru.md
- Updated: wiki/geoflow/rekonstrukce-postup.md
- Updated: wiki/polyfit/fallback.md
- Updated: wiki/blender/validace.md
- Updated: wiki/pipeline/vysledky-pilot.md
