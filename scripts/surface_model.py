"""Drop / water-surface physics for the ink-dragon film.  Pure NumPy, no bpy.

Stateless closed-form functions of sim time t [s]  (t = 0: the ink drop first touches the water).
Units: metres, seconds.  World: Z up, glass axis = Z axis (see common.py).

    surface_height(x, y, t)  -> absolute z of the water surface (vectorised over x, y; scalar t)
    surface_static(x, y)     -> rest surface (flat WATER_Z + meniscus), == surface_height(x, y, t<0)
    drop_state(t)            -> list of dicts, one per airborne / merging droplet
    SurfaceSampler(x, y)     -> object with .height(t): fast repeated evaluation on fixed points
    EVENTS                   -> dict of the key event times listed below

KEY EVENT TIMES (seconds, see EVENTS):
    release            -0.1223   drop released from rest 73.4 mm above the contact position
    contact             0.0000   drop bottom touches the water (speed 1.2 m/s)
    drop_swallowed      0.0042   primary drop fully flattened into the crater floor (mesh gone)
    crown_max           0.0045   small crown / rim at its highest (~0.6 mm)
    crater_max          0.0180   crater deepest: 4.0 mm deep, ~7.4 mm wide at the rest level
    jet_start           0.0290   crater has refilled, Worthington jet starts rising
    pinch_off           0.0510   jet tip (bulb) pinches off as a secondary droplet (r = 0.85 mm)
    jet_max             0.0525   jet column highest, ~8.5 mm above the rest level
    droplet_apex        0.0800   secondary droplet highest (centre ~11.9 mm above rest level)
    jet_end             0.0845   jet column has fallen back into the surface
    droplet_land        0.1274   secondary droplet touches down (0.47 m/s), small second crater
    droplet_swallowed   0.1331   secondary droplet gone
    wall_first_hit     ~0.14     first ripple ring reaches the glass wall (near side)
    refocus            ~0.28     reflected rings converge near the mirror point (-DROP_XY)
    calm               ~2.2      ripples below ~10 micrometres (60 um at 1.0 s, 20 um at 1.5 s)
  Ripple periods are ~30-60 ms (wavelengths 4-12 mm, speeds ~0.25-0.35 m/s): at real-time 30 fps
  they alias, so show the splash in slow motion (>= 4x) or rely on motion blur.

MODEL
  * rest:       WATER_Z + static meniscus (2.2 mm climb at the wall, contact line pinned).
  * 0..18 ms:   explicit crater  -D(t) (1-s^2) exp(-s^2),  s = rho / W(t)  (zero net volume) + crown.
  * >= 18 ms:   the crater-at-maximum is released as the initial condition of the *linear
                capillary-gravity wave problem in a circular basin* and evolved exactly with
                Bessel modes  J_m(k_mn r) cos(m theta)  (Neumann wall, off-axis source handled,
                omega^2 = g k + sigma k^3 / rho, viscous + wall damping).  This yields the crater
                collapse, the outgoing ripple rings, their reflection off the wall and refocusing.
  * jet:        explicit thin ballistic column on top (the linear rebound is too low/short), with
                bulb, pinch-off and fall-back; the jet fall-back and the secondary droplet landing
                launch two further small modal wave trains.
  * the dynamic displacement is multiplied by a pinning window that goes to 0 at the wall
    (pinned contact line), so the wetted line on the glass never moves.
Everything is C1 in time (velocities continuous) apart from sub-micrometre truncation residuals.
"""
import math
import numpy as np

try:                                    # works both as  scripts.surface_model  and as a top-level module
    from . import common as _c
except Exception:                       # pragma: no cover
    import os as _os, sys as _sys
    _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
    import common as _c

WATER_Z = _c.WATER_Z
DROP_XY = tuple(_c.DROP_XY)
DROP_RADIUS = _c.DROP_RADIUS
DROP_IMPACT_SPEED = _c.DROP_IMPACT_SPEED
G = _c.G

# ---------------------------------------------------------------- fluid constants
SIGMA = 0.072          # N/m
RHO = 1000.0
NU = 1.0e-6
GAMMA0 = 1.7           # 1/s  extra (wall / contact line) damping applied to every mode
VISC_FACTOR = 2.0      # gamma = GAMMA0 + VISC_FACTOR * nu * k^2

