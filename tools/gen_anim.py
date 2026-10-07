#!/usr/bin/env python3
"""
SK8 SESH -- animated skater sprite sheets.

Three skaters, each a looping pixel-art cycle rendered frame by frame:

    skater-street.png   rolls, crouches, pops an ollie, flips the deck, lands
    skater-bowl.png     pumps the bowl, airs out over the coping, drops back in
    skater-rail.png     rolls in, ollies onto the handrail, 50-50s, pops off

Poses are joint dictionaries; frames are produced by interpolating between
keyframe poses, so motion is smooth while the art stays on the pixel grid.
Each sheet is one horizontal strip of FRAMES cells, driven in CSS by
`steps(FRAMES)` -- the same way an NES sprite cycles.

    python3 tools/gen_anim.py            # writes the three sheets
    python3 tools/gen_anim.py --contact  # also writes a contact sheet to eyeball
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_scene import Canvas, hx, OUT, SKIN, HAIR, SHIRT, PANTS, DECK, pal_of

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FRAMES = 48            # cells per loop -- 12fps at a 4s cycle
SCALE = 5              # art pixel -> screen pixel, matches the park SVG
BOX_W, BOX_H = 46, 40  # sprite cell, in art pixels -- generous margins matter
ORIGIN = (23, 32)      # where the board centre sits inside the cell
FIG = 0.58             # figure scale
KEY = (1, 2, 3)        # transparent sentinel


# --------------------------------------------------------------------------
# poses  (local coords: +x forward, -y up, origin at the board centre)
# --------------------------------------------------------------------------
def P(head, neck, hip, arm, arm_b, leg, leg_b, ba=0, bx=0, by=0, bz='under', sq=1.0):
    """sq: squash/stretch -- <1 compresses the figure toward the board,
    >1 stretches it. Applied about the contact point at draw time."""
    return dict(head=head, neck=neck, hip=hip, arms=[arm], arms_back=[arm_b],
                legs=[leg], legs_back=[leg_b], sq=sq,
                board=dict(x=bx, y=by, a=ba, len=11, z=bz))


ROLL = P((.5, -21), (0, -17.5), (-.5, -10),
         ((0, -16.5), (4, -14), (7, -13)),
         ((-.5, -16.5), (-4, -14), (-7, -12.5)),
         ((-.5, -10), (3, -6), (4, -1.5)),
         ((-1, -10), (-4, -6), (-5, -1.5)))

ROLL2 = P((.5, -20.5), (0, -17), (-.5, -9.8),
          ((0, -16), (4.3, -13.4), (7.4, -12.6)),
          ((-.5, -16), (-4.3, -13.4), (-7.3, -12)),
          ((-.5, -9.8), (3.2, -5.8), (4, -1.5)),
          ((-1, -9.8), (-4.2, -5.8), (-5, -1.5)))

CROUCH = P((1, -17), (.5, -14), (-1, -8.5),
           ((.5, -13.5), (5, -12), (8, -13)),
           ((0, -13.5), (-4, -12.5), (-7, -11)),
           ((-1, -8.5), (3.5, -5.5), (4, -1.5)),
           ((-1.5, -8.5), (-4.5, -5.5), (-5, -1.5)), sq=0.88)

POP = P((1.5, -19), (1, -16), (-1, -9.5),
        ((1, -15.5), (5.5, -16), (9, -18)),
        ((.5, -15.5), (-4, -16), (-7, -18)),
        ((-1, -9.5), (3, -6.5), (5, -3.5)),
        ((-1.5, -9.5), (-4, -5.5), (-5.5, -.5)), ba=-24, sq=1.10)

AIR = P((1.5, -20), (.5, -16.5), (-1.5, -9.5),
        ((.5, -15.5), (5, -16), (8.5, -19)),
        ((0, -15.5), (-4.5, -17), (-7, -20)),
        ((-1.5, -9.5), (3, -7), (5, -3)),
        ((-2, -9.5), (-5, -7), (-5, -3)), ba=-6, by=.5)

LAND = P((1, -17.5), (.5, -14.5), (-1, -9),
         ((.5, -14), (5, -12.5), (8, -13.5)),
         ((0, -14), (-4.2, -13), (-7.2, -11.5)),
         ((-1, -9), (3.4, -6), (4, -1.5)),
         ((-1.5, -9), (-4.4, -6), (-5, -1.5)), sq=0.84)

# bowl: compressed pump, extended rise, grabbed air over the coping
PUMP = P((2.5, -16.5), (1.5, -13.5), (-1.5, -8),
         ((1.5, -13), (6, -12), (9.5, -11)),
         ((1, -13), (-3, -14), (-6, -15)),
         ((-1.5, -8), (3, -5.5), (4.5, -1.5)),
         ((-2, -8), (-4.5, -5), (-4.5, -1.5)), ba=-14)

RISE = P((2, -20), (1, -16.5), (-1.5, -9.5),
         ((1, -16), (6, -15), (10, -16)),
         ((.5, -16), (-3.5, -16.5), (-6.5, -18)),
         ((-1.5, -9.5), (3.2, -6.5), (4.8, -2.5)),
         ((-2, -9.5), (-4.8, -6), (-5, -2)), ba=-22)

GRAB = P((2.5, -19), (1.5, -15.5), (-2, -9.5),
         ((1.5, -15), (4, -11.5), (4.5, -6.5)),      # hand on the deck
         ((1, -15), (-3.5, -17.5), (-6.5, -21)),
         ((-2, -9.5), (2.5, -7.5), (5.5, -4.5)),
         ((-2.5, -9.5), (-5, -6.5), (-3.5, -3)), ba=-30, by=-1.5, bz='over')

# rail: locked 50-50, arms out for balance
GRIND = P((3, -17.5), (1.5, -14.5), (-2.5, -8.5),
          ((1.5, -14), (6.5, -13), (10, -15.5)),
          ((1, -14), (-4, -15.5), (-8, -14)),
          ((-2.5, -8.5), (2.5, -5.5), (3.5, -1.5)),
          ((-3, -8.5), (-5.5, -5), (-4.5, -1.5)))

GRIND2 = P((3, -17), (1.5, -14), (-2.5, -8.2),
           ((1.5, -13.5), (6.8, -13.6), (10.2, -16.2)),
           ((1, -13.5), (-4.2, -15), (-8.2, -13.2)),
           ((-2.5, -8.2), (2.6, -5.3), (3.5, -1.5)),
           ((-3, -8.2), (-5.6, -4.8), (-4.5, -1.5)))


STAND_A = P((0, -21), (0, -17.5), (0, -10),
            ((0, -17), (3, -13.5), (4.5, -10)),
            ((-.5, -17), (-3, -13.5), (-4.5, -10)),
            ((0, -10), (2, -5.5), (3, -1.5)),
            ((-.5, -10), (-2.5, -5.5), (-3.5, -1.5)))

STAND_B = P((0, -20.2), (0, -16.8), (0, -9.6),
            ((0, -16.3), (3.2, -13), (4.6, -9.4)),
            ((-.5, -16.3), (-3.2, -13), (-4.6, -9.4)),
            ((0, -9.6), (2.2, -5.3), (3, -1.5)),
            ((-.5, -9.6), (-2.7, -5.3), (-3.5, -1.5)))

TAP = P((0, -20.8), (0, -17.3), (-.3, -9.9),
        ((0, -16.8), (3.5, -14), (5.5, -11.5)),
        ((-.5, -16.8), (-3.5, -14), (-5.5, -11.5)),
        ((-.3, -9.9), (2.5, -6), (4, -3.2)),
        ((-.8, -9.9), (-2.8, -5.5), (-3.5, -1.5)), ba=-18)


# --------------------------------------------------------------------------
# interpolation
# --------------------------------------------------------------------------
def lerp(a, b, t):
    return a + (b - a) * t


def lerp_pt(a, b, t):
    return (lerp(a[0], b[0], t), lerp(a[1], b[1], t))


def lerp_pose(a, b, t):
    out = {}
    for k in ('head', 'neck', 'hip'):
        out[k] = lerp_pt(a[k], b[k], t)
    for k in ('arms', 'arms_back', 'legs', 'legs_back'):
        out[k] = [tuple(lerp_pt(p, q, t) for p, q in zip(a[k][0], b[k][0]))]
    out['sq'] = lerp(a.get('sq', 1.0), b.get('sq', 1.0), t)
    ab, bb = a['board'], b['board']
    out['board'] = dict(x=lerp(ab['x'], bb['x'], t), y=lerp(ab['y'], bb['y'], t),
                        a=lerp(ab['a'], bb['a'], t), len=ab['len'],
                        z=bb['z'] if t > .5 else ab['z'])
    return out


def ease(t, kind='smooth'):
    """Timing and spacing is what separates readable sprite animation from
    floaty interpolation. 'hold' sits on a pose then leaves late; 'snap'
    leaves instantly and decelerates in; 'linear' is constant speed."""
    if kind == 'linear':
        return t
    if kind == 'snap':                 # explosive out, settle in
        return 1 - (1 - t) ** 3
    if kind == 'hold':                 # lingers on the outgoing extreme
        return t ** 2.4
    if kind == 'settle':               # eases hard into the incoming pose
        return 1 - (1 - t) ** 2
    return t * t * (3 - 2 * t)         # smoothstep


def sample(timeline, u):
    """timeline: [(t, pose, board_angle_override|None[, ease_kind])]"""
    for i in range(len(timeline) - 1):
        t0, p0, a0 = timeline[i][0], timeline[i][1], timeline[i][2]
        t1, p1, a1 = timeline[i + 1][0], timeline[i + 1][1], timeline[i + 1][2]
        kind = timeline[i][3] if len(timeline[i]) > 3 else 'smooth'
        if t0 <= u <= t1:
            f = ease((u - t0) / (t1 - t0), kind) if t1 > t0 else 0
            pose = lerp_pose(p0, p1, f)
            if a0 is not None and a1 is not None:
                pose['board'] = dict(pose['board'], a=lerp(a0, a1, f))
            return pose
    return lerp_pose(timeline[-1][1], timeline[-1][1], 0)


# --------------------------------------------------------------------------
# drawing  (scaled-down version of the park rig)
# --------------------------------------------------------------------------
def board(c, cx, cy, ang, pal, length, s):
    a = math.radians(ang)
    dx, dy = math.cos(a), math.sin(a)
    nx, ny = -dy, dx
    hl = length * s / 2.0
    x0, y0 = cx - dx * hl, cy - dy * hl
    x1, y1 = cx + dx * hl, cy + dy * hl
    for f in (-0.26, 0.26):
        wx, wy = cx + dx * length * s * f, cy + dy * length * s * f
        c.line((wx, wy), (wx + nx * 1.4, wy + ny * 1.4), OUT, 3)
        c.fcircle(wx + nx * 2, wy + ny * 2, 1.6, OUT)
        c.fcircle(wx + nx * 2, wy + ny * 2, 1.0, pal['wheel'])
    for sx, sy, sd in ((x1, y1, 1), (x0, y0, -1)):
        c.limb((sx, sy), (sx + dx * 1.8 * sd - nx * 1.3, sy + dy * 1.8 * sd - ny * 1.3),
               pal['deck'], 2)
    c.limb((x0, y0), (x1, y1), pal['deck'], 2)
    c.line((x0 - nx * 1.1, y0 - ny * 1.1), (x1 - nx * 1.1, y1 - ny * 1.1), hx('#2a2a30'), 1)


def head(c, hp, facing, pal, s):
    hxp, hyp = hp
    f = facing
    r = 3.2 * s
    c.fcircle(hxp, hyp, r + 1, OUT)
    c.fcircle(hxp, hyp, r, pal['hair'])
    c.fcircle(hxp + .8 * f * s, hyp + .8 * s, r * .8, pal['skin'])
    st = pal['style']
    if st == 'long':
        c.rect(hxp - (4.0 * s) * f - (1.9 * s if f > 0 else 0), hyp - 1.6 * s, 2.0 * s, 7.5 * s, OUT)
        c.rect(hxp - (3.7 * s) * f - (1.5 * s if f > 0 else 0), hyp - 1.6 * s, 1.5 * s, 6.6 * s, pal['hair'])
    elif st == 'cap':
        c.fcircle(hxp, hyp - .5 * s, r + .6, pal['accent'])
        c.rect(hxp - r - 1, hyp - r - 1.4, 2 * r + 2, 1, OUT)
        c.rect(hxp + (.6 * s if f > 0 else -4.2 * s), hyp - 1.2 * s, 3.8 * s, 1.6, OUT)
        c.rect(hxp + (.8 * s if f > 0 else -4.0 * s), hyp - 1.0 * s, 3.4 * s, 1.1, pal['accent'])
    elif st == 'beanie':
        c.fcircle(hxp, hyp - .9 * s, r + .6, pal['accent'])
        c.rect(hxp - r - 1, hyp - 1.5 * s, 2 * r + 2, 1.5, OUT)
        c.rect(hxp - r - .6, hyp - 1.3 * s, 2 * r + 1.2, 1.1, pal['accent'])
    c.rect(hxp + 1.5 * s * f - (1 if f < 0 else 0), hyp + .1, 1, 2, OUT)


def draw_figure(c, ox, oy, pose, pal, flip, s=FIG):
    f = -1 if flip else 1

    sq = pose.get('sq', 1.0)

    def T(p):
        return (ox + p[0] * s * f, oy + p[1] * s * sq)

    bd = pose['board']
    if bd['z'] == 'under':
        board(c, ox + bd['x'] * s * f, oy + bd['y'] * s, bd['a'] * f, pal, bd['len'], s)

    strokes, blobs = [], []
    a = pose['arms_back'][0]
    strokes += [(T(a[0]), T(a[1]), pal['skin_sh'], 2), (T(a[1]), T(a[2]), pal['skin_sh'], 2)]
    blobs.append((T(a[2]), 2, pal['skin_sh']))
    l = pose['legs_back'][0]
    strokes += [(T(l[0]), T(l[1]), pal['pants_sh'], 3), (T(l[1]), T(l[2]), pal['pants_sh'], 2)]
    blobs.append((T(l[2]), 3, pal['shoe_sh']))

    strokes.append((T(pose['neck']), T(pose['hip']), pal['shirt'], 5))

    l = pose['legs'][0]
    strokes += [(T(l[0]), T(l[1]), pal['pants'], 3), (T(l[1]), T(l[2]), pal['pants'], 2)]
    blobs.append((T(l[2]), 3, pal['shoe']))
    a = pose['arms'][0]
    strokes += [(T(a[0]), T(a[1]), pal['skin'], 2), (T(a[1]), T(a[2]), pal['skin'], 2)]
    blobs.append((T(a[2]), 2, pal['skin']))

    for p0, p1, _, t in strokes:
        c.line(p0, p1, OUT, t + 2)
    for p, sz, _ in blobs:
        c.dot(p[0], p[1], sz + 2, OUT)
    for p0, p1, col, t in strokes:
        c.line(p0, p1, col, t)
    for p, sz, col in blobs:
        c.dot(p[0], p[1], sz, col)

    head(c, T(pose['head']), f, pal, s)

    if bd['z'] == 'over':
        board(c, ox + bd['x'] * s * f, oy + bd['y'] * s, bd['a'] * f, pal, bd['len'], s)


# --------------------------------------------------------------------------
# cycles
# --------------------------------------------------------------------------
# (t, pose, board-angle override)  -- the override lets the deck spin a full
# rotation during the ollie without the interpolator unwinding it
# blue shirt: rolls up the quarter pipe, flips out over the coping, lands and
# rides back down to where it started -- a closed loop, nothing teleports
RAMP = [(0.00, ROLL, 0, 'smooth'), (0.16, ROLL2, 0, 'hold'),
        (0.30, CROUCH, 0, 'hold'),                 # coil, and sit on it
        (0.38, POP, -30, 'snap'),                  # explode off the tail
        (0.48, AIR, -170, 'linear'), (0.56, AIR, -300, 'linear'),
        (0.63, AIR, -360, 'settle'),               # catch the board
        (0.69, LAND, -360, 'settle'),              # absorb
        (0.78, ROLL2, -360, 'smooth'), (1.00, ROLL, -360, 'smooth')]

# green shirt: in from off-screen right, onto the handrail, 50-50 down it,
# lands and rolls out before the loop restarts
RAIL = [(0.00, ROLL, 0, 'smooth'), (0.15, ROLL2, 0, 'hold'),
        (0.23, CROUCH, 0, 'hold'), (0.28, POP, -20, 'snap'),
        (0.33, AIR, -8, 'settle'), (0.37, GRIND, 0, 'settle'),
        (0.56, GRIND2, 0, 'smooth'), (0.76, GRIND, 0, 'hold'),
        (0.83, AIR, -10, 'snap'), (0.89, LAND, 0, 'settle'),
        (1.00, ROLL, 0, 'smooth')]

# pink shirt: stands her ground, breathing and tapping the nose of her board
IDLE = [(0.00, STAND_A, None, 'smooth'), (0.22, STAND_B, None, 'smooth'),
        (0.44, STAND_A, None, 'hold'),
        (0.58, TAP, None, 'snap'), (0.66, TAP, None, 'hold'),
        (0.78, STAND_A, None, 'settle'), (1.00, STAND_A, None, 'smooth')]


def sheet(timeline, pal, flip, path):
    """flip may be a bool, or a callable(u)->bool to turn mid-cycle"""
    from PIL import Image
    W, H = BOX_W * FRAMES, BOX_H
    c = Canvas(W, H, KEY)
    for i in range(FRAMES):
        u = i / float(FRAMES)
        pose = sample(timeline, u)
        fl = flip(u) if callable(flip) else flip
        draw_figure(c, i * BOX_W + ORIGIN[0], ORIGIN[1], pose, pal, fl)
    im = Image.new('RGBA', (W, H))
    im.putdata([(p + (0,)) if p == KEY else (p + (255,))
                for y in range(H) for x in range(W) for p in (c.px[y][x],)])
    im = im.resize((W * SCALE, H * SCALE), Image.NEAREST)
    im.save(path)
    return im


if __name__ == '__main__':
    jobs = [
        # blue shirt -- faces right on the way up the ramp, left on the way down
        ('skater-ramp.png', RAMP,
         pal_of(skin=0, hair=4, shirt=2, pants=0, deck=3, style='cap', accent='#ffd21f'),
         lambda u: u >= 0.66),
        # green shirt -- travels right to left the whole way
        ('skater-rail.png', RAIL,
         pal_of(skin=1, hair=0, shirt=3, pants=5, deck=2, style='beanie', accent='#19c7c7'), True),
        # pink shirt -- stationary
        ('skater-idle.png', IDLE,
         pal_of(skin=2, hair=3, shirt=0, pants=2, deck=1, style='long'), True),
    ]
    ims = []
    for name, tl, pal, flip in jobs:
        p = os.path.join(ROOT, name)
        ims.append(sheet(tl, pal, flip, p))
        print('%-20s %d frames  %dx%d  %d KB'
              % (name, FRAMES, BOX_W * FRAMES * SCALE, BOX_H * SCALE,
                 os.path.getsize(p) // 1024))

    if '--contact' in sys.argv:
        from PIL import Image
        cw = BOX_W * SCALE * 8
        rows = []
        for im in ims:
            for r in range(FRAMES // 8):
                rows.append(im.crop((r * cw, 0, (r + 1) * cw, BOX_H * SCALE)))
        out = Image.new('RGB', (cw, BOX_H * SCALE * len(rows)), (46, 52, 64))
        for i, r in enumerate(rows):
            out.paste(r, (0, i * BOX_H * SCALE), r)
        out.save(os.path.join(ROOT, 'tools', 'contact.png'))
        print('contact sheet -> tools/contact.png')
