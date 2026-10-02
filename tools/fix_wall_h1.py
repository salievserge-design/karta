# -*- coding: utf-8 -*-
"""Рекомпоновка стены зала 1 (ai-base-room.png), v2:
левая teal-рейка сужается до ширины правой (177px), вся зона панели собирается
синтезом из реальных профилей, логотип уменьшается, дерево расширяется, карта центрируется."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'ai-base-room.png')
OUT = os.path.join(ROOT, 'ai-base-room-wall2.png')
rng = np.random.default_rng(11)

im = Image.open(SRC).convert('RGB')
W, H = im.size
orig_im = im.copy()
arr0 = np.array(orig_im).astype(float)

ZX0, ZX1 = 150, 313        # зона левой панели (синтез)
LED_OLD, LED_NEW = (429, 443), (313, 327)
XW0, XW1 = 327, 443
Y0, Y1 = 150, 896
LOGO = (198, 214, 440, 380)
MAP_CUT = (316, 190, 918, 512)
MAP_DX = -48
LOGO_SCALE = 0.62
LOGO_CENTER = (232, 296)


def feathered_rect(w, h, box, feather=8):
    m = Image.new('L', (w, h), 0)
    ImageDraw.Draw(m).rectangle(box, fill=255)
    return m.filter(ImageFilter.GaussianBlur(feather))


# ---------- 0) чистый LED-борт (от старых фрагментов) ----------
sb = orig_im.crop((LED_OLD[0], Y0, LED_OLD[1], Y1))
clean = sb.crop((0, 480 - Y0, LED_OLD[1] - LED_OLD[0], 560 - Y0))
clean = clean.resize((LED_OLD[1] - LED_OLD[0], 402 - 208), Image.LANCZOS)
sb.paste(clean, (0, 208 - Y0))

# ---------- 1) синтез teal-панели ----------
# поперечный профиль: реальная строка y=550
P = arr0[550, ZX0:ZX1, :].copy()                    # (163,3)
# вертикальный градиент: колонки 160..300 без логотипа — берём 3 колонки,
# интерполируем разрыв в строках логотипа
cols = [170, 250, 290]
V = np.zeros((H, 3))
prof = arr0[:, cols, :].mean(axis=1)                # (H,3)
logo_rows = np.arange(210, 405)
ok_top = prof[160:205].mean(axis=0)
ok_bot = prof[408:600].mean(axis=0)
for y in range(H):
    if y < 210:
        V[y] = prof[y]
    elif y < 405:
        t = (y - 210) / 195.0
        tt = t * t * (3 - 2 * t)
        V[y] = ok_top * (1 - tt) + ok_bot * tt
    elif y < 660:
        V[y] = prof[y]
    else:
        V[y] = prof[640:660].mean(axis=0) * 0.96
# нормировка, чтобы zone(x,550)=P(x)
norm = V[550].copy()
zone = P[None, :, :] * (V[Y0:Y1] / norm[None, :])[:, None, :]
zone *= (1 + rng.normal(0, 0.009, size=zone.shape[:2])[..., None])
zone = np.clip(zone, 0, 255).astype('uint8')
mz = feathered_rect(W, H, [ZX0, Y0, ZX1, Y1], feather=6)
im.paste(Image.fromarray(zone), (ZX0, Y0), mz.crop((ZX0, Y0, ZX1, Y1)))

# вернуть кресла нижней зоны поверх синтеза (тёмные пиксели оригинала)
a1 = np.array(im).astype(int)
a0i = np.array(orig_im).astype(int)
chair = (a0i.max(axis=2) < 58)
chair[:620, :] = False
chair[:, ZX1 + 2:] = False
chair[:, :ZX0 - 2] = False
cm = Image.fromarray((chair * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(1.5))
im.paste(orig_im, (0, 0), cm)

# ---------- 2) LED-борт ----------
mled = feathered_rect(W, H, [LED_NEW[0], Y0, LED_NEW[1], Y1], feather=4)
im.paste(sb, (LED_NEW[0], Y0), mled.crop((LED_NEW[0], Y0, LED_NEW[1], Y1)))

# ---------- 3) деревянная полоса ----------
arr = np.array(im).astype(float)
prow = arr0[204:218, 443:900, :].mean(axis=0)
pat_len = prow.shape[0]
colc = arr0[:, 448:455, :].mean(axis=1)
ref_rgb = colc / colc[208:222].mean(axis=0)


def wood_band(x0, x1, y0, y1):
    bw = x1 - x0
    bh = y1 - y0
    idx = (np.arange(x0, x1) - 443) % pat_len
    Pw = prow[idx]
    G = ref_rgb[y0:y1]
    band = Pw[None, :, :] * G[:, None, :]
    y_probe = slice(28, 64)
    refp = arr0[y0 + 28:y0 + 64, 460:610, :].mean(axis=(0, 1))
    gotp = band[y_probe][:, :].mean(axis=(0, 1)) if x1 <= 900 else band[y_probe][:, :80].mean(axis=(0, 1))
    k = np.clip(refp / np.maximum(gotp, 1), 0.5, 1.6) * np.array([0.97, 0.95, 0.93])
    band = band * k[None, None, :]
    band *= (1 + rng.normal(0, 0.010, size=(bh, bw, 1)))
    return np.clip(band, 0, 255).astype('uint8')


band = wood_band(XW0, XW1, Y0, Y1)
mw = feathered_rect(W, H, [XW0, Y0, XW1, Y1], feather=7)
im.paste(Image.fromarray(band), (XW0, Y0), mw.crop((XW0, Y0, XW1, Y1)))

# ---------- 4) логотип ----------
reg = arr0[LOGO[1]:LOGO[3], LOGO[0]:LOGO[2]].astype(int)
white = (reg.min(axis=2) > 142) & ((reg.max(axis=2) - reg.min(axis=2)) < 48)
white = white | (reg.mean(axis=2) > 200)
lam = Image.fromarray((white * 255).astype('uint8'))
lam = lam.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.2))
limg = orig_im.crop(LOGO)
nw, nh = int(limg.width * LOGO_SCALE), int(limg.height * LOGO_SCALE)
im.paste(limg.resize((nw, nh), Image.LANCZOS),
         (int(LOGO_CENTER[0] - nw / 2), int(LOGO_CENTER[1] - nh / 2)),
         lam.resize((nw, nh), Image.LANCZOS))

# ---------- 5) карта ----------
mcut = MAP_CUT
mreg = im.crop(mcut)
vx0 = max(mcut[0], XW1)
vac = wood_band(vx0, min(mcut[2], 908), mcut[1], mcut[3])
im.paste(Image.fromarray(vac), (vx0, mcut[1]))
mled2 = feathered_rect(W, H, [LED_NEW[0], mcut[1], LED_NEW[1], mcut[3]], feather=4)
im.paste(sb.crop((0, mcut[1] - Y0, LED_NEW[1] - LED_NEW[0], mcut[3] - Y0)),
         (LED_NEW[0], mcut[1]), mled2.crop((LED_NEW[0], mcut[1], LED_NEW[1], mcut[3])))
# teal-хвост угла 908..927
tt = np.array(im)
for y in range(mcut[1], mcut[3]):
    rowv = tt[y, min(930, W):min(934, W)].astype(float)
    lo = np.percentile(rowv.reshape(-1, 3), 40, axis=0)
    tt[y, 908:927] = np.clip(lo + rng.normal(0, 1.0, size=(3,)), 0, 255)
im = Image.fromarray(tt)
imm = Image.new('L', (mreg.width, mreg.height), 0)
ImageDraw.Draw(imm).rectangle([22, 22, mreg.width - 23, mreg.height - 23], fill=255)
imm = imm.filter(ImageFilter.GaussianBlur(16))
im.paste(mreg, (mcut[0] + MAP_DX, mcut[1]), imm)

im.save(OUT, 'PNG')
print('saved', OUT)
