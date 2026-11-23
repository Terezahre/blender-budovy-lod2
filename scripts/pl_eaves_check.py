# -*- coding: utf-8 -*-
"""Kontrola vodorovnosti okapu ve finalnim modelu (povrch podel hran footprintu)."""
import json
import numpy as np
from shapely import wkt

FID = "ID-1465-38F62225-F3F5-F520-E053-CA2BA8C0BE14"
V, F = [], []
for line in open("output/pl_geof/%s/model_west15_bool.obj" % FID, encoding="utf-8"):
    if line.startswith("v "):
        V.append([float(x) for x in line.split()[1:4]])
    elif line.startswith("f "):
        F.append([int(x.split("/")[0]) - 1 for x in line.split()[1:]])
V = np.array(V)


def mesh_z_at(VV, FF, xy):
    out = np.full(len(xy), np.nan)
    for f in FF:
        P = VV[np.array(f)]
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
                zz = A[2] + u * v0[2] + v * v1[2]
                m = hit & (np.isnan(out) | (zz > out))
                out[m] = zz[m]
    return out


poly = wkt.loads(json.load(open("data_pl/warszawa_gt.json", encoding="utf-8"))[FID]["footprint_wkt"])
xs, ys = poly.exterior.coords.xy
ring = np.stack([xs, ys], 1)
tot = 0.0
n = 0
for i in range(len(ring) - 1):
    a, b = ring[i], ring[i + 1]
    L = float(np.linalg.norm(b - a))
    if L < 1.0:
        continue
    k = max(int(L / 0.5), 1)
    pts = np.stack([np.linspace(a[0], b[0], k), np.linspace(a[1], b[1], k)], 1)
    mz = mesh_z_at(V, F, pts)
    ok = ~np.isnan(mz)
    if ok.any():
        print("hrana %d: delka %.1f m, z_med=%.2f zmin=%.2f zmax=%.2f (bodu %d)" % (
            i, L, float(np.median(mz[ok])), float(mz[ok].min()), float(mz[ok].max()), int(ok.sum())))
        tot += abs(float(np.median(mz[ok])) - 125.38)
        n += 1
print("prumerna odchylka hran od 125.38: %.3f m" % (tot / max(n, 1)))
