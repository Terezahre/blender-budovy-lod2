# Pilotní výsledky: 7 budov Geoflow LoD2.2 v S-JTSK

> Sources: vlastní měření, 2026-11-20; 2026-11-21
> Raw: [vysledky](../../raw/pipeline/2026-11-20-pilot-vysledky.md); [scan](../../raw/pipeline/2026-11-21-scan-sedlovky.md); [blender](../../raw/blender/2026-11-20-blender43-headless.md)
> Updated: 2026-11-21; KOREKCE 2026-11-22 (viz níže)

## KOREKCE 2026-11-22: část modelů je fakticky LOD1

`scripts/audit_roofplanes.py` (shlukování normál, 10°): B02/B03/G2/G3/Z3 mají **1 střešní rovinu (plochý vršek)** přestože profil říká sedlová/valbová. Skutečné LOD2 (2 roviny) má jen **G1**; B01/B04 jsou správně ploché. Brno Geoflow výstupy: všech 7 s 1 rovinou.

Příčina: `DetectLines` nenajde hřebenové přímky (řídké DMP1G / rastr) → aranžmá bez vnitřních linií → plochý vršek. Validace (manifold, planarita, Val3dity) úroveň LOD nekontroluje — proto verdikty PASS níže platí pro **topologii**, ne pro střešní strukturu. Verdikt „PASS" = validní solid v S-JTSK; sloupec střech je opravený auditem.

## Overview (původní text 2026-11-21, ponechán z důvodu evidence)

Dodávka: 7 budov Geoflow LoD2.2 jako .obj v S-JTSK (EPSG:5514) v output/final/ — 4 ploché z pilotu + 3 sedlové z celomapového scanu. Vlastní cesta je odstavena (viz níže).

## Budovy (finální = Geoflow LoD2.2)

| ID | Profil | Geoflow RMSE | Mesh | Verdikt |
|---|---|---|---|---|
| B01_flat (211 bodů, 3.41 m) | SIMPLE_FLAT | 0.164 m | 32v/60f | PASS |
| B02_gable (229 bodů, 9.11 m) | STANDARD_GABLE | 0.460 m | 16v/28f | PASS |
| B03_row (210 bodů, 7.39 m) | COMPLEX_HIP | 1.588 m | 18v/32f | REVIEW |
| B04_panelak (750 bodů, 26.3 m) | SIMPLE_FLAT | 0.042 m | 36v/68f | PASS |
| G1_sedlova (280 bodů, 9.0 m) | COMPLEX_HIP | 1.669 m | 26v/48f | PASS |
| G2_sedlova (300 bodů, 6.59 m) | COMPLEX_HIP | 1.520 m | 20v/36f | PASS |
| G3_domek (164 bodů, 5.3 m) | COMPLEX_HIP | 0.774 m | 20v/36f | PASS |
| B05_vez (489 bodů) | COMPLEX_HIP | 8.570 m | 20v/36f | FAIL-skipped → output/rejected/ |

Všechny finální meshe: non-manifold 0, degenerované faces 0, normály konzistentní. Náhledy v render/geof_*.png. Vlastní stupňovitá cesta (nižší RMSE na plochých střechách, ale bez střešní struktury) je odstavena do output/ours/.

## Otevřené body

- Geoflow CLI doinstalovat s admin právy a přeběhnout `lod22-reconstruct` s configy z buildings/*/config.toml.
- B05: rozdělit RUIAN footprinty / hustší data; PolyFit na této hustotě neprojde.
- Šikmé střechy v datech zatím nejsou — Delaunay větev čeká na první sedlovou střechu.

## See Also

- [Per-building profily](../geoflow/profily-parametru.md)
- [PolyFit fallback](../polyfit/fallback.md)
- [Blender validace](../blender/validace.md)
