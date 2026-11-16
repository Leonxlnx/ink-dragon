"""Velocity / noise fields (pure NumPy, float32, tuned for speed)."""
import numpy as np


class NoiseGrid:
    """Periodic smooth random fields on an n^3 lattice: a divergence-free vector field (curl of a
    random potential) and a scalar field. Sampled with trilinear interpolation, tiling in all axes."""
    def __init__(self, n=48, seed=0, k0=2.5):
        rng = np.random.default_rng(seed)
        k = np.fft.fftfreq(n) * n
        KX, KY, KZ = np.meshgrid(k, k, k, indexing="ij")
        k2 = KX**2 + KY**2 + KZ**2
        filt = np.exp(-k2 / (2 * k0 * k0)); filt[0, 0, 0] = 0
        A = [np.fft.fftn(rng.standard_normal((n, n, n))) * filt for _ in range(3)]
        V = [1j * (KY * A[2] - KZ * A[1]), 1j * (KZ * A[0] - KX * A[2]), 1j * (KX * A[1] - KY * A[0])]
        v = np.stack([np.real(np.fft.ifftn(c)) for c in V], -1)
        v /= np.sqrt((v**2).sum(-1).mean())
        s = np.real(np.fft.ifftn(np.fft.fftn(rng.standard_normal((n, n, n))) * filt)); s /= s.std()
        self.n = n
        self.m = n + 1
        # padded copies: index +1 never has to wrap
        vp = np.empty((n + 1, n + 1, n + 1, 3), np.float32)
        sp = np.empty((n + 1, n + 1, n + 1), np.float32)
        ii = np.arange(n + 1) % n
        vp[:] = v[np.ix_(ii, ii, ii)]
        sp[:] = s[np.ix_(ii, ii, ii)]
        self.vp = np.ascontiguousarray(vp.reshape(-1, 3))
        self.sp = np.ascontiguousarray(sp.reshape(-1))

    def _sample(self, arr, P, wavelength, offset):
        P = np.asarray(P, np.float32)
        shp = P.shape[:-1]
        q = P.reshape(-1, 3) * np.float32(self.n / (wavelength * 5.0))
        q += np.asarray(offset, np.float32)
        f = np.floor(q)
        q -= f                                   # fractional part
        i = f.astype(np.int32)
        i %= self.n
        m = self.m
        base = (i[:, 0] * m + i[:, 1]) * m + i[:, 2]
        base = base.astype(np.intp)
        vec = arr.ndim == 2
        if vec:
            tx, ty, tz = q[:, 0:1], q[:, 1:2], q[:, 2:3]
        else:
            tx, ty, tz = q[:, 0], q[:, 1], q[:, 2]
        tk = (lambda o: arr.take(base + o, axis=0)) if vec else (lambda o: arr.take(base + o))
        m2 = m * m
        c00 = tk(0); c = tk(1); c -= c00; c *= tz; c00 += c
        c01 = tk(m); c = tk(m + 1); c -= c01; c *= tz; c01 += c
        c10 = tk(m2); c = tk(m2 + 1); c -= c10; c *= tz; c10 += c
        c11 = tk(m2 + m); c = tk(m2 + m + 1); c -= c11; c *= tz; c11 += c
        c01 -= c00; c01 *= ty; c00 += c01
        c11 -= c10; c11 *= ty; c10 += c11
        c10 -= c00; c10 *= tx; c00 += c10
        return c00.reshape(shp + ((3,) if vec else ()))

    def curl(self, P, wavelength, offset=(0, 0, 0)):
        """unit-RMS divergence-free vector noise; dominant feature size ~ wavelength (meters)"""
        return self._sample(self.vp, P, wavelength, offset)

    def scalar(self, P, wavelength, offset=(0, 0, 0)):
        return self._sample(self.sp, P, wavelength, offset)


def hill_vortex(P, center, a, U, m=(0.0, 0.0, -1.0)):
    """Lab-frame velocity of Hill's spherical vortex of radius a travelling with speed U along unit vector m.
    P (N,3) float32 -> (N,3) float32."""
    m = np.asarray(m, np.float32)
    d = P - np.asarray(center, np.float32)
    z = -(d @ m)                      # axial coordinate, vortex travels toward -z
    rv = d + z[:, None] * m           # radial vector (perpendicular to axis)
    r2 = np.einsum("ij,ij->i", rv, rv)
    R2 = r2 + z * z
    a = np.float32(a); U = np.float32(U)
    a2 = a * a; a3 = a2 * a
    inside = R2 < a2
    R2o = np.maximum(R2, a2)
    iR5 = R2o ** np.float32(-2.5)
    # outside (lab frame)
    uz = U * a3 * (np.float32(1.5) * r2 * iR5 - R2o * iR5)
    kr = np.float32(-1.5) * U * a3 * z * iR5
    # inside (lab frame)
    if inside.any():
        zi = z[inside]
        uz[inside] = np.float32(-1.5) * U * (1 - (zi * zi + 2 * r2[inside]) / a2) - U
        kr[inside] = np.float32(-1.5) * U * zi / a2
    out = kr[:, None] * rv
    out -= uz[:, None] * m
    return out
