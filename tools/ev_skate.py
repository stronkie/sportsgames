#!/usr/bin/env python3
"""ev_skate.py - graphics and sounds of the Skateboarding event (the half pipe, 60 seconds).
Created By Mark Stronks, Stronkie Soft."""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gfxlib as g

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(g.ROOT, 'build', 'gen')
random.seed(61)
PAL = [0x112, 0x000, 0xfff, 0xfd0, 0xd22, 0xccc, 0xaaa, 0x888, 0x666, 0x444,
       0x335, 0x447, 0x559, 0xe3a, 0x3c8, 0x2a4, 0xf90, 0xa52, 0x753, 0x8bf, 0xdde, 0x224]
(SKY, BLACK, WHITE, YELLOW, RED, R1, R2, R3, R4, R5, B1, B2, B3, PINK, CYAN, GREEN, ORANGE, BRICK, WOOD, LSKY, CLOUD, DARK) = range(22)
LIP_Y, FLOOR_Y = 92, 214
LX, RX = 34, 286            # the vertical walls
R = 78                      # radius of the curves
FL0, FL1 = LX + R, RX - R   # the flat bottom

def gradient():
    items = []
    for i, y in enumerate(range(24, 120, 6)):
        k = i / 16
        items.append((y, (int(3 + 8 * k) << 8) | (int(4 + 7 * k) << 4) | int(10 + 5 * k)))
    items.append((210, 0x112))
    return items

def path():
    """the ramp from the left lip to the right lip, one point per pixel of length: x, y, slope"""
    pts = []
    top = FLOOR_Y - R
    for y in np.arange(LIP_Y, top, 1.0): pts.append((LX, y))
    for a in np.arange(180, 90, -180 / (math.pi * R)):
        r = math.radians(a); pts.append((FL0 + R * math.cos(r), top + R * math.sin(r)))
    for x in np.arange(FL0, FL1, 1.0): pts.append((x, FLOOR_Y))
    for a in np.arange(90, 0, -180 / (math.pi * R)):
        r = math.radians(a); pts.append((FL1 + R * math.cos(r), top + R * math.sin(r)))
    for y in np.arange(top, LIP_Y - 0.5, -1.0): pts.append((RX, y))
    out = []
    for i, (x, y) in enumerate(pts):
        a = pts[max(0, i - 2)]; b = pts[min(len(pts) - 1, i + 2)]
        dx, dy = b[0] - a[0], b[1] - a[1]; l = math.hypot(dx, dy) or 1
        slope = int(round(64 * dy / l))                       # + = downhill going right
        ang = int(round(math.degrees(math.atan2(-dy, dx)) / 22.5)) % 16
        out.append((int(round(x)), int(round(y)), slope, ang))
    return out

