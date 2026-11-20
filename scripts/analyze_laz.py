# -*- coding: utf-8 -*-
"""Analýza KRAV59.laz: globální statistiky + návrh pilotních budov pro LOD2.
Čte KRAV59_DMP1G/KRAV59.laz (S-JTSK, EPSG:5514), výstup tiskne + ukládá JSON.
"""
import json
import numpy as np
import laspy

SRC = "KRAV59_DMP1G/KRAV59.laz"
OUT = "buildings/candidates.json"

# testovaci dlazdice 500x500 m s hustou zastavbou (z grid analyzy)
# vybrana rovina s nizkym zstd (~1.0): okoli Brezineves/Ďablice
TILE = (-738000.0, -737500.0, -1039350.0, -1038850.0)

def main():
    las = laspy.read(SRC)
    pts = np.vstack([las.x, las.y, las.z]).T
    cls = np.array(las.classification)
    print(f"total={len(pts)} header_mins={list(las.header.mins)} maxs={list(las.header.maxs)}")
    stats = {}
    for c in sorted(set(cls.tolist())):
        p = pts[cls == c]
        stats[int(c)] = dict(n=int((cls == c).sum()),
                             zmin=float(p[:, 2].min()), zmax=float(p[:, 2].max()),
                             zmean=float(p[:, 2].mean()), zstd=float(p[:, 2].std()))
        print(f"class {c}: {stats[int(c)]}")
    # --- DBSCAN klastry class 6 v testovací dlaždici ---
    from sklearn.cluster import DBSCAN
    x0, x1, y0, y1 = TILE
    m = (cls == 6) & (pts[:, 0] >= x0) & (pts[:, 0] < x1) & (pts[:, 1] >= y0) & (pts[:, 1] < y1)
    b = pts[m]
    print(f"tile {TILE}: building points={len(b)}")
    db = DBSCAN(eps=2.5, min_samples=30).fit(b[:, :2])
    labels = db.labels_
    ids = sorted(set(labels.tolist()) - {-1})
    print(f"clusters={len(ids)} noise={int((labels == -1).sum())}")
    cands = []
    for lab in ids:
        p = b[labels == lab]
        if len(p) < 200:
            continue
        area = (p[:, 0].max() - p[:, 0].min()) * (p[:, 1].max() - p[:, 1].min())
        dens = len(p) / max(area, 1.0)
        cands.append(dict(cluster=int(lab), n=int(len(p)),
                          x0=float(p[:, 0].min()), x1=float(p[:, 0].max()),
                          y0=float(p[:, 1].min()), y1=float(p[:, 1].max()),
                          zmin=float(p[:, 2].min()), zmax=float(p[:, 2].max()),
                          zstd=float(p[:, 2].std()),
                          bbox_area=float(area), density=float(dens)))
    cands.sort(key=lambda d: -d["n"])
    print("TOP 10 clusterů (n, bbox m, zstd, hustota):")
    for c in cands[:10]:
        w = c["x1"] - c["x0"]; h = c["y1"] - c["y0"]
        print(f"  cl={c['cluster']} n={c['n']} {w:.0f}x{h:.0f}m "
              f"z=[{c['zmin']:.1f},{c['zmax']:.1f}] zstd={c['zstd']:.2f} dens={c['density']:.2f}/m2")
    import os
    os.makedirs("buildings", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(dict(tile=list(TILE), candidates=cands), f, indent=1)
    print(f"-> {OUT} ({len(cands)} kandidatu)")

if __name__ == "__main__":
    main()
