# What counts as a highlight (user guidance, 2026-11-02)

Clips that are posted to YouTube keep only the interesting beats and drop quiet stretches and aimless walking.
The beats worth keeping:
1. **Storytelling**: someone tells a story or explains something with a setup and a payoff.
2. **Interaction with other people**: conversation, reactions, banter, meeting someone.
3. **Showing something**: the creator points the camera at something they want the viewer to see (a place, a dish, an object, a reveal).
4. **Punchlines**: a joke that lands (setup, then the laugh/reaction).
5. Anything else that is interesting in its own right.

Drop: silence, dead air, walking with nothing happening, reading chat with no payoff.

## Consequences for the edit
- Select by beat, not by loudness. Loudness is only one weak signal.
- Cut a beat from its setup (a few seconds before) to just after the payoff or reaction.
- Join beats directly (hard cut or a short transition); do not leave dead air between them.
- Music still follows `music-rules.md`: none while people talk, a bed only where nobody talks (for example while showing something).

## How `scripts/find_beats.py` scores a window (heuristic, to be checked by the user)
- laughter markers and exclamations in the captions (punchline/reaction)
- speaker changes (">>") per window (interaction)
- cue words such as "look", "check this out", "no way", "oh my god" (showing/reveal)
- loudness above the local baseline (excitement)
Low scores: very low speech density and no markers (dead air).
Captions are automatic and miss tone, so the picks are candidates for the user to rate, not verdicts.
