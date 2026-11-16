"""Film timeline + ink choreography: plume (Lagrangian sheets in a vortex-ring flow) -> morph -> dragon -> dissolve.
Everything is expressed as control lattices of ink sheets (S, NU, NV, 3) + SDF solids, rasterised per frame.
Sim time t: 0 = drop touches the water."""
import os, sys, time
import numpy as np
from . import raster, fields
from .dragon import Dragon, NU, NV, MM, body_radius
from .util import smoothstep, Timer, write_png

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as cm

CACHE = os.path.join(cm.ROOT, "work", "cache")
VDB_DIR = os.path.join(cm.ROOT, "work", "vdb")
DIS_TAG = "_v2"          # dissolve simulation data set (file name suffix)

# ------------------------------------------------------------------ timeline
T_START = 0.006          # ink sim starts (drop swallowed)
T_M0 = 2.6               # morph begins
T_F = 5.0                # dragon fully formed
T_D = 8.0                # dissolve begins (dragon lives exactly 3.0 s)
T_END = 12.6
# (video seconds, sim seconds) knots of the retime curve (monotone cubic through these)
KNOTS = [(0.0, -1.0), (3.5, -0.118), (6.5, -0.004), (10.5, 0.22), (17.5, 2.6), (22.5, 5.0), (35.5, 8.0), (42.0, 11.0), (45.0, 12.5)]


def pchip(xk, yk, x):
    xk = np.asarray(xk, float); yk = np.asarray(yk, float); x = np.asarray(x, float)
    h = np.diff(xk); d = np.diff(yk) / h
    m = np.zeros_like(xk)
    for i in range(1, len(xk) - 1):
        if d[i - 1] * d[i] > 0:
            w1 = 2 * h[i] + h[i - 1]; w2 = h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    m[0] = d[0]; m[-1] = d[-1]
    i = np.clip(np.searchsorted(xk, x) - 1, 0, len(xk) - 2)
    t = (x - xk[i]) / h[i]
    h00 = 2 * t**3 - 3 * t**2 + 1; h10 = t**3 - 2 * t**2 + t; h01 = -2 * t**3 + 3 * t**2; h11 = t**3 - t**2
    return h00 * yk[i] + h10 * h[i] * m[i] + h01 * yk[i + 1] + h11 * h[i] * m[i + 1]


def frame_time(f):
    """sim time of video frame f (0-based)"""
    xk = [k[0] for k in KNOTS]; yk = [k[1] for k in KNOTS]
    return pchip(xk, yk, np.asarray(f, float) / cm.FPS)


ALL_T = frame_time(np.arange(cm.N_FRAMES))

# ------------------------------------------------------------------ quantised lattice storage
Q_LO = np.array([-0.045, -0.045, 0.0], np.float32)
Q_SPAN = np.array([0.090, 0.090, 0.140], np.float32)


def quant(X):
    return np.clip(np.round((X - Q_LO) / Q_SPAN * 65535.0) - 32768, -32768, 32767).astype(np.int16)


def dequant(Q):
    return (Q.astype(np.float32) + 32768.0) * (Q_SPAN / 65535.0) + Q_LO


