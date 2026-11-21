# -*- coding: utf-8 -*-
"""Varšava: LoD2 GT z GML + filtr na LAZ dlazdici.
Vstup: data_pl/Modele_3D/1465_N-34-139-A-c-1-1.gml (CityGML 2.0 LoD2, GUGiK, CC BY 4.0)
       data_pl/warszawa_12ppsm.laz (12 pts/m2, 2025)
Vystup: data_pl/warszawa_gt.json {id: {roofType, bbox, zmin, zmax, footprint_wkt}}
  jen budovy protinajici LAZ dlazdici (souradnice primo EPSG:2180, zadna transformace).
Beh: python scripts/pair_warszawa.py (minuty, iterparse, setrne k RAM)
"""
import json
import os
import xml.etree.ElementTree as ET

GML = "data_pl/Modele_3D/1465_N-34-139-A-c-1-1.gml"
LAZ = "data_pl/warszawa_12ppsm.laz"
OUT = "data_pl/warszawa_gt.json"

# bbox dlazdice z WFS skorowidze (poradi os jako v LAZ: X, Y)
TILE = (637036.0, 487847.0, 637585.0, 488441.0)


def tag(el):
    return el.tag.split("}")[1] if "}" in el.tag else el.tag


def main():
    import laspy
    import numpy as np
    las = laspy.read(LAZ)
    print(f"LAZ: {len(las)} bodu, trida 6: {int((np.asarray(las.classification) == 6).sum())}")
    x0, y0, x1, y1 = TILE
    gt = {}
    n_tot = 0
    GMLID = "{http://www.opengis.net/gml}id"
    for _ev, b in ET.iterparse(GML, events=("end",)):
        if not tag(b) == "Building":
            continue
        n_tot += 1
        bid = b.attrib.get(GMLID, b.attrib.get("id", f"n{n_tot}"))
        roof = None
        pts = []
        for d in b.iter():
            t = tag(d)
            if t == "roofType" and (d.text or "").strip().isdigit():
                roof = int(d.text)
            elif t == "pos" and d.text:
                try:
                    pts.append([float(x) for x in d.text.split()])
                except ValueError:
                    pass
        if not pts:
            b.clear()
            continue
        P = np.array(pts)
        bx0, by0, bz0 = P.min(axis=0)
        bx1, by1, bz1 = P.max(axis=0)
        # prunik s dlazdici (s bufrem 5 m)
        if bx1 < x0 - 5 or bx0 > x1 + 5 or by1 < y0 - 5 or by0 > y1 + 5:
            b.clear()
            continue
        # footprint = hull bodu pri zemi (do +1 m nad minimem)
        from shapely.geometry import MultiPoint
        low = P[P[:, 2] < bz0 + 1.0][:, :2]
        fp = MultiPoint(low).convex_hull if len(low) >= 3 else MultiPoint(P[:, :2]).convex_hull
        gt[bid] = dict(roofType=roof, zmin=round(float(bz0), 2), zmax=round(float(bz1), 2),
                        footprint_wkt=fp.wkt)
        b.clear()
    json.dump(gt, open(OUT, "w", encoding="utf-8"), indent=1)
    roofs = {}
    for v in gt.values():
        roofs[v["roofType"]] = roofs.get(v["roofType"], 0) + 1
    print(f"budov v GML: {n_tot}, v dlazdici: {len(gt)}, typy strech: {roofs}")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
