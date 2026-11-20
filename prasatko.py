# Prasatko s jednorozcim rohem a duhou
# Spusteni: v Blenderu pres MCP tool execute_blender_code, nebo:
#   blender --background --python prasatko.py
import bpy
import bmesh
import math
from mathutils import Vector

OUT_PNG = r"C:\Users\Tereza\Documents\Blender_projekt\prasatko.png"
OUT_BLEND = r"C:\Users\Tereza\Documents\Blender_projekt\prasatko.blend"

scene = bpy.context.scene

# ---------------------------------------------------------------- helpers
def wipe():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                 bpy.data.lights, bpy.data.cameras):
        for block in list(coll):
            if block.users == 0:
                coll.remove(block)


def mat(name, color, rough=0.5, metallic=0.0, emission=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metallic
    if emission > 0.0:
        key = 'Emission Color' if 'Emission Color' in bsdf.inputs else 'Emission'
        if key in bsdf.inputs:
            bsdf.inputs[key].default_value = (*color, 1.0)
        if 'Emission Strength' in bsdf.inputs:
            bsdf.inputs['Emission Strength'].default_value = emission
    m.diffuse_color = (*color, 1.0)
    return m


def finish(bm, name, material, loc=(0, 0, 0), rot=(0, 0, 0),
           scale=(1, 1, 1), smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    if material:
        ob.data.materials.append(material)
    ob.location = loc
    ob.rotation_euler = rot
    ob.scale = scale
    return ob


def sphere(name, loc, radius=1.0, scale=(1, 1, 1), material=None,
           rot=(0, 0, 0), segs=48, rings=24):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=radius)
    return finish(bm, name, material, loc, rot, scale)


def cyl(name, loc, r=0.1, depth=0.5, material=None, rot=(0, 0, 0),
        scale=(1, 1, 1), segs=40, r2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs,
                          radius1=r, radius2=r if r2 is None else r2, depth=depth)
    return finish(bm, name, material, loc, rot, scale)


def tube(name, points, radii, material, bevel=0.05, res=6):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = bevel
    cu.bevel_resolution = res
    cu.use_fill_caps = True
    sp = cu.splines.new('POLY')
    sp.points.add(len(points) - 1)
    for p, co, rad in zip(sp.points, points, radii):
        p.co = (*co, 1.0)
        p.radius = rad
    ob = bpy.data.objects.new(name, cu)
    scene.collection.objects.link(ob)
    ob.data.materials.append(material)
    return ob


def area_light(name, loc, energy, size, color=(1.0, 1.0, 1.0), aim=(0, 0, 1.0)):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy = energy
    ld.size = size
    ld.color = color
    ob = bpy.data.objects.new(name, ld)
    scene.collection.objects.link(ob)
    ob.location = loc
    d = Vector(aim) - Vector(loc)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return ob


wipe()

# ---------------------------------------------------------------- materials
M_PINK = mat("Pig Pink", (1.0, 0.52, 0.60), rough=0.55)
M_PINK_DARK = mat("Pig Snout", (1.0, 0.40, 0.49), rough=0.5)
M_HOOF = mat("Hoof", (0.34, 0.20, 0.24), rough=0.45)
M_EYE = mat("Eye", (0.02, 0.02, 0.03), rough=0.12)
M_BLUSH = mat("Blush", (1.0, 0.36, 0.45), rough=0.6, emission=0.15)
M_GOLD = mat("Unicorn Horn", (1.0, 0.80, 0.32), rough=0.22, metallic=1.0)
M_GOLD_HI = mat("Unicorn Horn Glow", (1.0, 0.88, 0.55), rough=0.2,
                metallic=0.9, emission=0.6)
M_GROUND = mat("Ground", (0.80, 0.90, 0.84), rough=0.9)
M_GLINT = mat("Glint", (1.0, 1.0, 1.0), rough=0.1, emission=1.5)

RAINBOW = [
    ("Red", (0.95, 0.08, 0.12)),
    ("Orange", (1.00, 0.40, 0.03)),
    ("Yellow", (1.00, 0.82, 0.05)),
    ("Green", (0.12, 0.75, 0.22)),
    ("Cyan", (0.05, 0.55, 0.95)),
    ("Indigo", (0.15, 0.20, 0.85)),
    ("Violet", (0.55, 0.15, 0.85)),
]

# ---------------------------------------------------------------- ground
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=30.0)
finish(bm, "Ground", M_GROUND, loc=(0, 0, 0), smooth=False)

