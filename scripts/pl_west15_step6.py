# -*- coding: utf-8 -*-
"""Krok 6: finalni layout 15 vikýru + graft do Geoflow modelu.
Dolni 10: 2 (shluk t~-1.3/+0.5) + 8 (t=3.2..15.8), horni 5 (t=-3.5,3.5,7.5,12.5,17.3).
Kazdy obdelnik: uhel = okap, W/D z bumpu, top = vlastni q95 LiDARu v miste.
Graft hranolu (kontrola containmentu) -> model_west15_graft.obj + metriky.
"""
import json
import laspy
import numpy as np
from shapely import wkt
from shapely.geometry import Point
from matplotlib.path import Path as MplPath

FID = "ID-1465-38F62225-F3F5-F520-E053-CA2BA8C0BE14"
poly = wkt.loads(json.load(open("data_pl/warszawa_gt.json", encoding="utf-8"))[FID]["footprint_wkt"])
info = json.load(open("data_pl/west15_clusters.json", encoding="utf-8"))
eave = np.array(info["eave"])
perp = np.array([-eave[1], eave[0]])
cc = np.array(poly.centroid.coords[0])
pw = np.array(info["planes"][info["west"]])
eang = info["eang"]
print("okap: %.1f deg" % eang)

las = laspy.read(f"buildings_pl/{FID}/body.las")
x, y, z = np.asarray(las.x), np.asarray(las.y), np.asarray(las.z)
c = np.asarray(las.classification)
inside = np.array([poly.contains(Point(px, py)) for px, py in zip(x, y)])
roof = inside & (c == 6)
A = np.column_stack([x[roof], y[roof], np.ones(roof.sum())])
res = z[roof] - A @ pw
xr, yr, zr = x[roof], y[roof], z[roof]
t = (np.stack([xr, yr], 1) - cc) @ eave
s = (np.stack([xr, yr], 1) - cc) @ perp


def bump_center(t0, s_lo, s_hi, r_lo, r_hi, dt=1.3):
    m = (t > t0 - dt) & (t < t0 + dt) & (s > s_lo) & (s < s_hi) & (res > r_lo) & (res < r_hi)
    idx = np.where(m)[0]
    if len(idx) < 5:
        return None
    return idx


def rect_of(idx):
    Em, Nm = xr[idx].mean(), yr[idx].mean()
    te = (np.stack([xr[idx], yr[idx]], 1) - [Em, Nm]) @ eave
    se = (np.stack([xr[idx], yr[idx]], 1) - [Em, Nm]) @ perp
    return Em, Nm, te, se, idx


th = np.radians(eang)
R = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
doms = []
# --- dolni 2 (shluk) ---
for t0, tag in [(-1.3, "L1"), (0.5, "L2")]:
    idx = bump_center(t0, -5.6, -3.4, 0.3, 2.2, dt=1.0)
    Em, Nm, te, se, idx = rect_of(idx)
    Wm = round(float(te.max() - te.min() + 0.2), 2)
    Dm = 1.8
    zt = float(np.quantile(zr[idx], 0.95))
    doms.append(dict(id=tag, row="lower", cx=round(float(Em), 2), cy=round(float(Nm), 2),
                      W=Wm, D=Dm, ztop=round(zt, 2), n=int(len(idx))))
# --- dolni 8 ---
for i, t0 in enumerate([3.2, 5.0, 6.8, 8.5, 10.3, 12.1, 14.0, 15.8], start=3):
    idx = bump_center(t0, -5.6, -3.4, 0.5, 2.4, dt=1.0)
    Em, Nm, te, se, idx = rect_of(idx)
    Wm = round(float(min(te.max() - te.min() + 0.2, 2.4)), 2)
    Dm = 1.8
    zt = float(np.quantile(zr[idx], 0.95))
    doms.append(dict(id="L%d" % i, row="lower", cx=round(float(Em), 2), cy=round(float(Nm), 2),
                      W=Wm, D=Dm, ztop=round(zt, 2), n=int(len(idx))))