# ------------------------------------------------------------------ surface helper
class Surface:
    """fast water-surface height near the impact point (fine local grid), flat elsewhere"""
    def __init__(self):
        try:
            import surface_model as sm
            self.sm = sm
        except Exception as e:
            print("surface_model unavailable:", e); self.sm = None
        self.half = 0.0075; self.n = 76
        ax = np.linspace(-self.half, self.half, self.n)
        self.gx, self.gy = np.meshgrid(ax + cm.DROP_XY[0], ax + cm.DROP_XY[1], indexing="ij")
        self.sampler = None
        if self.sm is not None and hasattr(self.sm, "SurfaceSampler"):
            try:
                self.sampler = self.sm.SurfaceSampler(self.gx.ravel(), self.gy.ravel())
            except Exception as e:
                print("SurfaceSampler failed:", e)
        self._t = None; self._h = None

    def grid(self, t):
        if self._t != t:
            if self.sm is None or t < 0 or t > 0.16:
                h = np.full((self.n, self.n), cm.WATER_Z, np.float32)
            elif self.sampler is not None:
                h = np.asarray(self.sampler.height(t), np.float32).reshape(self.n, self.n)
            else:
                h = np.asarray(self.sm.surface_height(self.gx, self.gy, t), np.float32)
            self._t = t; self._h = h
        return self._h

    def ceiling(self, x, y, t):
        """max allowed z for ink at (x,y): surface minus a margin"""
        margin = 0.00035 + 0.0004 * float(smoothstep(0.9, 0.16, t))
        out = np.full(x.shape, cm.WATER_Z - margin, np.float32)
        if self.sm is None or t > 0.16:
            return out
        h = self.grid(t)
        fx = (x - cm.DROP_XY[0] + self.half) / (2 * self.half) * (self.n - 1)
        fy = (y - cm.DROP_XY[1] + self.half) / (2 * self.half) * (self.n - 1)
        ok = (fx >= 0) & (fx < self.n - 1) & (fy >= 0) & (fy < self.n - 1)
        if ok.any():
            ix = fx[ok].astype(np.int32); iy = fy[ok].astype(np.int32)
            tx = fx[ok] - ix; ty = fy[ok] - iy
            v = (h[ix, iy] * (1 - tx) + h[ix + 1, iy] * tx) * (1 - ty) + (h[ix, iy + 1] * (1 - tx) + h[ix + 1, iy + 1] * tx) * ty
            out[ok] = np.minimum(out[ok], v - 0.00022)
        return out


def confine(X, ceil=None):
    """keep ink inside the water: below the surface, inside the glass wall, above the floor (in place)"""
    z = X[..., 2]
    if ceil is None:
        ceil = cm.WATER_Z - 0.00035
    np.minimum(z, ceil, out=z)
    np.maximum(z, cm.GLASS_BASE + 0.0006, out=z)
    rmax = (cm.GLASS_RB + (cm.GLASS_RT - cm.GLASS_RB) * (z / cm.GLASS_H) - cm.GLASS_WALL - 0.0009).astype(np.float32)
    r = np.sqrt(X[..., 0] ** 2 + X[..., 1] ** 2)
    sc = np.minimum(1.0, rmax / np.maximum(r, 1e-6)).astype(np.float32)
    X[..., 0] *= sc; X[..., 1] *= sc
    return X


# ------------------------------------------------------------------ plume
PU, PV = NU // 2, NV // 2      # the plume is simulated on a coarser control lattice


def _cr_matrix(n_out, n_in):
    # Catmull-Rom interpolation matrix (n_out x n_in), clamped ends
    W = np.zeros((n_out, n_in), np.float32)
    x = np.linspace(0, n_in - 1, n_out)
    for r, xv in enumerate(x):
        i = min(int(np.floor(xv)), n_in - 2); t = xv - i
        w = [(-t**3 + 2 * t**2 - t) / 2, (3 * t**3 - 5 * t**2 + 2) / 2, (-3 * t**3 + 4 * t**2 + t) / 2, (t**3 - t**2) / 2]
        for k, wk in zip((i - 1, i, i + 1, i + 2), w):
            W[r, min(max(k, 0), n_in - 1)] += wk
    return W


_WU = _cr_matrix(NU, PU); _WV = _cr_matrix(NV, PV)


def upsample(X):
    """(n, PU, PV, 3) -> (n, NU, NV, 3)"""
    return np.einsum("ai,bj,sijc->sabc", _WU, _WV, X, optimize=True).astype(np.float32)


