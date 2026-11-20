#!/usr/bin/env python3
"""make_loading.py - the loading picture of Stronkie's Olympics (320x256, 32 colours, 5 separate
bitplanes for the loader's OS ViewPort; the loader draws the progress bar and its text).
Writes build/gen/loadpic.rle, loadpic.i, preview_loading.png and itch/cover_630x500.png (or cover_demo)."""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gfxlib as g
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(HERE), 'build', 'gen')
VER = os.environ.get('VER', '0.1'); DEMO = os.environ.get('DEMO', '0') == '1'
random.seed(7)
W, H = 320, 256
im = Image.new('RGB', (W, H)); d = ImageDraw.Draw(im)
for y in range(H):
    k = y / 255
    d.line([0, y, W - 1, y], fill=(int(15 + 50 * k), int(25 + 70 * k), int(70 + 110 * k)))
# the stands with the crowd
for y in range(118, 178):
    k = (y - 118) / 60
    d.line([0, y, W - 1, y], fill=(int(30 + 30 * k), int(40 + 40 * k), int(80 + 50 * k)))
for y in range(122, 178, 4): d.line([0, y, W - 1, y], fill=(20, 25, 45))
cols = [(230, 60, 50), (240, 240, 240), (250, 200, 40), (60, 120, 220), (240, 140, 40), (40, 160, 80), (230, 190, 150)]
for i in range(3000):
    d.point((random.randrange(W), random.randrange(120, 177)), fill=random.choice(cols))
d.rectangle([0, 178, W - 1, H - 1], fill=(50, 140, 60))
for y in range(184, H, 14): d.rectangle([0, y, W - 1, y + 6], fill=(70, 170, 80))
# a running track
d.polygon([(0, 214), (W, 214), (W, 240), (0, 240)], fill=(170, 80, 50))
for y in (222, 231): d.line([0, y, W - 1, y], fill=(240, 240, 240))
# the six sports as big balls / things along the bottom
def ball(cx, cy, r, col, lines):
    d.ellipse([cx - r - 1, cy - r - 1, cx + r + 1, cy + r + 1], fill=(0, 0, 0))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    for l in lines: d.line(l, fill=(0, 0, 0), width=1)
