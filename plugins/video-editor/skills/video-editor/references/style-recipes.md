# Style recipes (measured on 42 clips, 9 styles)

Measured by `scripts/analyze_clip.py` (ffmpeg scene detection at 0.3, shots under 0.25s merged; EBU R128 loudness).
Raw per-clip numbers: `research/analysis.json`. Public metadata: `research/meta.json`. Source videos were deleted after analysis.
Long clips were analysed on their first 3 minutes only (intros usually cut faster than the rest).
Cells show median (min-max). n is small per style, so treat them as starting points.

| Style | n | Avg shot (s) | Cuts/min | Loudness (LUFS) | Dynamics LRA (dB) | Silence (s) |
|---|---|---|---|---|---|---|
| cinematic | 8 | 3.9 (1.1-7.8) | 15 (7-55) | -12.9 (-16.7 to -9.8) | 6.6 (3.5-13.8) | ~0 |
| bright_vlog | 5 | 3.5 (1.9-4.1) | 17 (14-31) | -15.6 (-22.4 to -12.9) | 6.8 (4.2-11.7) | ~0 |
| funny, single-take Shorts | 2 | 21 (9.5-32.5) | 0 | -8.6 (-9.2 to -8.0) | 2.2 (1.6-2.8) | 0 |
| funny_fastcut | 2 | 6.3 (3.1-9.5) | 12.5 (6-19) | -20.1 (-23.6 to -16.5) | 12.1 (6.1-18.0) | 3.5 |
| storytelling | 6 | 5.5 (3.5-12.0) | 10.7 (4.7-16.7) | -19.4 (-28.5 to -13.3) | 11.9 (1.9-17.2) | 1.1 |
| shorts (cinematic) | 4 | 1.7 (1.3-5.2) | 35 (10-45) | -15.0 (-18.2 to -12.4) | 5.7 (4.0-14.0) | 0.6 |
| thai | 6 | 3.6 (2.6-4.3) | 16.6 (13.7-22.7) | -18.1 (-23.0 to -15.0) | 7.5 (5.6-14.6) | ~0 |
| thai_short | 1 | 1.8 | 32 | -10.4 | 4.6 | 0 |
| animation3d | 4 | 4.6 (3.4-59) | 13 (0-17) | -16.4 (-18.7 to -9.8) | 15.9 (10.8-21.4) | 5.5 |
| motion_graphic | 4 | 4.3 (2.1-7.5) | 14 (7-27) | -13.3 (-21.6 to -9.5) | 12 (6.4-20.5) | 4.2 |

## Working recipes
- **Cinematic travel:** about 4s shots (15 cuts/min); teaser edits go to ~1s. Loud, music-led (-13 LUFS), moderate dynamics.
- **Bright vlog:** ~3.5s shots, 17 cuts/min, mid loudness (-16 LUFS); voice and music share the mix, so duck music under speech.
- **Thai day-trip vlog:** ~3.6s shots, ~17 cuts/min, quieter (-18 LUFS) because voice and ambience lead.
- **Storytelling / documentary:** slower, ~5.5s shots, ~11 cuts/min, wide dynamics (LRA ~12) and quiet (-19 LUFS); leave breathing room and silence.
- **Fast-cut comedy:** ~6s shots in the two samples, wide dynamics with silence gaps (jokes land on silence). Thin sample.
- **Raw funny Shorts:** one take, loud and flat (-9 LUFS); editing adds little.
- **Vertical Shorts (cinematic):** ~1.7s shots, 35 cuts/min, ~-15 LUFS; cut on the beat.
- **3D animation / motion graphic:** big dynamics (LRA 12-16) with 4-5s silence; peaks near -7 LUFS, lots of quiet space.

## Caveats
- Samples are 1-8 clips per style; thai_short has 1, funny_fastcut 2. Add clips before relying on those rows.
- Search noise: some picks are only loosely in style (for example animated shorts under storytelling).
- Loudness cannot separate music from voice. Ducking depth and sound-effect timing are still unmeasured.
- Subtitle style and on-screen text were not measured.

## Case study: Go Went Go (Thai travel documentary vlog, 3 full videos, 25-38 min)
Measured on full-length 144p copies (deleted afterwards); data in `gowentgo/*.json` (local test data, not published).

| Measure | Result |
|---|---|
| Avg / median shot | 3.8-6.3s / 2.8-3.2s |
| Shots under 2s / over 8s | 16-26% / 8-20% |
| Cuts per min, first 3 min vs rest | 16-19 vs 9-16 (video 1 stays near 16, videos 2 and 3 slow to ~9) |
| Speech coverage (from subtitles) | 77-82% of runtime |
| Non-speech stretches of 3s or more | 23-46 per video, median 6-8s |
| Structure | Intro 1-3 min with a hook question, then 1-7 min chapters per place, closing summary 1-2 min |
| Narration pace | 126-136 words/min, subtitle cues ~1.4s |

Takeaways: a fast opening (about 17 cuts/min) that relaxes in the body; a median shot of ~3s with a long tail of 8s+ shots for scenery; speech-led audio with quiet gaps. Whether the gaps carry music is still unconfirmed (waiting on the user's listening check).
