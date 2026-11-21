# -*- coding: utf-8 -*-
"""Odvozeny flowchart pro KRAV59: instalovany gfc-brecon bez
CityJSONWriter a OGRWriter (nesoulad parametru meta_poc_address s pluginem
a nepotrebne DB vystupy). Rekonstrukcni matematika zustava identicka.
Vystupy: OBJ LOD12/13/22. Dale generuje per-building TOML z profilu agents.md.
"""
import copy
import json
import os

SRC = r"C:\Users\Tereza\geoflow-local\share\share\geoflow\gfc-brecon\single\reconstruct.json"
DST = "flowcharts/krav59_lod22/reconstruct_objonly.json"

DROP_NODES = {"OGRWriter-LoD11", "OGRWriter-LoD12",
              "OGRWriter-LoD12-3D", "OGRWriter-LoD13", "OGRWriter-LoD13-3D",
              "OGRWriter-LoD22", "OGRWriter-LoD22-3D"}
DROP_GLOBALS = {"output_cj_identifier", "output_cj_poc_address",
                "output_cj_poc_phone", "output_cj_title",
                "output_ogr", "output_ogr_EPSG", "output_ogr_format",
                "output_ogr_overwrite"}
# parametry CityJSONWriter, ktere instalovany plugin nezna (overeno ve strings DLL)
DROP_CJ_PARAMS = {"CRS", "meta_identifier", "meta_poc_address",
                  "meta_poc_phone", "meta_title", "prettyPrint"}

fc = json.load(open(SRC, encoding="utf-8"))
fc["nodes"] = {n: d for n, d in fc["nodes"].items() if n not in DROP_NODES}
# povyseni uzitecnych ladicich parametru na globaly (dialog + TOML):
fc["nodes"]["BuildArrFromLines"]["parameters"]["max_arr_complexity"] = "{{r_max_arr_complexity}}"
fc["nodes"]["SegmentRasterise"]["parameters"]["cellsize"] = "{{r_raster_cellsize}}"
fc["globals"]["r_max_arr_complexity"] = [
    "maximum arrangement complexity; higher keeps more roof detail but is slower",
    "int", 400]
fc["globals"]["r_raster_cellsize"] = [
    "heightfield raster cellsize in meters; match point spacing (e.g. 0.5 for 2 pts/m2)",
    "float", 0.05000000074505806]
# spojeni na smazane uzly pryc + oprava CityJSONWriter parametru
for n, d in fc["nodes"].items():
    conns = d.get("connections", {})
    for k in list(conns.keys()):
        conns[k] = [c for c in conns[k] if c[0] not in DROP_NODES]
cj = fc["nodes"]["CityJSONWriter"]["parameters"]
for p in DROP_CJ_PARAMS:
    cj.pop(p, None)
print("CityJSONWriter params:", sorted(cj.keys()))
# atributy dovnitr CityJSON (rmse, val3dity, pokryti; DetectPlanes klice tato
# verze flowchartu nepropaguje - overeno)
cj["output_attribute_names"] = {
    "SkipReplaceTester.replace": "lod11_replace",
    "SkipReplaceTester.roof_type": "roof_type",
    "SkipReplaceTester.skip": "reconstruction_skipped",
    "PC2MeshQuality-LoD12.mesh_error_f": "rmse_lod12",
    "PC2MeshQuality-LoD13.mesh_error_f": "rmse_lod13",
    "PC2MeshQuality-LoD22.mesh_error_f": "rmse_lod22",
    "Validator-LoD12.errors": "val12",
    "Validator-LoD13.errors": "val13",
    "Validator-LoD22.errors": "val22",
    "DataCoverageCalc.data_coverage": "data_coverage",
}
fc["globals"] = {k: v for k, v in fc["globals"].items() if k not in DROP_GLOBALS}

os.makedirs(os.path.dirname(DST), exist_ok=True)
json.dump(fc, open(DST, "w", encoding="utf-8"), indent=1)
print(f"STANDARD: uzlu: {len(fc['nodes'])}, globalu: {len(fc['globals'])} -> {DST}")

