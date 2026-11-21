# -*- coding: utf-8 -*-
"""Varsava Geoflow test: prave huste mracno (12 pts/m2) + GT footprint.
Budova ID-1465-38F62225-F3F5-F520-E053-CA2BA8C0BE14 (typ 1030, 16.9k bodu class 6).
Vstup: data_pl/warszawa_12ppsm.laz + data_pl/warszawa_gt.json
Vystup: buildings_pl/<FID>/ + output/pl_geof/<FID>_<profil>/ + results.json
Beh: python scripts/warszawa_geof.py --run
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np

GEOF = r"C:\Users\Tereza\geoflow-local\geof.exe"
FLOW = "flowcharts/krav59_lod22/reconstruct_objonly.json"
R2G = {"plane_detect__epsilon": "r_plane_epsilon",
       "plane_detect__min_points": "r_plane_min_points",
       "plane_detect__k": "r_plane_k",
       "normal_estimate__k": "r_normal_k",
       "line_detect__epsilon": "r_line_epsilon",
       "optimisation_data_term": "r_optimisation_data_term",
       "lod13__step_height": "r_lod13_step_height",
       "max_arr_complexity": "r_max_arr_complexity"}
PROFILE_PARAMS = {
    "SIMPLE_FLAT": dict(plane_detect__epsilon=0.25, plane_detect__min_points=20,
                         plane_detect__k=15, normal_estimate__k=8,
                         line_detect__epsilon=0.5, optimisation_data_term=5.0,
                         lod13__step_height=3.0, max_arr_complexity=400),
    "STANDARD_GABLE": dict(plane_detect__epsilon=0.20, plane_detect__min_points=15,
                           plane_detect__k=15, normal_estimate__k=8,
                           line_detect__epsilon=0.4, optimisation_data_term=7.0,
                           lod13__step_height=3.0, max_arr_complexity=400),
    "COMPLEX_HIP": dict(plane_detect__epsilon=0.15, plane_detect__min_points=10,
                        plane_detect__k=10, normal_estimate__k=5,
                        line_detect__epsilon=0.3, optimisation_data_term=9.0,
                        lod13__step_height=2.5, max_arr_complexity=800),
}
FID = "ID-1465-38F62225-F3F5-F520-E053-CA2BA8C0BE14"


def load_obj(path):
    V, F = [], []
    for line in open(path, encoding="utf-8"):
        if line.startswith("v "):
            V.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("f "):
            F.append([int(x.split("/")[0]) - 1 for x in line.split()[1:]])
    return np.array(V), F


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    import geopandas as gpd
    import laspy
    from shapely import wkt
    gt = json.load(open("data_pl/warszawa_gt.json", encoding="utf-8"))[FID]
    geom = wkt.loads(gt["footprint_wkt"])
    las = laspy.read("data_pl/warszawa_12ppsm.laz")
    x, y, z = np.asarray(las.x), np.asarray(las.y), np.asarray(las.z)
    cls = np.asarray(las.classification)
    minx, miny, maxx, maxy = geom.bounds
    win = (x >= minx - 5) & (x <= maxx + 5) & (y >= miny - 5) & (y <= maxy + 5)
    from shapely.geometry import Point
    pts = np.column_stack([x[win], y[win]])
    inside = np.array([geom.contains(Point(p)) for p in pts])
    sel6 = np.where(win)[0][inside & (cls[win] == 6)]
    sel2 = np.where(win)[0][~inside & (cls[win] == 2)]
    print(f"budova: {len(sel6)} bodu, teren: {len(sel2)} bodu")
    zb = z[sel6]
    zstd = float(zb.std())
    prof = ("SIMPLE_FLAT" if zstd < 1.2 else
            "STANDARD_GABLE" if zstd < 2.5 else "COMPLEX_HIP")
    print(f"zstd={zstd:.2f} -> profil {prof}, GT typ {gt['roofType']}")
    bdir = f"buildings_pl/{FID}"
    os.makedirs(bdir, exist_ok=True)
    gpd.GeoDataFrame({"id": [FID]}, geometry=[geom],
                     crs="EPSG:2180").to_file(os.path.join(bdir, "footprint.gpkg"), driver="GPKG")
    hdr = laspy.LasHeader(point_format=1, version="1.2")
    hdr.scales = [0.01, 0.01, 0.01]
    both = np.concatenate([sel6, sel2])
    sub = las[both]
    sub.write(os.path.join(bdir, "body.las"))
    params = dict(PROFILE_PARAMS[prof])
    lines = [f"# {FID} profil {prof} (huste PL mracno)",
             f'input_footprint = "{bdir}/footprint.gpkg"',
             f'input_pointcloud = "{bdir}/body.las"',
             'building_identifier = "id"',
             'input_footprint_select_sql = ""',
             f'output_obj_lod22 = "output/pl_geof/{FID}/model_lod22.obj"',
             f'output_obj_lod12 = "output/pl_geof/{FID}/model_lod12.obj"',
             f'output_obj_lod13 = "output/pl_geof/{FID}/model_lod13.obj"',
             f'output_cityjson = "output/pl_geof/{FID}/model.json"',
             'output_cj_referenceSystem = "http://www.opengis.net/def/crs/EPSG/0/2180"']
    for k, v in params.items():
        lines.append(f"{R2G[k]} = {v}")
    lines.append("r_raster_cellsize = 0.05")
    os.makedirs(f"output/pl_geof/{FID}", exist_ok=True)
    open(f"{bdir}/geof.toml", "w", encoding="utf-8").write("\n".join(lines) + "\n")
    if a.run:
        r = subprocess.run([GEOF, FLOW, "--config", f"{bdir}/geof.toml"],
                           capture_output=True, text=True, timeout=1800)
        ok = os.path.exists(f"output/pl_geof/{FID}/model_lod22.obj")
        print(f"geof exit={r.returncode} obj={ok}")
        if ok:
            V, F = load_obj(f"output/pl_geof/{FID}/model_lod22.obj")
            roof = np.column_stack([x[sel6], y[sel6], z[sel6]])
            roof = roof[roof[:, 2] > np.median(z[sel2]) + 1.5]
            mz = mesh_z_at(V, F, roof[:, :2])
            cov = ~np.isnan(mz)
            rmse = float(np.sqrt(((roof[cov, 2] - mz[cov]) ** 2).mean()))
            from collections import Counter
            ec = Counter()
            for f in F:
                tris = [[f[0], f[i], f[i + 1]] for i in range(1, len(f) - 1)] if len(f) > 3 else [f]
                for t in tris:
                    for e in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                        ec[tuple(sorted(e))] += 1
            nm = sum(1 for c in ec.values() if c != 2)
            res = dict(profile=prof, rmse=round(rmse, 3), coverage=round(float(cov.mean()), 3),
                       nonmanifold=int(nm), verts=int(len(V)), faces=len(F))
            json.dump(res, open(f"output/pl_geof/{FID}/result.json", "w", encoding="utf-8"), indent=1)
            print("RMSE=%.3f pokryti=%.2f nm=%d verts=%d faces=%d" % (
                rmse, cov.mean(), nm, len(V), len(F)))


if __name__ == "__main__":
    main()
