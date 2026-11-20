# Knowledge Base Index

## laz-dmp1g

Vstupní letecké mračno ČÚZK DMP 1G (S-JTSK).

| Article | Summary | Updated |
|---------|---------|---------|
| [Data KRAV59](laz-dmp1g/krav59-data.md) | Mračno KRAV59: 1.67M bodů, hustota na střechách ~1.5/m2 | 2026-11-20 |
| [Klastrování budov](laz-dmp1g/klastrovani.md) | DBSCAN eps=2.5, konvexní footprinty, lekce o kontaminaci bboxem | 2026-11-20 |

## geoflow

Rekonstrukce Geoflow a per-building parametry.

| Article | Summary | Updated |
|---------|---------|---------|
| [Per-building profily](geoflow/profily-parametru.md) | SIMPLE_FLAT / STANDARD_GABLE / COMPLEX_HIP / SPARSE + aplikace na pilot | 2026-11-20 |
| [Rekonstrukční postup](geoflow/rekonstrukce-postup.md) | RANSAC → DSM → stupně/heightfield → validátor + nástrahy | 2026-11-20 |
| [Skutečný Geoflow běh](geoflow/skutecny-beh.md) | geof 0.3.6 na všech 5 budovách + srovnání RMSE s vlastní cestou | 2026-11-21 |

## polyfit

PolyFit fallback pro složité budovy.

| Article | Summary | Updated |
|---------|---------|---------|
| [PolyFit fallback](polyfit/fallback.md) | Kdy nastupuje + proč na řídkých datech SCIP vrací 0 faces | 2026-11-20 |

## blender

Blender validace a S-JTSK workflow.

| Article | Summary | Updated |
|---------|---------|---------|
| [Blender validace](blender/validace.md) | Offset workflow (float32), cleanup metriky, CYCLES rendery | 2026-11-20 |

## pipeline

Celkový přehled a výsledky.

| Article | Summary | Updated |
|---------|---------|---------|
| [Pilotní výsledky](pipeline/vysledky-pilot.md) | 4 budovy LOD2 PASS/REVIEW, B05 FAIL, otevřené body | 2026-11-20 |
