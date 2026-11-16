# Audio credits: ink-dragon short (45 s)

Every file here was downloaded from a free-audio source whose license allows use in a video. Nothing was synthesized locally. The only licenses are **CC0**, **CC BY 3.0** and **CC BY 4.0**; there is no NC, ND or SA material. Each file was checked with `ffprobe` (it is real audio, not an HTML error page) and with `ffmpeg volumedetect`.

**How these were judged:** I (the sourcing agent) cannot listen to audio. My judgements come from three things: (1) the title, the uploader's description and the tags; (2) measurements I took myself with ffmpeg `ebur128`/`astats` and librosa: loudness over time, low-band (<150 Hz) energy, spectral centroid, onset density, transient "hit" detection, and a pitch-class histogram; (3) license text read on each source page. Instrument names come from the publisher's metadata, not from listening. Please audition before you lock the cut.

---

## Recommended picks

**Music: `music/music_01_RECOMMENDED_quendel_cinematic_suspense_trailer_extended_percussion_oga.mp3`** (Gregor Quendel, CC BY 4.0, 1:50)
It is the only candidate whose own dynamics follow the film with no edits. Play the window **0:55 → 1:40** against film **0 → 45 s**:
a quiet, sparse pulse for the calm glass; a small lift at ~1:02 (film 7, the impact); an accent at 1:10.3 (film 15, plume); a short dip at 1:14-1:16 (film 19-21, the "inhale"); **the loudest hit of the whole track at 1:18.0, which lands on film 23.0 (the dragon reveal)**; the loudest section 1:18-1:33 (film 23-38); percussion stops at ~1:34 (film 39, the dissolve); then a low, decaying tail. An even quieter opening exists at 0:02-0:12 if you prefer to cut.
For East Asian colour, layer the SFX below (taiko boom, tam-tam, reverse gong, singing bowl). `music_05` (pentatonic guzheng/koto) is also available as a quiet bed under the opening and the final haze.

**SFX, best file per slot:**

| Slot | Best pick | Alternatives |
|---|---|---|
| Drop / plop (impact at ~7 s) | `sfx/drop_plop_03_freesound_683102.mp3` (real, extremely clean), layered with `sfx/drop_stone_into_water_01_freesound_420227.mp3` pitched down for weight | `drop_plop_11_on_water_…16746`, `drop_plop_01_…174718` (classic rising "bloop", made by mouth), `drop_plop_05_…536113`, `drop_plop_10_…267221`, `drop_plop_09_…273870`, `drop_plop_04_object_in_water_…272392`, `drop_plop_06_…191678` (synthesized by its uploader) |
| Underwater view of the impact | `sfx/water_impact_hydrophone_01_freesound_718503.mp3` | `bubbles_02_pool_…208816` (has real underwater impacts) |
| Small splash / ripples (7-11 s) | `sfx/splash_small_02_freesound_416710.mp3` | `splash_small_01_…398032`; ripples bed `ripples_bed_01_…648332` |
| Tendrils / plume swirl (11-18 s) | `sfx/water_swirl_small_01_freesound_398710.mp3` (pitch down) | `water_swirl_02_…400346` |
| Underwater bed (11-42 s) | `sfx/underwater_bed_01_freesound_504641.mp3` | `underwater_bed_03_deepsea_…193822` (110 s, sub only), `underwater_bed_02_…567347`, `underwater_bed_04_…179927` |
| Bubbles | `sfx/bubbles_01_freesound_539823.mp3` | `bubbles_03_underwater_…173439`, `bubbles_02_pool_…208816` |
| Riser / swirl build (18-23 s) | `sfx/riser_reverse_gong_01_freesound_160359.mp3` (East Asian colour; the swell peaks at 19.1 s, so start the file at film ~3.9 s or trim its head) plus `sfx/whoosh_swirl_01_freesound_877983.mp3` for the twist | `riser_02_…334525` (peaks at its very end, 8 s), `reverse_cymbal_01_…383903`, `riser_03_horror_whoosh_…494981`, `riser_01_simple_…840719` |
| Reveal hit (~23 s) | `sfx/impact_trailer_boom_taiko_05_freesound_207755.mp3` (a real 30-inch taiko made into a trailer boom), with `sfx/impact_boom_01_freesound_255111.mp3` under it | `taiko_hit_03_41hz_…584131`, `impact_cinematic_02_…177242`, `impact_dramatic_hit_03_…222517`, `gong_massive_01_…260972` (tam-tam crash layer) |
| Sub rumble under the dragon | `sfx/impact_deep_tremor_04_freesound_119782.mp3` | `creature_low_rumble_03_…132873` |
| Dragon growl (mix low, pitch down) | `sfx/creature_deep_sea_monster_04_freesound_341173.mp3` | `creature_growl_reverb_05_…366672`, `creature_growl_deep_01_…222523`, `creature_growl_deep_02_…368255`, `creature_dragon_roars_pack_06_…479380` (60 s of material) |
| Shimmer / dissolve (36-42 s) | `sfx/shimmer_brightness_01_freesound_632762.mp3` | `shimmer_sparkle_flourish_02_…844398`, `shimmer_magic_aura_03_…547365` (reverse it), `reverse_cymbal_02_reverb_…244868` |
| Calm tail / final haze (42-45 s) | `sfx/shimmer_singing_bell_05_freesound_202017.mp3` (singing bowl, 43 s ring) or `sfx/gong_tamtam_soft_02_freesound_423477.mp3` | `shimmer_singing_bowl_strike_04_…271370` |
| Room tone / low drone | `sfx/drone_soft_tonal_wind_01_freesound_397091.mp3` | `drone_space_02_…20705`, `roomtone_apartment_01_…426767` |

### Attribution you must show (on-screen credits or the video description)
CC0 files need no credit, though listing them is polite. **These files require credit:**

- Music: "Cinematic Suspense Trailer - Extended Percussion Version", "Cinematic Action Percussion Trailer" and "Cinematic Oriental Trailer - II" by Gregor Quendel (www.gregorquendel.com), CC BY 4.0, via OpenGameArt.org. Credit only the ones you use.
- Music, Incompetech's required wording, one block per track you use:
  `"Big Mojo" Kevin MacLeod (incompetech.com)` / `Licensed under Creative Commons: By Attribution 4.0` / `https://creativecommons.org/licenses/by/4.0/`
  `"Ripples" Kevin MacLeod (incompetech.com)` / `Licensed under Creative Commons: By Attribution 4.0` / `https://creativecommons.org/licenses/by/4.0/`
