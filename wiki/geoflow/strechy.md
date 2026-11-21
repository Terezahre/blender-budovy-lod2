# Proč některé střechy chybí a kde je G3 bere

> Sources: vlastní měření, 2026-11-21
> Raw: [strechy](../../raw/geoflow/2026-11-21-strechy.md)
> Updated: 2026-11-21

## Overview

Geoflow standardní cestou placatí (0 šikmých faces): heightfield 5 cm je pro 2 pts/m2 prázdný a `dissolve_seg_edges` slepí segmenty. Ověřený recept na sedlo existuje, ale funguje jen tam, kde sedlo ve skutečnosti je — polovina "sedlových" kandidátů jsou falešné poplachy (fasády, slepené domy).

## Co platí pro naše budovy

- G3_domek: pravé sedlo (recept DETAIL_GABLE + DETAIL flowchart → 6 šikmých faces, hřeben, manifold 0).
- G1: plochá střecha s nástavbou (DSM důkaz). G2: slepený dvojdomek, obě poloviny ploché (fit rmse 0.148/0.083 m). B06: vysoký blok. Jejich placaté modely jsou správně.
- STANDARD vs DETAIL flowchart vybírá `run_cityjson.py` podle profilu v meta.json.
- CityJSON z geof má lokální vertexy bez transform → `cityjson_globalize.py` (RANSAC, G3 16/16) doplní standardní transform; pak je soubor skutečně S-JTSK.

## See Also

- [Skutečný Geoflow běh](skutecny-beh.md)
- [Sedlovky ze scanu](../pipeline/sedlovky.md)
