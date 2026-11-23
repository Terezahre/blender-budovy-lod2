# -*- coding: utf-8 -*-
"""SZ zona: vsechny bile obdelniky (primy mapping) vs hranoly. Najit chybejici vikýř."""
import json
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

FID = "ID-1465-38F62225-F3F5-F520-E053-CA2BA8C0BE14"
info = json.load(open("data_pl/west15_clusters.json", encoding="utf-8"))
eave = np.array(info["eave"])
perp = np.array([-eave[1], eave[0]])

im = Image.open("data_pl/warszawa_orto_200m_north.tif").convert("RGB")
A = np.array(im).astype(np.float32)
H, W = A.shape[:2]
yy, xx = np.mgrid[0:H, 0:W]
E = 636999.05 + 0.1 * xx
N = 488361.95 - 0.1 * yy
# SZ zona: E 637078-637098, N 488258-488278
zone = (E > 637078) & (E < 637098) & (N > 488258) & (N < 488278)
mx, mn = A.max(axis=2), A.min(axis=2)
bright = (mx > 165) & ((mx - mn) < 70) & zone
lab, n = ndi.label(bright, structure=np.ones((3, 3)))
print("komponentu v SZ zone: %d" % n)
comps = []
for i in range(1, n + 1):
    ys, xs = np.where(lab == i)
    area = len(xs) * 0.01
    if not (0.8 < area < 12):
        continue
    Em, Nm = E[ys, xs].mean(), N[ys, xs].mean()
    P = np.stack([E[ys, xs] - Em, N[ys, xs] - Nm], 1)
    we = P @ eave
    wp = P @ perp
    comps.append(dict(E=float(Em), N=float(Nm), area=float(area),
                      w=float(we.max() - we.min() + 0.1),
                      d=float(wp.max() - wp.min() + 0.1)))
for o in comps:
    print("  E=%.2f N=%.2f area=%4.1f %4.1fx%-4.1f m" % (
        o["E"], o["N"], o["area"], o["w"], o["d"]))
# vyrez s cisly
u0, v0 = 780, 830
crop = im.crop((u0, v0, u0 + 220, v0 + 220))
S = 4
crop = crop.resize((crop.width * S, crop.height * S), Image.LANCZOS)
d = ImageDraw.Draw(crop)
for i, o in enumerate(comps):
    X = ((o["E"] - 636999.05) / 0.1 - u0) * S
    Y = ((488361.95 - o["N"]) / 0.1 - v0) * S
    hw, hd = o["w"] / 0.1 * S / 2, o["d"] / 0.1 * S / 2
    d.rectangle([X - hw, Y - hd, X + hw, Y + hd], outline=(0, 255, 0), width=2)
    d.text((X - hw, Y - hd - 14), "%d" % i, fill=(0, 255, 0))
# hranoly U1/L1/L2
doms = json.load(open("data_pl/west15_layout.json", encoding="utf-8"))
for dd in doms:
    if dd["id"] in ("U1", "L1", "L2"):
        X = ((dd["cx"] - 636999.05) / 0.1 - u0) * S
        Y = ((488361.95 - dd["cy"]) / 0.1 - v0) * S
        d.ellipse([X - 8, Y - 8, X + 8, Y + 8], outline=(255, 0, 0), width=2)
        d.text((X + 10, Y - 8), dd["id"], fill=(255, 0, 0))
crop.save("render/pl_west15_sz.png")
print("ulozeno render/pl_west15_sz.png")
