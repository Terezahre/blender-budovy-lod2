# -*- coding: utf-8 -*-
"""
Budova zememerickych a katastralnich uradu (CUZK)
Pod sidlistem 1800/9, Praha 8 - Kobylisy

Parametricka rekonstrukce hmoty a fasady podle fotografií.
1 jednotka = 1 metr.
"""
import bpy, bmesh, math, os
from mathutils import Vector, Matrix

PROJ = r"C:\Users\Tereza\Documents\Blender_projekt"
RENDER_DIR = os.path.join(PROJ, "render")
os.makedirs(RENDER_DIR, exist_ok=True)

SCENE = bpy.context.scene
COLL_NAME = "CUZK_Kobylisy"

# ---------------------------------------------------------------- parametry
X_W = -44.0          # zapadni koncova stena
X_J = 16.0           # spara mezi hlavni hmotou a zaoblenym kridlem
X_ARC = 33.0         # stred zaobleni
ARC_R = 10.0
HALF_D = 10.0        # polovina hloubky (predni fasada y=-10, zadni y=+10)
Z_GF = 4.6           # vyska prizemi
FLOOR_H = 3.4
N_UP = 5
Z_TOP = Z_GF + FLOOR_H * N_UP      # 21.6
ENT_X0, ENT_X1 = -14.2, -1.8       # otvor vstupu
ENT_TOP = Z_GF + 1.42              # 6.02

# ---------------------------------------------------------------- uklid
if COLL_NAME in bpy.data.collections:
    c = bpy.data.collections[COLL_NAME]
    for ob in list(c.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.collections.remove(c)
coll = bpy.data.collections.new(COLL_NAME)
SCENE.collection.children.link(coll)

# puvodni objekty jen presuneme do skryte kolekce (nic se nemaze)
prev = bpy.data.collections.get("Previous_Model")
if prev is None:
    prev = bpy.data.collections.new("Previous_Model")
    SCENE.collection.children.link(prev)
for ob in list(SCENE.collection.objects):
    prev.objects.link(ob)
    SCENE.collection.objects.unlink(ob)
prev.hide_render = True
prev.hide_viewport = True

# ---------------------------------------------------------------- materialy
def M(name, rgb, rough=0.5, metal=0.0):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    m.diffuse_color = (rgb[0], rgb[1], rgb[2], 1.0)
    return m

MATS = {
    "mint":      M("CUZK_Fasada_Mint",   (0.297, 0.537, 0.452), 0.55),
    "white":     M("CUZK_Fasada_White",  (0.720, 0.725, 0.700), 0.55),
    "glass":     M("CUZK_Sklo",          (0.022, 0.040, 0.050), 0.08, 0.55),
    "glassdark": M("CUZK_Sklo_Tmave",    (0.010, 0.018, 0.022), 0.12, 0.45),
    "orange":    M("CUZK_Ramy_Oranz",    (0.400, 0.150, 0.055), 0.45),
    "band":      M("CUZK_Rimsy_Sede",    (0.300, 0.305, 0.295), 0.65),
    "concrete":  M("CUZK_Beton",         (0.600, 0.600, 0.580), 0.75),
    "roof":      M("CUZK_Streska",       (0.150, 0.150, 0.145), 0.85),
    "steel":     M("CUZK_Ocel",          (0.110, 0.120, 0.130), 0.45, 0.6),
    "asphalt":   M("CUZK_Asfalt",        (0.045, 0.045, 0.048), 0.9),
    "pave":      M("CUZK_Dlazba",        (0.330, 0.320, 0.300), 0.85),
    "green":     M("CUZK_Koruna",        (0.035, 0.095, 0.030), 0.85),
    "trunk":     M("CUZK_Kmen",          (0.060, 0.040, 0.025), 0.9),
    "red":       M("CUZK_Cervena",       (0.420, 0.030, 0.025), 0.5),
    "white2":    M("CUZK_Bila",          (0.800, 0.800, 0.790), 0.5),
    "sign":      M("CUZK_Poutac",        (0.090, 0.100, 0.105), 0.6),
    "canopy":    M("CUZK_StresniSklo",   (0.300, 0.430, 0.460), 0.10, 0.35),
}

# ---------------------------------------------------------------- helpery
class B:
    def __init__(self):
        self.g = {}
    def bm(self, k):
        if k not in self.g:
            self.g[k] = bmesh.new()
        return self.g[k]
    def finish(self):
        for k, bm in self.g.items():
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            me = bpy.data.meshes.new("CUZK_" + k)
            bm.to_mesh(me)
            bm.free()
            ob = bpy.data.objects.new("CUZK_" + k, me)
            ob.data.materials.append(MATS[k])
            coll.objects.link(ob)
        self.g = {}

b = B()

def box(bm, cx, cy, cz, sx, sy, sz, ang=0.0):
    hx, hy, hz = sx * 0.5, sy * 0.5, sz * 0.5
    ca, sa = math.cos(ang), math.sin(ang)
    pts = []
    for dz in (-hz, hz):
        for dx, dy in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)):
            pts.append(bm.verts.new((dx * ca - dy * sa + cx,
                                     dx * sa + dy * ca + cy,
                                     dz + cz)))
    for f in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
              (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        bm.faces.new([pts[i] for i in f])

def seg(bm, p0, p1, z0, z1, thick, inset=0.0, grow=None):
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    if L < 1e-6:
        return
    ang = math.atan2(dy, dx)
    nx, ny = dy / L, -dx / L          # vnejsi normala
    g = thick if grow is None else grow
    cx = (p0[0] + p1[0]) * 0.5 - nx * (inset + thick * 0.5)
    cy = (p0[1] + p1[1]) * 0.5 - ny * (inset + thick * 0.5)
    box(bm, cx, cy, (z0 + z1) * 0.5, L + g, thick, z1 - z0, ang)

def strip(bm, pts, z0, z1, thick, inset=0.0, grow=None):
    for a, c in zip(pts, pts[1:]):
        seg(bm, a, c, z0, z1, thick, inset, grow)

def arc(cx, cy, r, a0, a1, n):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
            for i in range(n + 1)]

