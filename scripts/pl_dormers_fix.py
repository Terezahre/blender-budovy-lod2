# -*- coding: utf-8 -*-
"""PL dum: automaticka oprava vikýru z ortofota + LiDARu.
Resi 3 pozadavky: stejne uhly (snap na okap + prave uhly), stejna vyska
v ramci svahu (median), spravny pocet (LiDAR + kontrola z orta).

Vstupy: buildings_pl/<FID>/body.las, data_pl/warszawa_gt.json,
        data_pl/dormers.json (LiDAR shluky), data_pl/warszawa_orto_200m.tif,
        output/pl_geof/<FID>/model_lod22.obj
Vystupy: data_pl/dormers_fixed.json, output/pl_geof/<FID>/model_fixed.obj,
         render/pl_dormers_overlay.png, render/pl_dormers_profiles.png

Orto slouzi jen relativne (rada/roztec/pocet); absolutni vysky z LiDARu.
Klasicke orto ma posun zástinem ~2-4 m kolmo na okap -> vzorkovaci pas,
profil podel okapu je na kolmy posun necitlivy.
"""
import json

import laspy
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from shapely import wkt
from shapely.geometry import Point

FID = "ID-1465-38F62225-F3F5-F520-E053-CA2BA8C0BE14"
E0, N0, SP = 636999.0, 488162.0, 200.0  # okno TIFF/JPG, mapovani C
RNG = np.random.default_rng(7)


def fit_plane(P):
    A = np.column_stack([P[:, 0], P[:, 1], np.ones(len(P))])
    coef, *_ = np.linalg.lstsq(A, P[:, 2], rcond=None)
    return coef


def ransac_plane(P, thresh=0.25, iters=800):
    # centrovano kuli stabilite (souradnice ~6e5)
    m = P[:, :2].mean(axis=0)
    Q = P.copy()
    Q[:, 0] -= m[0]
    Q[:, 1] -= m[1]
    best, best_in = None, np.zeros(len(P), bool)
    for _ in range(iters):
        s = RNG.choice(len(P), 3, replace=False)
        S = Q[s]
        n = np.cross(S[1] - S[0], S[2] - S[0])
        if np.linalg.norm(n) < 1e-9:
            continue
        A = np.column_stack([S[:, 0], S[:, 1], np.ones(3)])
        coef, *_ = np.linalg.lstsq(A, S[:, 2], rcond=None)
        r = np.abs(np.column_stack([Q[:, 0], Q[:, 1], np.ones(len(Q))]) @ coef - Q[:, 2])
        inn = r < thresh
        if inn.sum() > best_in.sum():
            best, best_in = coef, inn
    a, b, c0 = best
    # zpet do puvodnich souradnic: z = a*(x-mx)+b*(y-my)+c
    return np.array([a, b, c0 - a * m[0] - b * m[1]]), best_in


def load_obj(p):
    V, F = [], []
    for line in open(p, encoding="utf-8"):
        if line.startswith("v "):
            V.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("f "):
            F.append([int(x.split("/")[0]) - 1 for x in line.split()[1:]])
    return np.array(V), F


def mesh_z_at(V, F, xy):
    out = np.full(len(xy), np.nan)
    for f in F:
        P = V[np.array(f)]
        tris = [(P[0], P[i], P[i + 1]) for i in range(1, len(P) - 1)] if len(P) > 3 else [tuple(P)]
        for A, B, C in tris:
            v0, v1 = C - A, B - A
            den = (v1[:2] @ v1[:2]) * (v0[:2] @ v0[:2]) - (v1[:2] @ v0[:2]) ** 2
            if abs(den) < 1e-12:
                continue
            d = xy - A[:2]
            u = ((v1[:2] @ v1[:2]) * (d @ v0[:2]) - (v1[:2] @ v0[:2]) * (d @ v1[:2])) / den
            v = ((v0[:2] @ v0[:2]) * (d @ v1[:2]) - (v1[:2] @ v0[:2]) * (d @ v0[:2])) / den
            hit = (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9)
            if hit.any():
                z = A[2] + u * v0[2] + v * v1[2]
                m = hit & (np.isnan(out) | (z > out))
                out[m] = z[m]
    return out


