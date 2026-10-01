# -*- coding: utf-8 -*-
"""10 дизайн-вариантов фотопанели x 2 зала Транспроекта.
Запуск: python3 tools/make_variants.py
"""
import os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, 'assets')
OUTDIR = os.path.join(ROOT, 'variants')
os.makedirs(OUTDIR, exist_ok=True)
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_B = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

def load_photo(name):
    return Image.open(os.path.join(A, name)).convert('RGB')

def cover(im, ar, cx=0.5, cy=0.5):
    sw, sh = im.size
    if sw / sh > ar:
        nw = int(sh * ar); nh = sh
    else:
        nw = sw; nh = int(sw / ar)
    x = int((sw - nw) * cx); y = int((sh - nh) * cy)
    return im.crop((max(0, x), max(0, y), max(0, x) + nw, max(0, y) + nh))

def grade(im, color=1.0, contrast=1.0, bright=1.0):
    im = ImageEnhance.Color(im).enhance(color)
    im = ImageEnhance.Contrast(im).enhance(contrast)
    im = ImageEnhance.Brightness(im).enhance(bright)
    return im

def bw(im):
    return ImageEnhance.Contrast(im.convert('L').convert('RGB')).enhance(1.10)

PHOTOS = None
def photos():
    global PHOTOS
    if PHOTOS is None:
        PHOTOS = {
            'day':    (load_photo('chernavsky-day.jpg'),      dict(cx=0.50, cy=0.52, color=1.06, contrast=1.04)),
            'night':  (load_photo('chernavsky-night.jpg'),    dict(cx=0.55, cy=0.55, color=1.05, contrast=1.05)),
            'clover': (load_photo('cloverleaf-getty.jpg'),    dict(cx=0.50, cy=0.48, color=1.30, contrast=1.14, bright=1.02)),
            'pylon':  (load_photo('russky-pylon.jpg'),        dict(cx=0.50, cy=0.40, color=1.08, contrast=1.06)),
            'rostov': (load_photo('voroshilovsky-night.jpg'), dict(cx=0.47, cy=0.55, color=1.04, contrast=1.05)),
        }
    return PHOTOS

def prep(key, ar, Wpx, mono=False):
    im, g = photos()[key]
    im = cover(im, ar, g.get('cx', .5), g.get('cy', .5)).resize(
        (Wpx, max(1, int(Wpx / ar))), Image.LANCZOS)
    im = grade(im, g.get('color', 1), g.get('contrast', 1), g.get('bright', 1))
    if mono:
        im = bw(im)
    return im

# ---------------- perspective ----------------
def find_coeffs(target, source):
    m = []
    for (x2, y2), (x1, y1) in zip(target, source):
        m.append([x2, y2, 1, 0, 0, 0, -x1 * x2, -x1 * y2, x1])
        m.append([0, 0, 0, x2, y2, 1, -y1 * x2, -y1 * y2, y1])
    A = np.array(m, float)
    return np.linalg.solve(A[:, :8], A[:, 8])

def warp_in(base, src, target_quad):
    sw, sh = src.size
    coeffs = find_coeffs(target_quad, [(0, 0), (sw, 0), (sw, sh), (0, sh)])
    w = src.convert('RGBA').transform(base.size, Image.PERSPECTIVE, coeffs, Image.BICUBIC)
    mask = Image.new('L', (sw, sh), 255).transform(base.size, Image.PERSPECTIVE, coeffs, Image.BICUBIC)
    base.paste(w, (0, 0), mask)

# ---------------- synth slat panel ----------------
def sample_panel(img_path, strip_y0frac):
    """медианный цвет рейки и тёмного зазора по чистым строкам"""
    im = np.array(Image.open(img_path).convert('RGB')).astype(float)
    x0, x1, y0, y1 = strip_y0frac
    slats, gaps = [], []
    for y in range(y0, y1, 4):
        row = im[y, x0:x1]
        sig = row.mean(axis=1)
        th = sig.mean() * 0.86
        gp = sig < th
        if (~gp).any():
            slats.append(row[~gp].reshape(-1, 3))
        if gp.any():
            gaps.append(row[gp].reshape(-1, 3))
    slat = np.median(np.vstack(slats), axis=0)
    gap_c = np.median(np.vstack(gaps), axis=0) if gaps else slat * 0.62
    return slat, gap_c

