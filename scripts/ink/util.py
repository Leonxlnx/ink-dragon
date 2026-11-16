"""Small helpers: DLL setup for Blender's bundled python, PNG writer, timers."""
import os, sys, zlib, struct, time
import numpy as np

BL_SHARED = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.shared"
_dll_done = False
def add_dlls():
    global _dll_done
    if not _dll_done and os.path.isdir(BL_SHARED) and hasattr(os, "add_dll_directory"):
        os.add_dll_directory(BL_SHARED)
    _dll_done = True

def write_png(path, img):
    """img: HxWx3 float (0..1) or uint8"""
    if img.dtype != np.uint8:
        img = (np.clip(img, 0, 1) * 255.0 + 0.5).astype(np.uint8)
    h, w, c = img.shape
    raw = np.empty((h, w * c + 1), np.uint8); raw[:, 0] = 0; raw[:, 1:] = img.reshape(h, w * c)
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
    ct = 2 if c == 3 else 0
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, ct, 0, 0, 0)) + \
          chunk(b"IDAT", zlib.compress(raw.tobytes(), 3)) + chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)

class Timer:
    def __init__(self): self.t = time.time(); self.log = []
    def tick(self, name):
        n = time.time(); self.log.append((name, n - self.t)); self.t = n
    def __str__(self): return " ".join("%s=%.2f" % x for x in self.log)

def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)

def normalize(v, axis=-1, eps=1e-12):
    return v / (np.linalg.norm(v, axis=axis, keepdims=True) + eps)
