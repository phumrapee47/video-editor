# Mood and role lessons (from user ratings)

Each lesson comes from a real user rating of Claude's guess. Add a row per round so versions can be compared.

## Ratings log
| Date | Clip | Claude's guess | User rating | User's correction |
|---|---|---|---|---|
| 2026-10-31 | Kyoto live, boat ride (0:33:00) | scenic, calm: ambient music + 3D boat-on-river animation | 4/5 for picking a real highlight; cut points OK | The mood is comedy, judged from the dialogue and shouting, not from the scenery |
| 2026-10-31 | Kyoto live, samurai costume (2:15:40) | action: dramatic music + sword whoosh SFX | 4/5; cut points OK | Judging by the speech it is comedy, not action; dramatic music would be the wrong call |
| 2026-10-31 | Kyoto live, "monkey park" label (1:28:30) | monkeys, comedic | wrong by Claude's own check | Frames showed fans on a viewing deck; the monkey words were only in the captions |

| 2026-11-01 | Kyoto live, 6 clips re-guessed from speech (predictions in `kyoto/predictions_round2.md` (local test data, not published)) | see predictions file | no per-clip scores yet; user said overall "starting to get the mood right" | n/a |

## Rules learned
1. **Decide mood from speech and sound first, visuals second.** A calm-looking scene (river, boat) with shouting and jokes is a comedy moment, so use light, playful music and punchy captions, not calm ambient music.
2. **Check the frames before trusting the captions.** Captions mention things that are not on screen (the monkey joke). Label a window only after viewing its frames.
3. **Loudness picks a highlight, not a genre.** Use loudness to find candidates, then read the transcript to classify them (comedy, awe, tension, calm).
4. **Costumes and props do not set the genre.** Samurai armor looked like action but the dialogue was comedy; the same error happened twice (boat, samurai), so default to "comedy" for a vlogger who is joking with people unless the speech says otherwise.
5. **Cut points chosen from caption timing (start on a spoken line, end after the punchline) were acceptable.** Keep that rule.

## Round 2 outcome (2026-11-02)
Predicted scores for 6 clips from speech-first mood guesses: mean error 0.92 vs 0.75 for a constant guess of 3. The "speech first" rule fixed the genre labels (comedy) but did not predict how much the user liked a clip. Next time ask what the user values (energy, visuals, topic, music fit) instead of guessing a score.
Highest rated: izakaya 4.5 (visual, lively atmosphere, matching jazz), fans on the deck 4 (chaotic comedy with matching music). Lowest: both in-car chats 2.
