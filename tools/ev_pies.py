#!/usr/bin/env python3
"""ev_pies.py - graphics and sounds of Pie Dodge for Stronkie's Olympics: the arena seen from
above, the clowns, the pies, you.  Created By Mark Stronks, Stronkie Soft."""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gfxlib as g

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(g.ROOT, 'build', 'gen')
random.seed(44)
PAL = [0x112, 0x000, 0xfff, 0xfd0, 0xd22, 0x334, 0x446, 0xe55, 0xfd6, 0x5af, 0xdb7, 0xca6, 0xb95, 0x2a2, 0x4c4,
       0x889, 0x112, 0x777, 0xfee, 0xc84, 0xe6c, 0x36d, 0xf90, 0x000, 0x000]
(BG, BLACK, WHITE, YELLOW, RED, ST1, ST2, CR1, CR2, CR3, SAND, SAND2, SAND3, GREEN, GREEN2, GREY, DARK, SHADE,
 CREAM, CRUST, PINK, BLUE, ORANGE) = range(23)
X0, X1, Y0, Y1 = 8, 296, 40, 216        # where you can walk (the bob's top left)
ZL, ZR = 24, 280                         # the safe zones: left of ZL, right of ZR

def clown(d, x, y, up):
    d.ellipse([x - 7, y - 5, x + 7, y + 5], fill=[BLUE, PINK, ORANGE][(x // 12) % 3], outline=BLACK)       # body (from above)
    d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=WHITE, outline=BLACK)                              # the face
    d.ellipse([x - 2, y - 7 if up else y + 3, x + 2, y - 3 if up else y + 7], fill=RED)           # the hair / nose
    d.point((x - 1, y), fill=RED); d.point((x + 1, y), fill=RED)

def background():
    im = Image.new('P', (320, 256), BG); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 319, 23], fill=DARK); d.line([0, 23, 319, 23], fill=YELLOW)
    g.paint(im, 0, 24, g.stands_rgb(320, 16, seed=81, roof=False), PAL, None, 20)
    g.paint(im, 0, 232, g.stands_rgb(320, 8, seed=82, roof=False), PAL, None, 20)
    g.ground(im, (0, 40, 320, 232), PAL, [(0, (200, 170, 110)), (0.5, (225, 195, 130)), (1, (205, 175, 115))], [SAND, SAND2, SAND3], noise=9)
    g.ground(im, (0, 40, ZL + 8, 232), PAL, [(0, (40, 140, 50)), (1, (70, 190, 80))], [GREEN, GREEN2], stripes=(6, (10, 14, 6)))
    g.ground(im, (ZR + 9, 40, 320, 232), PAL, [(0, (40, 140, 50)), (1, (70, 190, 80))], [GREEN, GREEN2], stripes=(6, (10, 14, 6)))
    for r in range(70, 4, -6):                                      # the circus ring in the middle
        pass
    for y in range(44, 231, 12): d.line([ZL + 7, y, ZL + 7, y + 6], fill=WHITE); d.line([ZR + 9, y, ZR + 9, y + 6], fill=WHITE)
    g.text8(im, 120, 128, 'PIE DODGE', SAND3); g.text8(im, 112, 140, 'STRONKIE SOFT', SAND3)
    for x in range(44, 290, 24): clown(d, x, 32, False); clown(d, x + 12, 236, True)
    d.rectangle([0, 241, 319, 255], fill=DARK); d.line([0, 240, 319, 240], fill=YELLOW)
    g.topbar_to_copper(im)
    return im

def walker(kit, k):
    """you from above: k 0-3 walking, 4 with a pie in the face"""
    k_ = dict(hair=g.HAIR, skin=g.SKIN, shirt=g.SHIRT, shirtd=g.SHIRTD, shoes=g.SHOES)
    im = g.bob_canvas(16, 16); d = ImageDraw.Draw(im)
    s = [3, 0, -3, 0][k % 4] if k < 4 else 0
    d.ellipse([3, 6 + s, 6, 10 + s], fill=k_['shoes']); d.ellipse([9, 6 - s, 12, 10 - s], fill=k_['shoes'])   # the feet
    d.ellipse([1, 3, 14, 12], fill=k_['shirt'], outline=BLACK)                                          # the shoulders
    d.ellipse([0, 6 - s, 3, 10 - s], fill=k_['skin']); d.ellipse([12, 6 + s, 15, 10 + s], fill=k_['skin'])
    d.ellipse([4, 4, 11, 11], fill=k_['hair'], outline=BLACK)                                            # the head
    if k == 4:
        d.ellipse([2, 2, 13, 13], fill=CREAM, outline=BLACK); d.point((5, 5), fill=PINK); d.point((10, 9), fill=PINK)
    return im

def pie(k):
    im = g.bob_canvas(16, 12); d = ImageDraw.Draw(im)
    d.ellipse([2, 1, 13, 10], fill=CRUST, outline=BLACK); d.ellipse([4, 2, 11, 8], fill=CREAM)
    d.point((7 + k, 5), fill=RED)
    return im

def sounds(o):
    R = 8000
    o.sample('snd_splat', g.tosamp(g.bandnoise(int(0.3 * R), 1, 12, 4) * g.env(int(0.3 * R), 0.002, 0.08, R) + g.thump(int(0.3 * R), 150, 60, 0.03, R)), R)
    t = np.arange(int(0.2 * R)) / R
    o.sample('snd_honk', g.tosamp(np.sign(np.sin(2 * np.pi * 340 * t)) * 0.5 * np.exp(-t / 0.12)), R)
    o.sample('snd_ding', g.tosamp(np.sin(2 * np.pi * 1320 * t) * np.exp(-t / 0.08)), R)
    o.sample('v_title', g.speak('p aI d o d j'), 6000)

def main():
    o = g.Out(OUT, 'pie')
    o.bobs('pw', [walker(None, k) for k in range(5)]); o.bobs('pi', [pie(k) for k in range(2)])
    sounds(o)
    o.raw(g.palette_line('pal_pie', PAL))
    for k, v in (('X0', X0), ('X1', X1), ('Y0', Y0), ('Y1', Y1), ('ZL', ZL), ('ZR', ZR)): o.equ(k, v)
    n = o.write()
    bg = background()
    g.save_screen(bg, os.path.join(OUT, 'pie_bg.rle'))
    g.preview(bg, PAL, os.path.join(OUT, 'preview_pie.png'))
    print('pie dodge: %d bytes chip' % n)

if __name__ == '__main__':
    main()
