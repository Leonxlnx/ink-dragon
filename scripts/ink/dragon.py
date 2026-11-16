"""Procedural ink dragon: animated spine, SDF solids (body, legs, claws, head, horns, teeth) and
wisp sheets (mane, flank tufts, tail brush, whiskers) defined in body space and mapped to world.
Units: meters. tl = 'life time' of the dragon in seconds (0 at fully formed)."""
import os
import numpy as np
from .util import normalize, smoothstep
from .fields import NoiseGrid
from . import raster

MM = 1e-3
NU, NV = 20, 72          # lattice size of every sheet (across, along)


def catmull_rom(P, n=8):
    P = np.asarray(P, np.float64)
    Pm = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    t = np.linspace(0, 1, n, endpoint=False)[:, None]
    for i in range(len(P) - 1):
        p0, p1, p2, p3 = Pm[i], Pm[i + 1], Pm[i + 2], Pm[i + 3]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-1:])
    return np.vstack(out)


def resample(poly, M):
    seg = np.linalg.norm(np.diff(poly, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    L = s[-1]
    si = np.linspace(0, L, M)
    out = np.stack([np.interp(si, s, poly[:, k]) for k in range(3)], 1)
    return out, L


R_TAB_S = np.array([0.0, 0.05, 0.14, 0.30, 0.50, 0.68, 0.82, 0.93, 1.0])
R_TAB_R = np.array([3.3, 3.6, 4.2, 4.0, 3.45, 2.6, 1.7, 0.8, 0.15]) * MM
HEAD_SCALE = 1.14
LEG_SCALE = 1.25


def body_radius(s):
    return np.interp(np.clip(s, 0, 1), R_TAB_S, R_TAB_R)


def rot_axis(axis, ang):
    axis = axis / np.linalg.norm(axis)
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(ang) * K + (1 - np.cos(ang)) * (K @ K)


class SdfBox:
    """Dense local SDF builder (meters)."""
    def __init__(self, lo, hi, vox):
        self.lo = np.asarray(lo, np.float64); self.vox = vox
        self.n = np.round((np.asarray(hi) - self.lo) / vox).astype(int)
        self.d = np.full(tuple(self.n), 0.02, np.float32)
        self.ax = [(self.lo[i] + (np.arange(self.n[i]) + 0.5) * vox).astype(np.float32) for i in range(3)]

    def _sub(self, lo, hi):
        i0 = np.maximum(np.floor((np.asarray(lo) - self.lo) / self.vox).astype(int), 0)
        i1 = np.minimum(np.ceil((np.asarray(hi) - self.lo) / self.vox).astype(int) + 1, self.n)
        if np.any(i1 <= i0): return None
        sl = tuple(slice(int(a), int(b)) for a, b in zip(i0, i1))
        return sl, self.ax[0][sl[0]][:, None, None], self.ax[1][sl[1]][None, :, None], self.ax[2][sl[2]][None, None, :]

    def _combine(self, sl, d, k, sub):
        cur = self.d[sl]
        if sub:
            self.d[sl] = np.maximum(cur, -d)
        elif k <= 0:
            self.d[sl] = np.minimum(cur, d)
        else:
            h = np.clip(0.5 + 0.5 * (d - cur) / k, 0, 1)
            self.d[sl] = d + (cur - d) * h - k * h * (1 - h)

    def capsule(self, a, b, ra, rb, k=0.0, scale=(1, 1, 1), sub=False):
        a = np.asarray(a, np.float64); b = np.asarray(b, np.float64); sc = np.asarray(scale, np.float64)
        pad = max(ra, rb) * max(1.0, 1.0 / sc.min()) + 3 * k + 3 * self.vox
        s = self._sub(np.minimum(a, b) - pad, np.maximum(a, b) + pad)
        if s is None: return
        sl, x, y, z = s
        ba = (b - a) / sc; l2 = float(ba @ ba) + 1e-20
        pax = (x - np.float32(a[0])) / np.float32(sc[0]); pay = (y - np.float32(a[1])) / np.float32(sc[1]); paz = (z - np.float32(a[2])) / np.float32(sc[2])
        h = np.clip((pax * ba[0] + pay * ba[1] + paz * ba[2]) / l2, 0, 1).astype(np.float32)
        d = np.sqrt((pax - np.float32(ba[0]) * h) ** 2 + (pay - np.float32(ba[1]) * h) ** 2 + (paz - np.float32(ba[2]) * h) ** 2) - (ra + (rb - ra) * h)
        d = d * np.float32(sc.min())
        self._combine(sl, d.astype(np.float32), k, sub)

    def ellipsoid(self, c, r, k=0.0, sub=False):
        c = np.asarray(c, np.float64); r = np.asarray(r, np.float64)
        pad = 3 * k + 3 * self.vox
        s = self._sub(c - r - pad, c + r + pad)
        if s is None: return
        sl, x, y, z = s
        px = x - np.float32(c[0]); py = y - np.float32(c[1]); pz = z - np.float32(c[2])
        k0 = np.sqrt((px / r[0]) ** 2 + (py / r[1]) ** 2 + (pz / r[2]) ** 2)
        k1 = np.sqrt((px / r[0] ** 2) ** 2 + (py / r[1] ** 2) ** 2 + (pz / r[2] ** 2) ** 2) + 1e-9
        d = np.where(k0 < 1e-4, -r.min(), k0 * (k0 - 1.0) / k1)
        self._combine(sl, d.astype(np.float32), k, sub)

    def chain(self, pts, radii, k=0.0):
        for i in range(len(pts) - 1):
            self.capsule(pts[i], pts[i + 1], radii[i], radii[i + 1], k)


class Dragon:
    M = 360

    def __init__(self, seed=5, cache_dir=None, verbose=False):
        self.rng = np.random.default_rng(seed)
        self.noise = NoiseGrid(48, seed=11)
        self.cache_dir = cache_dir
        sp = self.spine(0.0)
        self.L = sp["L"]
        self._build_head_sdf()
        self._build_wisps()
        self._build_breath()
        # reference configuration for mass (tl = 0)
        Lw = self.sheet_lattices(0.0, sp)
        self.cell_mass = (raster.cell_areas(Lw) * self.tau_cells).astype(np.float32)
        if verbose:
            print("dragon: L=%.1f mm, sheets=%d, ctrl pts=%d" % (self.L * 1e3, self.S, self.S * NU * NV))

    # ------------------------------------------------------------------ spine
    def spine(self, tl):
        K = 110
        p = np.linspace(0, 1, K)
        turns = 1.55
        th0 = np.radians(-100.0) - 0.15 * (tl - 1.5)
        th = th0 - 2 * np.pi * turns * p - 2 * np.pi * 0.22 * smoothstep(0.82, 1.0, p) ** 1.5
        rho = 0.0080 + 0.0105 * smoothstep(0.0, 0.17, p)
        rho = rho - 0.0025 * smoothstep(0.40, 0.80, p)
        rho = rho * (1 - 0.30 * smoothstep(0.86, 1.0, p))
        # neck dives steeply right behind the skull, then the helix levels out
        gz = 0.085 * (1 - np.exp(-p / 0.035)) + 0.915 * (0.18 * p + 0.82 * p ** 1.7)
        z = 0.0975 - 0.0745 * gz + 0.0060 * smoothstep(0.88, 1.0, p)
        # undulation (travels toward the tail)
        A = (0.35 + 4.0 * p) * MM
        rho = rho + A * np.sin(2 * np.pi * (2.4 * p - 0.80 * tl))
        z = z + 0.65 * A * np.sin(2 * np.pi * (2.0 * p - 0.66 * tl) + 0.9)
        ctrl = np.stack([rho * np.cos(th), rho * np.sin(th), z], 1)
        dense = catmull_rom(ctrl, 6)
        C, L = resample(dense, self.M)
        T = normalize(np.gradient(C, axis=0))
        s = np.linspace(0, 1, self.M)
        radial = normalize(np.stack([C[:, 0], C[:, 1], np.zeros(self.M)], 1))
        wa = 0.20 + 0.55 * smoothstep(0.02, 0.22, s)
        ref = normalize(wa[:, None] * radial + np.sqrt(1 - wa ** 2)[:, None] * np.array([0, 0, 1.0]))
        N = normalize(ref - (ref * T).sum(1, keepdims=True) * T)
        B = np.cross(T, N)
        # head frame: heading = horizontal direction the neck arrives from, mild upward pitch
        hd = -T[0].copy(); hd[2] = 0; hd = hd / np.linalg.norm(hd)
        pitch0 = np.radians(13.0)
        xh = hd * np.cos(pitch0) + np.array([0, 0, 1.0]) * np.sin(pitch0)
        zh = np.array([0, 0, 1.0]) - xh[2] * xh; zh /= np.linalg.norm(zh)
        yh = np.cross(zh, xh)
        Rh = np.stack([xh, yh, zh], 1)          # columns = head local axes in world
        yaw = np.radians(8.0) * np.sin(2 * np.pi * 0.33 * tl + 0.4)
        pitch = np.radians(-6.0) * np.sin(2 * np.pi * 0.27 * tl + 1.3)
        Rh = Rh @ rot_axis(np.array([0, 0, 1.0]), yaw) @ rot_axis(np.array([0, 1.0, 0]), pitch)
        jaw = np.radians(12 + 23 * smoothstep(0.08, 0.50, tl) - 13 * smoothstep(1.25, 2.4, tl) + 1.8 * np.sin(2 * np.pi * 1.3 * tl) * smoothstep(0.4, 0.8, tl))
        return dict(C=C.astype(np.float32), T=T.astype(np.float32), N=N.astype(np.float32), B=B.astype(np.float32),
                    L=float(L), Rh=Rh, oh=C[0].copy(), jaw=float(jaw))

    def body_to_world(self, Q, sp):
        """Q (...,3): body-space (u meters from head toward tail, v along dorsal N, w along B)."""
        M = self.M
        f = Q[..., 0] / np.float32(sp["L"]) * (M - 1)
        i0 = np.clip(np.floor(f).astype(np.int32), 0, M - 2)
        fr = (f - i0).astype(np.float32)
        frc = np.clip(fr, 0, 1)[..., None]
        C = sp["C"]; N = sp["N"]; B = sp["B"]
        c = C[i0] + (C[i0 + 1] - C[i0]) * fr[..., None]
        n = N[i0] + (N[i0 + 1] - N[i0]) * frc
        b = B[i0] + (B[i0 + 1] - B[i0]) * frc
        return c + Q[..., 1:2] * n + Q[..., 2:3] * b

    # ------------------------------------------------------------------ solids
    def body_capsules(self, sp, grow=1.0, core=0.74):
        """grow: 0..1 body formation (tail first -> head)."""
        C = sp["C"]; M = self.M
        idx = np.arange(0, M - 1, 2)
        s = idx / (M - 1); s2 = np.minimum(idx + 2, M - 1) / (M - 1)
        g = self._grow_profile(s, grow); g2 = self._grow_profile(s2, grow)
        mod = lambda q: 1.0 + 0.10 * np.sin(q * 61.0 + 0.7) + 0.07 * np.sin(q * 137.0 + 2.1)
        ra = body_radius(s) * core * g * mod(s); rb = body_radius(s2) * core * g2 * mod(s2)
        A = C[idx]; Bp = C[np.minimum(idx + 2, M - 1)]
        keep = (ra > 0.03 * MM) | (rb > 0.03 * MM)
        return A[keep], Bp[keep], ra[keep].astype(np.float32), rb[keep].astype(np.float32)

    @staticmethod
    def _grow_profile(s, grow):
        # front of growth travels from tail (s=1) to head (s=0)
        return smoothstep(0.0, 1.0, (grow * 1.25 - (1 - s)) / 0.25)

    def leg_capsules(self, sp, tl, grow=1.0):
        C, T, N, B = sp["C"], sp["T"], sp["N"], sp["B"]
        A = []; Bb = []; ra = []; rb = []
        def cap(a, b, r0, r1):
            A.append(a); Bb.append(b); ra.append(r0); rb.append(r1)
        legs = [(0.185, +1, 0.0), (0.205, -1, 1.7), (0.555, +1, 3.1), (0.585, -1, 4.6)]
        for s0, side, ph in legs:
            g = float(self._grow_profile(np.array(s0), grow))
            if g <= 0.02: continue
            g *= LEG_SCALE
            i = int(s0 * (self.M - 1))
            c, t, n, b = C[i].astype(np.float64), T[i].astype(np.float64), N[i].astype(np.float64), B[i].astype(np.float64)
            R = float(body_radius(s0))
            sw = 0.38 * np.sin(2 * np.pi * 0.60 * tl + ph)
            root = c + (-0.30 * n + side * 0.70 * b) * R
            d1 = normalize(side * 0.80 * b - 0.50 * n - (0.25 + sw) * t)
            elbow = root + d1 * 6.2 * MM * g
            d2 = normalize(-(0.85 + sw) * t - 0.30 * n + side * 0.30 * b)
            wrist = elbow + d2 * 5.6 * MM * g
            cap(root, elbow, 1.45 * MM * g, 1.10 * MM * g)
            cap(elbow, wrist, 1.05 * MM * g, 0.80 * MM * g)
            f = d2; sa = normalize(np.cross(n, f)); up = np.cross(f, sa)
            cap(wrist, wrist + f * 0.8 * MM * g, 1.10 * MM * g, 1.0 * MM * g)
            for ang, ln in ((-34, 1.0), (-11, 1.12), (12, 1.12), (35, 1.0)):
                a_ = np.radians(ang)
                d = f * np.cos(a_) + sa * np.sin(a_)
                p0 = wrist + d * 0.6 * MM * g
                p1 = p0 + (d * 2.0 + up * 0.25) * MM * g * ln
                p2 = p1 + (d * 1.5 - up * 0.9) * MM * g * ln
                p3 = p2 + (d * 0.7 - up * 1.25) * MM * g * ln
                cap(p0, p1, 0.52 * MM * g, 0.44 * MM * g)
                cap(p1, p2, 0.44 * MM * g, 0.27 * MM * g)
                cap(p2, p3, 0.27 * MM * g, 0.04 * MM * g)
            p0 = wrist - f * 0.3 * MM * g
            p1 = p0 + (-f * 0.9 - up * 1.3 + sa * side * 0.3) * MM * g
            cap(p0, p1, 0.40 * MM * g, 0.05 * MM * g)
        if not A:
            return np.zeros((0, 3), np.float32), np.zeros((0, 3), np.float32), np.zeros(0, np.float32), np.zeros(0, np.float32)
        return np.array(A, np.float32), np.array(Bb, np.float32), np.array(ra, np.float32), np.array(rb, np.float32)

    # ------------------------------------------------------------------ head SDF
    def _build_head_sdf(self):
        ver = "head_v5"
        f = os.path.join(self.cache_dir, ver + ".npz") if self.cache_dir else None
        if f and os.path.exists(f):
            z = np.load(f)
            self.head_sdf, self.head_lo, self.head_vox = z["head"], z["head_lo"], float(z["vox"])
            self.jaw_sdf, self.jaw_lo = z["jaw"], z["jaw_lo"]
            self._erosion_noise()
            return
        vox = 0.10 * MM
        hb = SdfBox(np.array([-21, -12.5, -8.5]) * MM, np.array([27, 12.5, 25.0]) * MM, vox)
        m = MM
        k = 1.1 * m
        hb.ellipsoid(np.array([5.5, 0, 1.0]) * m, np.array([6.6, 5.0, 4.6]) * m)
        for sy in (-1, 1):
            hb.ellipsoid(np.array([5.0, 3.1 * sy, -1.0]) * m, np.array([4.2, 2.5, 3.0]) * m, k)
        hb.capsule(np.array([9.0, 0, 0.7]) * m, np.array([20.8, 0, 0.1]) * m, 3.7 * m, 2.6 * m, k, scale=(1, 1, 0.78))
        hb.ellipsoid(np.array([22.3, 0, 0.5]) * m, np.array([2.5, 2.6, 2.1]) * m, 0.8 * m)
        for sy in (-1, 1):
            hb.ellipsoid(np.array([23.3, 1.35 * sy, 1.5]) * m, np.array([1.25, 1.1, 1.0]) * m, 0.5 * m)      # nostril bumps
            hb.capsule(np.array([7.6, 2.7 * sy, 3.9]) * m, np.array([13.8, 2.35 * sy, 3.1]) * m, 1.55 * m, 0.95 * m, 0.7 * m)  # brow
            hb.ellipsoid(np.array([0.6, 5.5 * sy, 0.8]) * m, np.array([4.0, 0.75, 2.4]) * m, 0.5 * m)        # ear fin
        hb.capsule(np.array([2.5, 0, 4.7]) * m, np.array([12.0, 0, 3.4]) * m, 1.3 * m, 0.9 * m, 0.8 * m)    # crest
        hb.capsule(np.array([10.5, 0, -3.6]) * m, np.array([22.5, 0, -3.1]) * m, 2.1 * m, 1.6 * m, 0, scale=(1, 1.6, 0.6), sub=True)
        # eye tunnel (see-through 'glowing' almond eye)
        hb.capsule(np.array([11.4, -8, 1.9]) * m, np.array([11.4, 8, 1.9]) * m, 0.80 * m, 0.80 * m, 0, scale=(2.0, 1, 1), sub=True)
        for sy in (-1, 1):
            hb.capsule(np.array([23.6, 1.3 * sy, 1.6]) * m, np.array([25.5, 2.2 * sy, 2.0]) * m, 0.42 * m, 0.42 * m, 0, sub=True)
        # upper teeth
        for sy in (-1, 1):
            for i, x in enumerate(np.linspace(11.5, 21.3, 8)):
                y = (2.55 - 0.75 * i / 7) * sy
                ln = (1.5 + 0.5 * np.sin(i * 1.9) ** 2) * m
                if i == 6: ln = 3.3 * m
                hb.capsule(np.array([x, y, -1.5]) * m, np.array([x + 0.25, y, -1.5]) * m - np.array([0, 0, ln]), 0.48 * m, 0.03 * m)
        # horns (antlers)
        for sy in (-1, 1):
            main = np.array([[2.5, 2.6 * sy, 4.0], [-1.6, 4.0 * sy, 9.0], [-6.0, 5.2 * sy, 13.4], [-11.2, 5.8 * sy, 16.8], [-16.0, 5.0 * sy, 21.2]]) * m
            hb.chain(catmull_rom(main, 4), np.interp(np.linspace(0, 1, 17), [0, 0.3, 0.6, 0.85, 1], [1.25, 1.0, 0.8, 0.5, 0.10]) * m, 0.3 * m)
            t1 = np.array([[-6.0, 5.2 * sy, 13.4], [-5.6, 6.9 * sy, 17.6], [-3.6, 7.6 * sy, 21.2]]) * m
            hb.chain(catmull_rom(t1, 4), np.linspace(0.62, 0.07, 9) * m, 0.3 * m)
            t2 = np.array([[-1.6, 4.0 * sy, 9.0], [1.8, 5.4 * sy, 12.0], [4.6, 5.8 * sy, 15.2]]) * m
            hb.chain(catmull_rom(t2, 4), np.linspace(0.58, 0.07, 9) * m, 0.3 * m)
            t3 = np.array([[-11.2, 5.8 * sy, 16.8], [-14.6, 7.4 * sy, 18.4], [-18.0, 8.0 * sy, 19.4]]) * m
            hb.chain(catmull_rom(t3, 4), np.linspace(0.42, 0.06, 9) * m, 0.2 * m)
        self._roughen(hb)
        # lower jaw (jaw-local: x forward from the hinge, z up)
        jb = SdfBox(np.array([-3.5, -5.5, -5.0]) * MM, np.array([18.5, 5.5, 5.5]) * MM, vox)
        jb.capsule(np.array([0, 0, -0.6]) * m, np.array([14.3, 0, -0.2]) * m, 2.5 * m, 1.55 * m, 0, scale=(1, 1.25, 0.62))
        jb.ellipsoid(np.array([14.8, 0, -0.4]) * m, np.array([1.7, 1.9, 1.2]) * m, 0.6 * m)
        for sy in (-1, 1):
            for i, x in enumerate(np.linspace(4.5, 14.0, 7)):
                y = (2.35 - 0.95 * i / 6) * sy
                ln = (1.4 + 0.5 * np.cos(i * 2.3) ** 2) * m
                if i == 5: ln = 2.9 * m
                jb.capsule(np.array([x, y, 0.3]) * m, np.array([x + 0.2, y, 0.3]) * m + np.array([0, 0, ln]), 0.45 * m, 0.03 * m)
        tg = np.array([[1.0, 0, 0.9], [5.5, 0, 1.5], [10.0, 0, 1.3], [13.2, 0, 2.3]]) * m
        jb.chain(catmull_rom(tg, 4), np.linspace(1.0, 0.25, 13) * m, 0.4 * m)
        self._roughen(jb)
        self.head_sdf, self.head_lo, self.head_vox = hb.d, hb.lo, vox
        self.jaw_sdf, self.jaw_lo = jb.d, jb.lo
        if f:
            np.savez_compressed(f, head=hb.d, head_lo=hb.lo, vox=vox, jaw=jb.d, jaw_lo=jb.lo)
        self._erosion_noise()

    def _erosion_noise(self):
        # smooth 0..1 noise on the head / jaw SDF lattices: makes growth and erosion organic
        f = os.path.join(self.cache_dir, "head_noise_v1.npz") if self.cache_dir else None
        if f and os.path.exists(f):
            z = np.load(f); self.head_noise, self.jaw_noise = z["head"], z["jaw"]
            if self.head_noise.shape == self.head_sdf.shape and self.jaw_noise.shape == self.jaw_sdf.shape:
                return
        outs = []
        for sdf, lo in ((self.head_sdf, self.head_lo), (self.jaw_sdf, self.jaw_lo)):
            n = sdf.shape; vox = self.head_vox
            ax = [(lo[i] + (np.arange(n[i]) + 0.5) * vox).astype(np.float32) for i in range(3)]
            out = np.zeros(n, np.float32)
            for i0 in range(0, n[0], 64):
                sl = slice(i0, min(i0 + 64, n[0]))
                X = np.broadcast_to(ax[0][sl][:, None, None], (sl.stop - sl.start, n[1], n[2]))
                Y = np.broadcast_to(ax[1][None, :, None], X.shape); Z = np.broadcast_to(ax[2][None, None, :], X.shape)
                P = np.stack([X, Y, Z], -1)
                out[sl] = self.noise.scalar(P, 3.6 * MM, (2.2, 8.1, 5.5)) + 0.5 * self.noise.scalar(P, 1.5 * MM, (9.4, 0.3, 3.8))
            out = np.clip(0.5 + 0.33 * out, 0, 1).astype(np.float16)
            outs.append(out)
        self.head_noise, self.jaw_noise = outs
        if f:
            np.savez_compressed(f, head=outs[0], jaw=outs[1])

    def _roughen(self, box):
        n = box.n
        for i0 in range(0, n[0], 64):
            sl = slice(i0, min(i0 + 64, n[0]))
            X = np.broadcast_to(box.ax[0][sl][:, None, None], (sl.stop - sl.start, n[1], n[2]))
            Y = np.broadcast_to(box.ax[1][None, :, None], X.shape); Z = np.broadcast_to(box.ax[2][None, None, :], X.shape)
            P = np.stack([X, Y, Z], -1)
            box.d[sl] += (0.10 * MM) * self.noise.scalar(P, 0.9 * MM) + (0.16 * MM) * self.noise.scalar(P, 3.0 * MM, (7.3, 1.1, 4.4))

    JAW_HINGE = np.array([6.0, 0.0, -2.9]) * MM

    def add_head(self, grid, sp, offset=0.0, dens=1.0, out=None):
        Rh = sp["Rh"]; oh = sp["oh"].astype(np.float64)
        grid.add_sdf_volume(self.head_sdf, self.head_lo, self.head_vox, Rh, oh, dens=dens, offset=offset, out=out, noise=self.head_noise, scale=HEAD_SCALE)
        Rj = Rh @ rot_axis(np.array([0, 1.0, 0]), sp["jaw"])
        oj = oh + Rh @ (self.JAW_HINGE * HEAD_SCALE)
        grid.add_sdf_volume(self.jaw_sdf, self.jaw_lo, self.head_vox, Rj, oj, dens=dens, offset=offset, out=out, noise=self.jaw_noise, scale=HEAD_SCALE)

    # ------------------------------------------------------------------ wisps
    def _build_wisps(self):
        rng = self.rng; L = self.L
        keys = ("u0", "phic", "dphi", "r0", "length", "alpha", "hook", "namp", "tau", "conv", "swirl", "kind", "wave", "frame", "fing")
        cols = {k: [] for k in keys}
        def add(n, **kw):
            for k in keys:
                cols[k].append(np.broadcast_to(np.asarray(kw[k], np.float64), (n,)).copy())
        U = lambda a, b, n: rng.uniform(a, b, n)
        LN = lambda med, sig, n: med * np.exp(rng.normal(0, sig, n))
        sgn = lambda n, pp=0.7: np.where(rng.random(n) < pp, 1.0, -1.0)
        # (a) dorsal flame tufts along the body, clustered into clumps
        n = 300
        centers = np.sort(U(0.05, 0.93, 24))
        s = np.clip(rng.choice(centers, n) + rng.normal(0, 0.012, n), 0.03, 0.96)
        Rb = body_radius(s)
        add(n, u0=s * L, phic=rng.normal(0, 0.38, n), dphi=U(0.5, 1.15, n), r0=Rb * U(0.5, 0.9, n),
            length=np.clip(LN(13.0, 0.45, n), 6, 40) * MM * (1.15 - 0.5 * s), alpha=np.radians(U(30, 66, n)),
            hook=U(1.0, 5.5, n) * sgn(n), namp=U(0.25, 0.6, n), tau=U(0.85, 1.5, n), conv=U(1.2, 2.6, n),
            swirl=rng.normal(0, 0.15, n), kind=0, wave=U(0.6, 1.5, n), frame=0, fing=rng.integers(1, 4, n))
        # (b) flank / belly feathering (short, hugging the body)
        n = 260
        s = U(0.02, 0.97, n); Rb = body_radius(s)
        add(n, u0=s * L, phic=U(0.9, 2 * np.pi - 0.9, n), dphi=U(0.6, 1.4, n), r0=Rb * U(0.55, 0.92, n),
            length=np.clip(LN(5.6, 0.35, n), 3, 13) * MM, alpha=np.radians(U(12, 42, n)),
            hook=U(0.5, 4.0, n) * sgn(n), namp=U(0.2, 0.5, n), tau=U(0.5, 0.95, n), conv=U(1.0, 2.2, n),
            swirl=rng.normal(0, 0.25, n), kind=1, wave=U(0.4, 1.0, n), frame=0, fing=rng.integers(1, 3, n))
        # (c) neck mane (long flowing hair down the neck)
        n = 120
        u0 = U(-1.0, 16.0, n) * MM
        add(n, u0=u0, phic=rng.normal(0, 1.0, n), dphi=U(0.35, 0.8, n), r0=body_radius(u0 / L) * U(0.7, 1.1, n),
            length=np.clip(LN(15.5, 0.38, n), 8, 36) * MM, alpha=np.radians(U(12, 38, n)),
            hook=U(0.5, 3.4, n) * sgn(n), namp=U(0.3, 0.65, n), tau=U(0.45, 0.9, n), conv=U(1.4, 2.6, n),
            swirl=rng.normal(0, 0.2, n), kind=2, wave=U(0.8, 1.8, n), frame=0, fing=rng.integers(1, 4, n))
        # (d) head-frame tufts: beard, cheek fins, crest (u = -x_head, v = up, w = left)
        n = 60
        add(n, u0=U(-18.0, -7.0, n) * MM, phic=np.pi + rng.normal(0, 0.30, n), dphi=U(0.3, 0.6, n), r0=U(4.4, 6.0, n) * MM,
            length=np.clip(LN(9.5, 0.3, n), 5, 18) * MM, alpha=np.radians(U(40, 75, n)),
            hook=U(0.5, 3.2, n), namp=U(0.3, 0.6, n), tau=U(0.6, 1.0, n), conv=U(1.6, 2.8, n),
            swirl=rng.normal(0, 0.2, n), kind=3, wave=U(0.8, 1.6, n), frame=1, fing=rng.integers(1, 3, n))
        n = 70
        side = sgn(n, 0.5)
        add(n, u0=U(-7.0, -0.5, n) * MM, phic=side * U(1.0, 2.3, n), dphi=U(0.3, 0.7, n), r0=U(4.0, 5.2, n) * MM,
            length=np.clip(LN(11.0, 0.3, n), 6, 20) * MM, alpha=np.radians(U(15, 40, n)),
            hook=U(0.5, 3.0, n) * sgn(n), namp=U(0.3, 0.6, n), tau=U(0.55, 0.95, n), conv=U(1.6, 2.8, n),
            swirl=rng.normal(0, 0.2, n), kind=3, wave=U(0.8, 1.6, n), frame=1, fing=rng.integers(1, 3, n))
        n = 30
        add(n, u0=U(-12.0, -3.0, n) * MM, phic=rng.normal(0, 0.35, n), dphi=U(0.3, 0.6, n), r0=U(3.6, 4.4, n) * MM,
            length=np.clip(LN(6.5, 0.3, n), 4, 12) * MM, alpha=np.radians(U(15, 40, n)),
            hook=U(0.5, 3.0, n), namp=U(0.25, 0.5, n), tau=U(0.5, 0.9, n), conv=U(1.6, 2.8, n),
            swirl=rng.normal(0, 0.2, n), kind=3, wave=U(0.6, 1.2, n), frame=1, fing=1)
        # (e) tail brush: long flames streaming off the last fifth of the tail
        n = 120
        s = U(0.80, 0.995, n)
        add(n, u0=s * L, phic=U(0, 2 * np.pi, n), dphi=U(0.6, 1.6, n), r0=body_radius(s) * U(0.3, 0.9, n),
            length=np.clip(LN(20.0, 0.4, n), 10, 42) * MM, alpha=np.radians(U(6, 30, n)),
            hook=U(1.0, 4.5, n) * sgn(n, 0.5), namp=U(0.35, 0.7, n), tau=U(0.75, 1.3, n), conv=U(1.0, 2.2, n),
            swirl=rng.normal(0, 0.3, n), kind=4, wave=U(1.0, 2.0, n), frame=0, fing=rng.integers(1, 4, n))
        # (f) core wraps (inside the body: streak texture + mass for the morphs)
        n = 200
        s = U(0.0, 0.93, n); Rb = body_radius(s)
        add(n, u0=s * L, phic=U(0, 2 * np.pi, n), dphi=U(3.5, 7.5, n), r0=Rb * U(0.30, 0.80, n),
            length=U(10, 18, n) * MM, alpha=np.radians(U(0, 6, n)), hook=0.0, namp=U(0.05, 0.15, n), tau=U(1.0, 1.8, n),
            conv=0.0, swirl=rng.normal(0, 0.9, n), kind=5, wave=0.15, frame=0, fing=1)
        # (g) big faint veils (smoke shed by the body)
        n = 44
        s = U(0.03, 0.97, n); Rb = body_radius(s)
        add(n, u0=s * L, phic=rng.normal(0, 1.0, n), dphi=U(0.8, 1.7, n), r0=Rb * U(0.6, 1.0, n),
            length=np.clip(LN(19.0, 0.3, n), 11, 30) * MM, alpha=np.radians(U(25, 60, n)),
            hook=U(0.5, 3.0, n) * sgn(n), namp=U(0.3, 0.55, n), tau=U(0.16, 0.32, n), conv=U(0.0, 0.6, n),
            swirl=rng.normal(0, 0.2, n), kind=6, wave=U(1.0, 2.2, n), frame=0, fing=1)
        c = {k: np.concatenate(v) for k, v in cols.items()}
        S = len(c["u0"]); self.S = S; self.kind = c["kind"].astype(np.int8); self.frame = c["frame"].astype(np.int8)
        a = np.linspace(0, 1, NU)
        phi = c["phic"][:, None] + c["dphi"][:, None] * (a[None, :] - 0.5)
        q = np.stack([np.broadcast_to(c["u0"][:, None], (S, NU)), c["r0"][:, None] * np.cos(phi), c["r0"][:, None] * np.sin(phi)], -1)
        gid = np.minimum((a[None, :] * c["fing"][:, None]).astype(np.int64), (c["fing"][:, None] - 1).astype(np.int64))
        Q = np.zeros((S, NU, NV, 3), np.float32)
        ds = (c["length"] / (NV - 1))[:, None, None]
        off2 = np.array([3.1, 9.7, 5.2])
        nstart = np.where(c["frame"] > 0, 0.031, 0.0)[:, None, None] * np.array([1.0, 0.37, 0.71])   # decorrelate head noise
        for j in range(NV):
            Q[:, :, j] = q
            age = j / (NV - 1)
            rad = q[..., 1:3]; rn = np.linalg.norm(rad, axis=-1, keepdims=True) + 1e-9
            er = np.concatenate([np.zeros((S, NU, 1)), rad / rn], -1)
            eu = np.zeros((S, NU, 3)); eu[..., 0] = 1.0
            ephi = np.cross(eu, er)
            beta = (c["alpha"] + c["hook"] * age ** 2.2)[:, None, None]
            d = np.cos(beta) * eu + np.sin(beta) * er + (c["swirl"] * (0.3 + age))[:, None, None] * ephi
            d = d / (np.linalg.norm(d, axis=-1, keepdims=True) + 1e-9)
            nz = self.noise.curl(q + nstart, 6.0 * MM) + 0.6 * self.noise.curl(q + nstart, 2.4 * MM, off2)
            d = d + (c["namp"] * (0.25 + 1.2 * age))[:, None, None] * nz
            q = q + d * ds
            # taper every finger toward its own centre line
            shrink = (1 - (c["conv"] / NV))[:, None, None]
            for gk in range(3):
                mk = (gid == gk)[:, :, None]
                cnt = mk.sum(1, keepdims=True)
                ctr = (q * mk).sum(1, keepdims=True) / np.maximum(cnt, 1)
                q = np.where(mk, ctr + (q - ctr) * shrink, q)
        self.Q = Q
        # per-cell areal optical depth
        ac = (a[:-1] + a[1:]) * 0.5
        ag = (np.arange(NV - 1) + 0.5) / (NV - 1)
        fpos = (ac[None, :] * c["fing"][:, None]) % 1.0                    # position inside the finger
        across = np.sin(np.pi * fpos) ** 0.6
        along = smoothstep(0.0, 0.07, ag) * (1 - ag) ** 1.1
        tau = c["tau"][:, None, None] * across[:, :, None] * along[None, None, :]
        st = rng.random((S, NU - 1 + 4))
        st = (st[:, :-4] + st[:, 1:-3] + st[:, 2:-2] + st[:, 3:-1] * 0.5) / 3.5
        st2 = rng.random((S, NU - 1))
        streak = 0.25 + 1.5 * st ** 1.5 + 0.8 * (st2 > 0.82)
        tau = tau * streak[:, :, None]
        core = self.kind == 5
        tau[core] = (c["tau"][core][:, None, None] * (0.5 + streak[core][:, :, None])) * (smoothstep(0, 0.1, ag) * smoothstep(1.0, 0.85, ag))[None, None, :]
        veil = self.kind == 6
        tau[veil] = c["tau"][veil][:, None, None] * (np.sin(np.pi * ac) ** 0.4)[None, :, None] * (smoothstep(0, 0.15, ag) * (1 - ag) ** 0.7)[None, None, :] * (0.6 + 0.8 * st[veil][:, :, None])
        self.tau_cells = tau.astype(np.float32)
        # wave animation parameters
        self.wave_amp = (c["wave"] * MM * 1.6).astype(np.float32)
        self.wave_ph = rng.uniform(0, 2 * np.pi, S).astype(np.float32)
        self.wave_f = rng.uniform(0.55, 1.10, S).astype(np.float32)
        self.wave_dir = np.stack([np.zeros(S), -np.sin(c["phic"]), np.cos(c["phic"])], 1).astype(np.float32)
        self.sheet_s = np.where(c["frame"] > 0, 0.0, np.clip(c["u0"] / L, 0, 1)).astype(np.float32)
        self.age = (np.arange(NV) / (NV - 1)).astype(np.float32)

    def sheet_lattices(self, tl, sp, sl=slice(None)):
        """world-space control lattices (S, NU, NV, 3) of the wisp sheets [sl] at dragon time tl."""
        age = self.age
        ph = 2 * np.pi * (1.3 * age[None, :] - self.wave_f[sl, None] * tl) + self.wave_ph[sl, None]       # (S,NV)
        amp = self.wave_amp[sl, None] * age[None, :] ** 1.5 * np.sin(ph)
        Qa = self.Q[sl] + (amp[:, None, :, None] * self.wave_dir[sl, None, None, :])
        W = np.empty_like(Qa)
        bm = self.frame[sl] == 0
        W[bm] = self.body_to_world(Qa[bm], sp)
        hm = ~bm
        if hm.any():
            Rh = sp["Rh"].astype(np.float32); oh = sp["oh"].astype(np.float32)
            qh = Qa[hm]
            loc = np.stack([-qh[..., 0], qh[..., 2], qh[..., 1]], -1) * np.float32(HEAD_SCALE)   # head local x, y, z
            W[hm] = loc @ Rh.T + oh
        return W


    # ------------------------------------------------------------------ breath (roar)
    def _build_breath(self):
        rng = np.random.default_rng(909)
        nb = 28
        m = MM * HEAD_SCALE
        a = np.linspace(-0.5, 0.5, NU)
        d0 = np.array([0.956, 0.0, -0.292])
        e1 = np.array([0.0, 1.0, 0.0]); e2 = np.cross(d0, e1); e2 /= np.linalg.norm(e2)
        ctr = np.array([19.0, 0.0, -4.4]) * m + rng.normal(0, 1, (nb, 3)) * np.array([0.9, 0.8, 0.8]) * m
        ang = rng.uniform(0, np.pi, nb)
        across = np.cos(ang)[:, None] * e1 + np.sin(ang)[:, None] * e2
        width = rng.uniform(1.6, 3.4, nb) * m
        length = rng.uniform(6.5, 10.5, nb) * m
        cone = rng.uniform(0.45, 0.85, nb)
        namp = rng.uniform(0.25, 0.5, nb)
        q = ctr[:, None, :] + a[None, :, None] * width[:, None, None] * across[:, None, :]
        Q = np.zeros((nb, NU, NV, 3), np.float32)
        ds = (length / (NV - 1))[:, None, None]
        c0 = np.array([19.0, 0.0, -4.4]) * m
        for j in range(NV):
            Q[:, :, j] = q
            age = j / (NV - 1)
            rel = q - c0
            along = (rel @ d0)[..., None]
            rvec = rel - along * d0
            v = d0 + cone[:, None, None] * rvec / (np.abs(along) + 3.0 * m)
            v = v + (namp * (0.3 + 1.3 * age))[:, None, None] * (self.noise.curl(q + 0.017, 5.0 * MM) + 0.6 * self.noise.curl(q + 0.017, 2.2 * MM, (4.1, 2.7, 8.2)))
            q = q + v * ds
        self.breath_Q = Q
        ac = (np.linspace(0, 1, NU)[:-1] + np.linspace(0, 1, NU)[1:]) * 0.5
        ag = (np.arange(NV - 1) + 0.5) / (NV - 1)
        tau = rng.uniform(0.16, 0.34, nb)[:, None, None] * (np.sin(np.pi * ac) ** 0.5)[None, :, None] * (1.0 - 0.55 * ag)[None, None, :]
        st = rng.random((nb, NU - 1)); tau = tau * (0.5 + st[:, :, None])
        self.breath_mass0 = (raster.cell_areas(Q) * tau).astype(np.float32)
        self.breath_age = ag.astype(np.float32)

    def breath(self, tl, sp):
        """ink puff shot out of the mouth during the roar -> (world lattices, cell mass, spread sigma) or (None, None, 0)"""
        if tl < 0.15 or tl > 1.8:
            return None, None, 0.0
        front = smoothstep(0.18, 0.80, tl)
        fade = 1.0 - smoothstep(0.85, 1.75, tl)
        reveal = smoothstep(0.0, 1.0, (front - self.breath_age) / 0.14)
        mass = self.breath_mass0 * (reveal * fade)[None, None, :].astype(np.float32)
        Rh = sp["Rh"].astype(np.float32); oh = sp["oh"].astype(np.float32)
        W = self.breath_Q @ Rh.T + oh
        return W, mass, 0.00012 + 0.00045 * tl

    # ------------------------------------------------------------------ whiskers
    def whisker_lattices(self, tl, sp, grow=1.0):
        """two barbels as thin ribbons: (2, NU, NV, 3) world"""
        Rh = sp["Rh"]; oh = sp["oh"].astype(np.float64)
        out = []
        t = np.linspace(0, 1, NV)
        shapes = {1: [[21.8, 1.9, -0.4], [26.5, 3.4, 1.6], [30.0, 5.4, 6.0], [28.6, 7.4, 11.5], [22.5, 8.6, 15.0], [15.0, 9.2, 16.0], [8.0, 9.6, 14.0], [2.0, 10.4, 15.5], [-4.0, 11.0, 18.0]],
                  -1: [[21.8, -1.9, -0.4], [26.2, -3.6, -1.8], [29.6, -5.4, -5.8], [28.4, -6.8, -11.0], [22.8, -7.8, -14.6], [15.6, -8.4, -15.4], [9.0, -8.6, -13.0], [3.0, -9.0, -14.5], [-2.5, -9.6, -17.5]]}
        for sy in (-1, 1):
            ctrl = np.array(shapes[sy]) * MM * HEAD_SCALE
            c, Lw = resample(catmull_rom(ctrl, 10), NV)
            ph = 2 * np.pi * (1.6 * t - 1.0 * tl) + (0.0 if sy > 0 else 1.9)
            c = c + (t ** 1.3)[:, None] * (np.sin(ph)[:, None] * np.array([0.5, 0.8, 2.3]) + np.cos(ph * 0.7)[:, None] * np.array([1.2, 0.6 * sy, 0.3])) * MM
            if grow < 1.0:
                tt = np.minimum(t, max(grow, 1e-3))
                c = np.stack([np.interp(tt, t, c[:, k]) for k in range(3)], 1)
            w = (0.27 * (1 - 0.65 * t))[:, None] * MM
            side = np.array([0, 0, 1.0])[None, :] * np.linspace(-0.5, 0.5, NU)[:, None, None] * w[None, :, :]
            lat = c[None, :, :] + side                       # (NU, NV, 3) local
            out.append(lat @ Rh.T + oh)
        return np.stack(out, 0).astype(np.float32)
