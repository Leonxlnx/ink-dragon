"""Shot list: cameras (per video frame) and ink-volume bake specs (voxel size / region of interest).
Pure Python + NumPy; used by both the bake driver and the Blender render driver."""
import math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as cm
from ink import film
from ink.dragon import Dragon

WZ = cm.WATER_Z
DX, DY = cm.DROP_XY
T_F = film.T_F

try:
    import surface_model as _sm
except Exception:
    _sm = None

_D = object.__new__(Dragon); _D.M = Dragon.M      # light-weight: only spine() is used


def sim_time(f):
    return float(film.ALL_T[int(f)])


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def lerp(a, b, u):
    return a + (b - a) * u


def v3(a, b, u):
    return tuple(lerp(x, y, u) for x, y in zip(a, b))


def orbit(az_deg, dist, z, tgt=(0.0, 0.0, 0.0)):
    """az = 0: camera in front (-Y). Positive az swings the camera toward +X."""
    a = math.radians(az_deg)
    return (tgt[0] + dist * math.sin(a), tgt[1] - dist * math.cos(a), z)


def drop_z(t):
    if _sm is None:
        return WZ + 0.02
    st = _sm.drop_state(t)
    if not st:
        return WZ + 0.004
    return float(st[0]["center"][2])


def ring_z(t):
    """height of the leading ink front (primary ring, later the lobes)"""
    tt = max(t - film.T_START, 0.0)
    U0, tau = 0.20, 0.11
    z = WZ - 0.0042 - U0 * tau * math.log(1 + min(tt, 0.85) / tau)
    if t > 0.85:
        z -= 0.019 * (1 - math.exp(-(t - 0.85) / 0.9)) * 1.6
    return z


def turn_deg(t):
    """how far the dragon has turned about the glass axis (deg, CCW from above) relative to mid-life"""
    return math.degrees(-0.15 * ((t - T_F) - 1.5))


def head_pose(t):
    sp = _D.spine(t - T_F)
    oh = np.asarray(sp["oh"], float); R = sp["Rh"]
    return oh, R[:, 0], R[:, 2], sp


# ---------------------------------------------------------------- shots
# name, first frame, last frame (exclusive), voxel size (m) for the ink volume, roi ('auto' or (lo, hi))
SHOTS = [
    dict(spp=8, resx=1920, name="s01_establish",   f0=0,    f1=105,  vox=None,     roi=None),
    dict(spp=8, resx=1920, name="s01b_waterline",  f0=105,  f1=160,  vox=None,     roi=None),
    dict(spp=8, resx=1920, name="s02_drop_fall",   f0=160,  f1=195,  vox=None,     roi=None),
    dict(spp=7, resx=1600, name="s03a_impact",     f0=195,  f1=255,  vox=0.065e-3, roi=((DX - 0.013, DY - 0.013, WZ - 0.024), (DX + 0.013, DY + 0.013, WZ + 0.0015))),
    dict(spp=6, resx=1600, name="s03b_waterline",  f0=255,  f1=315,  vox=0.085e-3, roi=((DX - 0.017, DY - 0.017, WZ - 0.046), (DX + 0.017, DY + 0.017, WZ + 0.0015))),
    dict(spp=6, resx=1600, name="s04a_ring_track", f0=315,  f1=420,  vox=0.12e-3,  roi="auto"),
    dict(spp=7, resx=1920, name="s04b_low_wide",   f0=420,  f1=600,  vox=0.20e-3,  roi="auto"),
    dict(spp=6, resx=1600, name="s05_morph_orbit", f0=600,  f1=675,  vox=0.16e-3,  roi="auto"),
    dict(spp=7, resx=1600, name="s06_head_roar",   f0=675,  f1=780,  vox=0.14e-3,  roi=((-0.0375, -0.0375, 0.062), (0.0375, 0.0375, WZ + 0.0015))),
    dict(spp=6, resx=1600, name="s07_body_glide",  f0=780,  f1=870,  vox=0.15e-3,  roi="auto"),
    dict(spp=7, resx=1920, name="s08_top_down",    f0=870,  f1=945,  vox=0.20e-3,  roi="auto"),
    dict(spp=8, resx=1920, name="s09_hero_wide",   f0=945,  f1=1065, vox=0.20e-3,  roi="auto"),
    dict(spp=7, resx=1920, name="s10_dissolve_34", f0=1065, f1=1155, vox=0.20e-3,  roi="auto"),
    dict(spp=7, resx=1920, name="s11_final_wide",  f0=1155, f1=1350, vox=0.20e-3,  roi="auto"),
]


def shot_of(f):
    for s in SHOTS:
        if s["f0"] <= f < s["f1"]:
            return s
    return SHOTS[-1]


