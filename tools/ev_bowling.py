#!/usr/bin/env python3
"""ev_bowling.py - graphics and sounds of the Bowling event (ten pin, 10 frames).
Created By Mark Stronks, Stronkie Soft."""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gfxlib as g

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(g.ROOT, 'build', 'gen')
random.seed(41)
PAL = [0x112, 0x000, 0xfff, 0xfd0, 0xd22, 0xdb8, 0xca6, 0xa84, 0x763, 0x333,
       0x555, 0x888, 0x26c, 0x14a, 0x6af, 0xe6a, 0x223, 0x2c4, 0xbbb, 0x445,
       0x8ce, 0x931, 0xf80, 0x66a, 0x224]
(BG, BLACK, WHITE, YELLOW, RED, L1, L2, L3, L4, GUT, GUT2, GREY, BALL, BALLD, BALLL, PINK, WALL, GREEN, PINS, WALL2,
 LIGHT, BROWN, ORANGE, BLUEG, DARK) = range(25)
NEAR_Y, FAR_Y = 232, 84
NEAR_HW, FAR_HW = 92, 36
NV = 64

def lane_xy(u, v):
    """u -1..1 across, v 0..1 down the lane -> screen x, y"""
    z = 1 + 2.2 * v
    k = (1 / z - 1 / 3.2) / (1 - 1 / 3.2)          # 1 near .. 0 far
    y = FAR_Y + (NEAR_Y - FAR_Y) * k
    hw = FAR_HW + (NEAR_HW - FAR_HW) * k
    return 160 + u * hw, y, hw