# --- horni 5+1 (U0 pribyl: chybejici vikýř na SZ, 98 % bily v ortu) ---
for i, t0 in enumerate([-16.5, -3.5, 3.5, 7.5, 12.5, 17.3]):
    tag = "U0" if i == 0 else "U%d" % i
    dt = 0.9 if t0 == 17.3 else 1.2
    idx = bump_center(t0, -3.0, -0.5, 0.35, 1.35, dt=dt)
    Em, Nm, te, se, idx = rect_of(idx)
    Wm = round(float(min(max(te.max() - te.min() + 0.2, 1.0), 2.0)), 2)
    Dm = 1.5
    zt = float(np.quantile(zr[idx], 0.95))
    doms.append(dict(id=tag, row="upper", cx=round(float(Em), 2), cy=round(float(Nm), 2),
                      W=Wm, D=Dm, ztop=round(zt, 2), n=int(len(idx))))

# obdelniky: stred + uhel okapu + prave uhly
for d in doms:
    box = (np.array([[d["W"], d["D"]], [-d["W"], d["D"]], [-d["W"], -d["D"]], [d["W"], -d["D"]]]) / 2) @ R.T
    cc_ = np.array([d["cx"], d["cy"]])
    a, b, c0 = pw
    zt = a * cc_[0] + b * cc_[1] + c0
    c0t = c0 + (d["ztop"] - zt)
    zbase = a * cc_[0] + b * cc_[1] + c0 - 0.3
    rect = cc_ + box
    d["rect"] = [[round(float(p[0]), 2), round(float(p[1]), 2)] for p in rect]
    d["top_plane"] = [float(a), float(b), float(c0t)]
    d["base_z"] = round(float(zbase), 2)
    print("%s %s: E=%.2f N=%.2f W=%.2fx%.2f top=%.2f base=%.2f n=%d" % (
        d["id"], d["row"], d["cx"], d["cy"], d["W"], d["D"], d["ztop"], d["base_z"], d["n"]))
json.dump(doms, open("data_pl/west15_layout.json", "w", encoding="utf-8"), indent=1)
print("vikyru: %d -> data_pl/west15_layout.json" % len(doms))


def load_obj(p):
    V, F = [], []
    for line in open(p, encoding="utf-8"):
        if line.startswith("v "):
            V.append([float(v) for v in line.split()[1:4]])
        elif line.startswith("f "):
            F.append([int(v.split("/")[0]) - 1 for v in line.split()[1:]])
    return np.array(V, dtype=float), [list(map(int, f)) for f in F]


Vold, Fold = load_obj(f"output/pl_geof/{FID}/model_lod22.obj")

# --- 5b. srovnani celeho pasu: vsechny vrcholy s res>0.15 v pasu
# (t -19..19.5, s -6.2..-0.2) se polozi na zapadni rovinu: jehly kolem vikýru,
# stromovy trn u dvojshluku (t~-10.8) i koruna v SZ rohu (t -16..-17, class-6
# chyba nad parkovistem - GT polygon tam zasahuje, strecha zustava).
# 5d. stejne okapy Z/V: viz nize za 5c (potrebuje tV/sV).
Vold = np.array(Vold, dtype=float)
tV = (Vold[:, :2] - cc) @ eave
sV = (Vold[:, :2] - cc) @ perp
pe = np.array(info["planes"][0])
band = (tV > -19.0) & (tV < 19.5) & (sV > -6.2) & (sV < -0.2)
resv = Vold[:, 2] - (pw[0] * Vold[:, 0] + pw[1] * Vold[:, 1] + pw[2])
tall = band & (resv > 0.15)
Vold[tall, 2] = (pw[0] * Vold[tall, 0] + pw[1] * Vold[tall, 1] + pw[2])
print("srovnano jehel v zapadnim pasu: %d vrcholu" % int(tall.sum()))
bande = (tV > -19.0) & (tV < 19.5) & (sV > 4.0) & (sV < 6.3)
# 5c. vychodni okap: CAP na refit+0.35 (misto srovnani na rovinu).
# Rotace ZRUSENA (mrak ma okapy prirozene nesoumerne). Cap smaze jen
# Geoflow prehnuti (>0.35 nad rovinou), prirozeny ret ~0.3 zustava.
# Hreben zustava, zapad vcetne 16 vikýru beze zmen.
gmed = float(np.median(z[(~inside) & (c == 2)]))
s_all = (np.stack([x[inside], y[inside]], 1) - cc) @ perp
rsel = np.zeros(len(x), bool)
rsel[inside] = (s_all > 0.5) & (s_all < 4.5) & (z[inside] > gmed + 1.5)
rsel = rsel & (c == 6)
A_ = np.column_stack([x[rsel], y[rsel], np.ones(int(rsel.sum()))])
peN, *_ = np.linalg.lstsq(A_, z[rsel], rcond=None)
rese = Vold[:, 2] - (peN[0] * Vold[:, 0] + peN[1] * Vold[:, 1] + peN[2])
talle = bande & (rese > 0.35)
Vold[talle, 2] = (peN[0] * Vold[talle, 0] + peN[1] * Vold[talle, 1] + peN[2] + 0.35)
print("refit vychod (n=%d); capnuto prestrelenych: %d vrcholu" % (
    int(rsel.sum()), int(talle.sum())))