- SFX (Freesound, CC BY): see the per-file entries below and credit those you use, in the form *"Title" by Author (freesound.org), CC BY 4.0* (CC BY 3.0 for `riser_03`). Candidates that need credit: EminYILDIRIM, Porphyr, InspectorJ (x2), harrietniamh, duckduckpony, original_sound, hykenfreak, sandyrb, tarane468, gkillhour, kijjaz.

A suggested single credit block, if you use the recommended picks (music_01, taiko boom, swirl, splash_small_02):
```
Music: "Cinematic Suspense Trailer - Extended Percussion Version" by Gregor Quendel (gregorquendel.com) - CC BY 4.0
Sound effects from Freesound.org: "Movie Trailer Boom" by hykenfreak, "Water Swirl, Small, 8.wav" and "Splash, Small, A.wav" by InspectorJ - CC BY 4.0;
additional CC0 sounds by florianreichelt, 14FPanska_Nemec_Petr, InMotionAudio, rhapsodize, swiftoid, cylon8472, godspine, Qvantor, Fission9, ristooooo1, sonically_sound, ryancacophony, janbezouska.
CC BY 4.0: https://creativecommons.org/licenses/by/4.0/
```

---

## MUSIC

Timestamps are mm:ss in the track. The "S" values are EBU R128 short-term loudness (LUFS), measured on these exact files. The "hit" times come from transient detection: a >9 dB jump in energy over the preceding 1.5 s.

### music_01_RECOMMENDED_quendel_cinematic_suspense_trailer_extended_percussion_oga.mp3
- **Title:** Cinematic Suspense Trailer - Extended Percussion Version (track "Variations 05" of *Cinematic Trailer Music - Collection*)
- **Author:** Gregor Quendel (www.gregorquendel.com)
- **Source page:** https://opengameart.org/content/cinematic-trailer-music-collection
- **Direct download:** https://opengameart.org/sites/default/files/gregor_quendel_-_cinematic_trailer_music_-_variations_-_05_-_cinematic_suspense_trailer_-_extended_percussion_version.mp3
- **License:** CC BY 4.0, https://creativecommons.org/licenses/by/4.0/. The page's attribution notice reads "www.gregorquendel.com".
- **Duration / format:** 1:50.0 (109.99 s), mp3 44.1 kHz stereo 192 kbps, integrated -19.6 LUFS, loudness range 17.8 LU (very dynamic). Peak -5.3 dBFS.
- **Structure (measured):**
  - 0:00 a single low boom, then **0:02-0:12 near-silence / very sparse** (S ≈ -38 to -33).
  - 0:14-0:16 first swell (-27). 0:18-0:20 dip. **0:22 low hit**, then 0:26-0:28 dip.
  - **0:30.0 big hit**, opening the first full section, 0:30-0:50 (S ≈ -16 to -20), with an accent at 0:38.
  - 0:50-0:54 drop-out into a quieter middle, **0:54-1:08** (S ≈ -27 to -29), with a steady light percussion pulse.
  - **1:10.3 hit**; 1:14-1:16 short dip.
  - **1:18.0 the strongest hit in the track** (+11 dB jump, big low end). The loudest section runs 1:18-1:33 (S ≈ -15.5 to -18), and the mix is brighter there.
  - ~1:34 percussion stops; low, sustained material decays 1:34-1:45 (S -18 → -27).
  - Fade by 1:47; the file ends at 1:50.
- **Fit:** Dark trailer suspense. Window 0:55-1:40 maps one-to-one onto the film (see Recommended picks). Alternative: the window starting at 0:07 puts the 0:30 hit on film 23 and gives a quieter opening, but its loud section lasts to 0:50 (film 43), so the dissolve would need a cut or a fade. Instrumentation is not listed by the publisher; from the analysis it is orchestral/hybrid with percussion and low booms. There is no sign of vocals in the title or description, but I could not confirm this by ear.

### music_02_quendel_cinematic_action_percussion_trailer_oga.mp3
- **Title:** Cinematic Action Percussion Trailer (track 03 of *Cinematic Trailer Music - Collection*; the same piece is track 04 of the *Free Cinematic Trailer Music* pack, which is mastered ~5 dB louder)
- **Author:** Gregor Quendel (www.gregorquendel.com)
- **Source page:** https://opengameart.org/content/cinematic-trailer-music-collection (also https://opengameart.org/content/free-cinematic-trailer-music)
- **Direct download:** https://opengameart.org/sites/default/files/gregor_quendel_-_cinematic_trailer_music_-_03_-_cinematic_action_percussion_trailer.mp3
- **License:** CC BY 4.0, https://creativecommons.org/licenses/by/4.0/
- **Duration / format:** 1:18.0, mp3 44.1 kHz stereo 192 kbps, integrated -15.1 LUFS, LRA 19.1 LU. Peak -4.9 dBFS.
- **Structure (measured):**
  - **0:00-0:09 quiet, sparse intro.**
  - **0:10-0:28 a textbook steady crescendo**: level rises ~20 dB and onset density climbs from ~0.5 to 4.5 per second.
  - **~0:28 full arrival.** 0:28-0:58 loud, dense percussion (~6 onsets/s, heavy sub); loudest moments 0:50-0:58.
  - **~0:59-1:00 sudden drop** of ~8 dB into a lighter, still-pulsing outro, 1:00-1:13.
  - Ends at ~1:14.
- **Fit:** The clearest "build → arrival" curve. Start the track at film -5 s (track 0:05 = film 0) so the arrival at 0:28 lands on film 23. For the dissolve, either fade from film ~36 or cut to the 1:00 outro. It is the busiest and most "action" of the four, with less of the "clean" quality the brief asks for.

