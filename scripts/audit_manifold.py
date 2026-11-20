# -*- coding: utf-8 -*-
"""Manifold audit geoflow OBJ: hrany s != 2 faces."""
import numpy as np
from collections import Counter

p = "output/geoflow/B01_flat/model_lod22.obj"
V, F = [], []
for line in open(p, encoding="utf-8"):
    if line.startswith("v "):
        V.append([float(x) for x in line.split()[1:4]])
    elif line.startswith("f "):
        F.append([int(x.split("/")[0]) - 1 for x in line.split()[1:]])
V = np.array(V)
print("verts", len(V), "faces", len(F))
ec = Counter()
for f in F:
    # ngon -> trianguluj pro audit (fan)
    tris = [[f[0], f[i], f[i + 1]] for i in range(1, len(f) - 1)] if len(f) > 3 else [f]
    for t in tris:
        for e in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            ec[tuple(sorted(e))] += 1
bad = {e: c for e, c in ec.items() if c != 2}
print("nonmanifold hran:", len(bad))
for e, c in list(bad.items())[:10]:
    print("  ", e, "faces:", c, "dV:", np.linalg.norm(V[e[0]] - V[e[1]]))
