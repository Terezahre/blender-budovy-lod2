# Blender LOD2 budovy — Geoflow + PolyFit + Blender (S-JTSK EPSG:5514)

Cíl: nedeformované 3D budovy v **LOD2.2** z mračna **ČÚZK DMP 1G** (S-JTSK).
Vstup: `KRAV59_DMP1G/KRAV59.laz` (1 669 893 bodů, class 6 = budovy).
Výstup: `output/final/<ID>_LOD2_SJTSK.obj` + `*.meta.json` (`crs: EPSG:5514`).

Pravidla a parametry: viz [agents.md](agents.md). Znalostní báze: [wiki/index.md](wiki/index.md).
Interaktivní 3D prohlížeč výsledků: [viewer_3d.html](viewer_3d.html) (three.js, dvojklik z disku).
Dialogové spouštění Geoflow: [geoflow_dialog.bat](geoflow_dialog.bat) + [geoflow_dialog.hta](geoflow_dialog.hta) (JavaScript dialog: vstup + výstup + 9 laditelných parametrů: planarita, complexity, raster).

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
- [x] Celomapový scan: 286 kandidátů → 24 sedlovek → top 3 (G1, G2, G3)
- [x] Finále = 7× Geoflow LoD2.2 v S-JTSK (B01–B04 ploché + G1–G3 sedlové); B05/B06 zamítnuty
- [x] Vlastní cesta odstavena do output/ours/ (prototyp bez střešní struktury)
- [x] PolyFit pipeline ověřen na toy_data; na pilotu SCIP vrací 0 (dokumentováno)
- [x] Blender validace (manifold 0) + three.js prohlížeč (jen Geoflow)
- [x] Wiki (10 článků) + agents.md + GitHub push
- [x] CityJSON 2.0 jako výstupní formát (7× model.json EPSG:5514, cjio most do Blenderu)
- [ ] B05/B06: RUIAN footprinty / hustší data; valbové střechy