# ---------------------------------------------------------------- static meniscus
MENISCUS_H = 0.0022                    # climb height at the wall
_MEN_A1, _MEN_L1 = 0.0012, 0.0027      # long (capillary length) part
_MEN_A2, _MEN_L2 = 0.0010, 0.0008      # steep part right at the wall
Z_CONTACT = WATER_Z + MENISCUS_H       # height of the (pinned) contact line
R_CONTACT = _c.r_in(Z_CONTACT)         # radius of the contact line == inner wall radius there
PIN_LEN = 0.0015                       # e-fold length of the pinning window

# ---------------------------------------------------------------- primary impact
T_CRATER = 0.018
CRATER_DEPTH = 0.0040
CRATER_W0 = 0.0013
CRATER_W1 = 0.0037
CROWN_H = 0.0006
CROWN_T = 0.0045

# ---------------------------------------------------------------- jet + secondary droplet
T_JET0 = 0.029
JET_V0 = 0.50                          # launch speed of the jet tip (ballistic)
T_PINCH = 0.051
T_BULB0 = 0.036                        # bulb starts to form at the tip
SEC_RADIUS = 0.00085
JET_RETRACT_V = 0.40                   # tip retraction speed after pinch-off
JET_W_COL = 0.00078                    # column radius scale
JET_W_BASE = 0.0026                    # flared base radius scale
JET_BASE_FRAC = 0.26
SUPPRESS_RHO = 0.0045                  # radius inside which the linear rebound is muted during the jet

# ---------------------------------------------------------------- modal machinery sizes
_K_MAX = 2400.0
_M_MAX = 18
_NR_TAB = 1600


def _smoothstep(u):
    u = np.clip(u, 0.0, 1.0)
    return u * u * (3.0 - 2.0 * u)


def _hat(s):
    """zero-volume 'Mexican hat' crater profile: 1 at centre, rim of -0.135 at s = sqrt(2)"""
    s2 = s * s
    return (1.0 - s2) * np.exp(-s2)


# ================================================================= derived event times
_DROP_D = math.hypot(*DROP_XY)                       # source distance from the axis
_DROP_PHI = math.atan2(DROP_XY[1], DROP_XY[0])
T_RELEASE = -DROP_IMPACT_SPEED / G
RELEASE_HEIGHT = DROP_IMPACT_SPEED ** 2 / (2 * G)     # above the contact position


def _crater_depth(t):
    """primary crater depth for 0 <= t <= T_CRATER"""
    u = min(max(t / T_CRATER, 0.0), 1.0)
    return CRATER_DEPTH * (2 * u - u * u)


def _crater_width(t):
    u = min(max(t / T_CRATER, 0.0), 1.0)
    return CRATER_W0 + (CRATER_W1 - CRATER_W0) * (2 * u - u * u)


def _solve_swallow(top0, speed, depth_fn, t_hi):
    """time at which a drop whose top moves down ballistically meets the crater floor"""
    lo, hi = 0.0, t_hi
    f = lambda t: top0 - speed * t + depth_fn(t)
    if f(hi) > 0:
        return hi
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if f(mid) > 0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


T_SWALLOW = _solve_swallow(2 * DROP_RADIUS, DROP_IMPACT_SPEED, _crater_depth, T_CRATER)


def _jet_top_ballistic(t):
    """height of the free ballistic 'tip parabola' above rest level (not clamped)"""
    tau = t - T_JET0
    return JET_V0 * tau - 0.5 * G * tau * tau


def _jet_retract(t):
    u = max(t - T_PINCH, 0.0)
    return JET_RETRACT_V * u * u / (u + 0.002)


def _find_root(f, lo, hi):
    for _ in range(70):
        mid = 0.5 * (lo + hi)
        if (f(lo) > 0) == (f(mid) > 0):
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


T_JET_END = _find_root(lambda t: _jet_top_ballistic(t) - _jet_retract(t), T_PINCH + 0.005, T_JET0 + 0.2)
T_DROPLET_APEX = T_JET0 + JET_V0 / G
T_DROPLET_LAND = _find_root(lambda t: _jet_top_ballistic(t) - 2 * SEC_RADIUS, T_DROPLET_APEX, T_JET0 + 0.3)
SEC_LAND_SPEED = -(JET_V0 - G * (T_DROPLET_LAND - T_JET0))          # positive, downwards
_T_JET_MAX = max(np.linspace(T_PINCH, T_PINCH + 0.01, 201),
                 key=lambda t: _jet_top_ballistic(t) - _jet_retract(t))