class Plume:
    """Ink sheets injected by the drop, advected through a descending vortex ring that breaks into lobes."""
    N_POOL = 70

    def __init__(self, n_main, seed=21):
        rng = np.random.default_rng(seed)
        self.rng = rng
        self.n_main = n_main
        S = n_main + self.N_POOL
        self.S = S
        self.noise = fields.NoiseGrid(48, seed=5)
        self.surf = Surface()
        c0 = np.array([cm.DROP_XY[0], cm.DROP_XY[1], cm.WATER_Z - 0.0042])
        self.c0 = c0
        # ---- initial patches
        u = np.linspace(-0.5, 0.5, PU)[None, :, None]; v = np.linspace(-0.5, 0.5, PV)[None, None, :]
        # the drop is squashed into a thin lens lining the crater floor: mostly horizontal patches
        ang0 = rng.uniform(0, 2 * np.pi, S); rad = 3.1 * MM * np.sqrt(rng.random(S))
        ctr = np.stack([rad * np.cos(ang0), rad * np.sin(ang0), rng.normal(0, 0.28, S) * MM - 0.45 * MM + 0.35 * MM * (rad / (3.1 * MM)) ** 2], 1)
        nrm = np.stack([rng.normal(0, 0.22, S), rng.normal(0, 0.22, S), np.ones(S)], 1); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
        a1 = np.cross(nrm, rng.normal(0, 1, (S, 3))); a1 /= np.linalg.norm(a1, axis=1, keepdims=True)
        a2 = np.cross(nrm, a1)
        a3 = nrm
        Lu = rng.uniform(0.9, 1.9, S)[:, None, None] * MM; Lv = rng.uniform(1.5, 3.2, S)[:, None, None] * MM
        bend = rng.normal(0, 0.25, S)[:, None, None] * MM
        # 'wake' patches: upright sheets on the axis just behind the ring -> drawn out into the stem / bell veil
        wk = rng.random(S) < 0.32
        nw = int(wk.sum())
        aw = rng.uniform(0, 2 * np.pi, nw); rw = rng.uniform(0.0, 1.3, nw) * MM
        ctr[wk] = np.stack([rw * np.cos(aw), rw * np.sin(aw), rng.uniform(0.3, 1.6, nw) * MM], 1)
        hz = np.stack([np.cos(aw + rng.normal(0, 0.6, nw)), np.sin(aw + rng.normal(0, 0.6, nw)), rng.normal(0, 0.15, nw)], 1)
        hz /= np.linalg.norm(hz, axis=1, keepdims=True)
        a3[wk] = hz
        a2w = np.stack([rng.normal(0, 0.25, nw), rng.normal(0, 0.25, nw), np.ones(nw)], 1)
        a2w -= (a2w * hz).sum(1, keepdims=True) * hz; a2w /= np.linalg.norm(a2w, axis=1, keepdims=True)
        a2[wk] = a2w; a1[wk] = np.cross(a2w, hz)
        Lv[wk] = rng.uniform(2.2, 3.8, nw)[:, None, None] * MM
        X = (ctr[:, None, None, :] + c0
             + (u * Lu)[..., None] * a1[:, None, None, :] + (v * Lv)[..., None] * a2[:, None, None, :]
             + (bend * (4 * u * u + 4 * v * v))[..., None] * a3[:, None, None, :])
        # pool patches: flat-ish, just under the surface around the impact
        P = self.N_POOL
        ang = rng.uniform(0, 2 * np.pi, P); rr = rng.uniform(0.3, 3.2, P) * MM
        pc = np.stack([c0[0] + rr * np.cos(ang), c0[1] + rr * np.sin(ang), cm.WATER_Z - rng.uniform(0.5, 1.6, P) * MM], 1)
        b1 = np.stack([np.cos(ang), np.sin(ang), rng.normal(0, 0.25, P)], 1)
        b2 = np.stack([-np.sin(ang), np.cos(ang), rng.normal(0, 0.25, P)], 1)
        Lu2 = rng.uniform(1.5, 3.0, P)[:, None, None] * MM; Lv2 = rng.uniform(2.5, 5.0, P)[:, None, None] * MM
        X[n_main:] = pc[:, None, None, :] + (u * Lu2)[..., None] * b2[:, None, None, :] + (v * Lv2)[..., None] * b1[:, None, None, :]
        self.X0 = X.astype(np.float32)
        self.area0 = raster.cell_areas(upsample(self.X0)).astype(np.float32)
        # ---- vortex ring schedule
        self.U0 = 0.20; self.tau_u = 0.11; self.a0 = 3.0 * MM
        self.t_split = 0.85
        K = 5
        th = rng.uniform(0, 2 * np.pi) + np.arange(K) * 2 * np.pi / K + rng.normal(0, 0.18, K)
        self.sec_th = th
        self.sec_U = rng.uniform(0.050, 0.074, K)
        self.sec_tilt = rng.uniform(0.34, 0.62, K)
        self.sec_delay = rng.uniform(0.0, 0.25, K)

    # primary ring kinematics
    def prim(self, t):
        tt = max(t - T_START, 0.0)
        U = self.U0 / (1 + tt / self.tau_u)
        travel = self.U0 * self.tau_u * np.log(1 + tt / self.tau_u)
        if t > self.t_split:
            # decays after the break-up
            dts = t - self.t_split
            U = U * np.exp(-dts / 0.6)
            tr0 = self.U0 * self.tau_u * np.log(1 + (self.t_split - T_START) / self.tau_u)
            U_s = self.U0 / (1 + (self.t_split - T_START) / self.tau_u)
            travel = tr0 + U_s * 0.6 * (1 - np.exp(-dts / 0.6)) * 0.8
        a = self.a0 * (1 + tt / 0.06) ** 0.52
        c = self.c0 + np.array([0, 0, -travel])
        return c, a, U

    def sec(self, k, t):
        dts = t - self.t_split - self.sec_delay[k]
        if dts <= 0:
            return None
        cs, a_s, _ = self.prim(self.t_split + self.sec_delay[k])
        th = self.sec_th[k]
        m = np.array([self.sec_tilt[k] * np.cos(th), self.sec_tilt[k] * np.sin(th), -1.0]); m /= np.linalg.norm(m)
        start = cs + np.array([0.68 * a_s * np.cos(th), 0.68 * a_s * np.sin(th), -0.15 * a_s])
        U0 = self.sec_U[k]
        ramp = smoothstep(0.0, 0.25, dts)
        U = U0 * ramp / (1 + dts / 0.55)
        # travel = integral of U (numerical, cheap)
        ts = np.linspace(0, dts, 40)
        travel = np.trapezoid(U0 * smoothstep(0.0, 0.25, ts) / (1 + ts / 0.55), ts)
        a = 3.2 * MM * (1 + dts / 0.3) ** 0.50
        return start + m * travel, a, U, m

    def velocity(self, X, t):
        P = X.reshape(-1, 3)
        v = np.zeros_like(P)
        c, a, U = self.prim(t)
        dd = P - c.astype(np.float32)
        d2 = np.einsum("ij,ij->i", dd, dd)
        near = np.nonzero(d2 < np.float32((5.0 * a) ** 2))[0]
        if len(near):
            v[near] += fields.hill_vortex(P[near], c, a, U)
        for k in range(len(self.sec_th)):
            s = self.sec(k, t)
            if s is None: continue
            cs, a_s, Us, m = s
            dd = P - cs.astype(np.float32)
            d2 = np.einsum("ij,ij->i", dd, dd)
            near = np.nonzero(d2 < np.float32((5.0 * a_s) ** 2))[0]
            if len(near):
                v[near] += fields.hill_vortex(P[near], cs, a_s, Us, m)
        # turbulence (ramps in), drifting noise
        amp = 0.0088 * smoothstep(0.08, 0.5, t)
        if amp > 0:
            nz = self.noise.curl(P, 11 * MM, (0.13 * t, 0.07 * t, 0.21 * t)); nz *= np.float32(amp); v += nz
            nz = self.noise.curl(P, 4.5 * MM, (3.3 + 0.2 * t, 1.7, 5.1 - 0.15 * t)); nz *= np.float32(0.55 * amp); v += nz
        # surface film spreading + slow sinking streamers
        top = np.nonzero(P[:, 2] > np.float32(cm.WATER_Z - 0.004))[0]
        if len(top):
            Pt = P[top]
            depth = np.float32(cm.WATER_Z) - Pt[:, 2]
            rx = Pt[:, 0] - np.float32(self.c0[0]); ry = Pt[:, 1] - np.float32(self.c0[1])
            r = np.sqrt(rx * rx + ry * ry) + np.float32(1e-6)
            k = np.float32(0.016 * np.exp(-t / 0.45)) * np.exp(-depth / np.float32(0.002)) * (1 - np.exp(-r / np.float32(0.002))) / r
            v[top, 0] += k * rx; v[top, 1] += k * ry
            v[top, 2] -= np.float32(0.0012 * smoothstep(0.3, 1.5, t)) * (np.float32(0.5) + self.noise.scalar(Pt, 3 * MM, (1.1, 2.2, 0.05 * t)))
        return v.reshape(X.shape)

    def run(self, times, X, out, t_stop, log=None, tag=""):
        # advance lattice subset X (n, NU, NV, 3) from T_START, writing out[i] for every times[i] <= t_stop
        t = T_START
        t0 = time.time()
        for it, tt in enumerate(times):
            if tt > t_stop + 1e-9:
                break
            while t < tt - 1e-9:
                dt_max = 1 / 480 if t < 0.05 else (1 / 240 if t < 0.35 else (1 / 120 if t < 1.0 else 1 / 60))
                dt = min(dt_max, tt - t)
                k1 = self.velocity(X, t)
                k1 *= np.float32(0.5 * dt); k1 += X
                k2 = self.velocity(k1, t + 0.5 * dt)
                k2 *= np.float32(dt)
                X += k2
                t += dt
                ceil = self.surf.ceiling(X[..., 0], X[..., 1], t)
                confine(X, ceil)
            out[it] = quant(upsample(X))
            if log and (it % 25 == 0):
                log("plume%s snap %d/%d t=%.3f  (%.0fs)" % (tag, it, len(times), tt, time.time() - t0))
        return X


