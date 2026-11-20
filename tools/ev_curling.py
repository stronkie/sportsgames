#!/usr/bin/env python3
"""ev_curling.py - graphics and sounds of Penguin Curling for Stronkie's Olympics: the ice
seen from above, the house, the penguins.  Created By Mark Stronks, Stronkie Soft."""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gfxlib as g

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(g.ROOT, 'build', 'gen')
random.seed(66)
PAL = [0x112, 0x000, 0xfff, 0xfd0, 0xd22, 0x334, 0x446, 0xe55, 0xfd6, 0x5af, 0xdef, 0xbdf, 0x9bd, 0x24c, 0xc22,
       0x889, 0x112, 0x777, 0xf80, 0x222, 0x444, 0x000, 0x000, 0x000, 0x000]
(BG, BLACK, WHITE, YELLOW, RED, ST1, ST2, CR1, CR2, CR3, ICE, ICE2, ICE3, BLUE, RED2, GREY, DARK, SHADE,
 BEAK, PBLACK, PGREY) = range(21)
X_START, Y_MID, HX, HY = 24, 180, 270, 180     # the penguin starts at X_START; the house's button: HX, HY
POW_X, POW_Y = 128, 113

def background():
    im = Image.new('P', (320, 256), BG); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 319, 23], fill=DARK); d.line([0, 23, 319, 23], fill=YELLOW)
    g.stands(im, 24, 112, PAL, seed=71)
    d.rectangle([0, 112, 319, 121], fill=GREY); g.text8(im, 8, 113, 'STRONKIE', RED); g.text8(im, 80, 113, 'POWER', BLACK)
    g.text8(im, 240, 113, 'CURLING', BLACK)
    g.ground(im, (0, 122, 320, 238), PAL, [(0, (190, 215, 235)), (1, (235, 245, 255))], [ICE, ICE2, ICE3, WHITE], noise=6, spread=24)
    d.rectangle([0, 122, 319, 123], fill=BLUE); d.rectangle([0, 236, 319, 237], fill=BLUE)
    for r, c in ((40, BLUE), (30, WHITE), (20, RED2), (10, WHITE)):
        d.ellipse([HX - r, HY - r, HX + r, HY + r], fill=c, outline=ICE3)
    d.ellipse([HX - 2, HY - 2, HX + 2, HY + 2], fill=BLUE)
    d.line([HX, 124, HX, 235], fill=ICE3); d.line([0, HY, 319, HY], fill=ICE2)
    d.line([X_START + 40, 124, X_START + 40, 235], fill=RED2); d.line([HX - 70, 124, HX - 70, 235], fill=RED2)   # hog lines
    d.rectangle([0, 238, 319, 255], fill=DARK); d.line([0, 240, 319, 240], fill=YELLOW)
    g.topbar_to_copper(im)
    return im

def penguin(k):
    """from above, sliding on its belly to the right: k 0/1 the flippers, 2 standing"""
    im = g.bob_canvas(16, 16); d = ImageDraw.Draw(im)
    if k < 2:
        f = 2 if k else 0
        d.polygon([(4, 3 - f), (8, 6), (5, 7)], fill=PBLACK); d.polygon([(4, 12 + f), (8, 9), (5, 8)], fill=PBLACK)   # flippers
        d.ellipse([1, 4, 13, 11], fill=PBLACK, outline=BLACK)
        d.ellipse([9, 5, 14, 10], fill=PBLACK, outline=BLACK); d.point((12, 6), fill=WHITE); d.point((12, 9), fill=WHITE)
        d.polygon([(14, 7), (15, 7), (14, 8)], fill=BEAK); d.line([0, 6, 1, 6], fill=BEAK); d.line([0, 9, 1, 9], fill=BEAK)
    else:
        d.ellipse([3, 2, 12, 14], fill=PBLACK, outline=BLACK); d.ellipse([5, 5, 10, 13], fill=WHITE)
        d.point((6, 4), fill=WHITE); d.point((9, 4), fill=WHITE); d.polygon([(7, 5), (8, 5), (7, 7)], fill=BEAK)
    return im

def marker():
    im = g.bob_canvas(16, 16); d = ImageDraw.Draw(im)
    d.line([7, 1, 7, 13], fill=BLACK); d.line([1, 7, 13, 7], fill=BLACK); d.ellipse([4, 4, 10, 10], outline=YELLOW)
    return im

def sounds(o):
    R = 8000
    o.sample('snd_swish', g.tosamp(g.bandnoise(int(0.12 * R), 8, 40, 6) * g.env(int(0.12 * R), 0.01, 0.04, R) * 0.7), R)
    o.sample('snd_slide', g.tosamp(g.bandnoise(int(0.4 * R), 2, 10, 2) * g.env(int(0.4 * R), 0.05, 0.2, R) * 0.6), R)
    t = np.arange(int(0.25 * R)) / R
    o.sample('snd_squawk', g.tosamp(np.sign(np.sin(2 * np.pi * (700 + 500 * np.sin(2 * np.pi * 12 * t)) * t)) * 0.4 * np.exp(-t / 0.1)), R)
    o.sample('v_title', g.speak('p e N g w I n k @ r l I N'), 6000)

def main():
    o = g.Out(OUT, 'cur')
    o.bobs('pg', [penguin(k) for k in range(3)]); o.bob('marker', marker())
    sounds(o)
    o.raw(g.palette_line('pal_cur', PAL))
    for k, v in (('X_START', X_START), ('Y_MID', Y_MID), ('HX', HX), ('HY', HY), ('POW_X', POW_X), ('POW_Y', POW_Y)): o.equ(k, v)
    n = o.write()
    bg = background()
    g.save_screen(bg, os.path.join(OUT, 'cur_bg.rle'))
    g.preview(bg, PAL, os.path.join(OUT, 'preview_cur.png'))
    print('curling: %d bytes chip' % n)

if __name__ == '__main__':
    main()
