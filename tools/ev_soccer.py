#!/usr/bin/env python3
"""ev_soccer.py - graphics and sounds of the Soccer event (penalty shoot-out) of Stronkie's Olympics.
Created By Mark Stronks, Stronkie Soft."""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gfxlib as g

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(g.ROOT, 'build', 'gen')
random.seed(11)
PAL = [0x112, 0x000, 0xfff, 0xfd0, 0xd22, 0x262, 0x3a3, 0x383, 0xbbb, 0x777,
       0xfd2, 0xb90, 0xeb9, 0xb86, 0x222, 0x421, 0x345, 0x234, 0x58b, 0xe64,
       0xc33, 0xdd8, 0x9ab, 0x151, 0x47c]
PAL_B = list(PAL); PAL_B[10] = 0x2c4; PAL_B[11] = 0x182      # the keeper in green when you keep
(STRIP, BLACK, WHITE, YELLOW, RED, GD, GL, GM, NET, NETD, KS, KSD, KSK, KSKD, KSH, KHAIR,
 ST1, ST2, CR1, CR2, CR3, CR4, CR5, SHADOW, CR6) = range(25)
KEEPER = dict(hair=KHAIR, skin=KSK, skind=KSKD, shirt=KS, shirtd=KSD, shorts=KSH, shoes=BLACK)
GOAL_L, GOAL_R, BAR_Y, LINE_Y = 96, 224, 76, 132
SPOT = (160, 198)

