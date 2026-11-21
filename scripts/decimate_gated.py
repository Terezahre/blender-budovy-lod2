# -*- coding: utf-8 -*-
"""Decimace s Hausdorffovou branou: co nejmene tris, zadny bod se nehne o vic
nez TOL m od originalu (symetricky Hausdorff), manifold 0, vikyre zamcene.
Postup: cleanup -> planar dissolve -> ostrůvky (vikýře < 10 % do PROTECT)
-> pro kazdy pomer: kopie, Decimate COLLAPSE s invertovanou grupou,
   Hausdorff + manifold gate -> ze vsech proslych bere nejmensi.
Pouziti: blender --background --python scripts/decimate_gated.py -- <in.obj> <out.obj> <render.png> [tol_m]
"""
import bpy
import bmesh
import sys
import os

import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
IN_OBJ, OUT_OBJ, RENDER_PNG = argv[0], argv[1], argv[2]
TOL = float(argv[3]) if len(argv) > 3 else 0.05
RATIOS = [0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.25, 0.2, 0.15, 0.1]

_min = [1e18, 1e18, 1e18]
with open(IN_OBJ, encoding="utf-8") as f:
    for line in f:
        if line.startswith("v "):
            _, x, y, z = line.split()[:4]
            _min[0] = min(_min[0], float(x))
            _min[1] = min(_min[1], float(y))
            _min[2] = min(_min[2], float(z))
OFF = _min


def mesh_arrays(ob):
    me = ob.data
    V = np.array([v.co[:] for v in me.vertices])
    F = [tuple(p.vertices) for p in me.polygons]
    return V, F


def tris_of(V, F):
    out = []
    for f in F:
        P = V[np.array(f)]
        for i in range(1, len(P) - 1):
            out.append([P[0], P[i], P[i + 1]])
    return np.array(out)


def point_tri_dist(P, T):
    """P: (N,3) body, T: (M,3,3) trojuhelniky -> (N,) min vzdalenosti."""
    A, B, C = T[:, 0], T[:, 1], T[:, 2]
    AB, AC = B - A, C - A
    best = np.full(len(P), np.inf)
    CH = 64
    for i in range(0, len(T), CH):
        a = A[i:i + CH, None, :]
        ab = AB[i:i + CH, None, :]
        ac = AC[i:i + CH, None, :]
        ap = P[None, :, :] - a
        d1 = np.einsum("knj,knj->kn", ab, ap)
        d2 = np.einsum("knj,knj->kn", ac, ap)
        d3 = np.einsum("knj,knj->kn", ab, ab)
        d4 = np.einsum("knj,knj->kn", ab, ac)
        d5 = np.einsum("knj,knj->kn", ac, ac)
        denom = d3 * d5 - d4 * d4 + 1e-18
        u = (d5 * d1 - d4 * d2) / denom
        v = (d3 * d2 - d4 * d1) / denom
        inside = (u >= 0) & (v >= 0) & (u + v <= 1)
        proj = a + np.clip(u, 0, 1)[:, :, None] * ab + np.clip(v, 0, 1)[:, :, None] * ac
        dd = np.sqrt(np.einsum("knj,knj->kn", P[None, :, :] - proj, P[None, :, :] - proj))
        dd = np.where(inside, dd, np.inf)
        # hrany pro body mimo trojuhelnik: vzdalenost k useckam
        for Q, R in ((a, a + ab), (a, a + ac), (a + ab, a + ac)):
            t = np.einsum("knj,knj->kn", P[None, :, :] - Q, R - Q)
            t /= (np.einsum("knj,knj->kn", R - Q, R - Q) + 1e-18)
            t = np.clip(t, 0, 1)
            dd = np.minimum(dd, np.sqrt(np.einsum(
                "knj,knj->kn", P[None, :, :] - (Q + t[:, :, None] * (R - Q)),
                P[None, :, :] - (Q + t[:, :, None] * (R - Q)))))
        best = np.minimum(best, dd.min(axis=0))
    return best


def hausdorff(Va, Fa, Vb, Fb):
    Ta, Tb = tris_of(Va, Fa), tris_of(Vb, Fb)
    dab = point_tri_dist(Va, Tb).max() if len(Tb) else np.inf
    dba = point_tri_dist(Vb, Ta).max() if len(Ta) else np.inf
    return float(max(dab, dba)), float(np.mean(
        np.concatenate([point_tri_dist(Va, Tb), point_tri_dist(Vb, Ta)])))


