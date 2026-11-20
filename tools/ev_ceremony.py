#!/usr/bin/env python3
"""ev_ceremony.py - the opening and closing ceremony of Stronkie's Olympics (Ceremony.evt):
graphics, sounds and the anthem (an original tune by Stronkie Soft in the style of a stadium anthem).
Created By Mark Stronks, Stronkie Soft."""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gfxlib as g

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(g.ROOT, 'build', 'gen')
random.seed(71)
#      0 sky  1 blk  2 wht  3 yel  4 red  5 flame 6 std  7 std2 8 cr1  9 cr2  10 cr3 11 track 12 lane 13 grass 14 grass2
PAL_DAY = [0x248, 0x000, 0xfff, 0xfd0, 0xd22, 0xf70, 0x334, 0x446, 0xe55, 0xfd6, 0x5af, 0xb53, 0xeee, 0x383, 0x4a4,
           0x889, 0x556, 0x25d, 0x2a4, 0xd22, 0xfc2, 0x222, 0xfc9, 0x964, 0x321]
#      15 tower 16 tower2 17 kitA 18 kitB 19 kitC 20 kitD 21 shorts 22 skin 23 skin2 24 hair
PAL_NIGHT = [0x012, 0x000, 0xddd, 0xfd0, 0xa11, 0xf80, 0x112, 0x223, 0x635, 0x775, 0x347, 0x522, 0x777, 0x131, 0x242,
             0x445, 0x223, 0x124, 0x142, 0x711, 0x863, 0x111, 0x986, 0x643, 0x210]
(SKY, BLACK, WHITE, YELLOW, RED, FLAME, ST1, ST2, CR1, CR2, CR3, TRACK, LANE, GRASS, GRASS2, TOWER, TOWER2,
 KA, KB, KC, KD, SHORTS, SKIN, SKIN2, HAIR) = range(25)
TRACK_Y = 196                    # the marchers' feet
STAIR0 = (196, 196)              # the foot of the stairs
CAULDRON = (268, 58)             # where the torch goes (top of the tower)

def grad_day():
    cols = [0x235, 0x346, 0x457, 0x568, 0x779, 0x98a, 0xb89, 0xc97, 0xda7]
    return [(24 + i * 4, c) for i, c in enumerate(cols)] + [(190, 0x248)]

def grad_night():
    cols = [0x001, 0x001, 0x002, 0x012, 0x012, 0x013, 0x023, 0x124]
    return [(2 + i * 6, c) for i, c in enumerate(cols)] + [(190, 0x012)]

def background():
    im = Image.new('P', (320, 256), SKY); d = ImageDraw.Draw(im)
    # stars (only seen at night: colour 2 is grey-white at night too)
    # the stands: a big bowl
    a = g.stands_rgb(320, 120, seed=95, roof=False)                # the stands: a big bowl
    mask = np.zeros((120, 320), bool)
    for x in range(320):
        top = int(8 - 8 * (1 - abs(x - 160) / 160) ** 0.5)          # (the rim of the bowl curves up)
        mask[top:, x] = True
    g.paint(im, 0, 40, a, PAL_DAY, [BLACK, WHITE, YELLOW, RED, ST1, ST2, CR1, CR2, CR3, KA, KB, KC, KD, SKIN, HAIR], 20, mask)
    # floodlight masts
    for x in (12, 150):
        d.rectangle([x, 8, x + 3, 48], fill=TOWER2); d.rectangle([x - 7, 4, x + 10, 10], fill=WHITE)
    # the track and the field
    d.rectangle([0, 160, 319, 212], fill=TRACK)
    for y in (172, 184, 198, 210): d.line([0, y, 319, y], fill=LANE)
    d.rectangle([0, 213, 319, 255], fill=GRASS)
    for x in range(0, 320, 24): d.rectangle([x, 213, x + 11, 255], fill=GRASS2)
    # the tower with the stairs and the cauldron
    cx, cy = CAULDRON
    d.polygon([(cx - 22, TRACK_Y + 4), (cx + 22, TRACK_Y + 4), (cx + 10, cy + 8), (cx - 10, cy + 8)], fill=TOWER)
    d.polygon([(cx + 2, TRACK_Y + 4), (cx + 22, TRACK_Y + 4), (cx + 10, cy + 8), (cx + 2, cy + 8)], fill=TOWER2)
    x0, y0 = STAIR0
    n = 18
    for i in range(n):                                          # the stairs up to it
        t = i / n
        x = x0 + (cx - 14 - x0) * t; y = y0 - (y0 - cy - 10) * t
        d.rectangle([x, y, x + 8, y + 3], fill=WHITE); d.rectangle([x, y + 3, x + 8, y + 7], fill=TOWER2)
    d.polygon([(cx - 16, cy), (cx + 16, cy), (cx + 10, cy + 10), (cx - 10, cy + 10)], fill=YELLOW, outline=BLACK)
    d.rectangle([cx - 18, cy - 2, cx + 18, cy + 1], fill=FLAME)
    return im

