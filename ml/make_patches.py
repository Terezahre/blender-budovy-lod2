# -*- coding: utf-8 -*-
"""Generator nDSM patchu pro CPU trenovani (raster-U-Net cesta).

Vstup (bezi HNED, bez stahovani): existujici buildings/*/body.las + meta.json
  python ml/make_patches.py --src buildings --out ml/patches
Vstup (az bude Brno): ml/data_brno/laz/*.laz + footprints + brno_lod2
  python ml/make_patches.py --src ml/data_brno --out ml/patches_brno

Vystup per budova: ml/patches/<ID>.npz s poli:
  ndsm (HxH float32, 0.5m rastr, centrovany, NaN->0 + maska),
  dens (HxH hustota), valid_mask (HxH),
  stats (n_points, density, zstd, height, area, roofplane_guess),
  label_roof (0=flat zstd<1.2, 1=gable 1.2-2.5, 2=hip/complex>=2.5; heuristika z meta.json,
              po Brne se nahradi GT typem z LOD2),
  z_eave, z_ridge (odhad z percentilu, po Brne GT),
  origin_xy (offset pro navrat do S-JTSK), cellsize.

Zamerne jen numpy/laspy (jde na CPU bez torch).
"""
import argparse
import json
import os
import glob

import numpy as np

CELL = 0.5
SIZE = 64  # 64x64 px = 32x32 m pokryti, staci na vetsinu domu


def label_from_zstd(zstd):
    if zstd < 1.2:
        return 0
    if zstd < 2.5:
        return 1
    return 2


def rasterize(xyz, x0, y0):
    h = np.full((SIZE, SIZE), np.nan, np.float32)
    cnt = np.zeros((SIZE, SIZE), np.float32)
    ix = ((xyz[:, 0] - x0) / CELL).astype(int)
    iy = ((xyz[:, 1] - y0) / CELL).astype(int)
    ok = (ix >= 0) & (ix < SIZE) & (iy >= 0) & (iy < SIZE)
    ix, iy = ix[ok], iy[ok]
    z = xyz[ok][:, 2]
    for a, b, zz in zip(ix, iy, z):
        if np.isnan(h[b, a]) or zz > h[b, a]:
            h[b, a] = zz
        cnt[b, a] += 1
    return h, cnt


def process_building(bdir, outdir):
    bid = os.path.basename(bdir.rstrip(os.sep))
    las_path = os.path.join(bdir, "body.las")
    meta_path = os.path.join(bdir, "meta.json")
    if not (os.path.exists(las_path) and os.path.exists(meta_path)):
        return None
    import laspy
    meta = json.load(open(meta_path, encoding="utf-8"))
    las = laspy.read(las_path)
    pts = np.vstack([las.x, las.y, las.z]).T
    if len(pts) == 0:
        return None
    cx, cy = pts[:, 0].mean(), pts[:, 1].mean()
    x0, y0 = cx - (SIZE * CELL) / 2, cy - (SIZE * CELL) / 2
    h, cnt = rasterize(pts, x0, y0)
    ground = float(meta.get("ground_z_p5", np.nanmin(h)))
    ndsm = h - ground
    valid = (~np.isnan(ndsm)).astype(np.float32)
    ndsm = np.nan_to_num(ndsm, nan=0.0).astype(np.float32)
    stats = np.array([
        float(meta.get("n_points", len(pts))),
        float(meta.get("density_pts_m2", meta.get("density", 0))),
        float(meta.get("zstd", meta.get("z_std", 0))),
        float(meta.get("height_above_ground", meta.get("height_range", 0))),
        float(meta.get("footprint_area_m2", 0)),
        float(meta.get("roofplane_guess", 0)),
    ], dtype=np.float32)
    zstd = float(stats[2])
    out = dict(
        ndsm=ndsm, dens=cnt.astype(np.float32), valid_mask=valid, stats=stats,
        label_roof=np.int64(label_from_zstd(zstd)),
        z_eave=np.float32(np.percentile(pts[:, 2], 10) - ground),
        z_ridge=np.float32(np.percentile(pts[:, 2], 98) - ground),
        origin_xy=np.array([x0, y0], dtype=np.float64), cellsize=np.float32(CELL),
    )
    os.makedirs(outdir, exist_ok=True)
    np.savez_compressed(os.path.join(outdir, bid + ".npz"), **out)
    return bid, stats, int(out["label_roof"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="buildings")
    ap.add_argument("--out", default=os.path.join("ml", "patches"))
    a = ap.parse_args()
    bdirs = sorted(glob.glob(os.path.join(a.src, "*")))
    bdirs = [d for d in bdirs if os.path.isdir(d)]
    done = []
    for d in bdirs:
        try:
            r = process_building(d, a.out)
        except Exception as e:
            print("SKIP", d, e)
            continue
        if r:
            done.append(r)
            print(f"[{r[0]}] stats={np.round(r[1], 2).tolist()} label={r[2]}")
    print(f"Hotovo: {len(done)} patchu -> {a.out}/")


if __name__ == "__main__":
    main()