def sample(pts, spacing, start=0.0):
    segs, total = [], 0.0
    for a, c in zip(pts, pts[1:]):
        L = math.hypot(c[0] - a[0], c[1] - a[1])
        if L > 1e-6:
            segs.append((a, c, L, total))
            total += L
    out, s = [], start
    while s <= total:
        for a, c, L, c0 in segs:
            if c0 <= s <= c0 + L:
                t = (s - c0) / L
                out.append((a[0] + (c[0] - a[0]) * t,
                            a[1] + (c[1] - a[1]) * t,
                            math.atan2(c[1] - a[1], c[0] - a[0])))
                break
        s += spacing
    return out

def prism(bm, poly, z0, z1):
    bot = [bm.verts.new((p[0], p[1], z0)) for p in poly]
    top = [bm.verts.new((p[0], p[1], z1)) for p in poly]
    bm.faces.new(list(reversed(bot)))
    bm.faces.new(top)
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([bot[i], bot[j], top[j], top[i]])

def beam3d(bm, p0, p1, w, h):
    """obdelnikovy nosnik mezi dvema 3D body"""
    a, c = Vector(p0), Vector(p1)
    d = (c - a)
    L = d.length
    if L < 1e-6:
        return
    d.normalize()
    up = Vector((0, 0, 1))
    if abs(d.dot(up)) > 0.98:
        up = Vector((0, 1, 0))
    side = d.cross(up).normalized()
    up2 = side.cross(d).normalized()
    verts = []
    for e in (-1, 1):
        for f in (-1, 1):
            for g in (-1, 1):
                verts.append(bm.verts.new(a + d * (L * 0.5) + d * (L * 0.5 * e)
                                          + side * (w * 0.5 * f) + up2 * (h * 0.5 * g)))
    for f in ((0, 1, 3, 2), (6, 7, 5, 4), (0, 2, 6, 4),
              (1, 5, 7, 3), (0, 4, 5, 1), (2, 3, 7, 6)):
        bm.faces.new([verts[i] for i in f])