# --- 1. LiDAR: 2 hlavni roviny strechy -------------------------------------
las = laspy.read(f"buildings_pl/{FID}/body.las")
x, y, z = np.asarray(las.x), np.asarray(las.y), np.asarray(las.z)
c = np.asarray(las.classification)
poly = wkt.loads(json.load(open("data_pl/warszawa_gt.json", encoding="utf-8"))[FID]["footprint_wkt"])
inside = np.array([poly.contains(Point(px, py)) for px, py in zip(x, y)])
roof = np.column_stack([x[inside & (c == 6)], y[inside & (c == 6)], z[inside & (c == 6)]])
gmed = np.median(z[(~inside) & (c == 2)]) if ((~inside) & (c == 2)).any() else np.median(z[c == 2])
roof = roof[roof[:, 2] > gmed + 1.5]
print("roof pts: %d, teren med: %.2f" % (len(roof), gmed))

# --- 1. Hlavni roviny: RANSAC init + K-planes refit (2025 lidar) ------------
# Sekvencni RANSAC necha 2. rovinu naklonenou primysi vikýřů;
# K-planes (assign + refit na bodech do 0.5 m) to srovna.
c1, in1 = ransac_plane(roof)
c2, _ = ransac_plane(roof[~in1])  # init na zbytku: zachyti druhy svah
m = roof[:, :2].mean(axis=0)


def _fit(Q):
    B = np.column_stack([Q[:, 0] - m[0], Q[:, 1] - m[1], np.ones(len(Q))])
    s, *_ = np.linalg.lstsq(B, Q[:, 2], rcond=None)
    return np.array([s[0], s[1], s[2] - s[0] * m[0] - s[1] * m[1]])


for _it in range(10):
    A = np.column_stack([roof[:, 0], roof[:, 1], np.ones(len(roof))])
    r1 = np.abs(A @ c1 - roof[:, 2])
    r2 = np.abs(A @ c2 - roof[:, 2])
    best = np.minimum(r1, r2)
    m1 = (r1 <= r2) & (best < 0.5)
    m2 = (r2 < r1) & (best < 0.5)
    if m1.sum() < 50 or m2.sum() < 50:
        break
    c1, c2 = _fit(roof[m1]), _fit(roof[m2])
planes = [c1, c2]
for i, p in enumerate(planes):
    r = np.abs(np.column_stack([roof[:, 0], roof[:, 1], np.ones(len(roof))]) @ p - roof[:, 2])
    print("K-planes rovina%d: z=%.4f*x%+.4f*y%+.2f inliers<0.25m: %d/%d" % (
        i + 1, p[0], p[1], p[2], int((r < 0.25).sum()), len(roof)))
n1 = np.array([-c1[0], -c1[1], 1.0]); n1 /= np.linalg.norm(n1)
n2 = np.array([-c2[0], -c2[1], 1.0]); n2 /= np.linalg.norm(n2)
ridge = np.cross(n1, n2); ridge /= np.linalg.norm(ridge)
eave = ridge.copy(); eave[2] = 0.0; eave /= np.linalg.norm(eave)
eang = float(np.degrees(np.arctan2(eave[1], eave[0])))
print("smer okapu: %.1f deg" % eang)

# --- 2. Vikýře -> svah, sjednoceni ----------------------------------------
ds = json.load(open("data_pl/dormers.json", encoding="utf-8"))
# strana svahu se urcuje GEOMETRICKY (znaminko od hrebene), ne vyskou:
# base_z ve vstupu je odvozena ze GT (jina epocha, ~5 m mimo) a hazi residua.
perp = np.array([-eave[1], eave[0]])
c0 = np.array(poly.centroid.coords[0])
dd = np.array([c1[0] - c2[0], c1[1] - c2[1]])
t = -((dd @ c0) + (c1[2] - c2[2])) / (dd @ perp)
r0 = c0 + t * perp
for d in ds:
    side = float((np.array([d["cx"], d["cy"]]) - r0) @ perp)
    d["slope"] = 0 if side >= 0 else 1
    d["side_m"] = round(side, 1)
    zb = d["base_z"] + 0.5
    r = [abs(p[0] * d["cx"] + p[1] * d["cy"] + p[2] - zb) for p in planes]
    print("vikýř (%.1f, %.1f): strana %+.1f m -> svah %d (residua %.2f/%.2f)" % (
        d["cx"], d["cy"], side, d["slope"], r[0], r[1]))

