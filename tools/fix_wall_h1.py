# -*- coding: utf-8 -*-
"""Рекомпоновка стены зала 1 (ai-base-room.png), v3:
левая teal-секция сужается до ширины правой (177px), логотип 0.62,
дерево достраивается РЕАЛЬНЫМИ колонками стены (замена только строк
с картой/ореолом на чистые строки тех же колонок), карта центрируется."""
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

ZX0, ZX1 = 150, 313
LED_OLD, LED_NEW = (429, 443), (313, 327)
XW0 = 327                 # левая граница достраиваемого дерева
CORNER = 908              # правая граница дерева (угол)
Y0, Y1 = 150, 896
LOGO = (198, 214, 440, 380)
MAP_CUT = (316, 190, 918, 502)
MAP_DX = -55
LOGO_SCALE = 0.62
LOGO_CENTER = (232, 296)


def feathered_rect(w, h, box, feather=8):
    m = Image.new('L', (w, h), 0)
    ImageDraw.Draw(m).rectangle(box, fill=255)
    return m.filter(ImageFilter.GaussianBlur(feather))


# ---------- 0) чистый LED-борт ----------
sb = orig_im.crop((LED_OLD[0], Y0, LED_OLD[1], Y1))
clean = sb.crop((0, 480 - Y0, LED_OLD[1] - LED_OLD[0], 560 - Y0))
clean = clean.resize((LED_OLD[1] - LED_OLD[0], 402 - 208), Image.LANCZOS)
sb.paste(clean, (0, 208 - Y0))

# ---------- 1) teal-зона слева: синтез из реальных профилей + тёплое пятно ----------
P = arr0[550, ZX0:ZX1, :].copy()
cols = [170, 250, 290]
prof = arr0[:, cols, :].mean(axis=1)
V = np.zeros((H, 3))
ok_top = prof[160:205].mean(axis=0)
ok_bot = prof[408:600].mean(axis=0)
for y in range(H):
    if y < 210: V[y] = prof[y]
    elif y < 405:
        t = (y - 210) / 195.0; tt = t * t * (3 - 2 * t)
        V[y] = ok_top * (1 - tt) + ok_bot * tt
    elif y < 660: V[y] = prof[y]
    else: V[y] = prof[640:660].mean(axis=0) * 0.96
norm = V[550].copy()
strip = [x - ZX0 for x in (150, 151, 152, 310, 311, 312)]
baseline = (P[strip].mean(axis=0)[None, :] * (V / norm[None, :]))
orig_on_strip = arr0[:, [ZX0 + k for k in strip], :].mean(axis=1)
sur3 = np.clip(orig_on_strip - baseline, 0, None)
for ch in range(3):
    sur3[:, ch] = np.convolve(sur3[:, ch], np.ones(17) / 17, mode='same')
sur3 = sur3 * np.clip((430 - np.arange(H)) / 110.0, 0, 1)[:, None]
gx = np.exp(-0.5 * ((np.arange(ZX0, ZX1) - 232.0) / 95.0) ** 2)
zone = P[None, :, :] * (V[Y0:Y1] / norm[None, :])[:, None, :]
zone += sur3[Y0:Y1][:, None, :] * gx[None, :, None] * 0.9
zone *= (1 + rng.normal(0, 0.009, size=zone.shape[:2])[..., None])
zone = np.clip(zone, 0, 255).astype('uint8')
mz = feathered_rect(W, H, [ZX0, Y0, ZX1, Y1], feather=6)
im.paste(Image.fromarray(zone), (ZX0, Y0), mz.crop((ZX0, Y0, ZX1, Y1)))

# ---------- 2) LED-борт ----------
mled = feathered_rect(W, H, [LED_NEW[0], Y0, LED_NEW[1], Y1], feather=4)
im.paste(sb, (LED_NEW[0], Y0), mled.crop((LED_NEW[0], Y0, LED_NEW[1], Y1)))

# ---------- 3) ремонт дерева реальными колонками ----------
mcut = MAP_CUT
mreg_orig = orig_im.crop(mcut)          # карта+ореол с исходника
work = np.array(im).astype(float)

def bad_rows(col):
    r, g, b = col[:, 0], col[:, 1], col[:, 2]
    woodlike = (r > g + 22) & (r > b + 38) & (r < 225) & (g < 205)
    return ~woodlike

SRC_LO, SRC_HI = 512, 652   # чистые строки дерева ниже карты

for x in range(XW0, CORNER):
    col = work[Y0:655, x].copy()
    bad = bad_rows(col)
    bad[:40] = False         # верх стены не трогаем
    pool = col[SRC_LO - Y0:SRC_HI - Y0]
    i = 0
    while i < len(bad):
        if bad[i]:
            j = i
            while j < len(bad) and bad[j]:
                j += 1
            rl = j - i
            st0 = int(rng.integers(0, max(2, pool.shape[0] - 4)))
            take = min(pool.shape[0], rl)
            seg = pool[st0:st0 + take]
            if seg.shape[0] < rl:
                seg_img = Image.fromarray(seg.astype('uint8')[None, ...].repeat(2, axis=0))
                seg = np.array(seg_img.resize((rl, 2), Image.LANCZOS))[1]
            col[i:j] = seg * (1 + rng.normal(0, 0.006, size=(rl, 3)))
            i = j
        else:
            i += 1
    work[Y0:655, x] = col

im = Image.fromarray(np.clip(work, 0, 255).astype('uint8'))

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

# ---------- 5) LED-борт поверх выреза карты (очистка остатков ореола) ----------
mled2 = feathered_rect(W, H, [LED_NEW[0], mcut[1], LED_NEW[1], mcut[3]], feather=4)
im.paste(sb.crop((0, mcut[1] - Y0, LED_NEW[1] - LED_NEW[0], mcut[3] - Y0)),
         (LED_NEW[0], mcut[1]), mled2.crop((LED_NEW[0], mcut[1], LED_NEW[1], mcut[3])))

# ---------- 6) teal-хвост угла ----------
tt = np.array(im)
for y in range(mcut[1], mcut[3]):
    rowv = tt[y, min(930, W):min(934, W)].astype(float)
    lo = np.percentile(rowv.reshape(-1, 3), 40, axis=0)
    tt[y, 908:927] = np.clip(lo + rng.normal(0, 1.0, size=(3,)), 0, 255)
im = Image.fromarray(tt)

# ---------- 7) карта со сдвигом ----------
imm = Image.new('L', (mreg_orig.width, mreg_orig.height), 0)
ImageDraw.Draw(imm).rectangle([20, 20, mreg_orig.width - 21, mreg_orig.height - 21], fill=255)
imm = imm.filter(ImageFilter.GaussianBlur(15))
im.paste(mreg_orig, (mcut[0] + MAP_DX, mcut[1]), imm)

im.save(OUT, 'PNG')
print('saved', OUT)
