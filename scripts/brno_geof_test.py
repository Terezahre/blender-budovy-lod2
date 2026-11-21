# -*- coding: utf-8 -*-
"""Brno Geoflow test: ML-doporucene vs rucni parametry (krok a z planu).
Vybere 3 budovy (flat/gable/hip, purity==1.0, SV kvadrant = povodne holdout),
pro kazdou vyrobi: footprint.gpkg (ZABAGED), pseudo body.las z DSM/DTM rastru
(mrizka 1 m: uvnitr class 6 s DSM, buffer 5 m class 2 s DTM, S-JTSK),
dva geof.toml (ML profil z predict_params vs rucni zstd-heuristika)
a spusti geof.exe. Hodnoceni: RMSE strechy vs vstup, pokryti, manifold
(stejna metoda jako scripts/compare_geof.py).
Vystup: output/brno_geof/<FID>_<ml|manual>/{model_lod22.obj, result.json}
Beh: python scripts/brno_geof_test.py [--run] [--dry]
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ml"))
from predict_params import featurize, LABELS, PROFILE_PARAMS  # noqa: E402

R2G = {"plane_detect__epsilon": "r_plane_epsilon",
       "plane_detect__min_points": "r_plane_min_points",
       "plane_detect__k": "r_plane_k",
       "normal_estimate__k": "r_normal_k",
       "line_detect__epsilon": "r_line_epsilon",
       "optimisation_data_term": "r_optimisation_data_term",
       "lod13__step_height": "r_lod13_step_height",
       "max_arr_complexity": "r_max_arr_complexity"}
BBOX = (-598500.0, -1161500.0)
GEOF = r"C:\Users\Tereza\geoflow-local\geof.exe"
FLOW = "flowcharts/krav59_lod22/reconstruct_objonly.json"
GRID = 1.0
BUF = 5.0


def mesh_z_at(V, F, xy):
    out = np.full(len(xy), np.nan)
    for f in F:
        P = V[f]
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


def load_obj(path):
    V, F = [], []
    for line in open(path, encoding="utf-8"):
        if line.startswith("v "):
            V.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("f "):
            F.append([int(x.split("/")[0]) - 1 for x in line.split()[1:]])
    return np.array(V), F


def pick_test_buildings():
    import geopandas as gpd
    gt = json.load(open("ml/gt_brno.json", encoding="utf-8"))
    fp = gpd.read_file("ml/data_brno/footprints.geojson")
    fp = fp.set_index(fp["fid_zbg"].astype(str))
    # SV kvadrant (puvodni holdout) + ciste typy + stredni velikost
    cands = {}
    for fid, g in gt.items():
        if g.get("purity") != 1.0 or g["roof_type"] not in (0, 1, 2):
            continue
        try:
            geom = fp.loc[str(fid)].geometry
        except KeyError:
            continue
        cx, cy = geom.centroid.x, geom.centroid.y
        if not (cx > -597500 and cy > -1160500):
            continue
        area = float(geom.area)
        if 80 <= area <= 400 and fid in cands.get(g["roof_type"], [None]):
            continue
        if g["roof_type"] not in cands and 80 <= area <= 400:
            cands[g["roof_type"]] = fid
    return cands  # {typ: fid}


def split_levels(xy, z, cls, geom, gap=2.0, min_pts=20):
    """Rozdeleni footprintu podle vyskovych hladin (bimodalni DSM).
    Stejny problem jako slite klastry v KRAV59 (split_by_gap), jen ve Z.
    Vraci list (subgeom, mask6) - hull komponent jak v extract_buildings.py.
    """
    from shapely.geometry import MultiPoint
    from scipy.ndimage import label as nd_label
    m6 = cls == 6
    if m6.sum() < 2 * min_pts:
        return [(geom, m6)]
    zb = z[m6]
    lo, hi = zb.min(), zb.max()
    if hi - lo < gap:
        return [(geom, m6)]
    bins = np.arange(lo, hi + 1.0, 1.0)
    hist, edges = np.histogram(zb, bins=bins)
    occ = np.where(hist > 2)[0]  # ignoruj ojedinele body (komarne, sum)
    gaps = [(edges[occ[i + 1]] - edges[occ[i] + 1], (edges[occ[i] + 1] + edges[occ[i + 1]]) / 2)
            for i in range(len(occ) - 1)]
    big = [g for g in gaps if g[0] >= gap]
    if not big:
        return [(geom, m6)]
    thr = max(big)[1]
    # komponenty na mrizce 1 m v bboxu
    minx, miny = xy[:, 0].min(), xy[:, 1].min()
    gx = ((xy[:, 0] - minx) / GRID).astype(int)
    gy = ((xy[:, 1] - miny) / GRID).astype(int)
    H, W = gy.max() + 1, gx.max() + 1
    out = []
    for lev, sel in (("lo", m6 & (z < thr)), ("hi", m6 & (z >= thr))):
        if sel.sum() < min_pts:
            continue
        grid = np.zeros((H, W), bool)
        grid[gy[sel], gx[sel]] = True
        lab, n = nd_label(grid)
        for c in range(1, n + 1):
            yy, xx = np.where(lab == c)
            if len(xx) < min_pts:
                continue
            pts_c = np.column_stack([minx + xx * GRID, miny + yy * GRID])
            hull = MultiPoint(pts_c).convex_hull.simplify(0.3, preserve_topology=True)
            if hull.is_empty or hull.area < 10:
                continue
            mm = m6 & (z < thr if lev == "lo" else z >= thr)
            # jen body uvnitr hullu
            from shapely.geometry import Point as SPoint
            inside_h = np.array([hull.contains(SPoint(p)) for p in xy[mm]])
            idx = np.where(mm)[0][inside_h]
            if len(idx) < min_pts:
                continue
            mask = np.zeros(len(xy), bool)
            mask[idx] = True
            out.append((hull, mask))
    return out if out else [(geom, m6)]


def sample_pseudo_cloud(geom, fid):
    import tifffile
    from shapely import points as sh_points
    from shapely.geometry import box
    ddir = os.path.join("ml", "data_brno", "dsm")
    x0, y0 = BBOX
    cx, cy = geom.centroid.x, geom.centroid.y
    bx, by = int((cx - x0) / 1000), int((cy - y0) / 1000)
    name = {(0, 0): "SW", (0, 1): "SE", (1, 0): "NW", (1, 1): "NE"}[(by, bx)]
    dsm = tifffile.imread(os.path.join(ddir, f"dsm_{name}.tif")).astype(float)
    dtm = tifffile.imread(os.path.join(ddir, f"dmt_{name}.tif")).astype(float)
    lx0, ly0 = x0 + bx * 1000, y0 + by * 1000
    minx, miny, maxx, maxy = geom.bounds
    xs = np.arange(minx - BUF, maxx + BUF, GRID)
    ys = np.arange(miny - BUF, maxy + BUF, GRID)
    GX, GY = np.meshgrid(xs, ys)
    pts = np.column_stack([GX.ravel(), GY.ravel()])
    inside = np.array([geom.contains(__import__("shapely").geometry.Point(p)) for p in pts])
    ix = np.clip(((pts[:, 0] - lx0) / 0.5).astype(int), 0, 1999)
    iy = np.clip(((pts[:, 1] - ly0) / 0.5).astype(int), 0, 1999)
    z_surf = np.where(inside, dsm[iy, ix], dtm[iy, ix])
    cls = np.where(inside, 6, 2).astype(np.uint8)
    keep = np.isfinite(z_surf)
    pts, z_surf, cls = pts[keep], z_surf[keep], cls[keep]
    # jitter: dokonale pravidelna mrizka degeneruje detekci rovin/primet
    # (DetectLines mlcky neprobehne) - rozptyl jako u realneho lidaru
    rng = np.random.default_rng(42)
    pts = pts + rng.uniform(-0.3, 0.3, pts.shape)
    z_surf = z_surf + rng.uniform(-0.05, 0.05, len(z_surf))
    return pts, z_surf, cls


def write_las(path, xy, z, cls):
    import laspy
    hdr = laspy.LasHeader(point_format=1, version="1.2")  # stejny format jako KRAV59 body.las
    hdr.scales = [0.01, 0.01, 0.01]
    hdr.offsets = [float(xy[:, 0].min()), float(xy[:, 1].min()), float(z.min())]
    las = laspy.LasData(hdr)
    las.x, las.y, las.z = xy[:, 0], xy[:, 1], z
    las.classification = cls
    las.write(path)


def write_toml(path, bdir, outdir, profile, extra_note=""):
    params = dict(PROFILE_PARAMS[profile])
    h_ridge = extra_note.get("h_ridge") if isinstance(extra_note, dict) else None
    if h_ridge is not None and h_ridge < 6:
        params["lod13__step_height"] = 2.5
    lines = [f"# {bdir} profil {profile}",
             f'input_footprint = "{bdir}/footprint.gpkg"',
             f'input_pointcloud = "{bdir}/body.las"',
             'building_identifier = "id"',
             'input_footprint_select_sql = ""',
             f'output_obj_lod22 = "{outdir}/model_lod22.obj"',
             f'output_obj_lod12 = "{outdir}/model_lod12.obj"',
             f'output_obj_lod13 = "{outdir}/model_lod13.obj"',
             f'output_cityjson = "{outdir}/model.json"',
             'output_cj_referenceSystem = "http://www.opengis.net/def/crs/EPSG/0/5514"']
    for k, v in params.items():
        lines.append(f"{R2G[k]} = {v}")
    lines.append("r_raster_cellsize = 0.05")
    open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return profile, params


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true", help="spustit geof.exe (jinak jen pripravit data)")
    a = ap.parse_args()
    import geopandas as gpd
    import pickle
    cands = pick_test_buildings()
    print("testovaci budovy (typ: fid):", cands)
    if len(cands) < 3:
        print("POZOR: nenasel 3 typy, beru co je")
    fp = gpd.read_file("ml/data_brno/footprints.geojson")
    fp = fp.set_index(fp["fid_zbg"].astype(str))
    m_roof = pickle.load(open("ml/gb_roof.pkl", "rb"))["model"]
    m_ridge = pickle.load(open("ml/gb_ridge.pkl", "rb"))["model"]
    results = {}
    for rtype, fid in sorted(cands.items()):
        geom = fp.loc[str(fid)].geometry
        xy, z, cls = sample_pseudo_cloud(geom, fid)
        # vyskove hladiny: slite budovy rozdelit (KRAV59 split_by_gap ve Z)
        units = split_levels(xy, z, cls, geom)
        print(f"[{fid}] hladin: {len(units)}")
        # ML profil z patchu (uroven budovy)
        import glob
        npz = sorted(glob.glob("ml/patches_brno/*.npz"))
        pf = [p for p in npz if os.path.basename(p)[:-4] == str(fid)]
        if not pf:
            print(f"[{fid}] chybi patch, skip"); continue
        X = featurize(pf[0])
        ml_prof = LABELS[int(m_roof.predict(X)[0])]
        ml_h = float(m_ridge.predict(X)[0])
        gt = json.load(open("ml/gt_brno.json", encoding="utf-8"))[str(fid)]
        for i, (subgeom, m6) in enumerate(units):
            suf = "" if len(units) == 1 else chr(97 + i)
            bid = f"{fid}{suf}"
            bdir = f"buildings_brno/{bid}"
            os.makedirs(bdir, exist_ok=True)
            gpd.GeoDataFrame({"id": [bid]}, geometry=[subgeom],
                             crs="EPSG:5514").to_file(os.path.join(bdir, "footprint.gpkg"), driver="GPKG")
            m2 = cls == 2
            xx = np.concatenate([xy[m6], xy[m2]])
            zz = np.concatenate([z[m6], z[m2]])
            cc = np.concatenate([np.full(m6.sum(), 6, np.uint8), np.full(m2.sum(), 2, np.uint8)])
            write_las(os.path.join(bdir, "body.las"), xx, zz, cc)
            nb, ng = int(m6.sum()), int(m2.sum())
            zb = z[m6]
            zstd = float(zb.std())
            man_prof = ("SIMPLE_FLAT" if zstd < 1.2 else
                        "STANDARD_GABLE" if zstd < 2.5 else "COMPLEX_HIP")
            print(f"[{bid}] GT={LABELS[gt['roof_type']]} ML={ml_prof}(h={ml_h:.1f}m) "
                  f"MANUAL={man_prof}(zstd={zstd:.2f}) body={nb}+{ng}")
            for variant, prof, h in [("ml", ml_prof, ml_h), ("manual", man_prof, None)]:
                outdir = f"output/brno_geof/{bid}_{variant}"
                os.makedirs(outdir, exist_ok=True)
                write_toml(f"{bdir}/geof_{variant}.toml", bdir, outdir, prof, {"h_ridge": h})
                if a.run:
                    r = subprocess.run([GEOF, FLOW, "--config", f"{bdir}/geof_{variant}.toml"],
                                       capture_output=True, text=True, timeout=900)
                    ok = os.path.exists(f"{outdir}/model_lod22.obj")
                    print(f"  {variant}: geof exit={r.returncode} obj={ok} "
                          f"{(r.stderr[-300:] if r.returncode else '')}")
                    if ok:
                        V, F = load_obj(f"{outdir}/model_lod22.obj")
                        roof = np.column_stack([xx[cc == 6], zz[cc == 6]])
                        roof = roof[roof[:, 2] > np.median(zz[cc == 2]) + 1.5]
                        mz = mesh_z_at(V, F, roof[:, :2])
                        cov = ~np.isnan(mz)
                        rmse = float(np.sqrt(((roof[cov, 2] - mz[cov]) ** 2).mean())) if cov.any() else -1
                        from collections import Counter
                        ec = Counter()
                        for f in F:
                            tris = [[f[0], f[i], f[i + 1]] for i in range(1, len(f) - 1)] if len(f) > 3 else [f]
                            for t in tris:
                                for e in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                                    ec[tuple(sorted(e))] += 1
                        nm = sum(1 for c in ec.values() if c != 2)
                        results[f"{bid}_{variant}"] = dict(
                            profile=prof, rmse=round(rmse, 3),
                            coverage=round(float(cov.mean()), 3),
                            nonmanifold=int(nm),
                            verts=int(len(V)), faces=len(F))
                        print(f"  {variant}: RMSE={rmse:.3f} m pokryti={cov.mean():.2f} nm={nm}")
    json.dump(results, open("output/brno_geof/results.json", "w", encoding="utf-8"), indent=1)
    print("-> output/brno_geof/results.json:", json.dumps(results, ensure_ascii=False))


if __name__ == "__main__":
    main()