def manifold_n(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.edges.ensure_lookup_table()
    nm = sum(1 for e in bm.edges if not e.is_manifold)
    nv = len(bm.verts)
    nf = len(bm.faces)
    bm.free()
    return nv, nf, nm


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
base = bpy.context.selected_objects[0]
bpy.context.view_layer.objects.active = base

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=0.001)
bpy.ops.mesh.delete_loose()
bpy.ops.mesh.normals_make_consistent(inside=False)
import math
bpy.ops.mesh.dissolve_limited(angle_limit=math.radians(0.5), delimit={'NORMAL'})
bpy.ops.object.mode_set(mode='OBJECT')

# vikyre do PROTECT (ostruvky < 10 % nejvetsiho)
bm = bmesh.new()
bm.from_mesh(base.data)
bm.faces.ensure_lookup_table()
up = [f for f in bm.faces if f.normal.z > 0.5]
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
areas = [sum(g.calc_area() for g in isl) for isl in islands]
big = max(areas) if areas else 0
protect = set()
for isl, a in zip(islands, areas):
    if big > 0 and a < 0.10 * big:
        for g in isl:
            for v in g.verts:
                protect.add(v.index)
print(f"ostruvku: {len(islands)}, chraneno vrcholu: {len(protect)}", flush=True)
bm.free()
vg = base.vertex_groups.new(name="PROTECT")
if protect:
    vg.add(list(protect), 1.0, 'REPLACE')

V0, F0 = mesh_arrays(base)
print(f"start: verts={len(V0)} faces={len(F0)}", flush=True)

best = None  # (nfaces, ratio, obj_name)
for r in RATIOS:
    bpy.ops.object.select_all(action='DESELECT')
    base.select_set(True)
    bpy.ops.object.duplicate()
    cand = bpy.context.selected_objects[0]
    bpy.context.view_layer.objects.active = cand
    mod = cand.modifiers.new("Dec", 'DECIMATE')
    mod.decimate_type = 'COLLAPSE'
    mod.ratio = r
    mod.use_collapse_triangulate = True
    if protect:
        mod.vertex_group = "PROTECT"
        mod.invert_vertex_group = True
    try:
        bpy.ops.object.modifier_apply(modifier=mod.name)
    except Exception as e:
        print(f"ratio {r}: apply selhalo ({e}), mazu kandidata", flush=True)
        bpy.data.objects.remove(cand, do_unlink=True)
        continue
    nv, nf, nm = manifold_n(cand)
    if nm != 0:
        print(f"ratio {r}: faces={nf} NONMANIFOLD -> zahozeno", flush=True)
        bpy.data.objects.remove(cand, do_unlink=True)
        continue
    Vc, Fc = mesh_arrays(cand)
    hmax, hmean = hausdorff(V0, F0, Vc, Fc)
    ok = hmax <= TOL
    print(f"ratio {r}: faces={nf} Hmax={hmax*100:.1f} cm Hmean={hmean*100:.1f} cm "
          f"{'OK' if ok else 'NAD LIMITEM'}", flush=True)
    if ok and (best is None or nf < best[0]):
        if best is not None:
            bpy.data.objects.remove(best[2], do_unlink=True)
        best = (nf, r, cand)
    else:
        bpy.data.objects.remove(cand, do_unlink=True)

if best is None:
    print("ZADNY pomer neprosel branou, beru planar verzi", flush=True)
    winner, wratio = base, 1.0
else:
    _, wratio, winner = best
    bpy.data.objects.remove(base, do_unlink=True)
bpy.context.view_layer.objects.active = winner
winner.select_set(True)
ob = winner
nv, nf, nm = manifold_n(ob)
print(f"VITEZ: ratio={wratio} verts={nv} faces={nf} nonmanifold={nm}", flush=True)

tmp_out = OUT_OBJ + ".centered.obj"
bpy.ops.wm.obj_export(filepath=tmp_out, export_selected_objects=True,
                      export_materials=False)
with open(tmp_out, encoding="utf-8") as fin, open(OUT_OBJ, "w", encoding="utf-8") as fout:
    fout.write(f"# gated decimate tol={TOL}m ratio={wratio}, offset={OFF}\n")
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
