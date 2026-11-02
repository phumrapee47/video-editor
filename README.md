# 🎬 video-editor — Claude Code skill

[English](#english) · [ภาษาไทย](#ภาษาไทย)

## English

A Claude Code skill that edits video with ffmpeg and Python: finding the best moments in a livestream or long video, making vertical Shorts with subtitles, placing background music at the right moments, and building 2.5D animations from real photos synced to a narration.

Every rule in the skill comes from real experiments and a viewer's scores, not guesswork. The latest test clip scored **9.5/10**.

### 📦 Install

```
/plugin marketplace add phumrapee47/video-editor
/plugin install video-editor@video-editor
```

Update to the latest version:

```
/plugin marketplace update video-editor
```

**Manual install (personal skill):** copy `plugins/video-editor/skills/video-editor` to `~/.claude/skills/`, then call it with `/video-editor`.

### Requirements

- **ffmpeg** (tested with 9.0.1), runnable from the command line
- **Python 3.11** with `numpy` and `Pillow`
- **yt-dlp** to fetch video metadata and subtitles from YouTube
- **rembg** (`pip install "rembg[cpu]"`) to remove photo backgrounds (downloads its model on first use)
- **faster-whisper** (optional) for English transcription with word timestamps (Thai does not work yet; see Limits)

### What it does

**1. 2.5D animation from a narration**
- Storyboards the narration with a shot change about every 3 seconds, landing visuals on key words
- Finds freely licensed real photos on Wikimedia Commons, removes backgrounds, and keeps the credits
- Layers images in depth, grades every photo to one look, and adds real moving atmosphere (clouds, smoke, ash)
- Camera shake and sound effects only where the story is tense or exciting; explainer diagrams and call-outs; whip-pan transitions
- Checks that the hero subject is never cropped (`scripts/check_cutout.py`) and sends a preview before the full render

**2. Highlights from livestreams or long videos, cut into short clips**
- Keeps storytelling, interaction with people, showing something, and punchlines; drops dead air and aimless walking
- Uses the transcript, loudness, and YouTube's replay heatmap to find candidates, then checks the frames
- Makes 9:16 vertical clips with subtitles and loudness set per style

**3. Music and sound**
- No music while people talk; music fades in only during scenery or whatever the camera is showing, and fades out before speech returns (ducked on subtitle timestamps)
- Picks the music genre from the setting, and always runs a level calibration before asking a listener to judge

**4. Basic editing**
- Cut, join, crop, speed change, subtitles, loudness, export
- Orders several clips by their recording timestamps (`scripts/order_clips.py`), then asks the user to confirm

### Test results

| What was tested | Result |
|---|---|
| Animation v1 (geometric shapes in Blender) | Rejected: "not pretty at all", use real photos |
| Animation v2 (real photo cut-outs, layered) | 6/10: whole clip shook, too much empty space |
| Animation v3 (mood-based shake, layered temples, mood sound) | 8/10, passed: the sky was still generated, not a photo |
| Animation with the v4 rules (Pompeii clip) | **9.5/10**: "understands the mood and context"; minus 0.5 for cropping the hero subject |
| Ducking music under speech | Subtitle-timestamp ducking beat a sidechain compressor in a listening test |
| Audible music level under speech | 20 dB below speech: inaudible; 10-15 dB: audible |
| Highlight finder | "Good enough" |

### Demos

The videos in `demos/` are real results from the tests, but **the narration and subtitles were removed** because the narration belongs to the original creator. What remains is the picture, on-screen text, and sound effects.

- [`demos/pompeii_demo.mp4`](demos/pompeii_demo.mp4): Pompeii, bodies frozen in time (85 s)
- [`demos/roro_jonggrang_demo.mp4`](demos/roro_jonggrang_demo.mp4): the legend of Roro Jonggrang (81 s)

Credits for every photo, footage clip, and sound are in [`demos/CREDITS.md`](demos/CREDITS.md). The demo videos are released under CC BY-SA 4.0, as required by the source photos.

### Limits

- Claude cannot hear. Music fit, mix balance, and humor need a human listener.
- Whisper small cannot transcribe Thai; the skill uses YouTube's Thai auto captions corrected by hand, so visuals are timed to 2-3 s caption chunks, not to individual words.
- YouTube videos may include an AI-dubbed audio track; choose the original track (see `references/ffmpeg-recipes.md`).
- Other people's audio or video is for local testing only. Publishing it needs permission; credit alone is not enough.

---

## ภาษาไทย

Skill สำหรับ Claude Code ที่ตัดต่อวิดีโอด้วย ffmpeg และ Python ตั้งแต่หาช่วงเด็ดในไลฟ์หรือคลิปยาว ทำ Shorts แนวตั้งพร้อมซับ วางเพลงประกอบให้ถูกจังหวะ ไปจนถึงสร้างแอนิเมชัน 2.5D จากภาพจริงตามเสียงบรรยาย

กฎทุกข้อใน skill มาจากการทดลองจริงและการให้คะแนนของคนดู ไม่ได้มาจากการเดา คลิปทดสอบล่าสุดได้ **9.5/10**

### 📦 ติดตั้ง

```
/plugin marketplace add phumrapee47/video-editor
/plugin install video-editor@video-editor
```

อัปเดตเป็นเวอร์ชันล่าสุด:

```
/plugin marketplace update video-editor
```

**ติดตั้งแบบ manual (personal skill):** คัดลอกโฟลเดอร์ `plugins/video-editor/skills/video-editor` ไปไว้ที่ `~/.claude/skills/` แล้วเรียกด้วย `/video-editor`

### สิ่งที่ต้องมี

- **ffmpeg** (ทดสอบกับ 9.0.1) สั่งรันจาก command line ได้
- **Python 3.11** พร้อม `numpy` และ `Pillow`
- **yt-dlp** สำหรับดึงข้อมูลคลิปและซับจาก YouTube
- **rembg** (`pip install "rembg[cpu]"`) สำหรับตัดฉากหลังของภาพ (โหลดโมเดลครั้งแรกที่ใช้)
- **faster-whisper** (ไม่บังคับ) ถอดเสียงภาษาอังกฤษพร้อมเวลาระดับคำ (ภาษาไทยยังใช้ไม่ได้ ดูข้อจำกัด)

### ทำอะไรได้บ้าง

#### 1. แอนิเมชัน 2.5D จากเสียงบรรยาย
- วางสตอรีบอร์ดตามเสียงบรรยาย เปลี่ยนช็อตทุกราว 3 วินาที ผูกภาพกับคำสำคัญ
- หาภาพจริงที่ใช้ได้ตามลิขสิทธิ์จาก Wikimedia Commons ตัดฉากหลัง และเก็บเครดิตให้
- ซ้อนชั้นมีมิติ ปรับสีชุดเดียวทั้งคลิป ใส่บรรยากาศเคลื่อนไหวจริง (เมฆ ควัน เถ้า)
- ภาพสั่นและเสียงประกอบเฉพาะช่วงที่มีอารมณ์ มีแผนภาพอธิบายและเส้นชี้ เปลี่ยนฉากแบบกวาดกล้อง
- ตรวจว่าวัตถุหลักไม่ถูกครอปขาด (`scripts/check_cutout.py`) และส่งพรีวิวก่อนเรนเดอร์เต็ม

#### 2. หาช่วงเด็ดจากไลฟ์หรือคลิปยาว แล้วทำคลิปสั้น
- เก็บเฉพาะการเล่าเรื่อง ปฏิสัมพันธ์ การโชว์ของ และมุก ตัดช่วงเงียบและการเดินเรื่อยๆ
- ใช้บทพูด ความดังเสียง และ heatmap ของ YouTube หาจุดเริ่ม แล้วดูภาพยืนยัน
- ทำแนวตั้ง 9:16 พร้อมซับ และปรับระดับเสียงตามสไตล์

#### 3. เพลงและเสียง
- ไม่มีเพลงตอนคนพูด เพลงค่อยๆ เข้ามาเฉพาะตอนโชว์วิวหรือสิ่งที่กล้องชี้ แล้วลดลงก่อนเสียงพูดกลับมา (ลดตามเวลาของซับ)
- เลือกแนวเพลงตามสถานที่ และทดสอบระดับเสียงก่อนให้คนฟังตัดสินทุกครั้ง

#### 4. งานตัดต่อพื้นฐาน
- ตัด ต่อ ครอป เร่งความเร็ว ใส่ซับ ปรับความดัง export
- เรียงหลายคลิปตาม timestamp ในไฟล์ (`scripts/order_clips.py`) แล้วให้ผู้ใช้ยืนยัน

### ผลการทดสอบ

| สิ่งที่ทดสอบ | ผล |
|---|---|
| แอนิเมชัน v1 (รูปทรงเรขาคณิตใน Blender) | ไม่ผ่าน: "ไม่สวยเลย" ให้ใช้ภาพจริง |
| แอนิเมชัน v2 (ภาพจริงตัดขอบซ้อนชั้น) | 6/10: ภาพสั่นทั้งคลิป พื้นที่ว่างเยอะ |
| แอนิเมชัน v3 (สั่นตามอารมณ์ วิหารซ้อนหลายชั้น เสียงตามอารมณ์) | 8/10 ผ่าน: ท้องฟ้ายังเป็นภาพที่สร้างเอง |
| แอนิเมชันตามกฎ v4 (คลิปปอมเปอี) | **9.5/10**: "เข้าถึงอารมณ์ เข้าใจบริบททุกอย่าง" หัก 0.5 เพราะครอปวัตถุหลักขาด |
| วิธีลดเสียงเพลงตอนพูด | ลดตามเวลาซับ ชนะ sidechain compressor ในการฟังเทียบ |
| ระดับเพลงที่ได้ยินใต้เสียงพูด | ต่ำกว่า 20 dB ไม่ได้ยิน, 10-15 dB ได้ยิน |
| ตัวหาช่วงเด็ด | "พอใช้ได้" |

### เดโม

วิดีโอใน `demos/` เป็นผลงานจริงจากการทดสอบ แต่**ตัดเสียงบรรยายและซับออก** เพราะเสียงบรรยายเป็นลิขสิทธิ์ของเจ้าของช่อง จึงเหลือภาพ ข้อความ และเสียงประกอบ

- [`demos/pompeii_demo.mp4`](demos/pompeii_demo.mp4): ปอมเปอี ร่างที่หยุดเวลา (85 วินาที)
- [`demos/roro_jonggrang_demo.mp4`](demos/roro_jonggrang_demo.mp4): ตำนาน Roro Jonggrang (81 วินาที)

เครดิตภาพ ฟุตเทจ และเสียงทั้งหมดอยู่ใน [`demos/CREDITS.md`](demos/CREDITS.md) วิดีโอเดโมเผยแพร่ภายใต้ CC BY-SA 4.0 ตามเงื่อนไขของภาพต้นฉบับ

### ข้อจำกัด

- Claude ฟังเสียงไม่ได้ ความเข้ากันของเพลง ความสมดุลเสียง และความตลก ต้องให้คนฟังตัดสิน
- ถอดเสียงภาษาไทยด้วย Whisper รุ่น small ไม่ได้ ตอนนี้ใช้ซับอัตโนมัติของ YouTube แล้วแก้คำผิด จังหวะภาพจึงผูกกับท่อนซับ 2-3 วินาที ไม่ใช่ระดับคำ
- คลิปจาก YouTube อาจมีแทร็กเสียงพากย์อัตโนมัติ ต้องเลือกแทร็กเสียงต้นฉบับให้ถูก (วิธีอยู่ใน `references/ffmpeg-recipes.md`)
- เสียงหรือคลิปของคนอื่นใช้ทดลองในเครื่องเท่านั้น ถ้าจะเผยแพร่ต้องได้รับอนุญาต การใส่เครดิตอย่างเดียวไม่พอ
