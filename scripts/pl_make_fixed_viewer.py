# -*- coding: utf-8 -*-
"""Viewer opraveneho domu (three.js): LOD22 vs boolean-fixed vs final + GT.
Vystup: render/pl_fixed_viewer.html (samostatny soubor, geometrie inline).
Beh: python scripts/pl_make_fixed_viewer.py
"""
import json
import os
import xml.etree.ElementTree as ET

import numpy as np

FID = "ID-1465-38F62225-F3F5-F520-E053-CA2BA8C0BE14"
GML = r"C:\Users\Tereza\.t3\worktrees\Blender_projekt\t3-f6940c75-0f8474738a846f6b\data_pl\Modele_3D\1465_N-34-139-A-c-1-1.gml"
GMLID = "{http://www.opengis.net/gml}id"
D = f"output/pl_geof/{FID}"
MODELS = {
    "GT_LoD2": ("gml", None),
    "GEOFLOW": ("obj", f"{D}/model_lod22.obj"),
    "BOOL": ("obj", f"{D}/model_bool.obj"),
    "FINAL": ("obj", f"{D}/model_final.obj"),
}
OUT = "render/pl_fixed_viewer.html"
NAMES = {"GT_LoD2": "GUGiK LoD2 GT", "GEOFLOW": "Geoflow LOD22 (jehly)",
         "BOOL": "boolean-fixed (sjednocene vikýře)", "FINAL": "final (validovany)"}
COLORS = {"GT_LoD2": 0xb0603c, "GEOFLOW": 0x4d7fb0, "BOOL": 0x4da06a, "FINAL": 0x9a6ac8}


def load_obj_centered(path):
    V, F = [], []
    for line in open(path, encoding="utf-8"):
        if line.startswith("v "):
            V.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("f "):
            F.append([int(x.split("/")[0]) - 1 for x in line.split()[1:]])
    V = np.array(V)
    off = V.mean(axis=0)
    V = V - off
    pos, idx = [], []
    for f in F:
        base = len(pos)
        P = V[np.array(f)]
        for i in range(1, len(P) - 1):
            for p in (P[0], P[i], P[i + 1]):
                pos.append([round(float(v), 3) for v in p])
            idx.append([base, base + 1, base + 2])
            base += 3
    return {"pos": pos, "idx": idx, "nverts": int(len(V)),
            "nfaces": int(len(F)), "offset": [round(float(v), 2) for v in off]}


def load_gt():
    tris = []
    for _ev, b in ET.iterparse(GML, events=("end",)):
        if not b.tag.endswith("}Building"):
            continue
        if b.attrib.get(GMLID) != FID:
            continue
        for d in b.iter():
            t = d.tag.split("}")[1] if "}" in d.tag else d.tag
            if t == "Polygon":
                P = []
                for p in d.iter():
                    tt = p.tag.split("}")[1] if "}" in p.tag else p.tag
                    if tt == "pos":
                        P.append([float(v) for v in p.text.split()])
                P = np.array(P)
                for i in range(1, len(P) - 1):
                    tris.append(P[[0, i, i + 1]])
        b.clear()
        break
    V = np.array([t for tri in tris for t in tri])
    off = V.mean(axis=0)
    pos = [[round(float(v), 3) for v in (p - off)] for tri in tris for p in tri]
    idx = [[i * 3, i * 3 + 1, i * 3 + 2] for i in range(len(tris))]
    return {"pos": pos, "idx": idx, "nverts": int(len(V)),
            "nfaces": int(len(tris)), "offset": [round(float(v), 2) for v in off]}


