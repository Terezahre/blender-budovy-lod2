# -*- coding: utf-8 -*-
"""Render varšavské budovy: husté mračno vs LoD2 GT (lidská kontrola párování)."""
import json

import laspy
import numpy as np
from shapely import wkt

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

GMLID = "{http://www.opengis.net/gml}id"
TX = (637036.0, 487847.0, 637585.0, 488441.0)


def inside(v):
    p = wkt.loads(v["footprint_wkt"])
    b = p.bounds
    return b[0] > TX[0] + 10 and b[1] > TX[1] + 10 and b[2] < TX[2] - 10 and b[3] < TX[3] - 10


def main():
    import xml.etree.ElementTree as ET
    gt = json.load(open("data_pl/warszawa_gt.json", encoding="utf-8"))
    cands = [(k, v) for k, v in gt.items() if inside(v)]
    cands.sort(key=lambda kv: wkt.loads(kv[1]["footprint_wkt"]).area, reverse=True)
    pick = next((k for k, v in cands if v["roofType"] == 1030), None)
    pick = pick or next((k for k, v in cands if v["roofType"] == 1130), cands[0][0])
    print("budova:", pick, gt[pick]["roofType"])
    poly = wkt.loads(gt[pick]["footprint_wkt"])
    l = laspy.read("data_pl/warszawa_12ppsm.laz")
    x, y, z = np.asarray(l.x), np.asarray(l.y), np.asarray(l.z)
    c = np.asarray(l.classification)
    m = ((c == 6) & (x >= poly.bounds[0] - 5) & (x <= poly.bounds[2] + 5)
         & (y >= poly.bounds[1] - 5) & (y <= poly.bounds[3] + 5))
    print("bodu tridy 6 v okne:", m.sum())
    xp, yp, zp = x[m], y[m], z[m]
    cx, cy = poly.centroid.x, poly.centroid.y
    tris = []
    for _ev, b in ET.iterparse("data_pl/Modele_3D/1465_N-34-139-A-c-1-1.gml", events=("end",)):
        if b.tag.endswith("}Building") and b.attrib.get(GMLID) == pick:
            for d in b.iter():
                t = d.tag.split("}")[1] if "}" in d.tag else d.tag
                if t == "Polygon":
                    P = []
                    for p in d.iter():
                        tt = p.tag.split("}")[1] if "}" in p.tag else p.tag
                        if tt == "pos":
                            P.append([float(v) for v in p.text.split()])
                    P = np.array(P)
                    for i in range(1, len(P) - 1):
                        tris.append(P[[0, i, i + 1]] - np.array([cx, cy, 0]))
            b.clear()
            break
        elif b.tag.endswith("}Building"):
            b.clear()
    print("GT trojuhelniku:", len(tris))
    fig = plt.figure(figsize=(14, 6))
    a1 = fig.add_subplot(121, projection="3d")
    a1.scatter(xp - cx, yp - cy, zp, s=0.4, c=zp, cmap="viridis")
    a1.set_title("Varsava LAZ 12 pts/m2, trida 6 (%d bodu)" % m.sum(), fontsize=11)
    a1.set_box_aspect((1, 1, 0.5))
    a1.view_init(elev=25, azim=-60)
    a1.set_xlabel("x [m]")
    a1.set_ylabel("y [m]")
    a1.set_zlabel("z [m]")
    a2 = fig.add_subplot(122, projection="3d")
    a2.add_collection3d(Poly3DCollection(
        tris, facecolor="firebrick", edgecolor="k", linewidths=0.1, alpha=0.9))
    a2.set_title("Polsko LoD2 GT (GUGiK, typ %s)" % gt[pick]["roofType"], fontsize=11)
    a2.set_box_aspect((1, 1, 0.5))
    a2.view_init(elev=25, azim=-60)
    a2.set_xlabel("x [m]")
    a2.set_ylabel("y [m]")
    a2.set_zlabel("z [m]")
    for a in (a1, a2):
        a.set_xlim(-40, 40)
        a.set_ylim(-40, 40)
    plt.suptitle("Varsava %s (EPSG:2180, centrovano)" % pick, fontsize=12)
    plt.tight_layout()
    plt.savefig("render/warszawa_compare.png", dpi=110)
    print("ulozeno render/warszawa_compare.png")


if __name__ == "__main__":
    main()