def cyl(bm, x, y, z0, z1, r, n=16):
    mtx = Matrix.Translation((x, y, (z0 + z1) * 0.5))
    try:
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=n,
                              radius1=r, radius2=r, depth=(z1 - z0), matrix=mtx)
    except TypeError:
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=n,
                              diameter1=r * 2, diameter2=r * 2, depth=(z1 - z0),
                              matrix=mtx)

def ball(bm, x, y, z, r, sub=2):
    mtx = Matrix.Translation((x, y, z))
    try:
        bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r, matrix=mtx)
    except TypeError:
        bmesh.ops.create_icosphere(bm, subdivisions=sub, diameter=r * 2, matrix=mtx)

# ---------------------------------------------------------------- pudorys
FRONT = [(-44.0, -10.0), (33.0, -10.0)] + arc(X_ARC, 0, ARC_R, -90, 90, 48)[1:]
PLAN = [(-44.0, -10.0)] + arc(X_ARC, 0, ARC_R, -90, 90, 48) + [(-44.0, 10.0)]
PLAN = [p for i, p in enumerate(PLAN) if i == 0 or p != PLAN[i - 1]]

# ---------------------------------------------------------------- sokl, strecha
prism(b.bm("concrete"), PLAN, -0.35, 0.16)
prism(b.bm("roof"), PLAN, Z_TOP, Z_TOP + 0.35)

# ---------------------------------------------------------------- prizemi
GF_INSET = 1.35
gf_runs_front = [[(-44.0, -10.0), (ENT_X0, -10.0)],
                 [(ENT_X1, -10.0), (16.0, -10.0)]]
gf_runs_other = [[(16.0, 10.0), (-44.0, 10.0)],
                 [(-44.0, 10.0), (-44.0, -10.0)]]
for run in gf_runs_front + gf_runs_other:
    strip(b.bm("glassdark"), run, 0.16, 4.55, 0.07, inset=GF_INSET)
    strip(b.bm("band"), run, 4.35, 4.58, 1.45, inset=0.70)   # podhled arkady
    # oranzove sloupky proskleni
    for (x, y, a) in sample(run, 2.15, 1.0):
        nx, ny = math.sin(a), -math.cos(a)
        px, py = x - nx * (GF_INSET + 0.05), y - ny * (GF_INSET + 0.05)
        box(b.bm("orange"), px, py, 2.35, 0.10, 0.16, 4.35, a)

# sloupy arkady
for (x, y, a) in sample(FRONT, 5.6, 1.2):
    if ENT_X0 - 0.6 < x < ENT_X1 + 0.6:
        continue
    nx, ny = math.sin(a), -math.cos(a)
    box(b.bm("concrete"), x - nx * 0.28, y - ny * 0.28, Z_GF * 0.5,
        0.56, 0.56, Z_GF, a)

# ---------------------------------------------------------------- hlavni hmota
def floor_bands(panel_runs, glass_runs, z0, mat_panel, panel_top, glass_top):
    for run in panel_runs:
        strip(b.bm(mat_panel), run, z0 + 0.18, z0 + panel_top, 0.30, inset=0.02)
    for run in glass_runs:
        strip(b.bm("glass"), run, z0 + panel_top, z0 + glass_top, 0.07, inset=0.18)
        strip(b.bm("orange"), run, z0 + panel_top - 0.07, z0 + panel_top + 0.07,
              0.24, inset=0.04)
        strip(b.bm("orange"), run, z0 + glass_top - 0.07, z0 + glass_top + 0.05,
              0.24, inset=0.04)
        for (x, y, a) in sample(run, 2.15, 1.0):
            nx, ny = math.sin(a), -math.cos(a)
            px, py = x - nx * 0.10, y - ny * 0.10
            box(b.bm("orange"), px, py,
                (z0 + panel_top + z0 + glass_top) * 0.5,
                0.11, 0.22, glass_top - panel_top, a)
    # jemne spary panelu
    for run in panel_runs:
        for (x, y, a) in sample(run, 2.15, 1.0):
            nx, ny = math.sin(a), -math.cos(a)
            px, py = x - nx * 0.015, y - ny * 0.015
            box(b.bm("band"), px, py, z0 + 0.18 + (panel_top - 0.18) * 0.5,
                0.035, 0.02, panel_top - 0.18, a)

