"""Assemble the film: stage frames (rendered, else detail-matched interpolated fill, else plain fill) -> per-shot
segments (900p shots upscaled to 1080p) -> concat -> finishing pass (curve, vignette, grain) + audio.
python assemble.py [--draft] [--allow-missing] [--threads 6]"""
import os, sys, subprocess, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common as cm
import shots

ROOT = cm.ROOT
FR = os.path.join(ROOT, "frames"); FILL = os.path.join(ROOT, "frames_fill")
FILL_SHARP = os.path.join(ROOT, "frames_fill_sharp")       # interpolated frames, detail-matched (match_fill.py)
OUT = os.path.join(ROOT, "out"); SEG = os.path.join(OUT, "segments"); STAGE = os.path.join(OUT, "stage")
for d in (SEG, STAGE):
    os.makedirs(d, exist_ok=True)
draft = "--draft" in sys.argv
allow_missing = "--allow-missing" in sys.argv
THREADS = sys.argv[sys.argv.index("--threads") + 1] if "--threads" in sys.argv else "6"   # keep the laptop responsive
# frame 675 (first frame of the roar close-up) was baked with a different surface-pool state than 676+:
# hold frame 676 for one frame instead (invisible right after the cut).
ALIAS = {}

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-2000:]); raise SystemExit("ffmpeg failed")

def source(f):
    f = ALIAS.get(f, f)
    for d in (FR, FILL_SHARP, FILL):
        p = os.path.join(d, "f_%04d.png" % f)
        if os.path.exists(p):
            return p, d != FR
    return None, False

n_fill = 0; missing = []
for f in range(cm.N_FRAMES):
    dst = os.path.join(STAGE, "f_%04d.png" % f)
    if os.path.exists(dst):
        os.remove(dst)
    src, is_fill = source(f)
    if src is None:
        missing.append(f); continue
    n_fill += is_fill
    try:
        os.link(src, dst)
    except OSError:
        shutil.copyfile(src, dst)
print("staged: %d rendered, %d interpolated, %d missing %s" % (cm.N_FRAMES - n_fill - len(missing), n_fill, len(missing), missing[:20]))
if missing and not allow_missing:
    raise SystemExit("frames missing")

segs = []
for s in shots.SHOTS:
    f0, f1 = s["f0"], s["f1"]
    n = f1 - f0
    if any(not os.path.exists(os.path.join(STAGE, "f_%04d.png" % f)) for f in range(f0, f1)):
        print("skip shot (incomplete):", s["name"]); continue
    out = os.path.join(SEG, s["name"] + ".mkv")
    vf = "scale=1920:1080:flags=lanczos"
    if s.get("resx", 1920) != 1920:
        vf += ",unsharp=5:5:0.45:5:5:0.0"
    run(["ffmpeg", "-y", "-v", "error", "-framerate", str(cm.FPS), "-start_number", str(f0), "-i", os.path.join(STAGE, "f_%04d.png"),
         "-frames:v", str(n), "-vf", vf, "-c:v", "libx264", "-qp", "0", "-preset", "veryfast", "-pix_fmt", "yuv444p",
         "-threads", THREADS, out])
    segs.append(out)
    print("segment", s["name"], n, "frames")

lst = os.path.join(SEG, "list.txt")
with open(lst, "w") as fh:
    for p in segs:
        fh.write("file '%s'\n" % p.replace("\\", "/"))
dur = sum(s["f1"] - s["f0"] for s in shots.SHOTS if os.path.join(SEG, s["name"] + ".mkv") in segs) / cm.FPS
audio = os.path.join(OUT, "audio_mix.wav")
final = os.path.join(OUT, "ink_dragon_draft.mp4" if draft else "ink_dragon_1080p30.mp4")
vf = ("curves=master='0/0 0.25/0.235 0.5/0.5 0.75/0.775 1/1',"
      "vignette=PI/5.2,"
      "noise=alls=3:allf=t+u,"
      "format=yuv420p")       # no fades: the last frame matches the first one (seamless loop)
cmd = ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-r", str(cm.FPS), "-i", lst]
has_audio = os.path.exists(audio) and len(segs) == len(shots.SHOTS)
if has_audio:
    cmd += ["-i", audio]
cmd += ["-vf", vf, "-c:v", "libx264", "-preset", "medium" if draft else "slow", "-crf", "20" if draft else "14",
        "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", str(cm.FPS), "-threads", THREADS, "-movflags", "+faststart",
        "-metadata", "title=Ink Dragon", "-metadata",
        "comment=Music: Cinematic Suspense Trailer - Extended Percussion Version by Gregor Quendel (CC BY 4.0). SFX: Freesound.org - hykenfreak, InspectorJ, EminYILDIRIM (CC BY 4.0) and CC0 contributors. See README.md"]
if has_audio:
    cmd += ["-c:a", "aac", "-b:a", "256k", "-shortest"]
cmd += [final]
run(cmd)
print("wrote", final, "%.2f s" % dur, "(with audio)" if has_audio else "(no audio: incomplete cut)")