### music_03_kevin_macleod_big_mojo_incompetech.mp3
- **Title:** Big Mojo
- **Author:** Kevin MacLeod (incompetech.com)
- **Source page:** https://incompetech.com/music/royalty-free/index.html?isrc=USUAN1100306 (catalogue entry; Incompetech's own data lists instruments: Percussion, Koto, Strings, Flute, Misc Orchestral, Electronic; feel: Action, Dark, Driving, Epic, Grooving, Intense, Mystical; 171 bpm)
- **Direct download:** https://incompetech.com/music/royalty-free/mp3-royaltyfree/Big%20Mojo.mp3
- **License:** CC BY 4.0, https://creativecommons.org/licenses/by/4.0/ (as stated in the Incompetech FAQ, https://incompetech.com/music/royalty-free/faq.html). Required credit: `"Big Mojo" Kevin MacLeod (incompetech.com) Licensed under Creative Commons: By Attribution 4.0 https://creativecommons.org/licenses/by/4.0/`
- **Duration / format:** 2:37.2, mp3 48 kHz stereo 320 kbps (also carries embedded cover art, which is harmless). Integrated -20.5 LUFS, LRA 19.8 LU.
- **Structure (measured):**
  - **0:00-0:31 a near-silent, filtered intro** (the composer calls it "high and low shelves"). RMS rises slowly from -65 to -46 dB, with almost no sub. It is very quiet; boost it if you want it audible.
  - **0:32.0 a full-range drop** with a "massive bass kick" (low band jumps ~35 dB).
  - From 0:35, a kick about every 2.8 s (0:35.1, 0:37.9, 0:40.8, …) and a steady driving groove at RMS -24 to -28.
  - ~1:18-1:22 a brief thinner breakdown.
  - The groove continues to a big ending at ~2:30-2:37, with no calm tail.
- **Fit:** The East Asian colour comes from the publisher's instrument list (koto, flute). However, its pitch content after the drop is not pentatonic (fairly chromatic: D, C#, D#, E, C, F), so the "Asian" flavour may be mild. Start at track 0:09 so the drop at 0:32 lands on film 23; fade out from film ~36. Risk: it is a groove, so it may feel more "driving" than "elegant".

### music_04_quendel_cinematic_oriental_trailer_ii_oga.mp3   (note: 57 s, just under the 60 s minimum)
- **Title:** Cinematic Oriental Trailer - II (track 09 of *Cinematic Trailer Music - Collection*; track 12 of the *Free Cinematic Trailer Music* pack)
- **Author:** Gregor Quendel (www.gregorquendel.com)
- **Source page:** https://opengameart.org/content/cinematic-trailer-music-collection
- **Direct download:** https://opengameart.org/sites/default/files/gregor_quendel_-_cinematic_trailer_music_-_09_-_cinematic_oriental_trailer_-_ii.mp3
- **License:** CC BY 4.0, https://creativecommons.org/licenses/by/4.0/
- **Duration / format:** 0:57.0, mp3 44.1 kHz stereo 192 kbps, integrated -16.6 LUFS, LRA 8.3 LU. Peak -5.3 dBFS.
- **Structure (measured):**
  - 0:00 a low hit, then **0:02-0:30 a steady full section** (not a quiet intro), with drum accents around 0:10 and 0:16. It is brighter and thinner from 0:20.
  - **0:30-0:32 a dip / breath.**
  - **0:34-0:46 the climax**, loudest at 0:40-0:44 (very bright, little sub) with a dense passage at 0:44-0:46.
  - 0:48 a last low hit, then a **decay to silence by 0:52**.
- **Fit:** This is the only candidate whose pitch content looks genuinely East Asian. The dominant pitch classes are C, F, C#, D#, F#, A#, which matches a Japanese in/iwato-type mode (C-Db-F-Gb-Bb) better than any Western scale; I inferred this from analysis, not by ear. Suggested sync: track 0:11 = film 0, which puts the 0:30-0:32 breath at film 19-21, the climax onset at 0:34 on film 23, and the decay to silence at film 39-41. Leave film 42-45 to the singing bowl or haze SFX. It has no quiet opening, so fade it in from about film 4.

### music_05_optional_layer_kevin_macleod_ripples_guzheng_incompetech.mp3   (optional layer, not a full score)
- **Title:** Ripples
- **Author:** Kevin MacLeod (incompetech.com)
- **Source page:** https://incompetech.com/music/royalty-free/index.html?isrc=USUAN1100691
- **Direct download:** https://incompetech.com/music/royalty-free/mp3-royaltyfree/Ripples.mp3
- **License:** CC BY 4.0, https://creativecommons.org/licenses/by/4.0/ (Incompetech FAQ). Required credit: `"Ripples" Kevin MacLeod (incompetech.com) Licensed under Creative Commons: By Attribution 4.0 https://creativecommons.org/licenses/by/4.0/`
- **Duration / format:** 3:25.5, mp3 44.1 kHz stereo 320 kbps, integrated -17.8 LUFS, fairly even throughout (S -16 to -25). Starts at ~0:01, ends ~3:18.
- **What it is:** A solo plucked zither, which Incompetech lists as koto and describes as "Chinese guzheng", at 57 bpm, "flowing like water". It has no build and no climax. Its pitch content is cleanly major/minor pentatonic (E, D, G, A, C = 83% of the energy), which is the most clearly East Asian sound in the set.
- **Use:** Lay it quietly under the calm glass (0-7 s) and the final haze (42-45 s), or under the dissolve, alongside music_01. Any 10-20 s stretch works because it is even throughout.

---

## SOUND EFFECTS (all from Freesound.org)

Freesound serves these "HQ previews" (variable-bitrate mp3, the original sample rate kept) without a login. The original uploads (wav/aiff/flac) need a free account, which I did not create, so these are the mp3 previews. Every license below was read from the sound's own Freesound page. Durations come from ffprobe. "Level" is the ffmpeg `volumedetect` mean/max.

### Water drop / plop
- **`sfx/drop_plop_01_freesound_174718.mp3`**: "Single Water Drop" by **paespedro**  
  Page: https://freesound.org/people/paespedro/sounds/174718/  
  Direct: https://cdn.freesound.org/previews/174/174718_1850811-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  0.47 s, 44.1 kHz, stereo, 162 kbps mp3; level mean -23.8 / max -2.0 dB  
  Very clean, warm 'bloop' (~0.4 kHz body whose pitch rises, the classic plop shape). Made with mouth and hands, not real water, but sounds like a drop. Pitch it down for the slow-motion impact at ~7 s.
