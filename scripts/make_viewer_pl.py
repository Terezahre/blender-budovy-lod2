# -*- coding: utf-8 -*-
"""Generator viewer_pl.html (three.js): Varsava GT vs nas model vs zjednoduseny.
Vstupy: GML (GT triangulace), output/pl_geof/.../model_lod22.obj, model_simple.obj.
Kazdy model vlastni offset (centroid), CRS EPSG:2180. Geometrie vlozena v HTML.
Beh: python scripts/make_viewer_pl.py
"""
import json
import os

import numpy as np

FID = "ID-1465-38F62225-F3F5-F520-E053-CA2BA8C0BE14"
GML = "data_pl/Modele_3D/1465_N-34-139-A-c-1-1.gml"
GMLID = "{http://www.opengis.net/gml}id"
OUR = f"output/pl_geof/{FID}/model_lod22.obj"
SIMPLE = f"output/pl_geof/{FID}/model_simple.obj"
ULTRA = f"output/pl_geof/{FID}/model_light24.obj"
OUT = "viewer_pl.html"


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
    import xml.etree.ElementTree as ET
    tris = []
    for _ev, b in ET.iterparse(GML, events=("end",)):
        if not b.tag.endswith("}Building"):
            continue
        if b.attrib.get(GMLID) != FID:
            b.clear()
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
<title>Varsava: LoD2 GT vs Geoflow vs zjednoduseny (three.js, EPSG:2180)</title>
<style>
  body { margin:0; font-family:system-ui,sans-serif; background:#111; color:#eee; }
  #ui { position:fixed; top:10px; left:10px; background:#1c1c1cee; padding:12px 14px;
        border-radius:10px; max-width:340px; font-size:14px; }
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
  <h3>Varsava: GUGiK LoD2 vs nas Geoflow (EPSG:2180)</h3>
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
let mesh = null, state = {id:'GEOFLOW', wire:false, rot:true};
const NAMES = {'GT_LoD2':'GUGiK LoD2 GT (48 tri)', 'GEOFLOW':'nas Geoflow (676 tri)', 'SIMPLE':'planar 140 tri', 'ULTRA':'nejlehci cely (24 tri)'};
const COLORS = {'GT_LoD2':0xb0603c, 'GEOFLOW':0x4d7fb0, 'SIMPLE':0x4da06a, 'ULTRA':0x9a6ac8};
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
    data = {"GT_LoD2": load_gt(), "GEOFLOW": load_obj_centered(OUR),
            "SIMPLE": load_obj_centered(SIMPLE), "ULTRA": load_obj_centered(ULTRA)}
    html = HTML.replace("__DATA__", json.dumps(data))
    open(OUT, "w", encoding="utf-8").write(html)
    print(f"-> {OUT} ({os.path.getsize(OUT)//1024} KB)")


if __name__ == "__main__":
    main()
