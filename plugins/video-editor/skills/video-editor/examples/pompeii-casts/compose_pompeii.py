"""Pompeii: plaster casts (v1 of this clip, built with the v4 rules). 1920x1080, 24 fps, Thai original narration.

Usage: python compose_pompeii.py stills 9,20,30,40,44,57,76,80     -> ./stills/
       python compose_pompeii.py range 17.5 37.5                   -> ./frames/ (preview window)
       python compose_pompeii.py anim                              -> ./frames/ (all)
Rules applied (references/animation-2-5d.md, v4): sub-shots ~3 s, visuals timed to key words, one grade + grain + vignette,
1080p, real moving atmosphere (Bromo time-lapse: sky, clouds, smoke, ash haze), depth of field on cut-out shots, whip pans and a
match cut instead of dips, explainer graphics (cavity diagram, callouts), shake only for the eruption and the fear moment.
No puppet motion on the casts: they are real victims, so they stay still and are treated with respect.
"""
import math, pathlib, random, sys
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

HERE = pathlib.Path(__file__).parent; A = HERE / "assets"; CUT = HERE / "cut"
W, H, FPS, DUR = 1920, 1080, 24, 84.6
random.seed(11); np.random.seed(11)


def ease(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def lerp(t, t0, t1, a, b): return a + (b - a) * ease((t - t0) / (t1 - t0)) if t1 > t0 else b
def pulse(t, t0, t1, f=0.35): return lerp(t, t0, t0 + f, 0, 1) * (1 - lerp(t, t1 - f, t1, 0, 1))


def font(size, thai=True):
    try: return ImageFont.truetype("C:/Windows/Fonts/" + ("LeelaUIb.ttf" if thai else "georgiab.ttf"), size)
    except OSError: return ImageFont.load_default()


# ---- grading: one look for every photo ----------------------------------------------------------------------------------
def grade(im, mood="museum"):
    rgba = im.mode == "RGBA"; a = im.split()[3] if rgba else None; c = im.convert("RGB")
    if mood == "museum": c = ImageEnhance.Color(c).enhance(0.8); c = ImageChops.multiply(c, Image.new("RGB", c.size, (255, 238, 215)))
    elif mood == "sepia": g = ImageOps.grayscale(c); c = ImageOps.colorize(g, (35, 25, 15), (240, 220, 180))
    elif mood == "cold": c = ImageEnhance.Color(c).enhance(0.35); c = ImageChops.multiply(c, Image.new("RGB", c.size, (215, 225, 245)))
    elif mood == "fire": c = ImageEnhance.Contrast(c).enhance(1.15); c = ImageChops.multiply(c, Image.new("RGB", c.size, (255, 200, 160)))
    elif mood == "stone": c = ImageOps.grayscale(c).convert("RGB")
    c = ImageEnhance.Contrast(c).enhance(1.05)
    if rgba: c = c.convert("RGBA"); c.putalpha(a)
    return c


def load(name, mood="museum", w=None):
    im = Image.open(A / f"{name}.jpg").convert("RGB")
    if w: im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    return grade(im, mood).convert("RGBA")


def cutout(name, mood, h=None, w=None):
    im = Image.open(CUT / f"{name}.png").convert("RGBA")
    if h: im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
    if w: im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    return grade(im, mood)


def shadowed(im, s=18):
    pad = s * 3; out = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 255)); sh.putalpha(im.split()[3].point(lambda v: int(v * 0.6)))
    out.alpha_composite(sh, (pad + s // 2, pad + s)); out = out.filter(ImageFilter.GaussianBlur(s / 2)); out.alpha_composite(im, (pad, pad)); return out


def place(frame, im, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if alpha <= 0.01 or scale <= 0.005: return
    if rot: im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    w, h = im.width * scale, im.height * scale; x0, y0 = cx - w / 2, cy - h / 2
    bx, by = math.floor(x0), math.floor(y0); bw, bh = int(math.ceil(w + x0 - bx)) + 1, int(math.ceil(h + y0 - by)) + 1
    if bx >= W or by >= H or bx + bw <= 0 or by + bh <= 0: return
    L = im.transform((bw, bh), Image.AFFINE, (1 / scale, 0, -(x0 - bx) / scale, 0, 1 / scale, -(y0 - by) / scale), resample=Image.BICUBIC)
    if alpha < 0.999: L.putalpha(L.split()[3].point(lambda v: int(v * alpha)))
    full = Image.new("RGBA", (W, H), (0, 0, 0, 0)); full.paste(L, (bx, by)); frame.alpha_composite(full)


def cover(frame, im, t, t0, t1, z=(1.0, 1.06), fx=(0.5, 0.5), fy=(0.5, 0.5), alpha=1.0):
    """Ken-Burns on a full-frame image: zoom range z, focus point moving from fx[0],fy[0] to fx[1],fy[1] (fractions of the image)."""
    base = max(W / im.width, H / im.height); s = base * lerp(t, t0, t1, *z)
    px, py = lerp(t, t0, t1, *fx), lerp(t, t0, t1, *fy)
    cx = W / 2 - (px - 0.5) * im.width * s; cy = H / 2 - (py - 0.5) * im.height * s
    cx = min(max(cx, W - im.width * s / 2), im.width * s / 2); cy = min(max(cy, H - im.height * s / 2), im.height * s / 2)
    place(frame, im, cx, cy, s, alpha)


def label(frame, txt, y, size, t, t0, t1, col=(250, 240, 220), thai=True):
    a = pulse(t, t0, t1, 0.4)
    if a <= 0.01: return
    f = font(size, thai); L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    tw = d.textlength(txt, font=f); x = (W - tw) / 2; yy = y + (1 - a) * 18
    d.text((x + 4, yy + 4), txt, font=f, fill=(0, 0, 0, int(190 * a))); d.text((x, yy), txt, font=f, fill=(*col, int(255 * a))); frame.alpha_composite(L)


def callout(frame, px, py, lx, ly, txt, t, t0, t1):
    """Explainer call-out: a dot on the subject, a line that draws itself, then the text."""
    a = pulse(t, t0, t1, 0.3); k = lerp(t, t0, t0 + 0.6, 0, 1)
    if a <= 0.01: return
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L); c = (245, 210, 120, int(255 * a))
    d.ellipse((px - 12, py - 12, px + 12, py + 12), outline=c, width=4)
    ex, ey = px + (lx - px) * k, py + (ly - py) * k; d.line([(px, py), (ex, ey)], fill=c, width=4)
    if k > 0.95:
        f = font(66); tw = d.textlength(txt, font=f); tx = lx + 14 if lx >= px else lx - tw - 14
        d.rectangle((tx - 16, ly - 46, tx + tw + 16, ly + 46), fill=(20, 16, 12, int(200 * a))); d.text((tx, ly - 42), txt, font=f, fill=(250, 240, 220, int(255 * a)))
    frame.alpha_composite(L)


def footage(name, t, t0, speed=1.0, mood=None, dim=1.0):
    seq = sorted((A / "fx" / name).glob("*.jpg")); i = int((t - t0) * FPS * speed) % len(seq)
    im = Image.open(seq[i]).convert("RGB"); im = im.crop((0, int(im.height * 0.06), im.width, int(im.height * 0.94)))   # trim letterbox
    if mood: im = grade(im, mood).convert("RGB")
    if dim != 1.0: im = ImageEnhance.Brightness(im).enhance(dim)
    return im.resize((W, H), Image.BICUBIC).convert("RGBA")


# ---- assets -------------------------------------------------------------------------------------------------------------
forum = load("forum", "museum", 2400); excav = load("excav1892", "sepia", 2400); excav_blur = excav.filter(ImageFilter.GaussianBlur(10))
cast_photo = load("cast_victim", "stone", 2600); painting = load("painting", "fire", 2600); jewelry = load("jewelry", "museum", 2400)
dark_bg = ImageEnhance.Brightness(forum.filter(ImageFilter.GaussianBlur(14))).enhance(0.28)
cast_cut = shadowed(cutout("cast_victim", "stone", w=1250)); case_cut = shadowed(cutout("cast_close", "cold", w=1500))
case_big = shadowed(cutout("cast_close", "cold", w=3400))
silver_cut = shadowed(cutout("silver", "museum", w=1100)); bread_cut = shadowed(cutout("bread", "museum", h=640)); fiorelli_cut = shadowed(cutout("fiorelli", "sepia", h=820))
mask_src = Image.open(CUT / "cast_victim.png").convert("RGBA")
DIAG_W = 1250; cav = mask_src.resize((DIAG_W, int(mask_src.height * DIAG_W / mask_src.width)), Image.LANCZOS).split()[3]
CAV_X, CAV_Y = (W - cav.width) // 2, 560 - cav.height // 2
ash_tex = ImageEnhance.Brightness(grade(Image.open(sorted((A / "fx" / "ash").glob("*.jpg"))[70]).convert("RGB"), "sepia")).enhance(0.55).resize((W, H)).convert("RGBA")
VIGNETTE = Image.new("L", (W, H), 0); ImageDraw.Draw(VIGNETTE).ellipse((-W * 0.15, -H * 0.25, W * 1.15, H * 1.25), fill=255)
VIGNETTE = VIGNETTE.filter(ImageFilter.GaussianBlur(160))
FLAKES = [(random.uniform(0, W), random.uniform(-H, H), random.uniform(2, 6), random.uniform(60, 160), random.uniform(-30, 30)) for _ in range(260)]


def ash_fall(frame, t, t0, strength=1.0):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L); dt = t - t0
    for x, y, r, v, drift in FLAKES:
        yy = (y + v * dt) % (H * 2) - H * 0.5; xx = (x + drift * dt) % W
        d.ellipse((xx - r, yy - r, xx + r, yy + r), fill=(205, 195, 180, int(150 * strength)))
    frame.alpha_composite(L.filter(ImageFilter.GaussianBlur(1.2)))


def diagram(frame, t, fill=0.0, lift=0.0):
    """Cross-section: night sky above, a layer of volcanic ash with a body-shaped void; plaster fills it; then the ash is dug away."""
    frame.alpha_composite(footage("night", t, 28.0, 0.5, "cold", 0.6))
    ground = ash_tex.copy(); d = ImageDraw.Draw(ground)
    top = Image.new("L", (W, H), 0); ImageDraw.Draw(top).rectangle((0, 300, W, H), fill=255)
    hole = Image.new("L", (W, H), 0); hole.paste(cav, (CAV_X, CAV_Y))
    ground.putalpha(ImageChops.subtract(top, hole))
    if lift < 1.0:
        g = ground.copy(); g.putalpha(g.split()[3].point(lambda v: int(v * (1 - lift))))
        frame.alpha_composite(g)
    void = Image.new("RGBA", (W, H), (8, 6, 5, 255)); void.putalpha(hole.point(lambda v: int(v * 0.95 * (1 - lift)))); frame.alpha_composite(void)
    if fill > 0:
        level = CAV_Y + cav.height * (1 - fill)
        pl = Image.new("L", (W, H), 0); ImageDraw.Draw(pl).rectangle((0, level, W, H), fill=255)
        plaster = Image.new("RGBA", (W, H), (232, 228, 218, 255)); plaster.putalpha(ImageChops.multiply(hole, pl).point(lambda v: int(v * (1 - lift))))
        frame.alpha_composite(plaster)
    if lift > 0: place(frame, cast_cut, W / 2, CAV_Y + cav.height / 2 + 6, DIAG_W / (cast_cut.width - 2 * 54), lift)


# ---- shake only for the eruption and the fear moment --------------------------------------------------------------------
SHAKE = [(19.5, 22.6, 14.0), (63.4, 65.2, 4.0)]


def shake(t):
    amp = sum(a * pulse(t, s, e, 0.25) * (1 - 0.6 * ease((t - s) / (e - s))) for s, e, a in SHAKE if s <= t <= e)
    return amp * math.sin(t * 61) * math.cos(t * 23), amp * math.sin(t * 47 + 1.3)


def shot(t):
    fr = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    if t < 2.0: cover(fr, forum, t, 0, 2, (1.0, 1.07), (0.45, 0.55)); label(fr, "ปอมเปอี  ค.ศ. 79", 90, 84, t, 0.4, 3.8)
    elif t < 4.0: cover(fr, excav, t, 2, 4, (1.08, 1.12), (0.3, 0.7)); label(fr, "ปอมเปอี  ค.ศ. 79", 90, 84, t, 0.4, 3.8)
    elif t < 6.0:
        fr.alpha_composite(excav_blur.resize((W, int(excav_blur.height * W / excav_blur.width))).crop((0, 0, W, H)) if excav_blur.height * W / excav_blur.width >= H else excav_blur.resize((W, H)))
        fr.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 120)))
        place(fr, cast_cut, W / 2, lerp(t, 4, 6, 640, 600), lerp(t, 4, 6, 0.62, 0.68), lerp(t, 4, 4.5, 0, 1)); label(fr, "กว่า 1,000 ร่าง", 120, 110, t, 4.3, 6.0)
    elif t < 8.3: cover(fr, cast_photo, t, 6, 8.3, (1.0, 1.1), (0.5, 0.48))
    elif t < 11.0:
        fr.alpha_composite(dark_bg.resize((W, H))); zt = min(t, 10.9)                       # the zoom stops dead when the clock stops
        place(fr, cast_cut, W / 2, 580, lerp(zt, 8.3, 10.9, 0.78, 0.9)); label(fr, "หยุดเวลาเอาไว้", 110, 96, t, 9.0, 11.0)
    elif t < 14.7:
        fr.alpha_composite(dark_bg.resize((W, H))); place(fr, case_cut, W / 2, 560, lerp(t, 11, 14.7, 0.95, 1.06)); label(fr, "ไม่ใช่ร่างจริง ?", 110, 96, t, 13.7, 14.7)
    elif t < 17.5:
        cover(fr, cast_photo, t, 14.7, 17.5, (1.6, 1.75), (0.42, 0.6)); callout(fr, 900, 560, 1300, 300, "ปูนปลาสเตอร์", t, 15.8, 17.5)
    elif t < 19.5: fr.alpha_composite(footage("night", t, 17.5, 1.0, "cold", 0.9))          # "imagine..." - quiet real night sky
    elif t < 21.5: cover(fr, painting, t, 19.5, 21.5, (1.0, 1.08), (0.5, 0.45)); ash_fall(fr, t, 19.5, 0.6)
    elif t < 24.0:
        cover(fr, painting, t, 21.5, 24, (1.9, 2.1), (0.62, 0.32))
        sm = footage("smoke", t, 21.5, 1.0, "fire", 0.8).convert("RGB"); fr = ImageChops.screen(fr.convert("RGB"), ImageEnhance.Brightness(sm).enhance(0.45)).convert("RGBA")
        ash_fall(fr, t, 21.5, 1.0)
    elif t < 28.0:
        fr.alpha_composite(footage("clouds", t, 24.0, 1.6, "cold", 0.75)); label(fr, "เกือบ 2,000 ปี", 120, 110, t, 24.3, 27.6)
        if t > 26.3: place(fr, cast_cut, W / 2, 640, 0.6, lerp(t, 26.3, 27.6, 0, 0.55))
    elif t < 34.0:
        z = lerp(t, 28, 34, 1.0, 1.12); tmp = Image.new("RGBA", (W, H)); diagram(tmp, t)
        place(fr, tmp, W / 2, H / 2, z); callout(fr, 960, 600, 1420, 330, "โพรง", t, 29.6, 34.0)
    elif t < 38.0:
        cover(fr, excav_blur, t, 34, 38, (1.0, 1.05)); fr.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 90)))
        place(fr, fiorelli_cut, lerp(t, 34, 38, 700, 720), 560, 1.0, lerp(t, 34, 34.6, 0, 1))
        label(fr, "จูเซปเป ฟีออเรลลี  ·  ค.ศ. 1863", 90, 72, t, 35.0, 38.0)
    elif t < 42.5:
        diagram(fr, t, fill=lerp(t, 38.6, 41.8, 0, 1)); label(fr, "เทปูนปลาสเตอร์เหลวลงไป", 110, 84, t, 38.6, 42.4)
    elif t < 46.0:
        diagram(fr, t, fill=1.0, lift=lerp(t, 43.4, 45.2, 0, 1)); label(fr, "ขุดชั้นเถ้าถ่านออก", 110, 84, t, 43.6, 46.0)
    elif t < 50.8: cover(fr, cast_photo, t, 46, 50.8, (1.05, 1.2), (0.5, 0.5))
    elif t < 54.0:
        fr.alpha_composite(dark_bg.resize((W, H))); zt = min(t, 52.5)
        place(fr, grade(case_cut, "stone") if t > 52.5 else case_cut, W / 2, 560, lerp(zt, 50.8, 52.5, 1.0, 1.08)); label(fr, "เวลาหยุดนิ่ง", 110, 96, t, 52.4, 54.0)
    elif t < 58.5:
        fr.alpha_composite(dark_bg.resize((W, H))); place(fr, case_big, lerp(t, 54, 58.5, 1050, 1000), 760, lerp(t, 54, 58.5, 0.93, 1.02))
        callout(fr, 980, 600, 1380, 300, "รอยยับของเสื้อผ้า", t, 57.2, 58.5)
    elif t < 62.0: cover(fr, cast_photo, t, 58.5, 62, (1.7, 1.85), (0.3, 0.55), (0.55, 0.5))
    elif t < 65.5:
        cover(fr, cast_photo, t, 62, 65.5, (2.0, 2.3), (0.8, 0.79), (0.72, 0.7))
        fr.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(lerp(t, 62, 65.5, 40, 120)))))
    elif t < 69.5: cover(fr, forum, t, 65.5, 69.5, (1.12, 1.0), (0.55, 0.45))
    elif t < 74.0: cover(fr, excav, t, 69.5, 74, (1.0, 1.08), (0.7, 0.3))
    elif t < 76.0: cover(fr, jewelry, t, 74, 76, (1.1, 1.2), (0.45, 0.4)); label(fr, "เครื่องประดับ", 110, 96, t, 74.6, 76.0)
    elif t < 78.0:
        fr.alpha_composite(dark_bg.resize((W, H))); place(fr, silver_cut, W / 2, 560, lerp(t, 76, 78, 0.95, 1.03)); label(fr, "เครื่องเงิน", 110, 96, t, 76.1, 78.0)
    elif t < 83.0:
        fr.alpha_composite(dark_bg.resize((W, H))); place(fr, bread_cut, W / 2, 590, lerp(t, 78, 83, 1.0, 1.1), lerp(t, 78, 78.4, 0, 1), rot=lerp(t, 78, 83, 0, 8))
        label(fr, "ขนมปัง อายุเกือบ 2,000 ปี", 110, 90, t, 79.0, 83.0)
    else:
        fr.alpha_composite(dark_bg.resize((W, H)))
        place(fr, silver_cut, 620, 600, 0.6); place(fr, bread_cut, 1300, 600, 0.65); place(fr, cast_cut, 960, 300, 0.45, 0.8)
    return fr