FRONT_FULL = [(-44.0, -10.0), (16.0, -10.0)]
FRONT_SPLIT = [[(-44.0, -10.0), (ENT_X0, -10.0)],
               [(ENT_X1, -10.0), (16.0, -10.0)]]
REAR = [[(16.0, 10.0), (-44.0, 10.0)]]
WEST = [[(-44.0, 10.0), (-44.0, -10.0)]]

for i in range(N_UP):
    z0 = Z_GF + i * FLOOR_H
    panel_runs = (FRONT_SPLIT if i == 0 else [FRONT_FULL]) + REAR + WEST
    glass_runs = [FRONT_FULL] + REAR + WEST
    floor_bands(panel_runs, glass_runs, z0, "mint", 1.42, 3.10)
    # hruba rimsova deska
    for run in glass_runs:
        strip(b.bm("band"), run, z0 + 3.10, z0 + 3.40, 0.34, inset=-0.16, grow=0.34)

# ---------------------------------------------------------------- zaoblene kridlo
WING_FRONT = [(16.0, -10.0), (33.0, -10.0)] + arc(X_ARC, 0, ARC_R, -90, 90, 48)[1:]
wing_runs = [WING_FRONT, [(33.0, 10.0), (16.0, 10.0)]]
for i in range(N_UP):
    z0 = Z_GF + i * FLOOR_H
    for run in wing_runs:
        strip(b.bm("white"), run, z0, z0 + 1.52, 0.30, inset=0.02)
        strip(b.bm("glass"), run, z0 + 1.52, z0 + 3.16, 0.07, inset=0.16)
        strip(b.bm("orange"), run, z0 + 1.45, z0 + 1.59, 0.22, inset=0.03)
        strip(b.bm("orange"), run, z0 + 3.09, z0 + 3.20, 0.22, inset=0.03)
        strip(b.bm("band"), run, z0 + 3.16, z0 + 3.19, 0.06, inset=0.10)
        strip(b.bm("white"), run, z0 + 3.19, z0 + 3.40, 0.28, inset=0.02)
        for (x, y, a) in sample(run, 2.40, 1.0):
            nx, ny = math.sin(a), -math.cos(a)
            px, py = x - nx * 0.09, y - ny * 0.09
            box(b.bm("orange"), px, py, z0 + 2.34, 0.10, 0.20, 1.64, a)

# spara mezi hmotami
for yy in (-9.86, 9.86):
    box(b.bm("band"), X_J, yy, (Z_GF + Z_TOP) * 0.5, 0.55, 0.30, Z_TOP - Z_GF)

# ---------------------------------------------------------------- atika
for run in [FRONT, [(33.0, 10.0), (-44.0, 10.0)], [(-44.0, 10.0), (-44.0, -10.0)]]:
    strip(b.bm("white"), run, Z_TOP + 0.30, Z_TOP + 1.10, 0.30, inset=0.10)
strip(b.bm("band"), FRONT, Z_TOP + 0.30, Z_TOP + 0.45, 0.34, inset=-0.02)

# ---------------------------------------------------------------- vstup
strip(b.bm("glassdark"), [(ENT_X0, -10.0), (ENT_X1, -10.0)], 0.16, ENT_TOP,
      0.08, inset=1.30)
strip(b.bm("band"), [(ENT_X0, -10.0), (ENT_X1, -10.0)], ENT_TOP - 0.12, ENT_TOP,
      0.30, inset=1.20)
for (x, y, a) in sample([(ENT_X0, -10.0), (ENT_X1, -10.0)], 2.05, 0.6):
    nx, ny = math.sin(a), -math.cos(a)
    box(b.bm("orange"), x - nx * 1.24, y - ny * 1.24, 3.1, 0.12, 0.18, 5.9, a)
box(b.bm("orange"), -8.0, -8.72, 4.55, 12.2, 0.18, 0.14, 0.0)

