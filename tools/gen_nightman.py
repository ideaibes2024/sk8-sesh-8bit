#!/usr/bin/env python3
"""
NIGHT MAN -- an original 8-bit pixel-art superhero.

Standing heroic on a rooftop, wind from the right, cape streaming far to
the LEFT with chunky pixelated folds. Night skyline and a big moon behind.

Deliberately NOT Batman: smooth armored helmet with a glowing visor slit
and a single swept-back crest fin (no pointed ears, no bat emblem). His
mark is an original one -- a waning crescent pierced by a vertical bar.

    python3 tools/gen_nightman.py
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_scene import Canvas, hx

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H, SCALE = 160, 160, 6

SKY = ['#080818', '#0e0e28', '#151540', '#1d1a54', '#2a1f5e']
MOON = '#ece9c9'
MOON_SH = '#cdc9a2'
MOON_CRATER = '#d8d4ae'
BLD = '#090a18'
BLD2 = '#101228'
BLD3 = '#15182f'
WIN = '#ffd98a'
WIN2 = '#ffeec0'
LEDGE = '#121428'
LEDGE_TOP = '#1d2040'

NAVY = '#1e2a52'
NAVY_D = '#131a34'
NAVY_L = '#2f4078'
BLK = '#080a12'
SILVER = '#c6ccdc'
SILVER_D = '#8b93a8'
VISOR = '#6ad3ff'
VISOR_L = '#c3ecff'
CAPE = '#0f1536'
CAPE_F = '#1a2254'
CAPE_E = '#080b1e'

CX, FEET = 96, 138          # character centre line, and where his boots land


def sky(c):
    bands = [(0, 26), (26, 52), (52, 76), (76, 96), (96, 118)]
    for i, (a, b) in enumerate(bands):
        c.rect(0, a, W, b - a, hx(SKY[i]))
        for x in range(0, W, 2):                      # ordered dither seam
            c.set(x + i % 2, b - 1, hx(SKY[min(i + 1, 4)]))
    for i, (sx, sy) in enumerate(((12, 10), (34, 26), (58, 8), (76, 30), (120, 14),
                                  (140, 34), (26, 48), (66, 58), (148, 56), (6, 34),
                                  (96, 18), (132, 70), (18, 66), (112, 46))):
        c.set(sx, sy, hx('#ffffff' if i % 3 else '#cfe4ff'))


def moon(c):
    mx, my, r = 100, 44, 31
    for i in range(5):                                 # soft halo, banded
        c.fcircle(mx, my, r + 10 - i * 2, hx(SKY[4]), .10)
    c.fcircle(mx, my, r, hx(MOON_SH))
    c.fcircle(mx - 2, my - 2, r - 2, hx(MOON))
    for cx_, cy_, cr in ((94, 30, 5), (114, 48, 4), (100, 52, 3),
                         (112, 30, 2), (90, 45, 2)):
        c.fcircle(cx_, cy_, cr, hx(MOON_CRATER))


def skyline(c):
    for bx, bw, bh, col in ((0, 20, 30, BLD2), (18, 14, 44, BLD), (30, 22, 24, BLD3),
                            (50, 16, 38, BLD), (64, 20, 28, BLD2), (82, 14, 48, BLD),
                            (94, 24, 32, BLD3), (116, 16, 42, BLD), (130, 18, 26, BLD2),
                            (146, 16, 38, BLD)):
        top = 134 - bh
        c.rect(bx, top, bw, bh, hx(col))
        c.rect(bx, top, bw, 1, hx('#20244a'))
        n = 0
        for wy in range(top + 4, 132, 5):
            for wx in range(bx + 3, bx + bw - 3, 5):
                n += 1
                if n % 5 == 0:
                    continue
                c.rect(wx, wy, 2, 2, hx(WIN2 if n % 3 else WIN))
    # rooftop he stands on
    c.rect(0, 134, W, 8, hx(LEDGE))
    c.rect(0, 134, W, 2, hx(LEDGE_TOP))
    c.rect(0, 142, W, H - 142, hx('#0b0c1a'))
    for x in range(0, W, 12):                          # parapet blocks
        c.rect(x, 140, 7, 2, hx('#171a34'))


def cape(c):
    """Swept hard left. The outer edge is a curve, not a straight taper, and
    the folds narrow toward the leading edge so it reads as cloth."""
    top, bot = 78, 144
    for y in range(top, bot):
        t = (y - top) / float(bot - top)
        # ease the sweep so it bells out low down instead of forming a wedge
        reach = 14 + (t ** 0.72) * 72 + math.sin(y * 0.38) * 4 * t
        xl = int(CX - reach)
        xr = int(CX + 9 - t * 6)
        if y > bot - 9:                                 # ragged hem
            xl += int(abs(math.sin(y * 1.55)) * 11)
        for x in range(xl, xr):
            d = (CX - x) / max(1.0, reach)              # 0 at body, 1 at edge
            # folds get tighter toward the leading edge
            period = 9 - d * 4
            band = int((CX - x + t * 14) / period) % 2
            col = CAPE_F if band else CAPE
            if d > 0.93:
                col = CAPE_E
            c.set(x, y, hx(col))
        c.set(xl, y, hx(CAPE_E)); c.set(xl + 1, y, hx(CAPE_E))
    # the cape's shoulder yoke, so it attaches instead of floating
    c.rect(CX - 14, 76, 24, 4, hx(CAPE_F))
    c.rect(CX - 14, 76, 24, 1, hx(CAPE_E))
    # torn streamers off the leading edge
    for sy, sl in ((104, 11), (118, 15), (130, 9)):
        t = (sy - top) / float(bot - top)
        x0 = int(CX - (14 + (t ** 0.72) * 72)) - 3
        c.rect(x0 - sl, sy, sl, 2, hx(CAPE))
        c.rect(x0 - sl, sy, 2, 2, hx(CAPE_E))


def hero(c):
    # --- legs and boots -------------------------------------------------
    for lx in (CX - 11, CX + 3):
        c.rect(lx, 110, 8, 20, hx(NAVY_D))
        c.rect(lx, 110, 4, 20, hx(NAVY))
        c.rect(lx - 1, 128, 10, 10, hx(BLK))
        c.rect(lx - 1, 128, 10, 2, hx(SILVER_D))
        c.rect(lx - 1, 136, 10, 2, hx('#05060c'))
    # --- torso ----------------------------------------------------------
    c.rect(CX - 13, 80, 26, 26, hx(NAVY_D))
    c.rect(CX - 13, 80, 13, 26, hx(NAVY))
    c.rect(CX - 13, 80, 26, 3, hx(NAVY_L))
    for yy in (89, 97):
        c.rect(CX - 13, yy, 26, 1, hx(BLK))
    # --- shoulders ------------------------------------------------------
    for px in (CX - 19, CX + 11):
        c.rect(px, 78, 8, 9, hx(NAVY_L))
        c.rect(px, 78, 8, 2, hx(SILVER_D))
        c.rect(px, 86, 8, 1, hx(BLK))
    # --- his mark: a waning crescent pierced by a bar -------------------
    c.fcircle(CX - 1, 92, 6, hx(SILVER))
    c.fcircle(CX + 3, 91, 5.2, hx(NAVY_D))
    c.rect(CX - 1, 85, 2, 14, hx(SILVER))
    # --- belt -----------------------------------------------------------
    c.rect(CX - 14, 106, 28, 5, hx(SILVER_D))
    c.rect(CX - 14, 106, 28, 2, hx(SILVER))
    for px in (CX - 12, CX - 3, CX + 7):
        c.rect(px, 107, 5, 5, hx(SILVER))
        c.rect(px, 110, 5, 1, hx(SILVER_D))
    c.rect(CX - 13, 111, 26, 3, hx(NAVY_D))
    # --- arms (a dark gap keeps them off the torso) ---------------------
    for ax in (CX - 20, CX + 14):
        c.rect(ax - 1, 86, 8, 22, hx(BLK))
        c.rect(ax, 87, 6, 19, hx(NAVY_D))
        c.rect(ax, 87, 2, 19, hx(NAVY))
        c.rect(ax - 1, 104, 8, 6, hx(BLK))           # gauntlet
        c.rect(ax - 1, 104, 8, 1, hx(SILVER))
        c.rect(ax - 1, 108, 8, 1, hx(SILVER_D))
        c.rect(ax, 110, 6, 5, hx(BLK))               # clenched fist
    # --- head -----------------------------------------------------------
    c.rect(CX - 9, 58, 18, 20, hx(NAVY_D))
    c.rect(CX - 9, 58, 9, 20, hx(NAVY))
    c.rect(CX - 9, 58, 18, 2, hx(NAVY_L))
    c.rect(CX - 10, 61, 1, 13, hx(NAVY_D))
    c.rect(CX + 9, 61, 1, 13, hx(NAVY_D))
    c.rect(CX - 8, 74, 16, 4, hx(BLK))               # jaw guard
    c.rect(CX - 6, 76, 12, 2, hx(NAVY_D))
    # swept-back crest fin -- one blade, not ears
    for i in range(10):
        c.rect(CX - 2 - i, 53 - (i // 4), 2, 5 - (i // 5), hx(NAVY_L if i % 2 else NAVY))
    c.rect(CX - 11, 56, 13, 2, hx(NAVY_L))
    c.rect(CX - 11, 56, 13, 1, hx(BLK))
    # visor
    c.rect(CX - 8, 64, 16, 4, hx(BLK))
    c.rect(CX - 7, 65, 14, 2, hx(VISOR))
    c.rect(CX - 7, 65, 5, 1, hx(VISOR_L))
    c.rect(CX + 3, 65, 3, 1, hx(VISOR_L))
    for i in range(4):
        c.rect(CX - 9 - i, 63 - i, 18 + i * 2, 6 + i * 2, hx(VISOR), .06)
    c.rect(CX - 5, 78, 10, 3, hx(BLK))               # neck


def vignette(c):
    for y in range(H):
        for x in range(W):
            d = max(abs(x - W / 2) / (W / 2), abs(y - H / 2) / (H / 2))
            if d > .74:
                c.set(x, y, hx('#04040c'), (d - .74) * 1.5)


if __name__ == '__main__':
    from PIL import Image
    c = Canvas(W, H, hx(SKY[0]))
    sky(c); moon(c); skyline(c)
    cape(c); hero(c)
    vignette(c)
    im = Image.new('RGB', (W, H))
    im.putdata([c.px[y][x] for y in range(H) for x in range(W)])
    out = os.path.join(ROOT, 'nightman.png')
    im.resize((W * SCALE, H * SCALE), Image.NEAREST).save(out)
    print('nightman.png  %dx%d  %d KB' % (W * SCALE, H * SCALE,
                                          os.path.getsize(out) // 1024))
