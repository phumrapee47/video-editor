"""Synthesize a mood sound-effects track for Roro Jonggrang v3 (no downloads). Writes sfx.wav (44.1 kHz mono).
Cue times match compose_roro_v3.py: the effects follow the mood of each moment, not a constant bed.
"""
import wave
import numpy as np

SR, DUR = 44100, 81.0
rng = np.random.default_rng(5)
out = np.zeros(int(SR * DUR))


def env(n, a, r):
    e = np.ones(n); ai, ri = int(SR * a), int(SR * r)
    if ai: e[:ai] = np.linspace(0, 1, ai)
    if ri: e[-ri:] *= np.linspace(1, 0, ri)
    return e


def lowpass(x, k):
    return np.convolve(x, np.ones(k) / k, mode="same")


def add(t, sig, gain):
    i = int(t * SR); j = min(len(out), i + len(sig)); out[i:j] += gain * sig[: j - i]


def tt(d): return np.arange(int(SR * d)) / SR


def drone(d):  # ominous low hum (curse)
    x = tt(d); return (np.sin(2 * np.pi * 55 * x) + 0.6 * np.sin(2 * np.pi * 82.5 * x)) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.3 * x)) * env(len(x), 2, 2)


def boom(d=1.6):  # deep hit (death, fury)
    x = tt(d); f = 90 * np.exp(-x * 1.5) + 30
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.5 * lowpass(rng.standard_normal(len(x)), 60)) * np.exp(-x * 2.2)


def heartbeat():
    x = tt(0.18); thump = np.sin(2 * np.pi * 55 * x) * np.exp(-x * 25); s = np.zeros(int(SR * 0.9))
    s[: len(thump)] += thump; s[int(SR * 0.28): int(SR * 0.28) + len(thump)] += 0.7 * thump; return s


def chime(d=2.5):  # soft romance bell
    x = tt(d); return sum(a * np.sin(2 * np.pi * f * x) for f, a in ((880, 1), (1320, 0.5), (1760, 0.25))) * np.exp(-x * 1.8)


def crickets(d):
    x = tt(d); return np.sin(2 * np.pi * 4300 * x) * (np.sin(2 * np.pi * 28 * x) > 0.6) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.7 * x)) * env(len(x), 1, 1)


def thud():
    x = tt(0.5); return (np.sin(2 * np.pi * 70 * x) + 0.4 * lowpass(rng.standard_normal(len(x)), 40)) * np.exp(-x * 9)


def shimmer(d):  # magic building sound
    x = tt(d); n = rng.standard_normal(len(x)); hi = n - lowpass(n, 6)
    return hi * (np.sin(2 * np.pi * 6 * x) * 0.3 + 0.7) * np.linspace(0.3, 1, len(x)) * env(len(x), 0.5, 1)


def crackle(d):  # fire
    x = tt(d); c = np.zeros(len(x)); idx = rng.integers(0, len(x), int(d * 25)); c[idx] = rng.uniform(0.4, 1, len(idx)) * rng.choice([-1, 1], len(idx))
    c = lowpass(c, 3) * 6 + 0.25 * lowpass(rng.standard_normal(len(x)), 200); return c * env(len(x), 0.6, 1.5)


def whoosh(d=1.4):
    x = tt(d); n = rng.standard_normal(len(x)); a = np.sin(np.pi * x / d) ** 2
    return (lowpass(n, 8) * a + 0.5 * (n - lowpass(n, 4)) * a ** 3)


def rumble(d):
    x = tt(d); return lowpass(rng.standard_normal(len(x)), 300) * 4 * np.exp(-x * 0.9) * env(len(x), 0.05, 0.6)


def grind(d):  # stone forming
    x = tt(d); return lowpass(rng.standard_normal(len(x)), 120) * 3 * (0.6 + 0.4 * np.sin(2 * np.pi * 7 * x)) * env(len(x), 0.8, 1.2)


def sting(d=4.0):
    x = tt(d); return sum(np.sin(2 * np.pi * f * x) for f in (220, 261.6, 329.6)) * env(len(x), 1.2, 2.5) / 3


add(0.0, drone(10.0), 0.35); add(7.6, boom(1.8), 0.5)                          # the curse
add(12.8, chime(), 0.25); add(17.6, chime(), 0.2)                               # love
add(21.0, boom(), 0.7); [add(t, heartbeat(), 0.5) for t in (22.4, 23.4, 24.4, 25.4, 26.4)]   # father's death
add(28.2, crickets(10.6), 0.05)                                                 # quiet night, the challenge
add(39.4, shimmer(7.4), 0.12); [add(t, thud(), 0.45) for t in (39.6, 41.4, 43.2, 45.0)]      # temples rise, back to front
add(42.0, boom(1.4), 0.35)                                                      # demons summoned (matches the shake)
add(49.3, crackle(9.5), 0.35)                                                   # fire
add(57.3, whoosh(), 0.5); add(58.0, whoosh(1.2), 0.35)                          # spirits flee
add(64.05, boom(2.0), 0.8); add(64.1, rumble(2.6), 0.5)                         # fury
add(69.8, grind(4.2), 0.4); add(76.4, sting(), 0.3)                             # turned to stone, ending
out = out / max(1e-9, np.abs(out).max()) * 0.5
with wave.open("sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())
print("sfx.wav", len(out) / SR, "s")
