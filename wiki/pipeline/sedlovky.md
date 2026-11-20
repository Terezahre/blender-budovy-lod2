# Sedlové domy z celomapového scanu + Geoflow-only rozhodnutí

> Sources: vlastní měření, 2026-11-21
> Raw: [scan](../../raw/pipeline/2026-11-21-scan-sedlovky.md)
> Updated: 2026-11-21

## Overview

Pilotní dlaždice obsahuje jen ploché střechy, proto proběhl scan celého KRAV59 (286 kandidátů → 24 pravých sedlovek → top 3). Finále je POUZE Geoflow LoD2.2; vlastní stupňovité kvádry jsou odstaveny do `output/ours/` jako překonaný prototyp.

## Budovy

- G1_sedlova (14×15 m, 280 bodů): Geoflow RMSE 1.669 m, 26v/48f, PASS — sedlo s hřebenem.
- G2_sedlova (21×21 m, 300 bodů): Geoflow RMSE 1.520 m, 20v/36f, PASS.
- G3_domek (9×10 m, 164 bodů): Geoflow RMSE 0.774 m, 20v/36f, PASS — nejčistší.
- B06_sedlova se škrtá: falešný pozitiv scanu (vysoký blok, rel 12.7 m), Geoflow RMSE 2.683 m, plochá střecha.

## Rozhodnutí Geoflow-only

Vlastní cesta dává na plochých střechách nižší RMSE, ale výstupem jsou bezvýrazné kvádry bez střešní struktury. Finální dodávka (`output/final/`, 7 budov) je proto výhradně Geoflow LoD2.2: B01, B02, B03, B04, G1, G2, G3. Prohlížeč `viewer_3d.html` už nemá přepínač cest.

## See Also

- [Pilotní výsledky](vysledky-pilot.md)
- [Skutečný Geoflow běh](../geoflow/skutecny-beh.md)
