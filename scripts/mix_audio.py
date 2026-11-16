"""Build the 45 s soundtrack from the downloaded music + SFX with ffmpeg (no synthesis).
python mix_audio.py  ->  out/audio_mix.wav   (also prints the cue list)"""
import os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # project folder (parent of scripts/)
A = os.path.join(ROOT, "audio")
OUT = os.path.join(ROOT, "out"); os.makedirs(OUT, exist_ok=True)
DUR = 45.0
SR = 48000

def f(name):
    import glob
    g = glob.glob(os.path.join(A, "*", name + "*"))
    assert g, name
    return g[0]

# (file, start in film [s], gain dB, speed (pitch+tempo factor), trim (ss, t) inside the source or None, fade_in, fade_out, max length in film)
REVEAL = 22.5          # dragon fully formed / cut to the roar
IMPACT = 6.60          # drop touches the water
cues = [
    # --- music: track 1:18.0 (strongest hit) lands on the reveal
    ("music_01_RECOMMENDED", 0.0, -2.5, 1.0, (78.0 - REVEAL, DUR + 0.5), 1.2, 3.0, DUR),
    # --- room / calm
    ("drone_soft_tonal_wind_01", 0.0, -19, 1.0, (4.0, 11.0), 1.5, 3.0, 11.0),
    # --- impact (slow motion: pitched down)
    ("drop_plop_03", IMPACT - 0.03, -3, 0.62, None, 0.0, 0.3, 4.0),
    ("drop_stone_into_water_01", IMPACT, -8, 0.5, None, 0.0, 0.5, 4.0),
    ("water_impact_hydrophone_01", IMPACT + 0.02, -9, 0.5, None, 0.0, 0.3, 3.0),
    ("splash_small_02", IMPACT + 0.25, -15, 0.6, None, 0.05, 1.0, 5.0),
    ("ripples_bed_01", IMPACT + 0.3, -22, 1.0, (0.5, 4.5), 0.5, 1.5, 4.5),
    ("drop_plop_05", 9.20, -12, 0.7, None, 0.0, 0.3, 3.0),              # the rebound bead lands
    # --- under water
    ("underwater_bed_01", 10.2, -17, 1.0, (2.0, 33.0), 2.0, 4.0, 33.0),
    ("bubbles_01", 10.6, -18, 0.6, None, 0.1, 1.0, 6.0),
    ("water_swirl_small_01", 11.6, -13, 0.5, None, 0.1, 1.0, 5.0),
    ("bubbles_01", 13.8, -20, 0.5, None, 0.1, 1.0, 7.0),
    ("water_swirl_small_01", 15.2, -14, 0.45, None, 0.1, 1.0, 5.5),
    # --- the plume twists into the dragon
    ("riser_reverse_gong_01", REVEAL - 19.1, -9, 1.0, (0.0, 19.3), 2.0, 0.25, 19.3),
    ("whoosh_swirl_01", 19.4, -9, 0.7, None, 0.2, 0.8, 4.8),
    # --- reveal
    ("impact_trailer_boom_taiko_05", REVEAL - 0.02, -2, 1.0, None, 0.0, 2.0, 7.0),
    ("impact_boom_01", REVEAL, -7, 1.0, None, 0.0, 2.5, 7.5),
    ("impact_deep_tremor_04", REVEAL + 0.05, -10, 1.0, None, 0.05, 4.0, 13.0),
    ("creature_deep_sea_monster_04", REVEAL + 0.45, -7, 0.8, None, 0.15, 3.0, 8.5),
    ("whoosh_swirl_01", REVEAL + 1.1, -15, 0.6, None, 0.4, 1.6, 5.2),       # the ink breath of the roar
    # --- dragon alive: soft swirls on the cuts, a second low growl on the hero shot
    ("water_swirl_small_01", 25.9, -15, 0.55, None, 0.1, 1.0, 4.2),
    ("water_swirl_small_01", 28.9, -16, 0.5, None, 0.1, 1.0, 4.6),
    ("creature_growl_reverb_05", 31.5, -13, 0.75, None, 0.3, 3.0, 7.0),
    # --- dissolve + tail
    ("gong_tamtam_soft_02", 35.4, -10, 1.0, None, 0.02, 4.0, 9.6),
    ("shimmer_brightness_01", 35.6, -13, 1.0, None, 1.0, 4.0, 9.4),
    ("shimmer_singing_bell_05", 41.6, -9, 1.0, None, 0.02, 3.0, 3.4),
]

inputs = []; filt = []; labels = []
for i, (name, start, gain, speed, trim, fi, fo, maxlen) in enumerate(cues):
    inputs += ["-i", f(name)]
    ch = []
    if trim:
        ch.append("atrim=start=%.3f:duration=%.3f" % trim)
        ch.append("asetpts=PTS-STARTPTS")
    ch.append("aresample=%d" % SR)
    if speed != 1.0:
        ch.append("asetrate=%d" % int(SR * speed)); ch.append("aresample=%d" % SR)
    ch.append("aformat=channel_layouts=stereo")
    L = min(maxlen, DUR - start)
    ch.append("atrim=duration=%.3f" % L)
    if fi > 0: ch.append("afade=t=in:st=0:d=%.3f" % fi)
    if fo > 0: ch.append("afade=t=out:st=%.3f:d=%.3f" % (max(L - fo, 0), fo))
    ch.append("volume=%.2fdB" % gain)
    ch.append("adelay=%d:all=1" % int(max(start, 0) * 1000))
    filt.append("[%d:a]%s[a%d]" % (i, ",".join(ch), i)); labels.append("[a%d]" % i)
filt.append("%samix=inputs=%d:normalize=0:duration=longest,atrim=duration=%.2f,afade=t=in:st=0:d=0.4,afade=t=out:st=%.2f:d=2.6,volume=2.0dB,alimiter=limit=0.84:attack=5:release=80:level=disabled[out]"
            % ("".join(labels), len(labels), DUR, DUR - 2.6))
out = os.path.join(OUT, "audio_mix.wav")
cmd = ["ffmpeg", "-y", "-v", "error"] + inputs + ["-filter_complex", ";".join(filt), "-map", "[out]", "-ar", str(SR), "-c:a", "pcm_s16le", out]
subprocess.check_call(cmd)
print("wrote", out)
for c in cues:
    print("%6.2fs  %+5.1f dB  x%.2f  %s" % (c[1], c[2], c[3], c[0]))
