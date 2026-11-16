"""Match the fine detail of motion-interpolated in-between frames to their rendered neighbours.

Motion-compensated interpolation averages two warped frames, which acts as a slight low-pass wherever the camera or
the ink moves (15-20 % less fine-detail energy than a rendered frame). Played back, every second frame would be a
touch softer. This script measures the fine-detail energy (RMS Laplacian of luma) of each interpolated frame and of
its two rendered neighbours and adds exactly as much 3x3 unsharp mask as is needed to match them (capped).
Results go to frames_fill_sharp/; assemble.py prefers frames/ > frames_fill_sharp/ > frames_fill/.

python match_fill.py [a:b]      (optional frame range for a test run)"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import common as cm, shots
from ink import util
util.add_dlls()
import OpenImageIO as oiio

FR = os.path.join(cm.ROOT, "frames"); FILL = os.path.join(cm.ROOT, "frames_fill"); OUT = os.path.join(cm.ROOT, "frames_fill_sharp")
os.makedirs(OUT, exist_ok=True)
A_TEST, A_MAX, A_MIN = 0.3, 0.5, 0.03
rng = None
for a in sys.argv[1:]:
    if ":" in a:
        rng = [int(x) for x in a.split(":")]

def rd(p):
    return np.asarray(oiio.ImageBuf(p).get_pixels(oiio.FLOAT))[:, :, :3].astype(np.float32)

def blur(a):                      # 3x3 binomial, edges replicated
    p = np.pad(a, ((1, 1), (1, 1), (0, 0)), mode="edge")
    v = 0.25 * p[:-2] + 0.5 * p[1:-1] + 0.25 * p[2:]
    return 0.25 * v[:, :-2] + 0.5 * v[:, 1:-1] + 0.25 * v[:, 2:]

def hf(l):
    d = 4 * l[1:-1, 1:-1] - l[:-2, 1:-1] - l[2:, 1:-1] - l[1:-1, :-2] - l[1:-1, 2:]
    return float(np.sqrt((d * d).mean()))

_cache = {}
def hf_real(f):
    if f not in _cache:
        _cache[f] = hf(rd(os.path.join(FR, "f_%04d.png" % f)).mean(2))
    return _cache[f]

n = 0; amounts = {}
for s in shots.SHOTS:
    for f in range(s["f0"], s["f1"]):
        if rng and not (rng[0] <= f < rng[1]):
            continue
        name = "f_%04d.png" % f
        src = os.path.join(FILL, name); dst = os.path.join(OUT, name)
        if os.path.exists(os.path.join(FR, name)) or not os.path.exists(src) or os.path.exists(dst):
            continue
        if not (os.path.exists(os.path.join(FR, "f_%04d.png" % (f - 1))) and os.path.exists(os.path.join(FR, "f_%04d.png" % (f + 1)))):
            continue
        img = rd(src); det = img - blur(img)
        l0 = img.mean(2); ld = det.mean(2)
        h0 = hf(l0); h1 = hf(l0 + A_TEST * ld)
        target = 0.5 * (hf_real(f - 1) + hf_real(f + 1))
        a = A_TEST * (target - h0) / (h1 - h0) if h1 > h0 else 0.0
        a = float(min(max(a, 0.0), A_MAX))
        tmp = os.path.join(OUT, "tmp_%d_%s" % (os.getpid(), name))
        if a < A_MIN:
            a = 0.0
            try:
                os.link(src, tmp)
            except OSError:
                import shutil; shutil.copyfile(src, tmp)
        else:
            util.write_png(tmp, img + a * det)
        os.replace(tmp, dst)
        amounts.setdefault(s["name"], []).append(a); n += 1
        if rng:
            print("frame %d  fill %.4f  target %.4f  amount %.3f" % (f, h0, target, a)); sys.stdout.flush()
for k, v in amounts.items():
    print("%-16s %3d frames, unsharp amount mean %.3f (min %.3f, max %.3f)" % (k, len(v), np.mean(v), min(v), max(v)))
print("matched", n)
