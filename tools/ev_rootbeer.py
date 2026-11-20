#!/usr/bin/env python3
"""ev_rootbeer.py - graphics and sounds of the Root Beer Sprint (drink, run, don't hiccup) for
Stronkie's Olympics: the sprint track with a table and a mug.  Created By Mark Stronks, Stronkie Soft."""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gfxlib as g
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(g.ROOT, 'build', 'gen')
sys.argv = sys.argv[:2]
import ev_sprint as sp

PAL = list(sp.PAL)
PAL[14] = 0x962                       # (the second grass colour becomes root beer brown)
FOAM, BEER = sp.WHITE, 14
(BG, BLACK, WHITE, YELLOW, RED, GREY, DARK) = (sp.BG, sp.BLACK, sp.WHITE, sp.YELLOW, sp.RED, sp.GREY, sp.DARK)
MUG_X, HIC_X, BAR_Y = 64, 184, 113

def background():
    im = sp.background(); d = ImageDraw.Draw(im)
    d.rectangle([0, 112, 319, 121], fill=GREY)                     # the strip: MUG and HIC meters
    g.text8(im, 32, 113, 'MUG', BLACK); g.text8(im, 152, 113, 'HIC', BLACK); g.text8(im, 256, 113, 'BURP', RED)
    for lane in (sp.LANE_C, sp.LANE_P):                          # the tables at the start
        x = 0; y = lane - 18
        d.rectangle([x, y, x + 12, y + 2], fill=sp.SHADE, outline=BLACK)
        d.line([x + 2, y + 3, x + 2, lane], fill=BLACK); d.line([x + 10, y + 3, x + 10, lane], fill=BLACK)
    return im

def mug_in(d, x, y, tilt):
    """a mug at x, y (its top left), tilted (0 upright, 1 drinking)"""
    if tilt:
        d.polygon([(x, y), (x + 6, y - 3), (x + 9, y + 2), (x + 3, y + 5)], fill=BEER, outline=BLACK)
        d.line([x + 6, y - 3, x + 9, y + 2], fill=FOAM)
    else:
        d.rectangle([x, y, x + 5, y + 7], fill=BEER, outline=BLACK); d.line([x + 1, y + 1, x + 4, y + 1], fill=FOAM)
        d.line([x + 6, y + 2, x + 7, y + 5], fill=BLACK)

def drinker(kit, woman, kind):
    """kind 0: ready with the mug, 1: drinking, 2: hiccup"""
    im = g.bob_canvas(32, 48); d = ImageDraw.Draw(im)
    p = g.pose_stand()
    if kind == 0:
        p.update(rel=(21, 18), rha=(24, 22))
    elif kind == 1:
        p.update(head=(14, 6), neck=(15, 12), rel=(21, 15), rha=(20, 9))
    else:
        p.update(head=(16, 3), neck=(16, 10), hip=(16, 25), lel=(10, 15), lha=(8, 11), rel=(22, 15), rha=(24, 11),
                 lkn=(14, 35), lft=(14, 43), rkn=(18, 35), rft=(18, 43))
    a = g.athlete(p, woman=woman, kit=kit)
    m = Image.fromarray(((np.array(a) != g.TRANSP) * 255).astype('uint8'), 'L'); im.paste(a, (0, 0), m)
    if kind == 0: mug_in(d, 23, 18, 0)
    if kind == 1: mug_in(d, 17, 5, 1)
    if kind == 2:
        d.ellipse([22, 0, 26, 4], fill=FOAM, outline=BLACK); d.ellipse([27, 4, 30, 7], fill=FOAM)   # bubbles
    return im

def frames(kit, woman):
    run = [g.athlete(q, woman=woman, kit=kit) for q in g.run_cycle(6, lean=3)]
    return run + [drinker(kit, woman, k) for k in range(3)]

def sounds(o):
    R = 8000
    o.sample('snd_gun', g.tosamp(g.noise(int(0.35 * R), 3) * g.env(int(0.35 * R), 0.001, 0.06, R) + g.thump(int(0.35 * R), 160, 60, 0.05, R)), R)
    o.sample('snd_gulp', g.tosamp(g.thump(int(0.12 * R), 180, 70, 0.04, R) * 0.8), R)
    o.sample('snd_hic', g.speak('h I k', speed=1.4), 6000)
    t = np.arange(int(0.6 * R)) / R
    f = 70 + 20 * np.sin(2 * np.pi * 9 * t)
    burp = np.sign(np.sin(2 * np.pi * np.cumsum(f) / R)) * 0.5 + g.bandnoise(len(t), 1, 8, 3) * 0.6
    o.sample('snd_burp', g.tosamp(burp * g.env(len(t), 0.02, 0.25, R)), R)
    o.sample('v_title', g.speak('r u t b I @ r s p r I n t'), 6000)

def main():
    o = g.Out(OUT, 'rbr')
    o.bobs('pm', frames(None, False)); o.bobs('pw', frames(None, True))
    o.bobs('cm', frames(sp.RIVAL, False)); o.bobs('cw', frames(sp.RIVAL, True))
    sounds(o)
    o.raw(g.palette_line('pal_race', PAL))
    for k, v in (('START_X', sp.START_X), ('FINISH_X', sp.FINISH_X), ('LANE_C', sp.LANE_C), ('LANE_P', sp.LANE_P),
                 ('MUG_X', MUG_X), ('HIC_X', HIC_X), ('BAR_Y', BAR_Y)):
        o.equ(k, v)
    n = o.write()
    bg = background()
    g.save_screen(bg, os.path.join(OUT, 'rbr_bg.rle'))
    g.preview(bg, PAL, os.path.join(OUT, 'preview_rbr.png'))
    fr = frames(None, False); pal = PAL + g.DEF_PLAYER
    sheet = Image.new('P', (32 * 9, 48), sp.TRACK)
    for i, f in enumerate(fr):
        m = Image.fromarray(((np.array(f) != g.TRANSP) * 255).astype('uint8'), 'L'); sheet.paste(f, (i * 32, 0), m)
    g.preview(sheet, pal, os.path.join(OUT, 'preview_rbr_men.png'), scale=4)
    print('root beer: %d bytes chip' % n)

if __name__ == '__main__':
    main()
