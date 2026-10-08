#!/usr/bin/env python3
"""
SK8 SESH -- "the night lookout": an original caped figure that glides in
after dark and perches on a rooftop with its cloak moving in the wind.

  lookout-glide.png   8 frames, cloak fanned out, drifting in
  lookout-perch.png   24 frames, crouched on the ledge, cloak rippling

Original design: a hooded courier silhouette with a plain trailing cloak.

    python3 tools/gen_lookout.py [--contact]
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_scene import Canvas, hx, KEY

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCALE = 5
BOX = 34
ORIGIN = (17, 30)          # feet / perch contact inside the cell

CLOAK = hx('#241c3a')
CLOAK_HI = hx('#3b2f5c')
BODY = hx('#17121f')
TRIM = hx('#6b5fa8')
SKIN = hx('#d9b48a')


def save(c, path):
    from PIL import Image
    im = Image.new('RGBA', (c.w, c.h))
    im.putdata([(0, 0, 0, 0) if c.px[y][x] == KEY else c.px[y][x] + (255,)
                for y in range(c.h) for x in range(c.w)])
    im.resize((c.w * SCALE, c.h * SCALE), Image.NEAREST).save(path)
    return os.path.getsize(path)


def perched(c, ox, oy, ph):
    """Crouched on a ledge facing left, cloak trailing right and rippling."""
    # cloak first, behind everything
    for y in range(-13, 4):
        t = (y + 13) / 17.0
        reach = 2.5 + t * 11 + math.sin(y * 0.55 + ph) * 2.6 * (0.35 + t)
        c.rect(ox + 1, oy + y, max(1, reach), 1, CLOAK)
        if y % 3 == 0:
            c.rect(ox + 1 + reach * .55, oy + y, 2, 1, CLOAK_HI)
    # trailing hem flicks
    hem = 2 + math.sin(ph * 1.3) * 1.5
    c.rect(ox + 12, oy + 2, max(1, hem + 3), 1, CLOAK)

    # legs tucked under, body crouched
    c.rect(ox - 3, oy - 3, 5, 3, BODY)
    c.rect(ox - 4, oy, 7, 1, BODY)
    c.rect(ox - 4, oy - 11, 6, 9, BODY)
    # shoulders / hood
    c.fcircle(ox - 1, oy - 13, 3.4, CLOAK)
    c.fcircle(ox - 2, oy - 13, 2.4, BODY)
    c.rect(ox - 4, oy - 14, 2, 2, SKIN)        # a sliver of face
    c.rect(ox - 2, oy - 9, 4, 1, TRIM)         # belt
    # forearm resting on the knee
    c.rect(ox - 4, oy - 6, 3, 1, BODY)


def gliding(c, ox, oy, ph):
    """Cloak fanned wide, body angled forward, drifting."""
    span = 13 + math.sin(ph) * 2.5
    for y in range(-9, 6):
        t = (y + 9) / 15.0
        w = span * (1 - abs(t - 0.45) * 1.5)
        if w < 1:
            continue
        c.rect(ox - w, oy + y - 2, w * 2, 1, CLOAK)
        if y % 4 == 0:
            c.rect(ox - w * .6, oy + y - 2, w * 1.2, 1, CLOAK_HI)
    c.rect(ox - 2, oy - 10, 5, 11, BODY)
    c.fcircle(ox, oy - 11, 3.2, CLOAK)
    c.fcircle(ox - 1, oy - 11, 2.2, BODY)
    c.rect(ox - 3, oy - 12, 2, 2, SKIN)
    c.rect(ox - 2, oy - 6, 4, 1, TRIM)
    c.rect(ox - 4, oy + 1, 3, 2, BODY)         # trailing legs
    c.rect(ox + 1, oy + 1, 3, 2, BODY)


def sheet(fn, frames, path):
    c = Canvas(BOX * frames, BOX, KEY)
    for i in range(frames):
        fn(c, i * BOX + ORIGIN[0], ORIGIN[1], i / float(frames) * 2 * math.pi)
    return save(c, path), c


if __name__ == '__main__':
    for name, fn, n in (('lookout-glide', gliding, 8), ('lookout-perch', perched, 24)):
        p = os.path.join(ROOT, name + '.png')
        size, c = sheet(fn, n, p)
        print('%-18s %d frames  %d KB' % (name + '.png', n, size // 1024))
        if '--contact' in sys.argv:
            from PIL import Image
            im = Image.open(p)
            w = BOX * SCALE * min(n, 8)
            rows = [im.crop((r * w, 0, (r + 1) * w, BOX * SCALE))
                    for r in range(max(1, n // 8))]
            out = Image.new('RGB', (w, BOX * SCALE * len(rows)), (40, 44, 58))
            for i, r in enumerate(rows):
                out.paste(r, (0, i * BOX * SCALE), r)
            out.save(os.path.join(ROOT, 'tools', name + '-contact.png'))
