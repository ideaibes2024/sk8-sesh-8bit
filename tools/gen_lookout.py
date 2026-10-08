#!/usr/bin/env python3
"""
SK8 SESH -- "the night lookout": an original caped figure.

  lookout-glide.png   12 frames, a pure black bat silhouette, wings beating
  lookout-perch.png   24 frames, front-facing on the ledge, cloak in the wind

Original design. In the air it reads only as a bat shape; perched it is a
small hooded figure facing the viewer with a cloak spreading to both sides.

    python3 tools/gen_lookout.py [--contact]
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_scene import Canvas, hx, KEY

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCALE = 5
BOX = 34
ORIGIN = (17, 26)          # perch contact inside the cell
K = 0.62                   # overall figure scale -- smaller than before

BLACK = hx('#07060c')
CLOAK = hx('#17132a')
CLOAK_HI = hx('#2b2448')
BODY = hx('#0d0a16')
TRIM = hx('#5b4f94')
SKIN = hx('#caa882')

# Night Man's palette (matches tools/gen_nightman.py)
NM_NAVY = hx('#1e2a52')
NM_NAVY_D = hx('#131a34')
NM_NAVY_L = hx('#2f4078')
NM_BLK = hx('#080a12')
NM_SILVER = hx('#c6ccdc')
NM_SILVER_D = hx('#8b93a8')
NM_VISOR = hx('#6ad3ff')
NM_VISOR_L = hx('#c3ecff')
NM_CAPE = hx('#0f1536')
NM_CAPE_F = hx('#1a2254')
NM_CAPE_E = hx('#080b1e')


def save(c, path):
    from PIL import Image
    im = Image.new('RGBA', (c.w, c.h))
    im.putdata([(0, 0, 0, 0) if c.px[y][x] == KEY else c.px[y][x] + (255,)
                for y in range(c.h) for x in range(c.w)])
    im.resize((c.w * SCALE, c.h * SCALE), Image.NEAREST).save(path)
    return os.path.getsize(path)


def bat(c, ox, oy, ph):
    """Flying form: a flat black bat silhouette, nothing but shape."""
    flap = math.sin(ph)
    span = 13 * K * 1.9
    for s in (-1, 1):
        for i in range(1, int(span) + 1):
            t = i / span
            # wing sweeps up and down; the membrane scallops along the edge
            top = -1.5 * K - math.sin(t * math.pi) * 3.2 * K + flap * 7.5 * K * t
            thick = (1 - t) * 4.6 * K + 1.2 + math.sin(t * 9) * .5
            c.rect(ox + s * i, oy + top, 1, max(1, thick), BLACK)
        # wing tip finger
        tt = flap * 7.5 * K + -1.5 * K
        c.rect(ox + s * int(span), oy + tt - 1, 1, 3, BLACK)
    # body and ears
    c.fcircle(ox, oy, 2.6 * K + 1.1, BLACK)
    c.rect(ox - 2, oy - 3.4 * K - 1.6, 1, 2, BLACK)
    c.rect(ox + 1, oy - 3.4 * K - 1.6, 1, 2, BLACK)


def perched(c, ox, oy, ph):
    """Night Man standing watch on the rooftop, cape streaming left.

    Small -- roughly 20px tall. The silhouette is FIXED; only the cape's
    trailing edge drifts, because animating the whole outline makes it
    pulse like a loading spinner. Origin is at his feet."""
    # --- cape first, behind him, swept hard left ------------------------
    for y in range(-14, 1):
        t = (y + 14) / 15.0
        reach = 2 + (t ** 0.7) * 10
        xl = int(ox - reach)
        for x in range(xl, ox + 3):
            band = ((ox - x) // 3) % 2
            c.set(x, oy + y, NM_CAPE_F if band else NM_CAPE)
        c.set(xl, oy + y, NM_CAPE_E)
    for i, yy in enumerate((-1, 0)):
        gust = math.sin(ph + i * 0.8)
        extra = (1 if gust > 0.1 else 0) + (1 if gust > 0.7 else 0)
        c.rect(ox - 12 - extra, oy + yy, 2 + extra, 1, NM_CAPE)
    wisp = int(1 + (math.sin(ph * 1.2) + 1) * 1.2)
    c.rect(ox - 14 - wisp, oy - 3, wisp, 1, NM_CAPE_E)

    # --- legs and boots -------------------------------------------------
    for lx in (ox - 3, ox + 1):
        c.rect(lx, oy - 7, 2, 5, NM_NAVY_D)
        c.rect(lx - 1, oy - 2, 4, 2, NM_BLK)
    # --- torso, belt, emblem --------------------------------------------
    c.rect(ox - 4, oy - 13, 8, 6, NM_NAVY_D)
    c.rect(ox - 4, oy - 13, 4, 6, NM_NAVY)
    c.rect(ox - 5, oy - 14, 10, 2, NM_NAVY_L)
    c.rect(ox, oy - 12, 1, 3, NM_SILVER)
    c.rect(ox - 4, oy - 8, 9, 1, NM_SILVER)
    c.rect(ox - 4, oy - 7, 9, 1, NM_SILVER_D)
    # --- arms -------------------------------------------------------------
    for ax in (ox - 6, ox + 5):
        c.rect(ax, oy - 12, 2, 5, NM_NAVY_D)
        c.rect(ax, oy - 8, 2, 1, NM_BLK)
    # --- helmet, visor, swept crest --------------------------------------
    c.rect(ox - 2, oy - 19, 5, 6, NM_NAVY_D)
    c.rect(ox - 2, oy - 19, 2, 6, NM_NAVY)
    c.rect(ox - 2, oy - 19, 5, 1, NM_NAVY_L)
    c.rect(ox - 1, oy - 14, 3, 1, NM_BLK)
    c.rect(ox - 1, oy - 17, 4, 1, NM_VISOR)
    c.set(ox - 1, oy - 17, NM_VISOR_L)
    for i in range(3):
        c.rect(ox - 2 - i, oy - 20, 1, 1, NM_NAVY_L if i % 2 else NM_NAVY)


def sheet(fn, frames, path):
    """Emits frames+1 cells, the last a copy of the first.

    With background-size:(N*100)% the browser spreads position 0%..100%
    across (imageWidth - elementWidth) = (N-1) cells, so steps(N) lands
    BETWEEN cells and two figures show at once. One extra cell makes the
    travel exactly N cells, so every step is cell-aligned."""
    n = frames + 1
    c = Canvas(BOX * n, BOX, KEY)
    for i in range(n):
        fn(c, i * BOX + ORIGIN[0], ORIGIN[1],
           (i % frames) / float(frames) * 2 * math.pi)
    return save(c, path)


if __name__ == '__main__':
    for name, fn, n in (('lookout-glide', bat, 12), ('lookout-perch', perched, 16)):
        p = os.path.join(ROOT, name + '.png')
        print('%-18s %d frames  %d KB' % (name + '.png', n, sheet(fn, n, p) // 1024))
        if '--contact' in sys.argv:
            from PIL import Image
            im = Image.open(p)
            w = BOX * SCALE * min(n, 12)
            rows = [im.crop((r * w, 0, (r + 1) * w, BOX * SCALE))
                    for r in range(max(1, n // 12))]
            out = Image.new('RGB', (w, BOX * SCALE * len(rows)), (36, 34, 52))
            for i, r in enumerate(rows):
                out.paste(r, (0, i * BOX * SCALE), r)
            out.save(os.path.join(ROOT, 'tools', name + '-contact.png'))
