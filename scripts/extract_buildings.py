# -*- coding: utf-8 -*-
"""Extrahuje pilotni budovy z KRAV59.laz: body + footprint + meta + Geoflow config.
Profily parametru dle agents.md (SIMPLE_FLAT / STANDARD_GABLE / COMPLEX_HIP / SPARSE).
Vystup: buildings/<ID>/{body.las, footprint.geojson, footprint.gpkg, meta.json, config.toml}
Souradnice zustavaji v S-JTSK (EPSG:5514), zadny posun ani skalovani.
"""
import json
import os
import numpy as np
import laspy

SRC = "KRAV59_DMP1G/KRAV59.laz"
CANDS = "buildings/candidates.json"

# vybrane klastry z analyze_laz.py: (id, cluster, profil-ocekavani)
PILOT = [
    ("B01_flat", 1, "SIMPLE_FLAT"),
    ("B02_gable", 46, "STANDARD_GABLE"),
    ("B03_row", 171, "COMPLEX_HIP"),
    ("B04_panelak", 59, "SIMPLE_FLAT"),  # vysoky panelovy blok, bimodalni hist: teren + strecha ~25 m
    ("B05_vez", 73, "COMPLEX_HIP"),  # vysoka/clenita struktura, horizontalni + stenove roviny
]

BUF = 5.0  # buffer kolem bbox pro ground body (urceni podlahy v Geoflow)

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


def footprint_polygon(xy):
    from shapely.geometry import MultiPoint
    # konvexni obal: pri 2 pts/m2 dela concave_hull falesne zuby/diry
    poly = MultiPoint(xy).convex_hull
    poly = poly.simplify(0.3, preserve_topology=True)
    if poly.geom_type == "MultiPolygon":
        poly = max(poly.geoms, key=lambda g: g.area)
    return poly


def split_by_gap(sel):
    """Rozdeleni sliteho klastru podle ulicky v 1m DSM (prazdny sloupec/radek
    deli obsazene bunky na obe strany). Vraci list poli, nebo [sel]."""
    ox, oy = sel[:, 0].min(), sel[:, 1].min()
    gx = ((sel[:, 0] - ox) / 1.0).astype(int)
    gy = ((sel[:, 1] - oy) / 1.0).astype(int)
    occ = np.zeros((gx.max() + 1, gy.max() + 1), bool)
    occ[gx, gy] = True
    best = None
    for i in range(occ.shape[0]):
        c = int(occ[i, :].sum())
        if best is None or c < best[2]:
            best = ("x", i, c)
    for j in range(occ.shape[1]):
        c = int(occ[:, j].sum())
        if c < best[2]:
            best = ("y", j, c)
    typ, idx, c = best
    if typ == "x":
        L, R = occ[:idx, :].any(), occ[idx + 1:, :].any()
        ok = occ.shape[0] > 4 and 0 < idx < occ.shape[0] - 1
        if c <= 1 and L and R and ok:
            return [sel[gx < idx], sel[gx > idx]]
    else:
        L, R = occ[:, :idx].any(), occ[:, idx + 1:].any()
        ok = occ.shape[1] > 4 and 0 < idx < occ.shape[1] - 1
        if c <= 1 and L and R and ok:
            return [sel[gy < idx], sel[gy > idx]]
    return [sel]


