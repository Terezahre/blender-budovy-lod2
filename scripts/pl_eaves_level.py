# -*- coding: utf-8 -*-
"""Srovnani OBOU okapu presne do 125.38 (cele hrany, ne jen vrcholy).
Okapove hrany = vrcholy do 1.0 m od hranice footprintu, z>123, |t|<16
(mimo stity). Staci posunout Z, topologie se nemeni.
"""
import numpy as np
from shapely import wkt
from shapely.geometry import Point
import json

FID = "ID-1465-38F62225-F3F5-F520-E053-CA2BA8C0BE14"
Z_OKAP = 125.38
P = "output/pl_geof/%s/model_west15_flat.obj" % FID
V, F = [], []
for line in open(P, encoding="utf-8"):
    if line.startswith("v "):
        V.append([float(x) for x in line.split()[1:4]])
    elif line.startswith("f "):
        F.append(line)
V = np.array(V)
info = json.load(open("data_pl/west15_clusters.json", encoding="utf-8"))
eave = np.array(info["eave"])
perp = np.array([-eave[1], eave[0]])
poly = wkt.loads(json.load(open("data_pl/warszawa_gt.json", encoding="utf-8"))[FID]["footprint_wkt"])
cc = np.array(poly.centroid.coords[0])
ring = poly.exterior
d = np.array([ring.distance(Point(px, py)) for px, py in V[:, :2]])
t = (V[:, :2] - cc) @ eave
m = (d < 1.0) & (V[:, 2] > 123.0) & (np.abs(t) < 16)
print("okapovych vrcholu k srovnani: %d (z %.2f..%.2f)" % (
    int(m.sum()), float(V[m, 2].min()) if m.any() else 0, float(V[m, 2].max()) if m.any() else 0))
V[m, 2] = Z_OKAP
with open(P, "w", encoding="utf-8") as f:
    f.write("# Geoflow LOD22 + srovnane okoli vikýru + rovne okapy 125.38\n")
    for v in V:
        f.write("v %.3f %.3f %.3f\n" % tuple(v))
    for fa in F:
        f.write(fa)
print("zapsano", P)
