# -*- coding: utf-8 -*-
"""PL dum: sever-up GeoTIFF + kontrola prekryvu (OPRAVENO).
WMS vraci radek 0 = SEVER (overeno vegetaci z LiDARu: tridy 3/4/5 sedi na
zelenou jen pri v=(N1-N); puvodni predpoklad 'radek 0 = jih' byl spatne
a druhe vlakno ho melo spatne taky (extent+origin jim patch zrcadlil).
Mapovani: sloupec u=(E-E0)/SP*W, radek v=(N1-N)/SP*H (sever nahore).
Vystup: data_pl/warszawa_orto_200m_north.tif (+ .tfw, standardni north-up),
        render/pl_orto_footprint.png (kontrola prekryvu).
"""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from shapely import wkt

FID = "ID-1465-38F62225-F3F5-F520-E053-CA2BA8C0BE14"
E0, N0, E1, N1, SP = 636999.0, 488162.0, 637199.0, 488362.0, 200.0

img = np.array(Image.open("data_pl/warszawa_orto_200m.tif").convert("RGB"))
H, W, _ = img.shape
assert (W, H) == (2000, 2000), (W, H)
north = img[::-1, :, :].copy()  # radek 0 = sever
Image.fromarray(north).save("data_pl/warszawa_orto_200m_north.tif")
px = SP / W
with open("data_pl/warszawa_orto_200m_north.tfw", "w") as f:
    f.write(f"{px:.6f}\n0.0\n0.0\n{-px:.6f}\n{E0 + px/2:.3f}\n{N1 - px/2:.3f}\n")
print("sever-up ulozen, px=%.3f m" % px)

poly = wkt.loads(json.load(open("data_pl/warszawa_gt.json", encoding="utf-8"))[FID]["footprint_wkt"])
x, y = poly.exterior.coords.xy
u = (np.array(x) - E0) / SP * W
v = (N1 - np.array(y)) / SP * H

import os
for f in ["data_pl/warszawa_orto_200m.tfw"]:
    if os.path.exists(f):
        os.remove(f)
        print("smazan spatny soubor:", f)

fig, a = plt.subplots(figsize=(10, 10))
a.imshow(north)
a.plot(u, v, "r-", lw=2, label="GT footprint")
a.plot(u, v, "ro", ms=3)
a.set_title("StandardResolution sever-up + GT footprint (opraveno)")
a.legend()
plt.tight_layout()
plt.savefig("render/pl_orto_footprint.png", dpi=110)
print("ulozeno render/pl_orto_footprint.png; footprint bounds:",
      [round(v, 2) for v in poly.bounds])
