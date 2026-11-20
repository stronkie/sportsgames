#!/usr/bin/env python3
"""ev_surf.py - graphics and sounds of the Surfing event (ride the wave, 60 seconds).
Created By Mark Stronks, Stronkie Soft."""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gfxlib as g

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(g.ROOT, 'build', 'gen')
random.seed(51)
PAL = [0x112, 0x000, 0xfff, 0xfd0, 0xd22, 0x036, 0x158, 0x27a, 0x39c, 0x5be,
       0xbef, 0xf90, 0xdef, 0x112, 0x8ad, 0x9cf, 0x269, 0xccd, 0xe60, 0x024, 0x6cf]
(SKY, BLACK, WHITE, YELLOW, RED, W1, W2, W3, W4, W5, FOAM, BOARD, FOAM2, DARK, HAZE, SPRAY, W6, CLOUD, BOARDD, DEEP, LIGHTW) = range(21)
LIP_Y, TROUGH_Y = 86, 222        # h = 0 at the trough, h = 136 at the lip
CURL_X = 46

def gradient():
    items = []
    for i, y in enumerate(range(24, 84, 5)):
        k = i / 12
        items.append((y, (int(4 + 7 * k) << 8) | (int(7 + 6 * k) << 4) | int(12 + 3 * k)))
    items.append((200, 0x112))
    return items

def background():
    im = Image.new('P', (320, 256), SKY); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 319, 23], fill=DARK); d.line([0, 23, 319, 23], fill=YELLOW)
    for (x, y) in ((200, 36), (60, 50), (260, 58)):
        for i in range(4): d.ellipse([x + i * 9, y - (i % 2) * 3, x + i * 9 + 16, y + 8 - (i % 2) * 3], fill=CLOUD)
    # far sea behind the wave
    d.rectangle([0, 76, 319, 90], fill=W2)
    # the wave face: bands, lighter near the top; the lip line bends up to the curl
    for y in range(LIP_Y - 10, TROUGH_Y + 2):
        k = (y - LIP_Y) / (TROUGH_Y - LIP_Y)
        col = [W5, W4, W3, W6, W2, W1][min(5, max(0, int(k * 6)))]
        d.line([0, y, 319, y], fill=col)
    for x in range(320):                                       # the lip
        lip = LIP_Y - 6 + 6 * math.exp(-(x - CURL_X) / 60) if x > CURL_X else LIP_Y - 12
        d.line([x, 76, x, int(lip)], fill=W2)
        d.line([x, int(lip), x, int(lip) + 3], fill=FOAM2)
    for i in range(240):                                       # streaks on the face
        x = random.randrange(CURL_X + 10, 320); y = random.randrange(LIP_Y + 8, TROUGH_Y - 4)
        d.line([x, y, x + random.randint(4, 14), y], fill=random.choice([W4, W5, LIGHTW]))
    # the curl: a tube of falling water and foam at the left
    d.pieslice([-60, 60, CURL_X + 40, TROUGH_Y + 20], 270, 90, fill=W1)
    d.arc([-60, 60, CURL_X + 40, TROUGH_Y + 20], 270, 90, fill=FOAM, width=6)
    d.ellipse([-40, 120, CURL_X - 6, TROUGH_Y], fill=DEEP)
    for i in range(300):
        x = random.randrange(0, CURL_X + 30); y = random.randrange(70, TROUGH_Y + 12)
        if (x - CURL_X + 10) ** 2 / 2500 + ((y - 150) / 80) ** 2 > 0.7: d.point((x, y), fill=random.choice([FOAM, WHITE, SPRAY]))
    # white water at the bottom
    for y in range(TROUGH_Y, 240):
        d.line([0, y, 319, y], fill=FOAM if (y + random.randrange(2)) % 3 else SPRAY)
    for i in range(400):
        d.point((random.randrange(320), random.randrange(TROUGH_Y - 4, 240)), fill=random.choice([WHITE, W5, FOAM2]))
    d.rectangle([0, 240, 319, 255], fill=DARK); d.line([0, 240, 319, 240], fill=YELLOW)
    return im

def surfer(woman):
    p = dict(head=(17, 9), neck=(16, 15), hip=(15, 27), lel=(10, 18), lha=(6, 21), rel=(22, 18), rha=(27, 16),
             lkn=(11, 35), lft=(8, 42), rkn=(20, 35), rft=(22, 42))
    body = g.athlete(p, woman=woman)
    base = Image.new('P', (48, 48), g.TRANSP)
    base.paste(body, (8, -2))
    d = ImageDraw.Draw(base)
    d.ellipse([4, 39, 44, 45], fill=BLACK); d.ellipse([5, 40, 43, 44], fill=BOARD); d.line([8, 42, 40, 42], fill=BOARDD)
    # put the body back over the board (feet on it)
    a = np.array(body); bb = np.array(base)
    for y in range(48):
        for x in range(32):
            yy = y - 2
            if 0 <= yy < 48 and a[y, x] != g.TRANSP and yy < 41: bb[yy, x + 8] = a[y, x]
    return Image.fromarray(bb, 'P')