# ---------------------------------------------------------------- pig body
sphere("Body", (0, 0.0, 0.82), 1.0, scale=(0.72, 0.98, 0.62), material=M_PINK)
sphere("Head", (0, -1.03, 1.02), 1.0, scale=(0.53, 0.50, 0.50), material=M_PINK)

# snout (valec otoceny podél Y)
cyl("Snout", (0, -1.50, 0.93), r=0.215, depth=0.20, material=M_PINK_DARK,
    rot=(math.radians(90), 0, 0), segs=40)
for sx, tag in ((-1, "L"), (1, "R")):
    sphere("Nostril." + tag, (0.08 * sx, -1.605, 0.945), 1.0,
           scale=(0.034, 0.02, 0.052), material=M_HOOF, segs=24, rings=12)

# eyes + highlights + blush
for sx, tag in ((-1, "L"), (1, "R")):
    sphere("Eye." + tag, (0.315 * sx, -1.38, 1.26), 0.088,
           scale=(1.0, 0.85, 1.0), material=M_EYE, segs=32, rings=20)
    sphere("EyeGlint." + tag, (0.345 * sx, -1.445, 1.30), 0.023,
           material=M_GLINT, segs=20, rings=12)
    sphere("Blush." + tag, (0.405 * sx, -1.27, 0.93), 1.0,
           scale=(0.11, 0.075, 0.088), material=M_BLUSH, segs=28, rings=16)

# ears - kuzely zmackle do stran, base na povrchu hlavy
for sx, tag in ((-1, "L"), (1, "R")):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=20,
                          radius1=0.245, radius2=0.012, depth=0.50)
    for v in bm.verts:
        v.co.z += 0.25
    finish(bm, "Ear." + tag, M_PINK, loc=(0.295 * sx, -1.00, 1.42),
           rot=(math.radians(20), math.radians(24) * sx, 0),
           scale=(1.0, 0.32, 1.0))

# legs + hooves
for sx in (-1, 1):
    for sy, sytag in ((-0.55, "F"), (0.58, "B")):
        tag = ("L" if sx < 0 else "R") + sytag
        cyl("Leg." + tag, (0.40 * sx, sy, 0.33), r=0.155, depth=0.70,
            material=M_PINK, segs=28)
        cyl("Hoof." + tag, (0.40 * sx, sy, 0.07), r=0.168, depth=0.14,
            material=M_HOOF, segs=28)

# curly tail
pts, rads = [], []
for i in range(41):
    t = i / 40.0
    a = t * math.pi * 3.1
    r = 0.16 * (1.0 - 0.45 * t)
    pts.append((r * math.cos(a), 0.03 * math.sin(a * 2.0), r * math.sin(a) + 0.16))
    rads.append(1.0 - 0.3 * t)
tube("Tail", pts, rads, M_PINK, bevel=0.035)

# ---------------------------------------------------------------- unicorn horn
HORN_R, HORN_H, HORN_TURNS = 0.145, 0.86, 3.1
HORN_LOC = (0, -1.245, 1.44)
HORN_ROT = (math.radians(20), 0, math.radians(-12))

bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=40,
                      radius1=HORN_R, radius2=0.004, depth=HORN_H)
for v in bm.verts:
    v.co.z += HORN_H / 2.0
finish(bm, "Horn", M_GOLD, loc=HORN_LOC, rot=HORN_ROT)

pts, rads = [], []
for i in range(181):
    t = i / 180.0
    a = t * math.tau * HORN_TURNS
    rr = (HORN_R * (1.0 - t) + 0.004) * 1.03
    pts.append((rr * math.cos(a), rr * math.sin(a), t * HORN_H * 0.985))
    rads.append(1.0 - 0.55 * t)
ridge = tube("HornRidge", pts, rads, M_GOLD_HI, bevel=0.026, res=4)
ridge.location = HORN_LOC
ridge.rotation_euler = HORN_ROT

