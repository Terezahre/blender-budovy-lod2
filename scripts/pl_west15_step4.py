# -*- coding: utf-8 -*-
"""Krok 4b: layout 15 vikýru cislive.
Orto (svuj ramec): bile komponenty -> deleni podel okapu -> sheds + horni pas.
LiDAR (svuj ramec): boule res>0.8 -> 8+2 dolni; offset orto->lidar z poradi sheds.
Horni 5: orto pas u hrebene + offset -> snap na lidar bouli + vysky z LiDARu.
Vystup: data_pl/west15_layout.json + render/pl_west15_layout.png
"""
import json
import laspy
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
cc = np.array(poly.centroid.coords[0])
pw = np.array(info["planes"][info["west"]])
print("eave %.3f %.3f  perp %.3f %.3f" % (eave[0], eave[1], perp[0], perp[1]))

las = laspy.read(f"buildings_pl/{FID}/body.las")
x, y, z = np.asarray(las.x), np.asarray(las.y), np.asarray(las.z)
c = np.asarray(las.classification)
inside = np.array([poly.contains(Point(px, py)) for px, py in zip(x, y)])
roof = inside & (c == 6)
A = np.column_stack([x[roof], y[roof], np.ones(roof.sum())])
res = z[roof] - A @ pw
xr, yr, zr = x[roof], y[roof], z[roof]


def split_profile(vals, w, gap_bins=4, minn=6):
    """Rozdeleni hodnot na shluky podel osy: histogram + udoli."""
    lo, hi = vals.min() - 0.05, vals.max() + 0.05
    bins = np.arange(lo, hi, 0.15)
    prof, _ = np.histogram(vals, bins=bins)
    sm = ndi.gaussian_filter1d(prof.astype(float), 1.0)
    pk = sm.max()
    ismin = np.r_[False, (sm[1:-1] < sm[:-2]) & (sm[1:-1] <= sm[2:]) & (sm[1:-1] < pk * 0.35), False]
    cuts = sorted(np.where(ismin)[0].tolist())
    edges = [-1] + cuts + [len(prof) - 1]
    out = []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (vals >= bins[a + 1]) & (vals <= bins[min(b + 1, len(bins) - 1)])
        if m.sum() >= minn:
            out.append(m)
    return out


# --- LiDAR dolni rada: vysoke boule (res>0.8, s<-3) ---
t = (np.stack([xr, yr], 1) - cc) @ eave
s = (np.stack([xr, yr], 1) - cc) @ perp
tall = (res > 0.8) & (s < -3.0)
print("bodu res>0.8,s<-3: %d" % tall.sum())
tall_groups = split_profile(t[tall], None, minn=8)
print("skupin tall: %d" % len(tall_groups))
low = []
idx_all = np.where(tall)[0]
for m in tall_groups:
    idx = idx_all[m]
    Em, Nm = xr[idx].mean(), yr[idx].mean()
    low.append(dict(kind="tall", cx=float(Em), cy=float(Nm),
                    t=float(t[idx].mean()), s=float(s[idx].mean()),
                    w=float(t[idx].max() - t[idx].min() + 0.3),
                    ztop=float(np.quantile(zr[idx], 0.95)), n=int(len(idx))))
# male: res 0.25-0.8, s<-3, t<1
small = (res > 0.25) & (res <= 0.8) & (s < -3.0) & (t < 1.0)
print("bodu small: %d" % small.sum())
for m in split_profile(t[small], None, minn=5):
    idx = np.where(small)[0][m]
    Em, Nm = xr[idx].mean(), yr[idx].mean()
    low.append(dict(kind="small", cx=float(Em), cy=float(Nm),
                    t=float(t[idx].mean()), s=float(s[idx].mean()),
                    w=float(t[idx].max() - t[idx].min() + 0.3),
                    ztop=float(np.quantile(zr[idx], 0.95)), n=int(len(idx))))
low.sort(key=lambda d: d["t"])
for d in low:
    print("  LOW t=%+.1f s=%+.1f E=%.2f N=%.2f %s w=%.1f ztop=%.2f n=%d" % (
        d["t"], d["s"], d["cx"], d["cy"], d["kind"], d["w"], d["ztop"], d["n"]))

# --- Orto: bile komponenty (vlastni ramec TFW) ---
im = Image.open("data_pl/warszawa_orto_200m_north.tif").convert("RGB")
Arr = np.array(im).astype(np.float32)
mx, mn = Arr.max(axis=2), Arr.min(axis=2)
bright = (mx > 150) & ((mx - mn) < 80)
lab, n = ndi.label(bright, structure=np.ones((3, 3)))
H, W = bright.shape
yy, xx = np.mgrid[0:H, 0:W]
Eo = 636999.05 + 0.1 * xx
No = 488361.95 - 0.1 * yy
comps = []
for i in range(1, n + 1):
    ys, xs = np.where(lab == i)
    area = len(xs) * 0.01
    if not (0.6 < area < 120):
        continue
    Em, Nm = Eo[ys, xs].mean(), No[ys, xs].mean()
    if not poly.contains(Point(Em, Nm)):
        continue
    comps.append(dict(E=float(Em), N=float(Nm), area=float(area),
                      te=float(np.array([Em, Nm]) @ eave),
                      so=float(np.array([Em, Nm]) @ perp),
                      px=np.stack([Eo[ys, xs], No[ys, xs]], 1)))
print("orto komponent: %d" % len(comps))
# deleni velkych podel okapu
parts = []
for o in comps:
    P = o["px"]
    te = (P - P.mean(axis=0)) @ eave
    if o["area"] > 8:
        for m in split_profile(te, None, minn=8):
            Q = P[m]
            parts.append(dict(E=float(Q[:, 0].mean()), N=float(Q[:, 1].mean()),
                              area=float(len(Q) * 0.01),
                              te=float(Q[:, 0].mean() * eave[0] + Q[:, 1].mean() * eave[1]),
                              so=float(Q[:, 0].mean() * perp[0] + Q[:, 1].mean() * perp[1])))
    else:
        parts.append({k: o[k] for k in ("E", "N", "area", "te", "so")})
parts.sort(key=lambda d: -d["te"])
for i, o in enumerate(parts):
    print("  O%02d E=%.2f N=%.2f area=%.1f te=%+.1f so=%+.1f" % (i, o["E"], o["N"], o["area"], o["te"], o["so"]))
json.dump([{k: v for k, v in o.items()} for o in parts],
          open("data_pl/west15_orto.json", "w", encoding="utf-8"), indent=1)
