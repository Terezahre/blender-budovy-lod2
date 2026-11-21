# -*- coding: utf-8 -*-
"""Hausdorffova vzdalenost mezi dvema OBJ (cisty numpy, bez Blenderu).
Beh: python scripts/hausdorff_check.py <a.obj> <b.obj>
Vystup: Hmax/Hmean v metrech (+cm). Symetricky max z obou smeru.
"""
import sys

import numpy as np


def load(p):
    V, F = [], []
    for line in open(p, encoding="utf-8"):
        if line.startswith("v "):
            V.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("f "):
            F.append([int(x.split("/")[0]) - 1 for x in line.split()[1:]])
    V = np.array(V)
    T = []
    for f in F:
        P = V[np.array(f)]
        for i in range(1, len(P) - 1):
            T.append([P[0], P[i], P[i + 1]])
    return V, np.array(T)


def point_tri_dist(P, T):
    A, B, C = T[:, 0], T[:, 1], T[:, 2]
    AB, AC = B - A, C - A
    best = np.full(len(P), np.inf)
    for i in range(0, len(T), 64):
        a = A[i:i + 64, None, :]
        ab = AB[i:i + 64, None, :]
        ac = AC[i:i + 64, None, :]
        ap = P[None, :, :] - a
        d1 = np.einsum("knj,knj->kn", ab, ap)
        d2 = np.einsum("knj,knj->kn", ac, ap)
        d3 = np.einsum("knj,knj->kn", ab, ab)
        d4 = np.einsum("knj,knj->kn", ab, ac)
        d5 = np.einsum("knj,knj->kn", ac, ac)
        denom = d3 * d5 - d4 * d4 + 1e-18
        u = (d5 * d1 - d4 * d2) / denom
        v = (d3 * d2 - d4 * d1) / denom
        inside = (u >= 0) & (v >= 0) & (u + v <= 1)
        proj = a + np.clip(u, 0, 1)[:, :, None] * ab + np.clip(v, 0, 1)[:, :, None] * ac
        dd = np.sqrt(np.einsum("knj,knj->kn", P[None, :, :] - proj, P[None, :, :] - proj))
        dd = np.where(inside, dd, np.inf)
        for Q, R in ((a, a + ab), (a, a + ac), (a + ab, a + ac)):
            t = np.einsum("knj,knj->kn", P[None, :, :] - Q, R - Q)
            t /= (np.einsum("knj,knj->kn", R - Q, R - Q) + 1e-18)
            t = np.clip(t, 0, 1)
            dd = np.minimum(dd, np.sqrt(np.einsum(
                "knj,knj->kn", P[None, :, :] - (Q + t[:, :, None] * (R - Q)),
                P[None, :, :] - (Q + t[:, :, None] * (R - Q)))))
        best = np.minimum(best, dd.min(axis=0))
    return best


def main():
    Va, Ta = load(sys.argv[1])
    Vb, Tb = load(sys.argv[2])
    dab = point_tri_dist(Va, Tb)
    dba = point_tri_dist(Vb, Ta)
    print(f"Hmax={max(dab.max(), dba.max()):.3f} m "
          f"({max(dab.max(), dba.max()) * 100:.1f} cm) "
          f"Hmean={np.mean(np.concatenate([dab, dba])) * 100:.1f} cm")


if __name__ == "__main__":
    main()