# 5d ZHRUSENO (rotace vychodu): mrak ma okapy prirozene nesoumerne.
FLAT = f"output/pl_geof/{FID}/model_west15_flat.obj"
with open(FLAT, "w", encoding="utf-8") as f:
    f.write("# Geoflow LOD22 + srovnane okoli 15 vikýru (rezerva pro boolean)\n")
    for v in Vold:
        f.write("v %.3f %.3f %.3f\n" % tuple(v))
    for fa in Fold:
        if len(fa) == 4:
            # triangulace quadu (kratsi diagonalou): boolean-safe, zadne bowtie
            P = Vold[np.array(fa)]
            d02 = float(np.linalg.norm(P[0] - P[2]))
            d13 = float(np.linalg.norm(P[1] - P[3]))
            if d02 <= d13:
                f.write("f %d %d %d\n" % (fa[0] + 1, fa[1] + 1, fa[2] + 1))
                f.write("f %d %d %d\n" % (fa[0] + 1, fa[2] + 1, fa[3] + 1))
            else:
                f.write("f %d %d %d\n" % (fa[0] + 1, fa[1] + 1, fa[3] + 1))
                f.write("f %d %d %d\n" % (fa[1] + 1, fa[2] + 1, fa[3] + 1))
        else:
            f.write("f " + " ".join(str(i + 1) for i in fa) + "\n")
print("zapsano", FLAT)


def mesh_z_at(V, F, xy):
    out = np.full(len(xy), np.nan)
    for f in F:
        P = V[np.array(f)]
        tris = [(P[0], P[i], P[i + 1]) for i in range(1, len(P) - 1)] if len(P) > 3 else [tuple(P)]
        for A_, B_, C_ in tris:
            v0, v1 = C_ - A_, B_ - A_
            den = (v1[:2] @ v1[:2]) * (v0[:2] @ v0[:2]) - (v1[:2] @ v0[:2]) ** 2
            if abs(den) < 1e-12:
                continue
            dd = xy - A_[:2]
            u = ((v1[:2] @ v1[:2]) * (dd @ v0[:2]) - (v1[:2] @ v0[:2]) * (dd @ v1[:2])) / den
            v = ((v0[:2] @ v0[:2]) * (dd @ v1[:2]) - (v1[:2] @ v0[:2]) * (dd @ v0[:2])) / den
            hit = (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9)
            if hit.any():
                zz = A_[2] + u * v0[2] + v * v1[2]
                mm = hit & (np.isnan(out) | (zz > out))
                out[mm] = zz[mm]
    return out


