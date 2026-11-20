# -*- coding: utf-8 -*-
"""Porovnani skutecneho Geoflow LOD22 vs body.las: RMSE, pokryti, manifold.
Vystup: output/geof/<ID>/compare.json
"""
import json
import numpy as np
import laspy
from collections import Counter

IDS = ["B01_flat", "B02_gable", "B03_row", "B04_panelak", "B05_vez"]


def load_obj(path):
    V, F = [], []
    for line in open(path, encoding="utf-8"):
        if line.startswith("v "):
            V.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("f "):
            F.append([int(x.split("/")[0]) - 1 for x in line.split()[1:]])
    return np.array(V), F


def mesh_z_at(V, F, xy):
    """Vertikalni prusecik paprsku s mesh (nejvyssi trojuhelnik nad bodem)."""
    out = np.full(len(xy), np.nan)
    for f in F:
        P = V[f]
        # triangulace fan pro ngony
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
                z = A[2] + u * (v0[2]) + v * (v1[2])
                m = hit & (np.isnan(out) | (z > out))
                out[m] = z[m]
    return out


for bid in IDS:
    V, F = load_obj(f"output/geof/{bid}/model_lod22.obj")
    las = laspy.read(f"buildings/{bid}/body.las")
    pts = np.vstack([las.x, las.y, las.z]).T
    cls = np.array(las.classification)
    meta = json.load(open(f"buildings/{bid}/meta.json", encoding="utf-8"))
    roof = pts[(cls == 6) & (pts[:, 2] > meta["ground_z_p5"] + 1.5)]
    mz = mesh_z_at(V, F, roof[:, :2])
    covered = ~np.isnan(mz)
    rmse = float(np.sqrt(((roof[covered, 2] - mz[covered]) ** 2).mean())) if covered.any() else -1.0
    # manifold audit (fan-triangulace ngonu)
    ec = Counter()
    for f in F:
        tris = [[f[0], f[i], f[i + 1]] for i in range(1, len(f) - 1)] if len(f) > 3 else [f]
        for t in tris:
            for e in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                ec[tuple(sorted(e))] += 1
    nm = sum(1 for c in ec.values() if c != 2)
    rep = json.load(open(f"output/geoflow/{bid}/report.json", encoding="utf-8"))
    out = dict(id=bid, geof_verts=int(len(V)), geof_faces=len(F),
               geof_rmse=round(rmse, 3),
               geof_coverage=round(float(covered.mean()), 3),
               geof_nonmanifold=int(nm),
               ours_rmse=round(rep["rmse_roof"], 3),
               ours_verts=rep["validation"]["n_verts"],
               ours_faces=rep["validation"]["n_faces"])
    json.dump(out, open(f"output/geof/{bid}/compare.json", "w", encoding="utf-8"),
              indent=1)
    print(f"[{bid}] geof rmse={rmse:.3f}m pokryti={covered.mean():.2f} "
          f"nm={nm} | nase rmse={rep['rmse_roof']:.3f}m")
