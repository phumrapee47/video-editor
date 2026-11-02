"""Roro Jonggrang v3: photo collage with sub-pixel motion, mood-driven shake, depth-layered temples and demons.

Usage: python compose_roro_v3.py stills 6,19,25,36,45,57,65,78   -> ./stills3/
       python compose_roro_v3.py anim                             -> ./frames3/
Changes from v2 (user feedback 6/10): no pixel-step jitter (affine float transforms), shake only in tense moments,
temples layered in depth with haze toward the sky colour, demons layered near/far and kept behind the rooster.
"""
import math, pathlib, random, sys
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

HERE = pathlib.Path(__file__).parent
PH = HERE.parent / "photos"
W, H, FPS, DUR = 960, 540, 24, 81.0
random.seed(3)


def ease(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def lerp(t, t0, t1, a, b): return a + (b - a) * ease((t - t0) / (t1 - t0)) if t1 > t0 else b
def pulse(t, t0, t1, fade=0.4): return lerp(t, t0, t0 + fade, 0, 1) * (1 - lerp(t, t1 - fade, t1, 0, 1))


def font(size):
    for f in ("georgiab.ttf", "timesbd.ttf", "arialbd.ttf"):
        try: return ImageFont.truetype("C:/Windows/Fonts/" + f, size)
        except OSError: pass
    return ImageFont.load_default()


def fit(im, h=None, w=None):
    return im.resize((int(im.width * h / im.height), h) if h else (w, int(im.height * w / im.width)), Image.LANCZOS)


def fade_edge(im, side, frac):
    a = im.split()[3]; w = im.width; n = max(1, int(w * frac)); g = Image.new("L", im.size, 255); d = ImageDraw.Draw(g)
    for i in range(n):
        x = i if side == "left" else w - 1 - i; d.line([(x, 0), (x, im.height)], fill=int(255 * i / n))
    im = im.copy(); im.putalpha(ImageChops.multiply(a, g)); return im


def sticker(im, shadow=10):
    pad = shadow * 3
    out = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 255)); sh.putalpha(im.split()[3].point(lambda v: int(v * 0.55)))
    out.alpha_composite(sh, (pad + shadow // 2, pad + shadow)); out = out.filter(ImageFilter.GaussianBlur(shadow / 2))
    out.alpha_composite(im, (pad, pad)); return out


def tint(im, rgb, amount):
    base = im.convert("RGB"); out = Image.blend(base, ImageChops.multiply(base, Image.new("RGB", base.size, rgb)), amount)
    if im.mode == "RGBA": out = out.convert("RGBA"); out.putalpha(im.split()[3])
    return out


def haze(im, rgb, amount):
    """Blend a cut-out toward the sky colour: far layers look paler, like air in between."""
    base = im.convert("RGB"); out = Image.blend(base, Image.new("RGB", base.size, rgb), amount).convert("RGBA")
    out.putalpha(im.split()[3]); return out


def place(frame, im, cx, cy, scale=1.0, alpha=1.0):
    """Composite `im` centred at float (cx, cy) with float scale; no rounding to whole pixels (no stepping jitter)."""
    if alpha <= 0.01 or scale <= 0.01: return
    w, h = im.width * scale, im.height * scale
    x0, y0 = cx - w / 2, cy - h / 2
    bx, by = math.floor(x0), math.floor(y0)
    bw, bh = int(math.ceil(w + (x0 - bx))) + 1, int(math.ceil(h + (y0 - by))) + 1
    if bx >= W or by >= H or bx + bw <= 0 or by + bh <= 0: return
    fx, fy = x0 - bx, y0 - by
    layer = im.transform((bw, bh), Image.AFFINE, (1 / scale, 0, -fx / scale, 0, 1 / scale, -fy / scale), resample=Image.BICUBIC)
    if alpha < 0.999: layer.putalpha(layer.split()[3].point(lambda v: int(v * alpha)))
    full = Image.new("RGBA", (W, H), (0, 0, 0, 0)); full.paste(layer, (bx, by)); frame.alpha_composite(full)


def backdrop(frame, im, t, t0, t1, zoom=(1.0, 1.06), pan=(0.0, 0.0)):
    z = lerp(t, t0, t1, *zoom); px = lerp(t, t0, t1, *pan)
    place(frame, im, W / 2 + px, H / 2, z * max(W / im.width, H / im.height) * 1.04)


def label(frame, txt, y, size, t, t0, t1=None, col=(245, 232, 200)):
    a = lerp(t, t0, t0 + 0.6, 0, 1) * (1 - (lerp(t, t1, t1 + 0.5, 0, 1) if t1 else 0))
    if a <= 0.01: return
    f = font(size); layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    tw = d.textlength(txt, font=f); x = (W - tw) / 2; yy = y + (1 - a) * 12
    d.text((x + 3, yy + 3), txt, font=f, fill=(0, 0, 0, int(180 * a))); d.text((x, yy), txt, font=f, fill=(*col, int(255 * a)))
    frame.alpha_composite(layer)


def side_label(frame, txt, x, y, t, t0, t1):
    a = pulse(t, t0, t1)
    if a <= 0.01: return
    f = font(24); layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    tw = d.textlength(txt, font=f); d.rectangle((x - tw / 2 - 10, y - 6, x + tw / 2 + 10, y + 32), fill=(140, 20, 30, int(220 * a)))
    d.text((x - tw / 2, y), txt, font=f, fill=(250, 240, 220, int(255 * a))); frame.alpha_composite(layer)


# ---- assets -----------------------------------------------------------------------------------------------------------
cut = {k: Image.open(PH / "cut" / f"{k}.png").convert("RGBA") for k in ("durga", "dancers", "rooster", "demon", "prambanan", "moon")}
relief = Image.open(PH / "relief.jpg").convert("RGB"); sunrise = Image.open(PH / "sunrise.jpg").convert("RGB")
fire = Image.open(PH / "fire.jpg").convert("RGB")
relief_red = tint(ImageEnhance.Brightness(relief).enhance(0.55), (200, 40, 50), 0.85).convert("RGBA")
relief_dark = tint(ImageEnhance.Brightness(relief).enhance(0.35), (150, 30, 40), 0.9).convert("RGBA")
relief_stone = ImageEnhance.Brightness(relief).enhance(0.25).convert("RGBA")
sunrise_rgba = sunrise.convert("RGBA"); sunrise_dim = ImageEnhance.Brightness(sunrise).enhance(0.55).convert("RGBA")
dw, dh = cut["dancers"].size
prince = sticker(fit(fade_edge(cut["dancers"].crop((0, 0, int(dw * 0.6), dh)), "right", 0.22), h=430))
princess = sticker(fit(fade_edge(cut["dancers"].crop((int(dw * 0.48), 0, dw, dh)), "left", 0.25), h=400))
couple = sticker(fit(cut["dancers"], h=420))
prince_red = tint(prince, (220, 40, 40), 0.8)
rooster = sticker(fit(cut["rooster"], h=270))
durga = sticker(fit(cut["durga"], h=470), 14)
durga_warm = tint(durga, (230, 120, 80), 0.6)
durga_stone = Image.merge("RGBA", (*ImageOps.grayscale(durga.convert("RGB")).convert("RGB").split(), durga.split()[3]))
moon = fit(cut["moon"], h=150)
temple_base = fit(cut["prambanan"], w=900)
demon_base = fit(cut["demon"], h=300)

NIGHT_SKY = (36, 26, 70); DAWN_SKY = (150, 95, 105)
# depth layers, far -> near: (scale, baseline y, haze amount, parallax px/s, spacing as share of width)
DEPTH = [(0.42, 330, 0.62, 3, 0.95), (0.6, 365, 0.42, 6, 0.95), (0.85, 420, 0.2, 10, 1.0), (1.25, 530, 0.0, 16, 1.05)]


def temple_layers(sky):
    return [haze(temple_base, sky, hz) for (_, _, hz, _, _) in DEPTH]


T_NIGHT, T_DAWN = temple_layers(NIGHT_SKY), temple_layers(DAWN_SKY)


def sky_of(layers):
    return DAWN_SKY if layers[0] is T_DAWN[0] else NIGHT_SKY
DEMON_FAR, DEMON_NEAR = sticker(haze(demon_base, NIGHT_SKY, 0.5), 6), sticker(demon_base, 10)
DEMON_FAR_D, DEMON_NEAR_D = sticker(haze(demon_base, DAWN_SKY, 0.45), 6), sticker(tint(demon_base, (200, 160, 200), 0.3), 10)


def night_sky():
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    for y in range(H):
        k = y / H; d.line([(0, y), (W, y)], fill=(int(10 + 30 * k), int(12 + 14 * k), int(40 + 34 * k)))
    for _ in range(160):
        x, y = random.randrange(W), random.randrange(int(H * 0.65)); r = random.choice((1, 1, 1, 2))
        d.ellipse((x, y, x + r, y + r), fill=(235, 230, 210))
    return im.convert("RGBA")


NIGHT = night_sky()


def temples(frame, t, layers, t0, rise=None, xshift=0.0):
    """Draw the depth stack; `rise` = list of (start, end) per layer to make layers grow up from the ground."""
    for i, ((s, y, _, speed, gap), im) in enumerate(zip(DEPTH, layers)):
        g = 1.0 if rise is None else lerp(t, *rise[i], 0, 1)
        if g <= 0.01: continue
        step = im.width * s * gap; off = (-(t - t0) * speed + xshift * (i + 1)) % step
        x = -step + off; yy = y + (1 - g) * 160 * s
        while x < W + step:
            place(frame, im, x, yy, s, g); x += step
        # ground under the layer, hazed like the layer, so a rising row never floats above a strip of sky
        top = yy + im.height * s / 2 - 3
        if top < H:
            gnd = Image.new("RGBA", (W, H), (0, 0, 0, 0)); col = haze(Image.new("RGBA", (1, 1), (14, 16, 12, 255)), sky_of(layers), DEPTH[i][2]).getpixel((0, 0))
            ImageDraw.Draw(gnd).rectangle((0, top, W, H), fill=(*col[:3], int(255 * g))); frame.alpha_composite(gnd)


def demons(frame, t, near_im, far_im, base_t, flee=None):
    spots = [(150, 120, 0.42, far_im), (850, 125, 0.38, far_im), (330, 205, 0.7, near_im), (540, 175, 0.62, near_im)]
    for i, (x, y, s, im) in enumerate(spots):
        a = lerp(t, base_t + i * 0.5, base_t + i * 0.5 + 0.8, 0, 1)
        dx = 14 * math.sin(t * 0.9 + i * 1.7) * s; dy = 10 * math.cos(t * 0.7 + i) * s     # slow float, not a shake
        if flee: dx += lerp(t, flee[0] + i * 0.15, flee[1], 0, 1300); dy -= lerp(t, flee[0], flee[1], 0, 220) * s; a *= 1 - lerp(t, flee[1] - 0.6, flee[1], 0, 1)
        place(frame, im, x + dx, y + dy, s, a * (0.85 if im in (DEMON_FAR, DEMON_FAR_D) else 1.0))


# ---- shake only where the story is tense: (start, end, amplitude px) --------------------------------------------------
SHAKE = [(7.5, 9.5, 2.0), (21.0, 22.6, 4.0), (42.0, 43.4, 3.0), (64.1, 66.6, 9.0), (69.8, 73.8, 3.5)]


def shake(t):
    amp = sum(a * pulse(t, s, e, 0.3) * (1 - 0.6 * ease((t - s) / (e - s))) for s, e, a in SHAKE if s <= t <= e)
    return amp * math.sin(t * 61.0) * math.cos(t * 23.0), amp * math.sin(t * 47.0 + 1.3)


def render(t):
    fr = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    if t < 10:  # the curse
        backdrop(fr, relief_red, t, 0, 10, (1.0, 1.1))
        label(fr, "RORO JONGGRANG", 190, 64, t, 3.0, 9.4); label(fr, "a legend of love and revenge", 270, 26, t, 5.0, 9.4)
    elif t < 21:  # love
        fr.alpha_composite(NIGHT); place(fr, moon, 830, 90, 0.75)
        temples(fr, t, T_NIGHT[:3], 10)
        place(fr, couple, lerp(t, 10, 13, 1150, 480), 330, lerp(t, 10, 21, 0.95, 1.08))
        side_label(fr, "Prince Bandung Bondowoso", 220, 440, t, 14.5, 20.0); side_label(fr, "Princess Roro Jonggrang", 745, 440, t, 17.5, 20.6)
    elif t < 28:  # the father's death
        backdrop(fr, relief_dark, t, 21, 28, (1.08, 1.0))
        place(fr, prince_red, lerp(t, 21, 28, 300, 330), 300, lerp(t, 21, 28, 1.0, 1.12))
        place(fr, princess, lerp(t, 21, 27, 690, 760), 320, 1.0, 1 - lerp(t, 25.5, 27.5, 0, 1))
        label(fr, "...but he caused her father's death", 60, 30, t, 22.5, 27.4)
    elif t < 39:  # 1,000 temples in one night
        fr.alpha_composite(NIGHT); place(fr, moon, 830, lerp(t, 28, 35, 470, 120), lerp(t, 28, 35, 0.8, 1.1))
        temples(fr, t, T_NIGHT, 28)
        label(fr, "1,000 TEMPLES", 70, 56, t, 32.8, 38.4); label(fr, "in a single night", 140, 30, t, 34.0, 38.6)
    elif t < 49:  # spirits build, back rows first
        fr.alpha_composite(NIGHT); place(fr, moon, 840, 85, 0.65)
        demons(fr, t, DEMON_NEAR, DEMON_FAR, 39.3)
        temples(fr, t, T_NIGHT, 39, rise=[(39.5, 41.0), (41.3, 42.8), (43.1, 44.6), (44.9, 46.4)])
        label(fr, f"{int(lerp(t, 39.5, 46.4, 0, 999)):,}", 25, 64, t, 39.5, 48.6, (240, 200, 90))
    elif t < 60:  # fire, rooster, spirits flee
        fr.alpha_composite(NIGHT)
        dawn = lerp(t, 51, 56, 0, 1)
        if dawn > 0.01:
            s = Image.new("RGBA", (W, H)); backdrop(s, sunrise_rgba, t, 49, 60, (1.0, 1.05)); fr = Image.blend(fr, s, dawn)
        demons(fr, t, DEMON_NEAR_D, DEMON_FAR_D, 47.0, flee=(57.4, 60.0))
        glow = lerp(t, 49.3, 50.5, 0, 1) * (1 - lerp(t, 57, 59.5, 0, 0.6))
        if glow > 0.01:
            fl = fire.resize((W, int(fire.height * W / fire.width))).crop((0, 0, W, 240))
            base = fr.convert("RGB"); reg = ImageChops.screen(base.crop((0, H - 240, W, H)), ImageEnhance.Brightness(fl).enhance(glow))
            base.paste(reg, (0, H - 240)); fr = base.convert("RGBA")
        place(fr, princess, 240, 335, 0.92)
        pop = lerp(t, 54.6, 55.0, 0, 1); bounce = 1 + 0.12 * math.exp(-6 * max(0, t - 55)) * math.sin(max(0, t - 55) * 18)   # excited pop, not a fear shake
        place(fr, rooster, 715, 380, pop * bounce)
        label(fr, "COCK-A-DOODLE-DOO!", 40, 44, t, 55.2, 58.6)
    elif t < 69:  # unfinished, the prince's fury
        backdrop(fr, sunrise_dim, t, 60, 69, (1.05, 1.0))
        temples(fr, t, T_DAWN, 60)
        label(fr, "the last temple was never finished", 40, 30, t, 60.8, 63.8)
        flash = lerp(t, 64.0, 64.25, 0, 1) * (1 - lerp(t, 64.6, 66.5, 0, 0.65))
        if flash > 0.01: fr = Image.blend(fr, tint(fr, (230, 30, 30), 1.0), flash)
        place(fr, prince_red if t > 64.2 else prince, 480, 300, lerp(t, 62.5, 68.5, 0.8, 1.35), lerp(t, 62.5, 63.5, 0, 1))
    else:  # turned to stone
        backdrop(fr, relief_stone, t, 69, 81, (1.0, 1.08))
        st = lerp(t, 69.8, 74.5, 0, 1); z = lerp(t, 69, 81, 0.95, 1.12)
        place(fr, durga_warm, 480, 290, z, 1 - st); place(fr, durga_stone, 480, 290, z, st)
        label(fr, "THE CURSED LOVE", 30, 40, t, 76.5, 80.6)
    dx, dy = shake(t)
    if abs(dx) + abs(dy) > 0.05:  # move the whole picture with a 3% zoom so no edge shows
        z = 1.03; fr = fr.transform((W, H), Image.AFFINE, (1 / z, 0, (W - W / z) / 2 - dx, 0, 1 / z, (H - H / z) / 2 - dy), resample=Image.BICUBIC)
    for b in (10, 21, 28, 39, 49, 60, 69):
        d = abs(t - b)
        if d < 0.25: fr = Image.blend(fr, Image.new("RGBA", (W, H), (0, 0, 0, 255)), 1 - d / 0.25)
    if t > DUR - 0.6: fr = Image.blend(fr, Image.new("RGBA", (W, H), (0, 0, 0, 255)), lerp(t, DUR - 0.6, DUR, 0, 1))
    return fr.convert("RGB")


if __name__ == "__main__":
    if sys.argv[1] == "stills":
        out = HERE / "stills3"; out.mkdir(exist_ok=True)
        for s in sys.argv[2].split(","): render(float(s)).save(out / f"t{float(s):05.1f}.jpg", quality=90)
    else:
        out = HERE / "frames3"; out.mkdir(exist_ok=True)
        for i in range(int(DUR * FPS)):
            render(i / FPS).save(out / f"f_{i + 1:04d}.jpg", quality=92)
            if i % 240 == 0: print("frame", i, flush=True)
