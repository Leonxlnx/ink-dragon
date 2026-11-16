"""Physical set for the ink-dragon film: glass, water, table, lantern backdrop, drop, ink volume, camera.

bpy module, importable with no side effects.  Usage (inside Blender):

    import scene_lib as S
    S.build()                                   # once per session, in an empty scene
    S.configure_render('final', threads=14)
    S.apply_state(t)                            # water surface + drops for sim time t (stateless)
    S.set_ink(vdb_path, density_scale=2600)     # or S.set_ink(None)
    S.set_camera((0, -0.78, 0.105), (0, 0, 0.075), lens_mm=85, fstop=4)
    S.render_still(path)

Optional per-shot controls:  set_backdrop(azimuth_deg, strength, height), set_pad(strength, radius,
soft), set_exposure(ev).  By default set_camera() drives both automatically (BACKDROP_FOLLOW,
PAD_AUTO): the lantern hot spot always sits behind the subject, the table pad adapts to the camera
elevation.
World: metres, Z up, glass axis = Z, table top z = 0, 'front' camera sits at -Y looking +Y.
"""
import math
import os
import sys

import bpy
import bmesh
import numpy as np
from mathutils import Vector, Quaternion

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import common as C                      # noqa: E402
import surface_model as SM              # noqa: E402

# ------------------------------------------------------------------ tunables
SEG = 384                    # segments around the glass axis (glass + water share them)
IOR_GLASS = 1.50
IOR_WATER = 1.333
INK_DENSITY_SCALE = 2600.0
INK_TINT = (0.0, 0.07, 0.20)         # absorption 'colour': blue is absorbed least -> cool thin veils

BACKDROP_FOLLOW = True       # set_camera() keeps the lantern hot spot behind the subject (see set_backdrop)
BACKDROP_STRENGTH = 1.0      # scene-linear radiance of the lantern hot spot
IVORY = (1.00, 0.74, 0.45)
AMBER = (1.00, 0.40, 0.10)
COOL = (0.50, 0.72, 1.00)
PANEL_R = 0.32               # the paper lantern is a curved screen this far behind the glass axis
PANEL_H = 1.0                # ... this tall, spanning +-PANEL_SPAN_DEG of azimuth
PANEL_SPAN_DEG = 82.0
LOBE_AZ_DEG = 34.0           # gaussian half-width of the hot spot in azimuth (seen from the glass axis)
LOBE_H_UP = 0.12             # gaussian half-heights of the hot spot (metres on the screen)
LOBE_H_DOWN = 0.14
LOBE_TAIL = 0.10             # weak wide glow around the hot spot
STRIP_AZ_DEG = 40.0          # cool edge-light strips: azimuth either side of the hot spot ...
STRIP_DIST = 0.30            # ... at this distance from the glass axis (reflection-only objects)
STRIP_WIDTH = 0.045
STRIP_Z = (0.0, 0.45)
STRIP_POWER = 0.18           # watts per strip
DROP_KEY_POWER = 2.0         # soft cool key light that only the ink drops see (gives them a sheen)           # watts per strip
TABLE_R = 2.5
DENOISE_PASSES = 'RGB'       # do not change between renders of one Blender session (OIDN crash)
TABLE_REFL_MAX = 0.30        # cap on the table's grazing reflectance (art-directed, not physical)
TABLE_ROUGH = 0.11
PAD_AUTO = True              # set_camera() grows the pad with camera elevation (see set_pad)
PAD_STRENGTH = 0.45           # glowing disc under the glass
PAD_RADIUS = 0.07
PAD_SOFT = 0.09

_state = {}                  # handles to the objects / cached arrays created by build()


# ================================================================== helpers
def _sstep(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3.0 - 2.0 * u)


def _scene():
    return bpy.context.scene


def _link(ob):
    _scene().collection.objects.link(ob)
    return ob


