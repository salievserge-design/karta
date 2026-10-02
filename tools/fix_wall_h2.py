# -*- coding: utf-8 -*-
"""Рекомпоновка стены зала 2 (ai-base-room2.png):
левая teal-рейка сужается 408 -> 251 px (как правая), логотип масштабируется,
деревянная зона расширяется, карта центрируется по свободной части стены."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'ai-base-room2.png')
OUT = os.path.join(ROOT, 'ai-base-room2-wall2.png')
rng = np.random.default_rng(7)

im = Image.open(SRC).convert('RGB')
W, H = im.size
a = np.array(im).copy()

def feathered_rect(w, h, box, feather=8, invert=False):
    m = Image.new('L', (w, h), 255 if invert else 0)
    d = ImageDraw.Draw(m)
    d.rectangle(box, fill=0 if invert else 255)
    return m.filter(ImageFilter.GaussianBlur(feather))

def paste_band(base_px, src_x0, src_x1, dst_x0, y0=40, y1=906, feather=4):
    """копия вертикальной полосы (LED-борт) с мягкой стыковкой по краям"""
    band = np.array(im)[y0:y1, src_x0:src_x1].copy()
    w = src_x1 - src_x0
    ap = Image.new('L', (W, H), 0)
    dd = ImageDraw.Draw(ap)
    dd.rectangle([dst_x0, y0, dst_x0 + w, y1], fill=255)
    ap = ap.filter(ImageFilter.GaussianBlur(feather))
    tile = im.crop((src_x0, y0, src_x1, y1))
    im.paste(tile, (dst_x0, y0), ap.crop((dst_x0, y0, dst_x0 + w, y1)))

# ---------- 1) заливка нового дерева слева: 404..566 ----------
XW0, XW1 = 404, 572
WIN = (1338, 1383)      # чистое дерево справа от карты
LOGO = (188, 222, 527, 428)
MAP_CUT = (565, 190, 1330, 605)
MAP_DX = -55
LED_OLD, LED_NEW = (550, 568), (390, 408)

win_w = WIN[1] - WIN[0]
tile_rows = np.array(im)[:, WIN[0]:WIN[1]].astype(float)
# столбец за столбцом случайные связные куски 5-10 px из окна — убивает ступенчатые повторы
band = np.zeros((tile_rows.shape[0], XW1 - XW0, 3))
pos = 0
while pos < XW1 - XW0:
    chunk = int(rng.integers(5, 11))
    src0 = int(rng.integers(0, max(1, win_w - chunk)))
    take = min(chunk, XW1 - XW0 - pos)
    band[:, pos:pos + take] = tile_rows[:, src0:src0 + take]
    scale = 1 + rng.normal(0, 0.015)
    band[:, pos:pos + take] *= scale
    pos += take
# тон: подгон яркости окна под соседнее дерево слева
arr0 = np.array(im).astype(float)
src_m = band[100:770].mean()
ref_m = arr0[100:210, 576:620].mean()
band = band * (ref_m / src_m)
tiled = np.clip(band * (1 + rng.normal(0, 0.008, size=band.shape[:2])[..., None]), 0, 255).astype('uint8')
ref = np.array(im)[40:906, 573:600, :].astype(float)
ref_row = ref.mean(axis=1)                       # (866,3) тон соседнего дерева по строкам
win_row = rowmed_win = np.array(im)[40:906, WIN[0]:WIN[1], :].astype(float)
win_mean = win_row.mean(axis=1)
win_var = win_row - win_mean[:, None, :]
for y in range(745, tiled.shape[0]):
    yy = max(0, min(ref_row.shape[0] - 1, y - 40))
    base = ref_row[yy]
    shim_row = win_var[min(yy, win_var.shape[0] - 1)]
    shimmer = shim_row[(np.arange(XW1 - XW0) * 5 + y) % shim_row.shape[0]]
    tiled[y, :, :] = np.clip(base[None, :] + 0.3 * shimmer +
                             rng.normal(0, 2.0, size=(XW1 - XW0, 3)), 0, 255)
tt = Image.fromarray(tiled)
mask = feathered_rect(W, H, [XW0, 40, XW1, 906], feather=7)
im.paste(tt, (XW0, 0), mask.crop((XW0, 0, XW1, H)))

# ---------- 2) новый LED-борт на x=390..408 ----------
paste_band(None, LED_OLD[0], LED_OLD[1], LED_NEW[0])

# ---------- 3) стирание логотипа: teal из чистых строк ----------
lx0, ly0, lx1, ly1 = LOGO[0], LOGO[1], min(LOGO[2], LED_NEW[0] - 1), 448
arr = np.array(im).astype(float)
ref = arr[505:640, lx0:lx1]          # чистый teal ниже текста
col_med = np.median(ref, axis=0)     # цвет колонки
slat_pat = ref - col_med[None, :]    # паттерн реек по y
hrect = ly1 - ly0
repv = int(np.ceil(hrect / ref.shape[0])) + 1
pat = np.tile(slat_pat, (repv, 1, 1))[:hrect] * 0.85
prof = arr[120:860, lx0:lx1].mean(axis=(1, 2))
g = prof / prof[:150].mean()
gy = np.interp(np.arange(ly0, ly1), np.arange(120, 860), g)
fill = col_med[None, :, :] * gy[:, None, None] + pat
fill = np.clip(fill * (1 + rng.normal(0, 0.01, size=fill.shape[:2])[..., None]), 0, 255).astype('uint8')
fim = Image.fromarray(fill)
m2 = feathered_rect(W, H, [lx0, ly0, lx1, ly1], feather=7)
im.paste(fim, (lx0, ly0), m2.crop((lx0, ly0, lx1, ly1)))

# ---------- 4) логотип: вырезать по белой маске, уменьшить, вклеить ----------
lg = np.array(im).astype(int)  # ВАЖНО: логотип уже стёрт — берём из ОРИГИНАЛА
orig = np.array(Image.open(SRC).convert('RGB')).astype(int)
reg = orig[LOGO[1]:LOGO[3], LOGO[0]:LOGO[2]]
white = (reg.min(axis=2) > 142) & ((reg.max(axis=2) - reg.min(axis=2)) < 48)
white = white | (reg.mean(axis=2) > 200)
lam = Image.fromarray((white * 255).astype('uint8'))
lam = lam.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.2))
limg = Image.open(SRC).convert('RGB').crop(LOGO)
sc = 251 / 408.0
nw, nh = int(limg.width * sc), int(limg.height * sc)
limg_r = limg.resize((nw, nh), Image.LANCZOS)
lam_r = lam.resize((nw, nh), Image.LANCZOS)
cx, cy = 266, 325
px, py = int(cx - nw / 2), int(cy - nh / 2)
im.paste(limg_r, (px, py), lam_r)

# ---------- 5) карта: вырезать с ореолом, сдвинуть, заполнить правый след ----------
mcut = MAP_CUT
mreg = im.crop(mcut)  # включает glow
mm = feathered_rect(im.width, im.height, list(mcut), feather=20)
# мягкая альфа вырезки: рисуем на отдельном холсте через маску
bg = im.copy()
# заполнить исходное место дерева из окна случайными связными кусками
vacw = mcut[2] - mcut[0]
vband = np.zeros((mcut[3] - mcut[1], vacw, 3))
pos = 0
vwin = np.array(im)[mcut[1]:mcut[3], WIN[0]:WIN[1]].astype(float)
while pos < vacw:
    chunk = int(rng.integers(5, 11))
    src0 = int(rng.integers(0, max(1, win_w - chunk)))
    take = min(chunk, vacw - pos)
    vband[:, pos:pos + take] = vwin[:, src0:src0 + take]
    pos += take
vband *= (np.array(im)[mcut[1]:mcut[3], 576:610].astype(float).mean() / vband.mean())
im.paste(Image.fromarray(np.clip(vband, 0, 255).astype('uint8')), (mcut[0], mcut[1]))
# вклеить карту со сдвигом
imm = Image.new('L', (mreg.width, mreg.height), 0)
ImageDraw.Draw(imm).rectangle([20, 20, mreg.width - 21, mreg.height - 21], fill=255)
imm = imm.filter(ImageFilter.GaussianBlur(14))
im = im.convert('RGB')
im.paste(mreg, (mcut[0] + MAP_DX, mcut[1]), imm)

im.save(OUT, 'PNG')
print('saved', OUT)
