# -*- coding: utf-8 -*-
"""Krok 8: detailni 3D srovnani pasu vikýru (matplotlib, nizky pohled od JZ)."""
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


poly = wkt.loads(json.load(open("data_pl/warszawa_gt.json", encoding="utf-8"))[FID]["footprint_wkt"])
cx, cy = poly.centroid.x, poly.centroid.y
fig = plt.figure(figsize=(16, 7))
models = [("model_lod22.obj", "pred: Geoflow (jehly + vlny)", "steelblue"),
          ("model_west15_bool.obj", "po: 15 hranolu (boolean)", "firebrick")]
for i, item in enumerate(models):
    fn, ttl, col = item
    V, F = load_obj("output/pl_geof/" + FID + "/" + fn)
    Vc = V - np.array([cx, cy, 0])
    tris = []
    for f in F:
        P = Vc[np.array(f)]
        for j in range(1, len(P) - 1):
            tris.append(P[[0, j, j + 1]])
    a = fig.add_subplot(1, 2, i + 1, projection="3d")
    a.add_collection3d(Poly3DCollection(
        tris, facecolor=col, edgecolor="k", linewidths=0.08, alpha=0.95))
    a.set_title(ttl)
    a.set_box_aspect((1.6, 1, 0.5))
    a.view_init(elev=12, azim=-125)
    a.set_xlim(-20, 20)
    a.set_ylim(-20, 14)
    a.set_zlim(108, 131)
    a.set_xlabel("x [m]")
    a.set_ylabel("y [m]")
    a.set_zlabel("z [m]")
plt.suptitle("Pas 15 vikýru, zapadni svah (EPSG:2180, centrovano)")
plt.tight_layout()
plt.savefig("render/pl_west15_band.png", dpi=110)
print("ulozeno render/pl_west15_band.png")