# secondary impacts (small craters), same explicit-then-modal structure as the primary
#   name, t0, t_crater, depth, w0, w1
_IMPACTS = [
    ("primary", 0.0, T_CRATER, CRATER_DEPTH, CRATER_W0, CRATER_W1),
    ("jetfall", T_JET_END - 0.004, 0.009, 0.0008, 0.0016, 0.0026),
    ("droplet", T_DROPLET_LAND, 0.007, 0.0010, 0.0008, 0.0019),
]
T_SEC_SWALLOW = T_DROPLET_LAND + _solve_swallow(
    2 * SEC_RADIUS, SEC_LAND_SPEED,
    lambda t: _IMPACTS[2][3] * (2 * min(t / 0.007, 1) - min(t / 0.007, 1) ** 2), 0.007)

EVENTS = {
    "release": T_RELEASE,
    "contact": 0.0,
    "crown_max": CROWN_T,
    "drop_swallowed": T_SWALLOW,
    "crater_max": T_CRATER,
    "jet_start": T_JET0,
    "pinch_off": T_PINCH,
    "jet_max": float(_T_JET_MAX),
    "droplet_apex": T_DROPLET_APEX,
    "jet_end": T_JET_END,
    "droplet_land": T_DROPLET_LAND,
    "droplet_swallowed": T_SEC_SWALLOW,
    "wall_first_hit": 0.14,
    "refocus": 0.28,
    "calm": 2.2,
}


# ================================================================= Bessel modes (lazy)
class _Modes:
    """Neumann modes of the disc r <= R_CONTACT, symmetric about the axis->source line."""

    def __init__(self):
        R = R_CONTACT
        xmax = _K_MAX * R
        h = 0.01
        x = np.arange(0.0, xmax + 2 * h, h)
        M = _M_MAX
        nq = 256
        while nq < xmax + M + 48:
            nq *= 2
        tau = 2 * np.pi * (np.arange(nq) + 0.5) / nq
        ph = np.outer(x, np.sin(tau))
        cp, sp = np.cos(ph), np.sin(ph)
        del ph
        tab = np.empty((M + 2, x.size))
        for m in range(M + 2):
            tab[m] = (cp @ np.cos(m * tau) + sp @ np.sin(m * tau)) / nq
        del cp, sp
        self.x, self.h, self.tab = x, h, tab

        # zeros of J_m'
        self.k = []          # per m: array of k_mn
        for m in range(M + 1):
            d = -tab[1] if m == 0 else 0.5 * (tab[m - 1] - tab[m + 1])
            i0 = int(0.5 / h) if m == 0 else int(0.3 / h)
            sgn = np.sign(d[i0:])
            idx = np.nonzero(sgn[:-1] * sgn[1:] < 0)[0] + i0
            xz = x[idx] - d[idx] * h / (d[idx + 1] - d[idx])
            xz = xz[xz < xmax]
            self.k.append(xz / R)
        self.nm = [len(k) for k in self.k]

        # radial tables  G[m][i, n] = J_m(k_mn r_i)
        self.rtab = np.linspace(0.0, R, _NR_TAB)
        self.G = [self._J(m, np.outer(self.rtab, self.k[m])) for m in range(M + 1)]
        self.omega = [np.sqrt(G * k + SIGMA * k ** 3 / RHO) for k in self.k]
        self.gamma = [GAMMA0 + VISC_FACTOR * NU * k ** 2 for k in self.k]

        # projection quadrature (polar, about the glass axis, theta' measured from the source direction)
        nr, nth = 1400, 256
        self.rq = (np.arange(nr) + 0.5) * (R / nr)
        self.dr = R / nr
        self.thq = 2 * np.pi * (np.arange(nth) + 0.5) / nth
        self.rho_q = np.sqrt(np.maximum(
            self.rq[:, None] ** 2 + _DROP_D ** 2 - 2 * self.rq[:, None] * _DROP_D * np.cos(self.thq)[None, :], 0))
        self.Jq = [self._J(m, np.outer(self.rq, self.k[m])) for m in range(M + 1)]
        self.norm = [np.sum(Jq * Jq * self.rq[:, None], axis=0) * self.dr for Jq in self.Jq]

    def _J(self, m, xx):
        return np.interp(xx, self.x, self.tab[m])

    def project(self, f_of_rho):
        """coefficients a[m][n] of an axisymmetric-about-the-source profile f(rho)"""
        f = f_of_rho(self.rho_q)
        nth = self.thq.size
        out = []
        for m in range(_M_MAX + 1):
            Fm = f @ np.cos(m * self.thq) * ((1.0 if m == 0 else 2.0) / nth)
            a = (Fm * self.rq) @ self.Jq[m] * self.dr / self.norm[m]
            out.append(a)
        return out

    def radial(self, coeffs):
        """list over m of radial tables  sum_n c_mn J_m(k_mn r)  on self.rtab"""
        return np.stack([self.G[m] @ coeffs[m] for m in range(_M_MAX + 1)])