def background():
    im = Image.new('P', (320, 256), WALL); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 319, 23], fill=BG); d.line([0, 23, 319, 23], fill=YELLOW)
    # the back wall with lights and the pin deck
    for y in range(24, FAR_Y):
        d.line([0, y, 319, y], fill=WALL if (y // 4) % 2 else WALL2)
    d.rectangle([0, 24, 319, 34], fill=DARK)
    for x in range(8, 320, 32):
        d.ellipse([x, 26, x + 10, 32], fill=LIGHT)
    g.text8(im, 48, 38, 'STRONKIE BOWL', ORANGE)
    d.rectangle([116, 50, 204, FAR_Y], fill=BLACK)              # the pit
    # the lane in perspective, with gutters
    for i in range(NV):
        v0 = i / NV; v1 = (i + 1) / NV
        xa, ya, _ = lane_xy(-1, v0); xb, yb, _ = lane_xy(1, v0)
        xc, yc, _ = lane_xy(1, v1); xd, yd, _ = lane_xy(-1, v1)
        d.polygon([(xa, ya), (xb, yb), (xc, yc), (xd, yd)], fill=[L1, L2][i % 2])
        ga, _, _ = lane_xy(-1.25, v0); gb, _, _ = lane_xy(-1.25, v1)
        d.polygon([(ga, ya), (xa, ya), (xd, yd), (gb, yd)], fill=GUT)
        ga, _, _ = lane_xy(1.25, v0); gb, _, _ = lane_xy(1.25, v1)
        d.polygon([(xb, yb), (ga, ya), (gb, yd), (xc, yc)], fill=GUT)
    for u in (-0.6, -0.3, 0, 0.3, 0.6):                      # boards and arrows
        x0, y0, _ = lane_xy(u, 0); x1, y1, _ = lane_xy(u, 1)
        d.line([x0, y0, x1, y1], fill=L3)
    for u in (-0.6, -0.3, 0, 0.3, 0.6):
        x, y, _ = lane_xy(u, 0.3); d.polygon([(x, y - 4), (x - 3, y + 2), (x + 3, y + 2)], fill=RED)
    x0, y0, _ = lane_xy(-1, 0.06); x1, _, _ = lane_xy(1, 0.06)
    d.line([x0, y0, x1, y0], fill=L4)                           # the foul line
    # the floor next to the lane
    for y in range(FAR_Y, 240):
        xa, _, _ = lane_xy(-1.25, 0)
    # the pin diagram box (right) and the bottom bar
    d.rectangle([256, 40, 319, 92], fill=BLACK, outline=GREY)
    d.rectangle([0, 240, 319, 255], fill=BG); d.line([0, 240, 319, 240], fill=YELLOW)
    return im

def pin(fallen=False):
    if fallen:
        im = g.bob_canvas(14, 6); d = ImageDraw.Draw(im)
        d.ellipse([0, 0, 13, 5], fill=BLACK); d.ellipse([1, 1, 12, 4], fill=PINS); d.line([4, 1, 4, 4], fill=RED)
        return im
    im = g.bob_canvas(8, 15); d = ImageDraw.Draw(im)
    d.ellipse([2, 0, 5, 4], fill=WHITE, outline=BLACK)
    d.rectangle([3, 4, 4, 5], fill=WHITE); d.line([2, 5, 5, 5], fill=RED)
    d.ellipse([0, 5, 7, 14], fill=WHITE, outline=BLACK)
    d.point((2, 8), fill=PINS)
    return im

def balls():
    out = []
    for r in (6, 5, 4, 3, 2):
        im = g.bob_canvas(14, 14); d = ImageDraw.Draw(im)
        d.ellipse([7 - r - 1, 7 - r - 1, 7 + r, 7 + r], fill=BLACK)
        d.ellipse([7 - r, 7 - r, 7 + r - 1, 7 + r - 1], fill=BALL)
        if r >= 4: d.point((6, 5), fill=BALLL); d.point((8, 5), fill=BALLD); d.point((7, 7), fill=BALLD)
        out.append(im)
    return out

def bowler(woman):
    st = g.pose_stand(); st.update(rel=(21, 20), rha=(22, 27))
    back = dict(st); back.update(rel=(22, 17), rha=(25, 11), hip=(16, 27), lkn=(14, 37), rkn=(19, 36))
    rel = dict(st); rel.update(head=(16, 10), neck=(16, 16), hip=(16, 29), rel=(20, 24), rha=(20, 32),
                               lkn=(12, 38), lft=(10, 46), rkn=(20, 38), rft=(22, 44), lel=(10, 20), lha=(6, 22))
    out = []
    for i, p in enumerate((st, back, rel)):
        f = g.athlete(p, woman=woman, back=True)
        if i < 2:
            d = ImageDraw.Draw(f); hx, hy = p['rha']
            d.ellipse([hx - 4, hy - 3, hx + 4, hy + 5], fill=BLACK); d.ellipse([hx - 3, hy - 2, hx + 3, hy + 4], fill=BALL)
        out.append(f)
    return out

def sounds(o):
    R = 8000
    n = int(1.4 * R)
    roll = g.bandnoise(n, 20, 120, 3) * 0.7 + np.sin(2 * np.pi * 55 * np.arange(n) / R) * 0.3
    o.sample('snd_roll', g.tosamp(roll * np.minimum(1, np.arange(n) / 600)), R)
    crash = np.zeros(int(0.9 * R)); rng = np.random.default_rng(9)
    for i in range(14):
        p = rng.integers(0, len(crash) - 1500); t = np.arange(1500) / R
        f = rng.uniform(700, 1500)
        crash[p:p + 1500] += (np.sin(2 * np.pi * f * t) * 0.6 + g.noise(1500, i) * 0.5) * np.exp(-t / 0.03) * rng.uniform(0.4, 1)
    o.sample('snd_crash', g.tosamp(crash), R)
    o.sample('snd_gutter', g.tosamp(g.bandnoise(int(0.8 * R), 30, 200, 4) * g.env(int(0.8 * R), 0.05, 0.4, R)), R)
    o.sample('snd_drop', g.tosamp(g.thump(int(0.15 * R), 90, 50, 0.04, R)), R)
    V = 6000
    o.sample('v_bowling', g.speak('b oU l I N'), V)
    o.sample('v_strike', g.speak('s t r aI k'), V)
    o.sample('v_spare', g.speak('s p e @ r'), V)
    o.sample('v_gutter', g.speak('g V t @ r'), V)

def main():
    o = g.Out(OUT, 'bow')
    o.bob('pin_up', pin()); o.bob('pin_down', pin(True))
    o.bobs('bball', balls())
    o.bobs('bm', bowler(False)); o.bobs('bw', bowler(True))
    sounds(o)
    o.raw(g.palette_line('pal_bow', PAL))
    ys, xs = [], []
    for i in range(NV + 1):
        x, y, hw = lane_xy(0, i / NV); ys.append(int(round(y))); xs.append(int(round(hw)))
    o.raw('lane_y\tdc.w\t' + ','.join(map(str, ys)))
    o.raw('lane_hw\tdc.w\t' + ','.join(map(str, xs)))
    # the pins: lateral place (in 1/256 of the half width at the far end), y on the screen; rows of 1, 2, 3, 4
    pins = [(0, 0), (-1, 1), (1, 1), (-2, 2), (0, 2), (2, 2), (-3, 3), (-1, 3), (1, 3), (3, 3)]
    o.raw('pin_pos\tdc.w\t' + ','.join('%d,%d' % (c, r) for c, r in pins))
    o.raw('pin_scr\tdc.w\t' + ','.join('%d,%d' % (160 + c * 8 - 4, FAR_Y - 17 - r * 5) for c, r in pins))
    o.raw('pin_box\tdc.w\t' + ','.join('%d,%d' % (288 + c * 8, 82 - r * 10) for c, r in pins))
    o.equ('NV', NV); o.equ('NEAR_Y', NEAR_Y); o.equ('FAR_Y', FAR_Y)
    n = o.write()
    bg = background()
    g.save_screen(bg, os.path.join(OUT, 'bow_bg.rle'))
    g.preview(bg, PAL, os.path.join(OUT, 'preview_bow.png'))
    print('bowling: %d bytes chip' % n)

if __name__ == '__main__':
    main()
