"""Add a music bed to a finished short, ducked from caption timestamps (the "v3" method in references/music-rules.md).

Usage: python -I add_music.py <short.mp4> <captions.vtt> <clip_start_in_source_s> <music.mp3> <out.mp4> [bed_db] [depth_db]
 bed_db   level of the music in gaps, relative to the speech loudness (default -8)
 depth_db extra drop while someone speaks (default 30: music is effectively off while someone talks; use 4 only for a deliberate music-under-talk test, where 10 dB under speech was audible and 20 dB was not)
The music is loudness-matched first (-14 LUFS), then scaled by bed_db. It lowers 0.5s before speech and recovers 1.5s after it.
"""
import html, pathlib, re, subprocess, sys, tempfile

short, vtt, start, music, out = sys.argv[1:6]
bed_db = float(sys.argv[6]) if len(sys.argv) > 6 else -8.0
depth_db = float(sys.argv[7]) if len(sys.argv) > 7 else 30.0
start = float(start)
LEAD, REL = 0.5, 1.5


def duration(path):
    e = subprocess.run(["ffmpeg", "-hide_banner", "-i", path], capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", e)
    return int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])


length = duration(short)
cues = []
for m in re.finditer(r"(\d+):(\d+):([\d.]+) --> (\d+):(\d+):([\d.]+)", open(vtt, encoding="utf-8").read()):
    a = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) - start
    b = int(m[4]) * 3600 + int(m[5]) * 60 + float(m[6]) - start
    if b > 0 and a < length:
        cues.append((max(a, 0), min(b, length)))
cues.sort()
iv = []
for a, b in cues:
    if iv and a - iv[-1][1] < 2:
        iv[-1][1] = max(iv[-1][1], b)
    else:
        iv.append([a, b])

hi = 10 ** (bed_db / 20)
lo = hi * 10 ** (-depth_db / 20)
bumps = [f"clip(min((t-{a - LEAD:.2f})/0.4,({b + REL:.2f}-t)/{REL}),0,1)" for a, b in iv]
mx = bumps[0] if bumps else "0"
for b in bumps[1:]:
    mx = f"max({mx},{b})"
expr = f"{hi:.5f}-({hi - lo:.5f})*{mx}"

graph = (f"[1:a]atrim=0:{length},asetpts=PTS-STARTPTS,loudnorm=I=-14:TP=-2:LRA=7,volume='{expr}':eval=frame,"
         f"afade=t=in:d=1.5,afade=t=out:st={length - 3:.2f}:d=3[m];"
         f"[0:a][m]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-2:LRA=11[a]")
with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
    f.write(graph)
r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", short, "-i", music, "-/filter_complex", f.name,
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out],
                   capture_output=True, text=True)
if r.returncode:
    sys.exit(r.stderr[-500:])
covered = sum(b - a for a, b in iv)
print(f"wrote {out}: speech intervals {len(iv)}, speech {covered:.0f}s of {length:.0f}s, gaps {length - covered:.0f}s")
