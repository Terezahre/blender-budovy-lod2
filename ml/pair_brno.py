# -*- coding: utf-8 -*-
"""Parovani GT s patchi: KRAV59 pseudo-GT (dnes) + Brno LOD2 (az budou data).

Rezim KRAV59 (bezi HNED, bez stahovani):
  python ml/pair_brno.py --mode krav59
  - z output/final/<ID>_LOD2_SJTSK.obj vytahne pseudo-GT: z_ridge, z_eave,
    pocet stresnich rovin (shlukovani normal) -> typ strechy
  - porovna s heuristickym labelem z ml/patches/*.npz
  - ulozi ml/gt_krav59.json (slouzi jako GT pro ml/train_raster.py)

Rezim Brno (az budou data v ml/data_brno/):
  python ml/pair_brno.py --mode brno
  - parser Brno LOD2 SHP (S-JTSK, TopGis): autodetekce vyskovych sloupcu,
    prostorovy join na footprints.geojson (centroid do 5 m)
  - rasterizace DMP LAZ dlazdic do patchu stejneho formatu jako make_patches
  - ulozi ml/gt_brno.json + ml/patches_brno/*.npz

Pseudo-GT upozorneni: KRAV59 GT pochazi z Geoflow (tentýz system, ktery chceme
nahradit) - slouzi jen pro overeni pipeline, ne pro finalni trenink.
Finalni GT = Brno LOD2 (nezavisle, fotogrammetricke).
"""
import argparse
import glob
import json
import os

import numpy as np


def extract_gt_from_obj(path):
    """Vrati (zmin, zmax, n_roof_planes, roof_type) z OBJ geometrie."""
    verts, faces = [], []
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.startswith("v "):
                p = line.split()
                verts.append([float(p[1]), float(p[2]), float(p[3])])
            elif line.startswith("f "):
                idx = [int(p.split("/")[0]) - 1 for p in line.split()[1:]]
                if len(idx) >= 3:
                    faces.append(idx)
    verts = np.array(verts, float)
    if len(verts) == 0 or not faces:
        return None
    zmin, zmax = float(verts[:, 2].min()), float(verts[:, 2].max())
    # normaly trojuhelniku, jen vzhuru (strechy)
    normals, areas = [], []
    for idx in faces:
        tri = verts[np.array(idx[:3])]
        n = np.cross(tri[1] - tri[0], tri[2] - tri[0])
        a = float(np.linalg.norm(n))
        if a < 1e-9:
            continue
        n = n / a
        if n[2] > 0.5:  # sklon do ~60 stupnu = strecha
            normals.append(n)
            areas.append(a / 2)
    normals = np.array(normals)
    # shlukovani normal (10 stupnu) vazene plochou
    planes = []
    if len(normals):
        order = np.argsort(areas)[::-1]
        for i in order:
            n = normals[i]
            for p in planes:
                if float(np.dot(n, p)) > np.cos(np.radians(10)):
                    break
            else:
                planes.append(n)
    n_planes = len(planes)
    h = zmax - zmin
    if n_planes <= 1 and h < 4:
        rtype = 0  # flat
    elif n_planes <= 2:
        rtype = 1  # gable
    else:
        rtype = 2  # hip/complex
    return dict(zmin=zmin, zmax=zmax, n_planes=n_planes, roof_type=rtype)


def mode_krav59():
    gt = {}
    rows = []
    for npz in sorted(glob.glob(os.path.join("ml", "patches", "*.npz"))):
        bid = os.path.splitext(os.path.basename(npz))[0]
        obj = os.path.join("output", "final", bid + "_LOD2_SJTSK.obj")
        if not os.path.exists(obj):
            rows.append((bid, "bez final OBJ (zamítnuto/nevalidováno)", None))
            continue
        g = extract_gt_from_obj(obj)
        d = np.load(npz)
        heur = int(d["label_roof"])
        # relativni vyska hrebene nad terenem (ground z meta.json, S-JTSK)
        ground = None
        mpath = os.path.join("buildings", bid, "meta.json")
        if os.path.exists(mpath):
            ground = json.load(open(mpath, encoding="utf-8")).get("ground_z_p5")
        ridge_rel = round(g["zmax"] - ground, 2) if ground is not None else None
        gt[bid] = dict(z_ridge_gt=g["zmax"], z_eave_gt=float(d["z_eave"] + 0),
                       n_planes=g["n_planes"], roof_type_gt=g["roof_type"],
                       roof_type_heuristic=heur, ridge_rel=ridge_rel,
                       z_ridge_patch=float(d["z_ridge"]), z_eave_patch=float(d["z_eave"]))
        ok = "OK " if heur == g["roof_type"] else "DIFF"
        rows.append((bid, f"GT={g['roof_type']}({g['n_planes']}rovin) heur={heur} "
                          f"hGT={g['zmax'] - g['zmin']:.1f}m", ok))
    os.makedirs("ml", exist_ok=True)
    json.dump(gt, open("ml/gt_krav59.json", "w", encoding="utf-8"), indent=1)
    for bid, info, flag in rows:
        print(f"[{bid}] {info}" + (f" {flag}" if flag else ""))
    agree = sum(1 for v in gt.values() if v["roof_type_gt"] == v["roof_type_heuristic"])
    print(f"Shoda heuristika vs Geoflow-GT: {agree}/{len(gt)}; -> ml/gt_krav59.json")
    print("POZOR: pseudo-GT z Geoflow - jen pro overeni pipeline, ne pro finalni trenink.")


