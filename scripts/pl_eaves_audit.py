# -*- coding: utf-8 -*-
"""Audit okapu z MRACNA (ne z modelu): vyska hrany strechy Z vs V podel t.
Hrana = nejnizsi strešni body (class 6, z>122 aby vypadly zdi) v pasu u okraje.
Plus hřeben pro kontrolu."""
import laspy
import json
import numpy as np
from shapely import wkt
from shapely.geometry import Point

FID = "ID-1465-38F62225-F3F5-F520-E053-CA2BA8C0BE14"
las = laspy.read(f"buildings_pl/{FID}/body.las")
x, y, z = np.asarray(las.x), np.asarray(las.y), np.asarray(las.z)
c = np.asarray(las.classification)
poly = wkt.loads(json.load(open("data_pl/warszawa_gt.json", encoding="utf-8"))[FID]["footprint_wkt"])
info = json.load(open("data_pl/west15_clusters.json", encoding="utf-8"))
eave = np.array(info["eave"])
perp = np.array([-eave[1], eave[0]])
cc = np.array(poly.centroid.coords[0])
inside = np.array([poly.contains(Point(px, py)) for px, py in zip(x, y)])
P = np.stack([x[inside], y[inside]], 1)
t = (P - cc) @ eave
s = (P - cc) @ perp
zi, ci = z[inside], c[inside]
print("=== MRACNO: hrana strechy = min z tridy 6 se z>122 v pasu s (okapovy pas) ===")
for (s0, tag) in [(-5.5, "ZAPAD"), (5.0, "VYCHOD")]:
    print("--- %s okap (s=%.1f+-0.8) ---" % (tag, s0))
    for t0 in range(-18, 19, 6):
        m = (np.abs(s - s0) < 0.8) & (t >= t0) & (t < t0 + 6) & (ci == 6) & (zi > 122)
        if m.sum() < 3:
            print("  t %d..%d: malo bodu" % (t0, t0 + 6))
            continue
        qs = np.quantile(zi[m], [0.0, 0.1, 0.5])
        print("  t %d..%d: n=%d min=%.2f q10=%.2f med=%.2f" % (t0, t0 + 6, int(m.sum()), float(qs[0]), float(qs[1]), float(qs[2])))
print("=== hreben (s=0+-0.5, class6, z>122) ===")
for t0 in range(-18, 19, 6):
    m = (np.abs(s) < 0.5) & (t >= t0) & (t < t0 + 6) & (ci == 6) & (zi > 122)
    if m.sum() >= 3:
        print("  t %d..%d: n=%d med=%.2f" % (t0, t0 + 6, int(m.sum()), float(np.median(zi[m]))))
