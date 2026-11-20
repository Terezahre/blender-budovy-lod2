# Blender LOD2 budovy — Geoflow + PolyFit + Blender (S-JTSK EPSG:5514)

Cíl: nedeformované 3D budovy v **LOD2.2** z mračna **ČÚZK DMP 1G** (S-JTSK).
Vstup: `KRAV59_DMP1G/KRAV59.laz` (1 669 893 bodů, class 6 = budovy).
Výstup: `output/final/<ID>_LOD2_SJTSK.obj` + `*.meta.json` (`crs: EPSG:5514`).

Pravidla a parametry: viz [agents.md](agents.md). Znalostní báze: [wiki/index.md](wiki/index.md).
Interaktivní 3D prohlížeč výsledků: [viewer_3d.html](viewer_3d.html) (three.js, přepínání budov + naše/Geoflow cesta, dvojklik z disku).

## Rychlý start

1. Nainstaluj Geoflow CLI (Windows instalátor `Geoflow-2024.03.08-win64.exe`, vyžaduje admin) —
   po instalaci `lod22-reconstruct --help` a `geof --list-nodes`.
2. `pip install laspy lazrs numpy scikit-learn scipy shapely`
3. `python scripts/analyze_laz.py` — statistika + výběr budov.
4. `python scripts/extract_buildings.py` — klastry, footprinty, `buildings/<ID>/meta.json`.
5. `lod22-reconstruct --input_footprint buildings/<ID>/footprint.gpkg --input_pointcloud buildings/<ID>/body.las --config buildings/<ID>/config.toml`
6. Komplexní budovy: `python scripts/polyfit_fallback.py --id <ID>`.
7. `blender --background --python scripts/blender_validate.py -- <in.obj> <out.obj>`.
8. Wiki update + commit + push.

## Stav (2026-11-21)

- [x] Vstupní data ověřena (KRAV59, 939 311 bodů class 6)
- [x] 5 pilotních budov vybráno + footprinty (GPKG S-JTSK) + per-building configy
- [x] LOD2 rekonstrukce: B01/B02/B04 PASS, B03 REVIEW, B05 FAIL-skipped
- [x] PolyFit pipeline ověřen na toy_data; na pilotu SCIP vrací 0 (dokumentováno)
- [x] Blender validace (manifold 0, normály OK) + finální OBJ v S-JTSK + rendery
- [x] Wiki (8 článků) + agents.md
- [x] Geoflow 0.3.6 nainstalováno + proběhnuto všech 5 budov (output/geof/, srovnání v compare.json)
- [ ] B05: RUIAN footprinty / hustší data; šikmé střechy (Delaunay větev)
