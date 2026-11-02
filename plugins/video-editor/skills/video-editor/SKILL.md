---
name: video-editor
description: Edit videos end to end with ffmpeg - find highlight moments in long raw footage or livestreams, cut them into short clips, add subtitles, place background music only where nobody is talking, add scene sounds, make vertical 9:16 Shorts/Reels, export. Styles - cinematic travel, bright/funny vlog, storytelling, Thai travel vlog, 3D animation, motion graphics. Use this skill whenever the user wants to edit, cut, trim, caption, add subtitles or music, add sound effects, find the best moments of a stream or vlog, make a highlight reel, Short or teaser from footage, or says things like "ตัดต่อคลิป", "หาช่วงเด็ด", "ใส่ซับ", "ใส่เพลงประกอบ", "ลดเสียงเพลงตอนพูด", "ทำ vlog", "ทำ Shorts/Reels/TikTok", "เพิ่มเสียงน้ำตก", even if they never say the word ffmpeg or name a style.
---

# Video editor

Turn raw footage into a finished edit: pick the moments worth keeping, plan the edit, get the user's approval, render with ffmpeg. Claude cannot hear audio or judge humor reliably, so the user rates the picks and the sound; every rating is logged and used to improve the rules.

## Workflow
0. **Several clips? Order them first.** Run `scripts/order_clips.py` on the files: it reads Apple creation date, container creation_time, the date in the file name, then file modified time (weakest), and flags clips with missing or shared timestamps and overlaps. Show the proposed order and ask the user to confirm; recording order is not always the story order. Only when timestamps are missing or flagged, fall back to content cues (on-screen clocks, light from day to night, the same outfit or place, words like "yesterday" or "next") and say how unsure you are. Content-only ordering has not been tested.
1. **Inspect.** `ffprobe` for duration, resolution, fps, audio. Get a transcript (YouTube captions via yt-dlp, or Whisper if installed; ask before installing). For long footage, get per-second loudness too.
2. **Find the beats (long or raw footage).** Keep only what a viewer wants: storytelling, interaction with people, showing something, punchlines; drop dead air and aimless walking (`references/highlight-criteria.md`). Run `scripts/find_beats.py` on the captions + loudness to get candidates, then look at frames of the top ones and read their text before choosing. The script mainly ranks dense dialogue, so treat its picks as candidates.
3. **Read the mood.** Classify each beat from speech and sound first, then visuals (`references/mood-lessons.md`); do not trust captions that mention things not on screen, and do not predict the user's score, ask for it.
4. **Pick a style** if not obvious and read its row in `references/style-recipes.md` (starting numbers from sample clips, not rules).
5. **Write an edit plan and wait for approval:** per beat the time range (start at the setup, end after the payoff or reaction), subtitle notes, music yes/no. Cut beats together without dead air.
6. **Render** with `references/ffmpeg-recipes.md`, `scripts/make_vertical_short.py` (9:16 + subtitles + loudness) and `scripts/add_music.py` (music ducked from caption timestamps). Work from low-res proxies for long footage. Never overwrite source files.
7. **Check and hand over.** Re-measure loudness, check subtitle frames, say what could not be verified (the sound itself), send files and ask for ratings. Before a rating round, make a calibration pair if a level is in doubt (music 20 dB under speech was inaudible).

## Music policy (confirmed by the user)
- While someone talks to the camera or in conversation: no music.
- Music fades in only where nobody talks: scenery, places, things the camera is pointing at, camera pans. It fades out about 0.5s before talking returns (timestamp ducking from the transcript, not a compressor alone; compressor only as a fallback).
- Dialogue-driven scenes (talking in a car or boat) rated lower with music; lively scenes with a matching genre (bossa in a restaurant) rated highest. Choose genre from the setting.
- Gap bed about 8 dB under speech loudness, fades 1-2s; details and evidence in `references/music-rules.md`. Raw chat-driven streams have almost no gaps, so expect little or no music there.
- Match style loudness: -13 to -15 LUFS for cinematic/Shorts, -18 to -19 for talk-led vlogs and storytelling; true peak below -1 dBTP (AAC adds about 1 dB, leave margin).
- Music and sound files: use the user's own or free-license tracks, ask before downloading, keep the credit text (see the workspace `music/CREDITS.md` pattern).

## Subtitles
Make an `.srt` from the transcript (`scripts/vtt_to_srt.py` handles YouTube auto captions: removes `>>` and HTML codes), let the user check the text (Thai errors are common), burn in with `subtitles=`. Short lines (about 42 characters, 2 lines), on screen at least 1s.

## Vertical, Shorts and Reels
1080x1920 with blurred background and the frame centered, or a face/screen stack when a webcam overlay exists. Hook within 2 seconds. Single-camera streams have no second angle; crop or zoom instead of promising B-roll.

## Animation (3D, motion graphics)
The wanted style is 2.5D motion graphics built from **real photos** (cut-outs of the real place, people, animals, sky) layered with parallax and synced to a narration; drawn geometric stand-ins were rejected. Find licensed photos (Wikimedia Commons), cut out with rembg, compose frames in Pillow, keep a credits file. Rules that took the test clip from 6/10 to 8/10 (passed): every element is a real photo, the sky too; smooth sub-pixel motion; camera shake and sound effects only where the story is tense or exciting; fill the frame with depth layers (near large and bright, far smaller and hazed toward the sky); figures never cover the hero subject. Never crop through the hero subject: run `scripts/check_cutout.py` on every cut-out and fix any subject that touches a border unless that is intended (landscape bands). The v4 rules (sub-shots every ~3 s, word-level sync, one colour grade with paper texture, 1080p, moving atmosphere, puppet motion, depth of field, meaningful transitions, real sound, whooshes, explainer graphics, preview first) scored 9.5/10 on the Pompeii clip; they are listed in `references/animation-2-5d.md`. Earlier note: next-level rules being tested (sub-shots every ~3 s, word-level sync, one colour grade with paper texture, 1080p, moving atmosphere, puppet motion, depth of field, meaningful transitions, real sound, whooshes, explainer graphics, preview first) are listed in `references/animation-2-5d.md` with the method, scripts and pitfalls. Narration from other creators is for local tests only.

## Honest limits
- Claude cannot listen. Music fit, mix balance and humor need the user's ears. Its score predictions were not better than guessing 3 (mean error 0.92 vs 0.75), so do not promise taste.
- Caption-based tools depend on auto captions (errors, no tone); scene detection misses soft transitions; style rows come from few clips.
- Other people's videos and music: use for local testing only unless the user has permission; ask before every download and say file, source and size.

## References and tools
- `references/`: `highlight-criteria.md`, `music-rules.md`, `mood-lessons.md`, `style-recipes.md` (includes a Go Went Go case study), `style-metadata.md`, `ffmpeg-recipes.md`
- `scripts/`: `order_clips.py`, `find_beats.py`, `find_highlights.py`, `vtt_to_srt.py`, `make_vertical_short.py`, `add_music.py`, `music_vs_speech.py`, `cut_rhythm.py`, `analyze_clip.py`, `fetch_meta.py`, `find_clips.py`, `scan_streams.py`, `compare_versions.py` (version comparison harness; the workspace folder holds `version-log.md` with user verdicts)
