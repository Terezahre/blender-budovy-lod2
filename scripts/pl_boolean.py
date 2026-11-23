# -*- coding: utf-8 -*-
"""PL dum: boolean cleanup vikýřů v Blenderu (headless).
Pro kazdy regularizovany vikýř: DIFFERENCE rezaci kostkou (rect x [zb-1, +inf))
smaze stare boule nad patou vcetne presahu; UNION hranolu da cisty tvar.
Vstup: model_lod22.obj + data_pl/dormers_fixed.json (vse EPSG:2180)
Vystup: model_fixed_bool.obj (EPSG:2180, offset vracen)
Beh: blender --background --python scripts/pl_boolean.py -- <in> <json> <out>
"""
import json
import sys

import bpy
import bmesh

argv = sys.argv[sys.argv.index("--") + 1:]
IN_OBJ, FIX_JSON, OUT_OBJ = argv[0], argv[1], argv[2]

# --- nacteni OBJ v Pythonu (bez importeru) -------------------------------
V, F = [], []
with open(IN_OBJ, encoding="utf-8") as f:
    for line in f:
        if line.startswith("v "):
            V.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("f "):
            F.append([int(x.split("/")[0]) - 1 for x in line.split()[1:]])
import math
OFF = [min(v[i] for v in V) for i in range(3)]
print("verts=%d faces=%d offset=%s" % (len(V), len(F), OFF))
Vc = [[v[0] - OFF[0], v[1] - OFF[1], v[2] - OFF[2]] for v in V]

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.wm.read_factory_settings(use_empty=True)

me = bpy.data.meshes.new("body")
me.from_pydata(Vc, [], F)
me.update()
body = bpy.data.objects.new("body", me)
bpy.context.collection.objects.link(body)
bpy.context.view_layer.objects.active = body
body.select_set(True)


def box_obj(name, rect, z0, z1):
    r = [(rect[0][0] - OFF[0], rect[0][1] - OFF[1]),
         (rect[1][0] - OFF[0], rect[1][1] - OFF[1]),
         (rect[2][0] - OFF[0], rect[2][1] - OFF[1]),
         (rect[3][0] - OFF[0], rect[3][1] - OFF[1])]
    vv = [[r[0][0], r[0][1], z0], [r[1][0], r[1][1], z0],
          [r[2][0], r[2][1], z0], [r[3][0], r[3][1], z0],
          [r[0][0], r[0][1], z1], [r[1][0], r[1][1], z1],
          [r[2][0], r[2][1], z1], [r[3][0], r[3][1], z1]]
    ff = [[0, 3, 2, 1], [4, 5, 6, 7],
          [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
    mm = bpy.data.meshes.new(name)
    mm.from_pydata(vv, [], ff)
    mm.update()
    ob = bpy.data.objects.new(name, mm)
    bpy.context.collection.objects.link(ob)
    return ob


def boolean(target, tool, op):
    bpy.context.view_layer.objects.active = target
    target.select_set(True)
    bpy.ops.object.modifier_add(type="BOOLEAN")
    md = target.modifiers[-1]
    md.name = "Bool_%s" % op
    md.operation = op
    md.solver = "EXACT"
    md.object = tool
    bpy.ops.object.modifier_apply(modifier=md.name)


ds = json.load(open(FIX_JSON, encoding="utf-8"))
for i, d in enumerate(ds):
    rect = [[float(p[0]), float(p[1])] for p in d["rect"]]
    cx = sum(p[0] for p in rect) / 4 - OFF[0]
    cy = sum(p[1] for p in rect) / 4 - OFF[1]
    a, b, c0 = d["top_plane"]
    tops = [a * p[0] + b * p[1] + c0 - OFF[2] for p in d["rect"]]
    tmax = max(tops)
    zb = d["base_z"] - OFF[2]
    cut = box_obj("cut_%d" % i, rect, zb - 1.0, tmax + 30.0)
    boolean(body, cut, "DIFFERENCE")
    bpy.data.objects.remove(cut, do_unlink=True)
    # hranol o 1 cm vetsi nez rez -> steny se schovaji do strechy
    cc = [sum(p[0] for p in rect) / 4, sum(p[1] for p in rect) / 4]
    big = [[cc[0] + (p[0] - cc[0]) * 1.01, cc[1] + (p[1] - cc[1]) * 1.01] for p in rect]
    pv = [[p[0] - OFF[0], p[1] - OFF[1], zb - 0.3] for p in big]
    for p in big:
        pv.append([p[0] - OFF[0], p[1] - OFF[1],
                   a * (p[0]) + b * (p[1]) + c0 - OFF[2]])
    pm = bpy.data.meshes.new("prism_%d" % i)
    pm.from_pydata(pv, [], [[0, 3, 2, 1], [4, 5, 6, 7],
                            [0, 1, 5, 4], [1, 2, 6, 5],
                            [2, 3, 7, 6], [3, 0, 4, 7]])
    pm.update()
    pr = bpy.data.objects.new("prism_%d" % i, pm)
    bpy.context.collection.objects.link(pr)
    boolean(body, pr, "UNION")
    bpy.data.objects.remove(pr, do_unlink=True)
    print("vikýř %d: cutter+prism hotovo" % i)

# cleanup pres bmesh (1 mm, bez risky operatoru)
bm = bmesh.new()
bm.from_mesh(body.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.edges.ensure_lookup_table()
nm = sum(1 for e in bm.edges if not e.is_manifold)
nv, nf = len(bm.verts), len(bm.faces)
bm.to_mesh(body.data)
bm.free()
print("po boolean: verts=%d faces=%d nonmanifold=%d" % (nv, nf, nm))

with open(OUT_OBJ, "w", encoding="utf-8") as f:
    f.write("# boolean-fixed dormers, EPSG:2180\n")
    for v in body.data.vertices:
        f.write("v %.3f %.3f %.3f\n" % (v.co.x + OFF[0], v.co.y + OFF[1], v.co.z + OFF[2]))
    for p in body.data.polygons:
        f.write("f " + " ".join(str(v + 1) for v in p.vertices) + "\n")
print("OK:", OUT_OBJ)
