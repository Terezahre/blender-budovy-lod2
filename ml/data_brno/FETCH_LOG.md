# Brno pilot – rucni kroky (studentske PC, stahuj po 1 dlazdici)

BBOX S-JTSK: (-598500.0, -1161500.0, -596500.0, -1159500.0)
ZABAGED budov stazeno: 991

## 1) Brno LOD2 (GT, TopGis, ~107k objektu)
- https://data.brno.cz/maps/dc95041d63e44e129ba0d9258a1dddb4/about
- alternativne https://webmaps.kambrno.cz/3d-model
- stahni SHP v S-JTSK, rozbal do ml/data_brno/brno_lod2/

## 2) DMP 1G LAZ (vstup, S-JTSK, CC-BY 4.0)
- https://atom.cuzk.cz/ -> datova sada DMP1G-LAZ-SJTSK
- vyhledej dlazdice pro vyse uvedeny bbox, stahni 1-2 .laz do ml/data_brno/laz/
- letecke skenovani 2009-2013: pocitej s casovym mismatch oproti Brno LOD2 (2020+) -> zmenene budovy filtrovat pres coverage (viz plan)

## 3) RUIAN
- footprinty vyse (ZABAGED vrstva 99) slouzi jako RUIAN prior; parcelni ID doplnime v ml/make_patches.py
