# Per-building profily Geoflow

> Sources: 3DGI/geoflow-bundle; vlastní měření, 2026-11-20
> Raw: [geoflow](../../raw/geoflow/2026-11-20-geoflow-bundle.md); [vysledky](../../raw/pipeline/2026-11-20-pilot-vysledky.md)
> Updated: 2026-11-20

## Overview

Každá budova dostává parametry podle vlastností svého mračna (hustota, zstd, odhad rovin). Výchozí hodnoty odpovídají gfc-lod13 (plane epsilon 0.2, min_points 15, data term 7.0).

## Profily (agents.md)

- SIMPLE_FLAT (zstd < 1.2): epsilon 0.25, min_points 20, k 15/8, line 0.5, data 5.0.
- STANDARD_GABLE (zstd 1.2–2.5): epsilon 0.20, min_points 15, k 15/8, line 0.4, data 7.0.
- COMPLEX_HIP (zstd ≥ 2.5 nebo > 4 rovin): epsilon 0.15, min_points 10, k 10/5, line 0.3, data 9.0, step 2.5, max_arr 800.
- SPARSE (hustota < 1.0): epsilon +0.05, min_points ×1.5, k +5, line +0.1, data −2.0. V pilotu se neuplatnila (nejnižší hustota byla 1.432/m2 u B04).

## Aplikace na pilot

B01 SIMPLE_FLAT → RMSE 0.056 m; B02 STANDARD_GABLE → 0.219 m; B03 COMPLEX_HIP → 0.592 m (REVIEW); B04 SIMPLE_FLAT → 0.043 m; B05 COMPLEX_HIP → 6.383 m (FAIL). Configy pro `lod22-reconstruct` leží v `buildings/*/config.toml` a čekají na instalaci Geoflow CLI.

## See Also

- [Klastrování](../laz-dmp1g/klastrovani.md)
- [PolyFit fallback](../polyfit/fallback.md)
