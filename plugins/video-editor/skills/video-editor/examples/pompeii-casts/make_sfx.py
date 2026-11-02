"""Sound effects for the Pompeii clip: real recordings (eruption, wind, clock; credits in assets/CREDITS.md) plus a few
synthesized accents (whoosh, heartbeat, thud, pour, chime). Writes sfx.wav (44.1 kHz mono, 84.6 s)."""
import subprocess, wave
import numpy as np

SR, DUR = 44100, 84.6
rng = np.random.default_rng(9); out = np.zeros(int(SR * DUR))


def rec(path, start=0.0, dur=None):
    args = ["ffmpeg", "-v", "error", "-ss", str(start), "-i", path] + (["-t", str(dur)] if dur else []) + ["-f", "s16le", "-ac", "1", "-ar", str(SR), "-"]
    x = np.frombuffer(subprocess.run(args, capture_output=True).stdout, dtype=np.int16).astype(np.float64) / 32768
    return x / max(1e-9, np.abs(x).max())


def fade(x, a=0.3, r=0.6):
    x = x.copy(); ai, ri = min(len(x), int(SR * a)), min(len(x), int(SR * r))
    if ai: x[:ai] *= np.linspace(0, 1, ai)
    if ri: x[-ri:] *= np.linspace(1, 0, ri)
    return x


def add(t, sig, g):
    i = int(t * SR); j = min(len(out), i + len(sig)); out[i:j] += g * sig[: j - i]


def tt(d): return np.arange(int(SR * d)) / SR
def lp(x, k): return np.convolve(x, np.ones(k) / k, mode="same")


def whoosh(d=0.8):
    x = tt(d); n = rng.standard_normal(len(x)); a = np.sin(np.pi * x / d) ** 2; return lp(n, 6) * a * 2
def heartbeat():
    x = tt(0.18); th = np.sin(2 * np.pi * 55 * x) * np.exp(-x * 25); s = np.zeros(int(SR * 0.85)); s[: len(th)] += th; s[int(SR * .27): int(SR * .27) + len(th)] += .7 * th; return s
def thud(): x = tt(0.7); return (np.sin(2 * np.pi * 60 * x) + 0.4 * lp(rng.standard_normal(len(x)), 40)) * np.exp(-x * 7)
def pour(d): x = tt(d); n = rng.standard_normal(len(x)); return lp(n, 25) * (0.6 + 0.4 * np.sin(2 * np.pi * 3 * x)) * 2
def chime(): x = tt(2.0); return sum(a * np.sin(2 * np.pi * f * x) for f, a in ((1046, 1), (1568, .4))) * np.exp(-x * 2.5)
def drone(d): x = tt(d); return (np.sin(2 * np.pi * 49 * x) + .5 * np.sin(2 * np.pi * 73.5 * x)) * (0.7 + 0.3 * np.sin(2 * np.pi * .4 * x))


clock = rec("assets/clock.ogg"); wind = rec("assets/wind.ogg"); rumble = rec("assets/rumble.wav", 0, 8)
add(8.3, fade(clock[: int(SR * 2.6)], .1, .05), 0.30)            # ticking, stops dead at "frozen"
add(50.8, fade(clock[: int(SR * 1.7)], .1, .05), 0.30)           # ticks again, stops at "time stopped"
add(17.2, whoosh(), 0.55); add(65.2, whoosh(), 0.55)              # whip pans
add(17.5, fade(wind[: int(SR * 2.2)], .4, .6), 0.25)              # "imagine..." quiet night
add(19.4, fade(rumble[: int(SR * 5.2)], .05, 1.0), 0.9)           # the eruption (real recording)
add(24.0, fade(drone(4.0), 1, 1), 0.18)                           # centuries pass
add(38.6, fade(pour(3.2), .5, .8), 0.12); add(44.2, thud(), 0.5) # plaster poured, cast revealed
add(54.0, fade(wind[: int(SR * 11.4)], 1.0, 1.0), 0.14)           # eerie close-ups
for b in (62.0, 62.9, 63.8, 64.7): add(b, heartbeat(), 0.45)      # fear
for c in (74.6, 76.1, 79.0): add(c, chime(), 0.12)                # artefacts
out = out / max(1e-9, np.abs(out).max()) * 0.6
with wave.open("sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())
print("sfx.wav", round(len(out) / SR, 1), "s")
