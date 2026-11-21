# -*- coding: utf-8 -*-
"""ZABAGED polygony -> GPKG + parovani s lidar klastrama."""
import json
import geopandas as gpd
from shapely.geometry import shape

d = json.load(open(r"C:\Users\Tereza\AppData\Local\Temp\opencode\zabaged.json"))
recs = []
for f in d["features"]:
    g = shape(f["geometry"])
    p = f["properties"]
    recs.append({"fid_zbg": str(p.get("fid_zbg")), "druh": p.get("druhbud"),
                 "area": float(p.get("Shape_Area", g.area)), "geometry": g})
gdf = gpd.GeoDataFrame(recs, crs="EPSG:5514")
gdf.to_file("buildings/zabaged_tile.gpkg", driver="GPKG")
print("budov:", len(gdf))
print(gdf[["fid_zbg", "druh", "area"]].sort_values("area").to_string())

# parovani: centroidy nasich footprintu vs ZABAGED
import os
print("\n--- nejblizsi ZABAGED polygon pro nase budovy ---")
for bid in ["B01_flat", "B02_gable", "B03_row", "B04_panelak", "G1_sedlova", "G2_sedlova", "G3_domek"]:
    gj = json.load(open(f"buildings/{bid}/footprint.geojson", encoding="utf-8"))
    c = shape(gj["features"][0]["geometry"]).centroid
    gdf["d"] = gdf.geometry.centroid.distance(c)
    b = gdf.sort_values("d").iloc[0]
    print(f"{bid}: ZABAGED area={b['area']:.0f} druh={b['druh']} dist={b['d']:.1f}m")
