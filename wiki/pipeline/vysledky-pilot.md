# Pilotní výsledky: 4 budovy LOD2 v S-JTSK

> Sources: vlastní měření, 2026-11-20
> Raw: [vysledky](../../raw/pipeline/2026-11-20-pilot-vysledky.md); [blender](../../raw/blender/2026-11-20-blender43-headless.md)
> Updated: 2026-11-20

## Overview

Dodávka: 4 nedeformované budovy LOD2 jako .obj v S-JTSK (EPSG:5514) v output/final/, každá s per-building Geoflow parametry; pátá (slitý klastr) je zamítnuta.

## Budovy

| ID | Profil | RMSE | Mesh | Verdikt |
|---|---|---|---|---|
| B01_flat (211 bodů, 3.41 m) | SIMPLE_FLAT | 0.056 m | 18v/20f | PASS |
| B02_gable (229 bodů, 9.11 m) | STANDARD_GABLE | 0.219 m | 16v/18f | PASS |
| B03_row (210 bodů, 7.39 m) | COMPLEX_HIP | 0.592 m | 16v/18f | REVIEW (nad 0.5 m, geometrie čistá) |
| B04_panelak (750 bodů, 26.3 m) | SIMPLE_FLAT | 0.043 m | 22v/24f | PASS |
| B05_vez (489 bodů, 35.11 m) | COMPLEX_HIP | 6.383 m | 84v/102f | FAIL-skipped → output/rejected/ |

Všechny finální meshe: non-manifold 0, degenerované faces 0, normály konzistentní. Náhledy v render/B*.png.

## Otevřené body

- Geoflow CLI doinstalovat s admin právy a přeběhnout `lod22-reconstruct` s configy z buildings/*/config.toml.
- B05: rozdělit RUIAN footprinty / hustší data; PolyFit na této hustotě neprojde.
- Šikmé střechy v datech zatím nejsou — Delaunay větev čeká na první sedlovou střechu.

## See Also

- [Per-building profily](../geoflow/profily-parametru.md)
- [PolyFit fallback](../polyfit/fallback.md)
- [Blender validace](../blender/validace.md)