def camera(f):
    """-> dict(loc, look_at, lens_mm, fstop, focus_dist)"""
    s = shot_of(f)
    u = (f - s["f0"]) / max(s["f1"] - s["f0"] - 1, 1)
    e = ease(u)
    t = sim_time(f)
    n = s["name"]
    fstop = None; focus = None
    if n == "s01_establish":
        tgt = (0.0, 0.0, lerp(0.088, 0.078, e))
        loc = orbit(lerp(-9, -3, e), lerp(1.04, 0.80, e), lerp(0.165, 0.112, e), tgt)
        lens, fstop = 85, 8.0
    elif n == "s01b_waterline":
        tgt = (DX * 0.5, DY * 0.5, WZ + 0.004)
        loc = orbit(lerp(-12, -3, e), lerp(0.262, 0.245, e), WZ + lerp(0.013, 0.008, e), (0, 0, 0))
        lens, fstop = 105, 11.0
    elif n == "s02_drop_fall":
        dz = drop_z(t)
        zt = WZ + 0.010 + 0.55 * (dz - WZ - 0.010)
        tgt = (DX, DY, zt)
        loc = orbit(lerp(10, 6, u), lerp(0.255, 0.245, u), zt + 0.010, (DX, DY, 0))
        lens, fstop = 120, 11.0
        focus = math.dist(loc, (DX, DY, dz))
    elif n == "s03a_impact":
        tgt = (DX, DY, WZ + 0.0035)
        loc = orbit(lerp(6, 2, e), lerp(0.262, 0.225, e), WZ + lerp(0.050, 0.040, e), (DX, DY, 0))
        lens, fstop = 105, 16.0
    elif n == "s03b_waterline":
        tgt = (DX, DY, WZ - lerp(0.008, 0.013, e))
        loc = orbit(lerp(5, 9, e), lerp(0.250, 0.240, e), WZ - lerp(0.005, 0.009, e), (DX, DY, 0))
        lens, fstop = 105, 11.0
    elif n == "s04a_ring_track":
        zc = ring_z(t)
        tgt = (DX * 0.6, DY * 0.6, zc + 0.004)
        loc = orbit(lerp(14, -10, e), lerp(0.29, 0.31, e), zc + lerp(0.036, 0.028, e), (0, 0, 0))
        lens, fstop = 135, 16.0
    elif n == "s04b_low_wide":
        tgt = (0.0, 0.0, lerp(0.080, 0.072, e))
        loc = orbit(lerp(10, 2, e), lerp(0.64, 0.58, e), lerp(0.020, 0.034, e), (0, 0, 0))
        lens, fstop = 70, 8.0
    elif n == "s05_morph_orbit":
        tgt = (lerp(0.0, 0.006, e), 0.0, lerp(0.064, 0.094, e))
        loc = orbit(lerp(-34, 8, e), lerp(0.44, 0.34, e), lerp(0.066, 0.102, e), (0, 0, 0))
        lens, fstop = 100, 11.0
    elif n == "s06_head_roar":
        oh, fw, up, sp = head_pose(t)
        hc = oh + fw * 0.013 + up * 0.004
        tgt = tuple(hc + np.array([0.002, 0.0, 0.002]))
        loc = orbit(lerp(-7, 9, e) + turn_deg(t), lerp(0.405, 0.365, e), hc[2] + lerp(0.004, 0.012, e), (hc[0], hc[1], 0))
        lens, fstop = 135, 22.0
    elif n == "s07_body_glide":
        oh, fw, up, sp = head_pose(t)
        C = sp["C"]
        i = int(lerp(0.10, 0.74, e) * (len(C) - 1))
        p = C[i].astype(float)
        tgt = (p[0] * 0.55, p[1] * 0.55, p[2] + 0.004)
        loc = orbit(lerp(26, -52, e), 0.30, p[2] + 0.022, (0, 0, 0))
        lens, fstop = 100, 16.0
    elif n == "s08_top_down":
        a = math.radians(lerp(-25, 20, e))
        tgt = (0.0, 0.0, 0.06)
        loc = (0.105 * math.sin(a), -0.105 * math.cos(a), lerp(0.62, 0.56, e))
        lens, fstop = 85, 11.0
    elif n == "s09_hero_wide":
        tgt = (0.0, 0.0, 0.074)
        loc = orbit(lerp(-7, 5, e) + turn_deg(t), lerp(0.78, 0.635, e), 0.098, (0, 0, 0))
        lens, fstop = 85, 8.0
    elif n == "s10_dissolve_34":
        tgt = (0.0, 0.0, 0.072)
        loc = orbit(lerp(32, 12, e), lerp(0.46, 0.52, e), lerp(0.058, 0.070, e), (0, 0, 0))
        lens, fstop = 85, 8.0
    else:  # s11_final_wide
        # ends exactly on the first frame's camera, so the film loops seamlessly
        tgt = (0.0, 0.0, lerp(0.076, 0.088, e))
        loc = orbit(lerp(4, -9, e), lerp(0.70, 1.04, e), lerp(0.100, 0.165, e), (0, 0, 0))
        lens, fstop = 85, 8.0
    return dict(loc=tuple(float(x) for x in loc), look_at=tuple(float(x) for x in tgt), lens_mm=lens, fstop=fstop, focus_dist=focus)


def bake_spec(f):
    """-> (vox, lo, hi) or None if this frame needs no ink volume"""
    s = shot_of(f)
    if s["vox"] is None or sim_time(f) < film.T_START:
        return None
    if s["roi"] == "auto":
        return s["vox"], None, None
    return s["vox"], s["roi"][0], s["roi"][1]
