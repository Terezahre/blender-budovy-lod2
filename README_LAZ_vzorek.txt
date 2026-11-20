Vzorek LAS/LAZ dat budov – ČÚZK DMP 1G
=====================================

Soubor:
- KRAV59.zip (originální ZIP z ČÚZK, 5,4 MB)
- KRAV59_DMP1G/KRAV59.laz (rozbaleno, 1 669 893 bodů)

Zdroj:
- Český úřad zeměměřický a katastrální (ČÚZK)
- Datová sada: Digitální model povrchu ČR 1. generace (DMP 1G), formát LAZ, S-JTSK (EPSG:5514)
- Mapový list: Kralupy nad Vltavou 5-9 (KRAV59)
- Pokrytí WGS84: 50.1177–50.1386 N, 14.4506–14.4891 E → Praha-Kobylisy / Ďáblice / Březiněves
- ATOM feed: https://atom.cuzk.gov.cz/DMP1G-SJTSK/DMP1G-SJTSK.xml
- Přímý download: https://openzu.cuzk.gov.cz/opendata/DMP1G/epsg-5514/KRAV59.zip
- Licence: CC BY 4.0 – bezplatné, uveďte zdroj „ČÚZK“
  https://geoportal.cuzk.gov.cz/Dokumenty/Podminky.pdf

Ověřeno (laspy 2.7.0):
- points: 1669893
- S-JTSK mins: [-740000, -1040000, 203.62] maxs: [-737500, -1038000, 396.87]
- klasifikace ASPRS: 2 = ground (298803), 5 = high vegetation (431779), 6 = building (939311)
- Vhodné pro test budov v Blenderu (třída 6).

Načtení v Blenderu:
- Blender nativně LAZ neumí. Použij např. CloudCompare / LAStools / PDAL pro konverzi/ořez,
  nebo Python (laspy + numpy) pro export XYZ/PLY.
- Příklad: python -m pip install laspy lazrs numpy
           python scripts/read_laz.py

Další volně dostupná LAS/LAZ data s budovami:
1. ČÚZK – celá ČR, DMP 1G (povrch vč. budov) + DMR 5G (jen terén)
   https://ags.cuzk.gov.cz/opendata
   https://atom.cuzk.gov.cz/
2. USGS 3DEP – celé USA, klasifikované (budovy = class 6), LAZ 1.4, AWS Open Data
   https://registry.opendata.aws/usgs-lidar/
   https://apps.nationalmap.gov/lidar-explorer/
3. OpenTopography – globální komunitní + USGS/NOAA mirror, LAS/LAZ zdarma po registraci
   https://portal.opentopography.org/dataCatalog
4. Nizozemsko AHN4 – celé Nizozemsko, velmi husté, CC0
   https://www.ahn.nl/
5. Helsinki 3D / HSY – město Helsinki, LAS + CityGML budov, CC BY 4.0
   https://hri.fi/en/
6. VZOROVÉ malé soubory pro testy (LAStools, libLAS):
   https://laszip.org/ , https://github.com/LAStools/LAStools/tree/master/data
