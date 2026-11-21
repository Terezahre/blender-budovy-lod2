# -*- coding: utf-8 -*-
"""ZABAGED budovy pro cele KRAV59 (4 kvadranty) -> buildings/zabaged_krav59.gpkg."""
import json
import urllib.parse
import urllib.request
import geopandas as gpd
from shapely.geometry import shape

QUADS = [
    (-740000, -1039000, -738750, -1038000),
    (-738750, -1039000, -737500, -1038000),
    (-740000, -1040000, -738750, -1039000),
    (-738750, -1040000, -737500, -1039000),
]
recs = {}
for q in QUADS:
    params = {"where": "1=1",
              "geometry": ",".join(map(str, q)),
              "geometryType": "esriGeometryEnvelope",
              "inSR": "5514", "outSR": "5514",
              "spatialRel": "esriSpatialRelIntersects",
              "outFields": "fid_zbg,druhbud,Shape_Area",
              "returnGeometry": "true", "f": "geojson"}
    url = ("https://ags.cuzk.gov.cz/arcgis/rest/services/ZABAGED_POLOHOPIS/MapServer/99/query?"
           + urllib.parse.urlencode(params))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    d = json.load(urllib.request.urlopen(req, timeout=120))
    for f in d.get("features", []):
        p = f["properties"]
        recs[str(p.get("fid_zbg"))] = {
            "fid_zbg": str(p.get("fid_zbg")), "druh": p.get("druhbud"),
            "area": float(p.get("Shape_Area", 0)), "geometry": shape(f["geometry"])}
    print(q, "->", len(d.get("features", [])), "exceeded:", d.get("exceededTransferLimit"))

gdf = gpd.GeoDataFrame(list(recs.values()), crs="EPSG:5514")
gdf.to_file("buildings/zabaged_krav59.gpkg", driver="GPKG")
print("TOTAL unikatnich budov:", len(gdf))
small = gdf[(gdf.area >= 60) & (gdf.area <= 400)]
print("rodinne domy 60-400 m2:", len(small))
