# -*- coding: utf-8 -*-
"""Chytrá decimace LOD: vikýře a detaily zamknout, decimovat jen velké plochy.
Postup: cleanup -> planar dissolve -> ostrůvky vzhůru miricich faces (spojitost
pres vrcholy) -> male ostrůvky (< 10 % nejvetsiho) = vikýře/kominy -> vertex
group PROTECT -> Decimate COLLAPSE s invertovanou grupou (chrani vikýře).
Pouziti: blender --background --python scripts/decimate_smart.py -- <in.obj> <out.obj> <render.png>
"""
import bpy
import bmesh
import sys
import os

argv = sys.argv[sys.argv.index("--") + 1:]
IN_OBJ, OUT_OBJ, RENDER_PNG = argv[0], argv[1], argv[2]

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
me = ob.data


def stats(tag):
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    nv, nf = len(bm.verts), len(bm.faces)
    nm = sum(1 for e in bm.edges if not e.is_manifold)
    bm.free()
    print(f"[{tag}] verts={nv} faces={nf} nonmanifold={nm}", flush=True)
    return nv, nf, nm


stats("import")
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=0.001)
bpy.ops.mesh.delete_loose()
bpy.ops.mesh.normals_make_consistent(inside=False)
import math
bpy.ops.mesh.dissolve_limited(angle_limit=math.radians(0.5), delimit={'NORMAL'})
bpy.ops.object.mode_set(mode='OBJECT')
stats("cleanup+planar")

# ostrůvky strech: souvisle vzhuru mirici faces
bm = bmesh.new()
bm.from_mesh(me)
bm.faces.ensure_lookup_table()
bm.verts.ensure_lookup_table()
up = [f for f in bm.faces
      if (f.calc_center_median_weighted() is not None and f.normal.z > 0.5)]
seen, islands = set(), []
for f in up:
    if f.index in seen:
        continue
    stack, isl = [f], []
    while stack:
        g = stack.pop()
        if g.index in seen:
            continue
        seen.add(g.index)
        isl.append(g)
        for e in g.edges:
            for h in e.link_faces:
                if h in up and h.index not in seen:
                    stack.append(h)
    islands.append(isl)
islands.sort(key=lambda isl: -sum(g.calc_area() for g in isl))
areas = [sum(g.calc_area() for g in isl) for isl in islands]
print(f"ostruvku strech: {len(islands)}, plochy: {[round(a, 1) for a in areas]}", flush=True)

# vikýře = ostrůvky mensi nez 10 % nejvetsiho
big = areas[0] if areas else 0
protect = set()
for isl, a in zip(islands, areas):
    if big > 0 and a < 0.10 * big:
        for g in isl:
            for v in g.verts:
                protect.add(v.index)
print(f"chranenych vrcholu (vikýře): {len(protect)}", flush=True)
bm.free()

vg = ob.vertex_groups.new(name="PROTECT")
if protect:
    vg.add(list(protect), 1.0, 'REPLACE')

# kolaps jen nechráněných, postupne, s hlidanim manifoldu
nf_prev = len(me.polygons)
for i, ratio in enumerate([0.5, 0.35]):
    mod = ob.modifiers.new(f"Smart{i}", 'DECIMATE')
    mod.decimate_type = 'COLLAPSE'
    mod.ratio = ratio
    mod.use_collapse_triangulate = True
    if protect:
        mod.vertex_group = "PROTECT"
        mod.invert_vertex_group = True
    bpy.ops.object.modifier_apply(modifier=mod.name)
    _, nf, nm = stats(f"collapse-{ratio}")
    if nm != 0:
        print("manifold porusen, stop", flush=True)
        break
    if nf >= nf_prev:
        print("bez pokroku, stop", flush=True)
        break
    nf_prev = nf

tmp_out = OUT_OBJ + ".centered.obj"
bpy.ops.wm.obj_export(filepath=tmp_out, export_selected_objects=True,
                      export_materials=False)
with open(tmp_out, encoding="utf-8") as fin, open(OUT_OBJ, "w", encoding="utf-8") as fout:
    fout.write(f"# smart decimate, offset=[{OFF[0]:.3f},{OFF[1]:.3f},{OFF[2]:.3f}]\n")
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
