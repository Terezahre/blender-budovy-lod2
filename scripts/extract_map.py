# -*- coding: utf-8 -*-
"""Extrakce sedlovych domu z celomapoveho scanu (tile, cluster) -> buildings/<ID>/.
Stejny format jako extract_buildings.py (body.las, footprint.*, meta.json).
"""
import json
import os
import numpy as np
import laspy
from sklearn.cluster import DBSCAN

SRC = "KRAV59_DMP1G/KRAV59.laz"
BUF = 5.0

CANDS = [
    ("G1_sedlova", (0, 2), 1, "COMPLEX_HIP"),
    ("G2_sedlova", (3, 3), 470, "COMPLEX_HIP"),
    ("G3_domek", (1, 2), 281, "COMPLEX_HIP"),
]

PROFILE_PARAMS = {
    "COMPLEX_HIP": dict(plane_detect__epsilon=0.15, plane_detect__min_points=10,
                        plane_detect__k=10, normal_estimate__k=5,
                        line_detect__epsilon=0.3, optimisation_data_term=9.0,
                        lod13__step_height=2.5, max_arr_complexity=800),
}

CH = 500.0
XS = np.arange(-740000.0, -737500.0, CH)
YS = np.arange(-1040000.0, -1038000.0, CH)


def footprint_polygon(xy):
    from shapely.geometry import MultiPoint
    poly = MultiPoint(xy).convex_hull.simplify(0.3, preserve_topology=True)
    if poly.geom_type == "MultiPolygon":
        poly = max(poly.geoms, key=lambda g: g.area)
    return poly


def main():
    import sys
    sys.path.insert(0, "scripts")
    from extract_buildings import split_by_gap
    las = laspy.read(SRC)
    pts = np.vstack([las.x, las.y, las.z]).T
    cls = np.array(las.classification)
    for bid, (xi, yi), cl, profile in CANDS:
        xa, ya = XS[xi], YS[yi]
        m = (cls == 6) & (pts[:, 0] >= xa) & (pts[:, 0] < xa + CH) & (pts[:, 1] >= ya) & (pts[:, 1] < ya + CH)
        b = pts[m]
        labels = DBSCAN(eps=2.5, min_samples=30).fit(b[:, :2]).labels_
        sel = b[labels == cl]
        parts = split_by_gap(sel)
        if len(parts) > 1:
            print(f"[{bid}] split na {len(parts)}, beru vetsi")
            sel = max(parts, key=len)
        base = np.where(m)[0][labels == cl]
        gx0, gx1 = sel[:, 0].min() - BUF, sel[:, 0].max() + BUF
        gy0, gy1 = sel[:, 1].min() - BUF, sel[:, 1].max() + BUF
        gsel = pts[(cls == 2) & (pts[:, 0] >= gx0) & (pts[:, 0] <= gx1)
                   & (pts[:, 1] >= gy0) & (pts[:, 1] <= gy1)]
        ground_z = float(np.percentile(gsel[:, 2], 5)) if len(gsel) else float(sel[:, 2].min())
        poly = footprint_polygon(sel[:, :2])
        dens = float(len(sel) / max(poly.area, 1.0))
        outdir = os.path.join("buildings", bid)
        os.makedirs(outdir, exist_ok=True)
        gmask = (cls == 2) & (pts[:, 0] >= gx0) & (pts[:, 0] <= gx1) & (pts[:, 1] >= gy0) & (pts[:, 1] <= gy1)
        las[np.union1d(base, np.where(gmask)[0])].write(os.path.join(outdir, "body.las"))
        import json as js
        gj = {"type": "FeatureCollection", "crs": {"type": "name", "properties": {"name": "EPSG:5514"}},
              "features": [{"type": "Feature", "properties": {"id": bid, "cluster": int(cl)},
                            "geometry": {"type": "Polygon", "coordinates": [list(poly.exterior.coords)]}}]}
        open(os.path.join(outdir, "footprint.geojson"), "w", encoding="utf-8").write(js.dumps(gj))
        import geopandas as gpd
        gpd.GeoDataFrame({"id": [bid], "cluster": [int(cl)]}, geometry=[poly],
                         crs="EPSG:5514").to_file(os.path.join(outdir, "footprint.gpkg"), driver="GPKG")
        meta = dict(id=bid, tile=[xi, yi], cluster=int(cl), profile=profile, crs="EPSG:5514",
                    n_points=int(len(sel)), n_ground=int(len(gsel)),
                    density_pts_m2=round(dens, 3), zstd=round(float(sel[:, 2].std()), 3),
                    zmin=round(float(sel[:, 2].min()), 2), zmax=round(float(sel[:, 2].max()), 2),
                    ground_z_p5=round(ground_z, 2),
                    height_above_ground=round(float(sel[:, 2].max() - ground_z), 2),
                    footprint_area_m2=round(float(poly.area), 1),
                    params=dict(PROFILE_PARAMS[profile]), sparse=bool(dens < 1.0))
        js.dump(meta, open(os.path.join(outdir, "meta.json"), "w", encoding="utf-8"),
                indent=1, ensure_ascii=False)
        print(f"[{bid}] tile=({xi},{yi}) cl={cl} n={len(sel)} dens={dens:.2f} "
              f"h={meta['height_above_ground']}m fp={meta['footprint_area_m2']}m2")


if __name__ == "__main__":
    main()
