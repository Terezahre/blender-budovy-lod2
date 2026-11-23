# -*- coding: utf-8 -*-
"""Krok 2b: detekce bilych vikýru na CELEM footprintu + filtr vyskou z LiDARu.
Bile komponenty (0.5-80 m2) -> median Z z LiDARu v boxu (musi byt streecha,
tim padnou silnicni cary/auta) -> strana hrebene z PRUSECIKU K-rovin
(ne centroid!) -> jen zapadni strana. Merged rady se stepi profilem podel okapu.
Vystup: render/pl_west15_white.png + data_pl/west15_white.json
"""
import json
import laspy
import numpy as np
from PIL import Image, ImageDraw
from shapely import wkt
from shapely.geometry import Point, box as sbox
from scipy import ndimage as ndi

FID = "ID-1465-38F62225-F3F5-F520-E053-CA2BA8C0BE14"
poly = wkt.loads(json.load(open("data_pl/warszawa_gt.json", encoding="utf-8"))[FID]["footprint_wkt"])
info = json.load(open("data_pl/west15_clusters.json", encoding="utf-8"))
eave = np.array(info["eave"])
perp = np.array([-eave[1], eave[0]])
cc = np.array(poly.centroid.coords[0])
p0 = np.array(info["planes"][0])
p1 = np.array(info["planes"][1])
# hreeben = prusecik rovin: p0-p1 = 0 -> bod + smer okap
dd = np.array([p0[0] - p1[0], p0[1] - p1[1]])
t = -((dd @ cc) + (p0[2] - p1[2])) / (dd @ perp)
r0 = cc + t * perp
print("hreeben bod: %.2f %.2f" % (r0[0], r0[1]))

las = laspy.read(f"buildings_pl/{FID}/body.las")
x, y, z = np.asarray(las.x), np.asarray(las.y), np.asarray(las.z)
c = np.asarray(las.classification)
gmed = float(np.median(z[c == 2]))
print("teren: %.2f" % gmed)

im = Image.open("data_pl/warszawa_orto_200m_north.tif").convert("RGB")
A = np.array(im).astype(np.float32)
H, W = A.shape[:2]
yy, xx = np.mgrid[0:H, 0:W]
E = 636999.05 + 0.1 * xx
N = 488361.95 - 0.1 * yy
Ef, Nf = E.ravel(), N.ravel()
inside = np.array([poly.contains(Point(px, py)) for px, py in zip(Ef, Nf)]).reshape(H, W)
print("pixelu ve footprintu:", int(inside.sum()))
mx, mn = A.max(axis=2), A.min(axis=2)
bright = (mx > 160) & ((mx - mn) < 70) & inside
lab, n = ndi.label(bright)
print("komponentu:", n)
cands = []
for i in range(1, n + 1):
    ys, xs = np.where(lab == i)
    area = len(xs) * 0.01
    if not (0.5 < area < 80):
        continue
    Em, Nm = E[ys, xs].mean(), N[ys, xs].mean()
    sel = (np.abs(x - Em) < 2.5) & (np.abs(y - Nm) < 2.5) & (c == 6)
    if sel.sum() < 5:
        continue
    zmed = float(np.median(z[sel]))
    cands.append(dict(cx=round(float(Em), 2), cy=round(float(Nm), 2),
                      area=round(float(area), 2), nlas=int(sel.sum()),
                      zmed=round(zmed, 2), px=np.stack([E[ys, xs], N[ys, xs]], 1)))
print("bilyCH komponent s lidarem: %d" % len(cands))
for o in cands:
    print("  E=%.2f N=%.2f area=%.1f nlas=%d zmed=%.2f %s" % (
        o["cx"], o["cy"], o["area"], o["nlas"], o["zmed"],
        "STRECHA" if o["zmed"] > gmed + 1.5 else "prizem"))
roof_c = [o for o in cands if o["zmed"] > gmed + 1.5]
# strana hreebene
for o in roof_c:
    o["side"] = float((np.array([o["cx"], o["cy"]]) - r0) @ perp)
    o["t"] = float((np.array([o["cx"], o["cy"]]) - cc) @ eave)
