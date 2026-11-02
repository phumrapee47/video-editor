"""Estimate how music/ambience behaves around speech, from subtitle timing + loudness.

Usage: python -I music_vs_speech.py <audio.m4a> <subs.vtt> <out.json>
Speech = seconds covered by subtitle cues; non-speech = everything else (music and/or ambience, cannot be told apart).
Caveat: subtitles can lag or lead speech slightly, so edges are fuzzy; gaps are only counted when >= 3s.
"""
import json, re, subprocess, sys
import numpy as np

audio, vtt, out = sys.argv[1:4]
SR = 4000
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", audio, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
n = len(x) // SR
db = 20 * np.log10(np.sqrt((x[: n * SR].reshape(n, SR) ** 2).mean(1)) + 1e-6)

speech = np.zeros(n, bool)
for m in re.finditer(r"(\d+):(\d+):([\d.]+) --> (\d+):(\d+):([\d.]+)", open(vtt, encoding="utf-8").read()):
    a = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]); b = int(m[4]) * 3600 + int(m[5]) * 60 + float(m[6])
    speech[int(a): min(int(b) + 1, n)] = True
# close tiny holes (< 2s) between cues: that is still one speaking stretch
i = 0
while i < n:
    if not speech[i]:
        j = i
        while j < n and not speech[j]:
            j += 1
        if j - i < 2 and i > 0 and j < n:
            speech[i:j] = True
        i = j
    else:
        i += 1

gaps, i = [], 0
while i < n:
    if not speech[i]:
        j = i
        while j < n and not speech[j]:
            j += 1
        if j - i >= 3:
            gaps.append((i, j))
        i = j
    else:
        i += 1

valid = db > -70
res = {
    "minutes": round(n / 60, 1),
    "speech_pct": round(float(speech.mean() * 100), 1),
    "speech_db_median": round(float(np.median(db[speech & valid])), 1),
    "nonspeech_db_median": round(float(np.median(db[~speech & valid])), 1),
    "gaps_ge3s": len(gaps),
    "gap_len_median_s": int(np.median([b - a for a, b in gaps])) if gaps else 0,
    "gap_len_p90_s": int(np.percentile([b - a for a, b in gaps], 90)) if gaps else 0,
    "gaps_ge10s": sum(b - a >= 10 for a, b in gaps),
}
long_gaps = [(a, b) for a, b in gaps if b - a >= 8]
if long_gaps:
    first = np.mean([db[a:a + 2].mean() for a, b in long_gaps]); mid = np.mean([db[a + 3:b - 3].mean() for a, b in long_gaps])
    last = np.mean([db[b - 2:b].mean() for a, b in long_gaps])
    pre = np.mean([db[max(a - 3, 0):a].mean() for a, b in long_gaps])
    res.update({"long_gaps_n": len(long_gaps), "db_before_gap": round(float(pre), 1), "db_gap_first2s": round(float(first), 1),
                "db_gap_middle": round(float(mid), 1), "db_gap_last2s": round(float(last), 1),
                "mid_minus_speech_db": round(float(mid - np.median(db[speech & valid])), 1)})
res["longest_gaps"] = [[int(a), int(b)] for a, b in sorted(gaps, key=lambda g: g[0] - g[1])[:5]]
json.dump(res, open(out, "w"), indent=1)
print(json.dumps(res))
