# -*- coding: utf-8 -*-
"""Krok 4c: registrace LiDAR<->orto pres masku strechy (NCC pres posun, vektorizovane)."""
import json
import laspy
import numpy as np
from PIL import Image, ImageDraw

las = laspy.read("buildings_pl/ID-1465-38F62225-F3F5-F520-E053-CA2BA8C0BE14/body.las")
x, y, z = np.asarray(las.x), np.asarray(las.y), np.asarray(las.z)
c = np.asarray(las.classification)
sel = (c == 6) & (z > 110)
E0, N0, CS = 637060.0, 488230.0, 0.5
NX, NY = int(70 / CS), int(65 / CS)
lz = np.full((NY, NX), np.nan)
ix = ((x[sel] - E0) / CS).astype(int)
iy = ((y[sel] - N0) / CS).astype(int)
m = (ix >= 0) & (ix < NX) & (iy >= 0) & (iy < NY)
np.maximum.at(lz, (iy[m], ix[m]), z[sel][m]) if False else None
for i, j, zz in zip(ix[m], iy[m], z[sel][m]):
    if np.isnan(lz[j, i]) or zz > lz[j, i]:
        lz[j, i] = zz
roofmask = (lz > 115).astype(np.float32)
print("lidar roof pixelu: %d" % roofmask.sum())

im = Image.open("data_pl/warszawa_orto_200m_north.tif").convert("RGB")
A = np.array(im).astype(np.float32)
R, G, B = A[:, :, 0], A[:, :, 1], A[:, :, 2]
green = ((G - R > 12) & (G > 70) & (G < 175) & (B < 170)).astype(np.float32)
H, W = green.shape
print("orto green pixelu: %d" % green.sum())

# souradnice stredu lidar bunek
ccx = E0 + (np.arange(NX) + 0.5) * CS
ccy = N0 + (np.arange(NY) + 0.5) * CS
a = roofmask.ravel()
am = a.mean()
best = None
res = []
for dE in np.arange(-20, 20.5, 1.0):
    uu = ((ccx + dE - 636999.05) / 0.1).astype(int)
    okx = (uu >= 0) & (uu < W)
    for dN in np.arange(-20, 20.5, 1.0):
        vv = ((488361.95 - (ccy + dN)) / 0.1).astype(int)
        oky = (vv >= 0) & (vv < H)
        if okx.sum() < 20 or oky.sum() < 20:
            continue
        g = np.zeros((NY, NX), np.float32)
        g[np.ix_(np.where(oky)[0], np.where(okx)[0])] = green[vv[oky][:, None], uu[okx]]
        b = g.ravel()
        if b.std() < 1e-9:
            continue
        ncc = ((a - am) * (b - b.mean())).mean() / (a.std() * b.std() + 1e-9)
        res.append((float(ncc), float(dE), float(dN)))
        if best is None or ncc > best[0]:
            best = res[-1]
res.sort(reverse=True)
print("top5:", res[:5])
print("NCC nejlepsi: %.3f dE=%.0f dN=%.0f" % best)
json.dump(dict(ncc=best[0], dE=best[1], dN=best[2]),
          open("data_pl/west15_reg.json", "w", encoding="utf-8"), indent=1)

# kontrolni render: lidar roofmask (cervene body) pres orto s posunem
dE, dN = best[1], best[2]
ys, xs = np.where(roofmask > 0)
Ex = E0 + (xs + 0.5) * CS + dE
Nn = N0 + (ys + 0.5) * CS + dN
crop = im.crop((700, 750, 1250, 1250)).copy()
d = ImageDraw.Draw(crop)
for px, py in zip(Ex[::3], Nn[::3]):
    X = (px - 636999.05) / 0.1 - 700
    Y = (488361.95 - py) / 0.1 - 750
    if 0 <= X < crop.width and 0 <= Y < crop.height:
        d.rectangle([X - 1, Y - 1, X + 1, Y + 1], fill=(255, 0, 0))
crop = crop.resize((crop.width * 2, crop.height * 2), Image.NEAREST)
crop.save("render/pl_west15_reg.png")
print("ulozeno render/pl_west15_reg.png")
