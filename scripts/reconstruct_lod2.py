# -*- coding: utf-8 -*-
"""LOD2.2 rekonstrukce jedne budovy (Geoflow-kompatibilni postup).
Vstup: buildings/<ID>/{body.las, footprint.geojson, meta.json}
Postup (mirror Geoflow gfc-lod13 nodes):
  DetectPlanes (sekvencni RANSAC, parametry z meta.json) ->
  SegmentRasterise/heightfield (2.5D Delaunay) ->
  ArrExtruder LoD2.2 (stena z hranice site + podlaha) ->
  Validator (planaritu, manifold) -> OBJ v S-JTSK (EPSG:5514, bez posunu).
Vystup: output/geoflow/<ID>/{model_lod22.obj, planes.json, report.json}
"""
import json
import os
import sys
import numpy as np
import laspy

ID = sys.argv[1] if len(sys.argv) > 1 else "B01_flat"
BDIR = os.path.join("buildings", ID)
ODIR = os.path.join("output", "geoflow", ID)
os.makedirs(ODIR, exist_ok=True)

RNG = np.random.default_rng(42)


def load_inputs():
    las = laspy.read(os.path.join(BDIR, "body.las"))
    pts = np.vstack([las.x, las.y, las.z]).T
    cls = np.array(las.classification)
    meta = json.load(open(os.path.join(BDIR, "meta.json"), encoding="utf-8"))
    gj = json.load(open(os.path.join(BDIR, "footprint.geojson"), encoding="utf-8"))
    poly_coords = gj["features"][0]["geometry"]["coordinates"][0]
    from shapely.geometry import Polygon
    footprint = Polygon(poly_coords)
    return pts[cls == 6], meta, footprint


def fit_plane(points):
    """Nejmenší čtverce: vrací (a,b,c,d) pro ax+by+cz+d=0, |n|=1 + RMSE."""
    c = points.mean(axis=0)
    _, _, vt = np.linalg.svd(points - c, full_matrices=False)
    n = vt[-1]
    if n[2] < 0:
        n = -n
    d = -float(n @ c)
    dist = np.abs(points @ n + d)
    rmse = float(np.sqrt((dist ** 2).mean()))
    return np.append(n, d), rmse


def ransac_planes(pts, eps, min_pts, max_planes=8, iters=400):
    """Sekvenční RANSAC extrakce rovin. Vrací list dictů {plane, idx, rmse}."""
    remaining = np.arange(len(pts))
    planes = []
    for _ in range(max_planes):
        if len(remaining) < min_pts:
            break
        P = pts[remaining]
        best_inliers, best_n = None, np.zeros(4)
        for _ in range(iters):
            s = RNG.choice(len(P), 3, replace=False)
            v1, v2 = P[s[1]] - P[s[0]], P[s[2]] - P[s[0]]
            n = np.cross(v1, v2)
            L = np.linalg.norm(n)
            if L < 1e-9:
                continue
            n = n / L
            if n[2] < 0:
                n = -n
            d = -float(n @ P[s[0]])
            inl = np.where(np.abs(P @ n + d) < eps)[0]
            if best_inliers is None or len(inl) > len(best_inliers):
                best_inliers, best_n = inl, np.append(n, d)
                if len(inl) > 0.95 * len(P):
                    break
        if best_inliers is None or len(best_inliers) < min_pts:
            break
        plane, rmse = fit_plane(P[best_inliers])
        planes.append(dict(plane=[float(x) for x in plane],
                           idx=remaining[best_inliers].tolist(), rmse=rmse))
        mask = np.ones(len(remaining), bool)
        mask[best_inliers] = False
        remaining = remaining[mask]
    return planes, remaining.tolist()


def snap_to_plane(xy, plane):
    a, b, c, d = plane
    return (-(a * xy[:, 0] + b * xy[:, 1] + d) / c)


def box_part(x0, x1, y0, y1, z0, z1, inset_poly=None):
    """Kvadrovy dil: 8 vrcholu, 12 trojuhelniku (bez spodku, ten resi podlaha).
    Pokud inset_poly je dan, steny kopiruji jeho hranici (misto obdelniku)."""
    if inset_poly is None:
        corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    else:
        corners = list(inset_poly.exterior.coords)[:-1]
    n = len(corners)
    top = [(x, y, z1) for x, y in corners]
    bot = [(x, y, z0) for x, y in corners]
    verts = top + bot
    faces = []
    fan = list(reversed(range(n)))
    faces.append(tuple(fan))  # strecha: zespodu vypada CCW, shora +Z (prave pravidlo)
    bfan = list(range(n, 2 * n))
    faces.append(tuple(bfan))  # spodek dilu: -Z (uzavreny solid, skryty uvnitr)
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j))
        faces.append((i, n + j, n + i))
    return verts, faces


