# Music placement rules

## Evidence
- Go Went Go, 3 full videos (25-38 min): subtitles cover 77-82% of the runtime; non-speech stretches of 3s or more number 23-46 per video, median 6-8s. Source: `scripts/music_vs_speech.py`, data in `gowentgo/` (local test data, not published).
- Loudness inside those gaps is 13-18 dB below the speech loudness in 2 of 3 videos (2 dB below in the third), and does not rise at the start of a gap.
- **User listening check (2026-11-01), 3 gap snippets:** (1) there is music in the gaps, (2) it gets louder after the speech stops, (3) it gets quieter before the speech returns.

## What the evidence means together
Music is a quiet bed, not a loud swell. It sits low under speech, becomes noticeable once the voice stops, and is lowered again just before the voice returns. Its absolute level stays well below speech loudness, which is why loudness alone could not show it.

## Rules for the edit
1. No music while people talk (see the policy section at the end, which is the final word); never let it compete with the voice.
2. When speech stops for 3s or more, bring the music up gently (about 1-2s ramp) to a bed roughly 13-18 dB below the speech level. Longer gaps (8s+) are the right place for scenery, mood shots and the music to be noticed.
3. Start lowering the music about 0.5s before speech returns (the duck must be timestamp-based, taken from the transcript or silence detection, so the music moves ahead of the voice).
4. Keep the fade shapes smooth; avoid abrupt cuts of music.
5. Open question: the exact fade lengths in the reference videos were not measured; the 1-2s ramp is a starting guess to be tuned by ear.

## Listening verdict on ducking method (2026-11-01)
User compared two 60s renders of the same Go Went Go audio: sidechain compressor (v2) vs caption-timestamp ducking (v3). v3 sounded better. Default to v3 whenever a transcript exists; sidechain only as fallback. See `version-log.md` (local test data, not published).

## Audibility calibration (2026-11-02, Kyoto live clip, music "Sneaky Snitch" against continuous speech)
- Music 20 dB below the speech loudness: not audible at all to the user (cannot be evaluated, do not use this level for a test).
- 15 dB below and 10 dB below: both audible.
- So against continuous speech the music must be no more than about 15 dB below the speech to be heard; plan for 10-15 dB when the goal is "audible bed under talking", and the 13-18 dB range only works in gaps where nothing masks it.
- Mistake to avoid: judging audibility from arithmetic. Always run a calibration pair at two or three levels before a rating round.

## Preferred level (2026-11-02)
User chose music about 10 dB under continuous speech ("fits well"), over 15 dB. This was a calibration test level (bed -6 dB, 4 dB extra drop under speech, one clip, one track) and is superseded by the policy section below; the current defaults in `scripts/add_music.py` are bed -8 dB in gaps and 30 dB drop under speech.

## When to use music at all (user ratings, 2026-11-02)
Music at 10 dB under speech was rated: izakaya + bossa 4.5, fans on the deck + playful music 4, boat 3, samurai 3, bench 3, koto 3, two car chats with other people 2.
User's explanation: some scenes do not need music, for example rowing a boat or riding in a car with other people. A drive helps from music only when the camera is showing views or things the viewer should look at, like a vlog.
Rules:
1. Dialogue-driven scenes (talking in a car or boat, face on camera): no music, or the user will rate it lower. Default to none.
2. Visual-driven scenes (scenery, food, places, B-roll the camera is pointing at): add a music bed; this is where music adds value.
3. Lively scenes with a matching genre can score high (jazz/bossa in a restaurant); pick genre from the setting, not just from "comedy".
4. Ask or check the scene type before adding music; do not add music to every clip.

## Policy confirmed by the user (2026-11-02) - overrides the "music under speech" test level
- While someone talks to the camera or in conversation: **no music** (effectively off).
- Music **fades in** when nobody is talking: scenery, places, things the camera is pointing at, camera pans and other B-roll.
- It fades out before talking returns.
- The 10 dB level from the calibration test only shows what is audible against speech; it is not the default. Defaults in `scripts/add_music.py` now: bed -8 dB in gaps, 30 dB drop while speech is present.
- Consequence: a window with continuous talking has nowhere for music. Pick windows with 6s+ gaps or B-roll to demonstrate music, and confirm by frames that the gap shows a view or an object, not a silent face.
