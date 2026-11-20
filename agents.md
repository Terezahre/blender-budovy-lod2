# AGENTS.md — 3D budovy z mračna (Geoflow + PolyFit + Blender)

Cíl: nedeformované 3D budovy v LOD2 z leteckého mračna ČÚZK DMP 1G, výstup `.obj` v S-JTSK (EPSG:5514).

## Pipeline (povinné pořadí)

1. `data/` — vstupní LAZ/LAS (S-JTSK). Neměnit originály.
2. `scripts/analyze_laz.py` / `scripts/scan_map.py` — statistika mračna + klastry budov
   (DBSCAN class 6); sedlovky hledá celomapový scan (`buildings/gable_candidates.json`).
3. `scripts/extract_buildings.py` / `scripts/extract_map.py` — pro každou budovu: ořez bodů
   (budova + okolní terén class 2), footprint (GPKG/GeoJSON), `buildings/<ID>/meta.json`
   + `geof.toml` s per-building `r_*` parametry.
4. Geoflow 0.3.6 (`C:\Users\Tereza\geoflow-local\geof.exe` + `GF_PLUGIN_FOLDER`)
   s `flowcharts/krav59_lod22/reconstruct_objonly.json` (47 uzlů, jen OBJ)
   → `output/geof/<ID>/model_lod22.obj` (+ LOD12/LOD13).
5. Pokud je budova moc složitá (viz kritéria) → `scripts/polyfit_fallback.py` (stav viz wiki).
6. `scripts/blender_validate.py` (headless Blender) — kontrola deformací, cleanup,
   validovaný model do `output/final/<ID>_LOD2_SJTSK.obj` + render.
   Souřadnice se NESMÍ posouvat ani škálovat — výstup zůstává v S-JTSK (EPSG:5514).
   Most CityJSON→Blender: `cjio model.json lod_filter 2.2 export obj lod22.obj`
   (vyžaduje `pip install cjio triangle`); vše najednou žene `scripts/run_cityjson.py`.
7. Výstupní formát dodávky = CityJSON 2.0 (`output/final/<ID>_LOD2_SJTSK.json`,
   CRS `http://www.opengis.net/def/crs/EPSG/0/5514`) + validovaný OBJ jako příloha.
7. `scripts/make_viewer.py` → `viewer_3d.html` (three.js, jen Geoflow modely).
8. Wiki — po každém kroku aktualizovat `wiki/` + `wiki/log.md` (viz Wiki pravidla).

Vlastní prototypová cesta (`scripts/reconstruct_lod2.py` → `output/geoflow/`, kvádry
v `output/ours/`) je ODSTAVENA. Finále = výhradně Geoflow LoD2.2.

## Per-building parametry Geoflow (podle vlastností mračna)

Vstupní vlastnosti z `meta.json`: `n_points`, `density_pts_m2`, `z_std`, `height_range`, `footprint_area_m2`, `roofplane_guess` (odhad počtu rovin střechy), `coverage` (pokrytí daty 0–1).

| Profil | Kdy použít | `plane_detect__epsilon` | `plane_detect__min_points` | `plane_detect__k` / `normal_estimate__k` | `line_detect__epsilon` | `optimisation_data_term` | `lod13__step_height` |
|---|---|---|---|---|---|---|---|
| SIMPLE_FLAT | `z_std < 1.2` a `roofplane_guess <= 2` | 0.25 | 20 | 15 / 8 | 0.5 | 5.0 | 3.0 |
| STANDARD_GABLE | `1.2 <= z_std < 2.5` | 0.20 | 15 | 15 / 8 | 0.4 | 7.0 | 3.0 |
| COMPLEX_HIP | `z_std >= 2.5` nebo `roofplane_guess > 4` | 0.15 | 10 | 10 / 5 | 0.3 | 9.0 | 2.5 |
| SPARSE (`density < 1.0`) | + k profilu výše | +0.05 k epsilon | ×1.5 min_points | k +5 | +0.1 | −2.0 | beze změny |

- `max_arr_complexity` = 400 (standard), 800 pro COMPLEX_HIP.
- Vždy `building_class=6`, `ground_class=2`, `ground_percentile=0.05`, buffer 1.0 m.

## Kdy použít PolyFit (místo Geoflow)

- `arr_complexity > max_arr_complexity`, nebo Geoflow vrátí `reconstruction_skipped=true`,
- `roofplane_guess > 8`, nebo `coverage < 0.5`,
- RMSE Geoflow LOD2.2 > 0.5 m.
- PolyFit váhy: jednoduchá `data_fitting=0.43/coverage=0.27/complexity=0.30`; složitá `0.50/0.20/0.30`.

## LOD2 + „nedeformované" (definice hotového)

- LOD2.2: střešní roviny z mračna + stěny + podlaha; žádné textury, jen geometrie.
- Validní: Val3dity `Validator.errors` prázdné, všechny polygony planární (odchylka < 1 cm), normály konzistentní, mesh manifold (žádné T-junkce, žádné self-intersection).
- Kontrola v Blenderu: `3D-Print Toolbox` / `Mesh Analysis`, statistika degenerovaných faces = 0.
- CRS: S-JTSK / Krovak East-North (EPSG:5514), jednotky metry, osa Z = nadmořská výška (Balt po vyrovnání). Do OBJ se CRS nezapisuje — proto ke každému OBJ patří `*.meta.json` s `crs: EPSG:5514`.

## Blender

- Blender 4.3 (`C:\Program Files\Blender Foundation\Blender 4.3\blender.exe`), headless: `blender --background --python scripts/blender_validate.py -- <in.obj> <out.obj>`.
- Nikdy nemazat `cuzk_kobylisy.blend` / `prasatko.*` — to je referenční ruční model.
- Nové výstupy do `output/final/`, náhledy do `render/`.

## Wiki (povinné)

- Zdroje do `raw/<topic>/RRRR-MM-DD-slug.md`, články do `wiki/<topic>/<concept>.md`.
- Po každém pipeline kroku: aktualizuj dotčený článek + `wiki/index.md` + append do `wiki/log.md`.
- Každé číslo/fakt v `wiki/` musí být dohledatelné v linked `raw/` (grounding invariant). Žádná vymyšlená čísla.
- Před commitem spusť lint: `python <skill-dir>/scripts/check_evidence.py .` (je-li skill dostupný), jinak ruční kontrola Raw odkazů.

## Git / GitHub

- Branch `master`, repo `Terezahre/blender-budovy-lod2` (případně dle `gh repo list`).
- Malé, časté commity v češtině: `feat: ...`, `data: ...`, `wiki: ...`, `fix: ...`.
- Nepushovat bez kontroly `git status`. Velké binárky (>50 MB) patří do Release, ne do gitu.
- `Geoflow-*-win64.exe` (instalátor) a `KRAV59.zip` se verzují 1× a dál nemění.
- `geoflow-bundle/` a `PolyFit/` jsou upstream klony — do nich nesahat, jen číst. Vlastní flowcharty patří do `flowcharts/`.

## Adresářová struktura (vynucená)

```
agents.md, README.md
data/               # LAZ/LAS originály (read-only)
buildings/<ID>/     # body.las, footprint.gpkg, meta.json, config.toml
flowcharts/         # vlastní Geoflow flowcharty + configy
scripts/            # analyze, extract, polyfit, blender_validate
output/geoflow|polyfit|final/
render/             # PNG náhledy z Blenderu
wiki/ + raw/        # knowledge base (viz skill karpathy-llm-wiki)
ref/                # referenční fotky
```
