"""Fetch public metadata (no video download) for sample clips and write research/meta.json.

Usage: python fetch_meta.py <style> <url> [<url> ...]   (appends to ../research/meta.json)
"""
import json, sys, pathlib
from yt_dlp import YoutubeDL

OUT = pathlib.Path(__file__).resolve().parent.parent / "research" / "meta.json"


def summarize(info, style):
    subs = list((info.get("subtitles") or {}).keys())
    auto = list((info.get("automatic_captions") or {}).keys())
    fmts = info.get("formats") or []
    best = max((f for f in fmts if f.get("height")), key=lambda f: (f["height"], f.get("fps") or 0), default={})
    return {
        "style": style,
        "id": info.get("id"),
        "title": info.get("title"),
        "channel": info.get("channel"),
        "duration_s": info.get("duration"),
        "views": info.get("view_count"),
        "likes": info.get("like_count"),
        "upload_date": info.get("upload_date"),
        "width": best.get("width"),
        "height": best.get("height"),
        "fps": best.get("fps"),
        "chapters": [(c.get("start_time"), c.get("title")) for c in (info.get("chapters") or [])],
        "tags": (info.get("tags") or [])[:12],
        "has_manual_subs": subs[:5],
        "has_auto_caps": bool(auto),
        "description": (info.get("description") or "")[:300],
        "heatmap_points": len(info.get("heatmap") or []),
    }


def main():
    style, urls = sys.argv[1], sys.argv[2:]
    data = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else []
    seen = {d["id"] for d in data}
    with YoutubeDL({"quiet": True, "skip_download": True, "no_warnings": True}) as ydl:
        for u in urls:
            try:
                s = summarize(ydl.extract_info(u, download=False), style)
            except Exception as e:
                print("FAIL", u, str(e)[:100])
                continue
            if s["id"] not in seen:
                data.append(s)
                seen.add(s["id"])
            print("ok", s["id"], s["duration_s"], s["height"], s["fps"])
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


main()
