# -*- coding: utf-8 -*-
"""Kontrola normal finalnich OBJ: strechy musi mit +Z, steny vodorovne."""
import numpy as np

for bid in ["B01_flat", "B02_gable", "B03_row", "B04_panelak", "B05_vez"]:
    p = f"output/final/{bid}_LOD2_SJTSK.obj"
    V, F = [], []
    for line in open(p, encoding="utf-8"):
        if line.startswith("v "):
            V.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("f "):
            F.append([int(x.split("/")[0]) - 1 for x in line.split()[1:]])
    V = np.array(V)
    ups, downs, walls, other = 0, 0, 0, 0
    for f in F:
        if len(f) < 3:
            continue
        n = np.cross(V[f[1]] - V[f[0]], V[f[2]] - V[f[0]])
        L = np.linalg.norm(n)
        if L < 1e-12:
            continue
        nz = n[2] / L
        if nz > 0.9:
            ups += 1
        elif nz < -0.9:
            downs += 1
        elif abs(nz) < 0.1:
            walls += 1
        else:
            other += 1
    print(f"{bid}: verts={len(V)} faces={len(F)} UP={ups} DOWN={downs} WALL={walls} SIKME={other}")
