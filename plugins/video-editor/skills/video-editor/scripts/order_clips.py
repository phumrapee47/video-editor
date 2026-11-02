"""Propose a timeline order for several clips from their timestamps, and flag clips that need the user's check.

Usage: python -I order_clips.py <file_or_folder> [<file_or_folder> ...]
Time sources, best first: Apple creation date (has timezone), container creation_time (UTC), date in the file name
(VID_20241101_142530, 2024-11-01 14.25.30), file modified time (weakest, changes when files are copied).
Flags: missing or weak timestamps, clips sharing one timestamp (batch export / messaging app), overlapping clips
(two cameras or a wrong clock), big jumps. It only orders by recording time; the story order may differ, so the user confirms.
"""
import datetime as dt, json, pathlib, re, subprocess, sys

EXT = {".mp4", ".mov", ".m4v", ".mkv", ".avi", ".webm", ".mts"}
NAME_RE = re.compile(r"(20\d{2})[-_.]?(\d{2})[-_.]?(\d{2})[-_ T.]?(\d{2})[-_.]?(\d{2})[-_.]?(\d{2})")


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:format_tags", "-of", "json", str(path)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    f = json.loads(r.stdout or "{}").get("format", {})
    return float(f.get("duration") or 0), {k.lower(): v for k, v in (f.get("tags") or {}).items()}


def parse_iso(s):
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def clip_time(path, tags):
    t = tags.get("com.apple.quicktime.creationdate")
    if t and parse_iso(t):
        return parse_iso(t), "apple creation date", "high"
    t = tags.get("creation_time")
    if t and parse_iso(t):
        return parse_iso(t), "container creation_time (UTC)", "high"
    m = NAME_RE.search(path.stem)
    if m:
        try:
            return dt.datetime(*map(int, m.groups()), tzinfo=dt.timezone.utc), "file name", "medium"
        except ValueError:
            pass
    return dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.timezone.utc), "file modified time", "low"


files = []
for a in sys.argv[1:]:
    p = pathlib.Path(a)
    files += sorted(x for x in p.iterdir() if x.suffix.lower() in EXT) if p.is_dir() else [p]
rows = []
for f in files:
    dur, tags = probe(f)
    t, src, conf = clip_time(f, tags)
    rows.append({"file": f.name, "start": t.astimezone(dt.timezone.utc), "dur": dur, "src": src, "conf": conf})
rows.sort(key=lambda r: r["start"])

# creation_time is the start of recording on most phones, the end on some cameras: use gaps only as a hint
notes = [[] for _ in rows]
for i, r in enumerate(rows):
    if r["conf"] == "low":
        notes[i].append("weak timestamp (file modified time): confirm order")
    same = [j for j, o in enumerate(rows) if j != i and abs((o["start"] - r["start"]).total_seconds()) < 2]
    if same:
        notes[i].append("shares a timestamp with another clip (batch export?): order is a guess")
    if i and (rows[i - 1]["start"] + dt.timedelta(seconds=rows[i - 1]["dur"]) > r["start"] + dt.timedelta(seconds=1)):
        notes[i].append("overlaps the previous clip (two cameras or wrong clock)")
srcs = {r["src"] for r in rows}
if len(srcs) > 1:
    for n in notes:
        n.append("mixed time sources across clips")
print(f"{'#':>2}  {'start (UTC)':19}  {'len s':>6}  {'source':28} conf    file")
for i, (r, n) in enumerate(zip(rows, notes), 1):
    print(f"{i:>2}  {r['start']:%Y-%m-%d %H:%M:%S}  {r['dur']:6.1f}  {r['src']:28} {r['conf']:6}  {r['file']}" + (("   <- " + "; ".join(dict.fromkeys(n))) if n else ""))
gaps = [(rows[i]["start"] - rows[i - 1]["start"]).total_seconds() / 3600 for i in range(1, len(rows))]
if gaps and max(gaps) > 6:
    print(f"\nNote: largest gap between starts is {max(gaps):.1f} h, so these may belong to different days or trips.")
print("\nThis is recording order. Confirm with the user whether the story should follow it.")