def build_stepped(roof_pts, footprint, ground_z):
    """LOD1.3-style stupnovite kvadry pro ploche strechy (vsechny roviny horizontalni).
    Urovne = shluky Z s mezerou > 1.0 m; kazda uroven vlastni footprint.
    Vystup: multisolid (uzavrene kvadry), geof-compatible."""
    z = roof_pts[:, 2]
    order = np.argsort(z)
    levels, cur = [], [order[0]]
    for i in order[1:]:
        if z[i] - z[cur[-1]] > 1.0:
            levels.append(np.array(cur))
            cur = [i]
        cur.append(i)
    levels.append(np.array(cur))
    from shapely.geometry import MultiPoint
    verts, faces = [], []
    prev_fp, prev_z = None, ground_z
    has_ground_box = False
    for lv in levels:
        pts = roof_pts[lv]
        fp = MultiPoint(pts[:, :2]).convex_hull.simplify(0.3, preserve_topology=True)
        if fp.geom_type != "Polygon" or fp.area < 1.0:
            continue
        lz = float(np.median(pts[:, 2]))
        base = prev_z if (prev_fp is not None and prev_fp.contains(fp.centroid)) else ground_z
        if lz - base < 0.5:
            continue
        v, f = box_part(0, 0, 0, 0, base, lz, inset_poly=fp)
        if abs(base - ground_z) < 0.01:
            # spodni kvadr stoji na zemi: jeho spodek = podlaha budovy,
            # globalni floor-fan se vynecha (duplicita -> non-manifold)
            has_ground_box = True
        off = len(verts)
        verts.extend(v)
        faces.extend([tuple(x + off for x in t) for t in f])
        prev_fp, prev_z = fp, lz
    if not has_ground_box:
        # podlaha: footprint na ground_z (fan)
        cx, cy = float(footprint.centroid.x), float(footprint.centroid.y)
        ring = list(footprint.exterior.coords)[:-1]
        ci = len(verts)
        verts.append((cx, cy, float(ground_z)))
        base_idx = len(verts)
        for x, y in ring:
            verts.append((float(x), float(y), float(ground_z)))
        for i in range(len(ring)):
            faces.append((ci, base_idx + i, base_idx + (i + 1) % len(ring)))
    return np.array(verts), faces, []


