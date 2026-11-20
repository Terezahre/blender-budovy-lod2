# PolyFit fallback (kdy a proč selhává)

> Sources: Liangliang Nan (PolyFit); vlastní měření, 2026-11-20
> Raw: [format](../../raw/polyfit/2026-11-20-polyfit-format-a-vahy.md)
> Updated: 2026-11-20

## Overview

PolyFit nastupuje, když je budova moc složitá (kritéria agents.md: > 8 rovin, pokrytí < 0.5, RMSE > 0.5 m, přeskočení rekonstrukce). Na pilotních datech ale SCIP vrací prázdnou množinu — řídká data (~2 pts/m2) nemají dost protínajících se rovin s bodovou podporou.

## Stav

- Pipeline je hotový a ověřený na toy_data.bvg: 14 grup → 490 kandidátů → 42 faces (váhy 0.43/0.27/0.3).
- .vg writer: RANSAC roviny včetně stěnových + podlaha z terénu, lokální souřadnice (stabilita solveru), návrat offsetu do S-JTSK.
- B03 (5 grup → 7 kandidátů → 0) a B05 (6 grup → 22 kandidátů → 0) selhávají i při fitting vahách do 0.8 — nevyrábět si k tomu iluze, kandidátní stěny bez podpory optimalizér vždy škrtne.
- Praktický důsledek: B03 drží REVIEW na LOD2 cestě (RMSE 0.592 m, geometrie čistá), B05 je FAIL z obou cest (slitý klastr).

## See Also

- [Per-building profily](../geoflow/profily-parametru.md)
- [Pilotní výsledky](../pipeline/vysledky-pilot.md)