def oldmax_in_rect(rect):
    gx = np.linspace(rect[:, 0].min(), rect[:, 0].max(), 12)
    gy = np.linspace(rect[:, 1].min(), rect[:, 1].max(), 12)
    GX, GY = np.meshgrid(gx, gy)
    return float(np.nanmax(mesh_z_at(Vold, Fold, np.stack([GX.ravel(), GY.ravel()], 1))))


verts = Vold.tolist()
faces = [list(f) for f in Fold]
used = []
for d in doms:
    cc_ = np.array([d["cx"], d["cy"]])
    a, b, c0t = d["top_plane"]
    base_rect = np.array(d["rect"])
    for k in (1.0, 1.15, 1.3, 1.5, 1.8):
        rect = cc_ + (base_rect - cc_) * k
        topmin = float(min(a * px + b * py + c0t for px, py in rect))
        om = oldmax_in_rect(rect)
        if om <= topmin + 0.05:
            break
    zb = d["base_z"]
    n0 = len(verts)
    for px, py in rect:
        verts.append([float(px), float(py), zb])
    for px, py in rect:
        verts.append([float(px), float(py), a * px + b * py + c0t])
    B = [n0, n0 + 1, n0 + 2, n0 + 3]
    Tp = [n0 + 4, n0 + 5, n0 + 6, n0 + 7]
    faces.append([B[0], B[3], B[2], B[1]])
    for i in range(4):
        j = (i + 1) % 4
        faces.append([B[i], B[j], Tp[j], Tp[i]])
    faces.append([Tp[0], Tp[1], Tp[2], Tp[3]])
    used.append(rect)
    print("%s: expanze %.2f, stary max %.2f vs top %.2f %s" % (
        d["id"], k, om, topmin, "OK" if om <= topmin + 0.05 else "PRESAHUJE"))
    d["expansion"] = k
V2 = np.array(verts, dtype=float)
OUT = f"output/pl_geof/{FID}/model_west15_graft.obj"
with open(OUT, "w", encoding="utf-8") as f:
    f.write("# Geoflow + 15 vikýru zapadni svah (liDAR vysky)\n")
    for v in V2:
        f.write("v %.3f %.3f %.3f\n" % tuple(v))
    for fa in faces:
        f.write("f " + " ".join(str(i + 1) for i in fa) + "\n")

from collections import Counter
ec = Counter()
for f_ in faces:
    tris = [[f_[0], f_[i], f_[i + 1]] for i in range(1, len(f_) - 1)] if len(f_) > 3 else [f_]
    for t_ in tris:
        for e_ in ((t_[0], t_[1]), (t_[1], t_[2]), (t_[2], t_[0])):
            ec[tuple(sorted(e_))] += 1
nm = sum(1 for v in ec.values() if v != 2)
core = np.array([poly.buffer(-1.0).contains(Point(px, py)) for px, py in zip(xr, yr)])
in_d = np.zeros(len(xr), bool)
for rect in used:
    in_d |= MplPath(rect).contains_points(np.stack([xr, yr], 1))
json.dump(doms, open("data_pl/west15_layout.json", "w", encoding="utf-8"), indent=1)
for tag, (VV, FF) in {"lod22": (Vold, Fold), "west15": (V2, faces)}.items():
    mz = mesh_z_at(np.array(VV, dtype=float), FF, np.stack([xr, yr], 1))
    cov = ~np.isnan(mz)
    rmse = float(np.sqrt(((zr[cov] - mz[cov]) ** 2).mean())) if cov.any() else -1
    mc = core & cov
    rmsec = float(np.sqrt(((zr[mc] - mz[mc]) ** 2).mean())) if mc.any() else -1
    md = in_d & cov
    rmsed = float(np.sqrt(((zr[md] - mz[md]) ** 2).mean())) if md.any() else -1
    print("%s: RMSE=%.3f m (jadro %.3f, vikýře %.3f) pokryti=%.2f %s" % (
        tag, rmse, rmsec, rmsed, cov.mean(), ("nm=%d" % nm) if tag == "west15" else ""))
print("zapsano", OUT, "verts=%d faces=%d" % (len(V2), len(faces)))
