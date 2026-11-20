#!/usr/bin/env python3
"""ev_weights.py - graphics and sounds of Weightlifting for Stronkie's Olympics: the platform,
the lifter with the barbell.  Created By Mark Stronks, Stronkie Soft."""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gfxlib as g

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(g.ROOT, 'build', 'gen')
random.seed(33)
PAL = [0x112, 0x000, 0xfff, 0xfd0, 0xd22, 0x334, 0x446, 0xe55, 0xfd6, 0x5af, 0xa63, 0xc85, 0x742, 0x2a2, 0x999,
       0x889, 0x112, 0x555, 0xc22, 0x22c, 0x444, 0x000, 0x000, 0x000, 0x000]
(BG, BLACK, WHITE, YELLOW, RED, ST1, ST2, CR1, CR2, CR3, WOOD, WOOD2, WOOD3, GREEN, METAL, GREY, DARK, SHADE,
 PLATE, PLATE2, CHALK) = range(21)
LX, LY = 128, 216                    # the lifter's bob: x, feet
MET_X, MET_Y, MET_H = 272, 120, 100  # the power meter

def background():
    im = Image.new('P', (320, 256), BG); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 319, 23], fill=DARK); d.line([0, 23, 319, 23], fill=YELLOW)
    g.stands(im, 24, 120, PAL, seed=61, light=0.85)
    d.rectangle([60, 30, 260, 62], fill=BLACK, outline=GREY)                 # the scoreboard
    g.text8(im, 92, 34, 'STRONKIE SOFT', RED); g.text8(im, 84, 48, 'WEIGHTLIFTING', YELLOW)
    g.ground(im, (0, 120, 320, 239), PAL, [(0, (18, 18, 30)), (0.6, (40, 40, 60)), (1, (70, 70, 90))], [DARK, SHADE, BLACK, METAL], spread=30)
    for x in range(40, 280, 8):                                   # a spotlight on the platform
        pass
    d.polygon([(40, 200), (280, 200), (300, 230), (20, 230)], fill=WOOD)       # the platform
    for x in range(40, 281, 24): d.line([x, 200, x - (x - 160) // 6, 230], fill=WOOD3)
    d.line([40, 200, 280, 200], fill=WOOD2); d.rectangle([20, 230, 300, 236], fill=WOOD3)
    d.rectangle([MET_X - 2, MET_Y - 2, MET_X + 17, MET_Y + MET_H + 1], fill=BLACK, outline=WHITE)
    g.text8(im, MET_X - 8, MET_Y + MET_H + 6, 'POWER', WHITE)
    d.rectangle([0, 239, 319, 255], fill=DARK); d.line([0, 240, 319, 240], fill=YELLOW)
    g.topbar_to_copper(im)
    return im

POSES = [   # 32x48 box, feet at 46; hands = the bar
    dict(head=(22, 20), neck=(19, 25), hip=(10, 30), lel=(20, 32), lha=(20, 38), rel=(20, 32), rha=(20, 38),
         lkn=(19, 34), lft=(14, 46), rkn=(19, 35), rft=(15, 46)),
    dict(head=(19, 8), neck=(18, 14), hip=(14, 27), lel=(17, 21), lha=(18, 27), rel=(17, 21), rha=(18, 27),
         lkn=(17, 36), lft=(14, 46), rkn=(18, 36), rft=(15, 46)),
    dict(head=(18, 16), neck=(17, 21), hip=(11, 33), lel=(24, 24), lha=(25, 18), rel=(24, 24), rha=(25, 18),
         lkn=(22, 36), lft=(14, 46), rkn=(22, 37), rft=(15, 46)),
    dict(head=(16, 6), neck=(16, 12), hip=(16, 26), lel=(23, 16), lha=(25, 11), rel=(23, 16), rha=(25, 11),
         lkn=(15, 36), lft=(14, 46), rkn=(17, 36), rft=(16, 46)),
    dict(head=(16, 10), neck=(16, 16), hip=(16, 29), lel=(17, 8), lha=(16, 1), rel=(17, 8), rha=(16, 1),
         lkn=(24, 36), lft=(26, 46), rkn=(9, 38), rft=(3, 46)),
    dict(head=(16, 6), neck=(16, 12), hip=(16, 26), lel=(17, 4), lha=(16, -3), rel=(17, 4), rha=(16, -3),
         lkn=(15, 36), lft=(13, 46), rkn=(17, 36), rft=(19, 46)),
    dict(head=(16, 6), neck=(16, 12), hip=(16, 26), lel=(11, 19), lha=(9, 26), rel=(21, 19), rha=(23, 26),
         lkn=(15, 36), lft=(14, 46), rkn=(17, 36), rft=(18, 46)),
]

def lifter(kit, woman, k):
    S = 1.5; W, H = 64, 80
    im = g.bob_canvas(W, H); d = ImageDraw.Draw(im)
    p = {n: (x, y + 6) for n, (x, y) in POSES[k].items()}               # (room above for the bar)
    a = g.athlete(p, w=int(32 * S) + 2, h=int(54 * S), woman=woman, kit=kit, scale=S)
    ox, oy = 8, H - a.size[1]
    hx, hy = p['rha'][0] * S + ox, p['rha'][1] * S + oy
    if k == 6: hx, hy = 30 + ox, 46 * S + oy - 9                        # dropped: on the floor
    def plates():
        d.ellipse([hx - 11, hy - 11, hx + 11, hy + 11], fill=PLATE, outline=BLACK)
        d.ellipse([hx - 7, hy - 7, hx + 7, hy + 7], outline=SHADE)
        d.ellipse([hx - 2, hy - 2, hx + 2, hy + 2], fill=METAL, outline=BLACK)
    if k == 6: plates()
    m = Image.fromarray(((np.array(a) != g.TRANSP) * 255).astype('uint8'), 'L'); im.paste(a, (ox, oy), m)
    if k != 6: plates()
    return im

def frames(kit, woman): return [lifter(kit, woman, k) for k in range(7)]

def sounds(o):
    R = 8000
    o.sample('snd_clang', g.tosamp(sum(np.sin(2 * np.pi * f * np.arange(int(0.5 * R)) / R) for f in (310, 470, 830)) * g.env(int(0.5 * R), 0.001, 0.12, R) + g.thump(int(0.5 * R), 90, 40, 0.06, R)), R)
    o.sample('snd_grunt', g.speak('h V', speed=0.8), 6000)
    o.sample('v_title', g.speak('w eI t l I f t I N'), 6000)

def main():
    o = g.Out(OUT, 'wgt')
    o.bobs('pm', frames(None, False)); o.bobs('pw', frames(None, True))
    sounds(o)
    o.raw(g.palette_line('pal_wgt', PAL))
    for k, v in (('LX', LX), ('LY', LY), ('MET_X', MET_X), ('MET_Y', MET_Y), ('MET_H', MET_H)): o.equ(k, v)
    n = o.write()
    bg = background()
    g.save_screen(bg, os.path.join(OUT, 'wgt_bg.rle'))
    g.preview(bg, PAL, os.path.join(OUT, 'preview_wgt.png'))
    fr = frames(None, False); pal = PAL + g.DEF_PLAYER
    sheet = Image.new('P', (64 * 7, 80), DARK)
    for i, f in enumerate(fr):
        m = Image.fromarray(((np.array(f) != g.TRANSP) * 255).astype('uint8'), 'L'); sheet.paste(f, (i * 64, 0), m)
    g.preview(sheet, pal, os.path.join(OUT, 'preview_wgt_men.png'), scale=3)
    print('weights: %d bytes chip' % n)

if __name__ == '__main__':
    main()