def main():
    las = laspy.read(SRC)
    pts = np.vstack([las.x, las.y, las.z]).T
    cls = np.array(las.classification)
    cands = {c["cluster"]: c for c in json.load(open(CANDS, encoding="utf-8"))["candidates"]}

    from sklearn.cluster import DBSCAN
    x0, x1, y0, y1 = (-738000.0, -737500.0, -1039350.0, -1038850.0)
    m = (cls == 6) & (pts[:, 0] >= x0) & (pts[:, 0] < x1) & (pts[:, 1] >= y0) & (pts[:, 1] < y1)
    b = pts[m]
    labels = DBSCAN(eps=2.5, min_samples=30).fit(b[:, :2]).labels_

    jobs = []
    for bid, cl, profile in PILOT:
        base = np.where(m)[0][labels == cl]
        sel = pts[base]
        parts = split_by_gap(sel)
        if len(parts) > 1:
            print(f"[{bid}] SPLIT na {len(parts)} budov podle ulicky")
            # globalni indexy pro casti: pres masku v sel
            taken = np.zeros(len(sel), bool)
            for k, part in enumerate(parts):
                pm = np.zeros(len(sel), bool)
                # part je sel[submask]; najdi submask porovnanim (bez duplikatu souradnic staci prvni vyskyt)
                rest = np.where(~taken)[0]
                # jednoduse: vzdalenostni matching
                from scipy.spatial import cKDTree
                d, ix = cKDTree(sel[rest]).query(part, k=1)
                assert (d < 1e-6).all()
                pm[rest[ix]] = True
                taken |= pm
                jobs.append((f"{bid}{chr(97 + k)}", cl, profile, base[pm]))
        else:
            jobs.append((bid, cl, profile, base))

    for bid, cl, profile, gidx in jobs:
        sel = pts[gidx]
        # ground body v bufferu (class 2) pro urceni podlahy
        gx0, gx1 = sel[:, 0].min() - BUF, sel[:, 0].max() + BUF
        gy0, gy1 = sel[:, 1].min() - BUF, sel[:, 1].max() + BUF
        gsel = pts[(cls == 2) & (pts[:, 0] >= gx0) & (pts[:, 0] <= gx1)
                   & (pts[:, 1] >= gy0) & (pts[:, 1] <= gy1)]
        ground_z = float(np.percentile(gsel[:, 2], 5)) if len(gsel) else float(sel[:, 2].min())
        rel_h = float(sel[:, 2].max() - ground_z)

        poly = footprint_polygon(sel[:, :2])
        fp_area = float(poly.area)
        dens = float(len(sel) / max(poly.area, 1.0))
        zstd = float(sel[:, 2].std())

        # SPARSE korekce dle agents.md
        params = dict(PROFILE_PARAMS[profile])
        sparse = dens < 1.0
        if sparse:
            params["plane_detect__epsilon"] = round(params["plane_detect__epsilon"] + 0.05, 3)
            params["plane_detect__min_points"] = int(params["plane_detect__min_points"] * 1.5)
            params["plane_detect__k"] = params["plane_detect__k"] + 5
            params["line_detect__epsilon"] = round(params["line_detect__epsilon"] + 0.1, 3)
            params["optimisation_data_term"] = float(params["optimisation_data_term"] - 2.0)

        # odhad poctu rovin strechy (heuristika, upresni Geoflow DetectPlanes)
        if zstd < 1.2:
            roof_guess = 1
        elif zstd < 2.5:
            roof_guess = 2
        else:
            roof_guess = 6
        use_polyfit = bool(roof_guess > 8 or (len(sel) / max(poly.area, 1.0)) < 0.5 and False)

        outdir = os.path.join("buildings", bid)
        os.makedirs(outdir, exist_ok=True)

        # body.las: presne clenove klastru (class 6) + ground (class 2) v bufferu
        # puvodni S-JTSK souradnice; bbox sousedu se vedome nebere (kontaminace)
        cl_global = gidx
        gmask = (cls == 2) & (pts[:, 0] >= gx0) & (pts[:, 0] <= gx1) \
            & (pts[:, 1] >= gy0) & (pts[:, 1] <= gy1)
        both_idx = np.union1d(cl_global, np.where(gmask)[0])
        sub = las[both_idx]
        sub.write(os.path.join(outdir, "body.las"))

        # footprint geojson + gpkg (S-JTSK)
        import json as js
        gj = {"type": "FeatureCollection", "crs": {"type": "name", "properties": {"name": "EPSG:5514"}},
              "features": [{"type": "Feature",
                            "properties": {"id": bid, "cluster": int(cl)},
                            "geometry": {"type": "Polygon",
                                         "coordinates": [list(poly.exterior.coords)]}}]}
        with open(os.path.join(outdir, "footprint.geojson"), "w", encoding="utf-8") as f:
            js.dump(gj, f)
        try:
            import geopandas as gpd
            gdf = gpd.GeoDataFrame({"id": [bid], "cluster": [int(cl)]},
                                   geometry=[poly], crs="EPSG:5514")
            gdf.to_file(os.path.join(outdir, "footprint.gpkg"), driver="GPKG")
            gpkg_ok = True
        except Exception as e:
            print(f"  [{bid}] GPKG zapis selhal ({e})")
            gpkg_ok = False

        meta = dict(id=bid, cluster=int(cl), profile=profile, crs="EPSG:5514",
                    n_points=int(len(sel)), n_ground=int(len(gsel)),
                    density_pts_m2=round(dens, 3), zstd=round(zstd, 3),
                    zmin=round(float(sel[:, 2].min()), 2), zmax=round(float(sel[:, 2].max()), 2),
                    ground_z_p5=round(ground_z, 2), height_above_ground=round(rel_h, 2),
                    footprint_area_m2=round(fp_area, 1),
                    bbox=[round(float(sel[:, 0].min()), 2), round(float(sel[:, 1].min()), 2),
                          round(float(sel[:, 0].max()), 2), round(float(sel[:, 1].max()), 2)],
                    roofplane_guess=roof_guess, sparse=bool(sparse),
                    polyfit_fallback=use_polyfit, gpkg_ok=bool(gpkg_ok),
                    params=params)
        with open(os.path.join(outdir, "meta.json"), "w", encoding="utf-8") as f:
            js.dump(meta, f, indent=1, ensure_ascii=False)

        # Geoflow TOML config (globals pro lod22-reconstruct)
        lines = [f"# Geoflow config {bid} — profil {profile}" + (" + SPARSE" if sparse else ""),
                 f'input_footprint = "buildings/{bid}/footprint.gpkg"',
                 f'input_pointcloud = "buildings/{bid}/body.las"',
                 f'output_obj_lod22 = "output/geoflow/{bid}/model_lod22.obj"',
                 f'output_obj_lod12 = "output/geoflow/{bid}/model_lod12.obj"',
                 f'output_cityjson = "output/geoflow/{bid}/model.json"']
        for k, v in params.items():
            lines.append(f"{k} = {v}")
        with open(os.path.join(outdir, "config.toml"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

        print(f"[{bid}] cl={cl} n={len(sel)} dens={dens:.2f}/m2 zstd={zstd:.2f} "
              f"h={rel_h:.1f}m fp={fp_area:.0f}m2 profil={profile}{' SPARSE' if sparse else ''} gpkg={gpkg_ok}")

    print("-> buildings/B0*/{body.las, footprint.*, meta.json, config.toml}")


if __name__ == "__main__":
    main()
