#!/usr/bin/env python3
"""ev_volley.py - graphics and sounds of the Volleyball event (beach volleyball, 1 against 1).
Created By Mark Stronks, Stronkie Soft."""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gfxlib as g

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(g.ROOT, 'build', 'gen')
random.seed(31)
#      0 sky   1 black 2 white 3 yellow 4 red  5 sea   6 sea2  7 sand  8 sand2 9 sand3
PAL = [0x112, 0x000, 0xfff, 0xfd0, 0xd22, 0x27b, 0x49d, 0xec8, 0xdb7, 0xb95,
       0x864, 0x2a4, 0x161, 0x112, 0x48f, 0xf8a, 0xca6,
       0x753,                                   # 17 shadow on the sand
       0x321, 0xc96, 0xa74, 0xd22, 0x911, 0x222, 0x111]   # 18-24: the other athlete (filled in)
(SKY, BLACK, WHITE, YELLOW, RED, SEA, SEA2, SAND, SAND2, SAND3, POST, LEAF, LEAFD, DARK, BLUE, PINK, SANDD, SHADOW) = range(18)
CPU = dict(hair=18, skin=19, skind=20, shirt=21, shirtd=22, shorts=23, shoes=24)
GROUND = 206          # feet / the sand line
NET_X, NET_TOP = 160, 132

def gradient():
    items = []
    for i, y in enumerate(range(24, 112, 6)):
        k = i / 14
        r, gg, b = int(3 + 6 * k), int(6 + 7 * k), int(12 + 3 * k)
        items.append((y, (min(15, r) << 8) | (min(15, gg) << 4) | min(15, b)))
    items.append((206, 0x112))
    return items

