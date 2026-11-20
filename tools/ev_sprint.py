#!/usr/bin/env python3
"""ev_sprint.py - the 100m sprint and the hurdles of Stronkie's Olympics (one generator, two events):
python3 tools/ev_sprint.py build/gen [hurdles].  Created By Mark Stronks, Stronkie Soft."""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gfxlib as g

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(g.ROOT, 'build', 'gen')
HURDLES = len(sys.argv) > 2 and sys.argv[2] == 'hurdles'
PRE = 'hur' if HURDLES else 'spr'
random.seed(81)
PAL = [0x112, 0x000, 0xfff, 0xfd0, 0xd22, 0x334, 0x446, 0xe55, 0xfd6, 0x5af, 0xb53, 0xc64, 0xeee, 0x383, 0x4a4,
       0x889, 0x112, 0x777,
       0x321, 0xc96, 0xa74, 0xd22, 0x911, 0x222, 0x111]          # 18-24: the rival
(BG, BLACK, WHITE, YELLOW, RED, ST1, ST2, CR1, CR2, CR3, TRACK, TRACK2, LANE, GRASS, GRASS2, GREY, DARK, SHADE) = range(18)
RIVAL = dict(hair=18, skin=19, skind=20, shirt=21, shirtd=22, shorts=23, shoes=24)
START_X, FINISH_X = 16, 296
LANE_C, LANE_P = 168, 214            # feet: the rival (back), you (front)
NH = 10

def background():
    im = Image.new('P', (320, 256), BG); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 319, 23], fill=DARK); d.line([0, 23, 319, 23], fill=YELLOW)
    for y in range(24, 112):
        d.line([0, y, 319, y], fill=ST1 if (y // 4) % 2 else ST2)
    for i in range(3600):
        d.point((random.randrange(320), random.randrange(25, 111)), fill=random.choice([CR1, CR2, CR3, WHITE, YELLOW, RED]))
    d.rectangle([0, 112, 319, 121], fill=GREY)
    g.text8(im, 24, 113, 'STRONKIE SOFT', RED); g.text8(im, 176, 113, '100M' if not HURDLES else '110M HURDLES', BLACK)
    d.rectangle([0, 122, 319, 132], fill=GRASS)
    d.rectangle([0, 133, 319, 232], fill=TRACK)
    for y in range(133, 233, 3): d.line([0, y, 319, y], fill=TRACK2 if y % 2 else TRACK)
    for y in (134, 176, 222): d.line([0, y, 319, y], fill=LANE)
    d.rectangle([0, 233, 319, 239], fill=GRASS2)
    for x in range(START_X + 28, FINISH_X, 28):                   # every 10 metres
        d.line([x, 134, x - 6, 222], fill=SHADE)
    for k in range(0, 11):
        x = START_X + k * 28
        if 0 < k < 10: g.text8(im, x - 8 if k < 10 else x - 12, 124, '%d' % (k * 10), WHITE)
    d.line([START_X, 134, START_X - 8, 222], fill=WHITE)            # start and finish
    for y in range(134, 222, 4):
        x = FINISH_X - (y - 134) * 8 // 88
        d.rectangle([x, y, x + 2, y + 1], fill=WHITE); d.rectangle([x, y + 2, x + 2, y + 3], fill=BLACK)
    d.rectangle([FINISH_X - 2, 96, FINISH_X + 1, 134], fill=GREY)
    d.rectangle([0, 240, 319, 255], fill=DARK); d.line([0, 240, 319, 240], fill=YELLOW)
    return im

def runner(kit, woman):
    out = [g.athlete(p, woman=woman, kit=kit) for p in g.run_cycle(6, lean=3)]
    crouch = dict(head=(22, 26), neck=(19, 30), hip=(12, 32), lel=(22, 38), lha=(24, 45), rel=(21, 38), rha=(23, 45),
                  lkn=(18, 40), lft=(9, 45), rkn=(9, 38), rft=(5, 45))
    jump = dict(head=(20, 8), neck=(19, 14), hip=(14, 26), lel=(24, 18), lha=(28, 20), rel=(13, 19), rha=(9, 23),
                lkn=(24, 27), lft=(30, 28), rkn=(9, 33), rft=(4, 30))
    fall = dict(head=(26, 34), neck=(22, 36), hip=(12, 38), lel=(26, 42), lha=(30, 46), rel=(24, 44), rha=(28, 46),
                lkn=(7, 40), lft=(2, 44), rkn=(8, 44), rft=(2, 46))
    out += [g.athlete(p, woman=woman, kit=kit) for p in (crouch, jump, fall)]
    return out

def hurdle(knocked):
    im = g.bob_canvas(16, 26); d = ImageDraw.Draw(im)
    if knocked:
        d.line([2, 24, 14, 24], fill=WHITE, width=2); d.line([2, 25, 2, 18], fill=GREY); d.line([14, 25, 14, 22], fill=GREY)
    else:
        d.rectangle([3, 2, 13, 5], fill=WHITE, outline=BLACK); d.line([4, 6, 4, 25], fill=GREY); d.line([12, 6, 12, 25], fill=GREY)
        d.line([3, 25, 6, 25], fill=BLACK); d.line([11, 25, 14, 25], fill=BLACK)
    return im

def sounds(o):
    R = 8000
    o.sample('snd_step', g.tosamp(g.thump(int(0.05 * R), 200, 90, 0.01, R)), R)
    o.sample('snd_gun', g.tosamp(g.noise(int(0.35 * R), 3) * g.env(int(0.35 * R), 0.001, 0.06, R) + g.thump(int(0.35 * R), 160, 60, 0.05, R)), R)
    t = np.arange(int(0.3 * R)) / R
    o.sample('snd_clatter', g.tosamp((np.sin(2 * np.pi * 700 * t) + g.noise(len(t), 5)) * np.exp(-t / 0.06)), R)
    V = 6000
    if HURDLES: o.sample('v_title', g.speak('h @ r d l z'), V)
    else: o.sample('v_title', g.speak('w V n h V n d r @ d m i t @ r z'), V)

def main():
    o = g.Out(OUT, PRE)
    o.bobs('pm', runner(None, False)); o.bobs('pw', runner(None, True))
    o.bobs('cm', runner(RIVAL, False)); o.bobs('cw', runner(RIVAL, True))
    if HURDLES: o.bob('hurdle_up', hurdle(False)); o.bob('hurdle_down', hurdle(True))
    sounds(o)
    o.raw(g.palette_line('pal_race', PAL))
    o.equ('START_X', START_X); o.equ('FINISH_X', FINISH_X); o.equ('LANE_C', LANE_C); o.equ('LANE_P', LANE_P)
    n = o.write()
    bg = background()
    g.save_screen(bg, os.path.join(OUT, PRE + '_bg.rle'))
    g.preview(bg, PAL, os.path.join(OUT, 'preview_%s.png' % PRE))
    print('%s: %d bytes chip' % (PRE, n))

if __name__ == '__main__':
    main()