# DETAIL varianta pro overene sedlovky (G3): nedissolvovat segmentove hrany
# LoD22 + volnejsi snapping linii; ostatni parametry (vc. bunky a komplexity)
# se ridici stejnymi globaly, jen profily nesou jine hodnoty
fc_d = copy.deepcopy(fc)
fc_d["nodes"]["ArrDissolve-LoD22"]["parameters"]["dissolve_seg_edges"] = False
fc_d["nodes"]["RegulariseLines"]["parameters"]["angle_threshold"] = 0.44999998807907104
DST_D = "flowcharts/krav59_lod22/reconstruct_detail.json"
json.dump(fc_d, open(DST_D, "w", encoding="utf-8"), indent=1)
print(f"DETAIL: -> {DST_D}")

# --- per-building TOML (mapovani profilu agents.md -> r_* globaly) ---
PROFILES = {
    "SIMPLE_FLAT": dict(r_plane_epsilon=0.25, r_plane_k=15, r_plane_min_points=20,
                        r_normal_k=8, r_line_epsilon=0.5,
                        r_optimisation_data_term=5.0, r_lod13_step_height=3.0,
                        r_max_arr_complexity=400, r_raster_cellsize=0.05),
    "STANDARD_GABLE": dict(r_plane_epsilon=0.20, r_plane_k=15, r_plane_min_points=15,
                           r_normal_k=8, r_line_epsilon=0.4,
                           r_optimisation_data_term=7.0, r_lod13_step_height=3.0,
                           r_max_arr_complexity=400, r_raster_cellsize=0.05),
    "COMPLEX_HIP": dict(r_plane_epsilon=0.15, r_plane_k=10, r_plane_min_points=10,
                        r_normal_k=5, r_line_epsilon=0.3,
                        r_optimisation_data_term=9.0, r_lod13_step_height=2.5,
                        r_max_arr_complexity=400, r_raster_cellsize=0.05),
    # overene sedlovky (G3): uzka detekce + vysoky data-term + DETAIL flowchart
    "DETAIL_GABLE": dict(r_plane_epsilon=0.10, r_plane_k=8, r_plane_min_points=8,
                         r_normal_k=5, r_line_epsilon=0.3,
                         r_optimisation_data_term=15.0, r_lod13_step_height=2.5,
                         r_max_arr_complexity=1500, r_raster_cellsize=0.5),
}
import glob
import json as js
BIDS = sorted(js.load(open(m, encoding="utf-8"))["id"]
             for m in glob.glob("buildings/*/meta.json"))
for bid in BIDS:
    meta = js.load(open(f"buildings/{bid}/meta.json", encoding="utf-8"))
    pr = dict(PROFILES[meta["profile"]])
    if meta.get("sparse"):
        pr["r_plane_epsilon"] = round(pr["r_plane_epsilon"] + 0.05, 3)
        pr["r_plane_min_points"] = int(pr["r_plane_min_points"] * 1.5)
        pr["r_plane_k"] += 5
        pr["r_line_epsilon"] = round(pr["r_line_epsilon"] + 0.1, 3)
        pr["r_optimisation_data_term"] = float(pr["r_optimisation_data_term"] - 2.0)
    lines = [f"# {bid} — profil {meta['profile']} (geof r_* globaly)"]
    lines.append(f'input_footprint = "buildings/{bid}/footprint.gpkg"')
    lines.append(f'input_pointcloud = "buildings/{bid}/body.las"')
    lines.append('building_identifier = "id"')
    lines.append('input_footprint_select_sql = ""')
    lines.append(f'output_obj_lod22 = "output/geof/{bid}/model_lod22.obj"')
    lines.append(f'output_obj_lod12 = "output/geof/{bid}/model_lod12.obj"')
    lines.append(f'output_obj_lod13 = "output/geof/{bid}/model_lod13.obj"')
    lines.append(f'output_cityjson = "output/geof/{bid}/model.json"')
    lines.append('output_cj_referenceSystem = "http://www.opengis.net/def/crs/EPSG/0/5514"')
    for k, v in pr.items():
        lines.append(f"{k} = {v}")
    open(f"buildings/{bid}/geof.toml", "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"  {bid}: {meta['profile']} eps={pr['r_plane_epsilon']} minpts={pr['r_plane_min_points']}")