def _lathe(name, prof, seg, mats):
    """prof: list of (r, z, material_index); a face takes the index of its *second* ring."""
    verts, faces, fmat, rings = [], [], [], []
    ca = [math.cos(2 * math.pi * i / seg) for i in range(seg)]
    sa = [math.sin(2 * math.pi * i / seg) for i in range(seg)]
    for (r, z, _m) in prof:
        if r <= 1e-9:
            rings.append([len(verts)])
            verts.append((0.0, 0.0, z))
        else:
            rings.append(list(range(len(verts), len(verts) + seg)))
            verts.extend((r * ca[i], r * sa[i], z) for i in range(seg))
    for k in range(len(prof) - 1):
        a, b = rings[k], rings[k + 1]
        m = prof[k + 1][2]
        if len(a) == 1 and len(b) == 1:
            continue
        for i in range(seg):
            j = (i + 1) % seg
            if len(a) == 1:
                faces.append((a[0], b[j], b[i]))
            elif len(b) == 1:
                faces.append((a[i], a[j], b[0]))
            else:
                faces.append((a[i], a[j], b[j], b[i]))
            fmat.append(m)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.polygons.foreach_set("material_index", fmat)
    me.polygons.foreach_set("use_smooth", [True] * len(faces))
    for m in mats:
        me.materials.append(m)
    me.update()
    return _link(bpy.data.objects.new(name, me))


def _new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.node_tree.nodes.clear()
    return m, m.node_tree


def _glass_mat(name, ior, color=(1, 1, 1, 1), shadow_color=(0.90, 0.93, 0.95, 1)):
    """sharp dielectric interface; shadow rays pass (tinted) so the glass never casts black blobs"""
    m, nt = _new_mat(name)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    g = nt.nodes.new("ShaderNodeBsdfGlass")
    g.inputs["IOR"].default_value = ior
    g.inputs["Color"].default_value = color
    g.inputs["Roughness"].default_value = 0.0
    lp = nt.nodes.new("ShaderNodeLightPath")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = shadow_color
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Shadow Ray"], mix.inputs[0])
    nt.links.new(g.outputs[0], mix.inputs[1])
    nt.links.new(tr.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m


# ================================================================== glass
def _glass_profile():
    H, w = C.GLASS_H, C.GLASS_WALL
    z0 = 0.00008                    # foot ring just above the table (no coplanar faces)
    punt = 0.0011                   # concave underside
    rf = 0.0032                     # outer bottom fillet
    ri = 0.0030                     # inner bottom fillet
    zc = SM.Z_CONTACT
    P = []
    cx = C.r_out(z0 + rf) - rf      # fillet centre radius == radius of the foot ring
    n = 14
    for i in range(n + 1):          # concave underside, centre -> foot
        r = cx * i / n
        P.append((r, z0 + punt * (1 - (r / cx) ** 2) ** 2, 0))
    for i in range(1, 13):          # bottom fillet
        a = math.pi / 2 * i / 12
        P.append((cx + rf * math.sin(a), z0 + rf - rf * math.cos(a), 0))
    z_lo, z_hi = z0 + rf, H - w / 2
    for i in range(1, 17):          # outer wall
        z = z_lo + (z_hi - z_lo) * i / 16
        P.append((C.r_out(z), z, 0))
    rc = C.r_out(z_hi) - w / 2
    for i in range(1, 16):          # rim (semi-circle)
        a = math.pi * i / 16
        P.append((rc + (w / 2) * math.cos(a), z_hi + (w / 2) * math.sin(a), 0))
    P.append((C.r_in(z_hi), z_hi, 0))
    for i in range(1, 7):           # inner wall above the contact line (glass / air)
        z = z_hi + (zc - z_hi) * i / 6
        P.append((C.r_in(z), z, 0))
    z_b = C.GLASS_BASE + ri
    for i in range(1, 17):          # wetted inner wall (glass / water)
        z = zc + (z_b - zc) * i / 16
        P.append((C.r_in(z), z, 1))
    rcb = C.r_in(z_b) - ri
    for i in range(1, 13):          # inner bottom fillet
        a = math.pi / 2 * i / 12
        P.append((rcb + ri * math.cos(a), z_b - ri * math.sin(a), 1))
    for i in range(1, 7):           # inner floor
        P.append((rcb * (1 - i / 6), C.GLASS_BASE, 1))
    return P


def _build_glass():
    m_ga = _glass_mat("GlassAir", IOR_GLASS)
    m_gw = _glass_mat("GlassWater", IOR_GLASS / IOR_WATER)
    ob = _lathe("Glass", _glass_profile(), SEG, [m_ga, m_gw])
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)      # closed surface -> normals leave the glass
    bm.to_mesh(ob.data)
    bm.free()
    return ob


