# -*- coding: utf-8 -*-
"""GT svahy z GML (GUGiK LoD2) pro FID -> data_pl/gt_slopes.json.
Presne navrzene roviny hlavni strechy (bez vikýřů) jako prior pro rebuild.
GML je velke (50 MB) a zije mimo git; vystup je tiny JSON.
"""
import json
import xml.etree.ElementTree as ET

import numpy as np

FID = "ID-1465-38F62225-F3F5-F520-E053-CA2BA8C0BE14"
GML = r"C:\Users\Tereza\.t3\worktrees\Blender_projekt\t3-f6940c75-0f8474738a846f6b\data_pl\Modele_3D\1465_N-34-139-A-c-1-1.gml"
GMLID = "{http://www.opengis.net/gml}id"
OUT = "data_pl/gt_slopes.json"


def tag(e):
    t = e.tag
    return t.split("}")[1] if isinstance(t, str) and "}" in t else t


def main():
    slopes = []
    for _ev, b in ET.iterparse(GML, events=("end",)):
        if tag(b) != "Building":
            continue
        if b.attrib.get(GMLID) != FID:
            b.clear()
            continue
        for d in b.iter():
            if tag(d) != "Polygon":
                continue
            for ring in d.iter():
                if tag(ring) != "LinearRing":
                    continue
                P = []
                for p in ring:
                    if tag(p) == "pos" and p.text:
                        try:
                            P.append([float(v) for v in p.text.split()])
                        except ValueError:
                            pass
                if len(P) < 4:
                    continue
                P = np.array(P)
                n = np.cross(P[1] - P[0], P[2] - P[0])
                a = np.linalg.norm(n)
                if a > 1e-9 and (n / a)[2] > 0.5:
                    A = np.column_stack([P[:, 0], P[:, 1], np.ones(len(P))])
                    coef, *_ = np.linalg.lstsq(A, P[:, 2], rcond=None)
                    rmse = float(np.sqrt(np.mean((A @ coef - P[:, 2]) ** 2)))
                    slopes.append((coef, rmse, len(P)))
        b.clear()
        break
    slopes.sort(key=lambda s: -s[2])
    print("GT svahu (nz>0.5):", len(slopes))
    for coef, rmse, n in slopes:
        print("  rmse=%.3f bodu=%d coef=%s" % (rmse, n, np.round(coef, 4)))
    # 2 nejvetsi = hlavni svahy
    main2 = sorted(slopes, key=lambda s: -s[2])[:2]
    json.dump([dict(a=float(c[0]), b=float(c[1]), c0=float(c[2]), rmse=r, npts=n)
               for c, r, n in main2],
              open(OUT, "w", encoding="utf-8"), indent=1)
    print("->", OUT)


if __name__ == "__main__":
    main()
