# Data KRAV59 (ČÚZK DMP 1G)

> Sources: ČÚZK, 2026-11-20
> Raw: [krav59](../../raw/laz-dmp1g/2026-11-20-krav59-dmp1g.md)
> Updated: 2026-11-20

## Overview

Vstupem projektu je letecké mračno ČÚZK DMP 1G, mapový list KRAV59 (Praha-Kobylisy / Ďáblice / Březiněves): 1 669 893 bodů v S-JTSK (EPSG:5514), z toho 939 311 bodů budov (class 6).

## Vlastnosti

- Hustota na střechách je jen 1.43–1.75 bodů/m2 — zhruba 5× méně než nizozemská data (8–10 pts/m2), pro která je Geoflow laděn. Proto se používají vyšší `min_points` a mírnější prahy (profily v agents.md).
- Terén v dlaždici kolísá kolem 289 m (std 18.85 m), takže absolutní Z nic neříká — výška budovy se vždy počítá vůči lokálnímu terénu (percentil p5 class 2 v bufferu 5 m).
- Klasifikace je slušná, ale ojediněle se najdou chyby (vegetace v class 6) — řeší kNN outlier filtr v rekonstrukci.

## See Also

- [Klastrování budov](klastrovani.md)
- [Pilotní výsledky](../pipeline/vysledky-pilot.md)
