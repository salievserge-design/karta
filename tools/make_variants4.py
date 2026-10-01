# -*- coding: utf-8 -*-
"""Серия 4: ещё 10 дизайн-вариантов (В31–В40) x 2 зала.
Запуск: python3 tools/make_variants4.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from make_variants_legacy import (PB, prep, photos, warp_in, sample_panel, brightness_profile,
                                  synth_panel, contact_sheet, HALLS, FONT, FONT_B,
                                  build_keep_mask)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, 'variants')


def micro(b, text, cx_frac, v, size_frac=0.030, color=(226, 232, 234)):
    f = ImageFont.truetype(FONT, max(13, int(b.W * size_frac)))
    d = ImageDraw.Draw(b.content)
    tw = d.textlength(text, font=f)
    d.text((int(cx_frac * b.W) - tw / 2, int(v * b.H)), text, font=f, fill=color)


def paste_bleed(b, key, box, side, axis='w'):
    """вставить фото целиком в прямоугольник box=(x0,y0,x1,y1) без рамы"""
    x0, y0, x1, y1 = box
    wpx, hpx = int(x1 - x0), int(y1 - y0)
    im = prep(key, wpx / hpx, wpx)
    b.content.paste(im, (int(x0), int(y0)))


# ---------------- В31–В40 ----------------
def v31_lux(b):  # Люкс 2×2: одна панорама, рассечённая на 4 квадрата
    b.title('МОСТЫ И РАЗВЯЗКИ', 0.04)
    m, gap = 0.05, 0.018
    side = (1 - 2 * m) * b.W
    y0 = (b.H - side) / 2 + 0.01 * b.H
    src = prep('clover', 1.0, int(side))
    ts = src.width // 2
    d = ImageDraw.Draw(b.content)
    g = int(gap * b.W)
    sw = (int(side) - g) // 2
    for r in range(2):
        for c in range(2):
            t = src.crop((c * ts, r * ts, (c + 1) * ts, (r + 1) * ts)).resize((sw, sw), Image.LANCZOS)
            x = int(b.W * m) + c * (sw + g)
            y = int(y0) + r * (sw + g)
            b.content.paste(t, (x, y))
            d.rectangle([x - 2, y - 2, x + sw + 1, y + sw + 1], outline=(24, 30, 33, 255), width=3)


def v32_columns(b):  # Пара колонн: день и ночь, равные стройные вертикали
    b.title('МОСТЫ И РАЗВЯЗКИ', 0.045)
    r = b.W / b.H
    w = 0.40
    hh = 0.78
    ar = w * r / hh
    v0 = 0.10
    b.fr(0.065, v0, w, ar, 'day', caption='ДЕНЬ')
    b.fr(0.535, v0, w, ar, 'night', caption='НОЧЬ')


def v33_shelf(b):  # Полка: большой кадр + ряд миниатюр на «полке»
    b.title('МОСТЫ И РАЗВЯЗКИ', 0.045)
    b.fr(0.06, 0.075, 0.88, 1.05, 'clover', style='alu')
    d = ImageDraw.Draw(b.content)
    ly = int(b.H * 0.62)
    d.rounded_rectangle([int(b.W * 0.06), ly - 3, int(b.W * 0.94), ly + 3],
                        radius=3, fill=(216, 220, 222, 255))
    keys = ['day', 'pylon', 'rostov', 'night']
    n, gap = 4, 0.03
    s = (0.88 - 3 * gap) / n
    for i, key in enumerate(keys):
        b.fr(0.06 + i * (s + gap), 0.665, s, 1.25, key, mat_scale=0.6)


def v34_grid9(b):  # Сетка 3×3: коллекция квадратов
    b.title('МОСТЫ И РАЗВЯЗКИ', 0.045)
    keys = ['day', 'pylon', 'clover', 'rostov', 'night', 'day', 'clover', 'pylon', 'rostov']
    m, gap = 0.06, 0.03
    s = (1 - 2 * m - 2 * gap) / 3
    r = b.W / b.H
    hor_frac = s * r          # высота квадрата в долях H
    side_frac = (3 * s + 2 * gap) * r
    v0 = (1 - side_frac) / 2 + 0.015
    for i, key in enumerate(keys):
        rw, c = divmod(i, 3)
        b.fr(m + c * (s + gap), v0 + rw * (hor_frac + gap * r), s, 1.0, key, mat_scale=0.55)


def v35_cross(b):  # Крест: центр + четыре спутника
    b.title('МОСТЫ И РАЗВЯЗКИ', 0.045)
    r = b.W / b.H
    cw = 0.34
    ch = cw * r
    cx, cy = 0.5, 0.50
    sw = 0.21
    sh = sw * r
    off = 0.035
    offv = off * r * 1.35
    b.fr(cx - cw / 2, cy - ch / 2, cw, 1.0, 'night')
    b.fr(cx - cw / 2 - off - sw, cy - sh / 2, sw, 1.0, 'day', mat_scale=0.6)
    b.fr(cx + cw / 2 + off, cy - sh / 2, sw, 1.0, 'clover', mat_scale=0.6)
    b.fr(cx - sw / 2, cy - ch / 2 - offv - sh, sw, 1.0, 'pylon', mat_scale=0.6)
    b.fr(cx - sw / 2, cy + ch / 2 + offv, sw, 1.0, 'rostov', mat_scale=0.6)


def v36_shift(b):  # Сдвиг: две колонны, правая на полкадра ниже
    b.title('МОСТЫ И РАЗВЯЗКИ', 0.045)
    r = b.W / b.H
    w = 0.41
    h = w * r / 0.95
    step = h + 0.04
    keys = [['day', 'clover', 'rostov'], ['night', 'pylon', 'day']]
    for col in (0, 1):
        v0 = 0.075 + col * (step / 2)
        for row in range(3):
            if v0 + row * step + h > 0.985:
                break
            b.fr(0.06 + col * (w + 0.06), v0 + row * step, w, 0.95, keys[col][row],
                 style='alu', mat_scale=0.7)


def v37_diagonal(b):  # Диагональ: сплит день/ночь по диагонали панели
    day = prep('day', b.W / b.H, b.W)
    night = prep('night', b.W / b.H, b.W)
    b.content.paste(day, (0, 0))
    mask = Image.new('L', (b.W, b.H), 0)
    dm = ImageDraw.Draw(mask)
    dm.polygon([(0, b.H), (int(b.W * 0.60), b.H), (b.W, int(b.H * 0.40))], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(2))
    b.content.paste(night, (0, 0), mask)
    d = ImageDraw.Draw(b.content)
    d.line([(0, b.H - 2), (int(b.W * 0.60), b.H - 2), (b.W, int(b.H * 0.40))],
           fill=(255, 196, 128, 255), width=max(3, b.W // 150))
    micro(b, 'ДЕНЬ', 0.5, 0.085)
    micro(b, 'НОЧЬ', 0.5, 0.90)


def v38_lshape(b):  # L-композиция: крупный + две справа + широкий низ
    b.title('МОСТЫ И РАЗВЯЗКИ', 0.045)
    b.fr(0.06, 0.075, 0.50, 0.72, 'clover', style='alu')
    b.fr(0.60, 0.075, 0.34, 1.55, 'pylon', style='alu', mat_scale=0.7)
    b.fr(0.60, 0.315, 0.34, 1.55, 'night', style='alu', mat_scale=0.7)
    b.fr(0.06, 0.66, 0.88, 2.35, 'rostov', style='alu', caption='РОСТОВ НОЧЬЮ')


def v39_showcase(b):  # Витрина: большой арт + музейная плашка с подписью
    b.title('МОСТЫ И РАЗВЯЗКИ', 0.045)
    b.fr(0.07, 0.075, 0.86, 1.15, 'night', style='frameless',
         mat_scale=0.5, glow_alpha=40)
    d = ImageDraw.Draw(b.content)
    x0, x1 = int(b.W * 0.07), int(b.W * 0.93)
    y0, y1 = int(b.H * 0.795), int(b.H * 0.935)
    d.rounded_rectangle([x0, y0, x1, y1], radius=max(3, b.W // 110),
                        fill=(210, 214, 216, 255))
    f1 = ImageFont.truetype(FONT_B, int(b.W * 0.068))
    f2 = ImageFont.truetype(FONT, int(b.W * 0.044))
    t1 = 'Чернавский мост · ночь'
    t2 = 'Воронеж · печать на композите · LED 2700K'
    cx = (x0 + x1) / 2
    d.text((cx - d.textlength(t1, font=f1) / 2, y0 + (y1 - y0) * 0.16), t1, font=f1,
           fill=(30, 34, 36, 255))
    d.text((cx - d.textlength(t2, font=f2) / 2, y0 + (y1 - y0) * 0.60), t2, font=f2,
           fill=(96, 104, 108, 255))


def v40_poster(b):  # Постер 50/50: типографика + ночное фото
    b.title('МОСТЫ И РАЗВЯЗКИ', 0.045)
    d = ImageDraw.Draw(b.content)
    x0, y0 = int(b.W * 0.06), int(b.H * 0.085)
    x1, y1 = int(b.W * 0.50), int(b.H * 0.915)
    d.rectangle([x0, y0, x1, y1], fill=(18, 44, 52, 255))
    f = ImageFont.truetype(FONT_B, int(b.W * 0.098))
    pad = int(b.W * 0.035)
    yy = y0 + int(b.H * 0.06)
    for ln in ['ЧЕР-', 'НАВ-', 'СКИЙ']:
        d.text((x0 + pad, yy), ln, font=f, fill=(236, 238, 241, 255))
        yy += int(b.W * 0.115)
    d.rectangle([x0 + pad, yy + int(b.W * 0.03), x0 + pad + int(b.W * 0.22),
                 yy + int(b.W * 0.048)], fill=(255, 196, 128, 255))
    f2 = ImageFont.truetype(FONT, int(b.W * 0.042))
    d.text((x0 + pad, yy + int(b.W * 0.085)), 'мост через Воронежское вдхр.',
           font=f2, fill=(150, 176, 180, 255))
    d.text((x0 + pad, y1 - int(b.W * 0.10)), 'ВОРОНЕЖ · 2025', font=f2,
           fill=(150, 176, 180, 255))
    b.fr(0.54, 0.085, 0.40, 0.40 * (b.W / b.H) / 0.83, 'night')


VARIANTS4 = [
    ('31-люкс-2x2',   'В31 «Люкс 2×2» — склейка',     v31_lux),
    ('32-колонны',    'В32 «Пара колонн» день/ночь',  v32_columns),
    ('33-полка',      'В33 «Полка» + миниатюры',      v33_shelf),
    ('34-сетка-3x3',  'В34 «Сетка 3×3»',              v34_grid9),
    ('35-крест',      'В35 «Крест» — центр+спутники', v35_cross),
    ('36-сдвиг',      'В36 «Сдвиг» — колонны',        v36_shift),
    ('37-диагональ',  'В37 «Диагональ» день/ночь',    v37_diagonal),
    ('38-элка',       'В38 «L-композиция»',           v38_lshape),
    ('39-витрина',    'В39 «Витрина» + плашка',       v39_showcase),
    ('40-постер',     'В40 «Постер 50/50»',           v40_poster),
]


def build_hall_s4(h):
    base = Image.open(os.path.join(ROOT, h['base'])).convert('RGB')
    slat, gap = sample_panel(os.path.join(ROOT, h['base']), h['strip'])
    prof, py0, py1 = brightness_profile(os.path.join(ROOT, h['base']), h['profstrip'], h['profrange'])
    panel = synth_panel(h['PW'], h['PH'], h['pitch'], slat, gap, prof, (py0, py1))
    keep = build_keep_mask(os.path.join(ROOT, h['base']), h['poly'], h['chairs'])
    outs = []
    for slug, label, fn in VARIANTS4:
        b = PB(panel.copy())
        fn(b)
        comp = b.finish()
        img = base.copy()
        warp_in(img, comp, h['quad'], keep)
        out = os.path.join(OUTDIR, f"{h['code']}-{slug}.png")
        img.save(out, 'PNG')
        outs.append((out, label))
        print('saved', out)
    return outs


if __name__ == '__main__':
    for h in HALLS:
        h4 = dict(h)
        h4['label'] = h['label'] + ' · серия 4'
        outs = build_hall_s4(h4)
        contact_sheet(h4, outs)
