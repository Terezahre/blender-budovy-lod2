# -*- coding: utf-8 -*-
"""3D srovnani lod22 vs boolean-fixed + bias jednotlivych vikýřů."""
import json

import laspy
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from shapely import wkt
from shapely.geometry import Point

FID = "ID-1465-38F62225-F3F5-F520-E053-CA2BA8C0BE14"


def load_obj(p):
    V, F = [], []
    for line in open(p, encoding="utf-8"):
        if line.startswith("v "):
            V.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("f "):
            F.append([int(x.split("/")[0]) - 1 for x in line.split()[1:]])
    return np.array(V, dtype=float), F


las = laspy.read(f"buildings_pl/{FID}/body.las")
x, y, z = np.asarray(las.x), np.asarray(las.y), np.asarray(las.z)
c = np.asarray(las.classification)
poly = wkt.loads(json.load(open("data_pl/warszawa_gt.json", encoding="utf-8"))[FID]["footprint_wkt"])
inside = np.array([poly.contains(Point(px, py)) for px, py in zip(x, y)])
gmed = np.median(z[(~inside) & (c == 2)])
roof = np.column_stack([x[inside & (c == 6)], y[inside & (c == 6)], z[inside & (c == 6)]])
roof = roof[roof[:, 2] > gmed + 1.5]
cx, cy = poly.centroid.x, poly.centroid.y

fig = plt.figure(figsize=(15, 6))
for i, tag in enumerate(("model_lod22", "model_bool")):
    V, F = load_obj(f"output/pl_geof/{FID}/{tag}.obj")
    Vc = V - np.array([cx, cy, 0])
    tris = []
    for f in F:
        P = Vc[np.array(f)]
        for j in range(1, len(P) - 1):
            tris.append(P[[0, j, j + 1]])
    a = fig.add_subplot(1, 2, i + 1, projection="3d")
    a.add_collection3d(Poly3DCollection(
        tris, facecolor="steelblue" if i == 0 else "firebrick",
        edgecolor="k", linewidths=0.05, alpha=0.95))
    a.set_title("Geoflow LOD22 (jehly)" if i == 0 else "Boolean-fixed (sjednocene vikýře)")
    a.set_box_aspect((1, 1, 0.5))
    a.view_init(elev=25, azim=-60)
    a.set_xlim(-40, 40)
    a.set_ylim(-40, 40)
    a.set_xlabel("x [m]")
    a.set_ylabel("y [m]")
    a.set_zlabel("z [m]")
plt.suptitle("Varšava %s: puvodni vs opravene (EPSG:2180, centrovano)" % FID)
plt.tight_layout()
plt.savefig("render/pl_bool_compare.png", dpi=110)
print("ulozeno render/pl_bool_compare.png")

# bias prismatu vuci bodum uvnitr
from matplotlib.path import Path as MplPath
fixed = json.load(open("data_pl/dormers_fixed.json", encoding="utf-8"))
V, F = load_obj(f"output/pl_geof/{FID}/model_bool.obj")


def mesh_z_at(VV, FF, xy):
    out = np.full(len(xy), np.nan)
    for f in FF:
        P = VV[np.array(f)]
        t = [(P[0], P[i], P[i + 1]) for i in range(1, len(P) - 1)] if len(P) > 3 else [tuple(P)]
        for A, B, C in t:
            v0, v1 = C - A, B - A
            den = (v1[:2] @ v1[:2]) * (v0[:2] @ v0[:2]) - (v1[:2] @ v0[:2]) ** 2
            if abs(den) < 1e-12:
                continue
            d = xy - A[:2]
            u = ((v1[:2] @ v1[:2]) * (d @ v0[:2]) - (v1[:2] @ v0[:2]) * (d @ v1[:2])) / den
            v = ((v0[:2] @ v0[:2]) * (d @ v1[:2]) - (v1[:2] @ v0[:2]) * (d @ v0[:2])) / den
            hit = (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9)
            if hit.any():
                zz = A[2] + u * v0[2] + v * v1[2]
                m = hit & (np.isnan(out) | (zz > out))
                out[m] = zz[m]
    return out


for d in fixed:
    m = MplPath(np.array(d["rect"])).contains_points(roof[:, :2])
    Q = roof[m]
    a, b, c0 = d["top_plane"]
    pred = a * Q[:, 0] + b * Q[:, 1] + c0
    print("vikýř (%.1f,%.1f) svah %d: bodu=%d bias prismatu %+.2f m rmse %.2f" % (
        d["cx"], d["cy"], d["slope"], m.sum(),
        float((pred - Q[:, 2]).mean()), float(np.sqrt(((pred - Q[:, 2]) ** 2).mean()))))
