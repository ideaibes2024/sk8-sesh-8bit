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
    """Perched facing the viewer, cloak narrower and blown to the left.

    The silhouette stays FIXED -- animating the whole outline makes it pulse
    like a loading spinner. Only the trailing edge drifts."""
    # narrow cloak, hanging further left than right as if the wind pushes it
    for y in range(int(-12 * K), int(5 * K) + 1):
        t = (y - (-12 * K)) / (17 * K)
        left = (2.0 + t * 5.4) * K * 1.5          # longer, trailing side
        right = (1.6 + t * 2.0) * K * 1.5         # tucked against the body
        c.rect(ox - left, oy + y, left + right, 1, CLOAK)

    # the trailing left edge ripples; the right side stays put
    hemy = int(5 * K)
    for i, yy in enumerate((hemy, hemy + 1)):
        base = (2.0 + 5.4) * K * 1.5
        gust = math.sin(ph + i * 0.8)
        w = base + (1 if gust > 0.2 else 0) + (1 if gust > 0.75 else 0)
        c.rect(ox - w, oy + yy, w, 1, CLOAK)
    # a wisp torn off the trailing edge, drifting further left
    wisp = int(2 + (math.sin(ph * 1.1) + 1) * 1.5)
    c.rect(ox - (2.0 + 5.4) * K * 1.5 - wisp, oy + hemy - 1, wisp, 1, CLOAK)

    # body, knees up, feet on the ledge -- all static
    c.rect(ox - 3, oy - 9 * K - 2, 6, 9 * K + 2, BODY)
    c.rect(ox - 4, oy - 1, 3, 2, BODY)
    c.rect(ox + 2, oy - 1, 3, 2, BODY)
    c.fcircle(ox, oy - 11 * K - 2.5, 3.0 * K + 1.4, CLOAK)
    c.fcircle(ox, oy - 11 * K - 2.2, 2.1 * K + 1.0, BODY)
    c.rect(ox - 1, oy - 11 * K - 2.6, 2, 2, SKIN)
    c.rect(ox - 2, oy - 5 * K - 1, 5, 1, TRIM)


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