def marcher_frames(kit, woman, torch=False, flag=None):
    out = []
    for i, p in enumerate(g.run_cycle(4, lean=0)):
        # a calm walk: smaller steps
        q = {k: (16 + (v[0] - 16) * 0.6 + 1, v[1]) if k in ('lkn', 'lft', 'rkn', 'rft') else v for k, v in p.items()}
        if torch: q.update(rel=(20, 12), rha=(22, 5))
        if flag: q.update(rel=(20, 14), rha=(21, 9))
        im = g.athlete(q, woman=woman, kit=kit)
        big = Image.new('P', (32, 64), g.TRANSP); big.paste(im, (0, 16)); d = ImageDraw.Draw(big)
        if torch:
            d.polygon([(21, 22), (25, 22), (24, 30), (22, 30)], fill=YELLOW, outline=BLACK)
            fl = [(18, 22), (28, 22), (25, 12 + i % 2), (23, 15), (21, 11 + (i + 1) % 2)]
            d.polygon(fl, fill=FLAME); d.polygon([(21, 22), (26, 22), (23, 16)], fill=YELLOW)
        if flag:
            d.line([21, 2, 21, 28], fill=TOWER2)
            wave = i % 2
            d.rectangle([22, 2 + wave, 31, 9 + wave], fill=flag[0]); d.rectangle([22, 5 + wave, 31, 6 + wave], fill=flag[1])
        out.append(big)
    return out

def flame(i):
    im = g.bob_canvas(32, 32); d = ImageDraw.Draw(im); rng = random.Random(i)
    for r, col in ((14, RED), (11, FLAME), (7, YELLOW), (3, WHITE)):
        pts = [(16 - r, 31), (16 + r, 31)]
        for k in range(5):
            pts.insert(1, (16 + r - k * r * 2 / 4 + rng.uniform(-2, 2), 31 - r * 1.8 - rng.uniform(0, 6) * (1 if k % 2 else 0.4)))
        d.polygon(pts, fill=col)
    return im

