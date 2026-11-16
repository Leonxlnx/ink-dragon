"""Blender render driver.
blender -b --factory-startup --python scripts/render_film.py -- <frames|planA|planB> [--preset final] [--pct N] [--spp N]
        [--threads 14] [--out frames] [--tag x] [--overwrite] [--scale 4000] [--wait]
<frames>: "a:b[:step]" ranges and/or single numbers, comma separated (e.g. "0:105,720,900:945:5"),
          or planA (first/last frame of every shot + all even frames, most important shots first),
          or planB (the remaining odd frames, same priority order).
Frames whose PNG already exists are skipped; a .lock file lets several Blender processes share one list.
--wait: keep sweeping until every frame of the list is rendered (frames wait for their VDB to be baked)."""
import bpy, sys, os, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common as cm
import scene_lib as sl
import shots
from ink import film

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def opt(name, default=None, cast=str):
    if name in argv:
        return cast(argv[argv.index(name) + 1])
    return default

PRIORITY = ["s06_head_roar", "s09_hero_wide", "s03a_impact", "s03b_waterline", "s07_body_glide", "s05_morph_orbit",
            "s04a_ring_track", "s04b_low_wide", "s08_top_down", "s10_dissolve_34", "s11_final_wide",
            "s02_drop_fall", "s01b_waterline", "s01_establish"]
# pass B order: shots where motion-interpolated in-betweens are weakest come first (fast ink motion, moving camera);
# the locked-off plume shots interpolate almost perfectly and come last.
PRIORITY_B = ["s06_head_roar", "s05_morph_orbit", "s07_body_glide", "s09_hero_wide", "s08_top_down", "s10_dissolve_34",
              "s11_final_wide", "s03a_impact", "s04a_ring_track", "s04b_low_wide", "s03b_waterline",
              "s02_drop_fall", "s01b_waterline", "s01_establish"]
def plan(which):
    out = []
    by = {s["name"]: s for s in shots.SHOTS}
    for n in (PRIORITY if which == "planA" else PRIORITY_B):
        s = by[n]
        for f in range(s["f0"], s["f1"]):
            a = (f % 2 == 0) or f == s["f0"] or f == s["f1"] - 1
            if a == (which == "planA"):
                out.append(f)
    return out

frames = []
if argv[0] in ("planA", "planB"):
    frames = plan(argv[0])
else:
    for part in argv[0].split(","):
        if ":" in part:
            b = [int(x) for x in part.split(":")]
            frames += list(range(b[0], b[1], b[2] if len(b) > 2 else 1))
        else:
            frames.append(int(part))
preset = opt("--preset", "final")
pct = opt("--pct", None, int)
spp = opt("--spp", None, int)
threads = opt("--threads", 14, int)
outdir = os.path.join(cm.ROOT, opt("--out", "frames"))
tag = opt("--tag", "")
overwrite = "--overwrite" in argv
wait = "--wait" in argv
scale = opt("--scale", 4000.0, float)
os.makedirs(outdir, exist_ok=True)

# ---- art direction overrides (lighter, cleaner ivory lantern)
sl.IVORY = (1.00, 0.90, 0.76)
sl.AMBER = (0.92, 0.50, 0.22)
sl.BACKDROP_STRENGTH = 1.25
sl.build()
P = sl.configure_render(preset, threads=threads)
sc = bpy.context.scene
if pct: sc.render.resolution_percentage = pct
sc.cycles.seed = 7
try:
    sc.cycles.denoising_quality = 'BALANCED'
except Exception as e:
    print('denoise quality', e)

def log(*a):
    print("[render]", *a); sys.stdout.flush()

def out_path(f):
    return os.path.join(outdir, "f_%04d%s.png" % (f, tag))

t_all = time.time(); done = 0
resweep = wait and argv[0] == "planB" and not overwrite
while True:
    pending = 0; rendered = 0
    for f in frames:
        while os.path.exists(os.path.join(cm.ROOT, "work", "PAUSE_ALL")):
            time.sleep(15)
        out = out_path(f)
        lock = out + ".lock"
        need = shots.bake_spec(f) is not None
        vdb = os.path.join(film.VDB_DIR, "ink_%04d.vdb" % f)
        if not overwrite:
            if os.path.exists(out):
                continue
            if need and not os.path.exists(vdb):
                pending += 1
                continue
            try:
                fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY); os.close(fd)
            except FileExistsError:
                continue
        elif need and not os.path.exists(vdb):
            log("frame %d: VDB missing" % f); continue
        t0 = time.time()
        t = shots.sim_time(f)
        sl.apply_state(t)
        sl.set_ink(vdb if need else None, density_scale=scale)
        cam = shots.camera(f)
        sl.set_camera(cam["loc"], cam["look_at"], lens_mm=cam["lens_mm"], fstop=cam["fstop"], focus_dist=cam["focus_dist"])
        sh = shots.shot_of(f)
        sc.cycles.samples = spp if spp else sh.get("spp", P["samples"])
        rx = sh.get("resx", 1920)
        if not pct:
            sc.render.resolution_x = rx; sc.render.resolution_y = rx * 9 // 16
        sl.render_still(out)
        try: os.remove(lock)
        except OSError: pass
        done += 1; rendered += 1
        log("frame %d (%s, t=%.3f) %.1fs" % (f, sh["name"], t, time.time() - t0))
        if resweep:
            break          # start again at the top: freshly baked frames of important shots go first
    if resweep and rendered:
        continue
    if overwrite or not wait or pending == 0:
        break
    if rendered == 0:
        time.sleep(30)
log("done %d frames in %.0fs" % (done, time.time() - t_all))
