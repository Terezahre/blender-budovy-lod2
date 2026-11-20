# -*- coding: utf-8 -*-
"""Celomapovy scan KRAV59: dlazdice 500 m, DBSCAN, predfiltr, RANSAC screen
sikmych rovin. Vystup: buildings/gable_candidates.json
"""
import json
import numpy as np
import laspy
from sklearn.cluster import DBSCAN

import sys
sys.path.insert(0, "scripts")
from reconstruct_lod2 import ransac_planes

las = laspy.read("KRAV59_DMP1G/KRAV59.laz")
pts = np.vstack([las.x, las.y, las.z]).T
cls = np.array(las.classification)

CH = 500.0
xs = np.arange(-740000.0, -737500.0, CH)
ys = np.arange(-1040000.0, -1038000.0, CH)
out = []
for xi, (xa, xb) in enumerate(zip(xs, xs + CH)):
    for yi, (ya, yb) in enumerate(zip(ys, ys + CH)):
        m = (cls == 6) & (pts[:, 0] >= xa) & (pts[:, 0] < xb) & (pts[:, 1] >= ya) & (pts[:, 1] < yb)
        b = pts[m]
        if len(b) < 200:
            continue
        try:
            lab = DBSCAN(eps=2.5, min_samples=30).fit(b[:, :2]).labels_
        except Exception:
            continue
        for L in sorted(set(lab.tolist()) - {-1}):
            p = b[lab == L]
            if not (120 <= len(p) <= 900):
                continue
            w, h = p[:, 0].max() - p[:, 0].min(), p[:, 1].max() - p[:, 1].min()
            if not (60 <= w * h <= 2500):
                continue
            zstd = float(p[:, 2].std())
            if not (1.5 < zstd < 8.0):
                continue
            g = pts[(cls == 2) & (pts[:, 0] >= p[:, 0].min() - 5) & (pts[:, 0] <= p[:, 0].max() + 5)
                    & (pts[:, 1] >= p[:, 1].min() - 5) & (pts[:, 1] <= p[:, 1].max() + 5)]
            gz = float(np.percentile(g[:, 2], 5)) if len(g) else float(p[:, 2].min())
            rel = float(p[:, 2].max() - gz)
            if not (3.0 < rel < 15.0):
                continue
            roof = p[p[:, 2] > gz + 1.5]
            if len(roof) < 60:
                continue
            planes, _ = ransac_planes(roof, 0.20, 12, max_planes=4, iters=150)
            kinds = []
            for pl in planes:
                nz = abs(pl["plane"][2])
                kinds.append(("H" if nz > 0.97 else ("W" if nz < 0.30 else "S"), len(pl["idx"])))
            sc = sum(n for k, n in kinds if k == "S")
            if sc >= 40:
                out.append(dict(tile=[xi, yi], cl=int(L), n=int(len(p)),
                                w=round(w, 1), h=round(h, 1), zstd=round(zstd, 2),
                                rel=round(rel, 1), xc=round(float(p[:, 0].mean()), 1),
                                yc=round(float(p[:, 1].mean()), 1),
                                kinds=kinds, score=int(sc)))
                print(f"tile=({xi},{yi}) cl={L} n={len(p)} {w:.0f}x{h:.0f}m "
                      f"zstd={zstd:.2f} rel={rel:.1f} {kinds}", flush=True)
        print(f"chunk ({xi},{yi}) hotovo", flush=True)

out.sort(key=lambda r: -r["score"])
json.dump(out, open("buildings/gable_candidates.json", "w", encoding="utf-8"), indent=1)
print(f"TOTAL {len(out)} kandidatu -> buildings/gable_candidates.json")
