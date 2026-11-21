# -*- coding: utf-8 -*-
"""Stazeni ZABAGED budov (vrstva 99) pro pilotni dlazdici, S-JTSK GeoJSON."""
import json
import urllib.parse
import urllib.request

base = "https://ags.cuzk.gov.cz/arcgis/rest/services/ZABAGED_POLOHOPIS/MapServer/99/query"
params = {
    "where": "1=1",
    "geometry": "-738000,-1039350,-737500,-1038850",
    "geometryType": "esriGeometryEnvelope",
    "inSR": "5514",
    "outSR": "5514",
    "spatialRel": "esriSpatialRelIntersects",
    "outFields": "*",
    "returnGeometry": "true",
    "f": "geojson",
}
url = base + "?" + urllib.parse.urlencode(params)
print(url[:120], "...")
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
d = json.load(urllib.request.urlopen(req, timeout=120))
feats = d.get("features", [])
print("budov:", len(feats), "| exceededTransferLimit:", d.get("exceededTransferLimit"))
json.dump(d, open(r"C:\Users\Tereza\AppData\Local\Temp\opencode\zabaged.json", "w"))
print("saved")
for f in feats[:5]:
    print(f.get("properties", {}).get("NAZEV", f.get("properties")))