# ------------------------------------------------------------------ film state
class Film:
    def __init__(self, verbose=False):
        self.D = Dragon(cache_dir=CACHE, verbose=verbose)
        self.S = self.D.S
        self.noise = fields.NoiseGrid(48, seed=31)
        rng = np.random.default_rng(77)
        s = self.D.sheet_s
        self.rnd = rng.random(self.S).astype(np.float32)
        self._set_schedules(rng)
        self.perm = None
        self.plume_times = None

    def _set_schedules(self, rng):
        s = self.D.sheet_s
        head = self.D.frame > 0
        S = self.S
        # --- morph: tail (s=1) first, head last
        self.m_t0 = (T_M0 + 0.90 * (1.0 - s) + 0.15 * self.rnd).astype(np.float32)
        self.m_t0[head] = T_M0 + 0.90 + 0.15 * self.rnd[head]
        self.m_dur = 1.10
        self.m_lag = 0.25                       # tip lags behind the root
        self.m_swirl = (rng.normal(0.9, 0.35, S) * np.where(rng.random(S) < 0.85, 1.0, -0.6)).astype(np.float32)
        # --- dissolve: tail first, head last
        self.d_t0 = (T_D + 1.00 * (1.0 - s) + 0.25 * self.rnd).astype(np.float32)
        self.d_t0[head] = T_D + 1.10 + 0.40 * self.rnd[head]
        self.d_lag = 0.30                       # root lags behind the tip

    # ---------------------------------------------------------- data access
    def load_plume(self):
        fz = "_frozen" if os.environ.get("INK_POOL_FROZEN") else ""
        z = np.load(os.path.join(CACHE, "plume_meta%s.npz" % fz))
        self.plume_times = z["times"]; self.perm = z["perm"]; self.n_main_times = int(z["n_main_times"])
        self.plume_area0 = z["area0"]
        nm = self.S
        self.pm = None if fz else np.memmap(os.path.join(CACHE, "plume_main.i16"), np.int16, "r", shape=(self.n_main_times, nm, NU, NV, 3))
        self.pp = np.memmap(os.path.join(CACHE, "plume_pool%s.i16" % fz), np.int16, "r", shape=(len(self.plume_times), Plume.N_POOL, NU, NV, 3))
        if os.environ.get("INK_PERM_V1"):
            self.perm = np.load(os.path.join(CACHE, "plume_perm_v1.npy"))

    def load_dissolve(self):
        z = np.load(os.path.join(CACHE, "dissolve_meta%s.npz" % DIS_TAG))
        self.dis_times = z["times"]
        self.dm = np.memmap(os.path.join(CACHE, "dissolve%s.i16" % DIS_TAG), np.int16, "r", shape=(len(self.dis_times), self.S, NU, NV, 3))

    def _snap(self, times, t):
        i = int(np.argmin(np.abs(times - t)))
        return i

    # ---------------------------------------------------------- solids schedule
    def solid_params(self, t):
        """returns dict: body per-s scale fn params, head offset/dens, whisker grow, core boost"""
        p = {}
        if t < T_D:
            p["grow"] = float(smoothstep(T_M0 + 0.75, T_F - 0.25, t))
            p["shrink"] = None
            p["head_off"] = float(3.2 * MM * (1 - smoothstep(T_F - 0.95, T_F - 0.05, t)) ** 1.3)
            p["head_on"] = t > T_F - 0.95
            p["wh"] = float(smoothstep(T_F - 0.45, T_F + 0.25, t))
            p["wh_fade"] = 1.0
        else:
            p["grow"] = 1.0
            p["shrink"] = t
            p["head_off"] = float(4.5 * MM * smoothstep(T_D + 1.0, T_D + 2.0, t) ** 1.4)
            p["head_on"] = t < T_D + 2.0
            p["wh"] = 1.0
            p["wh_fade"] = float(1 - smoothstep(T_D + 0.9, T_D + 1.8, t))
        return p

    def body_scale(self, s, t):
        """radius scale along the body during the dissolve (tail first)"""
        tr = T_D + 1.00 * (1.0 - s) + 0.1
        return 1.0 - smoothstep(0.0, 0.55, t - tr)

    # ---------------------------------------------------------- lattices at time t
    def sheets(self, t):
        """-> (lattices (S,NU,NV,3) float32, mass (S,NU-1,NV-1) float32, extra pool lattices/mass or None)"""
        D = self.D
        age = D.age
        if t < T_M0:
            i = self._snap(self.plume_times, t)
            L = dequant(self.pm[i])[self.perm]
            mass = self.plume_mass * self._stretch_boost(L)
            self._spread = np.full(self.S, 0.00016 * np.sqrt(max(t, 0.0)), np.float32)
            return L, mass
        if t < T_F + 1e-6:
            i = min(self._snap(self.plume_times, t), self.n_main_times - 1)
            Lp = dequant(self.pm[i])[self.perm]
            sp = D.spine(t - T_F)
            Ld = D.sheet_lattices(t - T_F, sp)
            x = (t - self.m_t0[:, None] - self.m_lag * age[None, :]) / self.m_dur            # (S, NV)
            w = smoothstep(0.0, 1.0, x).astype(np.float32)
            wv = w[:, None, :, None]
            L = Lp + (Ld - Lp) * wv
            # swirl about the glass axis + turbulent wobble, both vanish at w=0 and w=1
            bump = (4 * w * (1 - w))[:, None, :]
            ang = self.m_swirl[:, None, None] * bump * 0.9
            ca = np.cos(ang); sa = np.sin(ang)
            x0 = L[..., 0].copy(); y0 = L[..., 1].copy()
            # rotate around the point's own target axis position (blend of plume/dragon radius keeps it inside the glass)
            L[..., 0] = x0 * ca - y0 * sa
            L[..., 1] = x0 * sa + y0 * ca
            nz = self.noise.curl(L, 9 * MM, (0.2 * t, 0.1 * t, 0.3 * t))
            L += (0.0028 * bump)[..., None] * nz
            confine(L)
            wm = smoothstep(0.0, 1.0, (t - self.m_t0 - 0.2) / (self.m_dur))[:, None, None].astype(np.float32)
            mass = self.plume_mass * self._stretch_boost(Lp) * (1 - wm) + D.cell_mass * wm
            self._spread = (0.00016 * np.sqrt(t) * (1 - wm[:, 0, 0])).astype(np.float32)
            return L, mass
        if t < T_D:
            sp = D.spine(t - T_F)
            return D.sheet_lattices(t - T_F, sp), D.cell_mass
        # dissolve
        i = self._snap(self.dis_times, t)
        L = dequant(self.dm[i])
        rel = t - self.d_t0                                                       # (S,)
        fade = (np.exp(-np.maximum(rel - 0.25, 0) / 1.15) * (1.0 - smoothstep(10.9, 12.42, t))).astype(np.float32)
        boost = 1.0 + (self.core_boost - 1.0) * smoothstep(-0.2, 0.5, rel)
        # diffusion: released ink is splatted with a growing random spread (softens clumps into smoke)
        self._spread = (0.00055 * np.sqrt(np.maximum(rel, 0.0))).astype(np.float32)
        return L, D.cell_mass * (fade * boost)[:, None, None].astype(np.float32)

    def _stretch_boost(self, L):
        """Stretched sheets collapse into threads rather than thinning uniformly: keep them visible
        (optical depth falls with sqrt of the stretch instead of linearly)."""
        A = raster.cell_areas(L)
        r = A / np.maximum(self.plume_a0p, 1e-14)
        return np.clip(np.sqrt(r), 1.0, 9.0).astype(np.float32)

    def pool(self, t):
        i = self._snap(self.plume_times, t)
        L = dequant(self.pp[i])
        fade = float(np.exp(-max(t - 2.0, 0) / 6.0) * (1.0 - smoothstep(10.4, 12.35, t)))
        return L, self.pool_mass * fade

    def prepare(self):
        """derived quantities once plume data exists"""
        self.load_plume()
        a0 = self.plume_area0
        TAU_P = 0.8
        self.plume_mass = (a0[:self.S][self.perm] * TAU_P).astype(np.float32)
        self.plume_a0p = a0[:self.S][self.perm].astype(np.float32)
        self.pool_mass = (a0[self.S:] * 1.2).astype(np.float32)
        cb = np.ones(self.S, np.float32)
        cb[self.D.kind == 5] = 1.3
        cb[self.D.frame > 0] = 1.2
        self.core_boost = cb
        try:
            self.load_dissolve()
        except Exception as e:
            self.dis_times = None

    # ---------------------------------------------------------- rasterise one sim time
    def raster(self, t, vox=0.2e-3, lo=None, hi=None, timer=None, haze=True):
        D = self.D
        T = timer or Timer()
        self._spread = None
        L, mass = self.sheets(t); T.tick("sheets")
        ilo = np.array([-0.0375, -0.0375, cm.GLASS_BASE]); ihi = np.array([0.0375, 0.0375, cm.WATER_Z + 0.0015])
        if lo is None:
            ok = mass.reshape(self.S, -1).max(1) > 0
            Lk = L[ok] if ok.any() else L
            pad = 0.004
            lo = np.maximum(ilo, np.floor((Lk.reshape(-1, 3).min(0) - pad) / (8 * vox)) * (8 * vox))
            hi = np.minimum(ihi, np.ceil((Lk.reshape(-1, 3).max(0) + pad) / (8 * vox)) * (8 * vox))
            hi[2] = ihi[2]                      # always include the surface pool
        g = raster.Grid(lo, hi, vox)
        spr = None if self._spread is None else np.repeat(self._spread, (NU - 1) * (NV - 1))
        g.add_cells(*raster.cells_from_lattice(L), mass.reshape(-1), cell_seed=np.arange(mass.size), tau_min=0.0012, spread=spr)
        Lp, mp = self.pool(t)
        g.add_cells(*raster.cells_from_lattice(Lp), mp.reshape(-1), cell_seed=np.arange(mp.size) + 7_000_000)
        sp = None
        par = self.solid_params(t)
        if t > T_M0 + 0.5:
            sp = D.spine(t - T_F)
            if par["wh"] > 0.01 and par["wh_fade"] > 0.01:
                Ww = D.whisker_lattices(t - T_F, sp, grow=par["wh"])
                confine(Ww)
                wm = (raster.cell_areas(Ww) * 8.0 * par["wh_fade"]).astype(np.float32)
                g.add_cells(*raster.cells_from_lattice(Ww), wm.reshape(-1), cell_seed=np.arange(wm.size) + 9_000_000)
            Lb, mb, sb = D.breath(t - T_F, sp)
            if Lb is not None:
                confine(Lb)
                g.add_cells(*raster.cells_from_lattice(Lb), mb.reshape(-1), cell_seed=np.arange(mb.size) + 11_000_000,
                            tau_min=0.002, spread=np.full(mb.size, sb, np.float32))
        T.tick("cells")
        g.flush_sheets(blur=1); T.tick("flush")
        if sp is not None:
            solid = np.zeros_like(g.rho)
            A, B, ra, rb = D.body_capsules(sp, grow=par["grow"])
            if par["shrink"] is not None and len(A):
                M = D.M
                # recompute per-capsule s from index order
                idx = np.arange(0, M - 1, 2)[:len(A)]
                s1 = idx / (M - 1); s2 = np.minimum(idx + 2, M - 1) / (M - 1)
                ra = ra * self.body_scale(s1, t).astype(np.float32); rb = rb * self.body_scale(s2, t).astype(np.float32)
            g.add_capsules(A, B, ra, rb, dens=1.0, out=solid)
            lg = par["grow"] if par["shrink"] is None else 1.0
            A, B, ra, rb = D.leg_capsules(sp, t - T_F, grow=lg)
            if par["shrink"] is not None and len(A):
                k = len(A) // 4
                sc = np.repeat(self.body_scale(np.array([0.185, 0.205, 0.555, 0.585]), t), k)[:len(A)].astype(np.float32)
                ra = ra * sc; rb = rb * sc
            g.add_capsules(A, B, ra, rb, dens=1.0, out=solid)
            if par["head_on"]:
                D.add_head(g, sp, offset=par["head_off"], out=solid)
            g.rho += solid
            del solid
        T.tick("solids")
        return g


