# -*- coding: utf-8 -*-
"""Detailni vyrezy problemovych mist: dvojshluk a zacatek osmishluku s hornimi."""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from shapely import wkt

FID = "ID-1465-38F62225-F3F5-F520-E053-CA2BA8C0BE14"


def load_obj(p):
    V, F = [], []
    for line in open(p, encoding="utf-8"):
        if line.startswith("v "):
            V.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("f "):
            F.append([int(x.split("/")[0]) - 1 for x in line.split()[1:]])
    return np.array(V, dtype=float), F


info = json.load(open("data_pl/west15_clusters.json", encoding="utf-8"))
eave = np.array(info["eave"])
poly = wkt.loads(json.load(open("data_pl/warszawa_gt.json", encoding="utf-8"))[FID]["footprint_wkt"])
cc = np.array(poly.centroid.coords[0])
V0, F0 = load_obj(f"output/pl_geof/{FID}/model_lod22.obj")
V1, F1 = load_obj(f"output/pl_geof/{FID}/model_west15_bool.obj")
t0 = (V0 - np.array([cc[0], cc[1], 0])) @ np.append(eave, 0)
t1 = (V1 - np.array([cc[0], cc[1], 0])) @ np.append(eave, 0)


def panel(fig, pos, V, F, t, t_lo, t_hi, ttl, col):
    Vc = V - np.array([cc[0], cc[1], 0])
    tris = []
    for f in F:
        P = Vc[np.array(f)]
        if t[np.array(f)].mean() < t_lo or t[np.array(f)].mean() > t_hi:
            continue
        for j in range(1, len(P) - 1):
            tris.append(P[[0, j, j + 1]])
    a = fig.add_subplot(1, 2, pos, projection="3d")
    a.add_collection3d(Poly3DCollection(
        tris, facecolor=col, edgecolor="k", linewidths=0.15, alpha=0.95))
    a.set_title(ttl)
    a.set_box_aspect((1.2, 1, 0.6))
    a.view_init(elev=18, azim=-125)
    a.set_xlabel("x [m]")
    a.set_ylabel("y [m]")
    a.set_zlim(122, 130)


for tag, t_lo, t_hi in (("dvoj", -5, 3), ("osmi", 1, 10)):
    fig = plt.figure(figsize=(16, 7))
    panel(fig, 1, V0, F0, t0, t_lo, t_hi, "%s pred (LOD22)" % tag, "steelblue")
    panel(fig, 2, V1, F1, t1, t_lo, t_hi, "%s po (bool)" % tag, "firebrick")
    plt.suptitle("Vyrez t=%d..%d (EPSG:2180, centrovano)" % (t_lo, t_hi))
    plt.tight_layout()
    plt.savefig("render/pl_west15_%s.png" % tag, dpi=110)
    print("ulozeno render/pl_west15_%s.png" % tag)
