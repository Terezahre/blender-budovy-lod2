# Blender validace a S-JTSK workflow

> Sources: vlastní měření (Blender 4.3.2), 2026-11-20
> Raw: [blender](../../raw/blender/2026-11-20-blender43-headless.md)
> Updated: 2026-11-20

## Overview

Headless Blender (scripts/blender_validate.py) čistí mesh, kontroluje manifold a renderuje náhled; souřadnice zůstávají v S-JTSK díky offsetovému workflow.

## Pravidla

- Před importem odečíst min. roh (float32!), po exportu přičíst zpět v textu OBJ — geometrie se nikdy neškáluje ani neposouvá.
- Cleanup: merge 1 mm, delete loose, recalc normals; flat shading (hladké četlo roviny jako bubliny).
- Render: CYCLES CPU, kamera bounding-sphere fit, ABSOLUTNÍ cesta (relativní se v background ztratí).
- Cílové metriky: non-manifold 0→0, degenerované faces 0, normály UP/DOWN/WALL dle počtu úrovní.

## See Also

- [Rekonstrukční postup](../geoflow/rekonstrukce-postup.md)
- [Pilotní výsledky](../pipeline/vysledky-pilot.md)
