# 15 vikýřů západního svahu (PL pilot, ID-1465)

> Sources: GUGiK ORTO WMS StandardResolution (okno 200 m, 10 cm/px), LAZ 12 pts/m2 2025
> Raw: [vikyre15](../../raw/pl/2026-11-23-vikyre15.md)
> Updated: 2026-11-23

## Overview

Kompletní osazení západního (dvorního) svahu segmentu ID-1465: **15 vikýřů
ve dvou řadách** — horní řada 5 s většími rozestupy (4–8 m), dolní řada
10 (shluk 2 + řada 8 po ~1.8 m). Každý obdélník snapnut na okap (−41.3°),
top = q95 LiDARu v jeho místě (vlastní výška), graft + boolean v Blenderu.

## Co platí pro tento dům

- Orto a LiDAR sedí přímo (jasový test 12/15 bílých přímo na souřadnici,
  3 ve stínu); žádný posun. NCC registrace přes masky selhává, nepoužívat.
- SZ konec segmentu (t < −14): LiDAR boule = koruna stromu nad parkovištěm
  (class 6 chyby), NEJSOU vikýře — GT polygon tam přesahuje přes parkoviště.
- Geoflow jehly (až 128.9) přesahují skutečné topy → boolean nutný, graft nestačí.
- Výsledek: `model_west15_bool.obj` (756 verts / 813 faces, nm=0),
  RMSE 2.985 (jádro 0.546, pásy vikýřů 0.843); srovnán i východní
  okap (28 vrcholů na rovinu, řez sedí max +0.11 m).
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
