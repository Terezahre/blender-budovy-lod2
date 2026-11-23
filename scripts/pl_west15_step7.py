# -*- coding: utf-8 -*-
"""Krok 7: finalni vyhodnoceni west15_bool (manifold, RMSE, bias, overlay, 3D srovnani)."""
import json
from collections import Counter
import laspy
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.path import Path as MplPath
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from PIL import Image, ImageDraw
from shapely import wkt
from shapely.geometry import Point

FID = "ID-1465-38F62225-F3F5-F520-E053-CA2BA8C0BE14"


def load_obj(p):
    V, F = [], []
    for line in open(p, encoding="utf-8"):
        if line.startswith("v "):
            V.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("f "):
            F.append([int(x.split("/")[0]) - 1 for x in line.split()[1:]])
    return np.array(V, dtype=float), F


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
                zz = A[2] + u * v0[2] + v * v1[2]
                m = hit & (np.isnan(out) | (zz > out))
                out[m] = zz[m]
    return out


las = laspy.read(f"buildings_pl/{FID}/body.las")
x, y, z = np.asarray(las.x), np.asarray(las.y), np.asarray(las.z)
c = np.asarray(las.classification)
poly = wkt.loads(json.load(open("data_pl/warszawa_gt.json", encoding="utf-8"))[FID]["footprint_wkt"])
inside = np.array([poly.contains(Point(px, py)) for px, py in zip(x, y)])
gmed = float(np.median(z[(~inside) & (c == 2)]))
roof = np.stack([x[inside & (c == 6)], y[inside & (c == 6)], z[inside & (c == 6)]], 1)
roof = roof[roof[:, 2] > gmed + 1.5]
print("roof bodu (standard): %d, teren %.2f" % (len(roof), gmed))
doms = json.load(open("data_pl/west15_layout.json", encoding="utf-8"))

for tag, fn in (("lod22", "model_lod22.obj"), ("west15_bool", "model_west15_bool.obj")):
    V, F = load_obj(f"output/pl_geof/{FID}/{fn}")
    ec = Counter()
    for f_ in F:
        tris = [[f_[0], f_[i], f_[i + 1]] for i in range(1, len(f_) - 1)] if len(f_) > 3 else [f_]
        for t_ in tris:
            for e_ in ((t_[0], t_[1]), (t_[1], t_[2]), (t_[2], t_[0])):
                ec[tuple(sorted(e_))] += 1
    nm = [(e, n) for e, n in ec.items() if n != 2]
    print("%s: verts=%d faces=%d nonmanifold=%d" % (tag, len(V), len(F), len(nm)))
    if tag == "west15_bool" and nm:
        (a, b), nuse = nm[0]
        mid = (V[a] + V[b]) / 2
        above = mesh_z_at(V, F, np.array([[mid[0], mid[1]]]))[0]
        print("  nm hrana: pouziti=%d stred=(%.2f,%.2f,%.2f) povrch_nad=%.2f -> %s" % (
            nuse, mid[0], mid[1], mid[2], above,
            "SKRYTA uvnitr (nevadi)" if above > mid[2] + 0.01 else "NA POVRCHU (resit!)"))

core = np.array([poly.buffer(-1.0).contains(Point(px, py)) for px, py in zip(roof[:, 0], roof[:, 1])])
in_d = np.zeros(len(roof), bool)
for d in doms:
    in_d |= MplPath(np.array(d["rect"])).contains_points(roof[:, :2])
print("bodu v pasech 15 vikýru: %d" % in_d.sum())
res = {}
for tag, fn in (("lod22", "model_lod22.obj"), ("west15_bool", "model_west15_bool.obj")):
    V, F = load_obj(f"output/pl_geof/{FID}/{fn}")
    mz = mesh_z_at(V, F, roof[:, :2])
    cov = ~np.isnan(mz)
    out = {}
    out["rmse"] = float(np.sqrt(((roof[cov, 2] - mz[cov]) ** 2).mean()))
    mc = core & cov
    out["core"] = float(np.sqrt(((roof[mc, 2] - mz[mc]) ** 2).mean()))
    md = in_d & cov
    out["dorm"] = float(np.sqrt(((roof[md, 2] - mz[md]) ** 2).mean()))
    out["cov"] = float(cov.mean())
    res[tag] = out
    print("%s: RMSE=%.3f (jadro %.3f, vikýře %.3f) pokryti=%.3f" % (tag, out["rmse"], out["core"], out["dorm"], out["cov"]))
