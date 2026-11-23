# 16 vikýřů západního svahu (PL pilot, ID-1465)

> Sources: GUGiK ORTO WMS StandardResolution (okno 200 m, 10 cm/px), LAZ 12 pts/m2 2025
> Raw: [vikyre15](../../raw/pl/2026-11-23-vikyre15.md)
> Updated: 2026-11-23

## Overview

Kompletní osazení západního (dvorního) svahu segmentu ID-1465: **16 vikýřů
ve dvou řadách** — horní řada 6 (U0–U5) s většími rozestupy, dolní řada
10 (shluk 2 + řada 8 po ~1.8 m). Každý obdélník snapnut na okap (−41.3°),
top = q95 LiDARu v jeho místě (vlastní výška), graft + boolean v Blenderu.
(U0 na SZ vrácen dodatečně: kompaktní boule n=51, 98 % bílých pixelů.)

## Co platí pro tento dům

- Orto a LiDAR sedí přímo (jasový test 12/15 bílých přímo na souřadnici,
  3 ve stínu); žádný posun. NCC registrace přes masky selhává, nepoužívat.
- SZ konec segmentu: koruna stromu nad parkovištěm (class 6 chyby) + U0:
  U0 (t=−16.5, E 637085.1, N 488272.0, top 128.13) je správně vikýř
  (kompaktní boule n=51, 98 % bílých pixelů) — vrácen jako 16. do modelu.
  GT polygon tam zasahuje, LiDAR 2025 říká střecha z~128.
- Geoflow jehly (až 128.9) přesahují skutečné topy → boolean nutný, graft nestačí.
  Solver MANIFOLD (EXACT mazal celé tělo u U0 na koplanárním podkladu).
- Stejné okapy Z/V: východ rigidně otočen kolem 3D hřebene (−8.76°),
  okap 124.53 → 125.38 (= západní). Komin v meshi není.
- Výsledek: `model_west15_bool.obj` (782 verts / 804 faces, nm=0),
  RMSE 3.378 (jádro 0.732 — východní svah mimo data rozhodnutím,
  pásy vikýřů 0.825); oba okapy přesně 125.38 po celé délce.
- Předchůdce (jen 5 vikýřů, viz [oprava vikýřů z ortofota](vikyre-orto.md))
  slučoval prostřední řadu do 1 velkého a konce bral ze stromu/stínu.

## Vstupy / skripty / výstupy

- Vstupy: `buildings_pl/<FID>/body.las`, `data_pl/warszawa_gt.json`,
  `data_pl/warszawa_orto_200m_north.tif`, `model_lod22.obj`.
- Skripty: `scripts/pl_west15_step{1,5,6,7,8}.py` (K-planes → heatmap → layout
  + graft → metriky → 3D), `pl_boolean.py` + `pl_west15_render.py` (Blender 5.3).
- Výstupy (gitignored, reprodukovatelné): `model_west15_graft.obj`,
  `model_west15_bool.obj`, `west15_layout.json`, `west15_metrics.json`.
- Rendery (verzované): `render/pl_west15_{overlay,compare,band,before,after}.png`.
- Prohlížečka: `viewer_pl_west15.html` (three.js, LOD22 / graft / bool + metriky).

## See Also

- [Měřicí záznam](../../raw/pl/2026-11-23-vikyre15.md)
- [Oprava vikýřů z ortofota (5, předchůdce)](vikyre-orto.md)
- [Pilotní výsledky](../pipeline/vysledky-pilot.md)
