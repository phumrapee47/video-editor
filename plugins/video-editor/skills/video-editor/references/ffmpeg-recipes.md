# ffmpeg recipes

Replace names in `<angle brackets>`. Always write to a new file.

## Inspect
```bash
ffprobe -v error -show_entries format=duration:stream=codec_type,width,height,r_frame_rate -of default=nw=1 <in.mp4>
ffmpeg -i <in.mp4> -vf fps=1/3,scale=480:-1 frames/f_%03d.jpg        # one frame every 3s
ffmpeg -i <in.mp4> -af silencedetect=n=-35dB:d=0.4 -f null - 2>&1 | grep silence_
ffmpeg -i <in.mp4> -af ebur128=peak=true -f null - 2>&1 | tail -n 12  # loudness summary
```

## Cut and join
```bash
ffmpeg -ss <start> -to <end> -i <in.mp4> -c:v libx264 -crf 18 -c:a aac <clip.mp4>   # re-encode for exact cuts
# join: list.txt lines like  file 'clip1.mp4'
ffmpeg -f concat -safe 0 -i list.txt -c copy <joined.mp4>
```

## Music with ducking under speech
```bash
ffmpeg -i <video.mp4> -i <music.mp3> -filter_complex \
"[1:a]volume=0.5,afade=t=in:d=2[m];[0:a]asplit[v][sc];[m][sc]sidechaincompress=threshold=0.01:ratio=20:attack=300:release=800:makeup=1[duck];[v][duck]amix=inputs=2:duration=first:normalize=0[a]" \
-map 0:v -map "[a]" -c:v copy -c:a aac <out.mp4>
```

Tested on a 60s clip with speech at 0-14s and 46-60s and a 32s gap (Go Went Go audio): threshold 0.05 / ratio 8 ducked 10.2 dB, threshold 0.01 / ratio 20 ducked 17.7 dB, timestamp ducking (below) 15.0 dB, the set depth. An earlier note said the sidechain only reached 6-10 dB on real clips; that was a measurement artifact, because those two clips had continuous speech for the whole 60s and the metric needs a gap to compare against. Always measure depth on a clip that has gaps.

Sidechain cannot anticipate: it reacts about 0.3s after speech starts, so the first word can be partly covered. When a transcript exists, prefer timestamp ducking, which lowers the music 0.5s before speech returns and releases it 1.5s after speech ends (matches `music-rules.md`). Build the gain expression from caption intervals with `gain_expr()` in `scripts/compare_versions.py`, then apply `volume='<expr>':eval=frame` to the music (pass long expressions with `-/filter_complex <file>`; this ffmpeg 9 no longer has `-filter_complex_script`). Use sidechain (0.01 / ratio 20) as the fallback when there is no transcript.

## Ambient sound effect at a time range (for example a waterfall from 12s to 25s)
```bash
ffmpeg -i <video.mp4> -i <waterfall.wav> -filter_complex \
"[1:a]atrim=0:13,afade=t=in:d=1,afade=t=out:st=12:d=1,adelay=12000|12000,volume=0.6[sfx];[0:a][sfx]amix=inputs=2:duration=first:normalize=0[a]" \
-map 0:v -map "[a]" -c:v copy <out.mp4>
```

## Loudness normalize (target set per style, example -14 LUFS; single pass lands within about 1 LU)
```bash
ffmpeg -i <in.mp4> -af loudnorm=I=-14:TP=-1.5:LRA=7 -c:v copy <out.mp4>
```

## Subtitles
```bash
ffmpeg -i <in.mp4> -vf "subtitles=<subs.srt>:force_style='FontName=Noto Sans Thai,FontSize=22,Outline=2,MarginV=40'" -c:a copy <out.mp4>
```

## Vertical 9:16 from 16:9 (center crop) and fade
```bash
ffmpeg -i <in.mp4> -vf "crop=ih*9/16:ih,scale=1080:1920,fade=t=in:d=0.5,fade=t=out:st=<dur-0.5>:d=0.5" -c:a copy <vertical.mp4>
```

## Speed change
```bash
ffmpeg -i <in.mp4> -filter_complex "[0:v]setpts=0.5*PTS[v];[0:a]atempo=2[a]" -map "[v]" -map "[a]" <fast.mp4>
```

## Final export
```bash
ffmpeg -i <in.mp4> -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart <final.mp4>
```

## Picking the right audio track with yt-dlp (lesson 2026-11-02)
Many YouTube videos now carry an AI-dubbed track (`[en-US] ... dubbed-auto`) next to the original (`[th] ... original (default)`).
`-f worstaudio` / `bestaudio` can pick the dub. List tracks with `yt-dlp -F URL`, then choose by language, e.g. `-f "ba[language=th]"`
(or the format id of the "original" track). Narration used for Go Went Go tests before this date was the English AI dub, not the creator's Thai voice.
