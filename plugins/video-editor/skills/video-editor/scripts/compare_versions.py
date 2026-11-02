"""Render the same test clips with every skill version's audio settings, measure, write comparison.md.

Layout (workspace = ../../video-editor-workspace):
  versions/<name>.json   settings of one skill version. Two modes:
      sidechain (default): {"duck_threshold":0.01,"duck_ratio":20,"music_gain":0.5,"target_lufs":-14}
      timestamp:           {"mode":"timestamp","depth_db":15,"lead_s":0.5,"release_s":1.5,"music_gain":0.5,"target_lufs":-14}
  real-clips/*.mp4       test clips (other people's footage; local use only, never published)
  real-clips/<clip>*.vtt captions of the clip (needed by timestamp mode); real-clips/offset.json maps clip -> start second in the source video
  music.mp3              stand-in music bed
Outputs: outputs/<version>/<clip>.mp4 and comparison.md (all versions side by side).

Usage: python -I compare_versions.py
Add a new version by dropping a new JSON into versions/. Add a metric by extending measure().
"""
import json, math, pathlib, re, subprocess, wave, array, datetime, tempfile

WS = pathlib.Path(__file__).resolve().parents[2] / "video-editor-workspace"
CLIP_LEN = 60


def ff(*a):
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-y", *a], capture_output=True, text=True, encoding="utf-8", errors="replace").stderr


def speech_intervals(clip):
    """Speech intervals (seconds, relative to the clip) from the caption file, merged when closer than 2s."""
    vtts = sorted((WS / "real-clips").glob(clip.stem + "*.vtt"))
    offset = json.loads((WS / "real-clips" / "offset.json").read_text()).get(clip.stem, 0)
    cues = []
    for m in re.finditer(r"(\d+):(\d+):([\d.]+) --> (\d+):(\d+):([\d.]+)", vtts[0].read_text(encoding="utf-8")):
        a = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) - offset
        b = int(m[4]) * 3600 + int(m[5]) * 60 + float(m[6]) - offset
        if b > 0 and a < CLIP_LEN:
            cues.append((max(a, 0), min(b, CLIP_LEN)))
    cues.sort()
    merged = []
    for a, b in cues:
        if merged and a - merged[-1][1] < 2:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return merged


def gain_expr(intervals, cfg):
    """Music gain over time: base level, lowered by depth_db from lead_s before speech until release_s after it."""
    hi = cfg["music_gain"]
    lo = hi * 10 ** (-cfg["depth_db"] / 20)
    lead, rel = cfg["lead_s"], cfg["release_s"]
    bumps = [f"clip(min((t-{a - lead:.2f})/0.4,({b + rel:.2f}-t)/{rel}),0,1)" for a, b in intervals]
    mx = bumps[0] if bumps else "0"
    for b in bumps[1:]:
        mx = f"max({mx},{b})"
    return f"{hi}-({hi - lo:.5f})*{mx}"


def music_chain(clip, cfg, fade_in):
    """Filter text that turns [1:a] into the ducked music stream [duck] (needs [0:a] split to [sc] for sidechain mode)."""
    if cfg.get("mode") == "timestamp":
        return f"[1:a]volume='{gain_expr(speech_intervals(clip), cfg)}':eval=frame{fade_in}[duck];", False
    return (f"[1:a]volume={cfg['music_gain']}{fade_in}[m];[0:a]asplit[v][sc];"
            f"[m][sc]sidechaincompress=threshold={cfg['duck_threshold']}:ratio={cfg['duck_ratio']}:attack=300:release=800:makeup=1[duck];"), True


def run_graph(clip, music, graph, maps, out, extra=()):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(graph)
    return ff("-i", str(clip), "-i", str(music), "-t", str(CLIP_LEN), "-/filter_complex", f.name, *maps, *extra, str(out))