HTML = """<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="utf-8">
<title>Varšava ID-1465: puvodni vs opravene vikýře (three.js)</title>
<style>
  body { margin:0; font-family:system-ui,sans-serif; background:#111; color:#eee; }
  #ui { position:fixed; top:10px; left:10px; background:#1c1c1cee; padding:12px 14px;
        border-radius:10px; max-width:360px; font-size:14px; }
  #ui h3 { margin:0 0 8px; font-size:15px; }
  #ui button { margin:2px; padding:5px 10px; border:0; border-radius:6px; cursor:pointer; }
  #ui button.active { background:#e08a5a; color:#111; font-weight:bold; }
  #ui .row { margin-top:8px; }
  #info { color:#bbb; font-size:12.5px; margin-top:8px; line-height:1.5; }
  canvas { display:block; }
</style>
<script type="importmap">
{ "imports": {
  "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
  "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"
} }
</script>
</head>
<body>
<div id="ui">
  <h3>ID-1465: oprava vikýřů (EPSG:2180)</h3>
  <div id="models"></div>
  <div class="row">
    <button id="bWire">Drateny model</button><button id="bRot">Rotace</button>
  </div>
  <div id="info"></div>
</div>
<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
const DATA = __DATA__;
const NAMES = __NAMES__;
const COLORS = __COLORS__;
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x111111);
const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setSize(innerWidth, innerHeight);
document.body.appendChild(renderer.domElement);
scene.add(new THREE.HemisphereLight(0xffffff, 0x334455, 1.1));
const sun = new THREE.DirectionalLight(0xffffff, 2.2);
sun.position.set(60, 90, -40); scene.add(sun);
const camera = new THREE.PerspectiveCamera(45, innerWidth/innerHeight, 0.1, 5000);
const controls = new OrbitControls(camera, renderer.domElement);
let mesh = null, state = {id:'BOOL', wire:false, rot:true};
function show() {
  const d = DATA[state.id];
  if (mesh) { scene.remove(mesh); mesh.geometry.dispose(); }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(d.pos.flat(),3));
  geo.setIndex(d.idx.flat());
  geo.computeVertexNormals();
  const mat = new THREE.MeshStandardMaterial({color:COLORS[state.id], flatShading:true,
    wireframe:state.wire, side:THREE.DoubleSide});
  mesh = new THREE.Mesh(geo, mat); scene.add(mesh);
  const box = new THREE.Box3().setFromObject(mesh), c = box.getCenter(new THREE.Vector3()),
        s = box.getSize(new THREE.Vector3()).length();
  controls.target.copy(c);
  camera.position.set(c.x+s*0.9, c.y+s*0.7, c.z-s*0.9);
  document.getElementById('info').innerHTML =
    `<b>${NAMES[state.id]}</b><br>` +
    `vrcholy: ${d.nverts}, faces: ${d.nfaces}<br>` +
    `stred EPSG:2180: ${d.offset.map(v=>v.toFixed(1)).join(', ')}`;
  document.querySelectorAll('#models button').forEach(b=>b.classList.toggle('active', b.dataset.id===state.id));
}
const box = document.getElementById('models');
Object.keys(DATA).forEach(id => {
  const b = document.createElement('button'); b.textContent = NAMES[id]; b.dataset.id = id;
  b.onclick = () => { state.id = id; show(); }; box.appendChild(b);
});
document.getElementById('bWire').onclick = e => { state.wire=!state.wire;
  e.target.classList.toggle('active', state.wire); show(); };
document.getElementById('bRot').onclick = e => { state.rot=!state.rot;
  e.target.classList.toggle('active', state.rot); };
document.getElementById('bRot').classList.add('active');
addEventListener('resize', () => { camera.aspect=innerWidth/innerHeight;
  camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); });
(function anim(){ requestAnimationFrame(anim);
  if (state.rot && mesh) mesh.rotation.y += 0.004;
  controls.update(); renderer.render(scene, camera); })();
show();
</script>
</body>
</html>
"""


def main():
    data = {}
    for tag, (kind, path) in MODELS.items():
        data[tag] = load_gt() if kind == "gml" else load_obj_centered(path)
        print(tag, data[tag]["nverts"], "v/", data[tag]["nfaces"], "f")
    html = HTML.replace("__DATA__", json.dumps(data))
    html = html.replace("__NAMES__", json.dumps(NAMES)).replace("__COLORS__", json.dumps(COLORS))
    open(OUT, "w", encoding="utf-8").write(html)
    print("-> %s (%d KB)" % (OUT, os.path.getsize(OUT) // 1024))
    # kontrola: indexy v rozsahu, JSON parsovatelny
    d = json.loads(json.dumps(data))
    for tag, m in d.items():
        assert max(i for tri in m["idx"] for i in tri) < len(m["pos"]), tag
    print("kontrola indexu OK")


if __name__ == "__main__":
    main()
