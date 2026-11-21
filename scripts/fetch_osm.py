# -*- coding: utf-8 -*-
"""Overpass pres hlavni endpoint s browser User-Agent."""
import json
import urllib.request

q = ('[out:json][timeout:60];way["building"]'
     '(50.1260,14.4810,50.1300,14.4870);out geom;')
req = urllib.request.Request(
    "https://overpass-api.de/api/interpreter", data=q.encode(),
    headers={"Content-Type": "application/x-www-form-urlencoded",
             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
try:
    d = json.load(urllib.request.urlopen(req, timeout=120))
    print("elements:", len(d.get("elements", [])))
    json.dump(d, open(r"C:\Users\Tereza\AppData\Local\Temp\opencode\osm.json", "w"))
    print("saved")
except Exception as e:
    print("FAIL", str(e)[:200])
