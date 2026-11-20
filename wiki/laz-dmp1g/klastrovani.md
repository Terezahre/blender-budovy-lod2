# Klastrování budov z class 6

> Sources: vlastní měření, 2026-11-20
> Raw: [krav59](../../raw/laz-dmp1g/2026-11-20-krav59-dmp1g.md); [vysledky](../../raw/pipeline/2026-11-20-pilot-vysledky.md)
> Updated: 2026-11-20

## Overview

Budovy se z class 6 hledají DBSCANem v testovací dlaždici 500×500 m; parametry eps=2.5, min_samples=30 jsou kompromis mezi konektivitou řídkých střech a sléváním sousedů.

## Zjištění

- eps=2.5/min_samples=30: 220 klastrů, šum 16 577 z 32 822 bodů. Menší eps (1.0–1.5) rozpadne i samotné střechy (zůstane jediný klastr 100+ bodů), protože rozestupy bodů DMP 1G přesahují 1.5 m.
- Footprint se odvozuje z konvexního obalu klastru (concave_hull při této hustotě vyrábí falešné zuby a díry).
- `body.las` obsahuje POUZE členy klastru + terén v bufferu — výběr celým bboxem kontaminoval data sousedními domy (u B04 to zvedlo RMSE z 0.043 m na 1.8 m).
- B05_vez (cl=73, zstd 11.111, výška 35.11 m) je slitina více objektů — DBSCAN ji nerozdělí a výsledek (RMSE 6.383 m) se zamítá. Správné řešení: katastrální footprinty (RUIAN) místo lidarových klastrů.

## See Also

- [Data KRAV59](krav59-data.md)
- [Profily parametrů](../geoflow/profily-parametru.md)
