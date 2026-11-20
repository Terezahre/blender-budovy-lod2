# Skutečný Geoflow běh a srovnání

> Sources: 3DGI/geoflow-bundle 0.3.6; vlastní měření, 2026-11-21
> Raw: [geof-run](../../raw/geoflow/2026-11-21-geof-run.md)
> Updated: 2026-11-21

## Overview

Po instalaci Geoflow 0.3.6 proběhlo všech 5 budov skutečným `geof` s per-building `r_*` parametry; všechny modely jsou manifold a v S-JTSK. Vlastní cesta má na 3 budovách nižší RMSE (méně generalizuje), na paneláku je shoda.

## Provozní zjištění

- Bez `GF_PLUGIN_FOLDER` se pluginy nenačtou (tichý pád); chyby ukáže až `-V`. Bez admin práv pomůže lokální kopie runtime mimo Program Files.
- Bundlovaný flowchart nesedí s pluginem v CityJSONWriter (`meta_poc_address`) — používá se ořezaná kopie jen s OBJ výstupy (47 uzlů), matematika stejná.
- Per-building TOML v `buildings/*/geof.toml` (mapování profilů na `r_*`); select SQL se přepisuje na prázdný (1 budova na GPKG).

## Srovnání (geof vs vlastní RMSE)

B01: 0.164 vs 0.056 m; B02: 0.460 vs 0.219 m; B03: 1.588 vs 0.592 m; B04: 0.042 vs 0.043 m; B05: 8.570 vs 6.383 m (obě cesty FAIL — slitý klastr). Pokrytí geof 0.95–0.99, non-manifold 0 všude. Závěr: vlastní stupňovité kvádry sedí na řídkých datech těsněji, Geoflow víc generalizuje (arrangement + graph-cut); topologicky jsou obě cesty čisté.

## See Also

- [Per-building profily](profily-parametru.md)
- [Pilotní výsledky](../pipeline/vysledky-pilot.md)
