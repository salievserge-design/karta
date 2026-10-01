# -*- coding: utf-8 -*-
"""Серия 3: ещё 10 дизайн-вариантов (В21–В30) x 2 зала.
Запуск: python3 tools/make_variants3.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageOps, ImageFont
from make_variants_legacy import (PB, prep, photos, warp_in, sample_panel, brightness_profile,
                                  synth_panel, contact_sheet, HALLS, FONT, FONT_B,
                                  build_keep_mask)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, 'variants')

def divider(b, v, frac_w=0.80, color=(255, 196, 128)):
    d1 = ImageDraw.Draw(b.content)
    x0, x1 = int(b.W * (1 - frac_w) / 2), int(b.W * (1 + frac_w) / 2)
    y = int(v * b.H)
    wl = max(3, int(b.W * 0.008))
    d1.line([(x0, y), (x1, y)], fill=color + (255,), width=wl)
    g = ImageDraw.Draw(b.glow_layer)
    g.rectangle([x0, y - wl * 4, x1, y + wl * 4], fill=(255, 190, 120, 120))

def micro(b, text, cx_frac, v, size_frac=0.030):
    f = ImageFont.truetype(FONT, max(13, int(b.W * size_frac)))
    d = ImageDraw.Draw(b.content)
    tw = d.textlength(text, font=f)
    d.text((int(cx_frac * b.W) - tw / 2, int(v * b.H)), text, font=f, fill=(226, 232, 234))

def duotone_on(keys=('day', 'night')):
    global _backup
    _backup = {}
    for k in keys:
        im0, g = photos()[k]
        L = im0.convert('L')
        duo = ImageOps.colorize(L, black=(10, 42, 52), mid=(58, 116, 130),
                                white=(255, 200, 135), midpoint=122)
        _backup[k] = (im0, g)
        photos()[k] = (duo, g)

def duotone_off():
    if '_backup' in globals():
        for k, v in _backup.items():
            photos()[k] = v

# ---------------- В21–В30 ----------------
def v21_billboard(b):
    b.title('МОСТЫ И РАЗВЯЗКИ', 0.05)
    r = b.W / b.H
    h = 0.90 * r / 1.6
    v0 = (1 - h) / 2 + 0.015
    b.fr(0.05, v0, 0.90, 1.6, 'night', caption='ЧЕРНАВСКИЙ МОСТ')

def v22_cascade(b):
    b.title('МОСТЫ И РАЗВЯЗКИ', 0.045)
    xs = [0.035, 0.225, 0.415]
    vs = [0.08, 0.32, 0.56]
    for i, key in enumerate(['day', 'night', 'clover']):
        b.fr(xs[i], vs[i], 0.56, 0.78, key)

def v23_story(b):
    b.title('МОСТЫ И РАЗВЯЗКИ', 0.04, size_frac=0.044)
    caps = ['УТРО', 'ВЕЧЕР', 'ДЕТАЛЬ']
    keys = ['day', 'night', 'pylon']
    r = b.W / b.H
    for i, key in enumerate(keys):
        v0 = 0.075 + i * (0.48 * r / 0.8 + 0.03)
        b.fr(0.26, v0, 0.48, 0.8, key, caption=caps[i])

def v24_facemix(b):
    b.title('МОСТЫ И РАЗВЯЗКИ', 0.045)
    r = b.W / b.H
    h = 0.86 * r / 2.2
    v0 = 0.10
    b.fr(0.07, v0, 0.86, 2.2, 'rostov', caption='РОСТОВ НОЧЬЮ')
    v2 = v0 + h + 0.05
    b.fr(0.06, v2, 0.42, 1.0, 'day')
    b.fr(0.52, v2, 0.42, 1.0, 'clover')

def v25_bigmat(b):
    b.title('МОСТЫ И РАЗВЯЗКИ', 0.05)
    r = b.W / b.H
    h = 0.80 * r / 0.75
    v0 = max(0.14, (1 - h) / 2)
    b.fr(0.10, v0, 0.80, 0.75, 'day', mat_scale=2.0, caption='ЧЕРНАВСКИЙ МОСТ')

def v26_warm_cold(b):
    r = b.W / b.H
    h = 0.84 * r
    gap = 0.055
    total = 2 * h + gap
    v0 = max(0.04, (1 - total) / 2)
    b.fr(0.08, v0, 0.84, 1.0, 'day', mat_scale=0.8)
    vdiv = v0 + h + gap / 2
    divider(b, vdiv)
    b.fr(0.08, v0 + h + gap, 0.84, 1.0, 'night', mat_scale=0.8)
    micro(b, 'ДЕНЬ', 0.5, v0 - 0.006)
    micro(b, 'НОЧЬ', 0.5, v0 + h + gap - 0.006)

def v27_white(b):
    b.title('МОСТЫ И РАЗВЯЗКИ', 0.045)
    for i, key in enumerate(['day', 'night', 'clover']):
        b.fr(0.18, 0.075 + i * 0.315, 0.64, 0.78, key, style='white')

def v28_duotone(b):
    duotone_on()
    b.title('МОСТЫ И РАЗВЯЗКИ', 0.05)
    r = b.W / b.H
    h = 0.68 * r / 0.75
    total = 2 * h + 0.04
    v0 = max(0.07, (1 - total) / 2)
    b.fr(0.16, v0, 0.68, 0.75, 'day', style='alu', caption='ДЕНЬ · ДУОТОН')
    b.fr(0.16, v0 + h + 0.04, 0.68, 0.75, 'night', style='alu', caption='НОЧЬ · ДУОТОН')
    duotone_off()

def v29_medals(b):
    b.title('МОСТЫ И РАЗВЯЗКИ', 0.045)
    photos()['day_p'] = (photos()['day'][0],
                         dict(cx=0.66, cy=0.56, color=1.06, contrast=1.04))
    r = b.W / b.H
    h = 0.40 * r
    total = 3 * h + 2 * 0.028
    v0 = max(0.115, (1 - total) / 2 + 0.02)
    xs = [0.075, 0.525]
    keys = ['day', 'night', 'clover', 'pylon', 'rostov', 'day_p']
    i = 0
    for row in range(3):
        for col in range(2):
            b.fr(xs[col], v0 + row * (h + 0.028), 0.40, 1.0, keys[i], mat_scale=0.8)
            i += 1

def v30_stele(b):
    b.title('МОСТЫ И РАЗВЯЗКИ', 0.045)
    r = b.W / b.H
    h = 0.46 * r / 0.42
    v0 = (1 - h) / 2 + 0.02
    b.fr(0.27, v0, 0.46, 0.42, 'pylon', glow_alpha=45, caption='ВАНТОВЫЙ МОСТ')

VARIANTS3 = [
    ('21-билборд',          'В21 «Билборд» 16:10',              v21_billboard),
    ('22-каскад',           'В22 «Каскад» — лесенка',           v22_cascade),
    ('23-сюжет',            'В23 «Сюжет» — утро/вечер/деталь',  v23_story),
    ('24-лицо',             'В24 «Микс» — панорама+диптих',     v24_facemix),
    ('25-большое-паспарту', 'В25 «Большое паспарту»',           v25_bigmat),
    ('26-тепло-холод',      'В26 «Тепло/холод» + LED',          v26_warm_cold),
    ('27-белая-галерея',    'В27 «Белая галерея»',              v27_white),
    ('28-дуотон',           'В28 «Дуотон» — бирюза/медь',       v28_duotone),
    ('29-медальоны',        'В29 «Медальоны» — 2×3',            v29_medals),
    ('30-стела',            'В30 «Стела» — ультравертикаль',    v30_stele),
]

def build_hall_s3(h):
    base = Image.open(os.path.join(ROOT, h['base'])).convert('RGB')
    slat, gap = sample_panel(os.path.join(ROOT, h['base']), h['strip'])
    prof, py0, py1 = brightness_profile(os.path.join(ROOT, h['base']), h['profstrip'], h['profrange'])
    panel = synth_panel(h['PW'], h['PH'], h['pitch'], slat, gap, prof, (py0, py1))
    keep = build_keep_mask(os.path.join(ROOT, h['base']), h['poly'], h['chairs'])
    outs = []
    for slug, label, fn in VARIANTS3:
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
        h3 = dict(h)
        h3['label'] = h['label'] + ' · серия 3'
        outs = build_hall_s3(h3)
        contact_sheet(h3, outs)