# STRECHA_KOD (Brno SceneServer/SHP): 1=sedlova 2=mansardova 3=plocha 4=pultova
#   5=stanova 6=valbova 7=jina  -> mapovani na nase 0/1/2
STRECHA_MAP = {3: 0, 1: 1, 4: 1, 2: 2, 5: 2, 6: 2, 7: 2}
ROOFFORM_MAP = {"flat": 0, "plocha": 0, "gable": 1, "sedlova": 1, "pultova": 1,
                "hip": 2, "valbova": 2, "mansard": 2, "stanova": 2, "jina": 2,
                "other": 2}


def mode_brno():
    """Parser lokalniho Brno Polygon-Z SHP (rucni download, viz FETCH_LOG.md).
    Ocekavane sloupce (realne schema sluzby): RUIAN_IBO, PATA_VYSKA, HREBEN_VYSKA,
    ABS_VYSKA, STRECHA_KOD, ROK_POROZENI. Toleruje i SHP s ROOFFORM/BLDGHEIGHT.
    Vystup: ml/gt_brno.json {ruian_ibo: {ridge, eave, roof_type, rok}}.
    """
    import geopandas as gpd
    ddir = os.path.join("ml", "data_brno")
    shp_cands = glob.glob(os.path.join(ddir, "brno_lod2", "**", "*.shp"), recursive=True)
    if not shp_cands:
        print("Brno LOD2 SHP chybi. Manualni kroky (viz ml/data_brno/FETCH_LOG.md):")
        print("  1) data.brno.cz -> 3D model budov -> Polygon Z S-JTSK (cele Brno / MC Brno-stred)")
        print("     nebo aplikace Teren_A_Budovy_Ke_Stazeni (ctverce 1x1 km v bboxu).")
        print("  2) Rozbalit do ml/data_brno/brno_lod2/ a spustit znovu.")
        print("  Mezitím: DSM raster jde stahnout automaticky: python scripts/fetch_brno_dsm.py")
        return
    gdf = gpd.read_file(shp_cands[0])
    print(f"SHP: {shp_cands[0]} | objektu: {len(gdf)} | CRS: {gdf.crs}")
    print(f"sloupce: {list(gdf.columns)}")
    cols = {c.lower(): c for c in gdf.columns}

    def pick(*names):
        for n in names:
            if n.lower() in cols:
                return cols[n.lower()]
        return None

    c_ruian = pick("RUIAN_IBO", "KOD_RUIAN", "ruian")
    c_ridge = pick("HREBEN_VYSKA", "BLDGHEIGHT", "ridge")
    c_eave = pick("PATA_VYSKA", "EAVEHEIGHT", "eave", "okap")
    c_roof = pick("STRECHA_KOD", "ROOFFORM", "typ_strechy")
    c_rok = pick("ROK_POROZENI", "ROK_PORIZENI", "rok", "year")
    gt = {}
    for i, r in gdf.iterrows():
        key = str(r[c_ruian]) if c_ruian else str(i)
        if c_roof and str(r[c_roof]).strip().isdigit():
            rt = STRECHA_MAP.get(int(r[c_roof]), 2)
        elif c_roof:
            rt = ROOFFORM_MAP.get(str(r[c_roof]).strip().lower(), 2)
        else:
            rt = None
        gt[key] = dict(
            ridge=float(r[c_ridge]) if c_ridge and r[c_ridge] == r[c_ridge] else None,
            eave=float(r[c_eave]) if c_eave and r[c_eave] == r[c_eave] else None,
            roof_type=rt,
            rok=int(r[c_rok]) if c_rok and r[c_rok] == r[c_rok] else None,
        )
    json.dump(gt, open(os.path.join("ml", "gt_brno.json"), "w", encoding="utf-8"), indent=1)
    roofs = [v["roof_type"] for v in gt.values() if v["roof_type"] is not None]
    from collections import Counter
    print(f"GT zaznamu: {len(gt)} | typy {dict(Counter(roofs))} (0=flat 1=gable 2=hip/complex)")
    print("-> ml/gt_brno.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["krav59", "brno"], default="krav59")
    a = ap.parse_args()
    if a.mode == "krav59":
        mode_krav59()
    else:
        mode_brno()


if __name__ == "__main__":
    main()
