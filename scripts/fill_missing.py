"""Synthesize missing in-between frames (single-frame gaps inside a shot) by motion-compensated interpolation
of the two rendered neighbours. Results go to frames_fill/ so real renders can still replace them later.
python fill_missing.py [--list]"""
import os, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common as cm, shots
FR = os.path.join(cm.ROOT, "frames"); FILL = os.path.join(cm.ROOT, "frames_fill")
os.makedirs(FILL, exist_ok=True)
have = lambda f: os.path.exists(os.path.join(FR, "f_%04d.png" % f))
todo = []; bad = []
for s in shots.SHOTS:
    for f in range(s["f0"], s["f1"]):
        if have(f):
            continue
        if f - 1 >= s["f0"] and f + 1 < s["f1"] and have(f - 1) and have(f + 1):
            todo.append(f)
        else:
            bad.append(f)
print("to interpolate:", len(todo), " not fillable:", len(bad), bad[:30])
if "--list" in sys.argv:
    raise SystemExit
# pass B renders these shots first, so their gaps are filled last (most of them get a real render anyway)
LATE = ("s06_head_roar", "s09_hero_wide")
todo.sort(key=lambda f: (shots.shot_of(f)["name"] in LATE, f))
if "--worker" in sys.argv:            # --worker k n : this process takes every n-th frame, starting at k
    i = sys.argv.index("--worker"); todo = todo[int(sys.argv[i + 1])::int(sys.argv[i + 2])]
n = 0
for f in todo:
    final = os.path.join(FILL, "f_%04d.png" % f)
    if os.path.exists(final) or have(f):
        continue
    out = os.path.join(FILL, "tmp_%d_%04d.png" % (os.getpid(), f))
    a = os.path.join(FR, "f_%04d.png" % (f - 1)); b = os.path.join(FR, "f_%04d.png" % (f + 1))
    fc = ("[0:v][1:v][1:v]concat=n=3:v=1:a=0,settb=1/15,setpts=N/15/TB,"
          "minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1:scd=none,select='eq(n,1)'")
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", a, "-i", b, "-filter_complex", fc, "-frames:v", "1", out],
                       capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(out):
        print("fail", f, r.stderr[-300:]); continue
    os.replace(out, final)
    n += 1; sys.stdout.flush()
print("interpolated", n)