def duck_stem(clip, music, cfg, out):
    chain, _ = music_chain(clip, cfg, "")
    if cfg.get("mode") == "timestamp":
        graph = chain.rstrip(";")
    else:  # the stem graph does not need the speech copy
        graph = (f"[1:a]volume={cfg['music_gain']}[m];[m][0:a]sidechaincompress=threshold={cfg['duck_threshold']}:"
                 f"ratio={cfg['duck_ratio']}:attack=300:release=800:makeup=1[duck]")
    run_graph(clip, music, graph, ["-map", "[duck]", "-ac", "1", "-ar", "8000"], out)


def duck_depth(wav):
    """95th minus 5th percentile of 0.5s RMS (dB) of the ducked music stem = how far music drops under speech."""
    with wave.open(str(wav)) as w:
        s = array.array("h", w.readframes(w.getnframes())); n = w.getframerate() // 2
    lv = sorted(20 * math.log10(max(math.sqrt(sum(x * x for x in s[i:i + n]) / n), 1) / 32768) for i in range(0, len(s) - n, n))
    return None if len(lv) < 10 else round(lv[int(len(lv) * .95)] - lv[int(len(lv) * .05)], 1)


def render(clip, music, cfg, out):
    chain, split = music_chain(clip, cfg, ",afade=t=in:d=2")
    src = "[v]" if split else "[0:a]"
    graph = f"{chain}{src}[duck]amix=inputs=2:duration=first:normalize=0,loudnorm=I={cfg['target_lufs']}:TP=-1.5:LRA=11[a]"
    return run_graph(clip, music, graph, ["-map", "0:v", "-map", "[a]"], out, ["-c:v", "copy", "-c:a", "aac"])


def measure(out):
    e = ff("-i", str(out), "-af", "ebur128=peak=true", "-vn", "-f", "null", "-")
    s = e[e.rfind("Summary:"):]
    g = lambda k: float(re.search(k + r":\s*(-?[\d.]+)", s)[1])
    d = re.search(r"Duration: (\d+):(\d+):([\d.]+)", ff("-i", str(out)))
    return {"lufs": g("I"), "lra": g("LRA"), "peak": g("Peak"), "dur": round(int(d[1]) * 3600 + int(d[2]) * 60 + float(d[3]), 1)}


def main():
    music = WS / "music.mp3"
    versions = {p.stem: json.loads(p.read_text()) for p in sorted((WS / "versions").glob("*.json"))}
    clips = sorted((WS / "real-clips").glob("*.mp4"))
    rows = []
    for v, cfg in versions.items():
        for c in clips:
            od = WS / "outputs" / v; od.mkdir(parents=True, exist_ok=True)
            out, stem = od / c.name, od / (c.stem + "_stem.wav")
            out.unlink(missing_ok=True); stem.unlink(missing_ok=True)
            err = render(c, music, cfg, out); duck_stem(c, music, cfg, stem)
            if not out.exists():
                raise SystemExit(f"render failed for {v}/{c.name}: {err[-600:]}")
            m = measure(out); m["duck_db"] = duck_depth(stem) if stem.exists() else None; stem.unlink(missing_ok=True)
            rows.append((v, c.stem, m))
    md = [f"# Version comparison ({datetime.date.today()})", "", "Same clips, same stand-in music; only the version settings differ.",
          "`duck_db` = how far the music drops under speech (target 12-18). `lufs` = final loudness (target = each version's `target_lufs`).", "",
          "| version | settings | clip | duck_db | LUFS | LRA | true peak | dur s |", "|---|---|---|---|---|---|---|---|"]
    for v, c, m in rows:
        cfg = versions[v]
        desc = (f"timestamp, depth {cfg['depth_db']} dB, lead {cfg['lead_s']}s, release {cfg['release_s']}s" if cfg.get("mode") == "timestamp"
                else f"sidechain thr {cfg['duck_threshold']}, ratio {cfg['duck_ratio']}") + f", tgt {cfg['target_lufs']}"
        md.append(f"| {v} | {desc} | {c} | {m['duck_db']} | {m['lufs']} | {m['lra']} | {m['peak']} | {m['dur']} |")
    (WS / "comparison.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


main()
