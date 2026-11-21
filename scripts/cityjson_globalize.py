# -*- coding: utf-8 -*-
"""Globalizace CityJSON v2: meritko je presne 0.001 (mm), translace se hleda
RANSACem pres korespondence vertexu vuci S-JTSK OBJ. Verifikace < 5 mm,
jinak exit 1 a soubor se nemeni.
"""
import json
import sys
import numpy as np
from scipy.spatial import cKDTree

CJ, OBJ = sys.argv[1], sys.argv[2]
rng = np.random.default_rng(7)

d = json.load(open(CJ, encoding="utf-8"))
V = np.array(d["vertices"], dtype=float)
# jen vertexy pouzite v LoD 2.2 (mesta obsahuje i 0/1.2/1.3 s jinou teselaci)
used = set()
for o in d["CityObjects"].values():
    for g in o.get("geometry", []):
        if str(g.get("lod")) == "2.2":
            for shell in g["boundaries"]:
                for face in shell:
                    used.update(face[0])
used = sorted(used)
W = V[used]
O = np.array([[float(x) for x in l.split()[1:4]]
              for l in open(OBJ, encoding="utf-8") if l.startswith("v ")])

tree = cKDTree(O)
best = (0, None)
for _ in range(400):
    i, j = rng.integers(0, len(W)), rng.integers(0, len(O))
    t = O[j] - W[i] * 0.001
    dist, _ = tree.query(W * 0.001 + t)
    inl = int((dist < 0.005).sum())
    if inl > best[0]:
        best = (inl, t)
        if inl == len(W):
            break
inl, t = best
print(f"inliers: {inl}/{len(W)} (z {len(V)} total)  t={np.round(t, 3)}")
if inl < 0.9 * len(W):
    print("MAPOVANI NEOVERENO - soubor nemenim")
    sys.exit(1)
# vertexy zustavaji int (mm), georeference nese standardni transform klic
d["metadata"]["transform"] = {
    "scale": [0.001, 0.001, 0.001],
    "translate": [round(float(t[0]), 3), round(float(t[1]), 3), round(float(t[2]), 3)],
}
G = V * 0.001 + t
d["metadata"]["geographicalExtent"] = [
    round(float(G[:, 0].min()), 3), round(float(G[:, 1].min()), 3),
    round(float(G[:, 2].min()), 3), round(float(G[:, 0].max()), 3),
    round(float(G[:, 1].max()), 3), round(float(G[:, 2].max()), 3)]
json.dump(d, open(CJ, "w", encoding="utf-8"))
print(f"OK: {CJ} -> globalni S-JTSK metry")