# ================================================================== water surface
def _water_rings():
    """nominal ring radii (distance from the impact point for the inner rings), 0 .. R_CONTACT"""
    R = SM.R_CONTACT
    r, rings = 0.0, []
    while True:
        if r < 0.0016:
            d = 0.00005
        elif r < 0.006:
            d = 0.00005 + (r - 0.0016) / 0.0044 * 0.00013
        elif r < R - 0.008:
            d = min(0.00018 + (r - 0.006) * 0.03, 0.00034)
        else:
            d = max(0.00006, 0.00034 * ((R - r) / 0.008) ** 1.2)
        r += d
        if r >= R - 0.00003:
            break
        rings.append(r)
    rings.append(R)
    return np.array(rings)


def _build_water():
    rr = _water_rings()
    R = SM.R_CONTACT
    ang = 2 * np.pi * np.arange(SEG) / SEG
    w = 1.0 - (rr / R) ** 2                     # ring centres slide from the impact point to the axis
    cx = SM.DROP_XY[0] * w
    cy = SM.DROP_XY[1] * w
    X = cx[:, None] + rr[:, None] * np.cos(ang)[None, :]
    Y = cy[:, None] + rr[:, None] * np.sin(ang)[None, :]
    nr = len(rr)
    xs = np.concatenate([[SM.DROP_XY[0]], X.ravel()])
    ys = np.concatenate([[SM.DROP_XY[1]], Y.ravel()])
    faces = []
    for i in range(SEG):
        faces.append((0, 1 + i, 1 + (i + 1) % SEG))
    for k in range(nr - 1):
        a, b = 1 + k * SEG, 1 + (k + 1) * SEG
        for i in range(SEG):
            j = (i + 1) % SEG
            faces.append((a + i, b + i, b + j, a + j))
    sampler = SM.SurfaceSampler(xs, ys)
    co = np.empty((xs.size, 3), dtype=np.float32)
    co[:, 0], co[:, 1], co[:, 2] = xs, ys, sampler.height(-1.0)
    me = bpy.data.meshes.new("WaterTop")
    me.from_pydata(co.tolist(), [], faces)
    me.polygons.foreach_set("use_smooth", [True] * len(faces))
    me.materials.append(_glass_mat("WaterAir", IOR_WATER))
    me.update()
    ob = _link(bpy.data.objects.new("WaterTop", me))
    _state["water_sampler"] = sampler
    _state["water_co"] = co
    return ob


# ================================================================== backdrop (curved paper lantern)
def _backdrop_pixels(w=1024, h=1024):
    """float RGBA image: u = azimuth -SPAN..+SPAN (0 = behind the glass), v = height offset from the
    hot spot centre, -PANEL_H/2 .. +PANEL_H/2"""
    d2r = math.radians
    phi = ((np.arange(w) + 0.5) / w * 2 - 1) * d2r(PANEL_SPAN_DEG)
    dz = ((np.arange(h) + 0.5) / h - 0.5) * PANEL_H
    PH, DZ = np.meshgrid(phi, dz)
    az = np.exp(-(PH / d2r(LOBE_AZ_DEG)) ** 2)
    v = np.where(DZ > 0, np.exp(-(DZ / LOBE_H_UP) ** 2), np.exp(-(DZ / LOBE_H_DOWN) ** 2))
    tail = np.exp(-(PH / d2r(62.0)) ** 2) * np.exp(-(DZ / 0.30) ** 2)
    inten = (1 - LOBE_TAIL) * az * v + LOBE_TAIL * tail
    # fade to exactly zero at the screen edges so the screen itself is never visible
    e = np.clip((d2r(PANEL_SPAN_DEG) - np.abs(PH)) / d2r(18.0), 0, 1)
    e2 = np.clip((0.5 * PANEL_H - np.abs(DZ)) / 0.12, 0, 1)
    inten *= (e * e * (3 - 2 * e)) * (e2 * e2 * (3 - 2 * e2))
    ivory = np.array(IVORY)
    amber = np.array(AMBER)
    k = np.clip((inten - 0.04) / 0.80, 0, 1)
    k = k * k * (3 - 2 * k)
    col = amber[None, None, :] * (1 - k[..., None]) + ivory[None, None, :] * k[..., None]
    px = np.ones((h, w, 4), dtype=np.float32)
    px[..., :3] = col * inten[..., None]
    return px


