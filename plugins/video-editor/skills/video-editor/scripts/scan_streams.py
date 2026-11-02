"""Rank long travel/IRL videos by how much non-speech room they have, using only captions (no media download).
Usage: python -I scan_streams.py <out.json> <query> [<query> ...]
"""
import json, re, sys, tempfile, pathlib
from yt_dlp import YoutubeDL

out, queries = sys.argv[1], sys.argv[2:]
cand = {}
with YoutubeDL({"quiet": True, "no_warnings": True, "extract_flat": True, "skip_download": True}) as y:
    for q in queries:
        for e in y.extract_info(f"ytsearch20:{q}", download=False).get("entries", []):
            d, v = e.get("duration") or 0, e.get("view_count") or 0
            if 3600 <= d <= 18000 and v >= 150000:
                cand[e["id"]] = {"id": e["id"], "title": e.get("title"), "channel": e.get("channel"), "dur": d, "views": v}
rows = []
tmp = pathlib.Path(tempfile.mkdtemp())
for vid, c in sorted(cand.items(), key=lambda kv: -kv[1]["views"])[:14]:
    with YoutubeDL({"quiet": True, "no_warnings": True, "skip_download": True, "writeautomaticsub": True, "writesubtitles": True,
                    "subtitleslangs": ["en.*"], "subtitlesformat": "vtt", "outtmpl": str(tmp / "%(id)s")}) as y:
        try:
            y.extract_info(f"https://www.youtube.com/watch?v={vid}", download=True)
        except Exception as ex:
            continue
    f = list(tmp.glob(vid + "*.vtt"))
    if not f:
        c["note"] = "no captions"; rows.append(c); continue
    ivs = [(int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]), int(m[4]) * 3600 + int(m[5]) * 60 + float(m[6]))
           for m in re.finditer(r"(\d+):(\d+):([\d.]+) --> (\d+):(\d+):([\d.]+)", f[0].read_text(encoding="utf-8"))]
    ivs.sort(); gaps, end = [], 0
    for a, b in ivs:
        if a - end >= 6: gaps.append((end, a))
        end = max(end, b)
    c.update({"gaps_6s": len(gaps), "gap_minutes": round(sum(b - a for a, b in gaps) / 60, 1), "gaps_per_hour": round(len(gaps) / (c["dur"] / 3600)),
              "longest_gap_s": int(max((b - a for a, b in gaps), default=0))})
    rows.append(c)
json.dump(rows, open(out, "w"), indent=1)
for c in sorted(rows, key=lambda c: -c.get("gaps_per_hour", -1)):
    print(c["id"], f"{c['dur']/3600:.1f}h", c["views"] // 1000, "K", "gaps>=6s/h:", c.get("gaps_per_hour"), "longest", c.get("longest_gap_s"), "|", (c["channel"] or "")[:14], "|", c["title"][:48].encode("ascii", "replace").decode(), c.get("note", ""))