def plume_times_for_frames(frames=None):
    t = ALL_T if frames is None else frame_time(np.asarray(frames))
    t = np.unique(np.round(t[t >= T_START], 6))
    return t


# ------------------------------------------------------------------ dissolve
class Dissolve:
    """Released sheets drift in a decaying turbulent field; unreleased points keep following the animated dragon."""
    def __init__(self, film):
        self.film = film
        self.noise = fields.NoiseGrid(48, seed=91)

    def velocity(self, X, t):
        P = X.reshape(-1, 3)
        k = 1.0 / (1.0 + 0.18 * max(t - T_D, 0))
        v = self.noise.curl(P, 10 * MM, (0.10 * t, 0.06 * t, 0.14 * t)); v *= np.float32(0.0100 * k)
        n2 = self.noise.curl(P, 3.4 * MM, (2.1 + 0.16 * t, 4.4, 1.3 - 0.12 * t)); n2 *= np.float32(0.0072 * k); v += n2
        om = np.float32(0.32 * np.exp(-(t - T_D) / 2.2))
        v[:, 0] -= om * P[:, 1]; v[:, 1] += om * P[:, 0]
        v[:, 2] -= np.float32(0.0011)
        return v.reshape(X.shape)

    def run(self, times, out, sl=slice(None), log=None):
        F = self.film; D = F.D
        age = D.age
        t = T_D
        X = D.sheet_lattices(t - T_F, D.spine(t - T_F), sl).copy()
        rel_t = (F.d_t0[sl, None] + F.d_lag * (1 - age)[None, :]).astype(np.float32)      # (S, NV) release time per row
        t_all = float(F.d_t0.max() + F.d_lag) + 0.05
        t0 = time.time()
        for it, tt in enumerate(times):
            while t < tt - 1e-9:
                dt = min(1 / 30, tt - t)
                v = self.velocity(X, t)
                tr = t - rel_t
                ramp = (smoothstep(0.0, 0.35, tr) * (1.0 + 2.2 * np.exp(-np.maximum(tr, 0) / 0.7)))[:, None, :, None].astype(np.float32)
                v *= ramp * np.float32(dt)
                v += X
                t += dt
                if t < t_all:
                    Ld = D.sheet_lattices(t - T_F, D.spine(t - T_F), sl)
                    free = (t > rel_t)[:, None, :, None]
                    X = np.where(free, v, Ld)
                else:
                    X = v
                confine(X)
            out[it] = quant(X)
            if log and it % 20 == 0:
                log("dissolve snap %d/%d t=%.3f (%.0fs)" % (it, len(times), tt, time.time() - t0))
