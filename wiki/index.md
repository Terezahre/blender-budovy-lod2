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
| [Střechy: proč chybí](geoflow/strechy.md) | Placatění (cellsize, dissolve), recept DETAIL_GABLE, G2 split, CityJSON globalizace | 2026-11-21 |

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
| [Pilotní výsledky](pipeline/vysledky-pilot.md) | 7 budov Geoflow LoD2.2 (4 ploché + 3 sedlové), verdikty | 2026-11-21 |
| [Sedlovky ze scanu](pipeline/sedlovky.md) | Celomapový scan KRAV59 + Geoflow-only rozhodnutí | 2026-11-21 |
| [CityJSON výstup](pipeline/cityjson.md) | CityJSON 2.0 formát + cjio most do Blenderu (roundtrip 1:1) | 2026-11-21 |
| [Katastrální footprinty](pipeline/zabaged.md) | ZABAGED místo blobů: Z3 RMSE 0.104, pravidlo footprintů | 2026-11-21 |

## pl

Varšavský pilot (EPSG:2180, GUGiK data).

| Article | Summary | Updated |
|---------|---------|---------|
| [Oprava vikýřů z ortofota](pl/vikyre-orto.md) | Auto-fix 5 vikýřů fúzí orto+LiDAR + boolean (předchůdce) | 2026-11-22 |
| [15 vikýřů západního svahu](pl/vikyre-15.md) | Kompletních 15 (5+2+8), vlastní LiDAR výšky, boolean, RMSE | 2026-11-23 |
