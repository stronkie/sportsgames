#!/usr/bin/env python3
"""ev_swim.py - graphics and sounds of Swimming (50m freestyle) for Stronkie's Olympics.
Created By Mark Stronks, Stronkie Soft."""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gfxlib as g

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(g.ROOT, 'build', 'gen')
random.seed(91)
PAL = [0x112, 0x000, 0xfff, 0xfd0, 0xd22, 0x334, 0x446, 0xe55, 0xfd6, 0x5af, 0x18c, 0x3ad, 0x6cf, 0xbef, 0x9ab,
       0x889, 0x112, 0x777,
       0x321, 0xc96, 0xa74, 0xd22, 0x911, 0x222, 0x111]
(BG, BLACK, WHITE, YELLOW, RED, ST1, ST2, CR1, CR2, CR3, W1, W2, W3, FOAM, TILE, GREY, DARK, SHADE) = range(18)
RIVAL = dict(hair=18, skin=19, skind=20, shirt=21, shirtd=22, shorts=23, shoes=24)
START_X, FINISH_X = 24, 300
LANE_C, LANE_P = 172, 216

def background():
    im = Image.new('P', (320, 256), BG); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 319, 23], fill=DARK); d.line([0, 23, 319, 23], fill=YELLOW)
    for y in range(24, 110): d.line([0, y, 319, y], fill=ST1 if (y // 4) % 2 else ST2)
    for i in range(3000): d.point((random.randrange(320), random.randrange(25, 109)), fill=random.choice([CR1, CR2, CR3, WHITE, YELLOW]))
    d.rectangle([0, 110, 319, 124], fill=TILE); g.text8(im, 24, 113, 'STRONKIE SOFT', RED); g.text8(im, 152, 113, '50M', BLACK)
    d.rectangle([0, 125, 319, 239], fill=W2)
    for y in range(125, 238, 4):
        for x in range(random.randrange(8), 320, 18): d.line([x, y, x + 6, y], fill=random.choice([W1, W3, W2]))
    for y in (128, 184, 232):                                  # lane ropes
        for x in range(0, 320, 6): d.rectangle([x, y, x + 3, y + 2], fill=RED if (x // 6) % 4 == 0 else WHITE)
    d.rectangle([0, 125, START_X - 6, 238], fill=TILE)            # the walls and the blocks
    d.rectangle([FINISH_X + 2, 125, 319, 238], fill=TILE)
    for y in (LANE_C - 10, LANE_P - 10): d.rectangle([START_X - 14, y - 2, START_X - 2, y + 4], fill=WHITE, outline=BLACK)
    d.rectangle([0, 239, 319, 255], fill=DARK); d.line([0, 240, 319, 240], fill=YELLOW)
    return im

def swimmer(kit, woman, phase=None, block=False, dive=False):
    k = dict(hair=g.HAIR, skin=g.SKIN, skind=g.SKIND, shirt=g.SHIRT, shirtd=g.SHIRTD, shorts=g.SHORTS, shoes=g.SHOES)
    if kit: k.update(kit)
    im = g.bob_canvas(48, 48); d = ImageDraw.Draw(im)
    if block:
        p = dict(head=(26, 18), neck=(22, 20), hip=(12, 22), lel=(24, 28), lha=(27, 33), rel=(23, 28), rha=(26, 33),
                 lkn=(17, 30), lft=(14, 36), rkn=(15, 30), rft=(12, 36))
        a = g.athlete(p, woman=woman, kit=kit)
        m = Image.fromarray(((np.array(a) != g.TRANSP) * 255).astype('uint8'), 'L'); im.paste(a, (6, 0), m)
        return im
    wy = 40                                                       # the water line
    if dive:
        d.line([4, 30, 40, 30], fill=BLACK, width=6); d.line([5, 30, 39, 30], fill=k['skin'], width=4)
        d.line([12, 30, 26, 30], fill=k['shorts'], width=4); d.ellipse([38, 26, 46, 33], fill=k['shirt'], outline=BLACK)
        return im
    # the body in the water, head with a cap (shirt colour), arms going round
    d.ellipse([6, wy - 4, 38, wy + 3], fill=k['skind'], outline=BLACK)
    d.ellipse([10, wy - 3, 22, wy + 2], fill=k['shorts'])
    d.ellipse([34, wy - 6, 43, wy + 2], fill=k['shirt'], outline=BLACK); d.point((41, wy - 2), fill=BLACK)
    for arm, ph in ((0, phase), (1, phase + 3)):
        a = math.radians((ph % 6) * 60 + 20)
        sx, sy = 32, wy - 1
        ex, ey = sx + 14 * math.cos(a), sy - 14 * math.sin(a)
        if ey < wy + 2:
            d.line([sx, sy, ex, ey], fill=BLACK, width=4); d.line([sx, sy, ex, ey], fill=k['skin'], width=2)
    for i in range(6):                                            # splashes
        x = random.Random(phase * 7 + i).randrange(4, 44); d.ellipse([x - 1, wy - 2, x + 1, wy], fill=FOAM)
    d.line([4, wy + 1, 2, wy - 1], fill=FOAM); d.line([2, wy + 2, 0, wy], fill=FOAM)
    return im

def frames(kit, woman):
    return [swimmer(kit, woman, i) for i in range(6)] + [swimmer(kit, woman, block=True), swimmer(kit, woman, dive=True)]

def sounds(o):
    R = 8000
    o.sample('snd_splash', g.tosamp(g.bandnoise(int(0.6 * R), 2, 20, 5) * g.env(int(0.6 * R), 0.01, 0.2, R)), R)
    o.sample('snd_stroke', g.tosamp(g.bandnoise(int(0.12 * R), 3, 20, 6) * g.env(int(0.12 * R), 0.005, 0.04, R)), R)
    o.sample('snd_gasp', g.tosamp(g.bandnoise(int(0.3 * R), 1, 6, 8) * np.sin(np.linspace(0, np.pi, int(0.3 * R)))), R)
    o.sample('v_title', g.speak('s w I m I N'), 6000)
    o.sample('snd_gun', g.tosamp(g.noise(int(0.35 * R), 3) * g.env(int(0.35 * R), 0.001, 0.06, R) + g.thump(int(0.35 * R), 160, 60, 0.05, R)), R)

def main():
    o = g.Out(OUT, 'swi')
    o.bobs('pm', frames(None, False)); o.bobs('pw', frames(None, True))
    o.bobs('cm', frames(RIVAL, False)); o.bobs('cw', frames(RIVAL, True))
    sounds(o)
    o.raw(g.palette_line('pal_race', PAL))
    o.equ('START_X', START_X); o.equ('FINISH_X', FINISH_X); o.equ('LANE_C', LANE_C); o.equ('LANE_P', LANE_P)
    n = o.write()
    bg = background()
    g.save_screen(bg, os.path.join(OUT, 'swi_bg.rle'))
    g.preview(bg, PAL, os.path.join(OUT, 'preview_swi.png'))
    print('swimming: %d bytes chip' % n)

if __name__ == '__main__':
    main()