def surfer_frames(woman):
    """16 directions: 0 right, 4 up, 8 left, 12 down (the rider stays upright, the board tilts)"""
    base = surfer(woman); flip = base.transpose(Image.FLIP_LEFT_RIGHT)
    out = []
    for i in range(16):
        th = i * 22.5
        if th <= 90 or th >= 270:
            tilt = th if th <= 90 else th - 360; src = base
        else:
            tilt = 180 - th; src = flip
        tilt = max(-70, min(70, tilt))
        r = src.rotate(tilt, resample=Image.NEAREST, fillcolor=g.TRANSP, center=(24, 40))
        out.append(r)
    return out

def splash(i):
    im = g.bob_canvas(48, 32); d = ImageDraw.Draw(im); rng = random.Random(i)
    for k in range(60):
        a = rng.uniform(math.pi, 2 * math.pi); r = rng.uniform(4, 22 + i * 6)
        x = 24 + math.cos(a) * r; y = 30 + math.sin(a) * r * 0.9
        d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=rng.choice([WHITE, FOAM, SPRAY]))
    return im

def foam(i):
    im = g.bob_canvas(32, 16); d = ImageDraw.Draw(im); rng = random.Random(10 + i)
    for k in range(30):
        x = rng.uniform(2, 30); y = rng.uniform(2, 14)
        d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=rng.choice([WHITE, FOAM, FOAM2]))
    return im

def sounds(o):
    R = 8000
    n = int(1.6 * R)
    surf = g.bandnoise(n, 4, 60, 3) * (0.6 + 0.4 * np.sin(np.linspace(0, 6 * np.pi, n)))
    o.sample('snd_wave', g.tosamp(surf * np.minimum(1, np.minimum(np.arange(n), n - np.arange(n)) / 2000)), R)
    o.sample('snd_splash', g.tosamp(g.bandnoise(int(0.7 * R), 2, 20, 5) * g.env(int(0.7 * R), 0.01, 0.25, R)), R)
    o.sample('snd_whoosh', g.tosamp(g.bandnoise(int(0.3 * R), 2, 9, 6) * np.sin(np.linspace(0, np.pi, int(0.3 * R)))), R)
    V = 6000
    o.sample('v_surf', g.speak('s @ r f I N'), V)
    o.sample('v_wipe', g.speak('w aI p aI t'), V)
    o.sample('v_rad', g.speak('r ae d'), V)
    o.sample('v_tube', g.speak('t u b'), V)

def main():
    o = g.Out(OUT, 'sur')
    o.bobs('sm', surfer_frames(False)); o.bobs('sw', surfer_frames(True))
    o.bobs('splash', [splash(i) for i in range(3)])
    o.bobs('foam', [foam(i) for i in range(3)])
    sounds(o)
    o.raw(g.palette_line('pal_sur', PAL))
    o.raw(g.grad_lines('grad_sur', gradient()))
    cs = [int(round(64 * math.cos(math.radians(i * 22.5)))) for i in range(16)]
    sn = [int(round(64 * math.sin(math.radians(i * 22.5)))) for i in range(16)]
    o.raw('cos_t\tdc.w\t' + ','.join(map(str, cs)))
    o.raw('sin_t\tdc.w\t' + ','.join(map(str, sn)))
    o.equ('LIP_Y', LIP_Y); o.equ('TROUGH_Y', TROUGH_Y); o.equ('CURL_X', CURL_X)
    n = o.write()
    bg = background()
    g.save_screen(bg, os.path.join(OUT, 'sur_bg.rle'))
    pv = list(PAL); pv[0] = 0x6bf
    g.preview(bg, pv, os.path.join(OUT, 'preview_sur.png'))
    sheet = Image.new('P', (16 * 50, 52), W3)
    for i, im in enumerate(surfer_frames(False)):
        a = np.array(im); a[a == g.TRANSP] = W3; sheet.paste(Image.fromarray(a, 'P'), (i * 50, 2))
    g.preview(sheet, PAL, os.path.join(OUT, 'preview_sur_bobs.png'), 1)
    print('surfing: %d bytes chip' % n)

if __name__ == '__main__':
    main()
