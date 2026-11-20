# Rekonstrukční postup (Geoflow-kompatibilní)

> Sources: 3DGI/geoflow-bundle; vlastní měření, 2026-11-20
> Raw: [geoflow](../../raw/geoflow/2026-11-20-geoflow-bundle.md); [vysledky](../../raw/pipeline/2026-11-20-pilot-vysledky.md)
> Updated: 2026-11-20

## Overview

Geoflow CLI zatím není nainstalováno (instalátor vyžaduje admin práva), takže běží kompatibilní postup se stejnou logikou uzlů: DetectPlanes (sekvenční RANSAC) → heightfield → ArrExtruder → Validator.

## Kroky

1. RANSAC rovin s per-building epsilon/min_points; klasifikace horizontal/slant/wall (prahy 0.97/0.30 jako v DetectPlanes).
2. DSM filtr (nejvyšší bod na 0.5m buňku) + kNN outlier filtr — odstraňuje fasády a chyby klasifikace.
3. Ploché střechy (vše horizontal, což je celý pilot): stupňovité kvádry po 1.0m Z-úrovních. Šikmé střechy (budoucí): 2.5D Delaunay s limitem hrany 4 m.
4. Validátor: degenerované faces, manifold audit, RMSE ke vstupním bodům (obdoba PC2MeshQuality).
5. Výstup OBJ v plných S-JTSK souřadnicích, precision 3 jako OBJVecWriter.

## Známé nástrahy (ověřeno)

- Výběr bodů bboxem kontaminuje sousedy (B04: RMSE 1.8 → 0.043 m po opravě).
- Zapisovat celé polygony, ne `fa[:3]` (useknuté N-úhelníky = díry).
- Orientace fan: ověřit UP/DOWN audit (shapely ringy chodí po směru hodin).

## See Also

- [Per-building profily](profily-parametru.md)
- [Blender validace](../blender/validace.md)