_modes = None
_amps = None        # per impact: list over m of coefficient arrays
_rad0 = None        # per impact: radial tables of the modal sum at launch (for the residual)


def _get_modes():
    global _modes, _amps, _rad0
    if _modes is None:
        mo = _Modes()
        amps, rad0 = [], []
        for (_n, _t0, _tc, depth, _w0, w1) in _IMPACTS:
            a = mo.project(lambda rho, depth=depth, w1=w1: -depth * _hat(rho / w1))
            amps.append(a)
            rad0.append(mo.radial(a))
        _amps, _rad0, _modes = amps, rad0, mo
    return _modes


def _time_factor(mo, m, tau):
    g, w = mo.gamma[m], mo.omega[m]
    return np.exp(-g * tau) * (np.cos(w * tau) + (g / w) * np.sin(w * tau))


# ================================================================= time-only envelopes
def _suppress_q(t):
    """0..1: how strongly the linear central rebound is muted (the explicit jet replaces it)"""
    up = _smoothstep((t - (T_CRATER + 0.004)) / 0.014)
    down = 1.0 - _smoothstep((t - (T_JET_END - 0.010)) / 0.030)
    return float(up * down)


def _jet_ramp(t):
    return 1.0 - math.exp(-max(t - T_JET0, 0.0) / 0.002)


def _jet_height(t):
    """height of the jet column tip above the rest level (>= 0, C1)"""
    if t <= T_JET0 or t >= T_JET_END + 0.02:
        return 0.0
    hgt = (_jet_top_ballistic(t) - _jet_retract(t)) * _jet_ramp(t)
    if hgt <= 0.0:
        return 0.0
    eps = 0.0004
    return math.sqrt(hgt * hgt + eps * eps) - eps


def _bulb_radius(t):
    return SEC_RADIUS * math.sqrt(float(_smoothstep((t - T_BULB0) / (T_PINCH - T_BULB0))))


# ================================================================= static surface
def _static_from_r(r):
    d = np.maximum(R_CONTACT - r, 0.0)
    return WATER_Z + _MEN_A1 * np.exp(-d / _MEN_L1) + _MEN_A2 * np.exp(-d / _MEN_L2)


def _pin_from_r(r):
    d = np.maximum(R_CONTACT - r, 0.0)
    return 1.0 - np.exp(-d / PIN_LEN)


def surface_static(x, y):
    """rest water surface (absolute z): flat WATER_Z plus the meniscus at the wall"""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    return _static_from_r(np.hypot(x, y))


