# -*- coding: utf-8 -*-
"""Three.js prohlizec vyslednych budov (POUZE Geoflow LoD2.2):
geometrie OBJ vlozena primo do HTML (zadne fetch -> funguje dvojklikem).
Three.js + OrbitControls z CDN. Vystup: viewer_3d.html (koren projektu).
"""
import json
import numpy as np

MODELS = [
    ("B01_flat", "output/final/B01_flat_LOD2_SJTSK.obj"),
    ("B02_gable", "output/final/B02_gable_LOD2_SJTSK.obj"),
    ("B03_row", "output/final/B03_row_LOD2_SJTSK.obj"),
    ("B04_panelak", "output/final/B04_panelak_LOD2_SJTSK.obj"),
    ("G1_sedlova", "output/final/G1_sedlova_LOD2_SJTSK.obj"),
    ("G2_sedlova", "output/final/G2_sedlova_LOD2_SJTSK.obj"),
    ("G3_domek", "output/final/G3_domek_LOD2_SJTSK.obj"),
    ("Z3_dum", "output/final/Z3_dum_LOD2_SJTSK.obj"),
]


def load_obj_centered(path):
    V, F = [], []
    for line in open(path, encoding="utf-8"):
        if line.startswith("v "):
            V.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("f "):
            F.append([int(x.split("/")[0]) - 1 for x in line.split()[1:]])
    V = np.array(V)
    # triangulace ngonu (fan) + S-JTSK (x,y,z) -> three Y-up (x,z,-y), centrovano
    tris = []
    for f in F:
        for i in range(1, len(f) - 1):
            tris.append([f[0], f[i], f[i + 1]])
    P = V - V.mean(axis=0)
    pos = [[float(p[0]), float(p[2]), float(-p[1])] for p in P]
    return dict(pos=pos, idx=tris,
                offset=[float(x) for x in V.mean(axis=0)],
                nverts=int(len(V)), nfaces=len(F))


data = {}
for bid, final in MODELS:
    data[bid] = load_obj_centered(final)

html = """<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="utf-8">
<title>LOD2 budovy KRAV59 — three.js prohlížeč (S-JTSK EPSG:5514)</title>
<style>
  body { margin:0; font-family:system-ui,sans-serif; background:#111; color:#eee; }
  #ui { position:fixed; top:10px; left:10px; background:#1c1c1cee; padding:12px 14px;
        border-radius:10px; max-width:330px; font-size:14px; }
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
  <h3>LOD2.2 budovy KRAV59 — Geoflow (S-JTSK)</h3>
  <div id="models"></div>
  <div class="row">
    <button id="bWire">Drátěný model</button><button id="bRot">Rotace</button>
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
let mesh = null, state = {id:'Z3_dum', wire:false, rot:true};

function colorize(geo) {
  const n = geo.attributes.position.count, col = new Float32Array(n*3);
  const nm = geo.attributes.normal, roof = new THREE.Color(0xb0603c),
        wall = new THREE.Color(0xc9a37e), floor = new THREE.Color(0x777777);
  for (let i=0;i<n;i++) {
    const ny = nm.getY(i);
    const c = ny > 0.9 ? roof : (ny < -0.9 ? floor : wall);
    col[i*3]=c.r; col[i*3+1]=c.g; col[i*3+2]=c.b;
  }
  geo.setAttribute('color', new THREE.BufferAttribute(col,3));
}
function show() {
  const d = DATA[state.id];
  if (mesh) { scene.remove(mesh); mesh.geometry.dispose(); }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(d.pos.flat(),3));
  geo.setIndex(d.idx.flat());
  geo.computeVertexNormals(); colorize(geo);
  const mat = new THREE.MeshStandardMaterial({vertexColors:true, flatShading:true,
    wireframe:state.wire, side:THREE.DoubleSide});
  mesh = new THREE.Mesh(geo, mat); scene.add(mesh);
  const box = new THREE.Box3().setFromObject(mesh), c = box.getCenter(new THREE.Vector3()),
        s = box.getSize(new THREE.Vector3()).length();
  controls.target.copy(c);
  camera.position.set(c.x+s*0.9, c.y+s*0.7, c.z-s*0.9);
  document.getElementById('info').innerHTML =
    `<b>${state.id}</b> — Geoflow LoD2.2<br>` +
    `vrcholy: ${d.nverts}, faces: ${d.nfaces}<br>` +
    `střed S-JTSK: ${d.offset.map(v=>v.toFixed(1)).join(', ')} (EPSG:5514)<br>` +
    `střecha cihlová / stěny béžové / podlaha šedá`;
  document.querySelectorAll('#models button').forEach(b=>b.classList.toggle('active', b.dataset.id===state.id));
}
const box = document.getElementById('models');
Object.keys(DATA).forEach(id => {
  const b = document.createElement('button'); b.textContent = id; b.dataset.id = id;
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
</html>"""

blob = json.dumps(data)
# prevedeni na JS-friendly: pos/idx jako vnorené listy
html = html.replace("__DATA__", blob)
open("viewer_3d.html", "w", encoding="utf-8").write(html)
import os
print("-> viewer_3d.html", round(os.path.getsize("viewer_3d.html") / 1024), "KB")