fixed = []
for s in (0, 1):
    grp = [d for d in ds if d["slope"] == s]
    if not grp:
        continue
    # podtypy: kdyz se vysky v ramci svahu lisi > 1 m (velky x maly vikýř),
    # rozdel podle nejvetsi mezery v top (plochejsi velke vs vyssi male)
    grp = sorted(grp, key=lambda d: d["top_z"])
    gaps = [grp[i + 1]["top_z"] - grp[i]["top_z"] for i in range(len(grp) - 1)]
    subs = [grp]
    if gaps and max(gaps) > 1.0:
        k = int(max(range(len(gaps)), key=lambda i: gaps[i])) + 1
        subs = [grp[:k], grp[k:]]
        print("svah %d: deleni na %d podtypy (mezera %.2f m)" % (s, len(subs), max(gaps)))
    for gi, sub in enumerate(subs):
        base = float(np.median([d["base_z"] for d in sub]))
        top = float(np.median([d["top_z"] for d in sub]))
        # sjednocena sirka/hloubka v ramci podtypu: delsi strana = podel okapu
        sizes = []
        for d in sub:
            r = np.array(d["rect"])
            e = np.linalg.norm(r - np.roll(r, -1, axis=0), axis=1)
            sizes.append((max(e[0], e[1]), min(e[0], e[1])))
        Wm = float(np.median([a for a, _ in sizes]))
        Dm = float(np.median([b for _, b in sizes]))
        th = np.radians(eang)
        R = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
        box = (np.array([[Wm, Dm], [-Wm, Dm], [-Wm, -Dm], [Wm, -Dm]]) / 2) @ R.T
        cp = np.array(planes[s])  # hlavni rovina svahu
        for d in sub:
            cc = np.array([d["cx"], d["cy"]])
            rect = cc + box
            # horni rovina rovnobezna se svahem, posunuta na median top
            zt = cp @ np.array([cc[0], cc[1], 1.0])
            cpt = cp.copy(); cpt[2] += (top - zt)
            fixed.append(dict(cx=round(float(cc[0]), 2), cy=round(float(cc[1]), 2),
                              slope=s, subtype=gi,
                              rect=[[round(float(p[0]), 2), round(float(p[1]), 2)] for p in rect],
                              base_z=base, top_z=top,
                              top_plane=[float(v) for v in cpt],  # NIKDY nezaokrouhlovat: 1e-4 v gradientu = desitky m!
                              w_m=round(Wm, 2), d_m=round(Dm, 2),
                          old_base=d["base_z"], old_top=d["top_z"]))
        print("svah %d%s: n=%d base %.2f top %.2f W %.2fx%.2f m" % (
            s, "" if len(subs) == 1 else "/t%d" % gi, len(sub), base, top, Wm, Dm))

json.dump(fixed, open("data_pl/dormers_fixed.json", "w", encoding="utf-8"), indent=1)
print("vikýřů po sjednoceni: %d -> data_pl/dormers_fixed.json" % len(fixed))