- **`sfx/drop_plop_03_freesound_683102.mp3`**: "water drop" by **florianreichelt**  
  Page: https://freesound.org/people/florianreichelt/sounds/683102/  
  Direct: https://cdn.freesound.org/previews/683/683102_6253486-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  1.67 s, 48 kHz, stereo, 173 kbps mp3; level mean -27.6 / max -0.3 dB  
  Real water drop, extremely clean (noise floor about -86 dB below peak). Short, bright 'tip' at ~0.8-1 kHz. Best clean drop for the moment of impact at ~7 s. The 1.6 s file has silence after the drop.
- **`sfx/drop_plop_04_object_in_water_freesound_272392.mp3`**: "Object Drops In Water.wav" by **danhelbling**  
  Page: https://freesound.org/people/danhelbling/sounds/272392/  
  Direct: https://cdn.freesound.org/previews/272/272392_4783367-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  1.30 s, 48 kHz, stereo, 220 kbps mp3; level mean -34.5 / max -5.8 dB  
  A small object dropping into water: plop plus a little splash. The hit starts ~0.45 s into the file and the noise floor is moderate. Gives the impact more body and wetness.
- **`sfx/drop_plop_05_freesound_536113.mp3`**: "Water Drop Single" by **EminYILDIRIM**  
  Page: https://freesound.org/people/EminYILDIRIM/sounds/536113/  
  Direct: https://cdn.freesound.org/previews/536/536113_10912485-hq.mp3  
  License: CC BY 4.0 (attribution required), https://creativecommons.org/licenses/by/4.0/  
  1.57 s, 44.1 kHz, stereo, 198 kbps mp3; level mean -34.6 / max -5.8 dB  
  Single water drop with a bright ~1.4-1.6 kHz tone, clean. An alternative impact transient.
- **`sfx/drop_plop_06_freesound_191678.mp3`**: "Waterdrop" by **Porphyr**  
  Page: https://freesound.org/people/Porphyr/sounds/191678/  
  Direct: https://cdn.freesound.org/previews/191/191678_3464493-hq.mp3  
  License: CC BY 4.0 (attribution required), https://creativecommons.org/licenses/by/4.0/  
  0.62 s, 48 kHz, stereo, 190 kbps mp3; level mean -27.2 / max -10.3 dB  
  Smooth round 'bloop', SYNTHESIZED by the uploader on a modular synth (fetched, not made by us, but not an acoustic recording). Very clean. Use only if you want a stylised drop.
- **`sfx/drop_plop_09_freesound_273870.mp3`**: "water drop 1.aif" by **beskhu**  
  Page: https://freesound.org/people/beskhu/sounds/273870/  
  Direct: https://cdn.freesound.org/previews/273/273870_1031833-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  0.38 s, 44.1 kHz, stereo, 244 kbps mp3; level mean -29.4 / max -0.7 dB  
  Short real drip (~0.4 s) at ~1.1 kHz. Small and dry.
- **`sfx/drop_plop_10_freesound_267221.mp3`**: "Water Droplet.wav" by **gkillhour**  
  Page: https://freesound.org/people/gkillhour/sounds/267221/  
  Direct: https://cdn.freesound.org/previews/267/267221_3112522-hq.mp3  
  License: CC BY 4.0 (attribution required), https://creativecommons.org/licenses/by/4.0/  
  0.50 s, 44.1 kHz, mono, 240 kbps mp3; level mean -28.0 / max -3.3 dB  
  Single real droplet (~0.5 s) at ~0.84 kHz, recorded on a Yeti mic. Light and clean.
- **`sfx/drop_plop_11_on_water_freesound_16746.mp3`**: "water drop-01.aif" by **kijjaz**  
  Page: https://freesound.org/people/kijjaz/sounds/16746/  
  Direct: https://cdn.freesound.org/previews/16/16746_26950-hq.mp3  
  License: CC BY 4.0 (attribution required), https://creativecommons.org/licenses/by/4.0/  
  1.33 s, 44.1 kHz, stereo, 204 kbps mp3; level mean -43.9 / max -14.3 dB  
  Hand-made drop onto sink water, with a nice 'bouncing' resonance. Extremely quiet noise floor; needs a gain lift (peaks at -14 dB). A good natural plop.
- **`sfx/drop_stone_into_water_01_freesound_420227.mp3`**: "37 - 2 Water drop - stone.WAV" by **14FPanska_Nemec_Petr**  
  Page: https://freesound.org/people/14FPanska_Nemec_Petr/sounds/420227/  
  Direct: https://cdn.freesound.org/previews/420/420227_8375530-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  1.46 s, 48 kHz, stereo, 219 kbps mp3; level mean -33.2 / max -6.4 dB  
  Stone dropped into water: deeper (~220 Hz) plop-and-splash, very clean. Layer it under a bright drop, or pitch it down, to give the slow-motion impact weight.
- **`sfx/water_impact_hydrophone_01_freesound_718503.mp3`**: "WATRImpt_Impact12_InMotionAudio_FREESampleSunday" by **InMotionAudio**  
  Page: https://freesound.org/people/InMotionAudio/sounds/718503/  
  Direct: https://cdn.freesound.org/previews/718/718503_14083205-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  0.65 s, 48 kHz, stereo, 200 kbps mp3; level mean -29.8 / max -1.1 dB  
  Professional water-impact one-shot from InMotionAudio's free 'Sample Sunday' (tags mention hydrophone/underwater). Very clean, 0.65 s. Use for the below-surface view of the impact at ~7 s.

### Splash / ripples / swirl
- **`sfx/splash_small_01_freesound_398032.mp3`**: "Splash" by **swordofkings128**  
  Page: https://freesound.org/people/swordofkings128/sounds/398032/  
  Direct: https://cdn.freesound.org/previews/398/398032_7586736-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  1.33 s, 44.1 kHz, stereo, 165 kbps mp3; level mean -26.7 / max -0.3 dB  
  Hand splashing into a pool: bright small splash, 1.3 s. For the macro crown splash at 7-11 s; slowing it down works well.
