"""Render a 9:16 Short from a 16:9 window: blurred background, centered frame, burned subtitles, loudness normalised.

Usage: python -I make_vertical_short.py <window.mp4> <captions.vtt> <window_start_s> <skip_s> <len_s> <out.mp4> [lufs]
Subtitles come from YouTube auto captions via vtt_to_srt.py (errors expected; check before publishing).
"""
import pathlib, subprocess, sys, tempfile

win, vtt, wstart, skip, ln, out = sys.argv[1:7]
lufs = sys.argv[7] if len(sys.argv) > 7 else "-14"
here = pathlib.Path(__file__).resolve().parent
tmp = pathlib.Path(tempfile.mkdtemp())
srt = tmp / "s.srt"
subprocess.run([sys.executable, "-I", str(here / "vtt_to_srt.py"), vtt, wstart, skip, ln, str(srt)], check=True, capture_output=True)
srt_arg = str(srt).replace("\\", "/").replace(":", "\\:")
fc = ("[0:v]split=2[bg][fg];[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:5[b];"
      "[fg]scale=1080:-2[f];[b][f]overlay=0:(H-h)/2[v0];"
      f"[v0]subtitles='{srt_arg}':force_style='Alignment=2,FontSize=11,Bold=1,Outline=2,MarginV=70'[v];"
      f"[0:a]loudnorm=I={lufs}:TP=-2:LRA=11[a]")
subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", skip, "-t", ln, "-i", win, "-filter_complex", fc,
                "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "24", "-preset", "fast", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out], check=True)
print("wrote", out)
