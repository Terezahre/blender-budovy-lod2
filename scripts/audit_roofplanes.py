# -*- coding: utf-8 -*-
"""Audit skutecnych stresnich rovin ve vystupnich OBJ (LOD1 vs LOD2).
Metrika: shlukovani normal vzhuru miricich faces (10 stupnu).
Pravda: LOD2.2 vyzaduje >= 2 stresni roviny (sedlova) / 1 u ploche;
plosky vrsek u sedlove/valbove = fakticky LOD1.
Vystup: tabulka do konzole + wiki.
"""
import glob
import json
import os

import numpy as np


def audit(path):
    V, F = [], []
    for line in open(path, encoding="utf-8"):
        if line.startswith("v "):
            V.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("f "):
            F.append([int(x.split("/")[0]) - 1 for x in line.split()[1:]])
    V = np.array(V)
    up = []
    for f in F:
        P = V[np.array(f)[:3]]
        n = np.cross(P[1] - P[0], P[2] - P[0])
        a = np.linalg.norm(n)
        if a > 1e-9 and (n / a)[2] > 0.5:
            up.append(n / a)
    up = np.array(up)
    planes = []
    for n in up:
        for q in planes:
            if float(np.dot(n, q)) > np.cos(np.radians(10)):
                break
        else:
            planes.append(n)
    return dict(faces=len(F), up=len(up), planes=len(planes),
                h=round(float(V[:, 2].max() - V[:, 2].min()), 2) if len(V) else 0)


def main():
    rows = []
    for p in sorted(glob.glob("output/final/*_LOD2_SJTSK.obj")):
        bid = os.path.basename(p).replace("_LOD2_SJTSK.obj", "")
        m = audit(p)
        exp = None
        mp = os.path.join("buildings", bid, "meta.json")
        if os.path.exists(mp):
            meta = json.load(open(mp, encoding="utf-8"))
            exp = meta.get("profile")
        verdict = "OK" if (exp == "SIMPLE_FLAT" and m["planes"] <= 1) or \
            (exp != "SIMPLE_FLAT" and m["planes"] >= 2) else "LOD1!"
        rows.append((bid, exp, m["faces"], m["up"], m["planes"], m["h"], verdict))
    for p in sorted(glob.glob("output/brno_geof/*_ml/model_lod22.obj")):
        bid = os.path.basename(os.path.dirname(p))
        m = audit(p)
        rows.append(("brno:" + bid, "?", m["faces"], m["up"], m["planes"], m["h"], ""))
    print(f"{'model':32} {'profil':15} {'faces':>5} {'up':>3} {'rovin':>5} {'vyska':>6}  verdikt")
    lod1 = 0
    for bid, exp, f, u, pl, h, v in rows:
        if v == "LOD1!":
            lod1 += 1
        print(f"{bid:32} {str(exp):15} {f:>5} {u:>3} {pl:>5} {h:>6}  {v}")
    print(f"\nFakticky LOD1 (sedlova/valbova s ploskym vrskem): {lod1}")


if __name__ == "__main__":
    main()