# --- 3. Kontrola poctu z orta (1D profil podel okapu) ----------------------
ort = np.array(Image.open("data_pl/warszawa_orto_200m.tif").convert("RGB"), dtype=np.float32)
H, W = ort.shape[:2]
gray = ort.mean(axis=2)
minx, miny, maxx, maxy = poly.bounds
ex = eave[:2]
perp = np.array([-ex[1], ex[0]])
cc = np.array(poly.centroid.coords[0])
L = float(max(maxx - minx, maxy - miny)) + 24
t = np.arange(-L / 2, L / 2, 0.2)
fig, ax = plt.subplots(2, 1, figsize=(12, 7))
peaks_info = []
for s in (0, 1):
    profs = []
    for off in (-2.0, 0.0, 2.0):  # pas 4 m kolmo na okap = odolnost vuci zástinu
        pts = cc + np.outer(t, ex) + (s - 0.5) * 6.0 * perp + off * perp
        u = (pts[:, 0] - E0) / SP * W
        v = (pts[:, 1] - N0) / SP * H
        m = (u >= 0) & (u < W) & (v >= 0) & (v < H)
        pr = np.full_like(t, np.nan)
        pr[m] = gray[v[m].astype(int).clip(0, H - 1), u[m].astype(int).clip(0, W - 1)]
        profs.append(pr)
    prof = np.nanmean(profs, axis=0)
    sm = np.convolve(prof, np.ones(9) / 9, mode="same")
    med, sd = np.nanmedian(sm), np.nanstd(sm)
    # tmave vikýře = minima, světlá okna = maxima
    dark = (sm < med - 0.7 * sd)
    ids = np.where(dark)[0]
    groups, cur = [], []
    for i in ids:
        if cur and i - cur[-1] > 10:  # > 2 m rozestup
            groups.append(cur); cur = []
        cur.append(i)
    if cur:
        groups.append(cur)
    pk = [float(t[int(np.mean(g))]) for g in groups if 3 <= len(g) <= 40]
    # jen uvnitr prumetu footprintu na osu okapu
    pc = np.array(poly.exterior.coords)[:, :2]
    tp = (pc - cc) @ ex
    pk = [p for p in pk if tp.min() <= p <= tp.max()]
    peaks_info.append((s, pk))
    a = ax[s]
    a.plot(t, sm, lw=0.8)
    a.axhline(med, c="k", ls="--", lw=0.8)
    a.axhline(med - 0.7 * sd, c="r", ls=":", lw=0.8)
    for p in pk:
        a.axvline(p, c="g", lw=1.2)
    for d in [f for f in fixed if f["slope"] == s]:
        a.axvline((np.array([d["cx"], d["cy"]]) - cc) @ ex, c="b", ls="--", lw=1.2)
    a.set_title(f"svah {s}: zelená=orto minima (tmavé vikýře), modrá=LiDAR, n_lidar={sum(1 for f in fixed if f['slope']==s)}")
for s, pk in peaks_info:
    print("svah %d: orto tmavych peaku=%d, lidar vikýřů=%d" % (s, len(pk), sum(1 for f in fixed if f["slope"] == s)))
plt.tight_layout()
plt.savefig("render/pl_dormers_profiles.png", dpi=100)
print("ulozeno render/pl_dormers_profiles.png")

# --- 4. Graft: regularizovane vikýře na Geoflow mesh ----------------------
# Zamerne NEMAZEME puvodni bunky a nestavime strechu znovu: Geoflow mesh
# sedi na datech (jadro 0.52 m), 2-rovina by ho zhorsila (K=4 kryje jen 75 %).
# Hranoly obsahuji stare boule uvnitr (kontrola containmentu) -> zadne diry,
# manifold zustava. Volitelny boolean-union az v Blenderu (navaznost).
from matplotlib.path import Path as MplPath

Vold, Fold = load_obj(f"output/pl_geof/{FID}/model_lod22.obj")
Fold = [list(map(int, f)) for f in Fold]
Vold = np.array(Vold, dtype=float)


def oldmax_in_rect(rect):
    gx = np.linspace(rect[:, 0].min(), rect[:, 0].max(), 12)
    gy = np.linspace(rect[:, 1].min(), rect[:, 1].max(), 12)
    GX, GY = np.meshgrid(gx, gy)
    return float(np.nanmax(mesh_z_at(Vold, Fold, np.column_stack([GX.ravel(), GY.ravel()]))))


verts = Vold.tolist()
faces = [list(f) for f in Fold]
used_rects = []
for d in fixed:
    cc = np.array([d["cx"], d["cy"]])
    a, b, c0t = d["top_plane"]
    base_rect = np.array(d["rect"])
    for k in (1.15, 1.3, 1.5, 1.7, 2.0):
        rect = cc + (base_rect - cc) * k
        topmin = float(min(a * px_ + b * py_ + c0t for px_, py_ in rect))
        om = oldmax_in_rect(rect)
        if om <= topmin + 0.05:
            break
    zb = d["base_z"] - 0.3
    n0 = len(verts)
    for px_, py_ in rect:
        verts.append([float(px_), float(py_), zb])
    for px_, py_ in rect:
        verts.append([float(px_), float(py_), a * px_ + b * py_ + c0t])
    B = [n0, n0 + 1, n0 + 2, n0 + 3]
    T = [n0 + 4, n0 + 5, n0 + 6, n0 + 7]
    faces.append([B[0], B[3], B[2], B[1]])
    for i in range(4):
        j = (i + 1) % 4
        faces.append([B[i], B[j], T[j], T[i]])
    faces.append([T[0], T[1], T[2], T[3]])
    used_rects.append(rect)
    print("vikýř (%.1f, %.1f): expanze %.2f, stary max %.2f vs top %.2f %s" % (
        cc[0], cc[1], k, om, topmin, "OK" if om <= topmin + 0.05 else "PRESAHUJE"))
