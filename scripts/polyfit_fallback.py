# -*- coding: utf-8 -*-
"""PolyFit fallback pro slozite budovy.
Vstup: buildings/<ID>/{body.las} + output/geoflow/<ID>/planes.json (RANSAC roviny).
Postup: zapis .vg (body + normaly + roviny, lokalni souradnice kvuli stabilite SCIP),
polyfit.reconstruct s vahami dle agents.md, navrat do S-JTSK.
Vystup: output/polyfit/<ID>.obj + <ID>.meta.json
"""
import json
import os
import sys
import numpy as np
import laspy

ID = sys.argv[1] if len(sys.argv) > 1 else "B03_row"
BDIR = os.path.join("buildings", ID)
ODIR = os.path.join("output", "polyfit")
os.makedirs(ODIR, exist_ok=True)

WEIGHTS = {"SIMPLE_FLAT": (0.43, 0.27, 0.30),
           "STANDARD_GABLE": (0.46, 0.27, 0.27),
           "COMPLEX_HIP": (0.50, 0.20, 0.30)}


def estimate_normals(pts, k=12):
    from scipy.spatial import cKDTree
    tree = cKDTree(pts)
    _, idx = tree.query(pts, k=k + 1)
    normals = np.empty_like(pts)
    for i, nb in enumerate(idx):
        _, _, vt = np.linalg.svd(pts[nb[1:]] - pts[nb[1:]].mean(axis=0), full_matrices=False)
        n = vt[-1]
        if n[2] < 0:
            n = -n
        normals[i] = n
    return normals


def write_vg(path, pts, normals, planes_idx, planes):
    """ASCII .vg: body, barvy, normaly, skupiny (roviny ax+by+cz+d=0)."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"num_points: {len(pts)}\n")
        for p in pts:
            f.write(f"{p[0]:.4f} {p[1]:.4f} {p[2]:.4f}\n")
        f.write(f"num_colors: {len(pts)}\n")
        for _ in pts:
            f.write("0.7 0.7 0.7\n")
        f.write(f"num_normals: {len(pts)}\n")
        for n in normals:
            f.write(f"{n[0]:.5f} {n[1]:.5f} {n[2]:.5f}\n")
        f.write(f"num_groups: {len(planes)}\n")
        for gi, pl in enumerate(planes):
            a, b, c, d = pl["plane"]
            ids = planes_idx[gi]
            f.write("group_type: 0\nnum_group_parameters: 4\n")
            f.write(f"group_parameters: {a:.6f} {b:.6f} {c:.6f} {d:.6f}\n")
            f.write(f"group_label: plane_{gi}\n")
            f.write(f"group_color: {(gi * 0.37) % 1:.2f} {(gi * 0.61) % 1:.2f} {(gi * 0.83) % 1:.2f}\n")
            f.write(f"group_num_point: {len(ids)}\n")
            f.write(" ".join(str(i) for i in ids) + "\n")
            f.write("num_children: 0\n")


def main():
    import polyfit
    sys.path.insert(0, "scripts")
    from reconstruct_lod2 import ransac_planes, fit_plane
    polyfit.initialize()
    las = laspy.read(os.path.join(BDIR, "body.las"))
    pts_all = np.vstack([las.x, las.y, las.z]).T
    cls = np.array(las.classification)
    meta = json.load(open(os.path.join(BDIR, "meta.json"), encoding="utf-8"))
    ground_z = float(meta["ground_z_p5"])
    p = meta["params"]
    bpts = pts_all[(cls == 6) & (pts_all[:, 2] > ground_z + 0.3)]
    gpts = pts_all[cls == 2]
    # vlastni RANSAC vcetne stenovych rovin (maji realnou podporu bodu)
    planes, _ = ransac_planes(bpts, float(p["plane_detect__epsilon"]),
                              int(p["plane_detect__min_points"]), max_planes=8)
    # podlaha z terennich bodu
    if len(gpts) >= 3:
        gplane, grmse = fit_plane(gpts)
        planes.append(dict(plane=[float(x) for x in gplane], idx=[], rmse=grmse,
                           ground=True))
    # body pro .vg: stavebni + teren
    pts = np.vstack([bpts, gpts]) if len(gpts) else bpts
    nb = len(bpts)
    # lokalni souradnice (stabilita solveru), offset se vrati pri exportu
    offset = pts.mean(axis=0)
    loc = pts - offset
    loc_planes, planes_idx = [], []
    for pl in planes:
        n = np.array(pl["plane"][:3])
        d = pl["plane"][3] + float(n @ offset)
        if pl.get("ground"):
            ids = list(range(nb, len(pts)))
        else:
            ids = pl["idx"]
        if len(ids) >= 3:
            loc_planes.append({"plane": [float(n[0]), float(n[1]), float(n[2]), d]})
            planes_idx.append(ids)
    nz = [(abs(pl["plane"][2]), pl) for pl in loc_planes]
    kinds = ["horizontal" if z > 0.97 else ("wall" if z < 0.30 else "slant") for z, _ in nz]
    print(f"[{ID}] rovin: {len(loc_planes)} "
          f"({', '.join(k for k in kinds)})")
    normals = estimate_normals(loc)
    vg = os.path.join(ODIR, f"{ID}.vg")
    write_vg(vg, loc, normals, list(planes_idx), list(loc_planes))
    pc = polyfit.read_point_set(vg)
    if not pc:
        print(f"[{ID}] read_point_set selhal")
        sys.exit(1)
    fw, cw, xw = WEIGHTS.get(meta["profile"], (0.43, 0.27, 0.30))
    mesh = polyfit.reconstruct(pc, polyfit.SCIP, fw, cw, xw)
    if not mesh:
        print(f"[{ID}] reconstruct selhal")
        sys.exit(1)
    tmp = os.path.join(ODIR, f"{ID}_local.obj")
    polyfit.save_mesh(tmp, mesh)
    # navrat do S-JTSK
    out = os.path.join(ODIR, f"{ID}.obj")
    with open(tmp, encoding="utf-8") as fin, open(out, "w", encoding="utf-8") as fout:
        fout.write(f"# PolyFit {ID} S-JTSK EPSG:5514 (offset vracen)\n")
        for line in fin:
            if line.startswith("v "):
                _, x, y, z = line.split()[:4]
                fout.write(f"v {float(x) + offset[0]:.3f} {float(y) + offset[1]:.3f} "
                           f"{float(z) + offset[2]:.3f}\n")
            else:
                fout.write(line)
    nf = mesh.size_of_facets() if hasattr(mesh, "size_of_facets") else -1
    with open(os.path.join(ODIR, f"{ID}.meta.json"), "w", encoding="utf-8") as f:
        json.dump(dict(id=ID, crs="EPSG:5514", method="polyfit",
                       weights=dict(fitting=fw, coverage=cw, complexity=xw),
                       n_facets=int(nf), offset=list(map(float, offset)),
                       n_points=int(len(pts))), f, indent=1)
    print(f"[{ID}] polyfit faces={nf} vahy=({fw},{cw},{xw}) -> {out}")


if __name__ == "__main__":
    main()
