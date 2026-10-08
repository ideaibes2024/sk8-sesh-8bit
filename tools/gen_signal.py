#!/usr/bin/env python3
"""
The NIGHT SIGNAL -- Night Man's mark thrown onto the sky.

Emits night-signal.png: a banded disc of warm light with his
crescent-and-bar emblem standing dark inside it. The alpha falloff is
quantised into a handful of steps so it bands like 8-bit art instead of
fading smoothly. The beam itself is CSS (see index.html).

    python3 tools/gen_signal.py
"""
import math, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N, SCALE = 64, 5
CX = CY = 32.0

GLOW = (255, 243, 198)
EMBLEM = (14, 16, 34)


def main():
    from PIL import Image
    px = []
    for y in range(N):
        for x in range(N):
            d = math.hypot(x + .5 - CX, y + .5 - CY) / 30.0
            if d >= 1:
                px.append((0, 0, 0, 0)); continue
            a = (1 - d) ** 1.25
            a = round(a * 6) / 6.0                 # band the falloff
            px.append(GLOW + (int(a * 252),))

    im = Image.new('RGBA', (N, N))
    im.putdata(px)
    p = im.load()

    def disc(cx, cy, r, col):
        for y in range(N):
            for x in range(N):
                if (x + .5 - cx) ** 2 + (y + .5 - cy) ** 2 <= r * r:
                    p[x, y] = col

    # waning crescent: a disc with a second disc bitten out of it
    disc(30, 32, 10, EMBLEM + (255,))
    bite = []
    for y in range(N):
        for x in range(N):
            if (x + .5 - 34.5) ** 2 + (y + .5 - 30.5) ** 2 <= 8.6 ** 2:
                bite.append((x, y))
    for x, y in bite:
        d = math.hypot(x + .5 - CX, y + .5 - CY) / 30.0
        a = round(max(0.0, (1 - d)) ** 1.25 * 6) / 6.0
        p[x, y] = GLOW + (int(a * 252),)
    # the bar through it
    for y in range(19, 46):
        for x in range(29, 32):
            p[x, y] = EMBLEM + (255,)

    out = os.path.join(ROOT, 'night-signal.png')
    im.resize((N * SCALE, N * SCALE), Image.NEAREST).save(out)
    print('night-signal.png  %dx%d  %d KB'
          % (N * SCALE, N * SCALE, os.path.getsize(out) // 1024))


if __name__ == '__main__':
    main()
