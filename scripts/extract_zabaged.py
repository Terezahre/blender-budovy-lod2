# -*- coding: utf-8 -*-
"""Extrakce domu se ZABAGED footprintem (presny katastralni polygon).
body.las = class 6 v polygonu + buffer + class 2 teren; profil dle zstd.
"""
import json
import numpy as np
import laspy
import geopandas as gpd

FIDS = [
    ("Z1_dum", "10823132080242688"),
    ("Z2_dum", "10348047762456576"),
    ("Z3_dum", "9844434610946048"),
]
BUF = 5.0
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


def main():
    import os
    zab = gpd.read_file("buildings/zabaged_krav59.gpkg")
    las = laspy.read("KRAV59_DMP1G/KRAV59.laz")
    pts = np.vstack([las.x, las.y, las.z]).T
    cls = np.array(las.classification)
    for bid, fid in FIDS:
        poly = zab[zab.fid_zbg == fid].iloc[0].geometry
        x0, y0, x1, y1 = poly.bounds
        sel = pts[(cls == 6) & (pts[:, 0] >= x0) & (pts[:, 0] <= x1)
                  & (pts[:, 1] >= y0) & (pts[:, 1] <= y1)]
        inside = np.array([poly.contains(__import__("shapely").geometry.Point(p[0], p[1]))
                           for p in sel])
        b = sel[inside]
        gx0, gx1 = x0 - BUF, x1 + BUF
        gy0, gy1 = y0 - BUF, y1 + BUF
        gsel = pts[(cls == 2) & (pts[:, 0] >= gx0) & (pts[:, 0] <= gx1)
                   & (pts[:, 1] >= gy0) & (pts[:, 1] <= gy1)]
        gz = float(np.percentile(gsel[:, 2], 5)) if len(gsel) else float(b[:, 2].min())
        zstd = float(b[:, 2].std())
        profile = ("SIMPLE_FLAT" if zstd < 1.2 else
                   "STANDARD_GABLE" if zstd < 2.5 else "COMPLEX_HIP")
        outdir = os.path.join("buildings", bid)
        os.makedirs(outdir, exist_ok=True)
        bmask = np.zeros(len(pts), bool)
        bmask[np.where((cls == 6))[0][np.where(
            (pts[cls == 6][:, 0] >= x0) & (pts[cls == 6][:, 0] <= x1)
            & (pts[cls == 6][:, 1] >= y0) & (pts[cls == 6][:, 1] <= y1))[0]]] = True
        gmask = (cls == 2) & (pts[:, 0] >= gx0) & (pts[:, 0] <= gx1) \
            & (pts[:, 1] >= gy0) & (pts[:, 1] <= gy1)
        las[np.union1d(np.where(bmask)[0], np.where(gmask)[0])].write(
            os.path.join(outdir, "body.las"))
        gpd.GeoDataFrame({"id": [bid]}, geometry=[poly],
                         crs="EPSG:5514").to_file(os.path.join(outdir, "footprint.gpkg"), driver="GPKG")
        gj = {"type": "FeatureCollection", "crs": {"type": "name", "properties": {"name": "EPSG:5514"}},
              "features": [{"type": "Feature", "properties": {"id": bid},
                            "geometry": {"type": "Polygon", "coordinates": [list(poly.exterior.coords)]}}]}
        json.dump(gj, open(os.path.join(outdir, "footprint.geojson"), "w", encoding="utf-8"))
        meta = dict(id=bid, zabaged_fid=fid, profile=profile, crs="EPSG:5514",
                    n_points=int(len(b)), n_ground=int(len(gsel)),
                    density_pts_m2=round(float(len(b) / max(poly.area, 1)), 3),
                    zstd=round(zstd, 3), ground_z_p5=round(gz, 2),
                    height_above_ground=round(float(b[:, 2].max() - gz), 2),
                    footprint_area_m2=round(float(poly.area), 1),
                    params=dict(PROFILE_PARAMS[profile]), sparse=False)
        json.dump(meta, open(os.path.join(outdir, "meta.json"), "w", encoding="utf-8"),
                  indent=1, ensure_ascii=False)
        print(f"[{bid}] n={len(b)} zstd={zstd:.2f} h={meta['height_above_ground']}m "
              f"fp={meta['footprint_area_m2']}m2 profil={profile}")


if __name__ == "__main__":
    main()
