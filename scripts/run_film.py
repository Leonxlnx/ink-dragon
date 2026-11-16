"""Driver for the ink simulation.
  python run_film.py plume [frame_step]          run plume sim, dump lattices at video-frame sim times
  python run_film.py dissolve [frame_step]
  python run_film.py prev f0 f1 step [vox_mm]    orthographic preview PNGs (front) -> work/prev/f####.png
  python run_film.py bake f0 f1 step [vox_mm]    VDBs -> work/vdb/ink_####.vdb  (skips existing)
  python run_film.py times                       print the frame->sim time table summary
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from ink import film, raster, util
from ink.dragon import NU, NV
import common as cm

def log(*a):
    print(*a); sys.stdout.flush()

cmd = sys.argv[1]
args = sys.argv[2:]
os.makedirs(film.CACHE, exist_ok=True); os.makedirs(film.VDB_DIR, exist_ok=True)

if cmd == "times":
    t = film.ALL_T
    for f in range(0, cm.N_FRAMES, 30):
        log("frame %4d  video %5.2fs  sim %8.4fs" % (f, f / cm.FPS, t[f]))
    log("first ink frame:", int(np.argmax(t >= film.T_START)), " morph start:", int(np.argmax(t >= film.T_M0)),
        " formed:", int(np.argmax(t >= film.T_F)), " dissolve:", int(np.argmax(t >= film.T_D)))

elif cmd == "plume":
    import subprocess
    step = int(args[0]) if args else 1
    nproc = int(args[1]) if len(args) > 1 else 5
    F = film.Film(verbose=True)
    frames = np.arange(0, cm.N_FRAMES, step)
    times = film.plume_times_for_frames(frames)
    times = np.unique(np.concatenate([times, [film.T_M0, film.T_F]]))
    n_main = int((times <= film.T_F + 1e-9).sum())
    P = film.Plume(F.S)
    log("plume: %d sheets (+%d pool), %d snapshots (%d main), %d procs" % (F.S, P.N_POOL, len(times), n_main, nproc))
    np.save(os.path.join(film.CACHE, "plume_times.npy"), times)
    fm = os.path.join(film.CACHE, "plume_main.i16"); fp = os.path.join(film.CACHE, "plume_pool.i16")
    np.memmap(fm, np.int16, "w+", shape=(n_main, F.S, NU, NV, 3)).flush()
    np.memmap(fp, np.int16, "w+", shape=(len(times), P.N_POOL, NU, NV, 3)).flush()
    procs = [subprocess.Popen([sys.executable, os.path.abspath(__file__), "plume_part", str(k), str(nproc), str(F.S)]) for k in range(nproc)]
    rc = [p.wait() for p in procs]
    log("workers done", rc)
    pm = np.memmap(fm, np.int16, "r", shape=(n_main, F.S, NU, NV, 3))
    i0 = int(np.argmin(np.abs(times - film.T_M0)))
    zp = film.dequant(np.asarray(pm[i0]))[..., 2].reshape(F.S, -1).mean(1)
    sp = F.D.spine(0.0)
    zd = F.D.sheet_lattices(0.0, sp)[..., 2].reshape(F.S, -1).mean(1)
    od = np.argsort(-zd); op = np.argsort(-zp)
    perm = np.empty(F.S, np.int64); perm[od] = op
    np.savez(os.path.join(film.CACHE, "plume_meta.npz"), times=times, perm=perm, n_main_times=n_main, area0=P.area0)
    log("plume done")

elif cmd == "plume_part":
    k, nproc, S = int(args[0]), int(args[1]), int(args[2])
    times = np.load(os.path.join(film.CACHE, "plume_times.npy"))
    n_main = int((times <= film.T_F + 1e-9).sum())
    P = film.Plume(S)
    pm = np.memmap(os.path.join(film.CACHE, "plume_main.i16"), np.int16, "r+", shape=(n_main, S, NU, NV, 3))
    i0 = (S * k) // nproc; i1 = (S * (k + 1)) // nproc
    class View:
        def __init__(self, mm, a, b): self.mm, self.a, self.b = mm, a, b
        def __setitem__(self, it, val): self.mm[it, self.a:self.b] = val
    P.run(times, P.X0[i0:i1].copy(), View(pm, i0, i1), film.T_F, log if k == 0 else None, tag="[%d]" % k)
    pm.flush()
    if k == nproc - 1:
        pp = np.memmap(os.path.join(film.CACHE, "plume_pool.i16"), np.int16, "r+", shape=(len(times), P.N_POOL, NU, NV, 3))
        P.run(times, P.X0[S:].copy(), pp, film.T_END + 1.0, None)
        pp.flush()

elif cmd == "dissolve":
    import subprocess
    step = int(args[0]) if args else 1
    nproc = int(args[1]) if len(args) > 1 else 5
    F = film.Film(verbose=True)
    frames = np.arange(0, cm.N_FRAMES, step)
    t = film.frame_time(frames)
    times = np.unique(np.round(t[t >= film.T_D], 6))
    np.save(os.path.join(film.CACHE, "dissolve_times%s.npy" % film.DIS_TAG), times)
    fn = os.path.join(film.CACHE, "dissolve%s.i16" % film.DIS_TAG)
    np.memmap(fn, np.int16, "w+", shape=(len(times), F.S, NU, NV, 3)).flush()
    log("dissolve: %d snapshots, %d procs" % (len(times), nproc))
    procs = [subprocess.Popen([sys.executable, os.path.abspath(__file__), "dissolve_part", str(k), str(nproc)]) for k in range(nproc)]
    rc = [p.wait() for p in procs]
    np.savez(os.path.join(film.CACHE, "dissolve_meta%s.npz" % film.DIS_TAG), times=times)
    log("dissolve done", rc)

elif cmd == "dissolve_part":
    k, nproc = int(args[0]), int(args[1])
    F = film.Film()
    times = np.load(os.path.join(film.CACHE, "dissolve_times%s.npy" % film.DIS_TAG))
    mm = np.memmap(os.path.join(film.CACHE, "dissolve%s.i16" % film.DIS_TAG), np.int16, "r+", shape=(len(times), F.S, NU, NV, 3))
    i0 = (F.S * k) // nproc; i1 = (F.S * (k + 1)) // nproc
    class View:
        def __init__(self, mm, a, b): self.mm, self.a, self.b = mm, a, b
        def __setitem__(self, it, val): self.mm[it, self.a:self.b] = val
    film.Dissolve(F).run(times, View(mm, i0, i1), slice(i0, i1), log if k == 0 else None)
    mm.flush()

elif cmd in ("prev", "bake"):
    import shots
    if "," in args[0]:
        frame_list = [int(x) for x in args[0].split(",") if x]
        args = [0, 0, 1] + list(args[1:])
    else:
        frame_list = list(range(int(args[0]), int(args[1]), int(args[2])))
    vox_arg = float(args[3]) * 1e-3 if len(args) > 3 and float(args[3]) > 0 else None
    view = args[4] if len(args) > 4 else "front"
    F = film.Film()
    F.prepare()
    def _pause():
        while any(os.path.exists(os.path.join(cm.ROOT, "work", n)) for n in ("PAUSE_ALL", "PAUSE_BAKE")):
            time.sleep(15)
    for f in frame_list:
        _pause()
        t = float(film.ALL_T[f])
        if t < film.T_START:
            continue
        if t >= film.T_D and F.dis_times is None:
            log("no dissolve data, stop at", f); break
        out = os.path.join(film.VDB_DIR, "ink_%04d.vdb" % f)
        T = util.Timer()
        if cmd == "prev":
            vox = vox_arg or 0.25e-3
            lo = (-0.0375, -0.0375, cm.GLASS_BASE); hi = (0.0375, 0.0375, cm.WATER_Z + 0.0015)
        else:
            spec = shots.bake_spec(f)
            if spec is None:
                continue
            vox, lo, hi = spec
            if vox_arg: vox = vox_arg
            if os.path.exists(out):
                continue
            lock = out + ".lock"
            try:
                fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY); os.close(fd)
            except FileExistsError:
                continue
        g = F.raster(t, vox=vox, lo=lo, hi=hi, timer=T)
        if cmd == "prev":
            up = 2 if vox >= 0.19e-3 else 1
            for v in view.split(","):
                ax = {"front": 1, "side": 0, "top": 2}[v]
                util.write_png(os.path.join(cm.ROOT, "work", "prev", "f%04d_%s.png" % (f, v)), g.preview(ax, up=up))
        else:
            tmp = out + ".tmp"
            n = g.write_vdb(tmp)
            os.replace(tmp, out)
            try: os.remove(lock)
            except OSError: pass
            T.tick("vdb")
        log("frame %d t=%.3f vox %.3f grid %s max %.2f | %s" % (f, t, vox * 1e3, tuple(int(x) for x in g.n), float(g.rho.max()), T))