- **`sfx/splash_small_02_freesound_416710.mp3`**: "Splash, Small, A.wav" by **InspectorJ**  
  Page: https://freesound.org/people/InspectorJ/sounds/416710/  
  Direct: https://cdn.freesound.org/previews/416/416710_5121236-hq.mp3  
  License: CC BY 4.0 (attribution required), https://creativecommons.org/licenses/by/4.0/  
  3.49 s, 44.1 kHz, stereo, 207 kbps mp3; level mean -37.0 / max -4.3 dB  
  Small splash (a water-filled toy thrown into a pool) with drips and a tail, 3.5 s, lightly EQ-cleaned. For the macro splash at 7-11 s.
- **`sfx/water_swirl_02_freesound_400346.mp3`**: "Water Swirl" by **harrietniamh**  
  Page: https://freesound.org/people/harrietniamh/sounds/400346/  
  Direct: https://cdn.freesound.org/previews/400/400346_4061049-hq.mp3  
  License: CC BY 4.0 (attribution required), https://creativecommons.org/licenses/by/4.0/  
  1.80 s, 48 kHz, stereo, 198 kbps mp3; level mean -36.8 / max -14.4 dB  
  Hand drawn through bath water, 1.8 s, soft. A second swirl layer.
- **`sfx/water_swirl_small_01_freesound_398710.mp3`**: "Water Swirl, Small, 8.wav" by **InspectorJ**  
  Page: https://freesound.org/people/InspectorJ/sounds/398710/  
  Direct: https://cdn.freesound.org/previews/398/398710_5121236-hq.mp3  
  License: CC BY 4.0 (attribution required), https://creativecommons.org/licenses/by/4.0/  
  2.34 s, 44.1 kHz, stereo, 217 kbps mp3; level mean -32.0 / max -8.3 dB  
  Close-miked (15 cm) hands swirling water in a pool, 2.3 s. Good for the plume and tendrils unfurling (11-18 s), and for the twist (18-23 s) when pitched down.
- **`sfx/ripples_bed_01_freesound_648332.mp3`**: "Rippling water natural souce.wav" by **Rimmer**  
  Page: https://freesound.org/people/Rimmer/sounds/648332/  
  Direct: https://cdn.freesound.org/previews/648/648332_11944544-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  14.22 s, 44.1 kHz, stereo, 212 kbps mp3; level mean -49.4 / max -19.4 dB  
  Gentle natural rippling water, 14 s, very quiet (mean -49 dB, needs gain). A calm surface bed for 0-4 s and 42-45 s.

### Underwater ambience and bubbles
- **`sfx/underwater_bed_01_freesound_504641.mp3`**: "Underwater Ambience" by **Fission9**  
  Page: https://freesound.org/people/Fission9/sounds/504641/  
  Direct: https://cdn.freesound.org/previews/504/504641_9395330-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  46.86 s, 48 kHz, stereo, 174 kbps mp3; level mean -22.2 / max -10.4 dB  
  Designed 'deep ocean' ambience (slowed-down drink-can noises), 47 s, deep and muffled. Top pick for the underwater bed from 11-42 s.
- **`sfx/underwater_bed_02_freesound_567347.mp3`**: "Underwater ambience.wav" by **Merrick079**  
  Page: https://freesound.org/people/Merrick079/sounds/567347/  
  Direct: https://cdn.freesound.org/previews/567/567347_12735833-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  44.00 s, 48 kHz, stereo, 215 kbps mp3; level mean -16.6 / max -3.8 dB  
  Underwater ambience, 44 s, hotter level (mean -16.6 dB). Alternative bed.
- **`sfx/underwater_bed_03_deepsea_freesound_193822.mp3`**: "Deep Sea Ambience" by **jhumbucker**  
  Page: https://freesound.org/people/jhumbucker/sounds/193822/  
  Direct: https://cdn.freesound.org/previews/193/193822_208303-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  109.57 s, 48 kHz, stereo, 190 kbps mp3; level mean -30.1 / max -12.1 dB  
  Low-pitched deep-sea ambience, 110 s. Dark sub bed. A good long option if you want only low end.
- **`sfx/underwater_bed_04_freesound_179927.mp3`**: "underwater" by **yosarrian**  
  Page: https://freesound.org/people/yosarrian/sounds/179927/  
  Direct: https://cdn.freesound.org/previews/179/179927_3346789-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  28.25 s, 44.1 kHz, mono, 176 kbps mp3; level mean -24.7 / max -6.3 dB  
  Real underwater recording with movement and activity, mono, 28 s. Busier than the others.
- **`sfx/bubbles_01_freesound_539823.mp3`**: "Bubbles 001.wav" by **ristooooo1**  
  Page: https://freesound.org/people/ristooooo1/sounds/539823/  
  Direct: https://cdn.freesound.org/previews/539/539823_6205597-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  4.80 s, 48 kHz, mono, 208 kbps mp3; level mean -32.1 / max -9.8 dB  
  Bubbling, 4.8 s, mono. For bubbles trailing the drop after impact.
- **`sfx/bubbles_02_pool_freesound_208816.mp3`**: "Aquatic sound of some bubble in a swimming pool (underwater recording)" by **felix.blume**  
  Page: https://freesound.org/people/felix.blume/sounds/208816/  
  Direct: https://cdn.freesound.org/previews/208/208816_1661766-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  33.32 s, 48 kHz, stereo, 188 kbps mp3; level mean -20.6 / max -0.8 dB  
  Real underwater recording (Zoom H4n in a pool): bubbles plus a few water impacts, 33 s. Natural underwater perspective. Pick sections.
- **`sfx/bubbles_03_underwater_freesound_173439.mp3`**: "SFX_UnderWater" by **Perel**  
  Page: https://freesound.org/people/Perel/sounds/173439/  
  Direct: https://cdn.freesound.org/previews/173/173439_910681-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  5.59 s, 44.1 kHz, stereo, 144 kbps mp3; level mean -39.9 / max -25.6 dB  
  Short loopable underwater bubbles, 5.6 s, quiet.

### Whoosh / swirl / riser
- **`sfx/whoosh_02_freesound_683096.mp3`**: "Woosh" by **florianreichelt**  
  Page: https://freesound.org/people/florianreichelt/sounds/683096/  
  Direct: https://cdn.freesound.org/previews/683/683096_6253486-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  1.72 s, 48 kHz, stereo, 186 kbps mp3; level mean -25.7 / max -10.6 dB  
  Low, soft 'woosh' (mostly under 200 Hz), 1.7 s. A subtle body whoosh for camera moves or angle cuts (23-36 s).