def background():
    im = Image.new('P', (320, 256), SKY); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 319, 23], fill=DARK); d.line([0, 23, 319, 23], fill=YELLOW)
    for (x, y) in ((40, 38), (210, 30)):
        for i in range(4): d.ellipse([x + i * 9, y - (i % 2) * 3, x + i * 9 + 16, y + 8 - (i % 2) * 3], fill=CLOUD)
    # the city behind
    x = 0
    while x < 320:
        w = random.randint(18, 40); h = random.randint(30, 80)
        d.rectangle([x, 150 - h, x + w, 150], fill=random.choice([B1, B2, B3]))
        for wy in range(150 - h + 4, 146, 7):
            for wx in range(x + 3, x + w - 3, 6):
                if random.random() < 0.5: d.rectangle([wx, wy, wx + 2, wy + 3], fill=YELLOW if random.random() < 0.3 else B3)
        x += w + random.randint(0, 6)
    d.rectangle([0, 150, 319, 239], fill=BRICK)
    for y in range(150, 240, 6):
        d.line([0, y, 319, y], fill=WOOD)
    # the half pipe
    p = path()
    poly = [(x, y) for x, y, s, a in p]
    d.polygon([(0, LIP_Y)] + [(LX, LIP_Y)] + poly + [(RX, LIP_Y), (319, LIP_Y), (319, 239), (0, 239)], fill=R4)
    for i, (x, y, s, a) in enumerate(p):
        d.line([x, y, x, min(239, y + 6)], fill=R3)
    for x, y, s, a in p: d.point((x, y), fill=R1); d.point((x, y + 1), fill=R2)
    d.rectangle([0, LIP_Y - 4, LX, LIP_Y], fill=R2); d.rectangle([RX, LIP_Y - 4, 319, LIP_Y], fill=R2)
    d.line([0, LIP_Y - 4, LX + 1, LIP_Y - 4], fill=WHITE); d.line([RX - 1, LIP_Y - 4, 319, LIP_Y - 4], fill=WHITE)
    d.rectangle([LX - 1, LIP_Y - 4, LX + 2, LIP_Y], fill=ORANGE); d.rectangle([RX - 2, LIP_Y - 4, RX + 1, LIP_Y], fill=ORANGE)
    for x in range(4, 30, 10): d.line([x, LIP_Y, x, 239], fill=R5)
    for x in range(292, 319, 10): d.line([x, LIP_Y, x, 239], fill=R5)
    f = g.ttf(14)
    t = Image.new('P', (320, 30), 0); td = ImageDraw.Draw(t); td.text((160, 15), 'STRONKIE SOFT', font=f, fill=1, anchor='mm')
    a = np.array(t); px = im.load()
    for y in range(30):
        for x in range(320):
            if a[y, x]: px[x, y + 186] = PINK if (x // 4 + y // 3) % 3 else CYAN
    d.rectangle([0, 240, 319, 255], fill=DARK); d.line([0, 240, 319, 240], fill=YELLOW)
    return im, p

def skater(woman):
    p = dict(head=(18, 10), neck=(17, 16), hip=(15, 28), lel=(11, 20), lha=(7, 24), rel=(22, 19), rha=(27, 17),
             lkn=(11, 35), lft=(9, 41), rkn=(20, 35), rft=(22, 41))
    body = g.athlete(p, woman=woman)
    base = Image.new('P', (48, 48), g.TRANSP); d = ImageDraw.Draw(base)
    d.rounded_rectangle([10, 39, 38, 42], 1, fill=BLACK); d.line([11, 40, 37, 40], fill=RED)
    for x in (14, 33): d.ellipse([x - 2, 42, x + 2, 46], fill=WHITE, outline=BLACK)
    a = np.array(body); bb = np.array(base)
    for y in range(48):
        for x in range(32):
            yy = y - 2
            if 0 <= yy < 48 and a[y, x] != g.TRANSP and yy < 40: bb[yy, x + 8] = a[y, x]
    return Image.fromarray(bb, 'P')

def frames(woman):
    base = skater(woman); flip = base.transpose(Image.FLIP_LEFT_RIGHT)
    out = []
    for i in range(16):
        th = i * 22.5
        if th <= 90 or th >= 270: tilt = th if th <= 90 else th - 360; src = base
        else: tilt = 180 - th; src = flip
        out.append(src.rotate(tilt, resample=Image.NEAREST, fillcolor=g.TRANSP, center=(24, 44)))
    return out

def crash():
    im = g.bob_canvas(48, 24); d = ImageDraw.Draw(im)
    pose = dict(head=(4, 20), neck=(9, 19), hip=(20, 19), lel=(12, 14), lha=(9, 10), rel=(14, 22), rha=(8, 23),
                lkn=(26, 13), lft=(31, 18), rkn=(28, 21), rft=(34, 22))
    return pose

def sounds(o):
    R8 = 8000
    n = int(1.0 * R8)
    roll = g.bandnoise(n, 6, 80, 2) * 0.8 + g.noise(n, 3) * 0.1
    o.sample('snd_roll', g.tosamp(roll), R8)
    o.sample('snd_clack', g.tosamp(g.thump(int(0.1 * R8), 900, 300, 0.015, R8) + g.noise(int(0.1 * R8), 5) * g.env(int(0.1 * R8), 0.001, 0.01, R8)), R8)
    o.sample('snd_crash', g.tosamp(g.bandnoise(int(0.6 * R8), 1, 12, 7) * g.env(int(0.6 * R8), 0.002, 0.2, R8) + g.thump(int(0.6 * R8), 120, 50, 0.1, R8)), R8)
    V = 6000
    o.sample('v_skate', g.speak('s k eI t b o r d I N'), V)
    o.sample('v_rad', g.speak('r ae d I k @ l'), V)
    o.sample('v_ouch', g.speak('aI t S', speed=0.9), V)

def main():
    o = g.Out(OUT, 'ska')
    o.bobs('km', frames(False)); o.bobs('kw', frames(True))
    for woman, nm in ((False, 'crm'), (True, 'crw')):
        o.bob(nm, g.athlete(crash(), w=48, h=32, woman=woman).crop((0, 0, 48, 32)))
    sounds(o)
    bg, p = background()
    o.raw(g.palette_line('pal_ska', PAL))
    o.raw(g.grad_lines('grad_ska', gradient()))
    o.raw('ramp\t; x, y, slope, angle per pixel of the ramp')
    for i in range(0, len(p), 8):
        o.raw('\tdc.w\t' + ','.join('%d,%d,%d,%d' % q for q in p[i:i + 8]))
    o.equ('RAMP_N', len(p)); o.equ('LIP_Y', LIP_Y); o.equ('FLOOR_Y', FLOOR_Y)
    n = o.write()
    g.save_screen(bg, os.path.join(OUT, 'ska_bg.rle'))
    pv = list(PAL); pv[0] = 0x8bf
    g.preview(bg, pv, os.path.join(OUT, 'preview_ska.png'))
    sheet = Image.new('P', (16 * 50, 52), R1)
    for i, im in enumerate(frames(False)):
        a = np.array(im); a[a == g.TRANSP] = R1; sheet.paste(Image.fromarray(a, 'P'), (i * 50, 2))
    g.preview(sheet, PAL, os.path.join(OUT, 'preview_ska_bobs.png'), 1)
    print('skateboarding: %d bytes chip, ramp %d' % (n, len(p)))

if __name__ == '__main__':
    main()
