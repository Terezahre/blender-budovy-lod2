# -*- coding: utf-8 -*-
"""Diagnostika residui fixed vs lod22 po pasech vysky (samostatne)."""
import json

import laspy
import numpy as np
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
    return np.array(V, dtype=float), [list(map(int, f)) for f in F]


def mesh_z_at(V, F, xy):
    out = np.full(len(xy), np.nan)
    for f in F:
        P = V[np.array(f)]
        tris = [(P[0], P[i], P[i + 1]) for i in range(1, len(P) - 1)] if len(P) > 3 else [tuple(P)]
        for A, B, C in tris:
            v0, v1 = C - A, B - A
            den = (v1[:2] @ v1[:2]) * (v0[:2] @ v0[:2]) - (v1[:2] @ v0[:2]) ** 2
            if abs(den) < 1e-12:
                continue
            d = xy - A[:2]
            u = ((v1[:2] @ v1[:2]) * (d @ v0[:2]) - (v1[:2] @ v0[:2]) * (d @ v1[:2])) / den
            v = ((v0[:2] @ v0[:2]) * (d @ v1[:2]) - (v1[:2] @ v0[:2]) * (d @ v0[:2])) / den
            hit = (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9)
            if hit.any():
                z = A[2] + u * v0[2] + v * v1[2]
                m = hit & (np.isnan(out) | (z > out))
                out[m] = z[m]
    return out


las = laspy.read(f"buildings_pl/{FID}/body.las")
x, y, z = np.asarray(las.x), np.asarray(las.y), np.asarray(las.z)
c = np.asarray(las.classification)
poly = wkt.loads(json.load(open("data_pl/warszawa_gt.json", encoding="utf-8"))[FID]["footprint_wkt"])
inside = np.array([poly.contains(Point(px, py)) for px, py in zip(x, y)])
gmed = np.median(z[(~inside) & (c == 2)])
roof = np.column_stack([x[inside & (c == 6)], y[inside & (c == 6)], z[inside & (c == 6)]])
roof = roof[roof[:, 2] > gmed + 1.5]
print("gmed=%.2f n roof=%d" % (gmed, len(roof)))
# cista mnozina: body do 1 m od GT navrzene strechy (fasady/nadvori pryc)
gt = json.load(open("data_pl/gt_slopes.json", encoding="utf-8"))
s1, s2 = gt
zgt = np.maximum(s1["a"] * roof[:, 0] + s1["b"] * roof[:, 1] + s1["c0"],
                 s2["a"] * roof[:, 0] + s2["b"] * roof[:, 1] + s2["c0"])
clean = np.abs(roof[:, 2] - zgt) < 1.0
print("cistych strechych bodu: %d/%d" % (clean.sum(), len(roof)))
SETS = {"vsechny-class6": np.ones(len(roof), bool), "ciste-strecha": clean}
for tag in ("model_lod22", "model_fixed", "model_bool"):
    V, F = load_obj(f"output/pl_geof/{FID}/{tag}.obj")
    mz = mesh_z_at(V, F, roof[:, :2])
    r = mz - roof[:, 2]
    print(f"== {tag} ==")
    for sn, m in SETS.items():
        mm = m & ~np.isnan(r)
        print(f"  {sn}: n={mm.sum()} RMSE={np.sqrt((r[mm]**2).mean()):.3f} m")
    for lo, hi in ((111, 118), (118, 123), (123, 127), (127, 132)):
        m = (roof[:, 2] >= lo) & (roof[:, 2] < hi) & ~np.isnan(r)
        if m.any():
            print(f"  z {lo}-{hi}: n={m.sum()} bias={r[m].mean():+.2f} rmse={np.sqrt((r[m]**2).mean()):.2f}")
