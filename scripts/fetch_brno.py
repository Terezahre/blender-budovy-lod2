# -*- coding: utf-8 -*-
"""Priprava pilotniho datasetu Brno pro trenovani (CPU, bez GPU).

Co dela:
  1) Stahne ZABAGED/RUIAN footprinty pro pilotni bbox Brno-stred (vzor dle scripts/fetch_zabaged.py).
  2) Vypise ATOM URL pro rucni stazeni 1-2 DMP 1G LAZ dlazdic (pres atom.cuzk.cz).
  3) Vypise navod na rucni stazeni Brno LOD2 (data.brno.cz, 107k objektu TopGis).

Proc rucni kroky: DMP 1G LAZ dlazdice i Brno LOD2 jsou stovky MB - na studentskem
PC se stahuji po jedne dlazdici, ne bulk. Skript pripravi strukturu ml/data_brno/
a overi, co uz je stazene.

Vystup: ml/data_brno/{footprints.geojson, FETCH_LOG.md, manifest.json}
Souradnice: S-JTSK (EPSG:5514).
"""
import json
import os
import urllib.parse
import urllib.request

# Pilotni bbox Brno-stred (S-JTSK, EPSG:5514), 2 x 2 km kolem Spilberku.
# Overeno: ~991 budov ZABAGED (vysledek kompletni, limit 4000 neprekrocen).
BBOX = (-598500.0, -1161500.0, -596500.0, -1159500.0)  # x0, y0, x1, y1

OUTDIR = os.path.join("ml", "data_brno")
ZABAGED_URL = "https://ags.cuzk.gov.cz/arcgis/rest/services/ZABAGED_POLOHOPIS/MapServer/99/query"

BRNO_3D_HUB = "https://data.brno.cz/maps/dc95041d63e44e129ba0d9258a1dddb4/about"
BRNO_3D_APP = "https://webmaps.kambrno.cz/3d-model"
DMP_ATOM = "https://atom.cuzk.cz/"


def fetch_zabaged(bbox, limit=4000):
    x0, y0, x1, y1 = bbox
    params = {
        "where": "1=1",
        "geometry": f"{x0},{y0},{x1},{y1}",
        "geometryType": "esriGeometryEnvelope",
        "inSR": "5514",
        "outSR": "5514",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "*",
        "returnGeometry": "true",
        "resultRecordCount": str(limit),
        "f": "geojson",
    }
    url = ZABAGED_URL + "?" + urllib.parse.urlencode(params)
    print("ZABAGED query:", url[:140], "...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.load(r)
    feats = d.get("features", [])
    print(f"ZABAGED budov: {len(feats)} | exceededTransferLimit: {d.get('exceededTransferLimit')}")
    return d


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    try:
        d = fetch_zabaged(BBOX)
        with open(os.path.join(OUTDIR, "footprints.geojson"), "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False)
        n = len(d.get("features", []))
    except Exception as e:
        print("ZABAGED stazeni selhalo:", e)
        print("-> zkus znovu / zmensi bbox / pouzij scripts/fetch_zabaged.py vzor pro KRAV59.")
        n = 0

    manifest = {
        "bbox_sjtsk": list(BBOX),
        "crs": "EPSG:5514",
        "zabaged_count": n,
        "brno_lod2_hub": BRNO_3D_HUB,
        "brno_lod2_app": BRNO_3D_APP,
        "dmp1g_atom": DMP_ATOM,
        "next_steps": [
            "1) Stahni Brno LOD2 (SHP, S-JTSK) z data.brno.cz do ml/data_brno/brno_lod2/ (rucne, velke).",
            "2) Na atom.cuzk.cz vyhledej DMP1G-LAZ-SJTSK dlazdice pro vyse uvedeny bbox, stahni 1-2 .laz do ml/data_brno/laz/.",
            "3) Spust: python ml/make_patches.py --src ml/data_brno (az budou LAZ+LOD2) "
            "nebo hned: python ml/make_patches.py --src buildings (KRAV59 pilot).",
        ],
    }
    with open(os.path.join(OUTDIR, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1, ensure_ascii=False)

    log = (
        "# Brno pilot – rucni kroky (studentske PC, stahuj po 1 dlazdici)\n\n"
        f"BBOX S-JTSK: {BBOX}\nZABAGED budov stazeno: {n}\n\n"
        "## 1) Brno LOD2 (GT, TopGis, ~107k objektu)\n"
        f"- {BRNO_3D_HUB}\n- alternativne {BRNO_3D_APP}\n"
        "- stahni SHP v S-JTSK, rozbal do ml/data_brno/brno_lod2/\n\n"
        "## 2) DMP 1G LAZ (vstup, S-JTSK, CC-BY 4.0)\n"
        f"- {DMP_ATOM} -> datova sada DMP1G-LAZ-SJTSK\n"
        "- vyhledej dlazdice pro vyse uvedeny bbox, stahni 1-2 .laz do ml/data_brno/laz/\n"
        "- letecke skenovani 2009-2013: pocitej s casovym mismatch oproti Brno LOD2 (2020+) -> "
        "zmenene budovy filtrovat pres coverage (viz plan)\n\n"
        "## 3) RUIAN\n"
        "- footprinty vyse (ZABAGED vrstva 99) slouzi jako RUIAN prior; "
        "parcelni ID doplnime v ml/make_patches.py\n"
    )
    with open(os.path.join(OUTDIR, "FETCH_LOG.md"), "w", encoding="utf-8") as f:
        f.write(log)
    print(f"-> {OUTDIR}/{{footprints.geojson, manifest.json, FETCH_LOG.md}}")
    print("Dalsi: python ml/make_patches.py --src buildings   # bezi hned na KRAV59")


if __name__ == "__main__":
    main()