# pruh se jmenem uradu
box(b.bm("sign"), -8.0, -9.00, 4.72, 12.4, 0.55, 0.62, 0.0)
box(b.bm("band"), -8.0, -9.30, 4.40, 12.8, 0.10, 0.06, 0.0)
# pristresek nad dvermi
box(b.bm("sign"), -8.0, -9.95, 3.55, 8.6, 2.5, 0.16, 0.0)
box(b.bm("steel"), -12.2, -10.6, 3.42, 0.10, 1.6, 0.10, 0.0)
box(b.bm("steel"), -3.8, -10.6, 3.42, 0.10, 1.6, 0.10, 0.0)

# text
txt = bpy.data.curves.new("CUZK_Text", type='FONT')
txt.body = "ZEMĚMĚŘICKÝ A KATASTRÁLNÍ ÚŘAD"
txt.size = 0.40
txt.extrude = 0.012
txt.align_x = 'CENTER'
txt.align_y = 'CENTER'
fp = "C:/Windows/Fonts/arialbd.ttf"
if os.path.exists(fp):
    try:
        txt.font = bpy.data.fonts.load(fp)
    except Exception:
        pass
tob = bpy.data.objects.new("CUZK_Text", txt)
tob.location = (-8.0, -9.29, 4.72)
tob.rotation_euler = (math.radians(90), 0, 0)
tob.data.materials.append(MATS["white2"])
coll.objects.link(tob)

# ---------------------------------------------------------------- strecha
# ustoupene prosklene podlazi
PX0, PX1, PY0, PY1 = -36.0, 8.0, -7.4, 6.4
PZ0, PZ1 = Z_TOP + 0.35, Z_TOP + 2.85
box(b.bm("glass"), (PX0 + PX1) / 2, PY0, (PZ0 + PZ1) / 2, PX1 - PX0, 0.08, PZ1 - PZ0)
box(b.bm("glass"), (PX0 + PX1) / 2, PY1, (PZ0 + PZ1) / 2, PX1 - PX0, 0.08, PZ1 - PZ0)
box(b.bm("glass"), PX0, (PY0 + PY1) / 2, (PZ0 + PZ1) / 2, 0.08, PY1 - PY0, PZ1 - PZ0)
box(b.bm("glass"), PX1, (PY0 + PY1) / 2, (PZ0 + PZ1) / 2, 0.08, PY1 - PY0, PZ1 - PZ0)
for xx in [PX0 + i * 2.6 for i in range(int((PX1 - PX0) / 2.6) + 1)]:
    box(b.bm("steel"), xx, PY0 - 0.02, (PZ0 + PZ1) / 2, 0.10, 0.16, PZ1 - PZ0)
box(b.bm("steel"), (PX0 + PX1) / 2, (PY0 + PY1) / 2, PZ1, PX1 - PX0, PY1 - PY0, 0.16)

# sikma sklenena strieska nad ustupenym podlazim
CX0, CX1 = -37.0, 9.0
CY0, CY1 = -9.3, -1.4
CZ0, CZ1 = 25.55, 24.35
verts = []
for xx in (CX0, CX1):
    for yy, zz in ((CY0, CZ0), (CY1, CZ1)):
        verts.append((xx, yy, zz))
bmc = b.bm("canopy")
v = [bmc.verts.new(p) for p in verts]
bmc.faces.new([v[0], v[1], v[3], v[2]])
# tloustka
v2 = [bmc.verts.new((p[0], p[1], p[2] - 0.06)) for p in verts]
bmc.faces.new([v2[2], v2[3], v2[1], v2[0]])
bmc.faces.new([v[0], v2[0], v2[1], v[1]])
bmc.faces.new([v[1], v2[1], v2[3], v[3]])
bmc.faces.new([v[3], v2[3], v2[2], v[2]])
bmc.faces.new([v[2], v2[2], v2[0], v[0]])

for xx in [CX0 + i * 3.0 for i in range(int((CX1 - CX0) / 3.0) + 1)]:
    beam3d(b.bm("steel"), (xx, CY0, CZ0 - 0.18), (xx, CY1, CZ1 - 0.18), 0.14, 0.22)
beam3d(b.bm("steel"), (CX0, CY0, CZ0 - 0.18), (CX1, CY0, CZ0 - 0.18), 0.18, 0.26)
beam3d(b.bm("steel"), (CX0, CY1, CZ1 - 0.18), (CX1, CY1, CZ1 - 0.18), 0.18, 0.26)
for xx in (CX0, CX1):
    beam3d(b.bm("steel"), (xx, CY0, CZ0 - 0.18), (xx, CY1, CZ1 - 0.18), 0.18, 0.26)