def _build_backdrop():
    rig = _link(bpy.data.objects.new("LightRig", None))
    _state["rig"] = rig
    w = h = 1024
    img = bpy.data.images.new("LanternTex", w, h, alpha=False, float_buffer=True)
    img.colorspace_settings.name = "Linear Rec.709"
    img.pixels.foreach_set(_backdrop_pixels(w, h).ravel())
    img.pack()
    seg = 96
    span = math.radians(PANEL_SPAN_DEG)
    verts, faces = [], []
    for i in range(seg + 1):
        phi = -span + 2 * span * i / seg                 # azimuth measured from +Y towards +X
        x, y = PANEL_R * math.sin(phi), PANEL_R * math.cos(phi)
        verts.append((x, y, 0.0))
        verts.append((x, y, PANEL_H))
    for i in range(seg):
        a = 2 * i
        faces.append((a, a + 2, a + 3, a + 1))
    me = bpy.data.meshes.new("Backdrop")
    me.from_pydata(verts, [], faces)
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            uvl.data[li].uv = ((vi // 2) / seg, float(vi % 2))
    m, nt = _new_mat("Lantern")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.name = "BackdropEmission"
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = 'Cubic'
    tex.extension = 'EXTEND'
    uvn = nt.nodes.new("ShaderNodeUVMap")
    uvn.uv_map = "UVMap"
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.name = "BackdropMapping"
    nt.links.new(uvn.outputs[0], mp.inputs[0])
    nt.links.new(mp.outputs[0], tex.inputs[0])
    # rice-paper fibre: faint, fixed to the screen (does not move with the hot spot)
    geo = nt.nodes.new("ShaderNodeTexCoord")
    mp2 = nt.nodes.new("ShaderNodeMapping")
    mp2.inputs["Scale"].default_value = (12.0, 12.0, 70.0)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.0
    noise.inputs["Detail"].default_value = 1.5
    noise.inputs["Roughness"].default_value = 0.5
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.25
    mr.inputs["From Max"].default_value = 0.75
    mr.inputs["To Min"].default_value = 0.96
    mr.inputs["To Max"].default_value = 1.035
    nt.links.new(geo.outputs["Object"], mp2.inputs[0])
    nt.links.new(mp2.outputs[0], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], mr.inputs["Value"])
    mulc = nt.nodes.new("ShaderNodeVectorMath")
    mulc.operation = 'SCALE'
    nt.links.new(tex.outputs["Color"], mulc.inputs[0])
    nt.links.new(mr.outputs[0], mulc.inputs["Scale"])
    nt.links.new(mulc.outputs[0], em.inputs["Color"])
    em.inputs["Strength"].default_value = BACKDROP_STRENGTH
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    m.cycles.emission_sampling = 'NONE'      # found by BSDF sampling only: no shadow rays through the glass
    me.materials.append(m)
    me.update()
    ob = _link(bpy.data.objects.new("Backdrop", me))
    ob.parent = rig
    ob.visible_shadow = False
    _state["backdrop_mat"] = m
    return ob


def _build_strips():
    """two tall cool area lights behind-left / behind-right of the glass, just in front of the paper.
    Invisible to camera and transmission rays and light-linked to the glass / water / drops only,
    so they only ever show up as thin reflections along the glass edges (lights do not occlude)."""
    rig = _state["rig"]
    obs = []
    for sgn in (-1, 1):
        a = math.radians(STRIP_AZ_DEG) * sgn
        cx, cy = STRIP_DIST * math.sin(a), STRIP_DIST * math.cos(a)
        ld = bpy.data.lights.new("CoolStrip", 'AREA')
        ld.shape = 'RECTANGLE'
        ld.size = STRIP_WIDTH
        ld.size_y = STRIP_Z[1] - STRIP_Z[0]
        ld.color = COOL
        ld.energy = STRIP_POWER
        try:
            ld.use_shadow = False
        except Exception:
            pass
        ob = _link(bpy.data.objects.new("CoolStrip", ld))
        ob.location = (cx, cy, 0.5 * (STRIP_Z[0] + STRIP_Z[1]))
        ob.rotation_mode = 'QUATERNION'
        ob.rotation_quaternion = Vector((-cx, -cy, 0.0)).to_track_quat('-Z', 'Y')
        ob.parent = rig
        ob.visible_camera = False
        ob.visible_transmission = False
        ob.visible_diffuse = False
        ob.visible_volume_scatter = False
        obs.append(ob)
    _state["strips"] = obs
    # soft key for the ink drops only: front-left-high, turns with the rig
    ld = bpy.data.lights.new("DropKey", 'AREA')
    ld.shape = 'RECTANGLE'
    ld.size = 0.30
    ld.size_y = 0.30
    ld.color = (0.80, 0.90, 1.00)
    ld.energy = DROP_KEY_POWER
    key = _link(bpy.data.objects.new("DropKey", ld))
    key.location = (-0.26, -0.34, 0.46)
    key.rotation_mode = 'QUATERNION'
    key.rotation_quaternion = (Vector((0.0, 0.0, 0.14)) - Vector(key.location)).to_track_quat('-Z', 'Y')
    key.parent = rig
    key.visible_camera = False
    key.visible_transmission = False
    _state["drop_key"] = key
    return obs


def _link_strips():
    """restrict the cool strips to the glass, water and drops (no streaks in the table reflection)"""
    try:
        coll = bpy.data.collections.new("StripReceivers")
        for key in ("glass", "water", "drop_primary", "drop_secondary"):
            coll.objects.link(_state[key])
        for ob in _state["strips"]:
            ob.light_linking.receiver_collection = coll
        coll2 = bpy.data.collections.new("DropKeyReceivers")
        for key in ("drop_primary", "drop_secondary"):
            coll2.objects.link(_state[key])
        _state["drop_key"].light_linking.receiver_collection = coll2
    except Exception as e:                               # pragma: no cover
        print("scene_lib: light linking unavailable:", e)


# ================================================================== table (dark polished stone + light pad)
def _build_table():
    seg = 128
    radii = [0.0, 0.02, 0.04, 0.06, 0.09, 0.14, 0.3, 0.8, TABLE_R]
    prof = [(r, 0.0, 0) for r in radii]
    m, nt = _new_mat("Table")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    dif = nt.nodes.new("ShaderNodeBsdfDiffuse")
    dif.inputs["Color"].default_value = (0.006, 0.006, 0.007, 1)
    gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1)
    gl.inputs["Roughness"].default_value = TABLE_ROUGH
    fr = nt.nodes.new("ShaderNodeFresnel")
    fr.inputs["IOR"].default_value = 1.5
    cap = nt.nodes.new("ShaderNodeMath")
    cap.operation = 'MINIMUM'
    cap.inputs[1].default_value = TABLE_REFL_MAX
    nt.links.new(fr.outputs[0], cap.inputs[0])
    mixs = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(cap.outputs[0], mixs.inputs[0])
    nt.links.new(dif.outputs[0], mixs.inputs[1])
    nt.links.new(gl.outputs[0], mixs.inputs[2])
    # subtle large-scale roughness breakup (polished stone, not a mirror)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 9.0
    noise.inputs["Detail"].default_value = 3.0
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.3
    mr.inputs["From Max"].default_value = 0.7
    mr.inputs["To Min"].default_value = TABLE_ROUGH * 0.8
    mr.inputs["To Max"].default_value = TABLE_ROUGH * 1.25
    nt.links.new(geo.outputs["Position"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs[0], gl.inputs["Roughness"])
    # glowing pad: radial falloff around the glass axis
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    ln = nt.nodes.new("ShaderNodeVectorMath")
    ln.operation = 'LENGTH'
    nt.links.new(geo.outputs["Position"], sep.inputs[0])
    nt.links.new(sep.outputs["X"], comb.inputs["X"])
    nt.links.new(sep.outputs["Y"], comb.inputs["Y"])
    nt.links.new(comb.outputs[0], ln.inputs[0])
    fall = nt.nodes.new("ShaderNodeMapRange")
    fall.name = "PadFalloff"
    fall.interpolation_type = 'SMOOTHERSTEP'
    fall.inputs["From Min"].default_value = PAD_RADIUS + PAD_SOFT
    fall.inputs["From Max"].default_value = max(PAD_RADIUS - PAD_SOFT, 0.0)
    fall.inputs["To Min"].default_value = 0.0
    fall.inputs["To Max"].default_value = 1.0
    nt.links.new(ln.outputs["Value"], fall.inputs["Value"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (1.0, 0.42, 0.13, 1)
    ramp.color_ramp.elements[1].position = 0.8
    ramp.color_ramp.elements[1].color = (1.0, 0.80, 0.56, 1)
    nt.links.new(fall.outputs[0], ramp.inputs[0])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.name = "PadStrength"
    mul.operation = 'MULTIPLY'
    mul.inputs[1].default_value = PAD_STRENGTH
    nt.links.new(fall.outputs[0], mul.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(ramp.outputs["Color"], em.inputs["Color"])
    nt.links.new(mul.outputs[0], em.inputs["Strength"])
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(mixs.outputs[0], add.inputs[0])
    nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs["Surface"])
    m.cycles.emission_sampling = 'NONE'
    ob = _lathe("Table", prof, seg, [m])
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    bm.to_mesh(ob.data)
    bm.free()
    _state["table_mat"] = m
    return ob


# ================================================================== ink volume + drops
def _build_ink():
    vol = bpy.data.volumes.new("Ink")
    ob = _link(bpy.data.objects.new("Ink", vol))
    m, nt = _new_mat("InkVol")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ab = nt.nodes.new("ShaderNodeVolumeAbsorption")
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name = "density"
    mul = nt.nodes.new("ShaderNodeMath")
    mul.name = "InkDensityScale"
    mul.operation = 'MULTIPLY'
    mul.inputs[1].default_value = INK_DENSITY_SCALE
    ab.inputs["Color"].default_value = (*INK_TINT, 1)
    nt.links.new(at.outputs["Fac"], mul.inputs[0])
    nt.links.new(mul.outputs[0], ab.inputs["Density"])
    nt.links.new(ab.outputs[0], out.inputs["Volume"])
    vol.materials.append(m)
    ob.hide_render = True
    _state["ink_mat"] = m
    return ob


def _ink_surface_mat():
    m, nt = _new_mat("InkDrop")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Base Color"].default_value = (0.0035, 0.0045, 0.008, 1)
    p.inputs["Roughness"].default_value = 0.035
    p.inputs["IOR"].default_value = 1.40
    nt.links.new(p.outputs[0], out.inputs["Surface"])
    return m


def _build_drops():
    mat = _ink_surface_mat()
    obs = {}
    for name in ("DropPrimary", "DropSecondary"):
        me = bpy.data.meshes.new(name)
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=96, v_segments=48, radius=1.0)
        bm.to_mesh(me)
        bm.free()
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
        me.materials.append(mat)
        me.update()
        ob = _link(bpy.data.objects.new(name, me))
        ob.hide_render = True
        obs[name] = ob
    return obs


# ================================================================== public API
def build(clear=True):
    """Build the whole static set in the current scene (call once per Blender session)."""
    sc = _scene()
    if clear:
        for ob in list(bpy.data.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
    _state.clear()
    _state["glass"] = _build_glass()
    _state["water"] = _build_water()
    _state["table"] = _build_table()
    _state["backdrop"] = _build_backdrop()
    _build_strips()
    _state["ink"] = _build_ink()
    drops = _build_drops()
    _state["drop_primary"] = drops["DropPrimary"]
    _state["drop_secondary"] = drops["DropSecondary"]
    _link_strips()
    # world: almost black, slightly cool
    w = bpy.data.worlds.new("World")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.0025, 0.0028, 0.0035, 1)
    sc.world = w
    # camera
    cd = bpy.data.cameras.new("Cam")
    cd.sensor_width = 36.0
    cd.clip_start = 0.005
    cd.clip_end = 50.0
    cam = _link(bpy.data.objects.new("Cam", cd))
    sc.camera = cam
    _state["cam"] = cam
    set_camera((0.0, -0.78, 0.105), (0.0, 0.0, 0.075), lens_mm=85)
    apply_state(-1.0)
    return _state


def apply_state(t):
    """Pose everything that depends on sim time t (stateless; any t in any order)."""
    t = float(t)
    water = _state["water"]
    co = _state["water_co"]
    co[:, 2] = _state["water_sampler"].height(t)
    water.data.vertices.foreach_set("co", co.ravel())
    water.data.update()
    seen = set()
    for d in SM.drop_state(t):
        ob = _state["drop_primary"] if d["name"] == "primary" else _state["drop_secondary"]
        ob.location = d["center"]
        ob.scale = d["radii"]
        ob.hide_render = False
        ob.hide_viewport = False
        seen.add(ob.name)
    for key in ("drop_primary", "drop_secondary"):
        ob = _state[key]
        if ob.name not in seen:
            ob.hide_render = True
            ob.hide_viewport = True
    bpy.context.view_layer.update()


def set_ink(vdb_path, density_scale=None):
    """Point the 'Ink' volume at one VDB file (grid 'density'), or hide it with None."""
    ob = _state["ink"]
    if density_scale is not None:
        _state["ink_mat"].node_tree.nodes["InkDensityScale"].inputs[1].default_value = float(density_scale)
    if not vdb_path:
        ob.hide_render = True
        ob.hide_viewport = True
        return
    vol = ob.data
    vol.is_sequence = False
    vol.filepath = os.path.abspath(vdb_path)
    try:
        vol.grids.load()
    except Exception:
        pass
    ob.hide_render = False
    ob.hide_viewport = False


def set_camera(loc, look_at, lens_mm=85, fstop=None, focus_dist=None, roll_deg=0.0):
    """Place 'Cam'.  fstop None = DOF off; focus_dist None = focus on look_at.
    roll_deg > 0 rolls the camera counter-clockwise about its viewing direction."""
    cam = _state["cam"]
    loc = Vector(loc)
    look = Vector(look_at)
    d = look - loc
    q = d.to_track_quat('-Z', 'Y')
    if roll_deg:
        q = q @ Quaternion((0.0, 0.0, 1.0), math.radians(roll_deg))
    cam.rotation_mode = 'QUATERNION'
    cam.rotation_quaternion = q
    cam.location = loc
    cd = cam.data
    cd.lens = float(lens_mm)
    cd.dof.focus_object = None
    if fstop is None:
        cd.dof.use_dof = False
    else:
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = float(fstop)
        cd.dof.aperture_blades = 0
        cd.dof.focus_distance = float(focus_dist) if focus_dist is not None else d.length
    _apply_denoise_mode()
    if BACKDROP_FOLLOW:
        hl = math.hypot(d.x, d.y)
        if hl > 0.12 * d.length:                 # not (nearly) straight down
            # where the viewing axis meets the paper screen (far side of the cylinder r = PANEL_R)
            ux, uy = d.x / hl, d.y / hl
            bq = loc.x * ux + loc.y * uy
            cq = loc.x ** 2 + loc.y ** 2 - PANEL_R ** 2
            disc = bq * bq - cq
            sq = -bq + math.sqrt(disc) if disc > 0 else 0.0
            z_hit = loc.z + sq * d.z / hl
            _state["backdrop_az"] = math.degrees(math.atan2(d.x, d.y))
            _state["backdrop_z"] = min(max(z_hit, 0.05), PANEL_H - 0.35)
        set_backdrop(_state.get("backdrop_az", 0.0), None, _state.get("backdrop_z", 0.10))
    if PAD_AUTO:
        elev = math.degrees(math.asin(max(-1.0, min(1.0, -d.z / d.length))))
        k = _sstep((elev - 6.0) / 26.0) * (1.0 - _sstep((elev - 50.0) / 25.0))
        kt = _sstep((elev - 55.0) / 20.0)          # top-down: tight halo just outside the glass
        r = PAD_RADIUS + (0.17 - PAD_RADIUS) * k
        sft = PAD_SOFT + (0.15 - PAD_SOFT) * k
        set_pad(PAD_STRENGTH * (1.0 + 0.35 * k + 0.9 * kt), r + (0.060 - r) * kt, sft + (0.040 - sft) * kt)


def _apply_denoise_mode():
    """OIDN guide passes.  Colour-only on purpose: with depth of field the un-prefiltered
    albedo/normal guides are noisy and make OIDN keep the grain, and *changing* the guide passes
    between renders of one session crashes OIDN in Blender 5.2 (access violation with persistent
    data).  So this is set once and never switched."""
    _scene().cycles.denoising_input_passes = DENOISE_PASSES


def set_backdrop(azimuth_deg=None, strength=None, height=None):
    """Aim the paper lantern: azimuth of the hot spot about Z, emission scale, hot spot height.
    azimuth_deg = 0: screen centred on +Y (behind the glass for the front camera); positive =
    towards +X.  height = z of the hot spot centre on the screen (metres).  None keeps a value.
    With BACKDROP_FOLLOW = True (default) set_camera() calls this itself so that the hot spot sits
    exactly where the viewing axis meets the screen, i.e. always behind the subject (a lantern on
    the camera rig; equivalently the glass on a turntable).  The cool edge strips turn with it.
    Set scene_lib.BACKDROP_FOLLOW = False and call this yourself for a world-fixed lantern (the
    screen spans +-82 deg, so a fixed lantern supports orbits of roughly +-35 deg)."""
    if azimuth_deg is None:
        azimuth_deg = _state.get("backdrop_az", 0.0)
    if strength is None:
        strength = _state.get("backdrop_strength", 1.0)
    if height is None:
        height = _state.get("backdrop_z", 0.10)
    _state["backdrop_az"] = float(azimuth_deg)
    _state["backdrop_strength"] = float(strength)
    _state["backdrop_z"] = float(height)
    _state["rig"].rotation_euler = (0.0, 0.0, -math.radians(azimuth_deg))
    nt = _state["backdrop_mat"].node_tree
    nt.nodes["BackdropMapping"].inputs["Location"].default_value = (0.0, 0.5 - height / PANEL_H, 0.0)
    nt.nodes["BackdropEmission"].inputs["Strength"].default_value = BACKDROP_STRENGTH * float(strength)


def set_pad(strength=PAD_STRENGTH, radius=None, soft=None):
    """Glowing disc set into the table under the glass (radiance at its centre; 0 = off).
    Emission is full inside radius - soft and fades to 0 at radius + soft.
    With PAD_AUTO = True (default) set_camera() calls this itself: small pad for low cameras,
    a wide soft pool of light for 15..50 deg elevation (so the ink still has a bright ground
    behind it), small again for top-down views.  Set scene_lib.PAD_AUTO = False to take over."""
    nt = _state["table_mat"].node_tree
    nt.nodes["PadStrength"].inputs[1].default_value = float(strength)
    if radius is not None or soft is not None:
        f = nt.nodes["PadFalloff"]
        r = PAD_RADIUS if radius is None else radius
        s = PAD_SOFT if soft is None else soft
        f.inputs["From Min"].default_value = r + s
        f.inputs["From Max"].default_value = max(r - s, 0.0)


def set_exposure(ev):
    _scene().view_settings.exposure = float(ev)


PRESETS = {
    # pct: resolution %, samples: max spp, thr: adaptive noise threshold, min_s: adaptive min spp,
    # bounces: max / transmission bounces, dq: OIDN quality
    "preview": dict(pct=50, samples=12, thr=0.05, min_s=4, bounces=10, dq='FAST'),
    "final":   dict(pct=100, samples=6, thr=0.04, min_s=4, bounces=10, dq='HIGH'),
    "final_fast": dict(pct=100, samples=4, thr=0.04, min_s=4, bounces=10, dq='BALANCED'),
}


def configure_render(preset="final", threads=14):
    """Cycles CPU render settings.  Presets: 'preview' (960x540), 'final' (1920x1080, 6 spp max +
    OIDN high), 'final_fast' (1920x1080, 4 spp + OIDN balanced; ~3 s/frame cheaper)."""
    P = PRESETS[preset]
    sc = _scene()
    r = sc.render
    r.engine = 'CYCLES'
    cy = sc.cycles
    cy.device = 'CPU'
    cy.samples = P["samples"]
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = P["thr"]
    cy.adaptive_min_samples = P["min_s"]
    cy.use_denoising = True
    cy.denoiser = 'OPENIMAGEDENOISE'
    cy.denoising_prefilter = 'FAST'
    _apply_denoise_mode()
    try:
        cy.denoising_quality = P["dq"]
    except Exception:
        pass
    b = P["bounces"]
    cy.max_bounces = b
    cy.transmission_bounces = b
    cy.glossy_bounces = 6
    cy.diffuse_bounces = 1
    cy.volume_bounces = 0
    cy.transparent_max_bounces = 8
    cy.caustics_reflective = False
    cy.caustics_refractive = False
    cy.blur_glossy = 0.3
    cy.sample_clamp_direct = 0.0
    cy.sample_clamp_indirect = 8.0
    r.resolution_x, r.resolution_y = C.RES
    r.resolution_percentage = P["pct"]
    r.threads_mode = 'FIXED'
    r.threads = int(threads)
    r.use_persistent_data = True
    r.film_transparent = False
    r.use_motion_blur = False
    vs = sc.view_settings
    vs.view_transform = 'AgX'
    for look in ('AgX - Medium High Contrast', 'Medium High Contrast', 'AgX - Base Contrast', 'None'):
        try:
            vs.look = look
            break
        except Exception:
            continue
    vs.exposure = 0.0
    vs.gamma = 1.0
    r.image_settings.file_format = 'PNG'
    r.image_settings.color_mode = 'RGB'
    r.image_settings.color_depth = '8'
    r.image_settings.compression = 15
    r.dither_intensity = 1.0
    return P


def render_still(path):
    sc = _scene()
    sc.render.filepath = os.path.abspath(path)
    bpy.ops.render.render(write_still=True)
    return sc.render.filepath
