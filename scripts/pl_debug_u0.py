# -*- coding: utf-8 -*-
"""Debug U0 cutteru: postavi telo + 1 frézu, DIFFERENCE, statistiky."""
import json
import sys
import bpy
import bmesh

argv = sys.argv[sys.argv.index("--") + 1:]
IN_OBJ, FIX_JSON = argv[0], argv[1]

V, F = [], []
with open(IN_OBJ, encoding="utf-8") as f:
    for line in f:
        if line.startswith("v "):
            V.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("f "):
            F.append([int(x.split("/")[0]) - 1 for x in line.split()[1:]])
OFF = [min(v[i] for v in V) for i in range(3)]
print("body verts=%d faces=%d" % (len(V), len(F)))

bpy.ops.object.select_all(action="SELECT")
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new("body")
me.from_pydata([[v[0] - OFF[0], v[1] - OFF[1], v[2] - OFF[2]] for v in V], [], F)
me.update()
body = bpy.data.objects.new("body", me)
bpy.context.collection.objects.link(body)

d = json.load(open(FIX_JSON, encoding="utf-8"))[10]
print("U0:", d["id"], d["rect"], d["top_plane"], d["base_z"])
rect = [[float(p[0]), float(p[1])] for p in d["rect"]]
a, b, c0 = d["top_plane"]
tops = [a * p[0] + b * p[1] + c0 - OFF[2] for p in rect]
zb = d["base_z"] - OFF[2]
print("tops:", [round(t, 2) for t in tops], "zb:", round(zb, 2))
r = [(p[0] - OFF[0], p[1] - OFF[1]) for p in rect]
vv = [[r[0][0], r[0][1], zb - 1.0], [r[1][0], r[1][1], zb - 1.0],
      [r[2][0], r[2][1], zb - 1.0], [r[3][0], r[3][1], zb - 1.0],
      [r[0][0], r[0][1], max(tops) + 30.0], [r[1][0], r[1][1], max(tops) + 30.0],
      [r[2][0], r[2][1], max(tops) + 30.0], [r[3][0], r[3][1], max(tops) + 30.0]]
for i, v in enumerate(vv):
    print("  cut v%d: %.2f %.2f %.2f" % (i, v[0], v[1], v[2]))
mm = bpy.data.meshes.new("cut")
mm.from_pydata(vv, [], [[0, 3, 2, 1], [4, 5, 6, 7],
                       [0, 1, 5, 4], [1, 2, 6, 5],
                       [2, 3, 7, 6], [3, 0, 4, 7]])
mm.update()
cut = bpy.data.objects.new("cut", mm)
bpy.context.collection.objects.link(cut)
bpy.context.view_layer.objects.active = body
body.select_set(True)
bpy.ops.object.modifier_add(type="BOOLEAN")
md = body.modifiers[-1]
md.operation = "DIFFERENCE"
md.solver = "EXACT"
md.object = cut
bpy.ops.object.modifier_apply(modifier=md.name)
bm = bmesh.new()
bm.from_mesh(body.data)
print("po U0 DIFFERENCE: verts=%d faces=%d" % (len(bm.verts), len(bm.faces)))
bm.free()
