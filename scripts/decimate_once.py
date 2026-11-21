# -*- coding: utf-8 -*-
"""Jednorazova decimace na cilovy pocet (bez smycky).
Pouziti: blender --background --python scripts/decimate_once.py -- <in.obj> <out.obj> <render.png> <ratio>
"""
import bpy
import bmesh
import sys
import os

argv = sys.argv[sys.argv.index("--") + 1:]
IN_OBJ, OUT_OBJ, RENDER_PNG = argv[0], argv[1], argv[2]
RATIO = float(argv[3]) if len(argv) > 3 else 0.35

_min = [1e18, 1e18, 1e18]
with open(IN_OBJ, encoding="utf-8") as f:
    for line in f:
        if line.startswith("v "):
            _, x, y, z = line.split()[:4]
            _min[0] = min(_min[0], float(x))
            _min[1] = min(_min[1], float(y))
            _min[2] = min(_min[2], float(z))
OFF = _min

bpy.ops.object.select_all(action='SELECT')
bpy.ops.wm.read_factory_settings(use_empty=True)
tmp = IN_OBJ + ".centered.obj"
with open(IN_OBJ, encoding="utf-8") as fin, open(tmp, "w", encoding="utf-8") as fout:
    for line in fin:
        if line.startswith("v "):
            _, x, y, z = line.split()[:4]
            fout.write(f"v {float(x) - OFF[0]:.4f} {float(y) - OFF[1]:.4f} "
                       f"{float(z) - OFF[2]:.4f}\n")
        elif line.startswith("mtllib") or line.startswith("usemtl"):
            continue
        else:
            fout.write(line)
bpy.ops.wm.obj_import(filepath=tmp)
ob = bpy.context.selected_objects[0]
bpy.context.view_layer.objects.active = ob
mod = ob.modifiers.new("Decimate", 'DECIMATE')
mod.decimate_type = 'COLLAPSE'
mod.ratio = RATIO
mod.use_collapse_triangulate = True
bpy.ops.object.modifier_apply(modifier=mod.name)
bm = bmesh.new()
bm.from_mesh(ob.data)
bm.edges.ensure_lookup_table()
nv, nf = len(bm.verts), len(bm.faces)
nm = sum(1 for e in bm.edges if not e.is_manifold)
bm.free()
print(f"vysledek: verts={nv} faces={nf} nonmanifold={nm}", flush=True)

tmp_out = OUT_OBJ + ".centered.obj"
bpy.ops.wm.obj_export(filepath=tmp_out, export_selected_objects=True,
                      export_materials=False)
with open(tmp_out, encoding="utf-8") as fin, open(OUT_OBJ, "w", encoding="utf-8") as fout:
    fout.write(f"# decimate {RATIO}, offset=[{OFF[0]:.3f},{OFF[1]:.3f},{OFF[2]:.3f}]\n")
    for line in fin:
        if line.startswith("v "):
            _, x, y, z = line.split()[:4]
            fout.write(f"v {float(x) + OFF[0]:.3f} {float(y) + OFF[1]:.3f} "
                       f"{float(z) + OFF[2]:.3f}\n")
        else:
            fout.write(line)
os.remove(tmp)
os.remove(tmp_out)

bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.cycles.samples = 32
bpy.context.scene.cycles.device = 'CPU'
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 720
bpy.context.scene.render.film_transparent = True
sun = bpy.data.lights.new("Sun", 'SUN')
sun.energy = 3.0
so = bpy.data.objects.new("Sun", sun)
bpy.context.collection.objects.link(so)
so.rotation_euler = (0.9, 0.0, 0.6)
xs = [v.co.x for v in ob.data.vertices]
ys = [v.co.y for v in ob.data.vertices]
zs = [v.co.z for v in ob.data.vertices]
cx, cy, cz = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2,
              (min(zs) + max(zs)) / 2)
maxdim = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs), 1.0)
cam = bpy.data.cameras.new("Cam")
cam.lens = 28
cam.clip_end = maxdim * 50.0
co = bpy.data.objects.new("Cam", cam)
bpy.context.collection.objects.link(co)
import mathutils
direction = mathutils.Vector((1.0, -1.0, 0.7)).normalized()
co.location = (mathutils.Vector((cx, cy, cz)) + direction * maxdim * 2.2).to_tuple()
d = mathutils.Vector((cx, cy, cz)) - co.location
co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = co
mat = bpy.data.materials.new("LOD")
mat.use_nodes = True
bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
bsdf.inputs['Base Color'].default_value = (0.30, 0.45, 0.75, 1.0)
ob.data.materials.append(mat)
for poly in ob.data.polygons:
    poly.use_smooth = False
bpy.context.scene.render.filepath = os.path.abspath(RENDER_PNG)
bpy.ops.render.render(write_still=True)
print(f"OK: {OUT_OBJ} + {RENDER_PNG}", flush=True)
