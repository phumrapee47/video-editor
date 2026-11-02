"""Convert YouTube auto-caption VTT (rolling two-line cues) to a clean SRT for one time window.

Usage: python -I vtt_to_srt.py <captions.vtt> <window_start_s> <clip_start_in_window_s> <clip_len_s> <out.srt>
Times in the SRT are relative to the cut clip. Auto captions have errors; show the user the text before burning in.
"""
import html, re, sys

vtt, win, ss, ln, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
t0 = win + ss
ts = lambda m: int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])
cues = []
for m in re.finditer(r"(\d+):(\d+):([\d.]+) --> (\d+):(\d+):([\d.]+)[^\n]*\n(.*?)(?:\n\n|$)", open(vtt, encoding="utf-8").read(), re.S):
    lines = [html.unescape(re.sub(r"<[^>]+>", "", l)).replace(">>", "").strip() for l in m[7].split("\n")]  # ">>" marks a speaker change
    lines = [l for l in lines if l]
    if lines:
        cues.append((ts(m), float(m[4]) * 3600 + float(m[5]) * 60 + float(m[6]), lines[-1]))  # last line = newest text

rows = []
for i, (a, b, text) in enumerate(cues):
    if rows and rows[-1][2] == text:
        continue
    nxt = cues[i + 1][0] if i + 1 < len(cues) else b
    a2, b2 = max(a - t0, 0), min(min(b, nxt + 0.3) - t0, ln)
    if b2 - a2 >= 0.4 and a - t0 < ln and b - t0 > 0:
        rows.append((a2, b2, text))


def f(x):
    return f"{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{int(x % 60):02d},{int(x % 1 * 1000):03d}"


with open(out, "w", encoding="utf-8") as fh:
    for i, (a, b, t) in enumerate(rows, 1):
        fh.write(f"{i}\n{f(a)} --> {f(b)}\n{t}\n\n")
print(len(rows), "subtitle lines")
for a, b, t in rows:
    print(f"{a:5.1f}-{b:5.1f}  {t}")
