# -*- coding: utf-8 -*-
"""Kolik rovin ma strecha? K-planes pro K=2,3,4 + histogram vyskovych pasu."""
import json

import laspy
import numpy as np
from shapely import wkt
from shapely.geometry import Point

FID = "ID-1465-38F62225-F3F5-F520-E053-CA2BA8C0BE14"
RNG = np.random.default_rng(7)
las = laspy.read(f"buildings_pl/{FID}/body.las")
x, y, z = np.asarray(las.x), np.asarray(las.y), np.asarray(las.z)
c = np.asarray(las.classification)
poly = wkt.loads(json.load(open("data_pl/warszawa_gt.json", encoding="utf-8"))[FID]["footprint_wkt"])
inside = np.array([poly.contains(Point(px, py)) for px, py in zip(x, y)])
gmed = np.median(z[(~inside) & (c == 2)])
roof = np.column_stack([x[inside & (c == 6)], y[inside & (c == 6)], z[inside & (c == 6)]])
roof = roof[roof[:, 2] > gmed + 1.5]
print("n roof:", len(roof), "zmin/max: %.2f/%.2f" % (roof[:, 2].min(), roof[:, 2].max()))
m = roof[:, :2].mean(axis=0)
A = np.column_stack([roof[:, 0], roof[:, 1], np.ones(len(roof))])


def fit(Q):
    B = np.column_stack([Q[:, 0] - m[0], Q[:, 1] - m[1], np.ones(len(Q))])
    s, *_ = np.linalg.lstsq(B, Q[:, 2], rcond=None)
    return np.array([s[0], s[1], s[2] - s[0] * m[0] - s[1] * m[1]])


def ransac_init(P, thresh=0.25, iters=400):
    Q = P.copy()
    Q[:, 0] -= m[0]
    Q[:, 1] -= m[1]
    best, bn = None, -1
    for _ in range(iters):
        S = Q[RNG.choice(len(Q), 3, replace=False)]
        n = np.cross(S[1] - S[0], S[2] - S[0])
        if np.linalg.norm(n) < 1e-9:
            continue
        B = np.column_stack([S[:, 0], S[:, 1], np.ones(3)])
        co, *_ = np.linalg.lstsq(B, S[:, 2], rcond=None)
        inn = np.abs(np.column_stack([Q[:, 0], Q[:, 1], np.ones(len(Q))]) @ co - Q[:, 2]) < thresh
        if inn.sum() > bn:
            best, bn = co, inn.sum()
    a, b, c0 = best
    return np.array([a, b, c0 - a * m[0] - b * m[1]])


for K in (2, 3, 4):
    cs = [fit(roof)]
    for _ in range(1, K):
        rem = np.ones(len(roof), bool)
        R = np.stack([np.abs(A @ p - roof[:, 2]) for p in cs]).min(axis=0)
        cs.append(ransac_init(roof[R > 0.5 if (R > 0.5).sum() > 100 else slice(None)]))
    for _it in range(15):
        R = np.stack([np.abs(A @ p - roof[:, 2]) for p in cs])
        lab = R.argmin(axis=0)
        new = []
        for k in range(K):
            sel = (lab == k) & (R[k] < 0.5)
            new.append(fit(roof[sel]) if sel.sum() >= 50 else cs[k])
        cs = new
    R = np.stack([np.abs(A @ p - roof[:, 2]) for p in cs])
    best = R.min(axis=0)
    cov = (best < 0.25)
    det = " ".join("n%d=%d" % (k, int(((R.argmin(axis=0) == k) & (R[k] < 0.5)).sum())) for k in range(K))
    print("K=%d: pokryti<0.25m %.0f%% rmse_in=%.3f %s" % (
        K, cov.mean() * 100, float(np.sqrt((best[cov] ** 2).mean())), det))
