# -*- coding: utf-8 -*-
"""Profil vychodniho svahu u okapu: je zvednuti v datech, nebo artefakt meshe?"""
import laspy
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
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
fig, ax = plt.subplots(2, 1, figsize=(13, 8), sharex=True)
m6 = (t > -2) & (t < 6) & (ci == 6)
ax[0].scatter(s[m6], zi[m6], s=5)
ax[0].set_title("LiDAR class6, pas t=-2..6: s vs Z (vychod vpravo)")
ax[0].grid(True)
ax[0].set_ylabel("Z [m]")
m2 = (t > -2) & (t < 6) & (ci == 2)
ax[1].scatter(s[m2], zi[m2], s=5)
ax[1].set_title("LiDAR class2 (teren), stejny pas")
ax[1].grid(True)
ax[1].set_xlabel("s kolmo [m]")
ax[1].set_ylabel("Z [m]")
plt.tight_layout()
plt.savefig("render/pl_west15_vychod.png", dpi=90)
print("ulozeno")
me = (s > 4) & (s < 7) & (ci == 6)
print("class6 u vychodniho okapu (s 4..7): n=%d" % int(me.sum()))
if me.any():
    print("  zmin=%.2f zmax=%.2f zmed=%.2f" % (
        float(zi[me].min()), float(zi[me].max()), float(np.median(zi[me]))))
mw = (s > 3) & (s < 5) & (ci == 6)
print("class6 stred svahu (s 3..5): n=%d zmed=%.2f" % (
    int(mw.sum()), float(np.median(zi[mw])) if mw.any() else (0, 0)))