# podpory pristresku
for xx in [CX0 + 1.5 + i * 6.0 for i in range(int((CX1 - CX0 - 3) / 6.0) + 1)]:
    beam3d(b.bm("steel"), (xx, CY0 + 0.1, Z_TOP + 1.10), (xx, CY0 + 0.1, CZ0 - 0.10), 0.12, 0.12)
beam3d(b.bm("steel"), (CX0, CY0 + 0.1, Z_TOP + 1.10), (CX1, CY0 + 0.1, Z_TOP + 1.10), 0.14, 0.20)

# stožar a technika
cyl(b.bm("white2"), -4.0, 1.5, Z_TOP + 0.35, Z_TOP + 10.0, 0.09, 12)
for zz in (Z_TOP + 7.4, Z_TOP + 8.2, Z_TOP + 9.0):
    box(b.bm("white2"), -4.0, 1.5, zz, 0.10, 2.2, 0.10, 0.0)
for (x, y, sx, sy, sz) in [(26, 3, 3.0, 2.2, 1.3), (33, -2, 2.4, 2.0, 1.1),
                           (-20, 4, 2.6, 2.0, 1.0), (2, 3.5, 2.0, 1.8, 0.9)]:
    box(b.bm("concrete"), x, y, Z_TOP + 0.35 + sz / 2, sx, sy, sz)

# ---------------------------------------------------------------- zapadni balkony
for i in range(N_UP):
    z0 = Z_GF + i * FLOOR_H
    box(b.bm("concrete"), -45.05, -6.1, z0 + 0.14, 2.1, 3.9, 0.22)
    box(b.bm("glass"), -46.05, -6.1, z0 + 0.72, 0.06, 3.9, 0.95)
    box(b.bm("steel"), -46.08, -6.1, z0 + 1.22, 0.10, 4.0, 0.08)
    for yy in (-8.0, -6.1, -4.2):
        box(b.bm("steel"), -46.05, yy, z0 + 0.65, 0.08, 0.08, 1.05)

# ---------------------------------------------------------------- okoli
# teren, chodnik, silnice
box(b.bm("pave"), 0, -10, -0.06, 420, 300, 0.12)
box(b.bm("pave"), -10, -20.0, 0.02, 300, 20.0, 0.14)
box(b.bm("asphalt"), -10, -39.0, 0.0, 300, 38.0, 0.10)
box(b.bm("concrete"), -10, -29.4, 0.10, 300, 0.5, 0.22)
for i in range(-14, 15):
    box(b.bm("white2"), i * 8.0, -38.5, 0.06, 3.6, 0.16, 0.02)

# stromy
for x in (-34.0, -22.0, 6.0, 20.0, 34.0):
    cyl(b.bm("trunk"), x, -12.6, 0.0, 4.2, 0.22, 10)
    ball(b.bm("green"), x, -12.6, 5.0, 1.75, 2)
    ball(b.bm("green"), x - 0.9, -12.9, 5.9, 1.35, 2)
    ball(b.bm("green"), x + 1.0, -12.3, 5.7, 1.25, 2)

# lampy
for x in (-38.0, -8.0, 22.0, 48.0):
    cyl(b.bm("steel"), x, -26.6, 0.1, 9.2, 0.09, 10)
    beam3d(b.bm("steel"), (x, -26.6, 9.2), (x, -23.2, 9.35), 0.08, 0.08)
    box(b.bm("white2"), x, -23.1, 9.28, 0.55, 0.22, 0.12)

# cervenobile zabradli
for i, x in enumerate([-52.0 + j * 2.0 for j in range(56)]):
    key = "red" if i % 2 == 0 else "white2"
    box(b.bm(key), x, -29.9, 0.62, 0.06, 0.06, 1.05)
