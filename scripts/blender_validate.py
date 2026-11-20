# -*- coding: utf-8 -*-
"""Blender validace + finalizace LOD2 (headless).
Proc: geof/polyfit OBJ v S-JTSK ma velke souradnice (~7e5) - Blender interne
pouziva float32, proto se mesh centruje (offset), cisti a pri exportu se
offset v textu OBJ vrati zpet. Geometrie se NEMENI (zadny scale/posun site).
Kroky (mirror Val3dity): merge-by-distance 1 mm, recalc normals,
non-manifold statistika,degenerovane faces = 0, export + render nahled.
Pouziti: blender --background --python scripts/blender_validate.py -- <in.obj> <out.obj> <render.png>
"""
import bpy
import bmesh
import sys
import os

argv = sys.argv[sys.argv.index("--") + 1:]
IN_OBJ, OUT_OBJ, RENDER_PNG = argv[0], argv[1], argv[2]

# offset: min. roh (stabilni, deterministicky)
_min = [1e18, 1e18, 1e18]
with open(IN_OBJ, encoding="utf-8") as f:
    for line in f:
        if line.startswith("v "):
            _, x, y, z = line.split()[:4]
            _min[0] = min(_min[0], float(x))
            _min[1] = min(_min[1], float(y))
            _min[2] = min(_min[2], float(z))
OFF = _min
print(f"offset: {OFF}")

# cista scena
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.wm.read_factory_settings(use_empty=True)

# import s centrováním: predcti OBJ a odecti offset pri zapisu docasneho souboru
tmp = IN_OBJ + ".centered.obj"
with open(IN_OBJ, encoding="utf-8") as fin, open(tmp, "w", encoding="utf-8") as fout:
    for line in fin:
        if line.startswith("v "):
            _, x, y, z = line.split()[:4]
            fout.write(f"v {float(x) - OFF[0]:.4f} {float(y) - OFF[1]:.4f} "
                       f"{float(z) - OFF[2]:.4f}\n")
        else:
            fout.write(line)
bpy.ops.wm.obj_import(filepath=tmp)
ob = bpy.context.selected_objects[0]
bpy.context.view_layer.objects.active = ob
me = ob.data

# statistika pred cistenim
bm = bmesh.new()
bm.from_mesh(me)
bm.edges.ensure_lookup_table()
nonman_pre = sum(1 for e in bm.edges if not e.is_manifold)
loose_pre = sum(1 for v in bm.verts if not v.link_edges)
bm.free()

# cleanup: merge 1 mm, smaz volne, prepocitej normaly
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=0.001)
bpy.ops.mesh.delete_loose()
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode='OBJECT')

bm = bmesh.new()
bm.from_mesh(ob.data)
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()
nonman_post = sum(1 for e in bm.edges if not e.is_manifold)
deg = sum(1 for fa in bm.faces if fa.calc_area() < 1e-8 or len(fa.verts) < 3)
nv, nf = len(bm.verts), len(bm.faces)
bm.free()
print(f"verts={nv} faces={nf} nonmanifold: {nonman_pre}->{nonman_post} "
      f"loose_verts={loose_pre} degenerate={deg}")

# export + vraceni offsetu v textu
tmp_out = OUT_OBJ + ".centered.obj"
bpy.ops.wm.obj_export(filepath=tmp_out, export_selected_objects=True,
                      export_materials=False)
with open(tmp_out, encoding="utf-8") as fin, open(OUT_OBJ, "w", encoding="utf-8") as fout:
    fout.write(f"# LOD2.2 S-JTSK EPSG:5514 offset=[{OFF[0]:.3f},{OFF[1]:.3f},{OFF[2]:.3f}]\n")
    for line in fin:
        if line.startswith("v "):
            _, x, y, z = line.split()[:4]
            fout.write(f"v {float(x) + OFF[0]:.3f} {float(y) + OFF[1]:.3f} "
                       f"{float(z) + OFF[2]:.3f}\n")
        else:
            fout.write(line)
os.remove(tmp)
os.remove(tmp_out)

# render nahled: CYCLES na CPU (spolehlivy v headless), slunce + kamera fit
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
# kamera: bounding sphere fit, dostatecny odstup
xs = [v.co.x for v in ob.data.vertices]
ys = [v.co.y for v in ob.data.vertices]
zs = [v.co.z for v in ob.data.vertices]
cx, cy, cz = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2,
              (min(zs) + max(zs)) / 2)
maxdim = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs), 1.0)
cam = bpy.data.cameras.new("Cam")
cam.lens = 28
cam.clip_start = maxdim / 100.0
cam.clip_end = maxdim * 50.0
co = bpy.data.objects.new("Cam", cam)
bpy.context.collection.objects.link(co)
import mathutils
direction = mathutils.Vector((1.0, -1.0, 0.7)).normalized()
co.location = (mathutils.Vector((cx, cy, cz)) + direction * maxdim * 2.2).to_tuple()
d = mathutils.Vector((cx, cy, cz)) - co.location
co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = co
mat = bpy.data.materials.new("LOD2")
mat.use_nodes = True
bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
bsdf.inputs['Base Color'].default_value = (0.75, 0.45, 0.30, 1.0)
ob.data.materials.append(mat)
# ploche stinovani: LOD2 roviny se musi cist jako roviny
for poly in ob.data.polygons:
    poly.use_smooth = False
bpy.context.scene.render.filepath = os.path.abspath(RENDER_PNG)
print("camera:", bpy.context.scene.camera)
ret = bpy.ops.render.render(write_still=True)
print("render ret:", ret, "exists:", os.path.exists(os.path.abspath(RENDER_PNG)))
print(f"OK: {OUT_OBJ} + {RENDER_PNG}")
