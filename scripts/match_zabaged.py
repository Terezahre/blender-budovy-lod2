# -*- coding: utf-8 -*-
"""Parovani nasich budov na ZABAGED + vyber domu s lidar pokrytim."""
import json
import numpy as np
import laspy
import geopandas as gpd
from shapely.geometry import shape, Point

zab = gpd.read_file("buildings/zabaged_krav59.gpkg")
las = laspy.read("KRAV59_DMP1G/KRAV59.laz")
pts = np.vstack([las.x, las.y, las.z]).T
cls = np.array(las.classification)
b6 = pts[cls == 6]

print("--- nase budovy vs ZABAGED ---")
for bid in ["B01_flat", "B02_gable", "B03_row", "B04_panelak", "B05_vez",
            "B06_sedlova", "G1_sedlova", "G2_sedlova", "G3_domek"]:
    gj = json.load(open(f"buildings/{bid}/footprint.geojson", encoding="utf-8"))
    c = shape(gj["features"][0]["geometry"]).centroid
    hit = zab[zab.geometry.contains(c)]
    if len(hit):
        h = hit.iloc[0]
        print(f"{bid}: ZABAGED area={h['area']:.0f} druh={h['druh']}")
    else:
        zab["d"] = zab.geometry.centroid.distance(c)
        h = zab.sort_values("d").iloc[0]
        print(f"{bid}: MIMO polygon, nejblizsi area={h['area']:.0f} dist={h['d']:.1f}m")

# domy 60-300 m2 s >=100 lidar body class 6 uvnitr
print("\n--- TOP domy s pokrytim ---")
cand = zab[(zab.area >= 60) & (zab.area <= 300)].copy()
rows = []
for i, r in cand.iterrows():
    x0, y0, x1, y1 = r.geometry.bounds
    sel = b6[(b6[:, 0] >= x0) & (b6[:, 0] <= x1) & (b6[:, 1] >= y0) & (b6[:, 1] <= y1)]
    inside = sum(1 for p in sel if r.geometry.contains(Point(p[0], p[1])))
    if inside >= 100:
        rows.append((inside, r["fid_zbg"], r["area"], r["druh"],
                     round(float(r.geometry.centroid.x), 1),
                     round(float(r.geometry.centroid.y), 1)))
rows.sort(reverse=True)
for n, fid, a, druh, x, y in rows[:15]:
    print(f"n={n} area={a:.0f} {druh} centroid=({x},{y}) fid={fid}")
print("celkem s pokrytim 100+:", len(rows))