# zapad = ktera strana? normala WEST roviny ukazuje ven ze svahu
pw = np.array(info["planes"][info["west"]])
nh = np.array([-pw[0], -pw[1]])
nh /= np.linalg.norm(nh)
print("WEST normala_h:", nh, " perp:", perp, " -> zapad je strana", "s<0" if (nh @ perp) < 0 else "s>0")
west_c = [o for o in roof_c if o["side"] * (nh @ perp) > 0]
print("komponent na zapade: %d" % len(west_c))

# stepeni velkych komponent podel okapu (jasovy profil)
objs = []
for o in west_c:
    P = o["px"]
    te = (P - cc) @ eave
    bins = np.arange(te.min(), te.max() + 0.15, 0.1)
    if len(bins) < 5:
        objs.append(o)
        continue
    prof, _ = np.histogram(te, bins=bins)
    # vyhladit + najit udoli (mezery mezi vikýři)
    sm = ndi.gaussian_filter1d(prof.astype(float), 1.0)
    # minima hlubsi nez 40 % maxima = delici cary
    thr = sm.max() * 0.4
    ismin = np.r_[False, (sm[1:-1] < sm[:-2]) & (sm[1:-1] <= sm[2:]) & (sm[1:-1] < thr), False]
    cuts = sorted(np.where(ismin)[0].tolist())
    # priradit body do useku mezi rezy
    edges = [0] + [c + 1 for c in cuts] + [len(prof)]
    parts = []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (te >= bins[a]) & (te < bins[min(b, len(bins) - 1)])
        if m.sum() * 0.01 >= 0.5:
            parts.append(m)
    if len(parts) <= 1:
        objs.append(o)
        continue
    for m in parts:
        Q = P[m]
        Em, Nm = Q[:, 0].mean(), Q[:, 1].mean()
        PE = Q - [Em, Nm]
        we = PE @ eave
        wp = PE @ perp
        objs.append(dict(cx=round(float(Em), 2), cy=round(float(Nm), 2),
                         area=round(float(m.sum() * 0.01), 2), nlas=o["nlas"],
                         zmed=o["zmed"],
                         t=round(float((np.array([Em, Nm]) - cc) @ eave), 2),
                         side=round(float((np.array([Em, Nm]) - r0) @ perp), 2)))
    print("  stepeno E=%.2f N=%.2f na %d casti" % (o["cx"], o["cy"], len(parts)))
objs.sort(key=lambda d: -d["t"])
for k, o in enumerate(objs):
    sel = (np.abs(x - o["cx"]) < 1.2) & (np.abs(y - o["cy"]) < 1.2) & (c == 6)
    o["zq90"] = round(float(np.quantile(z[sel], 0.9)), 2) if sel.sum() >= 5 else None
    print("%2d: E=%.2f N=%.2f area=%.1f zmed=%.2f zq90=%s t=%+.1f s=%+.1f" % (
        k, o["cx"], o["cy"], o["area"], o["zmed"], o["zq90"], o["t"], o["side"]))
    o.pop("px", None)
json.dump(objs, open("data_pl/west15_white.json", "w", encoding="utf-8"), indent=1)

minx, miny, maxx, maxy = poly.bounds
ua, va = (minx - 636999.05) / 0.1, (488361.95 - maxy) / 0.1
ub, vb = (maxx - 636999.05) / 0.1, (488361.95 - miny) / 0.1
crop = im.crop((int(ua) - 15, int(va) - 15, int(ub) + 15, int(vb) + 15))
S = 3
crop = crop.resize((crop.width * S, crop.height * S), Image.LANCZOS)
d = ImageDraw.Draw(crop)
xs, ys = poly.exterior.coords.xy
d.line([(((EE - 636999.05) / 0.1 - (int(ua) - 15)) * S,
         ((488361.95 - NN) / 0.1 - (int(va) - 15)) * S)
        for EE, NN in zip(xs, ys)], fill=(255, 0, 0), width=2)
for k, o in enumerate(objs):
    u, v = (o["cx"] - 636999.05) / 0.1, (488361.95 - o["cy"]) / 0.1
    X, Y = (u - (int(ua) - 15)) * S, (v - (int(va) - 15)) * S
    d.ellipse([X - 16, Y - 16, X + 16, Y + 16], outline=(0, 255, 0), width=2)
    d.text((X + 18, Y - 10), "%d" % k, fill=(0, 255, 0))
crop.save("render/pl_west15_white.png")
print("ulozeno render/pl_west15_white.png", crop.size)
