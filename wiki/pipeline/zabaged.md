# Katastrální footprinty (ZABAGED) místo blobů

> Sources: ČÚZK; vlastní měření, 2026-11-21
> Raw: [zabaged](../../raw/pipeline/2026-11-21-zabaged.md)
> Updated: 2026-11-21

## Overview

Hranatost modelů způsobovaly footprinty z lidarových clusterů. ZABAGED polygony (1495 budov KRAV59, S-JTSK) to řeší: Z3_domek s katastrálním footprintem má RMSE 0.104 m a nejostřejší geometrii projektu.

## Výsledek

- Z3_domek (285 m2, 428 bodů): 8v/12f, PASS → 8. finální budova.
- Z1/Z2 zamítnuty (pokrytí 0.56/0.66, nesoulad polygonu s mračnem).
- Pravidlo do budoucna: footprint vždy ZABAGED/RUIAN (je-li), lidarový obal jen jako fallback.
- OSM pro footprinty nepoužitelné (Overpass blokuje naši síť).

## See Also

- [Pilotní výsledky](vysledky-pilot.md)
- [Klastrování](../laz-dmp1g/klastrovani.md)