- **`sfx/whoosh_swirl_01_freesound_877983.mp3`**: "Whoosh Swirl Spinning" by **Qvantor**  
  Page: https://freesound.org/people/Qvantor/sounds/877983/  
  Direct: https://cdn.freesound.org/previews/877/877983_19512113-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  3.32 s, 48 kHz, stereo, 182 kbps mp3; level mean -26.0 / max -1.3 dB  
  Synth whoosh that spins around the listener and pans faster as it swells, 3.3 s. Ideal for the plume twisting into the dragon (18-23 s).
- **`sfx/whoosh_swirling_wind_03_freesound_130509.mp3`**: "Swirling Wind.wav" by **duckduckpony**  
  Page: https://freesound.org/people/duckduckpony/sounds/130509/  
  Direct: https://cdn.freesound.org/previews/130/130509_1653827-hq.mp3  
  License: CC BY 4.0 (attribution required), https://creativecommons.org/licenses/by/4.0/  
  6.29 s, 44.1 kHz, stereo, 185 kbps mp3; level mean -46.2 / max -28.0 dB  
  Swirling, spinning wind, 6.3 s, quiet (needs gain). An airy spiral texture for the twist or the dissolve.
- **`sfx/riser_01_simple_freesound_840719.mp3`**: "Simple Riser" by **SoundEffectsForAll**  
  Page: https://freesound.org/people/SoundEffectsForAll/sounds/840719/  
  Direct: https://cdn.freesound.org/previews/840/840719_17848526-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  3.59 s, 48 kHz, stereo, 174 kbps mp3; level mean -21.6 / max -0.4 dB  
  Short suspense riser, 3.6 s: swells from ~1.6 s to a peak at ~2.9 s, then stops. Made from a tool thrown onto a metal table.
- **`sfx/riser_02_freesound_334525.mp3`**: "rise5.wav" by **soneproject**  
  Page: https://freesound.org/people/soneproject/sounds/334525/  
  Direct: https://cdn.freesound.org/previews/334/334525_2127539-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  8.00 s, 44.1 kHz, stereo, 202 kbps mp3; level mean -23.0 / max -1.5 dB  
  8 s bright noise riser that peaks at the very end (7.9 s). Line up its end with the 23 s reveal (start it at ~15 s).
- **`sfx/riser_03_horror_whoosh_freesound_494981.mp3`**: "Risers - Horror Whooshes Tension Builder 1.mp3" by **original_sound**  
  Page: https://freesound.org/people/original_sound/sounds/494981/  
  Direct: https://cdn.freesound.org/previews/494/494981_6687700-hq.mp3  
  License: CC BY 3.0 (attribution required), http://creativecommons.org/licenses/by/3.0/  
  4.51 s, 44.1 kHz, stereo, 185 kbps mp3; level mean -23.1 / max -3.4 dB  
  Horror whoosh / tension builder, 4.5 s, peaking at ~2.2 s. Darker and more 'sucking'.
- **`sfx/riser_reverse_gong_01_freesound_160359.mp3`**: "Reverse Gong.wav" by **godspine**  
  Page: https://freesound.org/people/godspine/sounds/160359/  
  Direct: https://cdn.freesound.org/previews/160/160359_2866962-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  20.02 s, 44.1 kHz, stereo, 179 kbps mp3; level mean -21.0 / max -0.6 dB  
  Reverse gong, 20 s: rises slowly from -42 dB and climbs steeply over the last ~6-8 s to peak at ~19 s, then cuts. Adds East Asian colour and is the best riser for 18-23 s. Start the file at about film 3.9 s so the peak lands at 23 s, or trim the quiet head.
- **`sfx/reverse_cymbal_01_freesound_383903.mp3`**: "Reverse Crash Cymbal Projection" by **deleted_user_7146007**  
  Page: https://freesound.org/people/deleted_user_7146007/sounds/383903/  
  Direct: https://cdn.freesound.org/previews/383/383903_7146007-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  8.92 s, 48 kHz, stereo, 151 kbps mp3; level mean -23.0 / max -0.0 dB  
  Reverse crash cymbal with a smooth rise from -61 dB to -5.5 dB over 8.9 s. Trim the head for a 3-5 s riser, or use it whole as a long swell.
- **`sfx/reverse_cymbal_02_reverb_freesound_244868.mp3`**: "Rev Cymb 18 reverb.wav" by **JarredGibb**  
  Page: https://freesound.org/people/JarredGibb/sounds/244868/  
  Direct: https://cdn.freesound.org/previews/244/244868_4056007-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  12.00 s, 48 kHz, stereo, 50 kbps mp3; level mean -27.0 / max 0.0 dB  
  Short reverse cymbal with reverb: only ~2 s of audio, then digital silence until 12 s. For quick swells into angle cuts.

### Impact / sub boom / taiko / gong
- **`sfx/impact_boom_01_freesound_255111.mp3`**: "Cinematic_Boom_Rhapsodize.wav" by **rhapsodize**  
  Page: https://freesound.org/people/rhapsodize/sounds/255111/  
  Direct: https://cdn.freesound.org/previews/255/255111_2472317-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  7.73 s, 44.1 kHz, stereo, 176 kbps mp3; level mean -19.0 / max -0.3 dB  
  Low, gut-wrenching trailer boom with some mid resonance so it carries on small speakers. 7.7 s, decays in ~2 s. Top pick for the dragon reveal at ~23 s.
- **`sfx/impact_cinematic_02_freesound_177242.mp3`**: "Cinematic Impact" by **deleted_user_3277771**  
  Page: https://freesound.org/people/deleted_user_3277771/sounds/177242/  
  Direct: https://cdn.freesound.org/previews/177/177242_3277771-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  7.92 s, 48 kHz, stereo, 184 kbps mp3; level mean -17.8 / max -3.0 dB  
  Layered cinematic impact with a short pre-swell (peak at 1.67 s) and a long 5 s decay. Alternative reveal hit.
