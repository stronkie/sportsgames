#!/usr/bin/env python3
"""ev_field.py - graphics and sounds of the field events of Stronkie's Olympics:
python3 tools/ev_field.py build/gen longjump|javelin|tp
  longjump: the runway, the board and the sand pit (one screen)
  javelin / tp (toilet paper throw): the run-up screen and the field screen.
Created By Mark Stronks, Stronkie Soft."""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gfxlib as g

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(g.ROOT, 'build', 'gen')
KIND = sys.argv[2] if len(sys.argv) > 2 else 'longjump'
PRE = dict(longjump='ljp', javelin='jav', tp='tpt')[KIND]
random.seed(55)
PAL = [0x112, 0x000, 0xfff, 0xfd0, 0xd22, 0x334, 0x446, 0xe55, 0xfd6, 0x5af, 0xb53, 0xc64, 0xdb7, 0x383, 0x4a4,
       0x889, 0x112, 0x777, 0x2a2, 0xa86, 0x9cf, 0xeee, 0xc8e, 0x000, 0x000]
(BG, BLACK, WHITE, YELLOW, RED, ST1, ST2, CR1, CR2, CR3, TRACK, TRACK2, SAND, GRASS, GRASS2, GREY, DARK, SHADE,
 GRASS3, SAND2, SKY, PAPER, PINK) = range(23)
START_X = 16
BOARD = 176                        # long jump: the board; javelin/tp: the foul line
LANE = 208                         # the feet of the athlete on the run-up
PX_M = dict(longjump=14, javelin=3, tp=6)[KIND]        # field scale: pixels per metre
FIELD0 = 8                          # javelin/tp: 0 m on the field screen
FIELD_Y = 200                       # the ground on the field screen

def stands(im, top=24, bottom=112):
    g.stands(im, top, bottom, PAL, seed=41 + top)

def frame_bars(im, d, title):
    d.rectangle([0, 0, 319, 23], fill=DARK); d.line([0, 23, 319, 23], fill=YELLOW)
    g.ad_boards(im, 112, PAL, [title] + g.SPONSORS, seed=5)
    d.rectangle([0, 239, 319, 255], fill=DARK); d.line([0, 240, 319, 240], fill=YELLOW)

def runup_bg():
    im = Image.new('P', (320, 256), BG); d = ImageDraw.Draw(im)
    stands(im); frame_bars(im, d, dict(longjump='LONG JUMP', javelin='JAVELIN', tp='TOILET PAPER')[KIND])
    g.ground(im, (0, 122, 320, 239), PAL, [(0, (40, 110, 45)), (1, (80, 175, 75))], [GRASS, GRASS2, GRASS3], stripes=(24, (14, 18, 8)))
    g.ground(im, (0, 186, 320 if KIND != 'longjump' else BOARD + 1, 217), PAL, [(0, (165, 75, 50)), (1, (205, 105, 70))], [TRACK, TRACK2, RED], noise=7)
    d.line([0, 186, 319, 186], fill=WHITE); d.line([0, 216, 319, 216], fill=WHITE)
    if KIND == 'longjump':
        d.rectangle([BOARD - 4, 186, BOARD, 216], fill=WHITE); d.line([BOARD - 4, 186, BOARD - 4, 216], fill=BLACK)
        d.rectangle([BOARD + 1, 184, 317, 218], fill=SAND, outline=SAND2)
        for i in range(500): d.point((random.randrange(BOARD + 2, 316), random.randrange(185, 218)), fill=SAND2)
        for m in range(3, 10):
            x = BOARD + m * PX_M
            d.line([x, 176, x, 182], fill=WHITE)
            if m >= 5: g.text8(im, x - 4, 166, str(m), WHITE)
    else:
        d.line([BOARD, 186, BOARD + 6, 216], fill=WHITE); d.line([BOARD + 1, 186, BOARD + 7, 216], fill=WHITE)
        g.text8(im, BOARD + 12, 222, 'FOUL LINE', WHITE)
    g.topbar_to_copper(im)
    return im

def field_bg():
    im = Image.new('P', (320, 256), BG); d = ImageDraw.Draw(im)
    frame_bars(im, d, 'JAVELIN' if KIND == 'javelin' else 'TOILET PAPER')
    g.ground(im, (0, 24, 320, 62), PAL, [(0, (60, 110, 200)), (1, (150, 200, 250))], [SKY, WHITE, GREY], spread=40)
    g.paint(im, 0, 62, g.stands_rgb(320, 50, seed=47, roof=False, light=0.9), PAL, None, 20)
    g.ground(im, (0, 122, 320, 239), PAL, [(0, (40, 110, 45)), (1, (80, 175, 75))], [GRASS, GRASS2, GRASS3], stripes=(24, (14, 18, 8)))
    step = 10 if KIND == 'javelin' else 5
    for m in range(0, 101 if KIND == 'javelin' else 51, step):
        x = FIELD0 + m * PX_M
        d.line([x, 150, x - 2, 234], fill=WHITE)
        if m: g.text8(im, x - (8 if m < 100 else 12), 140, str(m), WHITE)
    d.rectangle([0, 150, FIELD0, 234], fill=TRACK)
    g.topbar_to_copper(im)
    return im