V2 = np.array(verts, dtype=float)
OUT = f"output/pl_geof/{FID}/model_fixed.obj"
with open(OUT, "w", encoding="utf-8") as f:
    f.write("# Geoflow + regularizovane vikýře (orto pocet + lidar vysky, median/svah)\n")
    for v in V2:
        f.write("v %.3f %.3f %.3f\n" % tuple(v))
    for fa in faces:
        f.write("f " + " ".join(str(i + 1) for i in fa) + "\n")

from collections import Counter
ec = Counter()
for f_ in faces:
    idx = list(f_)
    tris = [[idx[0], idx[i], idx[i + 1]] for i in range(1, len(idx) - 1)] if len(idx) > 3 else [idx]
    for t_ in tris:
        for e_ in ((t_[0], t_[1]), (t_[1], t_[2]), (t_[2], t_[0])):
            ec[tuple(sorted(e_))] += 1
nm = sum(1 for v in ec.values() if v != 2)
core = np.array([poly.buffer(-1.0).contains(Point(px, py)) for px, py in zip(roof[:, 0], roof[:, 1])])
print("hodnoceni jadra (footprint erode -1 m, bez fasad): %d/%d bodu" % (core.sum(), len(roof)))
in_d = np.zeros(len(roof), bool)
for rect in used_rects:
    in_d |= MplPath(rect).contains_points(roof[:, :2])
print("bodu v pasech vikýřů: %d" % int(in_d.sum()))
for tag, (VV, FF) in {"lod22": (Vold, Fold), "fixed": (V2, faces)}.items():
    mz = mesh_z_at(np.array(VV, dtype=float), FF, roof[:, :2])
    cov = ~np.isnan(mz)
    rmse = float(np.sqrt(((roof[cov, 2] - mz[cov]) ** 2).mean())) if cov.any() else -1
    mc = core & cov
    rmsec = float(np.sqrt(((roof[mc, 2] - mz[mc]) ** 2).mean())) if mc.any() else -1
    md = in_d & cov
    rmsed = float(np.sqrt(((roof[md, 2] - mz[md]) ** 2).mean())) if md.any() else -1
    print("%s: RMSE=%.3f m (jadro %.3f, vikýře %.3f) pokryti=%.2f %s" % (
        tag, rmse, rmsec, rmsed, cov.mean(), ("nm=%d" % nm) if tag == "fixed" else ""))
print("zapsano", OUT, "verts=%d faces=%d" % (len(V2), len(faces)))

# --- 5. Overlay: puvodni vs sjednocene --------------------------------------
u0 = (minx - 12 - E0) / SP * W
v0 = (miny - 12 - N0) / SP * H
u1 = (maxx + 12 - E0) / SP * W
v1 = (maxy + 12 - N0) / SP * H
crop = ort[int(v0):int(v1), int(u0):int(u1)].astype(np.uint8)
fig, a = plt.subplots(figsize=(10, 10))
a.imshow(crop, origin="upper")
sx = (maxx + 12 - minx + 12) / crop.shape[1]
sy = (maxy + 12 - miny + 12) / crop.shape[0]
def P(E, N):
    return (np.asarray(E) - minx + 12) / sx, (np.asarray(N) - miny + 12) / sy
x, y = poly.exterior.coords.xy
a.plot(*P(np.array(x), np.array(y)), "w-", lw=1.5, label="footprint")
for d in ds:
    r = np.array(d["rect"]); r = np.vstack([r, r[:1]])
    a.plot(*P(r[:, 0], r[:, 1]), "r--", lw=1.2)
for d in fixed:
    r = np.array(d["rect"]); r = np.vstack([r, r[:1]])
    a.plot(*P(r[:, 0], r[:, 1]), "lime", lw=1.8)
a.plot([], [], "r--", label="puvodni (%d, ruzne vysky)" % len(ds))
a.plot([], [], "lime", label="sjednocene (%d, median/svah)" % len(fixed))
a.set_title("Vikýře: cervene=Geoflow/LiDAR puvodni, zelene=regularizovane")
a.legend(loc="upper right", fontsize=10)
plt.tight_layout()
plt.savefig("render/pl_dormers_overlay.png", dpi=110)
print("ulozeno render/pl_dormers_overlay.png")
