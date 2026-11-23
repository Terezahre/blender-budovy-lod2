# -*- coding: utf-8 -*-
"""Krok 1: K-planes strechy + shluky bodu nad zapadni rovinou (boule=vychylky).
Vystup: render/pl_west15_clusters.png (cislovane shluky na ortofotu) + data_pl/west15_clusters.json
"""
import json
import laspy
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw
from shapely import wkt
from shapely.geometry import Point

FID = "ID-1465-38F62225-F3F5-F520-E053-CA2BA8C0BE14"
RNG = np.random.default_rng(7)

las = laspy.read(f"buildings_pl/{FID}/body.las")
x, y, z = np.asarray(las.x), np.asarray(las.y), np.asarray(las.z)
c = np.asarray(las.classification)
poly = wkt.loads(json.load(open("data_pl/warszawa_gt.json", encoding="utf-8"))[FID]["footprint_wkt"])
inside = np.array([poly.contains(Point(px, py)) for px, py in zip(x, y)])
roof = np.column_stack([x[inside & (c == 6)], y[inside & (c == 6)], z[inside & (c == 6)]])
gmed = np.median(z[(~inside) & (c == 2)])
roof = roof[roof[:, 2] > gmed + 1.5]
print("roof pts: %d, teren: %.2f" % (len(roof), gmed))


def ransac_plane(P, thresh=0.25, iters=800):
    m = P[:, :2].mean(axis=0)
    Q = P.copy(); Q[:, 0] -= m[0]; Q[:, 1] -= m[1]
    best, best_in = None, np.zeros(len(P), bool)
    for _ in range(iters):
        s = RNG.choice(len(P), 3, replace=False)
        S = Q[s]
        n = np.cross(S[1] - S[0], S[2] - S[0])
        if np.linalg.norm(n) < 1e-9:
            continue
        A = np.column_stack([S[:, 0], S[:, 1], np.ones(3)])
        coef, *_ = np.linalg.lstsq(A, S[:, 2], rcond=None)
        r = np.abs(np.column_stack([Q[:, 0], Q[:, 1], np.ones(len(Q))]) @ coef - Q[:, 2])
        inn = r < thresh
        if inn.sum() > best_in.sum():
            best, best_in = coef, inn
    a, b, c0 = best
    return np.array([a, b, c0 - a * m[0] - b * m[1]]), best_in


c1, in1 = ransac_plane(roof)
c2, _ = ransac_plane(roof[~in1])
m = roof[:, :2].mean(axis=0)


def _fit(Q):
    B = np.column_stack([Q[:, 0] - m[0], Q[:, 1] - m[1], np.ones(len(Q))])
    s, *_ = np.linalg.lstsq(B, Q[:, 2], rcond=None)
    return np.array([s[0], s[1], s[2] - s[0] * m[0] - s[1] * m[1]])


for _it in range(10):
    A = np.column_stack([roof[:, 0], roof[:, 1], np.ones(len(roof))])
    r1 = np.abs(A @ c1 - roof[:, 2]); r2 = np.abs(A @ c2 - roof[:, 2])
    best = np.minimum(r1, r2)
    m1 = (r1 <= r2) & (best < 0.5); m2 = (r2 < r1) & (best < 0.5)
    if m1.sum() < 50 or m2.sum() < 50:
        break
    c1, c2 = _fit(roof[m1]), _fit(roof[m2])
planes = [c1, c2]
n1 = np.array([-c1[0], -c1[1], 1.0]); n1 /= np.linalg.norm(n1)
n2 = np.array([-c2[0], -c2[1], 1.0]); n2 /= np.linalg.norm(n2)
ridge = np.cross(n1, n2); ridge /= np.linalg.norm(ridge)
eave = ridge.copy(); eave[2] = 0.0; eave /= np.linalg.norm(eave)
if eave[0] * 0.7 + eave[1] * 0.7 < 0:  # orientace podel budovy (jv->sz je +)
    pass
eang = float(np.degrees(np.arctan2(eave[1], eave[0])))
print("eave: (%.3f, %.3f) %.1f deg" % (eave[0], eave[1], eang))
# zapadni svah = ten, jehoz horizontalni normalka mirir na zapad (-X)
for i, p in enumerate(planes):
    nh = np.array([-p[0], -p[1]]); nh /= np.linalg.norm(nh)
    print("rovina%d: normala_h=(%.3f, %.3f) inliers<0.25: %d" % (
        i, nh[0], nh[1], int((np.abs(np.column_stack([roof[:, 0], roof[:, 1], np.ones(len(roof))]) @ p - roof[:, 2]) < 0.25).sum())))