def brightness_profile(img_path, stripx, yr):
    im = np.array(Image.open(img_path).convert('RGB')).astype(float)
    x0, x1 = stripx
    y0, y1 = yr
    pts, vals = [], []
    for y in range(y0, y1, 4):
        vals.append(im[y, x0:x1].mean()); pts.append(y)
    vals = np.array(vals); med = np.median(vals)
    vals = np.clip(vals / med, 0.86, 1.16)
    sm = np.convolve(vals, np.ones(9) / 9, mode='same')
    return [(pts[i], float(sm[i])) for i in range(0, len(pts), 4)], y0, y1

def synth_panel(PW, PH, pitch_px, slat, gap, profile, prof_range):
    p = Image.new('RGB', (PW, PH))
    d = ImageDraw.Draw(p)
    rnd = random.Random(5)
    sw = int(pitch_px * 0.72); gw = pitch_px - sw
    x = 0
    while x < PW:
        v = rnd.randint(-6, 6)
        c = tuple(int(max(0, min(255, slat[k] + v))) for k in range(3))
        x1r = min(x + sw, PW)
        d.rectangle([x, 0, x1r, PH], fill=c)
        if x1r - x >= 5:
            d.rectangle([x, 0, min(x + 2, x1r), PH], fill=tuple(min(255, int(c[k] * 1.08 + 6)) for k in range(3)))
            d.rectangle([max(x, x1r - 3), 0, x1r, PH], fill=tuple(max(0, int(c[k] * 0.85)) for k in range(3)))
        d.rectangle([x1r, 0, min(x + sw + gw, PW), PH], fill=tuple(int(g) for g in gap))
        x += pitch_px
    p = p.filter(ImageFilter.GaussianBlur(0.5))
    arr = np.array(p).astype(float)
    y0, y1 = prof_range
    fx = np.linspace(y0, y1, len(profile))
    fv = np.array([f for _, f in profile])
    for row in range(PH):
        v = y0 + (y1 - y0) * row / PH
        arr[row] *= float(np.interp(v, fx, fv))
    return Image.fromarray(np.clip(arr, 0, 255).astype('uint8'))

# ---------------- builder ----------------
def mat_texture(w, h, c_top=(238, 235, 229), c_bot=(224, 221, 215)):
    m = Image.new('RGB', (w, h))
    d = ImageDraw.Draw(m)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)], fill=tuple(int(c_top[i] + (c_bot[i] - c_top[i]) * t) for i in range(3)))
    return m

