# 2.5D paper-cut animation with headless Blender (tested once: Roro Jonggrang, 2026-11-02)

The reference channel's "animations" are 2D / 2.5D motion graphics (flat silhouettes, maps, paper-cut layers), not 3D, and the user confirmed that is the style wanted.

## Method that worked
- Blender 5.2 installed at `C:/Program Files/Blender Foundation/Blender 5.2/blender.exe`; run `blender.exe -b -P script.py -- stills 100,300` for previews and `-- anim` for all frames. No GUI and no MCP server needed (the MCP bridge failed with "Cannot connect at localhost:9876" while Blender was closed).
- Render engine `BLENDER_WORKBENCH`, light `FLAT`, colour type `MATERIAL`, so each material's `diffuse_color` is the flat colour. Preview frames take about 0.3 s; the full 1,944-frame render at 960x540 took roughly 20-30 minutes.
- Build the whole scene from primitives (cones, cylinders, spheres, boxes), one camera per scene bound to a timeline marker, parallax from camera moves over layers at different depths. Script: the v1 Blender script (not published; superseded) (scenes follow the narration SRT timings).
- Encode with ffmpeg from PNG frames and mux the narration audio.

## Pitfalls found (all cost a render round)
1. A plane rotated 90 degrees about X has its height on local Y, so scale it as (width, height, 1); scaling local Z does nothing.
2. Neighbouring scenes placed closer than their backdrop width overlap; space scene origins at least one backdrop width apart (200 units for 160-wide planes).
3. Materials were cached by colour, so animating one material's colour changed every object that shared it. Use unique materials for anything whose colour is animated.
4. Black silhouettes vanish on a black ground; give the ground band a different tone.
5. Check text size against the camera's visible width at the text's depth; titles at 1.6 size overflowed.
6. Look at stills of every scene before the full render, and check that a patch script really applied (one run printed an assertion error, the later steps still ran on the old file).
7. A text caption ("IN ONE NIGHT") appeared partly hidden by the moon in one frame; not investigated.

## Limits
Characters are geometric silhouettes; no real figures, faces or detailed temples. Treat the result as a layout/pacing draft.
Narration audio is another creator's recording: local testing only, not for publication without permission.

## v2: real photo collage (2026-11-02) - the style the user actually wants
User feedback on v1 (geometric shapes): "ไม่สวยเลย" - use real photos (the real temple, real people, a real rooster, a real sunrise) cut out and layered in 2.5D, like Go Went Go's motion graphics. Do not draw stand-in shapes when real images can be found; ask before choosing a look.
Method that worked:
1. Find freely licensed photos on Wikimedia Commons through its API (filter CC0 / CC BY / CC BY-SA / public domain, width >= 1200), download 1400px thumbnails, keep author + licence + page URL in `CREDITS.md`. The API rate-limits (HTTP 429): wait 3s between requests and back off.
2. Look at every photo before using it: automatic picks can be wrong (a relief instead of the temple, fire with text in it, a tiny moon).
3. Cut subjects out with `rembg` (pip `rembg[cpu]`, model downloads on first use); round subjects like the moon with a circle mask. Review cut-outs on a checker sheet.
4. When one photo holds two people, crop each and fade the alpha along the crop edge (`fade_edge`) so no hard cut line shows.
5. Compose frames in Pillow (`examples/roro-jonggrang/ (v2 compositor, superseded by compose_roro_v3.py)`): background with slow zoom, cut-outs with drop shadows ("sticker" look), per-layer motion for parallax, colour tints for mood (red for revenge, grey for stone), short dips to black between scenes, text labels timed to the narration. 1,944 frames at 960x540 rendered in a few minutes, far faster than tuning Blender.
6. Encode with ffmpeg, mux narration, burn subtitles; keep scene labels away from the subtitle band.
Caveats: performers in the photos are from Sendratari Ramayana, standing in for the legend's characters; credits are needed for any publication (CC BY-SA requires share-alike).

## v3 rules from the user's 6/10 review of v2 (2026-11-02)
1. **No accidental jitter.** Rounding sizes and positions to whole pixels each frame makes slow zooms and pans step visibly; place layers with float affine transforms (`place()` in `examples/roro-jonggrang/compose_roro_v3.py`).
2. **Effects follow the mood.** Camera shake only in tense moments (curse, a death, demons appearing, fury, turning to stone), scaled to how tense it is; an exciting moment (rooster) gets a pop or bounce, not a shake. Same for sound: add effects where the moment is scary or exciting.
3. **Fill the frame with depth.** Repeat a subject in layers: near layer large and bright, far layers smaller and blended toward the sky colour (haze), each moving at its own parallax speed; put a ground band under each layer so nothing floats. When building something, raise layers back to front.
4. **Keep characters readable.** Floating figures go behind the hero subject and away from its head.
5. **Sound effects can be synthesized** with numpy when no licensed file exists (`make_sfx.py`: drone, chime, heartbeat, shimmer, thud, crackle, whoosh, rumble, grind, sting); a realistic animal call (rooster) needs a real recording.
6. **Every visible element should be a real photo, the sky too.** v3 scored 8/10 and passed; the one remaining note was that the generated night sky (gradient + dots) looks fake next to the photos. Use a real sky photo (night sky, Milky Way, dawn) as the backdrop.
7. Text font (Georgia Bold) and sizes in v3 were approved.

## v4 rules (agreed with the user 2026-11-02; not yet proven - score them on the next clip)
1. **Sub-shots:** split each scene into 2-3 shots, about one shot change every 3 s (Go Went Go median ~3 s): wide, push in, detail.
2. **Word-level sync:** time reveals to key words of the narration (needs word timestamps, e.g. Whisper); a picture or label should land on the word it illustrates.
3. **One look for all photos:** grade every photo to one palette and lay a light paper texture / film grain over the whole frame so mixed sources read as one piece.
4. **Resolution:** download photos at 2,500 px or more and render 1920x1080, so push-ins stay sharp.
5. **Moving atmosphere:** fog, smoke, dust, embers or light rays as thin layers; prefer real licensed footage over synthetic.
6. **Puppet motion:** split a cut-out into parts (head, arm) and rotate slightly, or add a breathing scale of ~1%; characters should not only slide.
7. **Depth of field:** blur far layers a little and add a foreground element (branches, pillar, ash) at the frame edge.
8. **Meaningful transitions:** match cuts, fast camera sweeps (whip pans), paper tear or ink reveal instead of a dip to black every time.
9. **Real sound:** recorded effects for animals, fire, crowds; a light music bed only where the narration pauses (music policy).
10. **Whoosh on every fast camera move or transition.**
11. **Explainer graphics:** maps with a route drawing itself, arrows, call-out labels, icons, in the same style as the text.
12. **Preview first:** send a 15-20 s low-res preview of the hardest scenes before the full render.

## Result of the v4 rules (Pompeii clip, 2026-11-02): 9.5/10
User: "เข้าถึงอารมณ์ เข้าใจบริบททุกอย่าง ถือว่าสุดยอด". The v4 rules are now proven on one clip.
13. **Show the hero subject whole.** The only deduction (0.5): a plaster cast was cropped in half. I had cropped the source photo to remove a visitor in the background and cut the top of the cast. Mask out only the distracting element (or pick another photo) and never crop through the subject. Run `scripts/check_cutout.py` on all cut-outs: it reports any subject that touches a border (intended cases like landscape bands can be ignored after a look).
14. Thai narration: Whisper small could not transcribe it; YouTube Thai auto captions (corrected by hand) gave usable 2-3 s timing.
