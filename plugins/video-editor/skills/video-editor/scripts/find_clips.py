"""Find candidate clips per style with yt-dlp search (metadata only). Writes research/candidates.json.

Usage: python -I find_clips.py
"""
import json, pathlib
from yt_dlp import YoutubeDL

ROOT = pathlib.Path(__file__).resolve().parent.parent / "research"
# style -> (queries, min_s, max_s)
STYLES = {
    "cinematic": (["cinematic travel film 4k", "cinematic travel vlog"], 60, 1500),
    "bright_vlog": (["bright fun travel vlog with friends", "happy vlog aesthetic day trip"], 240, 1500),
    "funny_fastcut": (["funny travel vlog fast cuts comedy", "funny vlog skit edit jump cuts"], 120, 1200),
    "storytelling": (["travel documentary storytelling short film", "storytime vlog documentary edit"], 240, 1500),
    "shorts": (["travel shorts vlog", "funny vlog shorts", "cinematic travel shorts"], 5, 60),
    "thai": (["เที่ยว vlog ไทย", "รีวิวเที่ยว วล็อก"], 240, 1800),
    "thai_short": (["เที่ยว shorts ไทย", "ตลก shorts เที่ยว"], 5, 60),
    "animation3d": (["cute 3d animation car short", "low poly 3d animation short blender"], 5, 300),
    "motion_graphic": (["motion graphics short animation kinetic typography", "2d animation explainer short"], 20, 300),
}
PER_STYLE = 6
MIN_VIEWS = 100_000

known = {d["id"] for d in json.loads((ROOT / "meta.json").read_text(encoding="utf-8"))}
out = {}
with YoutubeDL({"quiet": True, "no_warnings": True, "extract_flat": True, "skip_download": True}) as ydl:
    for style, (queries, lo, hi) in STYLES.items():
        seen, rows = set(known), []
        for q in queries:
            try:
                res = ydl.extract_info(f"ytsearch25:{q}", download=False)
            except Exception as e:
                print("FAIL", q, str(e)[:80])
                continue
            for e in res.get("entries", []):
                d, v = e.get("duration"), e.get("view_count") or 0
                if e["id"] in seen or not d or not (lo <= d <= hi) or v < MIN_VIEWS:
                    continue
                seen.add(e["id"])
                rows.append({"id": e["id"], "title": e.get("title"), "channel": e.get("channel"), "duration_s": d, "views": v,
                             "url": f"https://www.youtube.com/watch?v={e['id']}"})
        rows.sort(key=lambda r: -r["views"])
        out[style] = rows[:PER_STYLE]
        print(style, len(rows), "->", len(out[style]))
(ROOT / "candidates.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
