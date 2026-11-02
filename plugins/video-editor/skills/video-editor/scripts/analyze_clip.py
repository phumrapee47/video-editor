"""Measure cut rhythm and loudness of a local clip with ffmpeg; append to research/analysis.json.

Usage: python -I analyze_clip.py <style> <video.mp4> [scene_threshold]
"""
import json, re, subprocess, sys, pathlib, statistics as st

OUT = pathlib.Path(__file__).resolve().parent.parent / "research" / "analysis.json"


def run(args):
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostats", *args], capture_output=True, text=True, encoding="utf-8", errors="replace").stderr


def duration(path):
    err = run(["-i", path])
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)
    return int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])


def cuts(path, thr):
    err = run(["-i", path, "-vf", f"select='gt(scene,{thr})',showinfo", "-an", "-f", "null", "-"])
    return [float(x) for x in re.findall(r"pts_time:([\d.]+)", err)]


def loudness(path):
    err = run(["-i", path, "-af", "ebur128=peak=true,silencedetect=n=-45dB:d=0.5", "-vn", "-f", "null", "-"])
    mom = [(float(t), float(m)) for t, m in re.findall(r"t:\s*([\d.]+)\s.*?M:\s*(-?[\d.]+)", err)]
    summ = err[err.rfind("Summary:"):] if "Summary:" in err else ""
    g = lambda k: (re.search(k + r":\s*(-?[\d.]+)", summ) or [None, None])[1]
    sil = sum(float(d) for d in re.findall(r"silence_duration: ([\d.]+)", err))
    win = {}
    for t, m in mom:
        if m > -70:
            win.setdefault(int(t // 5), []).append(m)
    means = [sum(v) / len(v) for _, v in sorted(win.items())]
    return {
        "integrated_lufs": float(g("I")) if g("I") else None,
        "lra": float(g("LRA")) if g("LRA") else None,
        "true_peak_dbtp": float(g("Peak")) if g("Peak") else None,
        "silence_s": round(sil, 1),
        "win5s_lufs_range": [round(min(means), 1), round(max(means), 1)] if means else None,
        "win5s_lufs_stdev": round(st.pstdev(means), 2) if len(means) > 1 else None,
    }


def main():
    style, path = sys.argv[1], sys.argv[2]
    thr = float(sys.argv[3]) if len(sys.argv) > 3 else 0.3
    dur = duration(path)
    c = cuts(path, thr)
    c = [t for i, t in enumerate(c) if i == 0 or t - c[i - 1] >= 0.25]  # drop detector flicker (<0.25s apart)
    gaps = [b - a for a, b in zip([0] + c, c + [dur])]
    res = {
        "style": style, "file": pathlib.Path(path).stem, "duration_s": round(dur, 1), "scene_threshold": thr,
        "shots": len(gaps), "avg_shot_s": round(dur / len(gaps), 2),
        "median_shot_s": round(st.median(gaps), 2), "shortest_s": round(min(gaps), 2), "longest_s": round(max(gaps), 2),
        "cuts_per_min": round(len(c) / dur * 60, 1), **loudness(path),
    }
    data = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else []
    data = [d for d in data if d["file"] != res["file"]] + [res]
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False))


main()
