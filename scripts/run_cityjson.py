# -*- coding: utf-8 -*-
"""CityJSON pipeline: geof (model.json) -> globalize -> cjio lod_filter 2.2 ->
OBJ -> Blender validace -> output/final. Vse S-JTSK.
Flowchart: STANDARD pro vse, DETAIL jen pro profil DETAIL_GABLE (overene sedlovky).
"""
import glob
import json
import os
import subprocess
import glob
import os
import subprocess

GEOF = r"C:\Users\Tereza\geoflow-local\geof.exe"
FC_STD = "flowcharts/krav59_lod22/reconstruct_objonly.json"
FC_DET = "flowcharts/krav59_lod22/reconstruct_detail.json"
BLENDER = r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe"

env = dict(os.environ, GF_PLUGIN_FOLDER=r"C:\Users\Tereza\geoflow-local\plugins")
BIDS = sorted(os.path.basename(os.path.dirname(m)) for m in glob.glob("buildings/*/geof.toml"))

for bid in BIDS:
    odir = f"output/geof/{bid}"
    print(f"===== {bid} =====", flush=True)
    meta = json.load(open(f"buildings/{bid}/meta.json", encoding="utf-8"))
    fc = FC_DET if meta.get("profile") == "DETAIL_GABLE" else FC_STD
    r = subprocess.run([GEOF, fc, "--config", f"buildings/{bid}/geof.toml"],
                       capture_output=True, text=True, env=env)
    if r.returncode != 0:
        print("GEOF FAIL", r.stderr[-500:] if r.stderr else r.stdout[-500:])
        continue
    r = subprocess.run(["python", "scripts/cityjson_globalize.py",
                        f"{odir}/model.json", f"{odir}/model_lod22.obj"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("GLOBALIZE FAIL", (r.stdout or "")[-300:])
        continue
    r = subprocess.run(["cjio", f"{odir}/model.json", "lod_filter", "2.2",
                        "export", "obj", f"{odir}/lod22.obj"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("CJIO FAIL", (r.stderr or "")[-500:])
        continue
    r = subprocess.run([BLENDER, "--background", "--python", "scripts/blender_validate.py",
                        "--", f"{odir}/lod22.obj",
                        f"output/final/{bid}_LOD2_SJTSK.obj", f"render/{bid}.png"],
                       capture_output=True, text=True)
    ok = [l for l in r.stdout.splitlines() if l.startswith(("verts=", "OK:"))]
    print(" | ".join(ok) if ok else "BLENDER FAIL " + (r.stderr or "")[-300:])
print("HOTOVO")