- **`sfx/impact_deep_tremor_04_freesound_119782.mp3`**: "cinematic_deep_tremor.wav" by **swiftoid**  
  Page: https://freesound.org/people/swiftoid/sounds/119782/  
  Direct: https://cdn.freesound.org/previews/119/119782_854782-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  14.75 s, 48 kHz, stereo, 127 kbps mp3; level mean -10.5 / max -0.5 dB  
  Pure sub tremor/rumble, 14.8 s, swelling to a peak at ~5.5 s. Very hot level. Put it under the reveal and the dragon section; can be looped into a deep note.
- **`sfx/impact_dramatic_hit_03_freesound_222517.mp3`**: "Dramatic Hit" by **qubodup**  
  Page: https://freesound.org/people/qubodup/sounds/222517/  
  Direct: https://cdn.freesound.org/previews/222/222517_71257-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  7.04 s, 48 kHz, mono, 179 kbps mp3; level mean -19.4 / max -0.3 dB  
  Cymbal impact plus bass hit, mono, 7 s. Brighter crash-style hit.
- **`sfx/impact_trailer_boom_taiko_05_freesound_207755.mp3`**: "Movie Trailer Boom" by **hykenfreak**  
  Page: https://freesound.org/people/hykenfreak/sounds/207755/  
  Direct: https://cdn.freesound.org/previews/207/207755_2605156-hq.mp3  
  License: CC BY 4.0 (attribution required), https://creativecommons.org/licenses/by/4.0/  
  6.99 s, 44.1 kHz, stereo, 172 kbps mp3; level mean -18.6 / max -0.6 dB  
  Movie-trailer boom built from a recording of a real 30-inch Japanese taiko, enhanced. 7 s. Best combined taiko-plus-boom for the 23 s reveal.
- **`sfx/taiko_hit_01_freesound_82712.mp3`**: "TAIKO DRUM 001.wav" by **sandyrb**  
  Page: https://freesound.org/people/sandyrb/sounds/82712/  
  Direct: https://cdn.freesound.org/previews/82/82712_14771-hq.mp3  
  License: CC BY 4.0 (attribution required), https://creativecommons.org/licenses/by/4.0/  
  2.44 s, 44.1 kHz, mono, 159 kbps mp3; level mean -20.3 / max -0.6 dB  
  Simulated taiko (floor tom slowed to half speed), 2.4 s, deep and dry. Single drum accent.
- **`sfx/taiko_hit_03_41hz_freesound_584131.mp3`**: "Taikodrum (41 hz).wav" by **tarane468**  
  Page: https://freesound.org/people/tarane468/sounds/584131/  
  Direct: https://cdn.freesound.org/previews/584/584131_5876986-hq.mp3  
  License: CC BY 4.0 (attribution required), https://creativecommons.org/licenses/by/4.0/  
  4.45 s, 44.1 kHz, mono, 180 kbps mp3; level mean -17.5 / max -0.3 dB  
  Big low taiko (41 Hz fundamental) with a long ~4 s decay. Huge sub weight for the reveal; layer it with impact_boom_01.
- **`sfx/gong_massive_01_freesound_260972.mp3`**: "Massive Gong.mp3" by **bendavisdrumguy@gmail.com**  
  Page: https://freesound.org/people/bendavisdrumguy@gmail.com/sounds/260972/  
  Direct: https://cdn.freesound.org/previews/260/260972_1191746-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  17.16 s, 44.1 kHz, stereo, 111 kbps mp3; level mean -17.4 / max -0.7 dB  
  40-inch Zildjian tam-tam with effects: bright shimmering wash that sustains about 17 s. Layer it on the reveal for East Asian colour, or let it ring into the dissolve.
- **`sfx/gong_tamtam_soft_02_freesound_423477.mp3`**: "Tam tam (soft)" by **ThomEvans**  
  Page: https://freesound.org/people/ThomEvans/sounds/423477/  
  Direct: https://cdn.freesound.org/previews/423/423477_8092625-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  58.50 s, 44.1 kHz, stereo, 175 kbps mp3; level mean -23.8 / max -6.8 dB  
  Softly struck tam-tam: mellow, rounded, deep bloom with a very long decay (58 s file). A subtle gong under the reveal, or a dissolve and calm tail (36-45 s).

### Creature growl / rumble (mix subtly, pitch down)
- **`sfx/creature_deep_sea_monster_04_freesound_341173.mp3`**: "Deep sea monster.flac" by **cylon8472**  
  Page: https://freesound.org/people/cylon8472/sounds/341173/  
  Direct: https://cdn.freesound.org/previews/341/341173_3415022-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  9.81 s, 44.1 kHz, stereo, 178 kbps mp3; level mean -16.3 / max -0.2 dB  
  Deep-sea creature groan with a whale-like quality, 9.8 s. Fits a dragon living underwater. Strong pick.
- **`sfx/creature_dragon_breath_07_freesound_532156.mp3`**: "dragon breathe ire" by **soundmast123**  
  Page: https://freesound.org/people/soundmast123/sounds/532156/  
  Direct: https://cdn.freesound.org/previews/532/532156_9829875-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  9.21 s, 44.1 kHz, stereo, 194 kbps mp3; level mean -16.8 / max -0.1 dB  
  Dragon roar with fire breathing, 9.2 s. The fire breath may be off-theme, but the roar portions are usable.
- **`sfx/creature_dragon_roars_pack_06_freesound_479380.mp3`**: "Dragon: Several roars, growls and snarls" by **Breviceps**  
  Page: https://freesound.org/people/Breviceps/sounds/479380/  
  Direct: https://cdn.freesound.org/previews/479/479380_9159316-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  60.00 s, 48 kHz, stereo, 188 kbps mp3; level mean -14.7 / max 0.0 dB  
  60 s of dragon roars, growls and snarls made for a dragon character. Choose sections; the loudest roar is around 41 s.
- **`sfx/creature_growl_deep_01_freesound_222523.mp3`**: "Deep Monster Growl" by **uagadugu**  
  Page: https://freesound.org/people/uagadugu/sounds/222523/  
  Direct: https://cdn.freesound.org/previews/222/222523_255863-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  5.75 s, 44.1 kHz, stereo, 181 kbps mp3; level mean -20.0 / max -1.7 dB  
  Several layers of pitched-down vocal growl, 5.75 s, peaking at ~1.7 s. Clean and very low.