# ================================================================= dynamic surface
class SurfaceSampler:
    """Fast repeated evaluation of the surface on a fixed set of points.

        s = SurfaceSampler(x, y);  z = s.height(t)        # z has the broadcast shape of x, y
    """

    def __init__(self, x, y):
        x = np.asarray(x, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        x, y = np.broadcast_arrays(x, y)
        self.shape = x.shape
        x = x.ravel()
        y = y.ravel()
        self.r = np.hypot(x, y)
        self.rho = np.hypot(x - DROP_XY[0], y - DROP_XY[1])
        self.static = _static_from_r(self.r)
        self.pin = _pin_from_r(self.r)
        self._theta = np.arctan2(y, x) - _DROP_PHI
        self._modal_ready = False

    def _prep_modal(self):
        mo = _get_modes()
        rc = np.minimum(self.r, R_CONTACT)
        f = rc / R_CONTACT * (_NR_TAB - 1)
        i0 = np.minimum(f.astype(np.int64), _NR_TAB - 2)
        self._i0 = i0
        self._w = (f - i0)
        self._cosm = np.empty((_M_MAX + 1, self.r.size), dtype=np.float32)
        for m in range(_M_MAX + 1):
            self._cosm[m] = np.cos(m * self._theta)
        self._modal_ready = True
        return mo

    def _modal_eval(self, rad):
        """rad: (M+1, NR_TAB) radial tables -> field at the points"""
        i0, w = self._i0, self._w
        out = np.zeros(self.r.size)
        for m in range(_M_MAX + 1):
            row = rad[m]
            out += (row[i0] * (1.0 - w) + row[i0 + 1] * w) * self._cosm[m]
        return out

    def dynamic(self, t):
        """displacement relative to the rest surface, before the wall pinning window"""
        t = float(t)
        rho = self.rho
        out = np.zeros(rho.size)
        if t <= 0.0:
            return out
        modal_rad = None
        for i, (name, t0, tc, depth, w0, w1) in enumerate(_IMPACTS):
            if t <= t0:
                continue
            ta = t - t0
            if ta <= tc:                                   # explicit crater formation
                u = ta / tc
                e = 2 * u - u * u
                out += -(depth * e) * _hat(rho / (w0 + (w1 - w0) * e))
            else:                                          # linear modal evolution
                mo = _get_modes() if self._modal_ready else self._prep_modal()
                tau = ta - tc
                coeffs = [_amps[i][m] * _time_factor(mo, m, tau) for m in range(_M_MAX + 1)]
                rad = mo.radial(coeffs)
                resid = math.exp(-tau / 0.003)             # fade the tiny truncation residual
                if resid > 1e-5:
                    rad = rad - resid * _rad0[i]
                    out += resid * (-depth) * _hat(rho / w1)
                modal_rad = rad if modal_rad is None else modal_rad + rad
        if modal_rad is not None:
            q = _suppress_q(t)
            fld = self._modal_eval(modal_rad)
            if q > 0.0:
                fld *= 1.0 - q * np.exp(-(rho / SUPPRESS_RHO) ** 2)
            out += fld
        # crown / rim of the primary impact
        if t < 0.045:
            a = CROWN_H * (t / CROWN_T) * math.exp(1.0 - t / CROWN_T)
            if a > 1e-8:
                wc = _crater_width(t) + 0.02 * max(t - T_CRATER, 0.0)
                out += a * np.exp(-((rho - 1.3 * wc) / (0.3 * wc)) ** 2)
        # Worthington jet
        hj = _jet_height(t)
        if hj > 0.0:
            out += hj * ((1.0 - JET_BASE_FRAC) * np.exp(-(rho / JET_W_COL) ** 2.4)
                         + JET_BASE_FRAC * np.exp(-(rho / JET_W_BASE) ** 2))
        return out

    def height(self, t):
        if t <= 0.0:
            return self.static.reshape(self.shape).copy()
        return (self.static + self.pin * self.dynamic(t)).reshape(self.shape)


def surface_height(x, y, t):
    """Absolute z of the water surface at (x, y) [m] and sim time t [s].

    x, y: scalars or numpy arrays (broadcast together); t: scalar.  Outside the glass cavity the
    value at the wall (the pinned contact line height) is returned.  Exactly the rest surface for
    t <= 0.  For many calls on the same points use SurfaceSampler(x, y).height(t) (much faster).
    """
    s = SurfaceSampler(x, y)
    z = s.height(t)
    return z if z.shape else float(z)


# ================================================================= droplets
_OSC_F1 = math.sqrt(8 * SIGMA / (RHO * DROP_RADIUS ** 3)) / (2 * math.pi)     # ~54 Hz (Rayleigh n=2)
_OSC_F2 = math.sqrt(8 * SIGMA / (RHO * SEC_RADIUS ** 3)) / (2 * math.pi)      # ~154 Hz


def _center_floor(t):
    """absolute z of the water surface at the impact point"""
    return float(surface_height(DROP_XY[0], DROP_XY[1], t))


def _squash(top, bottom, R, cap=1.45):
    """radii + merge factor of a drop being flattened between its top and the crater floor"""
    rz = 0.5 * (top - bottom)
    if rz <= 1e-6:
        return None
    rz = min(rz, R)
    merge = 1.0 - rz / R
    rxy = min(R * math.sqrt(R / rz), cap * R)
    rxy *= 1.0 - float(_smoothstep((merge - 0.6) / 0.4))
    if rxy <= 1e-6:
        return None
    return rxy, rz, merge


def drop_state(t, include_pendant=False):
    """Airborne / merging droplets at sim time t.

    Returns a list of dicts (empty when nothing is airborne):
        name    'primary' | 'secondary'
        center  (x, y, z)  absolute, metres
        radii   (rx, ry, rz)  ellipsoid semi-axes (a falling drop oscillates oblate/prolate)
        merge   0..1   0 = free droplet in the air, 1 = fully part of the water body.
                The primary ramps 0->1 over 0..EVENTS['drop_swallowed'] while it is flattened onto
                the crater floor.  The secondary is 1 while it is still the bulb on the jet tip
                (EVENTS: before 'pinch_off'), 0 in flight, and ramps to 1 again on landing.
        vz      vertical velocity of the centre (m/s), for motion blur / streaks
    Before EVENTS['release'] the primary has not been released: it is omitted unless
    include_pendant=True (then it is returned at rest at the release height).
    """
    t = float(t)
    out = []
    R = DROP_RADIUS
    x0, y0 = DROP_XY
    # ---- primary
    if t < T_RELEASE:
        if include_pendant:
            out.append(dict(name="primary", center=(x0, y0, WATER_Z + R + RELEASE_HEIGHT),
                            radii=(R * 0.97, R * 0.97, R * 1.06), merge=0.0, vz=0.0))
    elif t <= 0.0:
        z = WATER_Z + R - DROP_IMPACT_SPEED * t - 0.5 * G * t * t
        ta = t - T_RELEASE
        a = 0.06 * math.exp(-ta / 0.30) * math.cos(2 * math.pi * _OSC_F1 * ta)     # prolate first
        out.append(dict(name="primary", center=(x0, y0, z),
                        radii=(R * (1 - 0.5 * a), R * (1 - 0.5 * a), R * (1 + a)),
                        merge=0.0, vz=-(DROP_IMPACT_SPEED + G * t)))
    elif t < T_SWALLOW:
        top = WATER_Z + 2 * R - DROP_IMPACT_SPEED * t
        bottom = WATER_Z - _crater_depth(t)
        sq = _squash(top, bottom, R)
        if sq is not None:
            rxy, rz, merge = sq
            out.append(dict(name="primary", center=(x0, y0, bottom + rz), radii=(rxy, rxy, rz),
                            merge=merge, vz=-0.5 * (DROP_IMPACT_SPEED + 2 * CRATER_DEPTH / T_CRATER)))
    # ---- secondary droplet (bulb on the jet tip -> free flight -> landing)
    r2 = SEC_RADIUS
    if T_BULB0 < t <= T_PINCH:
        rb = _bulb_radius(t)
        if rb > 1e-5:
            top = WATER_Z + _jet_top_ballistic(t) * _jet_ramp(t)
            out.append(dict(name="secondary", center=(x0, y0, top - rb), radii=(rb, rb, rb),
                            merge=1.0, vz=JET_V0 - G * (t - T_JET0)))
    elif T_PINCH < t <= T_DROPLET_LAND:
        zc = WATER_Z + _jet_top_ballistic(t) - r2
        ta = t - T_PINCH
        a = 0.10 * math.exp(-ta / 0.05) * math.cos(2 * math.pi * _OSC_F2 * ta)     # prolate at pinch-off
        merge = 1.0 - float(_smoothstep(ta / 0.004))
        out.append(dict(name="secondary", center=(x0, y0, zc),
                        radii=(r2 * (1 - 0.5 * a), r2 * (1 - 0.5 * a), r2 * (1 + a)),
                        merge=merge, vz=JET_V0 - G * (t - T_JET0)))
    elif T_DROPLET_LAND < t < T_SEC_SWALLOW:
        ta = t - T_DROPLET_LAND
        top = WATER_Z + 2 * r2 - SEC_LAND_SPEED * ta
        u = min(ta / _IMPACTS[2][2], 1.0)
        bottom = WATER_Z - _IMPACTS[2][3] * (2 * u - u * u)
        sq = _squash(top, bottom, r2)
        if sq is not None:
            rxy, rz, merge = sq
            out.append(dict(name="secondary", center=(x0, y0, bottom + rz), radii=(rxy, rxy, rz),
                            merge=merge, vz=-0.5 * SEC_LAND_SPEED))
    return out


if __name__ == "__main__":
    for k_, v_ in sorted(EVENTS.items(), key=lambda kv: kv[1]):
        print("%-18s %8.4f" % (k_, v_))
