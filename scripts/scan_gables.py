# -*- coding: utf-8 -*-
"""Scan vsech DBSCAN klastru v dlazdici: hledaji se sedlove strechy
(2 velke SIKME roviny RANSACem). Vystup: serazeny seznam kandidatu.
"""
import numpy as np
import laspy
from sklearn.cluster import DBSCAN

las = laspy.read("KRAV59_DMP1G/KRAV59.laz")
pts = np.vstack([las.x, las.y, las.z]).T
cls = np.array(las.classification)
x0, x1, y0, y1 = (-738000.0, -737500.0, -1039350.0, -1038850.0)
m = (cls == 6) & (pts[:, 0] >= x0) & (pts[:, 0] < x1) & (pts[:, 1] >= y0) & (pts[:, 1] < y1)
b = pts[m]
labels = DBSCAN(eps=2.5, min_samples=30).fit(b[:, :2]).labels_

import sys
sys.path.insert(0, "scripts")
from reconstruct_lod2 import ransac_planes, fit_plane

rows = []
for lab in sorted(set(labels.tolist()) - {-1}):
    p = b[labels == lab]
    if not (120 <= len(p) <= 900):
        continue
    g = pts[(cls == 2) & (pts[:, 0] >= p[:, 0].min() - 5) & (pts[:, 0] <= p[:, 0].max() + 5)
            & (pts[:, 1] >= p[:, 1].min() - 5) & (pts[:, 1] <= p[:, 1].max() + 5)]
    gz = float(np.percentile(g[:, 2], 5)) if len(g) else float(p[:, 2].min())
    roof = p[p[:, 2] > gz + 1.5]
    if len(roof) < 60:
        continue
    planes, rest = ransac_planes(roof, 0.20, 12, max_planes=6, iters=200)
    kinds = []
    for pl in planes:
        nz = abs(pl["plane"][2])
        kinds.append(("H" if nz > 0.97 else ("W" if nz < 0.30 else "S"), len(pl["idx"])))
    slanted = [n for k, n in kinds if k == "S"]
    score = sum(slanted)
    rows.append(dict(cl=int(lab), n=int(len(p)),
                     w=round(float(p[:, 0].max() - p[:, 0].min()), 1),
                     h=round(float(p[:, 1].max() - p[:, 1].min()), 1),
                     zstd=round(float(p[:, 2].std()), 2),
                     rel=round(float(p[:, 2].max() - gz), 1),
                     kinds=kinds, slant_score=int(score)))

rows.sort(key=lambda r: (-r["slant_score"], -r["n"]))
print(f"{'cl':>5} {'n':>5} {'rozmer':>9} {'zstd':>6} {'rel_h':>6}  roviny")
for r in rows[:25]:
    print(f"{r['cl']:>5} {r['n']:>5} {r['w']:>4.0f}x{r['h']:<4.0f} {r['zstd']:>6.2f} {r['rel']:>6.1f}  {r['kinds']} SCORE={r['slant_score']}")