for i, x in enumerate([-52.0 + j * 2.0 for j in range(55)]):
    key = "red" if i % 2 == 0 else "white2"
    box(b.bm(key), x + 1.0, -29.9, 1.05, 2.0, 0.05, 0.06)
    box(b.bm(key), x + 1.0, -29.9, 0.62, 2.0, 0.05, 0.05)

# pristresek zastavky
box(b.bm("steel"), 26.0, -24.4, 2.55, 7.0, 2.0, 0.12)
box(b.bm("glass"), 26.0, -25.35, 1.45, 7.0, 0.05, 2.1)
box(b.bm("steel"), 22.6, -24.4, 1.3, 0.08, 2.0, 2.4)
box(b.bm("steel"), 29.4, -24.4, 1.3, 0.08, 2.0, 2.4)
box(b.bm("concrete"), 26.0, -24.4, 0.42, 6.2, 0.45, 0.08)

# ---------------------------------------------------------------- finalizace
b.finish()
for ob in coll.objects:
    if ob.type == 'MESH' and ob.name.endswith("green"):
        for p in ob.data.polygons:
            p.use_smooth = True

# ---------------------------------------------------------------- scena
SCENE.unit_settings.system = 'METRIC'
SCENE.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in \
    [i.identifier for i in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
SCENE.render.resolution_x = 1600
SCENE.render.resolution_y = 900
SCENE.render.resolution_percentage = 100
SCENE.render.image_settings.file_format = 'PNG'
SCENE.render.film_transparent = False
try:
    SCENE.eevee.taa_render_samples = 64
    SCENE.eevee.use_raytracing = True
except Exception:
    pass
try:
    SCENE.view_settings.view_transform = 'AgX'
    SCENE.view_settings.look = 'AgX - Medium High Contrast'
except Exception:
    pass

# svet
world = bpy.data.worlds.get("CUZK_Sky")
if world is None:
    world = bpy.data.worlds.new("CUZK_Sky")
SCENE.world = world
world.use_nodes = True
nt = world.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputWorld")
bg = nt.nodes.new("ShaderNodeBackground")
sky = nt.nodes.new("ShaderNodeTexSky")
sky.sky_type = 'NISHITA'
sky.sun_elevation = math.radians(24)
sky.sun_rotation = math.radians(215)
sky.sun_disc = False
bg.inputs['Strength'].default_value = 0.55
nt.links.new(sky.outputs['Color'], bg.inputs['Color'])
nt.links.new(bg.outputs['Background'], out.inputs['Surface'])

def add_sun(name, direction, energy, angle=0.03):
    d = bpy.data.lights.new(name, 'SUN')
    d.energy = energy
    d.angle = angle
    o = bpy.data.objects.new(name, d)
    o.rotation_euler = Vector(direction).normalized().to_track_quat('-Z', 'Y').to_euler()
    coll.objects.link(o)
    return o

add_sun("CUZK_Sun", (-0.52, 0.72, -0.58), 4.2, 0.02)
add_sun("CUZK_Fill", (0.55, 0.55, -0.45), 1.0, 0.6)

def add_cam(name, loc, target, lens):
    c = bpy.data.cameras.new(name)
    c.lens = lens
    o = bpy.data.objects.new(name, c)
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    coll.objects.link(o)
    return o

cam_hero = add_cam("CUZK_Cam_Hero", (74.0, -96.0, 30.0), (-3.0, 0.0, 9.0), 50)
cam_front = add_cam("CUZK_Cam_Front", (-34.0, -78.0, 12.0), (-6.0, -6.0, 10.0), 45)
cam_detail = add_cam("CUZK_Cam_Entrance", (-24.0, -38.0, 9.0), (-8.0, -9.0, 5.0), 50)
SCENE.camera = cam_hero

# ---------------------------------------------------------------- render
def render(cam, path):
    SCENE.camera = cam
    SCENE.render.filepath = path
    bpy.ops.render.render(write_still=True)

render(cam_hero, os.path.join(RENDER_DIR, "cuzk_hero.png"))
render(cam_front, os.path.join(RENDER_DIR, "cuzk_front.png"))
render(cam_detail, os.path.join(RENDER_DIR, "cuzk_entrance.png"))
SCENE.camera = cam_hero

print("HOTOVO: budova postavena, objekty:", len(coll.objects))
