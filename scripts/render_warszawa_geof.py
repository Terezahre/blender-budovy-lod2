# -*- coding: utf-8 -*-
"""Varsava: nas Geoflow model vs polske LoD2 GT (stejna budova)."""
import numpy as np
from shapely import wkt
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

FID = "ID-1465-38F62225-F3F5-F520-E053-CA2BA8C0BE14"
GMLID = "{http://www.opengis.net/gml}id"


def load_obj(p):
    V, F = [], []
    for line in open(p, encoding="utf-8"):
        if line.startswith("v "):
            V.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("f "):
            F.append([int(x.split("/")[0]) - 1 for x in line.split()[1:]])
    return np.array(V), F


def main():
    import json
    import xml.etree.ElementTree as ET
    gt = json.load(open("data_pl/warszawa_gt.json", encoding="utf-8"))[FID]
    poly = wkt.loads(gt["footprint_wkt"])
    cx, cy = poly.centroid.x, poly.centroid.y
    V, F = load_obj(f"output/pl_geof/{FID}/model_lod22.obj")
    print("nas model: faces=%d z=%.1f-%.1f" % (len(F), V[:, 2].min(), V[:, 2].max()))
    ours = []
    for f in F:
        P = V[np.array(f)] - np.array([cx, cy, 0])
        for i in range(1, len(P) - 1):
            ours.append([P[0], P[i], P[i + 1]])
    tris = []
    for _ev, b in ET.iterparse("data_pl/Modele_3D/1465_N-34-139-A-c-1-1.gml", events=("end",)):
        if not b.tag.endswith("}Building"):
            continue
        if b.attrib.get(GMLID) != FID:
            b.clear()
            continue
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
    print("GT trojuhelniku:", len(tris))
    fig = plt.figure(figsize=(14, 6))
    a1 = fig.add_subplot(121, projection="3d")
    a1.add_collection3d(Poly3DCollection(
        ours, facecolor="steelblue", edgecolor="k", linewidths=0.15, alpha=0.9))
    a1.set_title("Nas Geoflow z LAZ 12 pts/m2 (RMSE 3.23 m)", fontsize=11)
    a1.set_box_aspect((1, 1, 0.6))
    a1.view_init(elev=25, azim=-60)
    a2 = fig.add_subplot(122, projection="3d")
    a2.add_collection3d(Poly3DCollection(
        tris, facecolor="firebrick", edgecolor="k", linewidths=0.1, alpha=0.9))
    a2.set_title("Polsko LoD2 GT (GUGiK, typ 1030)", fontsize=11)
    a2.set_box_aspect((1, 1, 0.6))
    a2.view_init(elev=25, azim=-60)
    for a in (a1, a2):
        a.set_xlabel("x [m]")
        a.set_ylabel("y [m]")
        a.set_zlabel("z [m]")
        a.set_xlim(-40, 40)
        a.set_ylim(-40, 40)
    plt.suptitle("Varsava (EPSG:2180, centrovano)", fontsize=12)
    plt.tight_layout()
    plt.savefig("render/warszawa_geof_vs_gt.png", dpi=110)
    print("ulozeno render/warszawa_geof_vs_gt.png")


if __name__ == "__main__":
    main()