ball(36, 200, 14, (245, 245, 245), [])
d.polygon([(36, 194), (41, 198), (39, 204), (33, 204), (31, 198)], fill=(0, 0, 0))
ball(80, 196, 15, (240, 120, 30), [(65, 196, 95, 196), (80, 181, 80, 211)])
d.arc([62, 181, 76, 211], -60, 60, fill=(0, 0, 0)); d.arc([84, 181, 98, 211], 120, 240, fill=(0, 0, 0))
ball(124, 200, 13, (250, 250, 230), [])
d.arc([112, 186, 140, 206], 100, 200, fill=(30, 80, 200), width=2); d.arc([108, 196, 132, 220], 280, 20, fill=(240, 200, 30), width=2)
# bowling pin
d.ellipse([162, 176, 172, 186], fill=(250, 250, 250), outline=(0, 0, 0)); d.rectangle([164, 186, 170, 190], fill=(250, 250, 250))
d.ellipse([158, 188, 176, 214], fill=(250, 250, 250), outline=(0, 0, 0)); d.rectangle([163, 186, 171, 188], fill=(220, 30, 30))
# surfboard
d.polygon([(196, 214), (236, 178), (242, 182), (204, 216)], fill=(255, 210, 40), outline=(0, 0, 0)); d.line([200, 212, 238, 180], fill=(220, 60, 40))
# skateboard
d.rounded_rectangle([256, 200, 306, 208], 4, fill=(200, 40, 40), outline=(0, 0, 0))
for x in (264, 296): d.ellipse([x - 4, 207, x + 4, 215], fill=(250, 250, 250), outline=(0, 0, 0))
# the torch
tx = 160
d.polygon([(tx - 9, 72), (tx + 9, 72), (tx + 4, 100), (tx - 4, 100)], fill=(200, 160, 60), outline=(90, 60, 20))
d.rectangle([tx - 11, 68, tx + 11, 73], fill=(240, 200, 90))
for r, col in ((14, (255, 120, 20)), (9, (255, 200, 40)), (4, (255, 250, 200))):
    d.polygon([(tx - r, 68), (tx + r, 68), (tx + r // 2, 68 - 3 * r), (tx, 68 - 2 * r), (tx - r // 3, 68 - 3 * r - 4)], fill=col)
def outlined(xy, s, font, col, w=2):
    for dx in range(-w, w + 1):
        for dy in range(-w, w + 1):
            if dx or dy: d.text((xy[0] + dx, xy[1] + dy), s, font=font, fill=(0, 0, 0), anchor='mm')
    d.text(xy, s, font=font, fill=col, anchor='mm')
lg = Image.open(os.path.join(os.path.dirname(HERE), 'assets', 'stronkiesoft_logo_x2.png')).convert('RGBA')
im.paste(lg, (160 - lg.width // 2, 0), lg)
outlined((84, 74), "STRONKIE'S", g.ttf(17), (255, 210, 0))
outlined((236, 74), 'OLYMPICS', g.ttf(20), (255, 210, 0))
outlined((160, 110), 'THE SPORTS GAME FOR THE AMIGA 500', g.ttf(9), (255, 255, 255), 1)
cv = im.copy()
label = ('V%s  DEMO' % VER) if DEMO else ('V%s  TEST VERSION' % VER)
d2 = ImageDraw.Draw(cv)
for dx in range(-1, 2):
    for dy in range(-1, 2): d2.text((160 + dx, 142 + dy), label, font=g.ttf(12), fill=(0, 0, 0), anchor='mm')
d2.text((160, 142), label, font=g.ttf(12), fill=(140, 220, 255), anchor='mm')
for dx in range(-1, 2):
    for dy in range(-1, 2): d2.text((160 + dx, 160 + dy), 'Created By Mark Stronks, Stronkie Soft', font=g.ttf(9, bold=False), fill=(0, 0, 0), anchor='mm')
d2.text((160, 160), 'Created By Mark Stronks, Stronkie Soft', font=g.ttf(9, bold=False), fill=(240, 240, 240), anchor='mm')
c2 = cv.resize((640, 512), Image.NEAREST).crop((5, 6, 635, 506))
itch = os.path.join(os.path.dirname(HERE), 'itch'); os.makedirs(itch, exist_ok=True)
c2.save(os.path.join(itch, 'cover_demo_630x500.png' if DEMO else 'cover_630x500.png'))
outlined((160, 124), label, g.ttf(10), (140, 220, 255), 1)
outlined((160, 166), 'Created By Mark Stronks, Stronkie Soft', g.ttf(9, bold=False), (230, 230, 230), 1)
# the progress bar frame
BAR = (58, 136, 264, 146)
TXT = (56, 149, 268, 159)
d.rectangle([BAR[0] - 2, BAR[1] - 2, BAR[2] + 2, BAR[3] + 2], fill=(220, 220, 230))
d.rectangle([TXT[0], TXT[1], TXT[2], TXT[3]], fill=(10, 30, 20))
FIXED = [(10, 10, 30), (40, 200, 240), (20, 130, 190), (255, 226, 30), (225, 150, 0), (0, 0, 0), (255, 255, 255),
         (255, 210, 0), (50, 140, 60), (70, 170, 80), (170, 80, 50), (240, 120, 30), (220, 30, 30), (140, 220, 255)]
auto = im.quantize(28 - len(FIXED), method=Image.MEDIANCUT).getpalette()[:(28 - len(FIXED)) * 3]
base = [v for c in FIXED for v in c] + auto
pimg = Image.new('P', (1, 1)); pimg.putpalette(base + [0] * (768 - len(base)))
q = im.quantize(palette=pimg, dither=Image.FLOYDSTEINBERG)
pal = base + [8, 30, 16, 255, 200, 40, 10, 30, 20, 235, 235, 225]
q.putpalette(pal + [0] * (768 - len(pal)))
pal12 = [tuple(min(15, (pal[i * 3 + k] + 8) // 17) for k in range(3)) for i in range(32)]
bar_bg, bar_fg, txt_bg, txt_c = 28, 29, 30, 31
px = q.load()
for y in range(BAR[1], BAR[3] + 1):
    for x in range(BAR[0], BAR[2] + 1): px[x, y] = bar_bg
for y in range(TXT[1], TXT[3] + 1):
    for x in range(TXT[0], TXT[2] + 1): px[x, y] = txt_bg
planes = bytearray()
a = np.array(q, dtype=np.uint8)
for p in range(5):
    planes += np.packbits((a >> p) & 1, axis=1).tobytes()
open(os.path.join(OUT, 'loadpic.rle'), 'wb').write(g.rle(bytes(planes)))
L = ['; generated by tools/make_loading.py']
L.append('loadpal:\tdc.w\t' + ','.join('$%x%x%x' % c for c in pal12))
L.append('BAR_X0\tequ\t%d\nBAR_Y0\tequ\t%d\nBAR_X1\tequ\t%d\nBAR_Y1\tequ\t%d' % BAR)
L.append('TXT_X\tequ\t%d\nTXT_Y\tequ\t%d' % (TXT[0] // 8 + 1, TXT[1] + 1))
L.append('C_BARBG\tequ\t%d\nC_BARFG\tequ\t%d\nC_TXT\tequ\t%d\nC_TXTBG\tequ\t%d' % (bar_bg, bar_fg, txt_c, txt_bg))
open(os.path.join(OUT, 'loadpic.i'), 'w').write('\n'.join(L) + '\n')
q.convert('RGB').resize((640, 512), Image.NEAREST).save(os.path.join(OUT, 'preview_loading.png'))
print('loading picture: %d bytes packed' % len(g.rle(bytes(planes))))