def background():
    im = Image.new('P', (320, 256), SKY); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 319, 23], fill=DARK); d.line([0, 23, 319, 23], fill=YELLOW)
    # sun and a few clouds
    d.ellipse([250, 34, 280, 64], fill=YELLOW)
    for (x, y) in ((40, 44), (120, 58), (190, 38)):
        for i in range(4): d.ellipse([x + i * 10, y - (i % 2) * 4, x + i * 10 + 18, y + 10 - (i % 2) * 4], fill=WHITE)
    # the sea
    for y in range(112, 150):
        d.line([0, y, 319, y], fill=SEA if (y // 3) % 3 else SEA2)
    for i in range(80):
        x = random.randrange(320); y = random.randrange(114, 148); d.line([x, y, x + 5, y], fill=WHITE)
    # the sand
    for y in range(150, 240):
        d.line([0, y, 319, y], fill=SAND)
    for i in range(1400):
        d.point((random.randrange(320), random.randrange(150, 240)), fill=random.choice([SAND2, SAND3, SANDD]))
    d.line([0, GROUND + 2, 319, GROUND + 2], fill=SAND3)
    # a palm tree at the left and an umbrella at the right
    for i in range(60):
        t = i / 60; x = 10 + 8 * math.sin(t * 2.2); y = 200 - i * 1.7
        d.ellipse([x - 3, y - 2, x + 3, y + 2], fill=POST)
    for a in range(0, 360, 50):
        r = math.radians(a)
        d.polygon([(18, 98), (18 + 34 * math.cos(r), 98 + 16 * math.sin(r) + 8), (18 + 30 * math.cos(r + 0.25), 98 + 14 * math.sin(r + 0.25) + 10)], fill=LEAF if a % 100 else LEAFD)
    d.pieslice([270, 150, 316, 176], 180, 360, fill=RED); d.pieslice([284, 150, 302, 176], 180, 360, fill=WHITE)
    d.line([293, 163, 293, 200], fill=DARK)
    # the court lines in the sand
    d.line([12, GROUND + 6, 308, GROUND + 6], fill=BLUE)
    # the net
    d.rectangle([NET_X - 2, NET_TOP - 8, NET_X + 1, GROUND], fill=POST)
    for y in range(NET_TOP, NET_TOP + 40, 4): d.line([NET_X - 3, y, NET_X + 2, y], fill=WHITE)
    d.rectangle([NET_X - 4, NET_TOP - 1, NET_X + 3, NET_TOP + 1], fill=WHITE)
    d.rectangle([0, 240, 319, 255], fill=DARK); d.line([0, 240, 319, 240], fill=YELLOW)
    return im

def frames(woman, kit=None, flip=False):
    st = g.pose_stand()
    st.update(lel=(19, 20), lha=(22, 24), rel=(13, 20), rha=(11, 25))
    ready = dict(st); ready.update(hip=(15, 28), lkn=(19, 37), lft=(15, 46), rkn=(14, 37), rft=(18, 46), lel=(20, 20), lha=(24, 18), rel=(21, 21), rha=(25, 19))
    jump = dict(head=(17, 9), neck=(16, 15), hip=(15, 28), lel=(19, 9), lha=(21, 2), rel=(20, 10), rha=(23, 3),
                lkn=(17, 36), lft=(13, 41), rkn=(19, 37), rft=(16, 43))
    spike = dict(jump); spike.update(lel=(21, 13), lha=(27, 10), rel=(21, 12), rha=(28, 9))
    run = g.run_cycle(4, lean=1)
    poses = [ready] + run + [jump, spike]
    return [g.athlete(p, woman=woman, kit=kit, flip=flip) for p in poses]

def ball():
    im = g.bob_canvas(14, 14); d = ImageDraw.Draw(im)
    d.ellipse([0, 0, 13, 13], fill=BLACK); d.ellipse([1, 1, 12, 12], fill=WHITE)
    d.arc([3, -6, 18, 9], 100, 200, fill=BLUE, width=2); d.arc([-5, 5, 9, 20], 280, 20, fill=YELLOW, width=2)
    return im

def shadow():
    im = g.bob_canvas(16, 4); d = ImageDraw.Draw(im)
    d.ellipse([0, 0, 13, 3], fill=SHADOW)
    return im

def sounds(o):
    R = 8000
    o.sample('snd_hit', g.tosamp(g.thump(int(0.1 * R), 300, 120, 0.02, R) + g.noise(int(0.1 * R), 4) * g.env(int(0.1 * R), 0.001, 0.008, R) * 0.7), R)
    o.sample('snd_spike', g.tosamp(g.thump(int(0.14 * R), 420, 140, 0.03, R) + g.noise(int(0.14 * R), 6) * g.env(int(0.14 * R), 0.001, 0.02, R)), R)
    o.sample('snd_sand', g.tosamp(g.bandnoise(int(0.18 * R), 3, 25, 8) * g.env(int(0.18 * R), 0.002, 0.05, R)), R)
    o.sample('snd_net', g.tosamp(g.bandnoise(int(0.2 * R), 6, 40, 9) * g.env(int(0.2 * R), 0.005, 0.07, R)), R)
    V = 6000
    o.sample('v_volley', g.speak('v o l i b o l'), V)
    o.sample('v_point', g.speak('p oI n t'), V)
    o.sample('v_spike', g.speak('s p aI k'), V)
    o.sample('v_out', g.speak('aI t', speed=0.9), V)

def main():
    o = g.Out(OUT, 'vol')
    o.bobs('pm', frames(False)); o.bobs('pw', frames(True))
    o.bobs('cm', frames(False, CPU, True)); o.bobs('cw', frames(True, CPU, True))
    o.bob('vball', ball()); o.bob('vshadow', shadow())
    sounds(o)
    o.raw(g.palette_line('pal_vol', PAL))
    o.raw(g.grad_lines('grad_vol', gradient()))
    o.equ('GROUND', GROUND); o.equ('NET_X', NET_X); o.equ('NET_TOP', NET_TOP)
    n = o.write()
    bg = background()
    g.save_screen(bg, os.path.join(OUT, 'vol_bg.rle'))
    g.preview(bg, PAL, os.path.join(OUT, 'preview_vol.png'))
    sheet = Image.new('P', (320, 110), SAND)
    for i, im in enumerate(frames(False) + frames(True, CPU, True)):
        a = np.array(im); a[a == g.TRANSP] = SAND; sheet.paste(Image.fromarray(a, 'P'), ((i % 7) * 40, 4 + (i // 7) * 52))
    g.preview(sheet, PAL, os.path.join(OUT, 'preview_vol_bobs.png'), 3)
    print('volleyball: %d bytes chip' % n)

if __name__ == '__main__':
    main()