def thrower(kit, woman):
    """the run-up frames 0-5, 6 ready, 7 take-off / throw, 8 landed (long jump)"""
    out = []
    for p in g.run_cycle(6, lean=3):
        if KIND != 'longjump': p.update(rel=(13, 14), rha=(14, 8))           # the arm up with the javelin / roll
        out.append(p)
    ready = g.pose_stand()
    if KIND != 'longjump': ready.update(rel=(13, 14), rha=(14, 8))
    if KIND == 'longjump':
        act = dict(head=(20, 6), neck=(18, 12), hip=(14, 24), lel=(24, 10), lha=(27, 5), rel=(10, 14), rha=(6, 10),
                   lkn=(24, 26), lft=(28, 34), rkn=(10, 34), rft=(4, 40))
    else:
        act = dict(head=(18, 6), neck=(16, 12), hip=(14, 26), lel=(22, 16), lha=(26, 20), rel=(20, 9), rha=(24, 3),
                   lkn=(22, 34), lft=(26, 45), rkn=(10, 36), rft=(6, 45))
    land = dict(head=(22, 30), neck=(20, 35), hip=(12, 42), lel=(26, 38), lha=(30, 36), rel=(24, 40), rha=(29, 42),
                lkn=(20, 40), lft=(28, 45), rkn=(20, 42), rft=(27, 46))
    ims = [g.athlete(p, woman=woman, kit=kit) for p in out + [ready, act, land]]
    if KIND != 'longjump':                                                  # the javelin / roll in the hand
        for i, im in enumerate(ims[:8]):
            d = ImageDraw.Draw(im)
            hx, hy = (out + [ready, act])[i]['rha']
            if KIND == 'javelin': d.line([hx - 12, hy + 3, hx + 12, hy - 3], fill=SHADE); d.point((hx + 12, hy - 3), fill=WHITE)
            else: d.ellipse([hx - 3, hy - 4, hx + 4, hy + 3], fill=PAPER, outline=BLACK); d.point((hx, hy), fill=GREY)
    return ims

def javelins():
    out = []
    for a in (60, 45, 30, 15, 0, -15, -30, -45):
        im = g.bob_canvas(32, 32); d = ImageDraw.Draw(im)
        r = math.radians(a); c, s = math.cos(r), -math.sin(r)
        d.line([16 - 14 * c, 16 - 14 * s, 16 + 14 * c, 16 + 14 * s], fill=BLACK, width=2)
        d.line([16 - 13 * c, 16 - 13 * s, 16 + 12 * c, 16 + 12 * s], fill=SHADE)
        d.line([16 + 10 * c, 16 + 10 * s, 16 + 14 * c, 16 + 14 * s], fill=WHITE)
        out.append(im)
    return out

def rolls():
    out = []
    for k in range(4):
        im = g.bob_canvas(16, 16); d = ImageDraw.Draw(im)
        d.ellipse([2, 2, 13, 13], fill=PAPER, outline=BLACK)
        a = k * math.pi / 4
        d.ellipse([6, 6, 9, 9], fill=GREY)
        d.line([8 + 5 * math.cos(a), 8 + 5 * math.sin(a), 8 + 2 * math.cos(a), 8 + 2 * math.sin(a)], fill=SHADE)
        out.append(im)
    return out

def trail():
    im = g.bob_canvas(16, 3); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 3, 1], fill=PAPER); d.point((1, 2), fill=PINK)
    return im

def sounds(o):
    R = 8000
    t = np.arange(int(0.25 * R)) / R
    o.sample('snd_whoosh', g.tosamp(g.bandnoise(len(t), 4, 30, 2) * np.sin(np.pi * t / t[-1])), R)
    o.sample('snd_thud', g.tosamp(g.thump(int(0.2 * R), 120, 50, 0.05, R) + g.noise(int(0.2 * R), 5) * g.env(int(0.2 * R), 0.001, 0.03, R) * 0.4), R)
    o.sample('snd_step', g.tosamp(g.thump(int(0.05 * R), 200, 90, 0.01, R)), R)
    V = 6000
    o.sample('v_title', g.speak(dict(longjump='l o N d j V m p', javelin='d j ae v l I n', tp='t oI l @ t p eI p @ r')[KIND]), V)

def main():
    o = g.Out(OUT, PRE)
    rv = dict(hair=g.HAIR, skin=g.SKIN, skind=g.SKIND, shirt=g.SHIRT, shirtd=g.SHIRTD, shorts=g.SHORTS, shoes=g.SHOES)
    o.bobs('pm', thrower(None, False)); o.bobs('pw', thrower(None, True))
    if KIND == 'javelin': o.bobs('jv', javelins()); o.bob('paper', trail())
    if KIND == 'tp': o.bobs('jv', rolls()); o.bob('paper', trail())
    sounds(o)
    o.raw(g.palette_line('pal_field', PAL + [0] * (25 - len(PAL))))
    for k, v in (('START_X', START_X), ('BOARD', BOARD), ('LANE', LANE), ('PX_M', PX_M), ('FIELD0', FIELD0), ('FIELD_Y', FIELD_Y)):
        o.equ(k, v)
    n = o.write()
    bg = runup_bg()
    g.save_screen(bg, os.path.join(OUT, PRE + '_bg.rle'))
    g.preview(bg, PAL, os.path.join(OUT, 'preview_%s.png' % PRE))
    if KIND != 'longjump':
        fb = field_bg()
        g.save_screen(fb, os.path.join(OUT, PRE + '_field.rle'))
        g.preview(fb, PAL, os.path.join(OUT, 'preview_%s_field.png' % PRE))
    fr = thrower(None, False); pal = PAL + [0] * (25 - len(PAL)) + g.DEF_PLAYER
    sheet = Image.new('P', (32 * 9, 48), GRASS)
    for i, f in enumerate(fr):
        m = Image.fromarray(((np.array(f) != g.TRANSP) * 255).astype('uint8'), 'L'); sheet.paste(f, (i * 32, 0), m)
    g.preview(sheet, pal, os.path.join(OUT, 'preview_%s_men.png' % PRE), scale=4)
    print('%s: %d bytes chip' % (KIND, n))

if __name__ == '__main__':
    main()
