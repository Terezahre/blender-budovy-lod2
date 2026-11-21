# -*- coding: utf-8 -*-
"""Brno nDSM patche z DSM/DTM rastru (bezi po scripts/fetch_brno_dsm.py).

Vstup: ml/data_brno/dsm/{dsm,dmt}_{NW,NE,SW,SE}.tif (S-JTSK, 0.5 m)
       + ml/data_brno/footprints.geojson (ZABAGED polygony, RUIAN prior)
       + ml/gt_brno.json (az bude rucni SHP download; jinak label=None)
Vystup: ml/patches_brno/<ruian>.npz ve STEJNEM formatu jako ml/make_patches.py
        (ndsm 64x64, dens=ones, valid_mask, stats, label_roof, z_eave, z_ridge...),
        takze je rovnou sezere ml/train_raster.py --labels ml/gt_brno.json.

nDSM = DSM - DTM; budova = ZABAGED polygon + 5 m buffer (teren z DTM uvnitr).
Vyzaduje: pip install tifffile
"""
import glob
import json
import os

import numpy as np

CELL = 0.5
SIZE = 64
BUF = 5.0


def load_tiles():
    import tifffile
    d = os.path.join("ml", "data_brno", "dsm")
    tiles = {}
    for kind in ("dsm", "dmt"):
        for name in ("NW", "NE", "SW", "SE"):
            p = os.path.join(d, f"{kind}_{name}.tif")
            if not os.path.exists(p):
                return None
            tiles[(kind, name)] = tifffile.imread(p).astype(np.float32)
    return tiles


def main():
    import geopandas as gpd
    tiles = load_tiles()
    if tiles is None:
        print("Chybi DSM/DTM TIFF. Nejdriv: python scripts/fetch_brno_dsm.py")
        return
    x0, y0 = -598500.0, -1161500.0  # musi sedet s BBOX ve fetch_brno_dsm.py
    fp = gpd.read_file(os.path.join("ml", "data_brno", "footprints.geojson"))
    gt = {}
    gp = os.path.join("ml", "gt_brno.json")
    if os.path.exists(gp):
        gt = json.load(open(gp, encoding="utf-8"))
        print(f"GT: {len(gt)} zaznamu")
    else:
        print("GT chybi (ml/gt_brno.json) - patche budou bez labelu")

    H = W = 2000
    outdir = os.path.join("ml", "patches_brno")
    os.makedirs(outdir, exist_ok=True)
    done = 0
    for _, r in fp.iterrows():
        geom = r.geometry
        if geom is None or geom.is_empty:
            continue
        cx, cy = geom.centroid.x, geom.centroid.y
        bx, by = int((cx - x0) / 1000), int((cy - y0) / 1000)
        name = {(0, 0): "SW", (0, 1): "SE", (1, 0): "NW", (1, 1): "NE"}.get((by, bx))
        if name is None:
            continue
        dsm = tiles[("dsm", name)]
        dtm = tiles[("dmt", name)]
        H, W = dsm.shape
        lx0, ly0 = (x0 + bx * 1000), (y0 + by * 1000)
        # vyrez 32x32 m kolem centroidu, bezpecne i pres hranu dlazdice
        px, py = int((cx - lx0) / CELL), int((cy - ly0) / CELL)
        s = SIZE // 2
        r0, r1 = max(py - s, 0), min(py + s, H)
        c0, c1 = max(px - s, 0), min(px + s, W)
        if r1 <= r0 or c1 <= c0:
            continue  # centroid mimo dlazdici (presah bboxu)
        cut_dsm = dsm[r0:r1, c0:c1]
        cut_dtm = dtm[r0:r1, c0:c1]
        canvas = np.full((SIZE, SIZE), np.nan, np.float32)
        orow, ocol = r0 - (py - s), c0 - (px - s)
        canvas[orow:orow + cut_dsm.shape[0], ocol:ocol + cut_dsm.shape[1]] = \
            cut_dsm - cut_dtm
        ndsm = canvas
        # interior maska: jen pixely uvnitr ZABAGED polygonu (stejna semantika
        # jako KRAV59 body.las = jen budova; ulice/teren kolem maskujeme pryc)
        from shapely import points as sh_points
        from shapely import contains as sh_contains
        ox, oy = cx - SIZE * CELL / 2, cy - SIZE * CELL / 2
        gx, gy = np.meshgrid(ox + (np.arange(SIZE) + 0.5) * CELL,
                             oy + (np.arange(SIZE) + 0.5) * CELL)
        inside = sh_contains(geom, sh_points(gx.ravel(), gy.ravel())).reshape(SIZE, SIZE)
        inside = inside & np.isfinite(ndsm)
        valid = inside.astype(np.float32)
        ndsm_m = np.where(inside, ndsm, 0.0).astype(np.float32)
        nin = int(inside.sum())
        area = float(geom.area)
        h = float(np.nanmax(np.where(inside, ndsm, np.nan))) if nin else 0.0
        zstd = float(np.nanstd(np.where(inside, ndsm, np.nan))) if nin else 0.0
        # n_points ve stejnych jednotkach jako KRAV59 (body = hustota*plocha):
        # typicka hustota DMP ~1.5 pts/m2
        stats = np.array([1.5 * nin * CELL * CELL, 1.5, zstd, h, area, 0],
                         dtype=np.float32)
        lab = -1
        key = str(r.get("KOD_RUIAN", r.get("fid_zbg", r.name)))
        if key in gt and gt[key].get("roof_type") is not None:
            lab = int(gt[key]["roof_type"])
        elif zstd < 1.2:
            lab = 0
        elif zstd < 2.5:
            lab = 1
        else:
            lab = 2
        np.savez_compressed(os.path.join(outdir, f"{key}.npz"), ndsm=ndsm_m,
                            dens=np.ones_like(ndsm_m), valid_mask=valid, stats=stats,
                            label_roof=np.int64(lab),
                            z_eave=np.float32(np.nanpercentile(
                                np.where(inside, ndsm, np.nan), 10) if nin else 0),
                            z_ridge=np.float32(h),
                            origin_xy=np.array([ox, oy]), cellsize=np.float32(CELL))
        done += 1
    print(f"Hotovo: {done} patchu -> {outdir}/ (label -1/heuristika tam kde chybi GT)")


if __name__ == "__main__":
    main()