class PB:
    def __init__(self, panel_img):
        self.panel = panel_img.convert('RGBA')
        self.W, self.H = self.panel.size
        self.glow_layer = Image.new('RGBA', self.panel.size, (0, 0, 0, 0))
        self.shad_layer = Image.new('RGBA', self.panel.size, (0, 0, 0, 0))
        self.content = Image.new('RGBA', self.panel.size, (0, 0, 0, 0))

    def fr(self, u0, v0, w_frac, aspect, photo_key, style='black', caption=None,
           mono=False, shadow=True, glow_alpha=0, mat_scale=1.0, frameless_pad=2):
        x0, y0 = int(u0 * self.W), int(v0 * self.H)
        w = int(w_frac * self.W); h = int(w / aspect)
        if glow_alpha:
            g = ImageDraw.Draw(self.glow_layer)
            p = int(w * 0.22)
            g.rounded_rectangle([x0 - p, y0 - int(p * 0.7), x0 + w + p, y0 + h + int(p * 0.7)],
                                radius=p, fill=(255, 186, 110, glow_alpha))
        if shadow:
            s = ImageDraw.Draw(self.shad_layer)
            off = max(5, w // 45)
            s.rectangle([x0 + off, y0 + off, x0 + w + off, y0 + h + off], fill=(8, 20, 30, 110))
        if style == 'frameless':
            frame = Image.new('RGB', (w, h), (38, 40, 43))
            ph = prep(photo_key, (w - 2 * frameless_pad) / (h - 2 * frameless_pad),
                      w - 2 * frameless_pad, mono)
            frame.paste(ph, (frameless_pad, frameless_pad))
        else:
            if style == 'alu':
                fpx, mpc = max(2, w // 110), (152, 158, 163)
            else:
                fpx, mpc = max(3, w // 80), (22, 22, 24)
            frame = Image.new('RGB', (w, h), mpc)
            if style == 'polaroid':
                m_side = int(w * 0.09); m_top = int(w * 0.08); m_bot = int(h * 0.19)
            else:
                m_side = int(w * 0.09 * mat_scale); m_top = int(w * 0.08 * mat_scale); m_bot = int(h * 0.12 * mat_scale)
            frame.paste(mat_texture(w - 2 * fpx, h - 2 * fpx), (fpx, fpx))
            iw = w - 2 * (fpx + m_side); ih = h - 2 * fpx - m_top - m_bot
            frame.paste(prep(photo_key, iw / ih, iw, mono), (fpx + m_side, fpx + m_top))
            dd = ImageDraw.Draw(frame)
            dd.rectangle([0, 0, w - 1, h - 1], outline=tuple(int(c * 0.65) for c in mpc), width=1)
            dd.rectangle([fpx, fpx, w - fpx - 1, h - fpx - 1], outline=(203, 200, 194), width=1)
        self.content.paste(frame, (x0, y0))
        if caption:
            cs = max(16, int(w * 0.052))
            cf = ImageFont.truetype(FONT, cs)
            d = ImageDraw.Draw(self.content)
            tw = d.textlength(caption, font=cf)
            while tw > self.W * 0.96 and cs > 9:
                cs = int(cs * 0.88)
                cf = ImageFont.truetype(FONT, cs)
                tw = d.textlength(caption, font=cf)
            cx = x0 + w // 2
            if style == 'polaroid':
                yy = y0 + h - int(h * 0.19) + int((h * 0.19 - cs) / 2) - 2
                d.text((cx - tw // 2, yy), caption, font=cf, fill=(92, 90, 88))
            else:
                yy = y0 + h + int(self.W * 0.014)
                d.text((cx - tw // 2, yy), caption, font=cf, fill=(232, 237, 239))
        return (x0, y0, w, h)

    def title(self, text, v0, size_frac=0.048, tracking=8, accent=True):
        f = ImageFont.truetype(FONT_B, int(self.W * size_frac))
        d = ImageDraw.Draw(self.content)
        widths = [d.textlength(ch, font=f) for ch in text]
        total = sum(widths) + tracking * (len(text) - 1)
        x = (self.W - total) // 2
        y = int(v0 * self.H)
        for ch, wch in zip(text, widths):
            d.text((x, y), ch, font=f, fill=(238, 241, 242))
            x += wch + tracking
        if accent:
            lw = int(self.W * 0.11)
            ly = y + int(self.W * size_frac * 1.65)
            d.line([(self.W // 2 - lw, ly), (self.W // 2 + lw, ly)],
                   fill=(255, 186, 112), width=max(2, int(self.W * 0.007)))


    def vtitle(self, text, u_center, v_center, size_frac=0.05, angle=90, tracking=6):
        """вертикальный заголовок на панели"""
        f = ImageFont.truetype(FONT_B, int(self.W * size_frac))
        tmp = Image.new('RGBA', (10, 10), (0, 0, 0, 0))
        d0 = ImageDraw.Draw(tmp)
        widths = [d0.textlength(ch, font=f) for ch in text]
        total = int(sum(widths) + tracking * (len(text) - 1))
        asc, desc = f.getmetrics()
        txt = Image.new('RGBA', (total + 10, asc + desc + 10), (0, 0, 0, 0))
        d = ImageDraw.Draw(txt)
        x = 5
        for ch, wch in zip(text, widths):
            d.text((x, 5), ch, font=f, fill=(235, 238, 239))
            x += wch + tracking
        rot = txt.rotate(angle, expand=True, resample=Image.BICUBIC)
        px = int(u_center * self.W - rot.width / 2)
        py = int(v_center * self.H - rot.height / 2)
        self.content.alpha_composite(rot, (px, py))

    def hline(self, v, u0=0.06, u1=0.94, color=(176, 184, 190), w_px=None):
        d = ImageDraw.Draw(self.content)
        y = int(v * self.H)
        w_px = w_px or max(3, int(self.W * 0.006))
        d.line([(int(u0 * self.W), y), (int(u1 * self.W), y)], fill=color, width=w_px)

    def tilt_fr(self, u_c, v_c, w_frac, aspect, photo_key, angle=0, pin=True,
                style='black', mat_scale=0.85):
        """рамка с наклоном (как приколотые принты)"""
        w = int(w_frac * self.W); h = int(w / aspect)
        if style == 'polaroid':
            fpx, mpc, mside, mtop = max(2, w // 100), (244, 244, 242), int(w * 0.07), int(w * 0.06)
            mbot = int(h * 0.16)
        else:
            fpx, mpc, mside, mtop = max(3, w // 80), (22, 22, 24), int(w * 0.09 * mat_scale), int(w * 0.08 * mat_scale)
            mbot = int(h * 0.12 * mat_scale)
        frame = Image.new('RGB', (w, h), mpc)
        frame.paste(mat_texture(w - 2 * fpx, h - 2 * fpx), (fpx, fpx))
        iw = w - 2 * (fpx + mside); ih = h - 2 * fpx - mtop - mbot
        frame.paste(prep(photo_key, iw / ih, iw), (fpx + mside, fpx + mtop))
        dd = ImageDraw.Draw(frame)
        dd.rectangle([0, 0, w - 1, h - 1], outline=tuple(int(c * 0.65) for c in mpc), width=1)
        dd.rectangle([max(0, fpx), max(0, fpx), w - fpx - 1, h - fpx - 1], outline=(203, 200, 194), width=1)
        frgba = frame.convert('RGBA')
        rot = frgba.rotate(angle, expand=True, resample=Image.BICUBIC)
        pad = rot.width - w
        sh = Image.new('RGBA', rot.size, (8, 20, 30, 120))
        sh.putalpha(rot.split()[3].point(lambda a: int(a * 0.45)))
        sblur = sh.filter(ImageFilter.GaussianBlur(8))
        cx, cy = int(u_c * self.W), int(v_c * self.H)
        ox = cx - rot.width // 2; oy = cy - rot.height // 2
        self.shad_layer.alpha_composite(sblur, (ox + 6, oy + 8))
        self.content.alpha_composite(rot, (ox, oy))
        if pin:
            d = ImageDraw.Draw(self.content)
            r = max(3, w // 60)
            d.ellipse([cx - r, oy + r * 2, cx + r, oy + r * 4], fill=(38, 40, 44), outline=(150, 150, 148))
        return (cx, cy, rot.width, rot.height)

    def film(self, u0, v0, w_frac, photo_keys, ratio=1.55):
        """кадр-кинолента с перфорацией"""
        w = int(w_frac * self.W)
        bx = max(4, int(w * 0.030))
        holes_h = max(10, int(w * 0.035))
        gapf = int(w * 0.012)
        cell_w = (w - 2 * bx - 2 * gapf) // 3
        cell_h = int(cell_w / ratio)
        h = holes_h * 2 + cell_h + bx * 4
        x0, y0 = int(u0 * self.W), int(v0 * self.H)
        frame = Image.new('RGB', (w, h), (18, 18, 20))
        d = ImageDraw.Draw(frame)
        # перфорация
        hr_w = max(4, int(w * 0.012)); hr_h = int(holes_h * 0.55)
        step = int(w / 16)
        for i in range(16):
            hx = int(i * step + step / 2 - hr_w / 2)
            for yy in (int(bx * 1.2), h - int(bx * 1.2) - holes_h + int((holes_h - hr_h) / 2)):
                d.rounded_rectangle([hx, yy, hx + hr_w, yy + hr_h], radius=2, fill=(96, 98, 100))
        for i, key in enumerate(photo_keys):
            px = bx + i * (cell_w + gapf)
            py = h // 2 - cell_h // 2
            frame.paste(prep(key, cell_w / cell_h, cell_w), (px, py))
        d.rectangle([0, 0, w - 1, h - 1], outline=(60, 60, 62), width=1)
        s = ImageDraw.Draw(self.shad_layer)
        off = max(5, w // 60)
        s.rectangle([x0 + off, y0 + off, x0 + w + off, y0 + h + off], fill=(8, 20, 30, 110))
        self.content.paste(frame, (x0, y0))
        return (x0, y0, w, h)

    def finish(self):
        gl = self.glow_layer.filter(ImageFilter.GaussianBlur(self.W // 18))
        sh = self.shad_layer.filter(ImageFilter.GaussianBlur(self.W // 50))
        out = self.panel.copy()
        out.alpha_composite(gl)
        out.alpha_composite(sh)
        out.alpha_composite(self.content)
        return out.convert('RGB')

# ---------------- 10 вариантов ----------------
def v01_hero(b):
    b.title('МОСТЫ И РАЗВЯЗКИ', 0.045)
    b.fr(0.17, 0.13, 0.66, 3 / 4, 'night', caption='ЧЕРНАВСКИЙ МОСТ')

def v02_panorama(b):
    b.title('МОСТЫ И РАЗВЯЗКИ', 0.045)
    b.fr(0.045, 0.42, 0.91, 2.35, 'rostov', caption='ВОРОШИЛОВСКИЙ МОСТ', glow_alpha=60)

def v03_squares(b):
    b.fr(0.19, 0.045, 0.62, 1.0, 'day')
    b.fr(0.19, 0.365, 0.62, 1.0, 'night')
    b.fr(0.19, 0.685, 0.62, 1.0, 'clover')

def v04_grid22(b):
    cw = 0.44; vh = (cw * b.W) / b.H; gap = vh * 0.10
    v0 = (1.0 - (2 * vh + gap)) / 2
    b.fr(0.065, v0, cw, 1.0, 'day')
    b.fr(1 - 0.065 - cw, v0, cw, 1.0, 'clover')
    b.fr(0.065, v0 + vh + gap, cw, 1.0, 'pylon')
    b.fr(1 - 0.065 - cw, v0 + vh + gap, cw, 1.0, 'night')

def v05_mosaic(b):
    b.title('МОСТЫ И РАЗВЯЗКИ', 0.038, size_frac=0.042)
    h_big = 0.50
    b.fr(0.055, 0.11, 0.55, (0.55 * b.W) / (h_big * b.H), 'pylon')
    sm_w = 0.335; sm_h = (h_big - 0.035) / 2
    ar = (sm_w * b.W) / (sm_h * b.H)
    b.fr(0.635, 0.11, sm_w * 1.0, ar, 'day')
    b.fr(0.635, 0.11 + sm_h + 0.035, sm_w, ar, 'clover')
    w2 = 0.90; ar2 = (w2 * b.W) / (0.30 * b.H)
    b.fr(0.055, 0.66, w2 / 1.0, ar2, 'night')

def v06_dibond(b):
    b.title('МОСТЫ И РАЗВЯЗКИ', 0.04, size_frac=0.044)
    v = 0.115; fh = 0.27; gap = 0.02
    ar = (0.86 * b.W) / (fh * b.H)
    b.fr(0.07, v, 0.86, ar, 'day', style='frameless')
    b.fr(0.07, v + fh + gap, 0.86, ar, 'night', style='frameless')
    b.fr(0.07, v + 2 * (fh + gap), 0.86, ar, 'clover', style='frameless')

def v07_polaroid(b):
    ph = 0.285; gap = 0.035
    ar = (0.72 * b.W) / (ph * b.H)
    b.fr(0.14, 0.045, 0.72, ar, 'day', style='polaroid', caption='Чернавский мост')
    b.fr(0.14, 0.045 + ph + gap, 0.72, ar, 'night', style='polaroid', caption='Синий час')
    b.fr(0.14, 0.045 + 2 * (ph + gap), 0.72, ar, 'clover', style='polaroid', caption='Клеверный лист')

def v08_alu_title(b):
    b.title('МОСТЫ И РАЗВЯЗКИ', 0.05)
    fh = 0.36
    ar = (0.78 * b.W) / (fh * b.H)
    b.fr(0.11, 0.14, 0.78, ar, 'day', style='alu', caption='ЧЕРНАВСКИЙ МОСТ')
    b.fr(0.11, 0.575, 0.78, ar, 'night', style='alu', caption='СИНИЙ ЧАС')

def v09_noir(b):
    b.title('МОСТЫ И РАЗВЯЗКИ', 0.045)
    h1 = 0.58
    b.fr(0.19, 0.13, 0.62, (0.62 * b.W) / (h1 * b.H), 'pylon', mono=True, mat_scale=0.75)
    h2 = 0.19
    ar2 = (0.62 * b.W) / (h2 * b.H)
    v2 = 0.13 + h1 + 0.045
    b.fr(0.19, v2, 0.62, ar2, 'night', mono=True, mat_scale=0.75)

def v10_aura(b):
    b.title('МОСТЫ И РАЗВЯЗКИ', 0.045)
    b.fr(0.13, 0.16, 0.74, 3 / 4, 'night', glow_alpha=95, caption='СИНИЙ ЧАС')

VARIANTS = [
    ('01-герой',        'В1 «Герой» — крупный кадр',        v01_hero),
    ('02-панорама',     'В2 «Панорама» 2.35:1',             v02_panorama),
    ('03-квадраты',     'В3 «Триптих» — квадраты',          v03_squares),
    ('04-сетка-2x2',    'В4 Сетка 2×2',                     v04_grid22),
    ('05-мозаика',      'В5 «Мозаика» — асимметрия',        v05_mosaic),
    ('06-дибонд',       'В6 «Дибонд» — без рам',            v06_dibond),
    ('07-полароид',     'В7 «Паспарту XL» с подписями',     v07_polaroid),
    ('08-алюминий',     'В8 «Алюминий» + заголовок',        v08_alu_title),
    ('09-нуар',         'В9 «Noir» — чёрно-белая серия',    v09_noir),
    ('10-аура',         'В10 «Аура» — LED-ореол',           v10_aura),
]

# ---------------- залы ----------------
HALLS = [
    dict(
        code='h1',
        label='Зал 1 (перспектива)',
        base='ai-base-room.png',
        quad=[(906, 148), (1083, 168), (1083, 525), (906, 560)],
        PW=712, PH=1560, pitch=42,
        strip=(908, 920, 500, 552),
        profstrip=(911, 916), profrange=(160, 556),
    ),
    dict(
        code='h2',
        label='Зал 2 (фронтальный)',
        base='ai-base-room2.png',
        quad=[(1387, 100), (1638, 94), (1638, 748), (1387, 812)],
        PW=1004, PH=2760, pitch=75,
        strip=(1590, 1634, 700, 740),
        profstrip=(1393, 1400), profrange=(132, 806),
    ),
]

def build_hall(h):
    base = Image.open(os.path.join(ROOT, h['base'])).convert('RGB')
    slat, gap = sample_panel(os.path.join(ROOT, h['base']), h['strip'])
    prof, py0, py1 = brightness_profile(os.path.join(ROOT, h['base']), h['profstrip'], h['profrange'])
    panel = synth_panel(h['PW'], h['PH'], h['pitch'], slat, gap, prof, (py0, py1))
    outs = []
    for slug, label, fn in VARIANTS:
        b = PB(panel.copy())
        fn(b)
        comp = b.finish()
        img = base.copy()
        warp_in(img, comp, h['quad'])
        out = os.path.join(OUTDIR, f"{h['code']}-{slug}.png")
        img.save(out, 'PNG')
        outs.append((out, label))
        print('saved', out)
    return outs

def contact_sheet(h, outs, suite='В1–В10', fname_tag=''):
    thumbs = []
    tw = 620
    for path, label in outs:
        im = Image.open(path).convert('RGB')
        r = tw / im.width
        thumbs.append((im.resize((tw, int(im.height * r)), Image.LANCZOS), label))
    cell_w, cell_h = tw + 60, thumbs[0][0].height + 100
    cols, rows = 2, max(1, (len(thumbs) + 1) // 2)
    sheet = Image.new('RGB', (cols * cell_w + 60, rows * cell_h + 130), (242, 243, 245))
    d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype(FONT_B, 34)
    ft = ImageFont.truetype(FONT, 26)
    title = f"ТРАНСПРОЕКТ · {h['label']} — варианты {suite}"
    d.text((40, 30), title, font=f, fill=(52, 62, 72))
    for i, (im, label) in enumerate(thumbs):
        c, r = i % cols, i // cols
        x = 30 + c * cell_w + 30; y = 100 + r * cell_h + 30
        d.rectangle([x - 2, y - 2, x + im.width + 1, y + im.height + 1], outline=(198, 203, 208), width=2)
        sheet.paste(im, (x, y))
        d.text((x, y + im.height + 14), label, font=ft, fill=(70, 80, 90))
    out = os.path.join(ROOT, f"Обзор вариантов {suite} — {h['label']}.png")
    sheet.save(out, 'PNG')
    print('saved', out)


def v11_lenta(b):
    b.title('МОСТЫ И РАЗВЯЗКИ', 0.045)
    w = 0.82; fh = (w * b.W / 1.78) / b.H; gap = 0.035
    v = (1.0 - (3 * fh + 2 * gap)) / 2 + 0.03
    b.fr((1 - w) / 2, v, w, 1.78, 'day')
    b.fr((1 - w) / 2, v + fh + gap, w, 1.78, 'rostov')
    b.fr((1 - w) / 2, v + 2 * (fh + gap), w, 1.78, 'night')

def v12_sutki(b):
    b.title('ОДИН ДЕНЬ', 0.045)
    cw = 0.40; ch = (cw * b.W) / b.H; v0 = 0.16; gap = 0.045
    b.fr(0.07, v0, cw, 1.0, 'clover', style='polaroid', caption='Утро')
    b.fr(1 - 0.07 - cw, v0, cw, 1.0, 'day', style='polaroid', caption='День')
    v2 = v0 + ch + gap + 0.10
    b.fr(0.07, v2, cw, 1.0, 'rostov', style='polaroid', caption='Закат')
    b.fr(1 - 0.07 - cw, v2, cw, 1.0, 'night', style='polaroid', caption='Ночь')

def v13_kaskad(b):
    w = 0.335; xh = (w * b.W) / b.H
    b.tilt_fr(0.24, 0.105 + xh / 2, w, 1.0, 'day', angle=-2.5)
    b.tilt_fr(0.52, 0.105 + xh * 1.5 + 0.03, w, 1.0, 'rostov', angle=1.8)
    b.tilt_fr(0.28, 0.105 + xh * 2.5 + 0.06, w, 1.0, 'night', angle=-1.5)
    b.tilt_fr(0.56, 0.105 + xh * 3.5 + 0.09, w, 1.0, 'clover', angle=2.2)

def v14_polka(b):
    b.title('МОСТЫ И РАЗВЯЗКИ', 0.04)
    hero_h = (0.60 * b.W / 0.75) / b.H
    b.fr(0.20, 0.10, 0.60, 3 / 4, 'night')
    rail_v = 0.10 + hero_h + 0.055
    b.hline(rail_v, color=(150, 158, 164))
    b.hline(rail_v - 0.003, color=(210, 214, 218), w_px=max(2, int(b.W * 0.004)))
    sw = 0.27; sh = (sw * b.W / 1.0) / b.H
    for i, key in enumerate(['day', 'clover', 'rostov']):
        b.fr(0.06 + i * (sw + 0.055), rail_v - sh + 0.004, sw, 1.0, key, shadow=True)

def v15_duet(b):
    b.title('ДЕНЬ · НОЧЬ', 0.045)
    fh = 0.62
    ar = (0.44 * b.W) / (fh * b.H)
    b.fr(0.05, 0.15, 0.44, ar, 'day', caption='ДЕНЬ')
    b.fr(0.51, 0.15, 0.44, ar, 'night', caption='НОЧЬ')

def v16_polosy(b):
    ar = (0.42 * b.W) / (0.955 * b.H)
    b.fr(0.05, 0.022, 0.42, ar, 'pylon', style='frameless')
    b.fr(0.53, 0.022, 0.42, ar, 'night', style='frameless')

def v17_tochka(b):
    b.title('ИЗБРАННОЕ', 0.05)
    w = 0.40; fh = (w * b.W) / b.H
    b.fr(0.30, 0.13, w, 1.0, 'day', glow_alpha=80)
    b.fr(0.30, 0.13 + fh + 0.09, w, 1.0, 'clover', glow_alpha=80)
    b.fr(0.30, 0.13 + 2 * (fh + 0.09), w, 1.0, 'night', glow_alpha=80)

def v18_vert(b):
    b.vtitle('МОСТЫ И РАЗВЯЗКИ', 0.115, 0.5, size_frac=0.042, tracking=10)
    fh = 0.34
    ar = (0.62 * b.W) / (fh * b.H)
    b.fr(0.26, 0.09, 0.62, ar, 'day', caption='ЧЕРНАВСКИЙ МОСТ')
    b.fr(0.26, 0.55, 0.62, ar, 'clover', caption='КЛОВЕРНЫЙ ЛИСТ')

def v19_prints(b):
    w = 0.42
    b.tilt_fr(0.27, 0.16, w, 1.0, 'day', angle=-3.2, style='polaroid')
    b.tilt_fr(0.71, 0.20, w * 0.96, 1.0, 'rostov', angle=2.4, style='polaroid')
    b.tilt_fr(0.28, 0.56, w * 0.96, 1.0, 'night', angle=2.8, style='polaroid')
    b.tilt_fr(0.70, 0.60, w, 1.0, 'clover', angle=-2.0, style='polaroid')

def v20_film(b):
    b.title('КИНОЛЕНТА', 0.045)
    fh = 0.165
    b.film(0.03, 0.20, 0.94, ['day', 'rostov', 'night'])
    b.film(0.03, 0.20 + fh + 0.16, 0.94, ['clover', 'pylon', 'night'])

VARIANTS2 = [
    ('11-лента',      'В11 «Лента» — горизонтальные ряды',   v11_lenta),
    ('12-сутки',      'В12 «Сутки» — один день мостов',      v12_sutki),
    ('13-каскад',     'В13 «Каскад» — диагональный ритм',    v13_kaskad),
    ('14-полка',      'В14 «Полка» — герой на консоли',      v14_polka),
    ('15-дуэт',       'В15 «Дуэт» — день и ночь 50/50',      v15_duet),
    ('16-полосы',     'В16 «Полосы» — фото во всю высоту',   v16_polosy),
    ('17-точка',      'В17 «Точка света» — квадраты с гало', v17_tochka),
    ('18-вертикаль',  'В18 «Вертикаль» — типографика сбоку', v18_vert),
    ('19-принты',     'В19 «Принты» — небрежная доска',      v19_prints),
    ('20-кинолента',  'В20 «Кинолента» — плёнка кадров',     v20_film),
]

def build_hall_suite(h, suites):
    base = Image.open(os.path.join(ROOT, h['base'])).convert('RGB')
    slat, gap = sample_panel(os.path.join(ROOT, h['base']), h['strip'])
    prof, py0, py1 = brightness_profile(os.path.join(ROOT, h['base']), h['profstrip'], h['profrange'])
    panel = synth_panel(h['PW'], h['PH'], h['pitch'], slat, gap, prof, (py0, py1))
    outs = []
    for slug, label, fn in suites:
        b = PB(panel.copy())
        fn(b)
        comp = b.finish()
        img = base.copy()
        warp_in(img, comp, h['quad'])
        out = os.path.join(OUTDIR, f"{h['code']}-{slug}.png")
        img.save(out, 'PNG')
        outs.append((out, label))
        print('saved', out)
    return outs

if __name__ == '__main__':
    for h in HALLS:
        outs1 = build_hall_suite(h, VARIANTS)
        contact_sheet(h, outs1, suite='В1–В10')
        outs2 = build_hall_suite(h, VARIANTS2)
        contact_sheet(h, outs2, suite='В11–В20')
