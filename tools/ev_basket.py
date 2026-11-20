#!/usr/bin/env python3
"""ev_basket.py - graphics and sounds of the Basketball event (three point shoot-out).
Created By Mark Stronks, Stronkie Soft."""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gfxlib as g

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(g.ROOT, 'build', 'gen')
random.seed(21)
PAL = [0x113, 0x000, 0xfff, 0xfd0, 0xd22, 0xdb7, 0xc95, 0x963, 0xe72, 0x842,
       0x2c3, 0x36b, 0xccd, 0x223, 0xe55, 0x58d, 0xec4, 0xddd, 0x6b6, 0xaab,
       0x161, 0x334, 0x445, 0x88a, 0x531]
(BG, BLACK, WHITE, YELLOW, RED, FL1, FL2, FL3, BALL, BALLD, GREEN, KEY, BOARD, STAND, CR1, CR2, CR3, CR4, CR5, NET,
 DGREEN, WALL, WALL2, GREY, POLE) = range(25)
FLOOR_Y = 206
RIM_X, RIM_Y = 262, 98          # the middle of the rim
SPOTS = [52, 80, 108, 80, 52]   # where the player stands (left edge of the 32 wide frame)

def background():
    im = Image.new('P', (320, 256), BG); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 319, 23], fill=BG); d.line([0, 23, 319, 23], fill=YELLOW)
    for y in range(24, 120):                                  # stands
        d.line([0, y, 319, y], fill=STAND if (y // 5) % 2 else WALL)
    for i in range(3000):
        d.point((random.randrange(320), random.randrange(25, 118)), fill=random.choice([CR1, CR2, CR3, CR4, CR5, WHITE, YELLOW, RED]))
    d.rectangle([0, 118, 319, 150], fill=WALL2)
    d.rectangle([0, 118, 319, 121], fill=GREY)
    g.text8(im, 56, 130, 'STRONKIE SOFT', YELLOW); g.text8(im, 176, 130, 'AMIGA 500', WHITE)
    # the floor: planks in perspective
    for y in range(150, 240):
        k = (y - 150) / 90
        d.line([0, y, 319, y], fill=FL1 if (y // 3) % 2 else FL2)
    for x in range(-200, 330, 18):
        d.line([x, 240, x + 60, 150], fill=FL3)
    d.line([0, 150, 319, 150], fill=FL3)
    # the key (painted) and the three point line
    d.polygon([(200, 240), (319, 240), (319, 180), (246, 180)], fill=KEY)
    d.line([200, 240, 246, 180], fill=WHITE); d.line([246, 180, 319, 180], fill=WHITE)
    d.line([60, 240, 150, 160], fill=WHITE)
    # the hoop: pole, arm, board, rim (the front of the rim and the net are a bob)
    d.rectangle([300, 92, 305, FLOOR_Y], fill=POLE); d.rectangle([298, FLOOR_Y - 4, 309, FLOOR_Y + 2], fill=BLACK)
    d.rectangle([282, 88, 300, 92], fill=POLE)
    d.rectangle([276, 60, 282, 104], fill=BOARD, outline=GREY)
    d.rectangle([277, 80, 281, 96], outline=RED)
    d.line([RIM_X - 10, RIM_Y, RIM_X + 12, RIM_Y], fill=RED)
    # the meter frame (left) and the bottom bar
    d.rectangle([14, 58, 33, 162], fill=BLACK, outline=WHITE)
    d.rectangle([0, 240, 319, 255], fill=BG); d.line([0, 240, 319, 240], fill=YELLOW)
    return im

def rim_front():
    im = g.bob_canvas(32, 22); d = ImageDraw.Draw(im)
    for i in range(6):
        d.line([4 + i * 4, 2, 7 + i * 3, 20], fill=NET)
    d.line([6, 20, 22, 20], fill=NET)
    d.line([0, 1, 26, 1], fill=RED); d.line([0, 2, 26, 2], fill=RED)
    return im

def ball(r=4, money=False):
    im = g.bob_canvas(12, 12); d = ImageDraw.Draw(im)
    d.ellipse([1, 1, 2 * r + 2, 2 * r + 2], fill=BLACK)
    d.ellipse([2, 2, 2 * r + 1, 2 * r + 1], fill=RED if money else BALL)
    if money: d.line([2, r + 1, 2 * r + 1, r + 1], fill=WHITE); d.line([r + 1, 2, r + 1, 2 * r + 1], fill=WHITE)
    else: d.line([2, r + 1, 2 * r + 1, r + 1], fill=BALLD); d.line([r + 1, 2, r + 1, 2 * r + 1], fill=BALLD)
    return im

def player_frames(woman):
    st = dict(head=(17, 7), neck=(16, 13), hip=(15, 27), lel=(20, 18), lha=(24, 16), rel=(21, 20), rha=(24, 17),
              lkn=(16, 37), lft=(14, 46), rkn=(19, 37), rft=(19, 46))
    crouch = dict(head=(18, 11), neck=(17, 17), hip=(14, 30), lel=(21, 21), lha=(24, 19), rel=(22, 23), rha=(24, 20),
                  lkn=(20, 37), lft=(14, 46), rkn=(22, 38), rft=(19, 46))
    shoot = dict(head=(17, 6), neck=(16, 12), hip=(15, 25), lel=(20, 7), lha=(21, 1), rel=(21, 8), rha=(23, 1),
                 lkn=(15, 35), lft=(13, 42), rkn=(18, 35), rft=(18, 42))
    after = dict(shoot); after.update(lel=(21, 8), lha=(26, 4), rel=(22, 9), rha=(27, 5))
    frames = [g.athlete(p, woman=woman) for p in (st, crouch, shoot, after)]
    frames += [g.athlete(p, woman=woman) for p in g.run_cycle(4, lean=1)]
    # a ball in the hands of the first two
    out = []
    for i, f in enumerate(frames):
        if i in (0, 1):
            d = ImageDraw.Draw(f); y = 14 if i == 0 else 17
            d.ellipse([22, y, 30, y + 8], fill=BLACK); d.ellipse([23, y + 1, 29, y + 7], fill=BALL); d.line([23, y + 4, 29, y + 4], fill=BALLD)
        if i == 2:
            d = ImageDraw.Draw(f)
            d.ellipse([18, 0, 26, 7], fill=BLACK); d.ellipse([19, 0, 25, 6], fill=BALL)
        out.append(f)
    return out

def sounds(o):
    R = 8000
    n = int(0.35 * R)
    o.sample('snd_swish', g.tosamp(g.bandnoise(n, 1, 6, 5) * np.sin(np.linspace(0, np.pi, n)) ** 2), R)
    t = np.arange(int(0.3 * R)) / R
    clank = (np.sin(2 * np.pi * 620 * t) + 0.7 * np.sin(2 * np.pi * 1310 * t) + 0.4 * np.sin(2 * np.pi * 2250 * t)) * np.exp(-t / 0.07)
    o.sample('snd_rim', g.tosamp(clank), R)
    o.sample('snd_bounce', g.tosamp(g.thump(int(0.12 * R), 140, 70, 0.03, R)), R)
    o.sample('snd_board', g.tosamp(g.thump(int(0.15 * R), 220, 160, 0.04, R) + g.noise(int(0.15 * R), 2) * g.env(int(0.15 * R), 0.001, 0.02, R) * 0.4), R)
    o.sample('snd_horn', g.tosamp(g.beep(233, 0.8, R) + g.beep(311, 0.8, R) * 0.7), R)
    V = 6000
    o.sample('v_basket', g.speak('b ae s k I t b o l'), V)
    o.sample('v_money', g.speak('m V n i'), V)
    o.sample('v_swish', g.speak('s w I S'), V)

def main():
    o = g.Out(OUT, 'bas')
    o.bobs('pm', player_frames(False)); o.bobs('pw', player_frames(True))
    o.bob('ball_n', ball()); o.bob('ball_m', ball(money=True))
    o.bob('rimfront', rim_front())
    sounds(o)
    o.raw(g.palette_line('pal_bas', PAL))
    o.raw('spots\tdc.w\t' + ','.join(str(x) for x in SPOTS))
    o.equ('FLOOR_Y', FLOOR_Y); o.equ('RIM_X', RIM_X); o.equ('RIM_Y', RIM_Y)
    n = o.write()
    bg = background()
    g.save_screen(bg, os.path.join(OUT, 'bas_bg.rle'))
    g.preview(bg, PAL, os.path.join(OUT, 'preview_bas.png'))
    sheet = Image.new('P', (320, 56), BG)
    for i, im in enumerate(player_frames(False)):
        a = np.array(im); a[a == g.TRANSP] = BG; sheet.paste(Image.fromarray(a, 'P'), (i * 36, 4))
    g.preview(sheet, PAL, os.path.join(OUT, 'preview_bas_bobs.png'), 3)
    print('basketball: %d bytes chip' % n)

if __name__ == '__main__':
    main()