WHIPS = [(17.5, 0.35), (65.5, 0.35)]          # fast camera sweeps between moods (with a whoosh)
MATCH = (43.4, 45.2)                          # the void becomes the cast inside the diagram (match cut handled in diagram())


def render(t):
    fr = shot(t)
    for c, d in WHIPS:
        if abs(t - c) < d:
            k = 1 - abs(t - c) / d; sm = fr.resize((max(1, int(W / (1 + 30 * k))), H), Image.BILINEAR).resize((W, H), Image.BILINEAR)
            off = int((t - c) / d * 400); fr = Image.new("RGBA", (W, H), (0, 0, 0, 255)); fr.alpha_composite(sm, (off, 0)) if off >= 0 else fr.alpha_composite(sm.crop((-off, 0, W, H)), (0, 0))
    dx, dy = shake(t)
    if abs(dx) + abs(dy) > 0.05:
        z = 1.04; fr = fr.transform((W, H), Image.AFFINE, (1 / z, 0, (W - W / z) / 2 - dx, 0, 1 / z, (H - H / z) / 2 - dy), resample=Image.BICUBIC)
    rgb = fr.convert("RGB")
    rgb = Image.composite(rgb, ImageEnhance.Brightness(rgb).enhance(0.45), VIGNETTE)          # vignette
    noise = Image.fromarray(np.random.normal(128, 9, (H // 2, W // 2)).clip(0, 255).astype(np.uint8)).resize((W, H)).convert("RGB")
    rgb = ImageChops.overlay(rgb, noise) if False else Image.blend(rgb, ImageChops.overlay(rgb, noise), 0.5)   # light film grain
    if t > DUR - 0.8: rgb = Image.blend(rgb, Image.new("RGB", (W, H)), lerp(t, DUR - 0.8, DUR, 0, 1))
    return rgb


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "stills":
        out = HERE / "stills"; out.mkdir(exist_ok=True)
        for s in sys.argv[2].split(","): render(float(s)).resize((960, 540), Image.LANCZOS).save(out / f"t{float(s):05.1f}.jpg", quality=88)
    else:
        a, b = (float(sys.argv[2]), float(sys.argv[3])) if mode == "range" else (0.0, DUR)
        out = HERE / "frames"; out.mkdir(exist_ok=True)
        for i in range(int(a * FPS), int(b * FPS)):
            render(i / FPS).save(out / f"f_{i + 1:04d}.jpg", quality=92)
            if i % 120 == 0: print("frame", i, flush=True)