def background():
    im = Image.new('P', (320, 256), STRIP); d = ImageDraw.Draw(im)
    for y in range(24, 62):                                  # the stands
        d.line([0, y, 319, y], fill=ST1 if (y // 4) % 2 else ST2)
    for i in range(2600):
        x = random.randrange(320); y = random.randrange(25, 61)
        d.point((x, y), fill=random.choice([CR1, CR2, CR3, CR4, CR5, CR6, WHITE, YELLOW]))
    # advertising boards
    cols = [(RED, WHITE, 'STRONKIE SOFT'), (CR6, YELLOW, 'AMIGA 500'), (YELLOW, BLACK, 'GOTEK'), (WHITE, RED, 'C64')]
    x = 0; i = 0
    while x < 320:
        bg, fg, t = cols[i % 4]; w = len(t) * 8 + 16
        d.rectangle([x, 62, x + w - 1, 71], fill=bg); g.text8(im, x + 8, 63, t, fg); x += w; i += 1
    # the grass in stripes, wider closer to us
    y = 72; k = 0
    while y < 240:
        h = 6 + (y - 72) // 10
        d.rectangle([0, y, 319, min(239, y + h - 1)], fill=GL if k % 2 else GM); y += h; k += 1
    # pitch lines
    d.line([0, LINE_Y, 319, LINE_Y], fill=WHITE)
    d.line([64, 150, 256, 150], fill=WHITE); d.line([64, 150, 78, LINE_Y], fill=WHITE); d.line([256, 150, 242, LINE_Y], fill=WHITE)
    d.line([0, 218, 319, 218], fill=WHITE); d.line([20, LINE_Y, 0, 160], fill=WHITE); d.line([300, LINE_Y, 319, 160], fill=WHITE)
    d.arc([110, 205, 210, 250], 180, 360, fill=WHITE)
    d.ellipse([SPOT[0] - 3, SPOT[1] + 2, SPOT[0] + 3, SPOT[1] + 5], fill=WHITE)
    # the goal: net, back, posts and bar
    d.polygon([(GOAL_L + 4, BAR_Y + 4), (GOAL_R - 4, BAR_Y + 4), (GOAL_R - 12, BAR_Y - 6), (GOAL_L + 12, BAR_Y - 6)], fill=STRIP)
    d.rectangle([GOAL_L + 4, BAR_Y + 4, GOAL_R - 5, LINE_Y], fill=GD)
    for x in range(GOAL_L + 4, GOAL_R - 4, 5): d.line([x, BAR_Y - 6 if GOAL_L + 12 <= x <= GOAL_R - 12 else BAR_Y + 4, x, LINE_Y], fill=NET)
    for y in range(BAR_Y + 4, LINE_Y, 5): d.line([GOAL_L + 4, y, GOAL_R - 5, y], fill=NET)
    for y in range(BAR_Y - 6, BAR_Y + 4, 4): d.line([GOAL_L + 12, y, GOAL_R - 12, y], fill=NETD)
    d.line([GOAL_L + 12, BAR_Y - 6, GOAL_R - 12, BAR_Y - 6], fill=NETD)
    d.rectangle([GOAL_L, BAR_Y, GOAL_L + 3, LINE_Y], fill=WHITE); d.rectangle([GOAL_R - 4, BAR_Y, GOAL_R - 1, LINE_Y], fill=WHITE)
    d.rectangle([GOAL_L, BAR_Y, GOAL_R - 1, BAR_Y + 3], fill=WHITE)
    d.line([GOAL_L + 3, BAR_Y + 4, GOAL_L + 3, LINE_Y], fill=NETD); d.line([GOAL_L, BAR_Y + 3, GOAL_R - 1, BAR_Y + 3], fill=NETD)
    # the power meter frame
    d.rectangle([294, 146, 311, 233], fill=BLACK, outline=WHITE)
    d.rectangle([STRIP, 240, 319, 255], fill=STRIP)
    d.rectangle([0, 240, 319, 255], fill=STRIP); d.line([0, 240, 319, 240], fill=YELLOW)
    d.rectangle([0, 0, 319, 23], fill=STRIP); d.line([0, 23, 319, 23], fill=YELLOW)
    return im

def keeper_frames():
    ready = dict(head=(16, 8), neck=(16, 14), hip=(16, 27), lel=(9, 18), lha=(5, 13), rel=(23, 18), rha=(27, 13),
                 lkn=(12, 37), lft=(10, 46), rkn=(20, 37), rft=(22, 46))
    up = dict(ready); up.update(lel=(11, 9), lha=(10, 2), rel=(21, 9), rha=(22, 2), lkn=(13, 36), lft=(12, 44), rkn=(19, 36), rft=(20, 44),
                                head=(16, 10), neck=(16, 16), hip=(16, 29))
    st = g.athlete(ready, kit=KEEPER)
    jump = g.athlete(up, kit=KEEPER)
    dive = dict(ready); dive.update(lel=(10, 10), lha=(7, 3), rel=(22, 10), rha=(25, 3))
    base = g.athlete(dive, kit=KEEPER)
    out = []
    for ang in (75, -75):
        c = Image.new('P', (48, 48), g.TRANSP); c.paste(base, (8, 0))
        r = c.rotate(ang, resample=Image.NEAREST, fillcolor=g.TRANSP, center=(24, 24))
        out.append(r)
    return st, jump, out[0], out[1]

def shooter_frames(woman):
    stand = g.pose_stand()
    r1 = dict(stand); r1.update(rkn=(19, 33), rft=(19, 40), lkn=(14, 37), lft=(14, 46), rel=(21, 19), rha=(22, 25), lel=(11, 18), lha=(10, 23))
    r2 = dict(stand); r2.update(lkn=(13, 33), lft=(13, 40), rkn=(18, 37), rft=(18, 46), lel=(11, 19), lha=(10, 25), rel=(21, 18), rha=(22, 23))
    kick = dict(stand); kick.update(head=(15, 7), neck=(15, 13), hip=(16, 26), rkn=(20, 31), rft=(22, 34), lkn=(14, 36), lft=(13, 45),
                                    rel=(23, 17), rha=(26, 20), lel=(9, 17), lha=(6, 20))
    return [g.athlete(p, woman=woman, back=True) for p in (stand, r1, r2, kick)]

def balls():
    out = []
    for r in (5, 4, 3, 2):
        im = g.bob_canvas(12, 12); d = ImageDraw.Draw(im)
        d.ellipse([6 - r - 1, 6 - r - 1, 6 + r, 6 + r], fill=BLACK)
        d.ellipse([6 - r, 6 - r, 6 + r - 1, 6 + r - 1], fill=WHITE)
        if r >= 3: d.point((6, 6), fill=BLACK); d.point((5, 5), fill=BLACK)
        out.append(im)
    return out

def cursor():
    im = g.bob_canvas(16, 16); d = ImageDraw.Draw(im)
    d.ellipse([1, 1, 14, 14], outline=BLACK); d.ellipse([2, 2, 13, 13], outline=YELLOW)
    d.line([8, 0, 8, 15], fill=YELLOW); d.line([0, 8, 15, 8], fill=YELLOW)
    d.point((8, 8), fill=RED)
    return im

def sounds(o):
    R = 8000
    o.sample('snd_kick', g.tosamp(g.thump(int(0.12 * R), 180, 60, 0.03, R) + g.noise(int(0.12 * R), 3) * g.env(int(0.12 * R), 0.001, 0.01, R) * 0.6), R)
    t = np.arange(int(0.4 * R)) / R
    clang = (np.sin(2 * np.pi * 1250 * t) + 0.6 * np.sin(2 * np.pi * 1870 * t) + 0.3 * np.sin(2 * np.pi * 3100 * t)) * np.exp(-t / 0.12)
    o.sample('snd_post', g.tosamp(clang), R)
    o.sample('snd_net', g.tosamp(g.bandnoise(int(0.25 * R), 2, 12, 4) * g.env(int(0.25 * R), 0.01, 0.08, R)), R)
    V = 6000
    o.sample('v_soccer', g.speak('s o k @ r'), V)
    o.sample('v_goal', g.speak('g oU oU l', speed=0.8), V)
    o.sample('v_saved', g.speak('s eI v d'), V)
    o.sample('v_missed', g.speak('m I s t'), V)
    o.sample('v_youwin', g.speak('j u w I n'), V)

def main():
    o = g.Out(OUT, 'soc')
    st, jump, dl, dr = keeper_frames()
    o.bob('kp_stand', st); o.bob('kp_jump', jump); o.bob('kp_divel', dl); o.bob('kp_diver', dr)
    o.bobs('shm', shooter_frames(False)); o.bobs('shw', shooter_frames(True))
    o.bobs('ball', balls())
    o.bob('aimcur', cursor())
    sounds(o)
    o.raw(g.palette_line('pal_a', PAL)); o.raw(g.palette_line('pal_b', PAL_B))
    o.equ('GOAL_L', GOAL_L); o.equ('GOAL_R', GOAL_R); o.equ('BAR_Y', BAR_Y); o.equ('LINE_Y', LINE_Y)
    o.equ('SPOT_X', SPOT[0]); o.equ('SPOT_Y', SPOT[1])
    n = o.write()
    bg = background()
    g.save_screen(bg, os.path.join(OUT, 'soc_bg.rle'))
    g.preview(bg, PAL, os.path.join(OUT, 'preview_soc.png'))
    sheet = Image.new('P', (320, 60), STRIP)
    for i, im in enumerate([st, jump, dl, dr] + shooter_frames(False)):
        a = np.array(im); a[a == g.TRANSP] = STRIP; sheet.paste(Image.fromarray(a, 'P'), (i * 40, 4))
    g.preview(sheet, PAL, os.path.join(OUT, 'preview_soc_bobs.png'), 3)
    print('soccer: %d bytes chip' % n)

if __name__ == '__main__':
    main()