def build_lod22(roof_pts, labels, planes, footprint, ground_z, eps):
    # ploche strechy -> stupnovite kvadry (Geoflow LoD1.2/1.3 ekvivalent,
    # pro flat-roof data totozne s LoD2.2 vystupem); sikme strechy -> heightfield
    if all(abs(pl["plane"][2]) > 0.97 for pl in planes):
        verts, faces, bnd = build_stepped(roof_pts, footprint, ground_z)
        if len(faces) == 0:  # fallback kdyby level-split selhal
            verts = np.column_stack([roof_pts[:, 0], roof_pts[:, 1],
                                     np.full(len(roof_pts), ground_z)])
            faces, bnd = [], []
        return verts, faces, bnd
    from scipy.spatial import Delaunay, cKDTree
    # každému bodu přiřaď rovinu (nezařazené → nejbližší rovina do 3*eps,
    # jinak generalizace medianem sousedu: kominy/antenny do LOD2 nepatri)
    n = len(roof_pts)
    lab = np.full(n, -1, int)
    for pi, pl in enumerate(planes):
        lab[pl["idx"]] = pi
    nozzle = np.where(lab == -1)[0]
    seg = np.where(lab != -1)[0]
    if len(nozzle) and len(planes):
        P = np.array([pl["plane"] for pl in planes])
        dists = np.abs(roof_pts[nozzle] @ P[:, :3].T + P[:, 3])
        best, bd = np.argmin(dists, axis=1), dists.min(axis=1)
        near = bd < 3 * eps
        lab[nozzle[near]] = best[near]
        far = nozzle[~near]
        if len(far) and len(seg):
            _, ix = cKDTree(roof_pts[seg][:, :2]).query(roof_pts[far][:, :2], k=5)
            zseg = np.empty(n)
            for pi, pl in enumerate(planes):
                m = lab == pi
                zseg[m] = snap_to_plane(roof_pts[m][:, :2], pl["plane"])
            lab[far] = -2  # znacka: median sousedu
            z = zseg
            z[far] = np.median(zseg[seg[ix]], axis=1)
        else:
            z = np.empty(n)
            for pi, pl in enumerate(planes):
                m = lab == pi
                z[m] = snap_to_plane(roof_pts[m][:, :2], pl["plane"])
            z[lab == -2] = z[seg].mean() if len(seg) else ground_z
    else:
        z = np.empty(n)
        for pi, pl in enumerate(planes):
            m = lab == pi
            z[m] = snap_to_plane(roof_pts[m][:, :2], pl["plane"])
    # Delaunay v XY + ořez footprintem (centroid uvnitř) + stop spikum:
    # trojúhelníky s hranou > 4 m překlenují díry v datech → pryč
    tri = Delaunay(roof_pts[:, :2])
    cent = roof_pts[tri.simplices][:, :, :2].mean(axis=1)
    from shapely import contains_xy
    inside = contains_xy(footprint, cent[:, 0], cent[:, 1])
    T = roof_pts[tri.simplices]
    elen = np.stack([np.linalg.norm(T[:, 0] - T[:, 1], axis=1),
                     np.linalg.norm(T[:, 1] - T[:, 2], axis=1),
                     np.linalg.norm(T[:, 2] - T[:, 0], axis=1)], axis=1).max(axis=1)
    inside = inside & (elen < 4.0)
    # ploche strechy: trojuhelniky pres vyskovy skok (>0.5 m) jsou artefakt
    # pres ulicku/dvur mezi urovnemi -> pryc; urovne se uzavrou stenami k zemi.
    # Plati jen pro vodorovne roviny; sikme strechy (hrebene) se nefiltruji.
    if all(abs(pl["plane"][2]) > 0.97 for pl in planes):
        zT = z[tri.simplices]
        zrange = zT.max(axis=1) - zT.min(axis=1)
        inside = inside & (zrange < 0.5)
    tris = tri.simplices[inside]
    verts = np.column_stack([roof_pts[:, 0], roof_pts[:, 1], z])
    # stěny: hraniční hrany (použité 1×) → kvádry dolů na ground_z
    from collections import Counter
    ec = Counter()
    for t in tris:
        for e in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            ec[e] += 1
            ec[(e[1], e[0])] += 0  # jen orientované počítání níže
    # hrana je hraniční, pokud se opačná nevyskytuje
    fwd = Counter()
    for t in tris:
        for e in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            fwd[e] += 1
    wall_quads = [e for e in fwd if fwd[(e[1], e[0])] == 0]
    nv = len(verts)
    gverts = verts.tolist()
    faces = [tuple(int(x) for x in t.tolist()) for t in tris]
    ground_pairs = []
    k = nv
    for (i, j) in wall_quads:
        i, j = int(i), int(j)
        gverts.append([float(verts[i, 0]), float(verts[i, 1]), float(ground_z)])
        gverts.append([float(verts[j, 0]), float(verts[j, 1]), float(ground_z)])
        gi, gj = k, k + 1
        k += 2
        faces.append((i, j, gj))
        faces.append((i, gj, gi))
        ground_pairs.append((gi, gj))
    # podlaha: fan z centroidu pres spodni hrany sten (uzavreny okruh)
    cx, cy = float(footprint.centroid.x), float(footprint.centroid.y)
    gverts.append([cx, cy, float(ground_z)])
    ci = len(gverts) - 1
    for (gi, gj) in ground_pairs:
        faces.append((ci, gj, gi))
    gverts = np.array(gverts)
    return gverts, faces, wall_quads


def validate(gverts, faces):
    """Lehký validátor (mirror Val3dity): degenerované faces + rozsah."""
    v = np.asarray(gverts)
    ndeg = 0
    for f in faces:
        if len(set(f)) < 3:
            ndeg += 1
            continue
        p = v[list(f)[:3]]
        if np.linalg.norm(np.cross(p[1] - p[0], p[2] - p[0])) < 1e-10:
            ndeg += 1
    return dict(n_verts=int(len(v)), n_faces=len(faces),
                degenerate=int(ndeg), zmin=float(v[:, 2].min()),
                zmax=float(v[:, 2].max()))