def small_flame(s):
    im = g.bob_canvas(32, 32); d = ImageDraw.Draw(im)
    for r, col in ((s, FLAME), (max(1, s // 2), YELLOW)):
        d.polygon([(16 - r, 31), (16 + r, 31), (16, 31 - r * 2)], fill=col)
    return im

def bird(i):
    im = g.bob_canvas(16, 10); d = ImageDraw.Draw(im)
    d.ellipse([5, 4, 11, 7], fill=WHITE, outline=BLACK)
    if i == 0: d.line([2, 0, 8, 5], fill=WHITE, width=2); d.line([14, 0, 8, 5], fill=WHITE, width=2)
    else: d.line([1, 8, 8, 5], fill=WHITE, width=2); d.line([15, 8, 8, 5], fill=WHITE, width=2)
    d.point((12, 5), fill=YELLOW)
    return im

def firework(i, col):
    im = g.bob_canvas(32, 32); d = ImageDraw.Draw(im)
    r = 4 + i * 5
    for a in range(0, 360, 30):
        x = 16 + math.cos(math.radians(a)) * r; y = 16 + math.sin(math.radians(a)) * r
        d.ellipse([x - 1, y - 1, x + 1, y + 1], fill=col if i < 2 else YELLOW)
        if i == 1: d.line([16 + math.cos(math.radians(a)) * r * 0.5, 16 + math.sin(math.radians(a)) * r * 0.5, x, y], fill=col)
    return im

# ------------------------------------------------------------------ music: original tunes by Stronkie Soft
# the anthem: slow and solemn (4/4, a tick = 1/8 note)
ANTHEM_M = ('G4/3 G4/1 C5/4 B4/2 A4/2 G4/4 E4/2 F4/2 G4/6 -/2 '
            'A4/3 A4/1 D5/4 C5/2 B4/2 A4/4 F#4/2 G4/2 A4/6 -/2 '
            'B4/3 C5/1 D5/4 E5/2 D5/2 C5/4 A4/2 B4/2 C5/4 G4/4 '
            'A4/2 B4/2 C5/2 D5/2 E5/4 D5/4 C5/8 -/8')
ANTHEM_B = ('C3/8 E3/8 F3/8 C3/8 D3/8 F#3/8 G3/8 D3/8 '
            'G2/8 C3/8 F3/8 E3/8 F3/4 G3/4 C3/8 C3/8')
# the farewell: the same tune, slower and lower
FAREWELL_M = ('E4/4 E4/2 G4/6 F4/4 E4/4 D4/8 -/4 '
              'D4/4 D4/2 F4/6 E4/4 D4/4 C4/12 -/4')
FAREWELL_B = 'C3/16 G2/16 F2/16 C3/16'

def main():
    o = g.Out(OUT, 'cer')
    kits = [dict(hair=HAIR, skin=SKIN, skind=SKIN2, shirt=k, shirtd=k, shorts=SHORTS, shoes=BLACK) for k in (KA, KB, KC, KD)]
    kit2 = [dict(kk, skin=SKIN2, skind=HAIR) for kk in kits]
    flags = [(KC, WHITE), (KA, YELLOW), (KB, WHITE), (RED, KD)]
    for i in range(4):
        o.bobs('mf%d_' % i, marcher_frames(kits[i], i % 2 == 1, flag=flags[i]))
        o.bobs('mn%d_' % i, marcher_frames(kit2[i], i % 2 == 0))
    o.bobs('lead_m', marcher_frames(None, False, torch=True))
    o.bobs('lead_w', marcher_frames(None, True, torch=True))
    o.bobs('flame', [flame(i) for i in range(3)])
    o.bobs('sflame', [small_flame(s) for s in (12, 9, 6, 3)])
    o.bobs('bird', [bird(i) for i in range(2)])
    o.bobs('fwa', [firework(i, KD) for i in range(3)])
    o.bobs('fwb', [firework(i, KA) for i in range(3)])
    o.raw('march_tab\tdc.l\t' + ','.join('mf%d__tab,mn%d__tab' % (i, i) for i in range(4)))
    R = 8000
    o.sample('snd_whoosh', g.tosamp(g.bandnoise(int(0.6 * R), 2, 14, 6) * np.sin(np.linspace(0, np.pi, int(0.6 * R))) ** 0.5), R)
    o.sample('snd_bang', g.tosamp(g.thump(int(0.5 * R), 90, 40, 0.15, R) + g.noise(int(0.5 * R), 4) * g.env(int(0.5 * R), 0.001, 0.12, R) * 0.6), R)
    o.sample('snd_flap', g.tosamp(g.bandnoise(int(0.5 * R), 3, 20, 7) * (0.5 + 0.5 * np.sign(np.sin(np.linspace(0, 30, int(0.5 * R))))) * g.env(int(0.5 * R), 0.01, 0.3, R)), R)
    V = 6000
    o.sample('v_welcome', g.speak('w e l k @ m t u s t r o N k i z oU l I m p I k s'), V)
    o.sample('v_begin', g.speak('l e t z @ g eI m z b I g I n'), V)
    o.sample('v_goodbye', g.speak('g u d b aI'), V)
    for line in g.song_lines('song_anthem', ANTHEM_M, ANTHEM_B, 7): o.raw(line)
    for line in g.song_lines('song_farewell', FAREWELL_M, FAREWELL_B, 9): o.raw(line)
    o.raw(g.palette_line('pal_day', PAL_DAY)); o.raw(g.palette_line('pal_night', PAL_NIGHT))
    o.raw(g.grad_lines('grad_day', grad_day())); o.raw(g.grad_lines('grad_night', grad_night()))
    o.equ('TRACK_Y', TRACK_Y); o.equ('STAIR_X', STAIR0[0]); o.equ('STAIR_Y', STAIR0[1])
    o.equ('CAUL_X', CAULDRON[0]); o.equ('CAUL_Y', CAULDRON[1])
    n = o.write()
    bg = background()
    g.save_screen(bg, os.path.join(OUT, 'cer_bg.rle'))
    pv = list(PAL_DAY); pv[0] = 0xb89
    g.preview(bg, pv, os.path.join(OUT, 'preview_cer.png'))
    g.preview(bg, PAL_NIGHT, os.path.join(OUT, 'preview_cer_night.png'))
    print('ceremony: %d bytes chip' % n)

if __name__ == '__main__':
    main()
