#!/usr/bin/env python3
"""
SK8 SESH -- background scene generator.

Draws the skatepark as a real 320x180 pixel-art raster, then emits it as a
crisp-edged SVG (one rect per merged run, grouped by colour).

    python3 tools/gen_scene.py          # writes scene-day.svg, scene-night.svg
    python3 tools/gen_scene.py --png    # also writes previews for eyeballing

Everything is drawn in 320x180 "art pixels"; SCALE blows that up to 1600x900
so the SVG matches the viewBox the CSS already expects.
"""
import math, os, sys

W, H, SCALE = 320, 180, 5
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def hx(c):
    c = c.lstrip('#')
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))


SKY_LINE = 96
BUILDINGS = ((6, 18, 26), (26, 11, 17), (40, 22, 33), (64, 14, 21),
             (222, 16, 23), (240, 12, 15), (254, 20, 30), (278, 13, 19),
             (294, 18, 25))

OUT = hx('#141414')          # universal outline ink
OUT2 = hx('#2a2320')         # softer ink for background layers


# --------------------------------------------------------------------------
# canvas
# --------------------------------------------------------------------------
KEY = (1, 2, 3)   # transparent sentinel: never blended into, never emitted


class Canvas:
    def __init__(self, w, h, bg=(0, 0, 0)):
        self.w, self.h = w, h
        self.px = [[bg] * w for _ in range(h)]

    def set(self, x, y, c, a=1.0):
        x, y = int(math.floor(x)), int(math.floor(y))
        if x < 0 or y < 0 or x >= self.w or y >= self.h or a <= 0:
            return
        if a >= 1:
            self.px[y][x] = c
        else:
            o = self.px[y][x]
            if o == KEY:        # don't tint empty sky into a grey haze
                return
            self.px[y][x] = (round(o[0] + (c[0] - o[0]) * a),
                             round(o[1] + (c[1] - o[1]) * a),
                             round(o[2] + (c[2] - o[2]) * a))

    def rect(self, x, y, w, h, c, a=1.0):
        for yy in range(int(math.floor(y)), int(math.floor(y + h))):
            for xx in range(int(math.floor(x)), int(math.floor(x + w))):
                self.set(xx, yy, c, a)

    def hline(self, x0, x1, y, c, a=1.0):
        if x1 < x0:
            x0, x1 = x1, x0
        self.rect(x0, y, x1 - x0 + 1, 1, c, a)

    def vline(self, x, y0, y1, c, a=1.0):
        if y1 < y0:
            y0, y1 = y1, y0
        self.rect(x, y0, 1, y1 - y0 + 1, c, a)

    def dot(self, x, y, t, c, a=1.0):
        """t x t block centred on x,y"""
        o = (t - 1) / 2.0
        self.rect(round(x - o), round(y - o), t, t, c, a)

    def line(self, p0, p1, c, t=1, a=1.0):
        x0, y0 = p0
        x1, y1 = p1
        n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
        for i in range(n + 1):
            f = i / n
            self.dot(x0 + (x1 - x0) * f, y0 + (y1 - y0) * f, t, c, a)

    def limb(self, p0, p1, c, t=2, ink=None):
        """outlined stroke: ink border 1px proud of a t-thick colour core"""
        self.line(p0, p1, ink if ink is not None else OUT, t + 2)
        self.line(p0, p1, c, t)

    def fcircle(self, cx, cy, r, c, a=1.0):
        r2 = r * r
        for yy in range(int(cy - r - 1), int(cy + r + 2)):
            for xx in range(int(cx - r - 1), int(cx + r + 2)):
                if (xx + .5 - cx) ** 2 + (yy + .5 - cy) ** 2 <= r2:
                    self.set(xx, yy, c, a)

    def ocircle(self, cx, cy, r, c, ink=None):
        self.fcircle(cx, cy, r + 1, ink if ink is not None else OUT)
        self.fcircle(cx, cy, r, c)

    def fellipse(self, cx, cy, rx, ry, c, a=1.0):
        for yy in range(int(cy - ry - 1), int(cy + ry + 2)):
            for xx in range(int(cx - rx - 1), int(cx + rx + 2)):
                if ((xx + .5 - cx) / rx) ** 2 + ((yy + .5 - cy) / ry) ** 2 <= 1:
                    self.set(xx, yy, c, a)

    def tint(self, c, a):
        for y in range(self.h):
            row = self.px[y]
            for x in range(self.w):
                o = row[x]
                if o == KEY:
                    continue
                row[x] = (round(o[0] + (c[0] - o[0]) * a),
                          round(o[1] + (c[1] - o[1]) * a),
                          round(o[2] + (c[2] - o[2]) * a))

    def glow(self, cx, cy, r, c, strength=.55):
        for yy in range(int(cy - r), int(cy + r + 1)):
            for xx in range(int(cx - r), int(cx + r + 1)):
                d = math.hypot(xx + .5 - cx, yy + .5 - cy)
                if d <= r:
                    self.set(xx, yy, c, strength * (1 - d / r) ** 2)


