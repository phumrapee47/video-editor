"""Find loud/excited moments in a long audio file and blend with the YouTube replay heatmap.

Usage: python -I find_highlights.py <audio.m4a> <youtube_id> <out.json> [top_n]
Score = loudness above the local (90s) baseline, averaged over 6s, plus replay-heat bonus.
Claude cannot hear: loudness spikes are a proxy for shouting/laughing/crowd noise, and the user judges the picks.
"""
import json, subprocess, sys
import numpy as np
from yt_dlp import YoutubeDL

audio, vid, out = sys.argv[1:4]
top_n = int(sys.argv[4]) if len(sys.argv) > 4 else 12
SR = 8000

raw = subprocess.run(["ffmpeg", "-v", "error", "-i", audio, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
n = len(x) // SR
db = 20 * np.log10(np.sqrt((x[: n * SR].reshape(n, SR) ** 2).mean(1)) + 1e-6)  # one value per second

k = 6
smooth = np.convolve(db, np.ones(k) / k, mode="same")
# local baseline: rolling median over 90s (computed on a coarse grid for speed)
base = np.array([np.median(db[max(0, i - 45): i + 45]) for i in range(0, n, 5)])
base = np.interp(np.arange(n), np.arange(0, n, 5), base)
score = smooth - base

with YoutubeDL({"quiet": True, "no_warnings": True, "skip_download": True}) as y:
    heat = y.extract_info("https://www.youtube.com/watch?v=" + vid, download=False).get("heatmap") or []


def heat_at(t):
    for s in heat:
        if s["start_time"] <= t < s["end_time"]:
            return float(s["value"])
    return 0.0


picks, used = [], np.zeros(n, bool)
for i in np.argsort(-score):
    if used[max(0, i - 40): i + 40].any() or i < 120 or i > n - 60:
        continue
    used[max(0, i - 40): i + 40] = True
    picks.append({"t": int(i), "clock": f"{i // 3600}:{i % 3600 // 60:02d}:{i % 60:02d}", "loud_over_baseline_db": round(float(score[i]), 1),
                  "level_db": round(float(smooth[i]), 1), "heat": round(heat_at(i), 2)})
    if len(picks) >= top_n * 2:
        break
for p in picks:
    p["rank_score"] = round(p["loud_over_baseline_db"] + 6 * p["heat"], 1)
picks = sorted(picks, key=lambda p: -p["rank_score"])[:top_n]
json.dump({"duration_s": n, "picks": picks}, open(out, "w"), indent=1)
for p in picks:
    print(p["clock"], "over+", p["loud_over_baseline_db"], "dB  heat", p["heat"], " score", p["rank_score"])
