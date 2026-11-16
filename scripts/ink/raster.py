"""Rasterisation of ink sheets (control lattices) and SDF solids into a density grid, VDB output, previews.

Density convention: grid value 1.0 == fully 'solid' ink (absorption coefficient SIGMA_REF per meter in the shader).
A sheet with areal optical depth tau contributes tau*area/(SIGMA_REF*voxel_volume) to a voxel.
"""
import numpy as np
from .util import add_dlls, write_png

SIGMA_REF = 4000.0   # 1/m at density 1.0


class Grid:
    def __init__(self, lo, hi, vox):
        self.vox = float(vox)
        self.lo = np.asarray(lo, np.float64)
        self.n = np.maximum(np.ceil((np.asarray(hi, np.float64) - self.lo) / vox).astype(np.int64), 1)
        self.hi = self.lo + self.n * vox
        self.rho = np.zeros(tuple(self.n), np.float32)
        self._idx = []
        self._w = []

    # ------------------------------------------------------------------ sheets
    def add_cells(self, P00, P10, P01, P11, mass, cell_seed=None, target=0.75, fmax=64, chunk=3_000_000, tau_min=0.006, max_per_cell=128, spread=None):
        """Splat quad cells. P.. : (C,3) corners (world, meters). mass: (C,) = tau * reference area (m^2)."""
        vox = self.vox
        lo = self.lo.astype(np.float32); hi = self.hi.astype(np.float32)
        # cull cells fully outside
        mn = np.minimum(np.minimum(P00, P10), np.minimum(P01, P11))
        mx = np.maximum(np.maximum(P00, P10), np.maximum(P01, P11))
        keep = np.all(mx > lo, 1) & np.all(mn < hi, 1) & (mass > 0)
        if not keep.all():
            P00, P10, P01, P11, mass = P00[keep], P10[keep], P01[keep], P11[keep], mass[keep]
            if cell_seed is not None: cell_seed = cell_seed[keep]
            if spread is not None: spread = spread[keep]
        if len(mass) == 0:
            return 0
        if cell_seed is None:
            cell_seed = np.arange(len(mass))
        lu = np.maximum(np.linalg.norm(P10 - P00, axis=1), np.linalg.norm(P11 - P01, axis=1))
        lv = np.maximum(np.linalg.norm(P01 - P00, axis=1), np.linalg.norm(P11 - P10, axis=1))
        # effective optical depth of the (stretched) cell: drop what cannot be seen, sample faint cells more coarsely
        area = np.maximum(lu * lv, 1e-14)
        tau = mass / area
        vis = tau > tau_min
        if not vis.all():
            P00, P10, P01, P11, mass, cell_seed, lu, lv, tau = P00[vis], P10[vis], P01[vis], P11[vis], mass[vis], cell_seed[vis], lu[vis], lv[vis], tau[vis]
            if spread is not None: spread = spread[vis]
            if len(mass) == 0:
                return 0
        tgt = target * np.where(tau > 0.05, 1.0, 1.6)
        eu = np.clip(np.ceil(np.log2(np.maximum(lu / (tgt * vox), 1e-6))), 0, np.log2(fmax)).astype(np.int8)
        ev = np.clip(np.ceil(np.log2(np.maximum(lv / (tgt * vox), 1e-6))), 0, np.log2(fmax)).astype(np.int8)
        cap = int(np.log2(max_per_cell))
        over = (eu.astype(np.int16) + ev) - cap
        while (over > 0).any():
            big = over > 0
            red_u = big & (eu >= ev)
            eu[red_u] -= 1; ev[big & ~red_u] -= 1
            over = (eu.astype(np.int16) + ev) - cap
        nsamp = 0
        key = eu.astype(np.int32) * 16 + ev
        jrng = np.random.default_rng(4242) if spread is not None else None
        for k in np.unique(key):
            sel = np.nonzero(key == k)[0]
            fu = 1 << int(k // 16); fv = 1 << int(k % 16)
            per = fu * fv
            step = max(1, chunk // per)
            a = (np.arange(fu, dtype=np.float32) + 0.5) / fu
            b = (np.arange(fv, dtype=np.float32) + 0.5) / fv
            for s0 in range(0, len(sel), step):
                ii = sel[s0:s0 + step]
                # per-cell stable jitter (Cranley-Patterson rotation)
                cs = cell_seed[ii].astype(np.uint64)
                ja = ((cs * np.uint64(2654435761)) % np.uint64(1 << 20)).astype(np.float32) / (1 << 20)
                jb = ((cs * np.uint64(40503) + np.uint64(12345)) % np.uint64(1 << 20)).astype(np.float32) / (1 << 20)
                A = (a[None, :] + (ja[:, None] - 0.5) / fu)[:, :, None, None]     # (n,fu,1,1)
                B = (b[None, :] + (jb[:, None] - 0.5) / fv)[:, None, :, None]     # (n,1,fv,1)
                p00 = P00[ii][:, None, None, :]; p10 = P10[ii][:, None, None, :]
                p01 = P01[ii][:, None, None, :]; p11 = P11[ii][:, None, None, :]
                P = (p00 * (1 - A) + p10 * A) * (1 - B) + (p01 * (1 - A) + p11 * A) * B
                P = P.reshape(-1, 3)
                if spread is not None:
                    sg = np.repeat(spread[ii], per)
                    if sg.max() > 0:
                        P = P + jrng.standard_normal(P.shape, dtype=np.float32) * sg[:, None]
                w = np.repeat(mass[ii] / per, per)
                self._splat_points(P, w)
                nsamp += len(w)
        return nsamp

    def _splat_points(self, P, w):
        q = (P - self.lo.astype(np.float32)) / np.float32(self.vox)
        i = np.floor(q).astype(np.int32)
        n = self.n
        ok = (i[:, 0] >= 0) & (i[:, 0] < n[0]) & (i[:, 1] >= 0) & (i[:, 1] < n[1]) & (i[:, 2] >= 0) & (i[:, 2] < n[2])
        if not ok.all():
            i = i[ok]; w = w[ok]
        flat = (i[:, 0].astype(np.int64) * n[1] + i[:, 1]) * n[2] + i[:, 2]
        self._idx.append(flat); self._w.append(w.astype(np.float32))

    def add_points(self, P, w):
        self._splat_points(np.asarray(P, np.float32), np.asarray(w, np.float32))

    def flush_sheets(self, blur=1):
        """Accumulate all queued samples; convert mass (tau*m^2) to density; optional binomial blur passes."""
        if self._idx:
            flat = np.concatenate(self._idx); w = np.concatenate(self._w)
            self._idx = []; self._w = []
            acc = np.bincount(flat, weights=w, minlength=int(np.prod(self.n)))
            sheet = (acc / (SIGMA_REF * self.vox ** 3)).astype(np.float32).reshape(tuple(self.n))
            del acc
            for _ in range(blur):
                sheet = blur3(sheet)
            self.rho += sheet

    # ------------------------------------------------------------------ solids
    def _bbox(self, lo, hi):
        i0 = np.maximum(np.floor((lo - self.lo) / self.vox).astype(np.int64), 0)
        i1 = np.minimum(np.ceil((hi - self.lo) / self.vox).astype(np.int64) + 1, self.n)
        if np.any(i1 <= i0):
            return None
        sl = tuple(slice(int(a), int(b)) for a, b in zip(i0, i1))
        axes = [((np.arange(i0[d], i1[d]) + 0.5) * self.vox + self.lo[d]).astype(np.float32) for d in range(3)]
        return sl, axes

    def add_capsules(self, A, B, ra, rb, dens=1.0, edge=None, out=None):
        """Union of tapered capsules (max-combined) into out (default self.rho, combined with max)."""
        tgt = self.rho if out is None else out
        edge = self.vox * 1.2 if edge is None else edge
        A = np.asarray(A, np.float32); B = np.asarray(B, np.float32)
        ra = np.broadcast_to(np.asarray(ra, np.float32), (len(A),)); rb = np.broadcast_to(np.asarray(rb, np.float32), (len(A),))
        dens = np.broadcast_to(np.asarray(dens, np.float32), (len(A),))
        for k in range(len(A)):
            a = A[k]; b = B[k]; r = max(ra[k], rb[k]) + edge
            if dens[k] <= 0: continue
            rm = max(ra[k], rb[k])
            if rm < 0.35 * self.vox: continue
            thin = min(1.0, rm / (1.2 * self.vox))        # fade out capsules thinner than a voxel
            bb = self._bbox(np.minimum(a, b) - r, np.maximum(a, b) + r)
            if bb is None: continue
            sl, (xs, ys, zs) = bb
            ba = b - a; l2 = float(ba @ ba) + 1e-20
            pax = (xs - a[0])[:, None, None]; pay = (ys - a[1])[None, :, None]; paz = (zs - a[2])[None, None, :]
            h = np.clip((pax * ba[0] + pay * ba[1] + paz * ba[2]) / l2, 0.0, 1.0)
            d = np.sqrt((pax - ba[0] * h) ** 2 + (pay - ba[1] * h) ** 2 + (paz - ba[2] * h) ** 2) - (ra[k] + (rb[k] - ra[k]) * h)
            v = np.clip(0.5 - d / edge, 0.0, 1.0) * (dens[k] * thin)
            np.maximum(tgt[sl], v, out=tgt[sl])

    def add_sdf_volume(self, sdf, sdf_lo, sdf_vox, R, origin, dens=1.0, edge=None, bound_radius=None, out=None, offset=0.0, mod=None, noise=None, scale=1.0):
        """Sample a precomputed local SDF array (meters) placed with rotation R (3x3, columns = local axes in world)
        and origin (world position of local (0,0,0)). Combined with max."""
        tgt = self.rho if out is None else out
        edge = self.vox * 1.2 if edge is None else edge
        # uniform scale: work in a scaled copy of the local frame (distances scale too)
        sdf_lo = np.asarray(sdf_lo, np.float64) * scale; sdf_vox = sdf_vox * scale
        edge = edge / scale; offset = offset / scale
        n = np.array(sdf.shape)
        # world bbox of the local box
        corners = np.array([[x, y, z] for x in (0, n[0]) for y in (0, n[1]) for z in (0, n[2])], np.float64) * sdf_vox + sdf_lo
        wc = corners @ R.T + origin
        bb = self._bbox(wc.min(0), wc.max(0))
        if bb is None: return
        sl, (xs, ys, zs) = bb
        Rf = R.astype(np.float32)
        dy = (ys - np.float32(origin[1]))[None, :, None]; dz = (zs - np.float32(origin[2]))[None, None, :]
        slab = max(1, int(600_000 // max(1, len(ys) * len(zs))))
        nx, ny, nz = sdf.shape
        flat = sdf.reshape(-1)
        inv = np.float32(1.0 / sdf_vox)
        band = np.float32(edge + 1.8 * sdf_vox / scale)
        for x0 in range(0, len(xs), slab):
            xsl = slice(sl[0].start + x0, min(sl[0].start + x0 + slab, sl[0].stop))
            dx = (xs[x0:x0 + slab] - np.float32(origin[0]))[:, None, None]
            q = [(dx * Rf[0, c] + dy * Rf[1, c] + dz * Rf[2, c] - np.float32(sdf_lo[c])) * inv - np.float32(0.5) for c in range(3)]
            ok = (q[0] > 0.5) & (q[0] < nx - 1.5) & (q[1] > 0.5) & (q[1] < ny - 1.5) & (q[2] > 0.5) & (q[2] < nz - 1.5)
            if not ok.any():
                continue
            sel = np.nonzero(ok.reshape(-1))[0]
            qx = q[0].reshape(-1)[sel]; qy = q[1].reshape(-1)[sel]; qz = q[2].reshape(-1)[sel]
            near = ((qx + 0.5).astype(np.int32).astype(np.int64) * ny + (qy + 0.5).astype(np.int32)) * nz + (qz + 0.5).astype(np.int32)
            if noise is not None and offset != 0.0:
                off = np.float32(offset) * (np.float32(0.4) + np.float32(1.2) * noise.reshape(-1)[near].astype(np.float32))
            else:
                off = np.full(len(near), np.float32(offset))
            d0 = flat[near] + off
            val = (d0 < 0).astype(np.float32)
            bsel = np.nonzero(np.abs(d0) < band)[0]
            if len(bsel):
                d = trilinear_sample(sdf, qx[bsel], qy[bsel], qz[bsel], fill=1.0) + off[bsel]
                val[bsel] = np.clip(0.5 - d / edge, 0.0, 1.0)
            v = np.zeros(ok.size, np.float32); v[sel] = val * np.float32(dens)
            ssl = (xsl, sl[1], sl[2])
            np.maximum(tgt[ssl], v.reshape(ok.shape), out=tgt[ssl])

    # ------------------------------------------------------------------ output
    def write_vdb(self, path, tol=2e-4, half=True):
        add_dlls()
        import openvdb as vdb
        g = vdb.FloatGrid()
        g.copyFromArray(self.rho, tolerance=tol)
        v = self.vox; o = self.lo + 0.5 * v
        g.transform = vdb.createLinearTransform([[v, 0, 0, 0], [0, v, 0, 0], [0, 0, v, 0], [o[0], o[1], o[2], 1]])
        g.name = "density"; g.gridClass = vdb.GridClass.FOG_VOLUME
        g.saveFloatAsHalf = half
        vdb.write(path, grids=[g])
        return g.activeVoxelCount()

    def preview(self, axis=1, sigma_scale=1.0, bg=(0.96, 0.90, 0.80), tint=(1.0, 0.96, 0.88), up=1):
        """Orthographic absorption preview looking along `axis` (1 = front view from -Y: x right, z up)."""
        tau = self.rho.sum(axis=axis) * (self.vox * SIGMA_REF * sigma_scale)
        if axis == 1:
            img = tau.T[::-1, :]            # rows: z down, cols: x
        elif axis == 0:
            img = tau.T[::-1, :]            # side view: cols y, rows z
        else:
            img = tau.T[::-1, :]            # top view: cols x, rows y
        T = np.exp(-img[:, :, None] * np.asarray(tint, np.float32)[None, None, :])
        out = T * np.asarray(bg, np.float32)
        if up > 1:
            out = np.repeat(np.repeat(out, up, 0), up, 1)
        return out


def blur3(a):
    """separable [1,2,1]/4 binomial blur, zero boundary"""
    for ax in range(3):
        t = a * np.float32(0.5)
        s1 = [slice(None)] * 3; s0 = [slice(None)] * 3
        s1[ax] = slice(1, None); s0[ax] = slice(None, -1)
        t[tuple(s1)] += a[tuple(s0)] * np.float32(0.25)
        t[tuple(s0)] += a[tuple(s1)] * np.float32(0.25)
        a = t
    return a


def trilinear_sample(arr, qx, qy, qz, fill=0.0):
    """arr (nx,ny,nz); q* broadcastable float index coords (voxel-centre aligned). Outside -> fill."""
    nx, ny, nz = arr.shape
    shape = np.broadcast_shapes(qx.shape, qy.shape, qz.shape)
    fx = np.floor(qx); fy = np.floor(qy); fz = np.floor(qz)
    tx = (qx - fx).astype(np.float32); ty = (qy - fy).astype(np.float32); tz = (qz - fz).astype(np.float32)
    ix = fx.astype(np.int32); iy = fy.astype(np.int32); iz = fz.astype(np.int32)
    okx = (ix >= 0) & (ix < nx - 1); oky = (iy >= 0) & (iy < ny - 1); okz = (iz >= 0) & (iz < nz - 1)
    ix = np.clip(ix, 0, nx - 2); iy = np.clip(iy, 0, ny - 2); iz = np.clip(iz, 0, nz - 2)
    flat = arr.reshape(-1)
    base = (ix.astype(np.int64) * ny + iy) * nz + iz        # broadcast to full shape
    s_y = nz; s_x = ny * nz
    c000 = flat[base]; c001 = flat[base + 1]
    c010 = flat[base + s_y]; c011 = flat[base + s_y + 1]
    c100 = flat[base + s_x]; c101 = flat[base + s_x + 1]
    c110 = flat[base + s_x + s_y]; c111 = flat[base + s_x + s_y + 1]
    c00 = c000 + (c001 - c000) * tz; c01 = c010 + (c011 - c010) * tz
    c10 = c100 + (c101 - c100) * tz; c11 = c110 + (c111 - c110) * tz
    c0 = c00 + (c01 - c00) * ty; c1 = c10 + (c11 - c10) * ty
    out = c0 + (c1 - c0) * tx
    ok = okx & oky & okz
    return np.where(ok, out, np.float32(fill))


def cells_from_lattice(L):
    """L: (S,nu,nv,3) -> four corner arrays (C,3)"""
    P00 = L[:, :-1, :-1].reshape(-1, 3); P10 = L[:, 1:, :-1].reshape(-1, 3)
    P01 = L[:, :-1, 1:].reshape(-1, 3); P11 = L[:, 1:, 1:].reshape(-1, 3)
    return P00, P10, P01, P11


def cell_areas(L):
    P00, P10, P01, P11 = cells_from_lattice(L)
    a1 = 0.5 * np.linalg.norm(np.cross(P10 - P00, P01 - P00), axis=1)
    a2 = 0.5 * np.linalg.norm(np.cross(P10 - P11, P01 - P11), axis=1)
    return (a1 + a2).reshape(L.shape[0], L.shape[1] - 1, L.shape[2] - 1)