# --------------------------------------------------------------------------
# tiny 5x7 graffiti font (only the glyphs the tags need)
# --------------------------------------------------------------------------
FONT = {
    'S': [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    'K': ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    '8': [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    'E': ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    'H': ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'O': [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'Z': ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    'L': ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    'C': [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    'A': [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'N': ["#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"],
    'Y': ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    'R': ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    'P': ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    'T': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    'I': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
    'D': ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    'U': ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    ' ': [".....", ".....", ".....", ".....", ".....", ".....", "....."],
}


def text(c, x, y, s, col, px=1, ink=None, space=1):
    """draw s at art-pixel scale px, optionally with a 1-unit ink outline"""
    cx = x
    for ch in s.upper():
        g = FONT.get(ch)
        if g is None:
            cx += (5 + space) * px
            continue
        if ink is not None:
            for ry, row in enumerate(g):
                for rx, v in enumerate(row):
                    if v == '#':
                        c.rect(cx + (rx - 1) * px, y + (ry - 1) * px, px * 3, px * 3, ink)
        for ry, row in enumerate(g):
            for rx, v in enumerate(row):
                if v == '#':
                    c.rect(cx + rx * px, y + ry * px, px, px, col)
        cx += (5 + space) * px
    return cx


# --------------------------------------------------------------------------
# skater rig
# --------------------------------------------------------------------------
SKIN = ['#ffcb9a', '#f0b184', '#c8865a', '#8d5524', '#5c3a21']
HAIR = ['#2b1a12', '#7a4a22', '#ffd45e', '#ff2fb0', '#111318', '#6ad3ff', '#b5452a', '#e9e3d6']
SHIRT = ['#ff2fb0', '#ffd21f', '#2d6cdf', '#3ddc84', '#ff8a1e', '#a855f7', '#ffffff', '#19c7c7']
PANTS = ['#4a6ba8', '#5d5d70', '#8a5fd6', '#2e9c6e', '#c24a74', '#ff6a3d', '#5a5478', '#7fa3cc']
DECK = ['#7a3fd6', '#ff2fb0', '#19c7c7', '#ffd21f', '#ff8a1e', '#3ddc84']


def board(c, cx, cy, ang, pal, length=11, flip=False):
    a = math.radians(ang)
    dx, dy = math.cos(a), math.sin(a)
    nx, ny = -dy, dx                       # "down" relative to the deck
    hl = length / 2.0
    x0, y0 = cx - dx * hl, cy - dy * hl
    x1, y1 = cx + dx * hl, cy + dy * hl
    deck = pal['deck']
    # wheels + trucks first so the deck sits over them
    for f in (-0.26, 0.26):
        wx, wy = cx + dx * length * f, cy + dy * length * f
        c.line((wx, wy), (wx + nx * 1.8, wy + ny * 1.8), OUT, 3)
        c.ocircle(wx + nx * 2.4, wy + ny * 2.4, 1.2, pal['wheel'])
    # kicked nose + tail
    c.limb((x1, y1), (x1 + dx * 2.2 - nx * 1.6, y1 + dy * 2.2 - ny * 1.6), deck, 2)
    c.limb((x0, y0), (x0 - dx * 2.2 - nx * 1.6, y0 - dy * 2.2 - ny * 1.6), deck, 2)
    # deck
    c.limb((x0, y0), (x1, y1), deck, 2)
    # griptape top edge
    c.line((x0 - dx * .5 - nx * 1.2, y0 - dy * .5 - ny * 1.2),
           (x1 + dx * .5 - nx * 1.2, y1 + dy * .5 - ny * 1.2), hx('#2a2a30'), 1)


def head(c, hp, facing, skin, hair, style, accent=None):
    hxp, hyp = hp
    f = facing
    # hair mass / skull
    c.ocircle(hxp, hyp, 3.6, hair)
    # face
    c.fcircle(hxp + .9 * f, hyp + .9, 2.8, skin)
    if style == 'long':
        c.rect(hxp - 4.2 * f - (2 if f > 0 else 0), hyp - 2, 2.4, 9, OUT)
        c.rect(hxp - 3.9 * f - (1.5 if f > 0 else 0), hyp - 2, 1.8, 8, hair)
    elif style == 'ponytail':
        c.limb((hxp - 3 * f, hyp - 1), (hxp - 7 * f, hyp - 4), hair, 2)
        c.limb((hxp - 7 * f, hyp - 4), (hxp - 10 * f, hyp - 2), hair, 2)
    elif style == 'bun':
        c.ocircle(hxp - 2.6 * f, hyp - 3.4, 1.9, hair)
    elif style == 'cap':
        c.fcircle(hxp, hyp - .6, 3.7, accent or hx('#ff2fb0'))
        c.rect(hxp - 4, hyp - 4.4, 8, 1, OUT)
        c.rect(hxp + (1 if f > 0 else -5) * 1, hyp - 1.4, 5 if f > 0 else 5, 1.6, OUT)
        c.rect(hxp + (1 if f > 0 else -4.6), hyp - 1.2, 4.4, 1.1, accent or hx('#ff2fb0'))
    elif style == 'beanie':
        c.fcircle(hxp, hyp - 1, 3.7, accent or hx('#19c7c7'))
        c.rect(hxp - 3.9, hyp - 1.6, 7.8, 1.6, OUT)
        c.rect(hxp - 3.6, hyp - 1.4, 7.2, 1.2, accent or hx('#19c7c7'))
        c.ocircle(hxp, hyp - 4.6, 1.2, hx('#ffffff'))
    elif style == 'helmet':
        c.fcircle(hxp, hyp - .4, 3.9, accent or hx('#ffd21f'))
        c.fcircle(hxp + 1.1 * f, hyp + 1.4, 2.5, skin)
        c.rect(hxp - 4, hyp - 4.6, 8, 1, OUT)
    # face features
    c.rect(hxp + 1.7 * f - (1 if f < 0 else 0), hyp + .2, 1, 2, OUT)
    c.rect(hxp + .2 * f, hyp + 2.6, 1.6, 1, OUT)


def skater(c, ox, oy, pose, pal, flip=False, shadow=None, board_ang=None):
    """pose: dict of local joints, +x forward, -y up, origin at board centre.

    Strokes are collected first, then drawn in two passes -- every outline,
    then every colour -- so neighbouring limbs can't ink over each other and
    the figure reads as a coloured silhouette instead of a black blob.
    """
    f = -1 if flip else 1

    def P(p):
        return (ox + p[0] * f, oy + p[1])

    if shadow is not None:
        c.fellipse(ox, shadow, 7, 2, hx('#000000'), .22)

    bd = pose.get('board')
    if bd and board_ang is not None:
        bd = dict(bd, a=board_ang * f)
    if bd and bd.get('z', 'under') == 'under':
        board(c, ox + bd['x'] * f, oy + bd['y'], bd['a'] * f, pal, bd.get('len', 11))

    strokes = []     # (p0, p1, colour, thickness)
    blobs = []       # (x, y, size, colour)

    for a in pose.get('arms_back', []):
        strokes += [(P(a[0]), P(a[1]), pal['skin_sh'], 3), (P(a[1]), P(a[2]), pal['skin_sh'], 3)]
        blobs.append((P(a[2]), 3, pal['skin_sh']))
    for l in pose.get('legs_back', []):
        strokes += [(P(l[0]), P(l[1]), pal['pants_sh'], 4), (P(l[1]), P(l[2]), pal['pants_sh'], 3)]
        blobs.append((P(l[2]), 3, pal['shoe_sh']))

    strokes.append((P(pose['neck']), P(pose['hip']), pal['shirt'], 6))

    for l in pose.get('legs', []):
        strokes += [(P(l[0]), P(l[1]), pal['pants'], 4), (P(l[1]), P(l[2]), pal['pants'], 3)]
        blobs.append((P(l[2]), 3, pal['shoe']))
    for a in pose.get('arms', []):
        strokes += [(P(a[0]), P(a[1]), pal['skin'], 3), (P(a[1]), P(a[2]), pal['skin'], 3)]
        blobs.append((P(a[2]), 3, pal['skin']))

    # pass 1 -- ink
    for p0, p1, _, t in strokes:
        c.line(p0, p1, OUT, t + 2)
    for p, s, _ in blobs:
        c.dot(p[0], p[1], s + 2, OUT)
    # pass 2 -- colour
    for p0, p1, col, t in strokes:
        c.line(p0, p1, col, t)
    for p, s, col in blobs:
        c.dot(p[0], p[1], s, col)
    # shirt fold + shoe soles
    nk, hp2 = P(pose['neck']), P(pose['hip'])
    c.line(((nk[0] + hp2[0]) / 2, (nk[1] + hp2[1]) / 2 - 1),
           ((nk[0] + hp2[0]) / 2 + 1.6 * f, (nk[1] + hp2[1]) / 2 + 1.6), pal['shirt_sh'], 2)
    for l in pose.get('legs', []):
        fx, fy = P(l[2])
        c.rect(fx - 1, fy + 1, 3, 1, hx('#ffffff'))

    head(c, P(pose['head']), f, pal['skin'], pal['hair'], pal['style'], pal.get('accent'))

    if bd and bd.get('z') == 'over':
        board(c, ox + bd['x'] * f, oy + bd['y'], bd['a'] * f, pal, bd.get('len', 11))


def pal_of(skin=0, hair=0, shirt=0, pants=0, deck=0, style='short', accent=None):
    def dark(c, k=.72):
        return (round(c[0] * k), round(c[1] * k), round(c[2] * k))
    sk, sh, pt = hx(SKIN[skin]), hx(SHIRT[shirt]), hx(PANTS[pants])
    return dict(skin=sk, skin_sh=dark(sk, .82), hair=hx(HAIR[hair]),
                shirt=sh, shirt_sh=dark(sh), pants=pt, pants_sh=dark(pt),
                shoe=hx('#ffffff'), shoe_sh=hx('#cfcfcf'),
                deck=hx(DECK[deck]), wheel=hx('#ffe14a'),
                style=style, accent=hx(accent) if accent else None)


# ---- poses -----------------------------------------------------------------
POSE_PUSH = dict(
    head=(.5, -21), neck=(0, -17.5), hip=(-.5, -10),
    arms=[((0, -16.5), (4, -14), (7, -15.5))],
    arms_back=[((-.5, -16.5), (-4.5, -13.5), (-7.5, -11))],
    legs=[((-.5, -10), (2.5, -5.5), (3, -1.2))],
    legs_back=[((-1, -10), (-5, -6.5), (-8.5, .6))],
    board=dict(x=1.5, y=0, a=0, len=11))

POSE_OLLIE = dict(
    head=(1.5, -20), neck=(.5, -16.5), hip=(-1.5, -9.5),
    arms=[((.5, -15.5), (5, -16), (8.5, -19))],
    arms_back=[((0, -15.5), (-4.5, -17), (-7, -20))],
    legs=[((-1.5, -9.5), (3, -6.5), (5, -2.5))],
    legs_back=[((-2, -9.5), (-5.5, -7), (-5, -2))],
    board=dict(x=0, y=0, a=-16, len=11))

POSE_FLIP = dict(
    head=(1.5, -21), neck=(.5, -17.5), hip=(-1, -10.5),
    arms=[((.5, -16.5), (5.5, -17.5), (9, -15))],
    arms_back=[((0, -16.5), (-5, -18), (-8.5, -16))],
    legs=[((-1, -10.5), (4, -8), (6.5, -5))],
    legs_back=[((-1.5, -10.5), (-5.5, -8.5), (-6.5, -4.5))],
    board=dict(x=1, y=.5, a=74, len=11, z='over'))

POSE_GRIND = dict(
    head=(3, -17.5), neck=(1.5, -14.5), hip=(-2.5, -8.5),
    arms=[((1.5, -14), (6.5, -13), (10, -15.5))],
    arms_back=[((1, -14), (-4, -15.5), (-8, -14))],
    legs=[((-2.5, -8.5), (2.5, -5.5), (3.5, -1.5))],
    legs_back=[((-3, -8.5), (-5.5, -5), (-4.5, -1.5))],
    board=dict(x=0, y=0, a=0, len=12))

POSE_AIR = dict(
    head=(2.5, -19), neck=(1.5, -15.5), hip=(-2, -9.5),
    arms=[((1.5, -15), (4, -11.5), (4.5, -6.5))],     # grabbing the deck
    arms_back=[((1, -15), (-3.5, -17.5), (-6.5, -21))],
    legs=[((-2, -9.5), (2.5, -7.5), (5.5, -4.5))],
    legs_back=[((-2.5, -9.5), (-5, -6.5), (-3.5, -3))],
    board=dict(x=1, y=-1.5, a=-28, len=11, z='over'))

POSE_CARVE = dict(
    head=(3.5, -18), neck=(2, -15), hip=(-2, -9),
    arms=[((2, -14.5), (7, -13.5), (11, -12))],
    arms_back=[((1.5, -14.5), (-3, -16), (-6.5, -18))],
    legs=[((-2, -9), (3, -6), (4.5, -2))],
    legs_back=[((-2.5, -9), (-5.5, -5.5), (-5, -1.5))],
    board=dict(x=0, y=.5, a=-8, len=12))

POSE_MANUAL = dict(
    head=(1, -21.5), neck=(0, -18), hip=(-1, -10.5),
    arms=[((0, -17), (5, -17.5), (8.5, -20))],
    arms_back=[((-.5, -17), (-5, -17.5), (-8.5, -19.5))],
    legs=[((-1, -10.5), (3.5, -7), (5.5, -3.5))],
    legs_back=[((-1.5, -10.5), (-4.5, -6.5), (-5.5, -2))],
    board=dict(x=0, y=-.5, a=-19, len=11))

POSE_STAND = dict(
    head=(0, -21.5), neck=(0, -18), hip=(0, -10.5),
    arms=[((0, -17), (3.5, -13.5), (6, -10))],
    arms_back=[((-.5, -17), (-3.5, -13), (-4.5, -9))],
    legs=[((0, -10.5), (1.5, -5.5), (2, -.5))],
    legs_back=[((-.5, -10.5), (-2, -5.5), (-2.5, -.5))],
    board=dict(x=7.5, y=-6, a=84, len=12, z='over'))

POSE_SIT = dict(
    head=(0, -17.5), neck=(0, -14), hip=(-.5, -7),
    arms=[((0, -13.5), (3, -10), (4, -6.5))],
    arms_back=[((-.5, -13.5), (-3.5, -10), (-4.5, -6.5))],
    legs=[((-.5, -7), (4, -5.5), (4.5, -.5))],
    legs_back=[((-1, -7), (3, -5), (3.5, -.5))],
    board=None)

POSE_WATCH = dict(
    head=(0, -21.5), neck=(0, -18), hip=(0, -10.5),
    arms=[((0, -17), (3, -14), (3.5, -10))],
    arms_back=[((-.5, -17), (-3, -14), (-3.5, -10))],
    legs=[((0, -10.5), (1.5, -5.5), (2, -.5))],
    legs_back=[((-.5, -10.5), (-2, -5.5), (-2.5, -.5))],
    board=None)

POSE_CHEER = dict(
    head=(0, -21.5), neck=(0, -18), hip=(0, -10.5),
    arms=[((0, -17), (3.5, -20), (5, -24))],
    arms_back=[((-.5, -17), (-4, -20), (-5.5, -24))],
    legs=[((0, -10.5), (2, -5.5), (2.5, -.5))],
    legs_back=[((-.5, -10.5), (-2.5, -5.5), (-3, -.5))],
    board=None)

POSE_FILM = dict(
    head=(1, -16), neck=(.5, -13), hip=(-1, -7.5),
    arms=[((.5, -12.5), (4, -13.5), (6, -15.5))],
    arms_back=[((0, -12.5), (3, -12), (5, -14.5))],
    legs=[((-1, -7.5), (3, -5), (4, -.5))],
    legs_back=[((-1.5, -7.5), (-3.5, -4.5), (-4, -.5))],
    board=None)


# --------------------------------------------------------------------------
# the park
# --------------------------------------------------------------------------
def build(night=False, sky=True):
    P = dict(
        sky=['#5bbdf7', '#7fd3ff', '#a9e2ff', '#cdeeff', '#eaf8ff'],
        sun='#ffe14a', cloud='#ffffff', cloud_sh='#c9e4f5',
        far='#9fb6cf', palm='#2e8b57', palm_d='#1f6b43', trunk='#7a5433',
        wall='#8e887e', wall_d='#766f66', wall_l='#a8a197',
        fence='#9aa3ad',
        ground='#cfc9be', ground_d='#bdb7ac', ground_l='#ded8cd',
    ) if not night else dict(
        sky=['#140826', '#2a0f47', '#45155f', '#6b1f72', '#9c2f6e'],
        sun='#f6f2d6', cloud='#3a1a56', cloud_sh='#2a1140',
        far='#2a1a44', palm='#1d3f4a', palm_d='#142c36', trunk='#3a2a22',
        wall='#5a5663', wall_d='#474350', wall_l='#6d6878',
        fence='#6f6a80',
        ground='#6a6472', ground_d='#575162', ground_l='#7d7688',
    )

    c = Canvas(W, H, hx(P['sky'][0]) if sky else KEY)

    # ---------------- sky ------------------------------------------------
    # (skipped in sky=False builds -- the page animates a live day cycle there)
    bands = [(0, 26), (26, 48), (48, 68), (68, 88), (88, 108)]
    for i, (a, b) in enumerate(bands if sky else []):
        c.rect(0, a, W, b - a, hx(P['sky'][i]))
        # ordered dither on each seam so the gradient reads as 8-bit
        for x in range(0, W, 2):
            c.set(x + (i % 2), b - 1, hx(P['sky'][min(i + 1, 4)]))
            c.set(x + 1 - (i % 2), b - 2, hx(P['sky'][min(i + 1, 4)]))

    if night and sky:
        stars = [(18, 14), (44, 30), (67, 9), (95, 22), (121, 12), (148, 34),
                 (172, 8), (196, 26), (223, 15), (247, 36), (272, 10), (298, 28),
                 (33, 52), (82, 46), (137, 58), (189, 50), (236, 61), (289, 48),
                 (12, 70), (108, 74), (160, 66), (212, 78), (258, 68), (310, 56)]
        for i, (sx, sy) in enumerate(stars):
            col = hx('#ffffff') if i % 3 else hx('#cfe8ff')
            c.set(sx, sy, col)
            if i % 4 == 0:
                c.set(sx - 1, sy, col, .5); c.set(sx + 1, sy, col, .5)
                c.set(sx, sy - 1, col, .5); c.set(sx, sy + 1, col, .5)
        # moon
        c.glow(266, 26, 22, hx('#e9dcff'), .30)
        c.ocircle(266, 26, 11, hx(P['sun']))
        c.fcircle(271, 22, 9, hx(P['sky'][1]))
        for mx, my, mr in ((262, 30, 2), (259, 24, 1), (264, 34, 1)):
            c.fcircle(mx, my, mr, hx('#ded8c0'))
    elif sky:
        # sun with a chunky pixel corona
        c.glow(266, 26, 26, hx('#fff4a8'), .35)
        c.ocircle(266, 26, 12, hx(P['sun']))
        c.fcircle(263, 22, 4, hx('#fff7b8'))
        for a in range(0, 360, 30):
            r = math.radians(a)
            x1, y1 = 266 + math.cos(r) * 15, 26 + math.sin(r) * 15
            x2, y2 = 266 + math.cos(r) * 18, 26 + math.sin(r) * 18
            c.line((x1, y1), (x2, y2), hx('#ffe14a'), 2, .8)

        # pixel clouds
        def cloud(cx, cy, s):
            lumps = [(-9, 0, 4), (-3, -3, 5), (3, -2, 4.5), (8, 1, 3.5), (0, 1, 5)]
            for dx, dy, r in lumps:
                c.fcircle(cx + dx * s, cy + dy * s, r * s, hx(P['cloud_sh']))
            for dx, dy, r in lumps:
                c.fcircle(cx + dx * s, cy + dy * s - 1 * s, r * s, hx(P['cloud']))
        cloud(44, 24, 1.0); cloud(140, 16, .75); cloud(212, 40, .9); cloud(306, 20, .7)
        cloud(96, 52, .6)

    # birds
    if not night and sky:
        for bx_, by_, sc in ((150, 44, 1), (162, 38, 1), (174, 47, 1), (96, 30, 1)):
            c.line((bx_ - 3 * sc, by_), (bx_, by_ - 2 * sc), OUT2, 1)
            c.line((bx_, by_ - 2 * sc), (bx_ + 3 * sc, by_), OUT2, 1)

    # ---------------- distant skyline + palms ----------------------------
    sky_line = 96
    for bx, bw, bh in BUILDINGS:
        c.rect(bx, sky_line - bh, bw, bh, hx(P['far']))
        c.rect(bx, sky_line - bh, bw, 1, OUT2)
        if not night:
            for wy in range(sky_line - bh + 3, sky_line - 2, 4):
                for wx in range(bx + 2, bx + bw - 2, 4):
                    c.rect(wx, wy, 2, 2, hx('#8aa0bb'))
        else:
            for wy in range(sky_line - bh + 3, sky_line - 2, 4):
                for wx in range(bx + 2, bx + bw - 2, 4):
                    if (wx + wy) % 3:
                        c.rect(wx, wy, 2, 2, hx('#ffd98a'), .85)

    def palm(px_, base, h_):
        c.rect(px_ - 1, base - h_, 3, h_, OUT2)
        c.rect(px_ - 1, base - h_, 2, h_, hx(P['trunk']))
        for i in range(base - h_, base, 4):
            c.rect(px_ - 1, i, 3, 1, hx('#5e3f26'))
        top = base - h_
        for dx, dy in ((-10, 2), (-7, -4), (0, -7), (7, -4), (10, 2), (-4, 4), (4, 4)):
            c.line((px_, top), (px_ + dx, top + dy), OUT2, 4)
        for dx, dy in ((-10, 2), (-7, -4), (0, -7), (7, -4), (10, 2), (-4, 4), (4, 4)):
            c.line((px_, top), (px_ + dx, top + dy), hx(P['palm']), 2)
            c.line((px_ + dx * .6, top + dy * .6), (px_ + dx, top + dy), hx(P['palm_d']), 1)
        c.fcircle(px_, top, 2, hx('#c8863a'))

    for px_, h_ in ((88, 34), (112, 26), (196, 30), (176, 22), (310, 28), (18, 24)):
        palm(px_, sky_line + 2, h_)

    # ---------------- graffiti back wall ---------------------------------
    wall_top, wall_bot = 96, 118
    c.rect(0, wall_top, W, wall_bot - wall_top, hx(P['wall']))
    c.rect(0, wall_top, W, 2, hx(P['wall_l']))
    c.rect(0, wall_bot - 3, W, 3, hx(P['wall_d']))
    for y in range(wall_top + 4, wall_bot - 2, 6):
        c.hline(0, W - 1, y, hx(P['wall_d']), .5)
        off = 0 if ((y - wall_top) // 6) % 2 == 0 else 8
        for x in range(off, W, 16):
            c.vline(x, y, y + 5, hx(P['wall_d']), .45)
    # stains / speckle
    for i in range(0, W, 7):
        c.rect(i + (i % 5), wall_bot - 6 + (i % 3), 2, 4, hx(P['wall_d']), .35)

    tagink = OUT
    text(c, 10, wall_top + 4, 'SK8', hx('#ff2fb0'), px=2, ink=tagink)
    text(c, 10, wall_top + 4 + 16, 'SESH', hx('#ffd21f'), px=1, ink=tagink)
    text(c, 118, wall_top + 5, 'SESH', hx('#19c7c7'), px=2, ink=tagink)
    text(c, 232, wall_top + 4, 'LOCALS', hx('#3ddc84'), px=1, ink=tagink)
    text(c, 232, wall_top + 13, 'ONLY', hx('#ff8a1e'), px=1, ink=tagink)
    text(c, 290, wall_top + 5, 'OZ', hx('#ffffff'), px=2, ink=tagink)
    # abstract throwie
    c.fellipse(205, wall_top + 11, 13, 7, hx('#a855f7'))
    c.fellipse(205, wall_top + 10, 11, 5, hx('#ff2fb0'))
    c.line((196, wall_top + 16), (214, wall_top + 6), hx('#ffffff'), 1, .8)

    # ---------------- ground ---------------------------------------------
    c.rect(0, wall_bot, W, H - wall_bot, hx(P['ground']))
    c.rect(0, wall_bot, W, 2, hx(P['ground_d']))
    # perspective joints
    for y in (130, 146, 164):
        c.hline(0, W - 1, y, hx(P['ground_d']), .55)
        c.hline(0, W - 1, y + 1, hx(P['ground_l']), .3)
    for x0, x1 in ((66, 40), (160, 160), (254, 286)):
        c.line((x0, wall_bot), (x1, H), hx(P['ground_d']), 1, .5)
    # speckle + cracks
    for i in range(240):
        x = (i * 97 + 13) % W
        y = wall_bot + 2 + (i * 53 + 7) % (H - wall_bot - 2)
        c.set(x, y, hx(P['ground_d']), .45)
        c.set(x + 1, y, hx(P['ground_l']), .25)
    c.line((20, 172), (34, 160), hx(P['ground_d']), 1, .6)
    c.line((34, 160), (28, 150), hx(P['ground_d']), 1, .5)
    c.line((300, 150), (288, 162), hx(P['ground_d']), 1, .5)
    # skid marks and wax smears from a thousand sessions
    for sx_, sy_, sl in ((128, 160, 18), (196, 150, 14), (236, 166, 20), (84, 136, 12)):
        c.rect(sx_, sy_, sl, 1, hx('#5b564f'), .28)
        c.rect(sx_ + 2, sy_ + 1, sl - 6, 1, hx('#5b564f'), .18)

    ink = OUT

    # ---------------- quarter pipe (left) --------------------------------
    # The transition curve, the deck height and the coping position are the
    # skating surface the rider's path is tuned to -- the detailing below
    # sits behind or beside it and never crosses it.
    qp_x0, qp_x1 = -4, 70          # transition footprint
    qp_base, qp_top = 150, 112

    def face_y(x):
        t = (x - qp_x0) / float(qp_x1 - qp_x0)
        return qp_base - (qp_base - qp_top) * (t ** 2.1)

    # cast shadow pooling on the flat in front of the ramp
    c.rect(0, qp_base + 4, qp_x1 + 30, 3, hx('#9d968b'), .55)
    c.rect(0, qp_base + 7, qp_x1 + 24, 2, hx('#aba49a'), .35)

    # --- riding surface: horizontal plywood panels, lighter toward the lip
    PLY = ('#b9833c', '#c8924a', '#d9a257', '#e9b86b', '#f3c87e')
    for x in range(max(0, qp_x0), qp_x1 + 1):
        y = int(face_y(x))
        for yy in range(y, qp_base):
            band = ((yy - qp_top) // 7) % len(PLY)
            c.set(x, yy, hx(PLY[band]))
        # panel seam lines run across the face
        for sy in range(qp_top, qp_base, 7):
            if sy > y:
                c.set(x, sy, hx('#8d6029'), .55)
        c.vline(x, y, y + 1, ink)                    # crisp surface edge
        c.set(x, y + 2, hx('#ffe3ab'), .5)           # worn sheen below it

    # vertical ply joints, stopping short of the surface so it stays clean
    for jx in range(6, qp_x1, 13):
        jy = int(face_y(jx)) + 3
        c.vline(jx, jy, qp_base - 1, hx('#8d6029'), .6)
        for by in range(jy + 3, qp_base - 2, 9):     # bolt heads down the joint
            c.rect(jx - 1, by, 2, 2, ink)
            c.set(jx - 1, by, hx('#cfd6dd'))

    # scratches and chipped paint along the riding line
    for sx, sl in ((14, 9), (30, 13), (46, 8), (56, 11)):
        sy = int(face_y(sx)) + 4
        c.rect(sx, sy, sl, 1, hx('#8d6029'), .45)
    for cx_ in range(2, qp_x1, 9):
        cy_ = int(face_y(cx_)) + 2
        c.set(cx_, cy_, hx('#a8762f'), .7)

    # --- skirt and footing under the ramp
    c.rect(0, qp_base, qp_x1 + 1, 5, hx('#8a5f28'))
    c.rect(0, qp_base, qp_x1 + 1, 1, ink)
    c.rect(0, qp_base + 4, qp_x1 + 1, 1, ink)
    for sx in range(4, qp_x1, 12):                   # darker supports beneath
        c.rect(sx, qp_base + 1, 3, 3, hx('#6b4820'))

    # --- deck: top surface, fascia, legs
    c.rect(qp_x1 - 1, qp_top, 32, 4, hx('#d9a257'))
    c.rect(qp_x1 - 1, qp_top, 32, 1, ink)
    c.rect(qp_x1 - 1, qp_top + 3, 32, 1, hx('#8d6029'))
    c.rect(qp_x1 - 1, qp_top + 4, 32, 22, hx('#9c6c2b'))
    for x in range(qp_x1 + 2, qp_x1 + 31, 7):        # fascia planks
        c.vline(x, qp_top + 5, qp_top + 24, hx('#7d5522'), .7)
        c.vline(x + 1, qp_top + 5, qp_top + 24, hx('#b07e34'), .25)
    for ly in (qp_top + 9, qp_top + 18):             # steel brackets
        c.rect(qp_x1 + 1, ly, 29, 2, hx('#6e767f'))
        c.rect(qp_x1 + 1, ly, 29, 1, hx('#99a2ab'))
        for bx in (qp_x1 + 3, qp_x1 + 14, qp_x1 + 27):
            c.rect(bx, ly, 2, 2, ink)
            c.set(bx, ly, hx('#cfd6dd'))
    c.rect(qp_x1 - 1, qp_top + 25, 32, 2, ink)
    c.rect(qp_x1 + 2, qp_top + 27, 4, 4, hx('#5d3f1c'))   # legs
    c.rect(qp_x1 + 24, qp_top + 27, 4, 4, hx('#5d3f1c'))

    # --- steel coping along the lip
    c.rect(qp_x1 - 3, qp_top - 1, 6, 3, ink)
    c.rect(qp_x1 - 2, qp_top - 1, 4, 2, hx('#b9c2cb'))
    c.rect(qp_x1 - 2, qp_top - 1, 4, 1, hx('#e8eef4'))
    c.set(qp_x1 - 2, qp_top, hx('#7b848d'))

    # --- deck guard rail
    for rx in (qp_x1 + 6, qp_x1 + 26):
        c.rect(rx, qp_top - 9, 2, 9, ink)
        c.rect(rx, qp_top - 9, 1, 9, hx('#6e767f'))
    c.rect(qp_x1 + 6, qp_top - 10, 22, 2, ink)
    c.rect(qp_x1 + 6, qp_top - 10, 22, 1, hx('#ffd21f'))

    # --- stickers slapped on the fascia, clear of the riding surface
    c.fellipse(30, 147, 5, 3, hx('#ff2fb0'))         # old slap, flat on the face
    c.fellipse(30, 146, 4, 2, hx('#ffffff'))
    c.rect(qp_x1 + 4, qp_top + 6, 7, 5, ink)         # square sticker
    c.rect(qp_x1 + 5, qp_top + 7, 5, 3, hx('#19c7c7'))
    c.rect(qp_x1 + 6, qp_top + 8, 3, 1, hx('#ffffff'))
    c.fellipse(qp_x1 + 19, qp_top + 8, 5, 3, ink)    # oval sticker
    c.fellipse(qp_x1 + 19, qp_top + 8, 4, 2, hx('#ffd21f'))
    c.rect(qp_x1 + 11, qp_top + 20, 6, 4, ink)       # little tag
    c.rect(qp_x1 + 12, qp_top + 21, 4, 2, hx('#3ddc84'))

    # ---------------- funbox + ledge (centre back) ------------------------
    fb_x, fb_y, fb_w = 138, 122, 64
    c.rect(fb_x, fb_y, fb_w, 10, hx('#b9b3a8'))
    c.rect(fb_x, fb_y, fb_w, 2, hx('#ded8cd'))
    c.rect(fb_x, fb_y, fb_w, 1, ink)
    c.rect(fb_x, fb_y + 9, fb_w, 1, ink)
    # banked ends
    for i in range(12):
        c.rect(fb_x - 12 + i, fb_y + i * .8, 2, 10 - i * .8, hx('#c6c0b5'))
        c.rect(fb_x + fb_w + 10 - i, fb_y + i * .8, 2, 10 - i * .8, hx('#c6c0b5'))
    c.line((fb_x - 12, fb_y + 10), (fb_x, fb_y), ink, 1)
    c.line((fb_x + fb_w, fb_y), (fb_x + fb_w + 12, fb_y + 10), ink, 1)
    # ledge coping edge
    c.rect(fb_x, fb_y + 1, fb_w, 2, hx('#ffd21f'))
    c.rect(fb_x, fb_y + 1, fb_w, 1, ink)
    # rail across the box
    c.rect(fb_x + 6, fb_y - 9, 2, 9, ink)
    c.rect(fb_x + fb_w - 8, fb_y - 9, 2, 9, ink)
    c.rect(fb_x + 4, fb_y - 11, fb_w - 8, 3, ink)
    c.rect(fb_x + 5, fb_y - 11, fb_w - 10, 2, hx('#ff2fb0'))
    c.rect(fb_x + 5, fb_y - 11, fb_w - 10, 1, hx('#ff8ad0'))

    # ---------------- stairs + handrail (right) ---------------------------
    # Tread positions, the top platform and the handrail line are what the
    # rail skater's climb and grind are tuned to -- none of it moves. The
    # detailing lives on the risers, the side and the floor.
    st_x, st_y = 300, 122          # top of the set, descending to the left
    RAIL_A, RAIL_B = (st_x - 56, st_y + 34), (st_x - 4, st_y - 6)
    RAIL_ANG = math.degrees(math.atan2(RAIL_B[1] - RAIL_A[1], RAIL_B[0] - RAIL_A[0]))
    steps = 5

    # shadow pooling at the foot of the set
    c.rect(st_x - 62, st_y + 36, 40, 3, hx('#9d968b'), .5)
    c.rect(st_x - 58, st_y + 39, 32, 2, hx('#aba49a'), .3)

    for i in range(steps):
        sx = st_x - (i + 1) * 11
        sy = st_y + i * 7
        c.rect(sx, sy, W - sx, 7, hx('#aba59a'))
        c.rect(sx, sy, W - sx, 2, hx('#ded8cd'))      # lit tread
        c.rect(sx, sy, W - sx, 1, ink)
        c.vline(sx, sy, sy + 6, ink)                  # nose
        c.rect(sx + 1, sy + 2, W - sx - 1, 5, hx('#938d84'), .45)   # riser
        c.rect(sx, sy + 6, W - sx, 1, hx('#6d675f'))  # dark edge beneath
        # chipped nose + worn patches where everyone lands
        c.rect(sx + 1, sy, 3, 1, hx('#f0eade'))
        c.rect(sx + 5 + (i * 3) % 7, sy + 1, 4, 1, hx('#8d877e'), .5)
        for k in range(2):                            # speckle on the riser
            c.set(sx + 4 + (i * 5 + k * 9) % 18, sy + 3 + k, hx('#7d776f'), .6)
        # hairline cracks running down a couple of risers
        if i in (1, 3):
            cx_ = sx + 9 + i
            c.set(cx_, sy + 2, hx('#6d675f'))
            c.set(cx_ + 1, sy + 3, hx('#6d675f'))
            c.set(cx_ + 1, sy + 4, hx('#6d675f'))

    # top platform
    c.rect(st_x - 11, st_y - 7, W - st_x + 11, 7, hx('#c6c0b5'))
    c.rect(st_x - 11, st_y - 7, W - st_x + 11, 1, ink)
    c.rect(st_x - 11, st_y - 6, W - st_x + 11, 1, hx('#e6e0d5'))

    # --- the stringer wall down the side of the set, where tags go --------
    for i in range(steps):
        sx = st_x - (i + 1) * 11
        sy = st_y + i * 7
        c.rect(sx - 4, sy + 2, 4, (steps - i) * 7, hx('#9a948a'))
        c.rect(sx - 4, sy + 2, 1, (steps - i) * 7, ink)
    # graffiti tags and skate stickers along that wall
    c.rect(st_x - 30, st_y + 16, 7, 4, ink)
    c.rect(st_x - 29, st_y + 17, 5, 2, hx('#ff2fb0'))
    c.fellipse(st_x - 43, st_y + 25, 4, 3, ink)
    c.fellipse(st_x - 43, st_y + 25, 3, 2, hx('#19c7c7'))
    c.rect(st_x - 19, st_y + 9, 5, 3, hx('#3ddc84'))
    c.rect(st_x - 19, st_y + 9, 5, 1, ink)
    for tx, ty in ((st_x - 52, st_y + 30), (st_x - 36, st_y + 21)):
        c.rect(tx, ty, 6, 1, hx('#ffd21f'), .8)
        c.rect(tx + 1, ty + 1, 4, 1, hx('#ffd21f'), .5)

    # --- debris scattered at the base --------------------------------------
    for dx, dy, dw in ((st_x - 60, st_y + 37, 2), (st_x - 54, st_y + 39, 1),
                       (st_x - 47, st_y + 38, 2), (st_x - 66, st_y + 38, 1)):
        c.rect(dx, dy, dw, 1, hx('#8d877e'))
    c.rect(st_x - 57, st_y + 36, 3, 1, hx('#ff8a1e'))     # a lost sticker

    # --- handrail bolted along the noses of the steps ----------------------
    for i in range(4):
        rx = st_x - 50 + i * 15
        ry = st_y + 36 - i * 10.5
        c.rect(rx, ry - 13, 3, 13, ink)
        c.rect(rx, ry - 13, 2, 13, hx('#b9b3a8'))
        c.rect(rx, ry - 13, 1, 13, hx('#e2dcd2'))
        c.rect(rx - 1, ry - 1, 5, 2, ink)                 # base plate
        c.rect(rx - 1, ry - 1, 5, 1, hx('#8f97a3'))
    c.line(RAIL_A, RAIL_B, ink, 5)
    c.line(RAIL_A, RAIL_B, hx('#ffd21f'), 3)
    c.line((RAIL_A[0], RAIL_A[1] - 1), (RAIL_B[0], RAIL_B[1] - 1), hx('#fff3a8'), 1, .8)

    # --- a short grindable flat bar set beside the stairs ------------------
    gb_y = st_y + 34
    for bx in (st_x - 78, st_x - 64):
        c.rect(bx, gb_y + 1, 2, 7, ink)
        c.rect(bx, gb_y + 1, 1, 7, hx('#6e767f'))
        c.rect(bx - 1, gb_y + 8, 4, 1, hx('#6d675f'))     # foot plate
    c.rect(st_x - 82, gb_y - 2, 24, 3, ink)
    c.rect(st_x - 81, gb_y - 1, 22, 2, hx('#b9c2cb'))
    c.rect(st_x - 81, gb_y - 1, 22, 1, hx('#e8eef4'))     # polished top
    c.rect(st_x - 74, gb_y - 1, 7, 1, hx('#9aa3ad'))      # waxed patch
    c.fellipse(st_x - 70, gb_y + 10, 13, 2, hx('#000000'), .18)

    # (the bowl used to sit here; removed -- it read as a hole in the floor)

    # ---------------- flat rail (front right) -----------------------------
    fr_y = 170
    c.rect(150, fr_y + 2, 3, 10, ink)
    c.rect(228, fr_y + 2, 3, 10, ink)
    c.rect(140, fr_y - 2, 100, 4, ink)
    c.rect(141, fr_y - 1, 98, 2, hx('#ff2fb0'))
    c.rect(141, fr_y - 1, 98, 1, hx('#ff8ad0'))
    c.fellipse(190, fr_y + 13, 50, 3, hx('#000000'), .18)

    # ---------------- props ------------------------------------------------
    def cone(x, y, s=1.0):
        c.line((x, y - 10 * s), (x - 5 * s, y), ink, 4)
        c.line((x, y - 10 * s), (x + 5 * s, y), ink, 4)
        for i in range(int(10 * s)):
            t = i / (10 * s)
            w = 1 + 9 * s * t
            c.rect(x - w / 2, y - 10 * s + i, w, 1, hx('#ff8a1e'))
        c.rect(x - 7 * s, y, 14 * s, 2, ink)
        c.rect(x - 6.4 * s, y, 12.8 * s, 1.4, hx('#ff8a1e'))
        c.rect(x - 3.4 * s, y - 5 * s, 6.8 * s, 2, hx('#ffffff'))

    # cones removed: half-hidden by the control bar they read as small figures

    # trash can
    tc_x, tc_y = 104, 134
    c.rect(tc_x - 6, tc_y - 14, 12, 16, ink)
    c.rect(tc_x - 5, tc_y - 13, 10, 14, hx('#3b7f5a'))
    for i in range(-4, 5, 3):
        c.vline(tc_x + i, tc_y - 12, tc_y, hx('#2c6346'))
    c.rect(tc_x - 7, tc_y - 16, 14, 3, ink)
    c.rect(tc_x - 6, tc_y - 16, 12, 2, hx('#4a9c6e'))

    # boombox
    bb_x, bb_y = 132, 140
    c.rect(bb_x - 11, bb_y - 9, 22, 11, ink)
    c.rect(bb_x - 10, bb_y - 8, 20, 9, hx('#2b2840'))
    c.ocircle(bb_x - 5, bb_y - 3, 2.6, hx('#6b6880'))
    c.ocircle(bb_x + 5, bb_y - 3, 2.6, hx('#6b6880'))
    c.rect(bb_x - 2, bb_y - 7, 4, 3, hx('#19c7c7'))
    c.line((bb_x - 7, bb_y - 9), (bb_x + 7, bb_y - 9), ink, 2)
    for i, (nx_, ny_) in enumerate(((bb_x - 17, bb_y - 15), (bb_x + 16, bb_y - 18))):
        c.rect(nx_, ny_, 3, 3, hx('#ffffff'), .85)
        c.rect(nx_ + 2, ny_ - 4, 1, 5, hx('#ffffff'), .85)

    # backpack + soda can
    c.rect(146, 150, 10, 8, ink)
    c.rect(147, 151, 8, 6, hx('#6b4a9e'))
    c.rect(149, 149, 4, 2, hx('#a855f7'))
    c.rect(162, 154, 3, 5, ink)
    c.rect(162, 154, 2, 4, hx('#ff2fb0'))

    # spare deck leaning on the wall
    c.line((124, 118), (130, 100), ink, 5)
    c.line((124, 118), (130, 100), hx('#19c7c7'), 3)
    c.ocircle(124, 119, 1.3, hx('#ffe14a'))

    # pigeon (the dog is gone -- it read as a small figure near the floor)
    c.rect(206, 116, 4, 3, ink); c.rect(206, 116, 3, 2, hx('#8e97a3'))
    c.rect(209, 115, 2, 1, ink)

    # ---------------- graffiti pass ---------------------------------------
    # Painted over the finished structures so it sits ON them. Everything
    # here is original: invented words, simple faces, stars, arrows and
    # abstract throwies. Kept to the wall, ramp fascia, stair side, the
    # funbox and the distant blocks -- never across a riding surface.
    NEON = ['#ff2fb0', '#19c7c7', '#3ddc84', '#ffd21f', '#ff8a1e',
            '#a855f7', '#6ad3ff', '#ffffff']

    def worn(x, y, w, h, n=3):
        """scuff a few pixels back toward the surface so paint looks aged"""
        for i in range(n):
            c.set(x + (i * 7 + 3) % max(1, w), y + (i * 5 + 1) % max(1, h),
                  hx(P['wall_d']), .55)

    def drips(x, y, cols, col):
        for i, dx in enumerate(cols):
            c.rect(x + dx, y, 1, 2 + (i % 3), hx(col), .8)

    def star(x, y, col):
        for ry, row in enumerate(('..#..', '.###.', '#####', '.#.#.', '#...#')):
            for rx, v in enumerate(row):
                if v == '#':
                    c.set(x + rx, y + ry, hx(col), .9)

    def arrow(x, y, col, flip=False):
        f = -1 if flip else 1
        c.rect(x, y + 2, 9, 2, hx(col), .9)
        for i in range(3):
            c.rect(x + (8 - i) * f if not flip else x + i, y + i, 1, 6 - i * 2, hx(col), .9)

    def face(x, y, col):
        """a scrawled cartoon head -- outline, two eyes, a crooked grin"""
        for ry, row in enumerate(('.###.', '#...#', '#.#.#', '#...#',
                                  '#.#.#', '.###.')):
            for rx, v in enumerate(row):
                if v == '#':
                    c.set(x + rx, y + ry, hx(col), .92)
        c.set(x + 1, y + 2, hx('#ffffff'))
        c.set(x + 3, y + 2, hx('#ffffff'))

    def throwie(x, y, w, h, fill, edge):
        c.fellipse(x, y, w, h, hx(edge), .9)
        c.fellipse(x, y - 1, w - 2, h - 2, hx(fill), .9)
        c.line((x - w + 2, y + 1), (x + w - 3, y - 2), hx('#ffffff'), 1, .35)

    def deck_tag(x, y, col):
        """a little board scrawl: deck, two wheels"""
        c.rect(x, y, 9, 2, hx(col), .9)
        c.set(x + 1, y + 2, hx(col)); c.set(x + 7, y + 2, hx(col))

    # --- back wall, in the gaps between the existing pieces ---------------
    text(c, 48, 99, 'KRUZ', hx(NEON[1]), px=1, ink=ink); worn(48, 99, 24, 7)
    drips(48, 106, (2, 9, 17), NEON[1])
    star(78, 99, NEON[3])
    face(90, 99, NEON[0])
    text(c, 48, 109, 'DUSK', hx(NEON[5]), px=1, ink=ink); worn(48, 109, 24, 7)
    arrow(76, 110, NEON[4])
    deck_tag(90, 111, NEON[2])

    text(c, 184, 99, 'HAZE', hx(NEON[2]), px=1, ink=ink); worn(184, 99, 24, 7)
    star(212, 100, NEON[6])
    text(c, 184, 109, 'ZONK', hx(NEON[3]), px=1, ink=ink); worn(184, 109, 24, 7)
    face(212, 108, NEON[2])
    throwie(222, 104, 7, 4, NEON[5], NEON[0])

    # LOCALS/ONLY already sit at 232; this drops into the gap below them
    text(c, 258, 109, 'SKID', hx(NEON[0]), px=1, ink=ink); worn(258, 109, 24, 7)
    arrow(262, 99, NEON[1], flip=True)
    star(276, 98, NEON[7])

    # --- ramp fascia (beside the riding surface, never on it) -------------
    star(74, 131, NEON[6])
    deck_tag(84, 133, NEON[0])
    drips(74, 136, (0, 5), NEON[6])

    # --- stair stringer wall ----------------------------------------------
    star(st_x - 47, st_y + 29, NEON[3])
    throwie(st_x - 26, st_y + 27, 5, 3, NEON[1], NEON[7])
    deck_tag(st_x - 40, st_y + 14, NEON[2])

    # --- funbox side -------------------------------------------------------
    text(c, 146, 124, 'SODA', hx(NEON[6]), px=1, ink=ink); worn(146, 124, 24, 7)
    star(176, 125, NEON[0])

    # --- distant blocks: just specks of colour at this range ---------------
    for bx, by, col in ((12, 82, NEON[0]), (46, 74, NEON[2]), (58, 86, NEON[3]),
                        (228, 80, NEON[1]), (260, 72, NEON[5]), (300, 84, NEON[4])):
        c.rect(bx, by, 3, 2, hx(col), .8)
        c.set(bx + 1, by + 2, hx(col), .5)

    # floodlight towers rising behind the fence
    for lx in (34, 286):
        c.rect(lx - 1, 34, 3, 84, ink)
        c.rect(lx - 1, 34, 2, 84, hx('#4d4858') if night else hx('#8e8a93'))
        for ry in range(44, 112, 10):          # lattice cross-bracing
            c.line((lx - 1, ry), (lx + 2, ry + 10), hx('#6f6a7a'), 1, .7)
            c.line((lx + 2, ry), (lx - 1, ry + 10), hx('#6f6a7a'), 1, .7)
        c.rect(lx - 9, 26, 19, 9, ink)
        for i in range(3):
            c.rect(lx - 7 + i * 6, 28, 5, 5, hx('#fff3c8') if night else hx('#cfd6dd'))

    # ---------------- chain-link fence (in front of the wall top) ----------
    fz_top, fz_bot = 74, 96
    # solid, not alpha-blended: the sky behind the fence is transparent now,
    # and a blended stroke would simply not land on it
    mesh = hx('#8d96a3') if not night else hx('#5f5a70')
    for x in range(-24, W + 24, 6):
        c.line((x, fz_top), (x + 22, fz_bot), mesh, 1)
        c.line((x + 22, fz_top), (x, fz_bot), mesh, 1)
    c.rect(0, fz_top - 2, W, 2, ink)
    c.rect(0, fz_top - 2, W, 1, hx(P['fence']))
    c.rect(0, fz_bot - 1, W, 2, ink)
    for x in range(10, W, 54):
        c.rect(x, fz_top - 4, 3, fz_bot - fz_top + 4, ink)
        c.rect(x, fz_top - 4, 2, fz_bot - fz_top + 4, hx(P['fence']))
    # banner zip-tied to the fence
    c.rect(118, 76, 58, 14, ink)
    c.rect(119, 77, 56, 12, hx('#ff2fb0'))
    text(c, 124, 79, 'SK8 SESH', hx('#ffffff'), px=1, ink=None)

    # Skaters are no longer drawn into the park: they are animated sprite
    # sheets (tools/gen_anim.py) layered over this backdrop by the page.

    # ---------------- night lighting pass ---------------------------------
    if night:
        c.tint(hx('#190a2e'), .38)
        for lx in (34, 286):
            c.glow(lx, 31, 40, hx('#ffd98a'), .55)
            for i in range(3):
                c.rect(lx - 7 + i * 6, 28, 5, 5, hx('#fffbe8'))
            # light spilling down the tower and pooling on the concrete
            c.fellipse(lx, 150, 46, 22, hx('#ffd98a'), .10)
            c.fellipse(lx, 152, 30, 13, hx('#ffe9b8'), .10)
        # neon on the back wall
        for i in range(2):
            c.glow(30, 108, 22, hx('#ff2fb0'), .28)
            c.glow(150, 106, 22, hx('#19c7c7'), .24)
            c.glow(300, 104, 18, hx('#ffffff'), .18)
        text(c, 10, 100, 'SK8', hx('#ff8ad0'), px=2, ink=None)
        text(c, 118, 101, 'SESH', hx('#8ef4f4'), px=2, ink=None)
        c.glow(50, 168, 16, hx('#19c7c7'), .3)
        c.glow(256, 157, 26, hx('#ff2fb0'), .22)
        c.glow(92, 158, 30, hx('#2d6cdf'), .2)

    # vignette so the UI reads on top
    for y in range(H):
        for x in range(W):
            d = max(abs(x - W / 2) / (W / 2), abs(y - H / 2) / (H / 2))
            if d > .72:
                c.set(x, y, hx('#0b0714'), (d - .72) * (.9 if night else .55))
    return c


def build_citylights():
    """Just the lit windows, on a transparent canvas the same size as the park
    so it can be layered over it at the same `cover` sizing. A CSS drop-shadow
    supplies the bloom, which keeps the windows themselves crisply pixelated."""
    c = Canvas(W, H, KEY)
    n = 0
    for bx, bw, bh in BUILDINGS:
        for wy in range(SKY_LINE - bh + 3, SKY_LINE - 2, 4):
            for wx in range(bx + 2, bx + bw - 2, 4):
                n += 1
                if n % 7 == 0:                 # a few windows stay dark
                    continue
                warm = ('#ffe9a8', '#ffd98a', '#fff3c8')[n % 3]
                c.rect(wx, wy, 2, 2, hx(warm))
    return c


# --------------------------------------------------------------------------
# emit
# --------------------------------------------------------------------------
def quantize(c, step=10):
    """Snap to a coarse palette. Keeps the file small AND makes the alpha
    blends (glows, vignette, shadows) band like real 8-bit colour ramps."""
    lut = {}
    for y in range(c.h):
        row = c.px[y]
        for x in range(c.w):
            o = row[x]
            if o == KEY:
                continue
            q = lut.get(o)
            if q is None:
                q = tuple(min(255, int(round(v / step)) * step) for v in o)
                lut[o] = q
            row[x] = q


def to_svg(c):
    used = [[False] * c.w for _ in range(c.h)]
    by_colour = {}
    for y in range(c.h):
        for x in range(c.w):
            if used[y][x]:
                continue
            col = c.px[y][x]
            w = 1
            while x + w < c.w and not used[y][x + w] and c.px[y][x + w] == col:
                w += 1
            h = 1
            while y + h < c.h:
                ok = all((not used[y + h][x + i]) and c.px[y + h][x + i] == col for i in range(w))
                if not ok:
                    break
                h += 1
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    used[yy][xx] = True
            by_colour.setdefault(col, []).append((x, y, w, h))

    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
             'width="%d" height="%d" shape-rendering="crispEdges" '
             'preserveAspectRatio="xMidYMax slice">' % (W * SCALE, H * SCALE, W * SCALE, H * SCALE)]
    for col, rs in sorted(by_colour.items(), key=lambda kv: -len(kv[1])):
        if col == KEY:          # transparent: emit nothing
            continue
        parts.append('<g fill="#%02x%02x%02x">' % col)
        for (x, y, w, h) in rs:
            parts.append('<rect x="%d" y="%d" width="%d" height="%d"/>'
                         % (x * SCALE, y * SCALE, w * SCALE, h * SCALE))
        parts.append('</g>')
    parts.append('</svg>')
    return ''.join(parts)


def to_png(c, path, zoom=3):
    from PIL import Image
    im = Image.new('RGB', (c.w, c.h))
    im.putdata([c.px[y][x] for y in range(c.h) for x in range(c.w)])
    im.resize((c.w * zoom, c.h * zoom), Image.NEAREST).save(path)


if __name__ == '__main__':
    want_png = '--png' in sys.argv
    for name, night in (('scene-day', False), ('scene-night', True)):
        c = build(night)
        quantize(c)
        svg = to_svg(c)
        with open(os.path.join(ROOT, name + '.svg'), 'w') as f:
            f.write(svg)
        print('%s.svg  %d KB' % (name, len(svg) // 1024))
        if want_png:
            to_png(c, os.path.join(ROOT, 'tools', name + '.png'))