json.dump(res, open("output/pl_geof/%s/west15_metrics.json" % FID, "w", encoding="utf-8"), indent=1)

# bias jednotlivych hranolu
V, F = load_obj(f"output/pl_geof/{FID}/model_west15_bool.obj")
for d in doms:
    m = MplPath(np.array(d["rect"])).contains_points(roof[:, :2])
    Q = roof[m]
    a, b, c0 = d["top_plane"]
    pred = a * Q[:, 0] + b * Q[:, 1] + c0
    if m.sum():
        print("%s: bodu=%d bias %+.2f m rmse %.2f" % (
            d["id"], m.sum(), float((pred - Q[:, 2]).mean()),
            float(np.sqrt(((pred - Q[:, 2]) ** 2).mean()))))
    else:
        print("%s: bodu=0" % d["id"])

# 3D srovnani pred/po
cx, cy = poly.centroid.x, poly.centroid.y
fig = plt.figure(figsize=(15, 6))
for i, (tag, fn, ttl, col) in enumerate((
        ("lod22", "model_lod22.obj", "pred: Geoflow LOD22 (jehly)", "steelblue"),
        ("west15_bool", "model_west15_bool.obj", "po: +15 vikýru (boolean)", "firebrick"))):
    V, F = load_obj(f"output/pl_geof/{FID}/{fn}")
    Vc = V - np.array([cx, cy, 0])
    tris = []
    for f in F:
        P = Vc[np.array(f)]
        for j in range(1, len(P) - 1):
            tris.append(P[[0, j, j + 1]])
    a = fig.add_subplot(1, 2, i + 1, projection="3d")
    a.add_collection3d(Poly3DCollection(tris, facecolor=col, edgecolor="k", linewidths=0.05, alpha=0.95))
    a.set_title(ttl)
    a.set_box_aspect((1, 1, 0.5))
    a.view_init(elev=25, azim=-60)
    a.set_xlim(-40, 40)
    a.set_ylim(-40, 40)
    a.set_xlabel("x [m]")
    a.set_ylabel("y [m]")
    a.set_zlabel("z [m]")
plt.suptitle("Zapadni svah ID-1465: pred/po (EPSG:2180, centrovano)")
plt.tight_layout()
plt.savefig("render/pl_west15_compare.png", dpi=110)
print("ulozeno render/pl_west15_compare.png")

# overlay 15 obdelniku na ortofoto
im = Image.open("data_pl/warszawa_orto_200m_north.tif").convert("RGB")
minx, miny, maxx, maxy = poly.bounds
ua, va = (minx - 636999.05) / 0.1, (488361.95 - maxy) / 0.1
ub, vb = (maxx - 636999.05) / 0.1, (488361.95 - miny) / 0.1
crop = im.crop((int(ua) - 10, int(va) - 10, int(ub) + 10, int(vb) + 10))
S = 3
crop = crop.resize((crop.width * S, crop.height * S), Image.LANCZOS)
d = ImageDraw.Draw(crop)
xs, ys = poly.exterior.coords.xy
d.line([(((EE - 636999.05) / 0.1 - (int(ua) - 10)) * S,
         ((488361.95 - NN) / 0.1 - (int(va) - 10)) * S)
        for EE, NN in zip(xs, ys)], fill=(255, 0, 0), width=2)
for dd in doms:
    r = np.array(dd["rect"])
    r = np.vstack([r, r[:1]])
    col = (0, 255, 0) if dd["row"] == "lower" else (255, 255, 0)
    d.line([(((p[0] - 636999.05) / 0.1 - (int(ua) - 10)) * S,
             ((488361.95 - p[1]) / 0.1 - (int(va) - 10)) * S) for p in r],
           fill=col, width=2)
    X = ((dd["cx"] - 636999.05) / 0.1 - (int(ua) - 10)) * S
    Y = ((488361.95 - dd["cy"]) / 0.1 - (int(va) - 10)) * S
    d.text((X - 6, Y - 24), dd["id"], fill=col)
crop.save("render/pl_west15_overlay.png")
print("ulozeno render/pl_west15_overlay.png", crop.size)
