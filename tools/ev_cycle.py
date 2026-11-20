#!/usr/bin/env python3
"""ev_cycle.py - graphics and sounds of Cycling (500m on the velodrome) for Stronkie's Olympics.
Created By Mark Stronks, Stronkie Soft."""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gfxlib as g

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(g.ROOT, 'build', 'gen')
random.seed(77)
PAL = [0x112, 0x000, 0xfff, 0xfd0, 0xd22, 0x334, 0x446, 0xe55, 0xfd6, 0x5af, 0xa63, 0xc85, 0x742, 0x29d, 0x999,
       0x889, 0x112, 0x555,
       0x321, 0xc96, 0xa74, 0xd22, 0x911, 0x222, 0x111]
(BG, BLACK, WHITE, YELLOW, RED, ST1, ST2, CR1, CR2, CR3, WOOD, WOOD2, WOOD3, BLUE, METAL, GREY, DARK, SHADE) = range(18)
RIVAL = dict(hair=18, skin=19, skind=20, shirt=21, shirtd=22, shorts=23, shoes=24)
START_X, FINISH_X = 24, 300
LANE_C, LANE_P = 172, 216

def background():
    im = Image.new('P', (320, 256), BG); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 319, 23], fill=DARK); d.line([0, 23, 319, 23], fill=YELLOW)
    for y in range(24, 104): d.line([0, y, 319, y], fill=ST1 if (y // 4) % 2 else ST2)
    for i in range(2600): d.point((random.randrange(320), random.randrange(25, 103)), fill=random.choice([CR1, CR2, CR3, WHITE, YELLOW]))
    d.rectangle([0, 104, 319, 121], fill=BLUE); g.text8(im, 24, 109, 'STRONKIE SOFT', WHITE); g.text8(im, 176, 109, '500M', YELLOW)
    for y in range(122, 240):                                     # the banked wooden track
        d.line([0, y, 319, y], fill=[WOOD, WOOD2, WOOD3][(y // 3) % 3] if y % 3 else WOOD3)
    for x in range(-40, 330, 37): d.line([x, 122, x + 6, 239], fill=WOOD3)
    d.rectangle([0, 122, 319, 127], fill=BLUE)
    d.line([0, 150, 319, 150], fill=RED); d.line([0, 194, 319, 194], fill=BLUE)
    d.rectangle([START_X - 1, 150, START_X, 236], fill=WHITE)
    for y in range(150, 236, 4): d.rectangle([FINISH_X - 2, y, FINISH_X + 1, y + 1], fill=BLACK); d.rectangle([FINISH_X - 2, y + 2, FINISH_X + 1, y + 3], fill=WHITE)
    d.rectangle([0, 239, 319, 255], fill=DARK); d.line([0, 240, 319, 240], fill=YELLOW)
    return im

def ik(hip, foot, l1=9.5, l2=10.0):
    """the knee between the hip and the foot, bent forward"""
    hx, hy = hip; fx, fy = foot
    dx, dy = fx - hx, fy - hy; dd = min(math.hypot(dx, dy), l1 + l2 - 0.01)
    a = math.atan2(dy, dx); c = (l1 * l1 + dd * dd - l2 * l2) / (2 * l1 * dd)
    b = math.acos(max(-1, min(1, c)))
    return (hx + l1 * math.cos(a - b), hy + l1 * math.sin(a - b))

def bike(kit, woman, phase):
    """phase 0-5 pedalling, 6: still"""
    im = g.bob_canvas(48, 48); d = ImageDraw.Draw(im)
    for cx in (9, 39):                                            # the wheels
        d.ellipse([cx - 8, 31, cx + 8, 47], outline=BLACK); d.ellipse([cx - 7, 32, cx + 7, 46], outline=METAL)
        a = (phase if phase < 6 else 0) * 0.5
        for k in range(3):
            q = a + k * math.pi / 3
            d.line([cx - 6 * math.cos(q), 39 - 6 * math.sin(q), cx + 6 * math.cos(q), 39 + 6 * math.sin(q)], fill=GREY)
    fc = kit['shirt'] if kit else g.SHIRT
    for a, b in (((9, 39), (24, 40)), ((24, 40), (20, 27)), ((20, 27), (36, 27)), ((24, 40), (36, 27)), ((36, 27), (39, 39))):
        d.line([a, b], fill=BLACK, width=3)
    for a, b in (((9, 39), (24, 40)), ((24, 40), (20, 27)), ((20, 27), (36, 27)), ((24, 40), (36, 27)), ((36, 27), (39, 39))):
        d.line([a, b], fill=RED, width=1)
    d.line([18, 26, 23, 26], fill=BLACK, width=2); d.line([36, 27, 39, 25], fill=BLACK, width=2)   # saddle, bars
    # the rider (athlete box 32x48 at x offset 6)
    ox = 6; ang = (phase if phase < 6 else 1.5) * math.pi / 3
    crank = (24 - ox, 40)
    f1 = (crank[0] + 5 * math.cos(ang), crank[1] + 5 * math.sin(ang))
    f2 = (crank[0] - 5 * math.cos(ang), crank[1] - 5 * math.sin(ang))
    hip = (20 - ox, 24); neck = (31 - ox, 16)
    p = dict(head=(34 - ox, 12), neck=neck, hip=hip, lel=(33 - ox, 21), lha=(37 - ox, 25), rel=(33 - ox, 21), rha=(37 - ox, 25),
             lkn=ik(hip, f2), lft=f2, rkn=ik(hip, f1), rft=f1)
    a = g.athlete(p, woman=woman, kit=kit)
    m = Image.fromarray(((np.array(a) != g.TRANSP) * 255).astype('uint8'), 'L'); im.paste(a, (ox, 0), m)
    for f in (f1, f2): d.line([f[0] + ox - 1, f[1], f[0] + ox + 2, f[1]], fill=BLACK)   # pedals
    return im

def frames(kit, woman):
    return [bike(kit, woman, i) for i in range(6)] + [bike(kit, woman, 6)]

def sounds(o):
    R = 8000
    o.sample('snd_gun', g.tosamp(g.noise(int(0.35 * R), 3) * g.env(int(0.35 * R), 0.001, 0.06, R) + g.thump(int(0.35 * R), 160, 60, 0.05, R)), R)
    t = np.arange(int(0.06 * R)) / R
    o.sample('snd_gear', g.tosamp((np.sign(np.sin(2 * np.pi * 900 * t)) * 0.5 + g.noise(len(t), 4)) * np.exp(-t / 0.015)), R)
    o.sample('snd_whirr', g.tosamp(g.bandnoise(int(0.1 * R), 6, 30, 7) * g.env(int(0.1 * R), 0.01, 0.05, R) * 0.6), R)
    o.sample('v_title', g.speak('s aI k l I N'), 6000)

def main():
    o = g.Out(OUT, 'cyc')
    o.bobs('pm', frames(None, False)); o.bobs('pw', frames(None, True))
    o.bobs('cm', frames(RIVAL, False)); o.bobs('cw', frames(RIVAL, True))
    sounds(o)
    o.raw(g.palette_line('pal_race', PAL))
    o.equ('START_X', START_X); o.equ('FINISH_X', FINISH_X); o.equ('LANE_C', LANE_C); o.equ('LANE_P', LANE_P)
    n = o.write()
    bg = background()
    g.save_screen(bg, os.path.join(OUT, 'cyc_bg.rle'))
    g.preview(bg, PAL, os.path.join(OUT, 'preview_cyc.png'))
    fr = frames(None, False); pal = list(PAL) + g.DEF_PLAYER
    sheet = Image.new('P', (48 * 7, 48), BG)
    for i, f in enumerate(fr):
        m = Image.fromarray(((np.array(f) != g.TRANSP) * 255).astype('uint8'), 'L'); sheet.paste(f, (i * 48, 0), m)
    g.preview(sheet, pal, os.path.join(OUT, 'preview_cyc_bikes.png'), scale=4)
    print('cycling: %d bytes chip' % n)

if __name__ == '__main__':
    main()
