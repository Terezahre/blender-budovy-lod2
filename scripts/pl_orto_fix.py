# -*- coding: utf-8 -*-
"""PL dum: overeni GeoTIFF okna + kontrola prekryvu s GT footprintem.
Fakt: WMS TIFF ma stejny layout jako JPG (radek 0 = jih, NCC 0.9926).
Mapovani C (overeno): sloupec u = vychod, radek v = sever odspodu.
  E = E0 + u/W*SP, N = N0 + v/H*SP   (E0=636999, N0=488162, SP=200)
Vystup: data_pl/warszawa_orto_200m.tfw (svetovy soubor, +y krok = jih-up),
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
E0, N0, SP = 636999.0, 488162.0, 200.0

img = np.array(Image.open("data_pl/warszawa_orto_200m.tif").convert("RGB"))
H, W, _ = img.shape
px = SP / W
assert W == H == 2000, (W, H)
# south-up world file: radek roste k severu -> +y krok, pocatek = JZ roh
with open("data_pl/warszawa_orto_200m.tfw", "w") as f:
    f.write(f"{px:.6f}\n0.0\n0.0\n{px:.6f}\n{E0 + px/2:.3f}\n{N0 + px/2:.3f}\n")
print("tfw zapsan (south-up, px=%.3f m)" % px)

poly = wkt.loads(json.load(open("data_pl/warszawa_gt.json", encoding="utf-8"))[FID]["footprint_wkt"])
x, y = poly.exterior.coords.xy
u = (np.array(x) - E0) / SP * W
v = (np.array(y) - N0) / SP * H

import os
for f in ["data_pl/warszawa_orto_200m_north.tif", "data_pl/warszawa_orto_200m_north.tfw"]:
    if os.path.exists(f):
        os.remove(f)
        print("smazan spatny soubor:", f)

fig, a = plt.subplots(figsize=(10, 10))
a.imshow(img)
a.plot(u, v, "r-", lw=2, label="GT footprint")
a.plot(u, v, "ro", ms=3)
a.set_title("StandardResolution (radek 0 = jih) + GT footprint, mapovani C")
a.legend()
plt.tight_layout()
plt.savefig("render/pl_orto_footprint.png", dpi=110)
print("ulozeno render/pl_orto_footprint.png; footprint bounds:",
      [round(v, 2) for v in poly.bounds])