WEST = int(np.argmin([(-p[0]) / np.hypot(p[0], p[1]) for p in planes]))
print("WEST slope index:", WEST)
pw = planes[WEST]
A = np.column_stack([roof[:, 0], roof[:, 1], np.ones(len(roof))])
res = roof[:, 2] - A @ pw
# body zapadniho svahu: blizko roviny pw
onw = np.abs(res) < 0.6
print("bodu na zapadnim svahu (|res|<0.6): %d" % onw.sum())
# shluky nad rovinou: res > 0.35, DBSCAN-lite pres mrizku 0.5 m
hi = (res > 0.35) & onw
P = roof[hi][:, :2]
print("bodu nad rovinou (>0.35 m): %d" % len(P))
cell, owner = 0.5, {}
for i, (px, py) in enumerate(P):
    owner.setdefault((int(px / cell), int(py / cell)), []).append(i)
seen = np.zeros(len(P), bool)
clusters = []
for i in range(len(P)):
    if seen[i]:
        continue
    stack, grp = [i], []
    while stack:
        j = stack.pop()
        if seen[j]:
            continue
        seen[j] = True; grp.append(j)
        cx, cy = int(P[j, 0] / cell), int(P[j, 1] / cell)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for k in owner.get((cx + dx, cy + dy), []):
                    if not seen[k] and np.hypot(*(P[j] - P[k])) < 0.75:
                        stack.append(k)
    if len(grp) >= 6:
        clusters.append(grp)
print("shluku (>=6 bodu): %d" % len(clusters))
cl = []
for grp in clusters:
    Q = roof[hi][np.array(grp)]
    cl.append(dict(cx=round(float(Q[:, 0].mean()), 2), cy=round(float(Q[:, 1].mean()), 2),
                   n=len(grp), zmax=round(float(Q[:, 2].max()), 2),
                   zmed=round(float(np.median(Q[:, 2])), 2),
                   t=round(float((np.array([Q[:, 0].mean(), Q[:, 1].mean()]) - m[:2]) @ eave[:2]), 2)))
cl.sort(key=lambda d: -d["t"])
for i, d in enumerate(cl):
    print("%2d: E=%.2f N=%.2f n=%d zmax=%.2f zmed=%.2f t=%.1f" % (i, d["cx"], d["cy"], d["n"], d["zmax"], d["zmed"], d["t"]))
json.dump(dict(eave=[float(eave[0]), float(eave[1])], eang=eang, west=WEST,
               planes=[[float(v) for v in p] for p in planes],
               clusters=cl),
          open("data_pl/west15_clusters.json", "w", encoding="utf-8"), indent=1)

# overlay na ortofoto
im = Image.open("data_pl/warszawa_orto_200m_north.tif").convert("RGB")
Aimg = np.array(im)
H, W = Aimg.shape[:2]


def vu(E, N):
    return (E - 636999.05) / 0.1, (488361.95 - N) / 0.1


u0, v0 = vu(*poly.bounds[:2][::-1][::-1]) if False else (None, None)
minx, miny, maxx, maxy = poly.bounds
ua, va = vu(minx, maxy); ub, vb = vu(maxx, miny)
crop = im.crop((int(ua) - 20, int(va) - 20, int(ub) + 20, int(vb) + 20))
S = 3
crop = crop.resize((crop.width * S, crop.height * S), Image.LANCZOS)
d = ImageDraw.Draw(crop)
xs, ys = poly.exterior.coords.xy
d.line([(((E - 636999.05) / 0.1 - (int(ua) - 20)) * S, ((488361.95 - N) / 0.1 - (int(va) - 20)) * S) for E, N in zip(xs, ys)], fill=(255, 0, 0), width=2)
for i, c_ in enumerate(cl):
    u, v = vu(c_["cx"], c_["cy"])
    X, Y = (u - (int(ua) - 20)) * S, (v - (int(va) - 20)) * S
    d.ellipse([X - 12, Y - 12, X + 12, Y + 12], outline=(0, 255, 255), width=3)
    d.text((X + 14, Y - 8), str(i), fill=(0, 255, 255))
crop.save("render/pl_west15_clusters.png")
print("ulozeno render/pl_west15_clusters.png")
