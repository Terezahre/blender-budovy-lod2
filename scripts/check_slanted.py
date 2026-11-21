# -*- coding: utf-8 -*-
"""Kontrola sikmych ploch v geof LOD22: pocet faces s |nz| v (0.1, 0.9)."""
import numpy as np
import sys

def slanted(path):
    V, F = [], []
    for line in open(path, encoding="utf-8"):
        if line.startswith("v "):
            V.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("f "):
            F.append([int(x.split("/")[0]) - 1 for x in line.split()[1:]])
    V = np.array(V)
    nS = nH = 0
    for f in F:
        if len(f) < 3:
            continue
        tris = [[f[0], f[i], f[i + 1]] for i in range(1, len(f) - 1)] if len(f) > 3 else [f]
        for t in tris:
            n = np.cross(V[t[1]] - V[t[0]], V[t[2]] - V[t[0]])
            L = np.linalg.norm(n)
            if L < 1e-12:
                continue
            nz = abs(n[2] / L)
            if nz > 0.9:
                nH += 1
            elif nz > 0.1:
                nS += 1
    return nH, nS

if __name__ == "__main__":
    for p in sys.argv[1:]:
        h, s = slanted(p)
        print(f"{p}: horizontal={h} SIKME={s}")
