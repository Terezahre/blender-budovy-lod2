# -*- coding: utf-8 -*-
"""PL west15: Blender render pred/po ze stejne kamery (zapadni svah).
Beh: blender --background --python scripts/pl_west15_render.py --
Vystup: render/pl_west15_gable_before.png + render/pl_west15_gable_after.png
"""
import bpy
import mathutils
import os

L22 = "output/pl_geof/ID-1465-38F62225-F3F5-F520-E053-CA2BA8C0BE14/model_lod22.obj"
FIN = "output/pl_geof/ID-1465-38F62225-F3F5-F520-E053-CA2BA8C0BE14/model_west15_bool.obj"
RENDER_DIR = "render"

V = []
with open(L22, encoding="utf-8") as f:
    for line in f:
        if line.startswith("v "):
            V.append([float(x) for x in line.split()[1:4]])
OFF = [min(v[i] for v in V) for i in range(3)]
print("offset:", OFF)


def load_centered(path):
    tmp = path + ".centered.obj"
    with open(path, encoding="utf-8") as fin, open(tmp, "w", encoding="utf-8") as fout:
        for line in fin:
            if line.startswith("v "):
                _, x, y, z = line.split()[:4]
                fout.write("v %.4f %.4f %.4f\n" % (
                    float(x) - OFF[0], float(y) - OFF[1], float(z) - OFF[2]))
            elif line.startswith("mtllib") or line.startswith("usemtl"):
                continue
            else:
                fout.write(line)
    bpy.ops.wm.obj_import(filepath=tmp)
    ob = bpy.context.selected_objects[0]
    os.remove(tmp)
    return ob


def setup_scene(ob, tag):
    bpy.context.view_layer.objects.active = ob
    me = ob.data
    mat = bpy.data.materials.new("LOD_%s" % tag)
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (0.30, 0.45, 0.75, 1.0)
    me.materials.append(mat)
    for poly in me.polygons:
        poly.use_smooth = False


bpy.ops.object.select_all(action="SELECT")
bpy.ops.wm.read_factory_settings(use_empty=True)
ob = load_centered(L22)
setup_scene(ob, "before")

# scena: svetlo + kamera na zapadni svah (od JZ, zvenku)
bpy.context.scene.render.engine = "CYCLES"
bpy.context.scene.cycles.samples = 64
bpy.context.scene.cycles.device = "CPU"
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 720
bpy.context.scene.render.film_transparent = True
sun = bpy.data.lights.new("Sun", "SUN")
sun.energy = 4.0
so = bpy.data.objects.new("Sun", sun)
bpy.context.collection.objects.link(so)
sundir = mathutils.Vector((-0.66, -0.75, 0.9)).normalized()
so.rotation_euler = sundir.to_track_quat("-Z", "Y").to_euler()
# seedne pozadi (misto pruhledne cerne)
world = bpy.data.worlds.new("W")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.25, 0.28, 0.33, 1.0)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
bpy.context.scene.world = world
bpy.context.scene.render.film_transparent = False
xs = [v.co.x for v in ob.data.vertices]
ys = [v.co.y for v in ob.data.vertices]
zs = [v.co.z for v in ob.data.vertices]
cx, cy, cz = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2,
              (min(zs) + max(zs)) / 2)
maxdim = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs), 1.0)
cam = bpy.data.cameras.new("Cam")
cam.type = 'ORTHO'
cam.ortho_scale = 16.0
cam.clip_end = maxdim * 50.0
co = bpy.data.objects.new("Cam", cam)
bpy.context.collection.objects.link(co)
# pohled primo na zapadni svah: cil = stred pasu vikýru, strmeji shora
dcx, dcy, dcz = (18.0, 16.0, 16.5)
direction = mathutils.Vector((0.751, -0.660, 0.02)).normalized()
co.location = (mathutils.Vector((dcx, dcy, dcz)) + direction * maxdim * 1.9).to_tuple()
d = mathutils.Vector((dcx, dcy, dcz)) - co.location
co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = co
bpy.context.scene.render.filepath = os.path.abspath(
    os.path.join(RENDER_DIR, "pl_west15_gable_before.png"))
bpy.ops.render.render(write_still=True)
print("OK before")

bpy.data.objects.remove(ob, do_unlink=True)
ob2 = load_centered(FIN)
setup_scene(ob2, "after")
bpy.context.scene.render.filepath = os.path.abspath(
    os.path.join(RENDER_DIR, "pl_west15_gable_after.png"))
bpy.ops.render.render(write_still=True)
print("OK after")