def write_obj(path, verts, faces, header="S-JTSK EPSG:5514"):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {header}\n")
        for v in verts:
            f.write(f"v {v[0]:.3f} {v[1]:.3f} {v[2]:.3f}\n")
        for fa in faces:
            f.write("f " + " ".join(str(int(i) + 1) for i in fa) + "\n")


def main():
    roof_pts_full, meta, footprint = load_inputs()
    p = meta["params"]
    eps = float(p["plane_detect__epsilon"])
    min_pts = int(p["plane_detect__min_points"])
    ground_z = float(meta["ground_z_p5"])
    # jen střešní body: nad ground + 1.5 m (odfiltruje zbytky terénu)
    roof_pts = roof_pts_full[roof_pts_full[:, 2] > ground_z + 1.5]
    if len(roof_pts) < min_pts:
        roof_pts = roof_pts_full
    # DSM filtr: v každé 0.5m XY buňce jen nejvyšší bod (odstraní fasády,
    # které by v 2.5D triangulaci dělaly svislé pruhy). Mirror SegmentRasterise.
    cell = 0.5
    gx = np.floor((roof_pts[:, 0] - roof_pts[:, 0].min()) / cell).astype(int)
    gy = np.floor((roof_pts[:, 1] - roof_pts[:, 1].min()) / cell).astype(int)
    best = {}
    for i, (ix, iy) in enumerate(zip(gx, gy)):
        k = (ix, iy)
        if k not in best or roof_pts[i, 2] > roof_pts[best[k], 2]:
            best[k] = i
    roof_pts = roof_pts[np.array(sorted(best.values()))]
    # outlier filtr (kNN): body dale od sousedu nez median+3*MAD pryc
    # (vegetace/chyby klasifikace delaji spiky v Delaunay)
    if len(roof_pts) > 10:
        from scipy.spatial import cKDTree
        dd, _ = cKDTree(roof_pts[:, :2]).query(roof_pts[:, :2], k=6)
        md = dd[:, 1:].mean(axis=1)
        med, mad = float(np.median(md)), float(np.median(np.abs(md - np.median(md)))) + 1e-9
        keep = md < med + 6 * mad
        if keep.sum() >= min_pts:
            roof_pts = roof_pts[keep]
    planes, rest = ransac_planes(roof_pts, eps, min_pts)
    # klasifikace rovin (mirror DetectPlanes metriky)
    for pl in planes:
        nz = abs(pl["plane"][2])
        pl["type"] = ("horizontal" if nz > 0.97 else
                      "wall" if nz < 0.30 else "slant")
    roof_planes = [pl for pl in planes if pl["type"] != "wall"]
    if not roof_planes:
        roof_planes = planes[:1]
    verts, faces, bnd = build_lod22(roof_pts, None, roof_planes, footprint, ground_z, eps)
    val = validate(verts, faces)
    # RMSE vůči vstupním bodům (mirror PC2MeshQuality)
    P = np.array([pl["plane"] for pl in roof_planes])
    d = np.abs(roof_pts @ P[:, :3].T + P[:, 3]) if len(P) else np.zeros((len(roof_pts), 1))
    rmse = float(np.sqrt((d.min(axis=1) ** 2).mean())) if len(P) else -1.0
    write_obj(os.path.join(ODIR, "model_lod22.obj"), verts, faces,
              header=f"LOD2.2 {ID} S-JTSK EPSG:5514 profil {meta['profile']}")
    # mapování indexů rovin zpět na roof_pts pro planes.json
    with open(os.path.join(ODIR, "planes.json"), "w", encoding="utf-8") as f:
        json.dump([{"plane": pl["plane"], "type": pl["type"], "rmse": pl["rmse"],
                    "n_points": len(pl["idx"])} for pl in roof_planes], f, indent=1)
    report = dict(id=ID, profile=meta["profile"], crs="EPSG:5514",
                  n_roof_points=int(len(roof_pts)), n_planes=len(roof_planes),
                  plane_types=[pl["type"] for pl in roof_planes],
                  rmse_roof=float(rmse), unsegmented=int(len(rest)),
                  validation=val, params=p)
    with open(os.path.join(ODIR, "report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1, ensure_ascii=False)
    print(f"[{ID}] rovin={len(roof_planes)} "
          f"({', '.join(pl['type'] for pl in roof_planes)}) rmse={rmse:.3f}m "
          f"verts={val['n_verts']} faces={val['n_faces']} deg={val['degenerate']}")
    print(f"-> {ODIR}/model_lod22.obj")


if __name__ == "__main__":
    main()
