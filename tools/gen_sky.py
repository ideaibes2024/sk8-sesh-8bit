#!/usr/bin/env python3
"""
SK8 SESH -- sky assets for the live day/night cycle.

  cloud-strip.png   a seamless, horizontally tileable band of pixel clouds
  sun.png / moon.png  the two celestial bodies

The sky gradient itself is pure CSS (see index.html); these are the pieces
that have to be drawn.

    python3 tools/gen_sky.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_scene import Canvas, hx, OUT, KEY

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCALE = 5


def save(c, path):
    from PIL import Image
    im = Image.new('RGBA', (c.w, c.h))
    im.putdata([(0, 0, 0, 0) if c.px[y][x] == KEY else c.px[y][x] + (255,)
                for y in range(c.h) for x in range(c.w)])
    im.resize((c.w * SCALE, c.h * SCALE), Image.NEAREST).save(path)
    return os.path.getsize(path)


def clouds():
    """Tileable: anything crossing the right edge is drawn again on the left."""
    W, H = 320, 64
    c = Canvas(W, H, KEY)
    lumps = [(-9, 0, 4), (-3, -3, 5), (3, -2, 4.5), (8, 1, 3.5), (0, 1, 5)]

    def puff(cx, cy, s):
        for dx in (0, W, -W):                      # wrap copies
            for lx, ly, r in lumps:
                c.fcircle(cx + dx + lx * s, cy + ly * s, r * s, hx('#cfe4f2'))
            for lx, ly, r in lumps:
                c.fcircle(cx + dx + lx * s, cy + ly * s - 1 * s, r * s, hx('#ffffff'))

    for cx, cy, s in ((26, 30, 1.0), (104, 18, .78), (170, 38, .92),
                      (238, 22, .70), (300, 34, .85)):
        puff(cx, cy, s)
    return c


def sun():
    c = Canvas(34, 34, KEY)
    c.ocircle(17, 17, 12, hx('#ffe14a'))
    c.fcircle(14, 13, 4, hx('#fff7b8'))
    return c


def moon():
    c = Canvas(34, 34, KEY)
    c.ocircle(17, 17, 11, hx('#f4f1d0'))
    c.fcircle(22, 13, 9, KEY)                      # bite out the crescent
    for mx, my, mr in ((13, 21, 2), (10, 15, 1), (15, 25, 1)):
        c.fcircle(mx, my, mr, hx('#ded8c0'))
    return c


if __name__ == '__main__':
    for name, maker in (('cloud-strip', clouds), ('sun', sun), ('moon', moon)):
        p = os.path.join(ROOT, name + '.png')
        print('%-14s %d KB' % (name + '.png', save(maker(), p) // 1024))
