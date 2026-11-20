#!/usr/bin/env python3
"""ev_archery.py - graphics and sounds of Archery for Stronkie's Olympics: the target, the sight,
the arrows.  Created By Mark Stronks, Stronkie Soft."""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gfxlib as g

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(g.ROOT, 'build', 'gen')
random.seed(12)
PAL = [0x112, 0x000, 0xfff, 0xfd0, 0xd22, 0x334, 0x446, 0xe55, 0xfd6, 0x5af, 0x6ae, 0x8cf, 0x2a2, 0x383, 0x4a4,
       0x889, 0x112, 0x777, 0x37d, 0xb21, 0xa75, 0xcb9, 0x642, 0x000, 0x000]
(BG, BLACK, WHITE, YELLOW, RED, ST1, ST2, CR1, CR2, CR3, SKY, SKY2, GRASS, GRASS2, GRASS3, GREY, DARK, SHADE,
 BLUE, RED2, WOOD, STRAW, WOOD2) = range(23)
CX, CY, RING = 160, 132, 7          # the target: centre, ring width (10 rings)

def background():
    im = Image.new('P', (320, 256), BG); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 319, 23], fill=DARK); d.line([0, 23, 319, 23], fill=YELLOW)
    g.ground(im, (0, 24, 320, 64), PAL, [(0, (90, 150, 230)), (1, (170, 215, 250))], [SKY, SKY2, WHITE], spread=40)
    for cx, cy in ((60, 36), (210, 30), (290, 44)):                 # clouds
        for k in range(5): d.ellipse([cx + k * 6 - 10, cy - 4 + (k % 2) * 2, cx + k * 6 + 6, cy + 5], fill=WHITE)
    g.paint(im, 0, 64, g.stands_rgb(320, 28, seed=51, roof=False), PAL, None, 20)
    g.ad_boards(im, 92, PAL, ['ARCHERY'] + g.SPONSORS, seed=6)
    g.ground(im, (0, 102, 320, 239), PAL, [(0, (40, 110, 45)), (1, (85, 180, 80))], [GRASS, GRASS2, GRASS3], stripes=(16, (12, 16, 6)))
    d.polygon([(CX - 50, 230), (CX - 30, CY), (CX + 30, CY), (CX + 50, 230)], fill=WOOD2)       # the stand
    d.line([CX - 50, 230, CX - 30, CY], fill=WOOD, width=4); d.line([CX + 50, 230, CX + 30, CY], fill=WOOD, width=4)
    d.ellipse([CX - 76, CY - 76, CX + 76, CY + 76], fill=STRAW, outline=WOOD2)
    cols = [WHITE, WHITE, BLACK, BLACK, BLUE, BLUE, RED2, RED2, YELLOW, YELLOW]
    for k in range(10):
        r = (10 - k) * RING
        d.ellipse([CX - r, CY - r, CX + r, CY + r], fill=cols[k], outline=BLACK if cols[k] != BLACK else WHITE)
    d.line([CX - 1, CY, CX + 1, CY], fill=BLACK); d.line([CX, CY - 1, CX, CY + 1], fill=BLACK)
    d.rectangle([0, 239, 319, 255], fill=DARK); d.line([0, 240, 319, 240], fill=YELLOW)
    g.topbar_to_copper(im)
    return im

def sight():
    im = g.bob_canvas(16, 16); d = ImageDraw.Draw(im)
    d.ellipse([1, 1, 14, 14], outline=BLACK); d.ellipse([2, 2, 13, 13], outline=WHITE)
    for a, b in (((7, 0), (7, 5)), ((7, 10), (7, 15)), ((0, 7), (5, 7)), ((10, 7), (15, 7))): d.line([a, b], fill=RED)
    return im

def arrow():
    """an arrow in the target, seen from the front-left: the shaft and the feathers"""
    im = g.bob_canvas(16, 12); d = ImageDraw.Draw(im)
    d.line([0, 0, 6, 6], fill=WOOD, width=1); d.line([1, 0, 7, 6], fill=WOOD2)
    d.line([0, 2, 2, 0], fill=RED); d.line([0, 3, 3, 0], fill=RED)
    d.point((7, 7), fill=BLACK)
    return im

def flying(k):
    """the arrow on its way, getting smaller"""
    s = [10, 8, 6, 4][k]
    im = g.bob_canvas(16, 16); d = ImageDraw.Draw(im)
    d.line([8 - s // 2, 8 - s // 2, 8 + s // 2, 8 + s // 2], fill=WOOD, width=2 if s > 6 else 1)
    d.line([8 - s // 2, 8 - s // 2 + 2, 8 - s // 2 + 2, 8 - s // 2], fill=RED)
    return im

def sounds(o):
    R = 8000
    t = np.arange(int(0.3 * R)) / R
    o.sample('snd_twang', g.tosamp(np.sin(2 * np.pi * (180 - 60 * t) * t) * np.exp(-t / 0.08) + g.noise(len(t), 3) * np.exp(-t / 0.01) * 0.5), R)
    o.sample('snd_thunk', g.tosamp(g.thump(int(0.15 * R), 220, 90, 0.03, R) + g.noise(int(0.15 * R), 9) * g.env(int(0.15 * R), 0.001, 0.02, R) * 0.5), R)
    o.sample('v_title', g.speak('a r t S @ r i'), 6000)

def main():
    o = g.Out(OUT, 'arc')
    o.bob('sight', sight()); o.bob('arrow', arrow()); o.bobs('fly', [flying(k) for k in range(4)])
    sounds(o)
    o.raw(g.palette_line('pal_arc', PAL))
    for k, v in (('CX', CX), ('CY', CY), ('RING', RING)): o.equ(k, v)
    n = o.write()
    bg = background()
    g.save_screen(bg, os.path.join(OUT, 'arc_bg.rle'))
    g.preview(bg, PAL, os.path.join(OUT, 'preview_arc.png'))
    print('archery: %d bytes chip' % n)

if __name__ == '__main__':
    main()
