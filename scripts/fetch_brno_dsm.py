# -*- coding: utf-8 -*-
"""Stazeni DSM (DMP 2025) + DTM (DMT 2019) pro Brno pilotni bbox pres OMI ImageServer.

Proc: DMP 1G LAZ 2009-13 pro Brno by se muselo hledat po SM5 listech v ATOM feedu;
mesto Brno publikuje novejsi DSM/DTM primo jako ImageServer (exportImage, CC BY).
Casovy mismatch vuci LOD2 (2020-23) je mensi nez u DMP 1G. Rozliseni: 0.5 m.
Vystup: ml/data_brno/dsm/{dsm,dmt}_{tile}.tif (4 dlazdice 1x1 km, Float32) + manifest.

Pozdeji: ml/make_patches_brno.py z nich vyrobi nDSM patche (nDSM = DSM - DTM).
Beh: python scripts/fetch_brno_dsm.py  (par minut, ~100-200 MB)
"""
import os
import urllib.parse
import urllib.request

BBOX = (-598500.0, -1161500.0, -596500.0, -1159500.0)  # x0, y0, x1, y1 (S-JTSK)
CELL = 0.5
LAYERS = {
    "dsm": "https://gis.brno.cz/ags1/rest/services/OMI/OMI_DMP__2025_elevation_sjtsk/ImageServer/exportImage",
    "dmt": "https://gis.brno.cz/ags1/rest/services/OMI/OMI_DMT_2019_elevation/ImageServer/exportImage",
}
OUTDIR = os.path.join("ml", "data_brno", "dsm")


def fetch_tile(base, x0, y0, x1, y1, size, out):
    params = {
        "bbox": f"{x0},{y0},{x1},{y1}", "bboxSR": "5514", "imageSR": "5514",
        "size": f"{size},{size}", "format": "tiff", "pixelType": "F32", "f": "image",
    }
    url = base + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=600) as r:
        raw = r.read()
    assert raw[:4] == b"II*\x00", f"neni TIFF: {raw[:20]}"
    with open(out, "wb") as f:
        f.write(raw)
    print(f"  {out}: {len(raw)/1e6:.1f} MB")


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    x0, y0, x1, y1 = BBOX
    xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
    tiles = {"NW": (x0, ym, xm, y1), "NE": (xm, ym, x1, y1),
             "SW": (x0, y0, xm, ym), "SE": (xm, y0, x1, ym)}
    size = int((x1 - x0) / 2 / CELL)  # 2000
    for name, (ax0, ay0, ax1, ay1) in tiles.items():
        for kind, base in LAYERS.items():
            out = os.path.join(OUTDIR, f"{kind}_{name}.tif")
            if os.path.exists(out) and os.path.getsize(out) > 1e6:
                print(f"  {out}: preskakuji (stazeno)")
                continue
            print(f"{kind} {name} {ax0},{ay0},{ax1},{ay1} px={size}")
            fetch_tile(base, ax0, ay0, ax1, ay1, size, out)
    print(f"-> {OUTDIR}/ (8x TIFF 2000x2000 F32); nDSM = dsm - dmt")


if __name__ == "__main__":
    main()
