# Brno pilot – zdroje dat (stav: vse automaticky stazeno)

BBOX S-JTSK: (-598500.0, -1161500.0, -596500.0, -1159500.0), 2x2 km Brno-stred
ZABAGED budov: 991 | GT budov: 947 | patchu: 957

## 1) Brno LOD2 (GT, TopGis, CC BY) – STAZENO
- Zdroj: data.brno.cz -> 3D model budov -> **PolygonZ_S_JTSK.zip (150 MB)**
- Prime URL (SharePoint guest, funguje pres urllib):
  `https://mmbonline.sharepoint.com/:u:/s/public/OMI/gis/EWJ7QNxc7mtEpaL9CiZbrs8BpxbiIvr3f582016oZKBQRw?e=8bTrMy&download=1`
- Obsah: **FileGDB** `PolygonZ_S_JTSK.gdb`, vrstva `pz_2020_2023_s_jtsk` (MultiPolygon Z, EPSG:5514)
- Schema (overeno): RUIAN_IBO, ID_SEG, ID_PLO, PATA_VYSKA, HREBEN_VYSKA, ABS_VYSKA,
  HORIZ_VYSKA, STRECHA_KOD (1=sedlova 2=mansardova 3=plocha 4=pultova 5=stanova 6=valbova 7=jina),
  PATA_SEG_VYSKA, ABS_SEG_VYSKA, PLOCHA_KOD, CAST_OBJEKTU, ROK_POROZENI
- Granularita = SEGMENTY strech (172k v bboxu); agregace na budovu v ml/pair_brno.py
- Cteni: `pyogrio.read_dataframe(gdb, layer=..., bbox=...)` (fiona neni treba)
- Slepé ulicky: SceneServer query vraci prazdne (GET i POST); OMI_budovy_pudorys = interiery

## 2) Vstupni vysky (misto DMP 1G LAZ) – STAZENO
- OMI ImageServer (CC BY): DMP 2025 + DMT 2019, exportImage, 0.5 m, 8x TIFF 2000x2000
- Skript: `python scripts/fetch_brno_dsm.py` -> ml/data_brno/dsm/ (~134 MB, gitignored)
- DMP 1G LAZ pres ATOM neni treba (DMP 2025 je novsi, mensi mismatch vuci LOD2 2020-23)

## 3) RUIAN prior
- ZABAGED vrstva 99 (991 polygonu, `footprints.geojson`); RUIAN_IBO v nich neni,
  join na LOD2 se dela prostorove (centroid segmentu v polygonu)

## Pipeline
1. `python scripts/fetch_brno.py` – footprinty
2. `python scripts/fetch_brno_dsm.py` – DSM/DTM
3. `python ml/make_patches.py --src buildings` – KRAV59 patche
4. `python ml/make_patches_brno.py` – Brno patche (vyzaduje DSM + tifffile)
5. `python ml/pair_brno.py --mode krav59|brno` – GT
6. `python ml/train_raster.py --labels ml/gt_brno.json --patches ml/patches_brno`
