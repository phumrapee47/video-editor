"""Score caption windows for highlight beats (interaction, laughter, reveals, excitement) and list the best ones.

Usage: python -I find_beats.py <captions.vtt> <loudness_db_per_second.npy> <out.json> [top_n] [window_s]
Criteria are in references/highlight-criteria.md. Heuristic only: the user rates the picks.
"""
import html, json, re, sys
import numpy as np

vtt, dbf, out = sys.argv[1:4]
top_n = int(sys.argv[4]) if len(sys.argv) > 4 else 12
W = int(sys.argv[5]) if len(sys.argv) > 5 else 25

db = np.load(dbf); n = len(db)
base = np.array([np.median(db[max(0, i - 300): i + 300]) for i in range(0, n, 10)]); base = np.interp(np.arange(n), np.arange(0, n, 10), base)
loud = np.convolve(db, np.ones(5) / 5, mode="same") - base

cues = []
for m in re.finditer(r"(\d+):(\d+):([\d.]+) --> (\d+):(\d+):([\d.]+)[^\n]*\n(.*?)(?:\n\n|$)", open(vtt, encoding="utf-8").read(), re.S):
    t = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])
    raw = html.unescape(re.sub(r"<[^>]+>", "", m[7]))
    lines = [l.strip() for l in raw.split("\n") if l.strip()]
    if lines and (not cues or cues[-1][1] != lines[-1]):
        cues.append((t, lines[-1]))

REVEAL = re.compile(r"\b(look|check (this|it) out|no way|oh my god|oh my gosh|what the|bro look|watch this|see that|are you serious|wait wait)\b", re.I)
score = np.zeros(n)
for t, s in cues:
    i = int(t)
    if i >= n:
        continue
    v = 0.0
    v += 3.0 * len(re.findall(r"\[(laughter|laughing|applause|screaming|cheering)\]", s, re.I))
    v += 1.0 * s.count(">>")
    v += 1.5 * len(REVEAL.findall(s))
    v += 0.5 * s.count("!") + 0.3 * s.count("?")
    score[i] += v
win = np.convolve(score, np.ones(W), mode="same") + 0.25 * np.convolve(np.clip(loud, 0, None), np.ones(W), mode="same") / W * 10
density = np.convolve(np.array([1.0 if any(int(t) == i for t, _ in cues[:0]) else 0 for i in range(0)]), [1]) if False else None

picks, used = [], np.zeros(n, bool)
for i in np.argsort(-win):
    if i < 90 or i > n - 90 or used[max(0, i - 60): i + 60].any():
        continue
    used[max(0, i - 60): i + 60] = True
    a = int(i - W // 2); b = int(i + W // 2)
    text = " | ".join(s for t, s in cues if a <= t < b)
    picks.append({"center_s": int(i), "start_s": a, "end_s": b, "score": round(float(win[i]), 1), "text": text[:420]})
    if len(picks) >= top_n:
        break
json.dump(picks, open(out, "w"), indent=1, ensure_ascii=False)
for p in picks:
    c = p["center_s"]
    print(f"{c // 3600}:{c % 3600 // 60:02d}:{c % 60:02d} score {p['score']:5.1f} | {p['text'][:200]}".encode("ascii", "replace").decode())
