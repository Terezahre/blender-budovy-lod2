# -*- coding: utf-8 -*-
"""CityJSON pipeline: geof (model.json) -> cjio lod_filter 2.2 -> OBJ ->
Blender validace -> output/final. Vse S-JTSK.
"""
import glob
import os
import subprocess

GEOF = r"C:\Users\Tereza\geoflow-local\geof.exe"
FC = "flowcharts/krav59_lod22/reconstruct_objonly.json"
BLENDER = r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe"

env = dict(os.environ, GF_PLUGIN_FOLDER=r"C:\Users\Tereza\geoflow-local\plugins")
BIDS = sorted(os.path.basename(os.path.dirname(m)) for m in glob.glob("buildings/*/geof.toml"))

for bid in BIDS:
    odir = f"output/geof/{bid}"
    print(f"===== {bid} =====", flush=True)
    r = subprocess.run([GEOF, FC, "--config", f"buildings/{bid}/geof.toml"],
                       capture_output=True, text=True, env=env)
    if r.returncode != 0:
        print("GEOF FAIL", r.stderr[-500:] if r.stderr else r.stdout[-500:])
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
