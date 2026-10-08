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
    """Perched facing the viewer, cloak spilling to both sides in the wind."""
    # cloak behind, drawn outward from the shoulders on each side
    for s in (-1, 1):
        for y in range(int(-13 * K), int(5 * K) + 1):
            t = (y - (-13 * K)) / (18 * K)
            gust = math.sin(ph + s * 0.7) * 0.5 + 0.5
            reach = (2.2 + t * 7.5 * (0.7 + gust * 0.7)) * K * 1.5
            reach += math.sin(y * 0.8 + ph * 1.4 + s) * 1.5 * K * t * 3
            if reach < 1:
                continue
            c.rect(ox + (1 if s > 0 else -reach), oy + y, max(1, reach), 1, CLOAK)
            if y % 4 == 0:
                c.rect(ox + s * reach * .6, oy + y, 1, 1, CLOAK_HI)
    # hunched body, knees up, feet gripping the ledge
    c.rect(ox - 3, oy - 9 * K - 2, 6, 9 * K + 2, BODY)
    c.rect(ox - 4, oy - 1, 3, 2, BODY)
    c.rect(ox + 2, oy - 1, 3, 2, BODY)
    # hood and a sliver of face, looking straight out
    c.fcircle(ox, oy - 11 * K - 2.5, 3.0 * K + 1.4, CLOAK)
    c.fcircle(ox, oy - 11 * K - 2.2, 2.1 * K + 1.0, BODY)
    c.rect(ox - 1, oy - 11 * K - 2.6, 2, 2, SKIN)
    c.rect(ox - 2, oy - 5 * K - 1, 5, 1, TRIM)


def sheet(fn, frames, path):
    c = Canvas(BOX * frames, BOX, KEY)
    for i in range(frames):
        fn(c, i * BOX + ORIGIN[0], ORIGIN[1], i / float(frames) * 2 * math.pi)
    return save(c, path)


if __name__ == '__main__':
    for name, fn, n in (('lookout-glide', bat, 12), ('lookout-perch', perched, 24)):
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
