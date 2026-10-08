#!/usr/bin/env python3
"""
The RIDER -- the reference skater, redrawn at the game's pixel scale and
animated for the left-hand quarter pipe.

Loop: in from off-screen left -> up the transition -> small air -> land on
the deck -> roll forward -> 180 turn -> roll back -> down the ramp -> off
the left edge. Seamless, because the first and last frames are both
off-screen on the flat.

Design follows the supplied character sheet: red beanie with a white pom
and a darker band, black sunglasses, goatee, blue hoodie, black trousers,
blue-and-white sneakers, blue deck on natural wood.

    python3 tools/gen_rider.py [--contact]
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_scene import Canvas, hx, KEY

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCALE = 5
BOX = 34
ORIGIN = (17, 28)          # board contact inside the cell
FRAMES = 48

RED = hx('#d8232a')
RED_D = hx('#a8171d')
WHITE = hx('#ffffff')
SKIN = hx('#f3c99a')
SKIN_D = hx('#d9a97a')
INK = hx('#141414')
LENS = hx('#6b7280')
GOATEE = hx('#4a2f1c')
HOOD = hx('#1a5fd0')
HOOD_D = hx('#134aa3')
PANT = hx('#2b2b2f')
PANT_D = hx('#1c1c20')
WOOD = hx('#e8c79a')
TRUCK = hx('#d8232a')
WHEEL = hx('#ffffff')


def save(c, path):
    from PIL import Image
    im = Image.new('RGBA', (c.w, c.h))
    im.putdata([(0, 0, 0, 0) if c.px[y][x] == KEY else c.px[y][x] + (255,)
                for y in range(c.h) for x in range(c.w)])
    im.resize((c.w * SCALE, c.h * SCALE), Image.NEAREST).save(path)
    return os.path.getsize(path)


def draw(c, ox, oy, p, k):
    """p: crouch 0..1, lean px, arm swing, board angle, vertical offset.
    k: horizontal scale -- 1 faces right, -1 faces left, near 0 is the
    foreshortened middle of the 180."""
    cr = p['c'] * 3.0
    ln = p['lean']
    oy = oy + p.get('dy', 0)
    kk = max(0.14, abs(k))

    def rr(dx, dy, w, h, col):
        ddx = dx if k >= 0 else -(dx + w)
        c.rect(ox + ddx * kk, oy + dy, max(1, w * kk), h, col)

    # --- board (tilted by angle, drawn column by column) ----------------
    ba = p['ba']
    for i in range(-8, 9):
        dy = -ba * i / 8.0
        rr(i, dy, 1, 1, WOOD)
        rr(i, dy + 1, 1, 1, HOOD)            # blue underside
    for tx in (-5, 4):
        dy = -ba * tx / 8.0
        rr(tx, dy + 2, 2, 1, TRUCK)
        rr(tx, dy + 3, 2, 1, WHEEL)

    # --- legs and shoes -------------------------------------------------
    for fx in (-6, 2):
        dy = -ba * (fx + 2) / 8.0
        rr(fx, dy - 3, 4, 2, WHITE)
        rr(fx, dy - 1, 4, 1, HOOD)           # blue sneaker stripe
        rr(fx + 1, -11 + cr, 3, 8 - cr + dy, PANT)
        rr(fx + 1, -11 + cr, 1, 8 - cr + dy, PANT_D)

    # --- hoodie ----------------------------------------------------------
    rr(-4 + ln, -19 + cr, 9, 8, HOOD)
    rr(-4 + ln, -19 + cr, 3, 8, HOOD_D)      # shaded back
    rr(-5 + ln, -20 + cr, 4, 3, HOOD_D)      # hood bunched behind the neck
    # arms: back arm swings opposite the front one
    sw = p['arm']
    rr(-6 + ln - sw, -18 + cr, 2, 6, HOOD_D)
    rr(4 + ln + sw, -18 + cr, 2, 6, HOOD)
    rr(-6 + ln - sw, -13 + cr, 2, 2, SKIN_D)
    rr(4 + ln + sw, -13 + cr, 2, 2, SKIN)

    # --- head ------------------------------------------------------------
    rr(-2 + ln, -24 + cr, 6, 5, SKIN)
    rr(-2 + ln, -24 + cr, 2, 5, SKIN_D)
    rr(-2 + ln, -22 + cr, 6, 1, INK)         # sunglasses
    rr(2 + ln, -22 + cr, 1, 1, LENS)
    rr(1 + ln, -20 + cr, 2, 1, GOATEE)
    # --- beanie ------------------------------------------------------------
    rr(-3 + ln, -27 + cr, 8, 2, RED)
    rr(-3 + ln, -25 + cr, 8, 1, RED_D)       # turned-up band
    rr(0 + ln, -28 + cr, 2, 1, WHITE)        # pom


# ---------------------------------------------------------------------------
# the loop: (t, crouch, lean, arm, board angle, dy, facing)
# facing is the horizontal scale -- it passes through ~0 during the 180.
# ---------------------------------------------------------------------------
KEYS = [
    (0.00, 0.10, 1.0,  0.6, 0,   0,  1),    # rolling in, slight forward lean
    (0.12, 0.05, 1.0, -0.6, 0,   0,  1),
    (0.24, 0.10, 1.0,  0.6, 0,   0,  1),
    (0.34, 0.15, 1.2, -0.4, -1,  0,  1),    # onto the transition
    (0.42, 0.35, 1.5,  0.2, -2,  0,  1),    # leaning back up the curve
    (0.47, 0.75, 1.0,  1.2, -3,  0,  1),    # compress before the lip
    (0.50, 0.15, 0.4,  1.8, -2, -3,  1),    # small air off the top
    (0.53, 0.20, 0.6,  1.2, -1, -1,  1),
    (0.56, 0.70, 0.8,  0.2, 0,   0,  1),    # landing compression
    (0.60, 0.15, 1.0, -0.5, 0,   0,  1),    # roll forward on the deck
    (0.66, 0.30, 0.4,  0.4, 0,   0,  1),    # slowing for the turn
    (0.70, 0.45, 0.0,  0.8, 0,   0,  0.5),  # pivoting -- foreshortened
    (0.73, 0.50, 0.0,  1.0, 0,   0, -0.2),
    (0.76, 0.40, 0.0,  0.6, 0,   0, -0.7),
    (0.79, 0.20, 1.0, -0.4, 0,   0, -1),    # round, now facing left
    (0.85, 0.10, 1.0,  0.6, 0,   0, -1),
    (0.89, 0.25, 1.3, -0.4, 2,   0, -1),    # over the lip, nose down
    (0.94, 0.20, 1.2,  0.5, 2,   0, -1),    # down the transition
    (0.97, 0.10, 1.0, -0.6, 0,   0, -1),
    (1.00, 0.10, 1.0,  0.6, 0,   0, -1),
]


def ease(t):
    return t * t * (3 - 2 * t)


def sample(u):
    for i in range(len(KEYS) - 1):
        a, b = KEYS[i], KEYS[i + 1]
        if a[0] <= u <= b[0]:
            f = ease((u - a[0]) / (b[0] - a[0])) if b[0] > a[0] else 0
            v = [a[j] + (b[j] - a[j]) * f for j in range(1, 7)]
            return dict(c=v[0], lean=v[1], arm=v[2], ba=v[3], dy=v[4]), v[5]
    return dict(c=KEYS[-1][1], lean=KEYS[-1][2], arm=KEYS[-1][3],
                ba=KEYS[-1][4], dy=KEYS[-1][5]), KEYS[-1][6]


if __name__ == '__main__':
    n = FRAMES + 1                     # +1 cell so CSS steps land cleanly
    c = Canvas(BOX * n, BOX, KEY)
    for i in range(n):
        p, k = sample((i % FRAMES) / float(FRAMES))
        draw(c, i * BOX + ORIGIN[0], ORIGIN[1], p, k)
    out = os.path.join(ROOT, 'rider.png')
    print('rider.png  %d frames  %d KB' % (FRAMES, save(c, out) // 1024))

    if '--contact' in sys.argv:
        from PIL import Image
        im = Image.open(out)
        w = BOX * SCALE * 12
        rows = [im.crop((r * w, 0, (r + 1) * w, BOX * SCALE)) for r in range(4)]
        sheet = Image.new('RGB', (w, BOX * SCALE * 4), (40, 44, 58))
        for i, r in enumerate(rows):
            sheet.paste(r, (0, i * BOX * SCALE), r)
        sheet.save(os.path.join(ROOT, 'tools', 'rider-contact.png'))
