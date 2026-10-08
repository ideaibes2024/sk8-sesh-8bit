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

    The silhouette is FIXED -- only the cape's trailing edge drifts.
    Animating the whole outline makes it pulse like a loading spinner.
    Origin is at his feet."""
    # --- cape first, behind him, swept hard left ------------------------
    for y in range(-19, 2):
        t = (y + 19) / 21.0
        reach = 3 + (t ** 0.7) * 13
        xl = int(ox - reach)
        for x in range(xl, ox + 4):
            band = ((ox - x) // 3) % 2
            c.set(x, oy + y, NM_CAPE_F if band else NM_CAPE)
        c.set(xl, oy + y, NM_CAPE_E)
    # trailing edge ripples, plus a wisp torn off it
    for i, yy in enumerate((-2, -1, 0)):
        gust = math.sin(ph + i * 0.7)
        extra = (1 if gust > 0.1 else 0) + (1 if gust > 0.7 else 0)
        c.rect(ox - 16 - extra, oy + yy, 3 + extra, 1, NM_CAPE)
    wisp = int(1 + (math.sin(ph * 1.2) + 1) * 1.6)
    c.rect(ox - 18 - wisp, oy - 4, wisp, 1, NM_CAPE_E)

    # --- legs and boots -------------------------------------------------
    for lx in (ox - 4, ox + 1):
        c.rect(lx, oy - 9, 3, 7, NM_NAVY_D)
        c.rect(lx, oy - 9, 1, 7, NM_NAVY)
        c.rect(lx - 1, oy - 2, 5, 2, NM_BLK)
    # --- torso, belt, emblem --------------------------------------------
    c.rect(ox - 5, oy - 18, 10, 9, NM_NAVY_D)
    c.rect(ox - 5, oy - 18, 5, 9, NM_NAVY)
    c.rect(ox - 7, oy - 19, 14, 2, NM_NAVY_L)          # shoulders
    c.rect(ox - 1, oy - 16, 2, 4, NM_SILVER)           # crescent-and-bar mark
    c.rect(ox - 5, oy - 10, 11, 2, NM_SILVER_D)        # belt
    c.rect(ox - 5, oy - 10, 11, 1, NM_SILVER)
    # --- arms ------------------------------------------------------------
    for ax in (ox - 8, ox + 6):
        c.rect(ax, oy - 17, 2, 7, NM_NAVY_D)
        c.rect(ax, oy - 11, 2, 2, NM_BLK)              # gauntlet
    # --- helmet, visor, swept crest --------------------------------------
    c.rect(ox - 3, oy - 25, 7, 7, NM_NAVY_D)
    c.rect(ox - 3, oy - 25, 3, 7, NM_NAVY)
    c.rect(ox - 3, oy - 25, 7, 1, NM_NAVY_L)
    c.rect(ox - 2, oy - 19, 5, 1, NM_BLK)              # jaw
    c.rect(ox - 2, oy - 22, 5, 2, NM_BLK)
    c.rect(ox - 2, oy - 22, 5, 1, NM_VISOR)
    c.set(ox - 2, oy - 22, NM_VISOR_L)
    for i in range(4):                                  # crest blade, swept back
        c.rect(ox - 2 - i, oy - 26, 1, 1 + (i % 2), NM_NAVY_L if i % 2 else NM_NAVY)


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
