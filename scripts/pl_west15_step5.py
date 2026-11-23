# -*- coding: utf-8 -*-
"""Krok 5b: bile vikýře = top-hat (lokalne svetle) ve footprintu.
Komponenty -> (te,so) centrovane -> pasy rad ku hreebeni -> cislovany overlay.
"""
import json
import numpy as np
from PIL import Image, ImageDraw
from shapely import wkt
from shapely.geometry import Point
from scipy import ndimage as ndi

FID = "ID-1465-38F62225-F3F5-F520-E053-CA2BA8C0BE14"
poly = wkt.loads(json.load(open("data_pl/warszawa_gt.json", encoding="utf-8"))[FID]["footprint_wkt"])
info = json.load(open("data_pl/west15_clusters.json", encoding="utf-8"))
eave = np.array(info["eave"])
perp = np.array([-eave[1], eave[0]])

im = Image.open("data_pl/warszawa_orto_200m_north.tif").convert("RGB")
A = np.array(im).astype(np.float32)
H, W = A.shape[:2]
yy, xx = np.mgrid[0:H, 0:W]
Eo = 636999.05 + 0.1 * xx
No = 488361.95 - 0.1 * yy
Ef, Nf = Eo.ravel(), No.ravel()
inside = np.array([poly.contains(Point(px, py)) for px, py in zip(Ef, Nf)]).reshape(H, W)
mx = A.max(axis=2)
bg = ndi.median_filter(mx, size=15)
tophat = (mx - bg > 22) & inside
lab, n = ndi.label(tophat, structure=np.ones((3, 3)))
print("komponentu: %d" % n)
comps = []
for i in range(1, n + 1):
    ys, xs = np.where(lab == i)
    area = len(xs) * 0.01
    if not (0.5 < area < 60):
        continue
    Em, Nm = Eo[ys, xs].mean(), No[ys, xs].mean()
    P = np.stack([Eo[ys, xs] - Em, No[ys, xs] - Nm], 1)
    we = P @ eave
    wp = P @ perp
    comps.append(dict(E=float(Em), N=float(Nm), area=float(area),
                      w=float(we.max() - we.min() + 0.1), d=float(wp.max() - wp.min() + 0.1)))
print("po filtru plochy: %d" % len(comps))
# centrovane souradnice rady
Eall = np.array([o["E"] for o in comps])
Nall = np.array([o["N"] for o in comps])
te = (np.stack([Eall, Nall], 1) - np.stack([Eall, Nall], 1).mean(axis=0)) @ eave
so = (np.stack([Eall, Nall], 1) - np.stack([Eall, Nall], 1).mean(axis=0)) @ perp
for o, a, b in zip(comps, te, so):
    o["te"], o["so"] = round(float(a), 2), round(float(b), 2)
comps.sort(key=lambda d: (round(d["so"]), -d["te"]))
for i, o in enumerate(comps):
    print("%2d: E=%.2f N=%.2f area=%5.1f %4.1fx%-4.1f te=%+6.1f so=%+6.1f" % (
        i, o["E"], o["N"], o["area"], o["w"], o["d"], o["te"], o["so"]))
json.dump(comps, open("data_pl/west15_tophat.json", "w", encoding="utf-8"), indent=1)

# overlay na vyrez
u0, v0, u1, v1 = 830, 790, 1090, 1090
crop = im.crop((u0, v0, u1, v1))
S = 4
crop = crop.resize((crop.width * S, crop.height * S), Image.LANCZOS)
d = ImageDraw.Draw(crop)
xs, ys = poly.exterior.coords.xy
d.line([(((EE - 636999.05) / 0.1 - u0) * S, ((488361.95 - NN) / 0.1 - v0) * S)
        for EE, NN in zip(xs, ys)], fill=(255, 0, 0), width=2)
for i, o in enumerate(comps):
    X = ((o["E"] - 636999.05) / 0.1 - u0) * S
    Y = ((488361.95 - o["N"]) / 0.1 - v0) * S
    d.rectangle([X - 12, Y - 12, X + 12, Y + 12], outline=(0, 255, 0), width=2)
    d.text((X + 14, Y - 8), str(i), fill=(0, 255, 0))
crop.save("render/pl_west15_tophat.png")
print("ulozeno render/pl_west15_tophat.png")