sphere("HornBase", (0, -1.245, 1.445), 1.0, scale=(0.155, 0.155, 0.05),
       material=M_GOLD_HI, segs=32, rings=12)

# ---------------------------------------------------------------- rainbow
R_INNER, BAND, Y_BACK = 1.45, 0.16, 2.50

rainbow_root = bpy.data.objects.new("RainbowRoot", None)
scene.collection.objects.link(rainbow_root)
rainbow_root.location = (0, Y_BACK, 0.02)
rainbow_root.rotation_euler = (0, 0, math.radians(-13))

for i, (cname, color) in enumerate(RAINBOW):
    r0 = R_INNER + i * BAND
    bm = bmesh.new()
    segs = 96
    ring = []
    for k in range(segs + 1):
        t = math.pi * k / segs
        c, s = math.cos(t), math.sin(t)
        ring.append((bm.verts.new((r0 * c, 0.0, r0 * s)),
                     bm.verts.new(((r0 + BAND * 0.92) * c, 0.0, (r0 + BAND * 0.92) * s))))
    for k in range(segs):
        a_in, a_out = ring[k]
        b_in, b_out = ring[k + 1]
        bm.faces.new((a_in, a_out, b_out, b_in))
    bm.normal_update()
    band = finish(bm, "Rainbow." + cname,
                  mat("Rainbow " + cname, color, rough=0.35, emission=0.20),
                  loc=(0, 0, 0), smooth=False)
    sol = band.modifiers.new("Solidify", 'SOLIDIFY')
    sol.thickness = 0.05
    sol.offset = 0.0
    band.parent = rainbow_root

# little clouds at the rainbow feet
M_CLOUD = mat("Cloud", (1, 1, 1), rough=0.85, emission=0.12)
for sx in (-1, 1):
    cx = (R_INNER + 6.5 * BAND) * sx
    for dx, dy, dz, r in ((0.0, 0.0, 0.14, 0.28), (0.20, 0.08, 0.08, 0.20),
                          (-0.19, 0.06, 0.09, 0.18), (0.02, -0.10, 0.22, 0.16)):
        cl = sphere("Cloud", (cx + dx * sx, dy, dz), r,
                    scale=(1.0, 0.8, 0.75), material=M_CLOUD, segs=28, rings=16)
        cl.parent = rainbow_root

# ---------------------------------------------------------------- world + light
world = scene.world or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (0.72, 0.86, 1.0, 1.0)
bg.inputs['Strength'].default_value = 0.28

area_light("Key", (3.6, -4.2, 5.0), 780, 2.2, (1.0, 0.97, 0.92), (0, -0.4, 1.0))
area_light("Fill", (-4.6, -3.4, 2.8), 120, 6.0, (0.85, 0.92, 1.0), (0, -0.3, 1.0))
area_light("Rim", (0.6, 4.6, 4.2), 260, 3.0, (1.0, 0.95, 0.85), (0, 0.6, 1.2))

sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 2.4
sun_data.angle = math.radians(7.0)
sun_data.color = (1.0, 0.98, 0.93)
sun = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(48), 0, math.radians(215))

# ---------------------------------------------------------------- camera
tgt = bpy.data.objects.new("CamTarget", None)
scene.collection.objects.link(tgt)
tgt.location = (0.18, 0.15, 1.10)

cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 47
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (2.60, -8.10, 3.35)
con = cam.constraints.new('TRACK_TO')
con.target = tgt
con.track_axis = 'TRACK_NEGATIVE_Z'
con.up_axis = 'UP_Y'
scene.camera = cam

# ---------------------------------------------------------------- render
try:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    pass

scene.render.resolution_x = 1200
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = OUT_PNG
try:
    scene.eevee.taa_render_samples = 96
except AttributeError:
    pass
try:
    scene.eevee.use_raytracing = True
except AttributeError:
    pass

scene.view_settings.view_transform = 'AgX'
for look in ('AgX - Punchy', 'Punchy', 'AgX - Medium High Contrast'):
    try:
        scene.view_settings.look = look
        break
    except TypeError:
        continue

bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
bpy.ops.render.render(write_still=True)

meshes = [o for o in scene.objects if o.type == 'MESH']
print("PIG_OK objects=%d engine=%s" % (len(scene.objects), scene.render.engine))
