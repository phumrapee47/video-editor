"""Measure cut rhythm of a long video (scene detection, shots under 0.25s merged).

Usage: python -I cut_rhythm.py <video.mp4> <out.json>
Reports overall shot length, share of short/long shots, first-3-minutes vs rest, and cuts/min per 5-minute block.
Scene detection misses soft transitions (dissolves, slow pans) and fires on camera shake, so treat results as approximate.
"""
import json, re, subprocess, sys
import numpy as np

video, out = sys.argv[1:3]
err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", video, "-vf", "select='gt(scene,0.3)',showinfo", "-an", "-f", "null", "-"],
                     capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
dur = float(re.search(r"Duration: (\d+):(\d+):([\d.]+)", err).expand(r"\1")) * 3600 + float(re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)[2]) * 60 + float(re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)[3])
cuts = [float(t) for t in re.findall(r"pts_time:([\d.]+)", err)]
cuts = [t for i, t in enumerate(cuts) if i == 0 or t - cuts[i - 1] >= 0.25]
gaps = np.diff([0] + cuts + [dur])
c = np.array(cuts)
res = {
    "minutes": round(dur / 60, 1), "shots": len(gaps), "avg_shot_s": round(dur / len(gaps), 2),
    "median_shot_s": round(float(np.median(gaps)), 2), "p90_shot_s": round(float(np.percentile(gaps, 90)), 1),
    "shots_under_2s_pct": round(float((gaps < 2).mean() * 100)), "shots_over_8s_pct": round(float((gaps > 8).mean() * 100)),
    "cuts_per_min_first3": round(float((c < 180).sum() / 3), 1), "cuts_per_min_rest": round(float((c >= 180).sum() / max(dur / 60 - 3, 1)), 1),
    "cuts_per_min_by_5min": [round(float(((c >= a) & (c < a + 300)).sum() / min(5, (dur - a) / 60)), 1) for a in range(0, int(dur), 300)],
}
json.dump(res, open(out, "w"), indent=1)
print(json.dumps(res))