- **`sfx/creature_growl_deep_02_freesound_368255.mp3`**: "Deep Growl" by **mburgess1**  
  Page: https://freesound.org/people/mburgess1/sounds/368255/  
  Direct: https://cdn.freesound.org/previews/368/368255_4537796-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  5.01 s, 44.1 kHz, stereo, 171 kbps mp3; level mean -24.4 / max -9.0 dB  
  Deep growl of a large creature in a cave, 5 s. Short and dark.
- **`sfx/creature_growl_reverb_05_freesound_366672.mp3`**: "Monster Growl_with Reverb.wav" by **cylon8472**  
  Page: https://freesound.org/people/cylon8472/sounds/366672/  
  Direct: https://cdn.freesound.org/previews/366/366672_3415022-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  12.86 s, 44.1 kHz, stereo, 169 kbps mp3; level mean -13.6 / max -1.3 dB  
  Monster growl with reverb, 12.9 s, very low (99% of energy under 200 Hz). An epic distant growl.
- **`sfx/creature_low_rumble_03_freesound_132873.mp3`**: "Monster Low Rumble 2.wav" by **ecfike**  
  Page: https://freesound.org/people/ecfike/sounds/132873/  
  Direct: https://cdn.freesound.org/previews/132/132873_2337290-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  9.45 s, 44.1 kHz, stereo, 172 kbps mp3; level mean -13.8 / max -3.3 dB  
  Low monster rumble, almost entirely sub, 9.5 s. A subtle 'breathing' presence under the dragon (23-36 s).

### Shimmer / dissolve / bells
- **`sfx/shimmer_brightness_01_freesound_632762.mp3`**: "Brightness" by **sonically_sound**  
  Page: https://freesound.org/people/sonically_sound/sounds/632762/  
  Direct: https://cdn.freesound.org/previews/632/632762_12946258-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  20.32 s, 44.1 kHz, stereo, 150 kbps mp3; level mean -31.8 / max -16.0 dB  
  Airy musical shimmer improvisation, 20 s, swelling to ~6 s. For the dissolve into haze (36-42 s).
- **`sfx/shimmer_magic_aura_03_freesound_547365.mp3`**: "Magic Aura Shimmer" by **EminYILDIRIM**  
  Page: https://freesound.org/people/EminYILDIRIM/sounds/547365/  
  Direct: https://cdn.freesound.org/previews/547/547365_10912485-hq.mp3  
  License: CC BY 4.0 (attribution required), https://creativecommons.org/licenses/by/4.0/  
  4.33 s, 44.1 kHz, stereo, 185 kbps mp3; level mean -31.4 / max -5.4 dB  
  Rising magic-aura shimmer, 4.3 s, that ends on its peak. Reverse it for a soft decay, or use it as a gentle pre-reveal swell.
- **`sfx/shimmer_singing_bell_05_freesound_202017.mp3`**: "singing bell hit 2.wav" by **ryancacophony**  
  Page: https://freesound.org/people/ryancacophony/sounds/202017/  
  Direct: https://cdn.freesound.org/previews/202/202017_1992412-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  43.38 s, 48 kHz, stereo, 182 kbps mp3; level mean -24.4 / max -0.3 dB  
  Singing bowl hit with a long 43 s ring. A beautiful calm tail under 36-45 s.
- **`sfx/shimmer_singing_bowl_strike_04_freesound_271370.mp3`**: "singing bowl strike sound" by **inoshirodesign**  
  Page: https://freesound.org/people/inoshirodesign/sounds/271370/  
  Direct: https://cdn.freesound.org/previews/271/271370_5159066-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  6.27 s, 44.1 kHz, stereo, 182 kbps mp3; level mean -42.2 / max -22.6 dB  
  Tibetan singing bowl strike, 6.3 s, quiet. A soft bell accent with East Asian colour for the final calm haze.
- **`sfx/shimmer_sparkle_flourish_02_freesound_844398.mp3`**: "Mysterious Sparkle Flourish" by **SkySpeira**  
  Page: https://freesound.org/people/SkySpeira/sounds/844398/  
  Direct: https://cdn.freesound.org/previews/844/844398_7155498-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  3.95 s, 48 kHz, stereo, 169 kbps mp3; level mean -39.5 / max -18.8 dB  
  Mysterious sparkle flourish, 4 s, delicate. For the dissolve or a small magical accent.

### Room tone / drone
- **`sfx/drone_soft_tonal_wind_01_freesound_397091.mp3`**: "Soft Tonal Wind_01" by **janbezouska**  
  Page: https://freesound.org/people/janbezouska/sounds/397091/  
  Direct: https://cdn.freesound.org/previews/397/397091_3287894-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  59.72 s, 48 kHz, stereo, 166 kbps mp3; level mean -44.8 / max -26.0 dB  
  Soft tonal wind drone, 60 s, very quiet (needs gain). Room tone / air bed for the calm glass at 0-4 s.
- **`sfx/drone_space_02_freesound_20705.mp3`**: "spacedrone3.wav" by **Elektrocell**  
  Page: https://freesound.org/people/Elektrocell/sounds/20705/  
  Direct: https://cdn.freesound.org/previews/20/20705_53896-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  73.60 s, 44.1 kHz, stereo, 180 kbps mp3; level mean -24.0 / max -10.0 dB  
  Long space drone, 74 s, 'like many little bugs working in a big wind'. Darker texture bed.
- **`sfx/roomtone_apartment_01_freesound_426767.mp3`**: "Apartment Room Tone.wav" by **cMilan**  
  Page: https://freesound.org/people/cMilan/sounds/426767/  
  Direct: https://cdn.freesound.org/previews/426/426767_7905750-hq.mp3  
  License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/  
  20.11 s, 48 kHz, stereo, 154 kbps mp3; level mean -44.6 / max -28.4 dB  
  City apartment room tone, 20 s, very quiet. A neutral room bed if needed.

---
Sources not used: Pixabay (its pages sit behind a bot-check challenge, so I skipped it rather than bypass it). I did not try Free Music Archive. A Wikimedia Commons search (shakuhachi, guzheng, erhu, taiko) turned up only short demos and folk clips, nothing cinematic. Total downloaded while evaluating, including candidates I rejected: about 190 MB.
