#!/usr/bin/env python3
"""make_main.py - graphics, sounds, music and tables of the main program of Stronkie's Olympics.
Writes build/gen/main_chip.bin, main_data.i, main_equ.i, title.rle, menu.rle, podium.rle, font8.bin, previews.
Created By Mark Stronks, Stronkie Soft."""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gfxlib as g

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(g.ROOT, 'build', 'gen')
os.makedirs(OUT, exist_ok=True)
VER = os.environ.get('VER', '0.1'); DEMO = os.environ.get('DEMO', '0') == '1'
random.seed(2026)

PAL = [0x013, 0x000, 0xfff, 0xfd0, 0xd22, 0x126, 0x25c, 0x6af, 0x2a4, 0x162, 0xf80, 0x999, 0x555, 0xfc3, 0xccd, 0xc73,
       0x238, 0x34a, 0x46c, 0x8bd, 0xdde, 0xa85, 0x743, 0x383, 0x5b5]
(BG, BLACK, WHITE, YELLOW, RED, DBLUE, BLUE, LBLUE, GREEN, DGREEN, ORANGE, GREY, DGREY, GOLD, SILVER, BRONZE,
 S1, S2, S3, S4, LIGHT, TRACK, TRACKD, GRASS, GRASSL) = range(25)

def quant(im_rgb, dither=True):
    pal = PAL + [0xf0f] * 7
    q = (g.quantize_dither if dither else g.quantize_to)(im_rgb, pal)
    a = np.array(q); a[a >= 25] = BG
    out = Image.fromarray(a.astype(np.uint8), "P").copy(); return out

# ------------------------------------------------------------------ countries
# name, flag, (shirt, shorts, shoes), cpu names
C = [('NETHERLANDS', 'h:4,2,6', (0xf70, 0xfff, 0x222), ('JAN', 'SANNE')),
     ('GERMANY', 'h:1,4,3', (0xeee, 0x222, 0x111), ('LUKAS', 'ANNA')),
     ('BELGIUM', 'v:1,3,4', (0xd22, 0x222, 0x111), ('WOUT', 'LOTTE')),
     ('FRANCE', 'v:5,2,4', (0x24c, 0xfff, 0x222), ('PIERRE', 'CHLOE')),
     ('BRITAIN', 'uk', (0xfff, 0x126, 0x111), ('OLIVER', 'EMMA')),
     ('USA', 'usa', (0x226, 0xfff, 0x222), ('JAKE', 'MADISON')),
     ('CANADA', 'ca', (0xd22, 0xfff, 0x222), ('NOAH', 'AVA')),
     ('ITALY', 'v:8,2,4', (0x36d, 0xfff, 0x222), ('MARCO', 'GIULIA')),
     ('SPAIN', 'es', (0xd22, 0x126, 0x111), ('PABLO', 'LUCIA')),
     ('SWEDEN', 'nordic:6,3,-', (0xfd2, 0x25b, 0x222), ('ERIK', 'ELSA')),
     ('NORWAY', 'nordic:4,5,2', (0xd22, 0xfff, 0x222), ('OLE', 'INGRID')),
     ('DENMARK', 'nordic:4,2,-', (0xe33, 0xfff, 0x222), ('MADS', 'FREJA')),
     ('JAPAN', 'jp', (0x25b, 0xfff, 0x222), ('KENJI', 'YUKI')),
     ('BRAZIL', 'br', (0xfd2, 0x25b, 0x222), ('PEDRO', 'ANA')),
     ('AUSTRALIA', 'au', (0xfc2, 0x284, 0x222), ('JACK', 'MIA')),
     ('POLAND', 'h2:2,4', (0xfff, 0xd22, 0x222), ('JAKUB', 'ZOFIA')),
     ('SWITZERLAND', 'ch', (0xd22, 0xfff, 0x222), ('LUCA', 'LEA')),
     ('AUSTRIA', 'h:4,2,4', (0xc22, 0xfff, 0x111), ('FELIX', 'LENA')),
     ('IRELAND', 'v:8,2,10', (0x2a4, 0xfff, 0x222), ('SEAN', 'AOIFE')),
     ('MEXICO', 'mx', (0x284, 0xfff, 0x222), ('DIEGO', 'SOFIA'))]
NCTRY = len(C)

def shade(c, k=0.7):
    r, gg, b = (c >> 8) & 15, (c >> 4) & 15, c & 15
    return (int(r * k) << 8) | (int(gg * k) << 4) | int(b * k)

FW, FH = 24, 16
def flag(spec):
    im = Image.new('P', (FW, FH), WHITE); d = ImageDraw.Draw(im)
    kind, _, arg = spec.partition(':')
    if kind == 'h':
        cs = [int(v) for v in arg.split(',')]
        for i, c in enumerate(cs): d.rectangle([0, i * FH // 3, FW - 1, (i + 1) * FH // 3 + (1 if i == 2 else 0)], fill=c)
    elif kind == 'h2':
        cs = [int(v) for v in arg.split(',')]
        d.rectangle([0, 0, FW - 1, 7], fill=cs[0]); d.rectangle([0, 8, FW - 1, FH - 1], fill=cs[1])
    elif kind == 'v':
        cs = [int(v) for v in arg.split(',')]
        for i, c in enumerate(cs): d.rectangle([i * 8, 0, i * 8 + 7, FH - 1], fill=c)
    elif kind == 'nordic':
        a, b, c = arg.split(',')
        d.rectangle([0, 0, FW - 1, FH - 1], fill=int(a))
        if c != '-':
            d.rectangle([6, 0, 11, FH - 1], fill=int(c)); d.rectangle([0, 5, FW - 1, 10], fill=int(c))
            d.rectangle([7, 0, 10, FH - 1], fill=int(b)); d.rectangle([0, 6, FW - 1, 9], fill=int(b))
        else:
            d.rectangle([7, 0, 10, FH - 1], fill=int(b)); d.rectangle([0, 6, FW - 1, 9], fill=int(b))
    elif kind == 'uk':
        d.rectangle([0, 0, FW - 1, FH - 1], fill=DBLUE)
        d.line([0, 0, FW - 1, FH - 1], fill=WHITE, width=3); d.line([0, FH - 1, FW - 1, 0], fill=WHITE, width=3)
        d.line([0, 0, FW - 1, FH - 1], fill=RED, width=1); d.line([0, FH - 1, FW - 1, 0], fill=RED, width=1)
        d.rectangle([9, 0, 14, FH - 1], fill=WHITE); d.rectangle([0, 5, FW - 1, 10], fill=WHITE)
        d.rectangle([10, 0, 13, FH - 1], fill=RED); d.rectangle([0, 6, FW - 1, 9], fill=RED)
    elif kind == 'usa':
        for i in range(8): d.rectangle([0, i * 2, FW - 1, i * 2], fill=RED if i % 2 == 0 else WHITE)
        for i in range(8): d.line([0, i * 2 + 1, FW - 1, i * 2 + 1], fill=WHITE if i % 2 == 0 else RED)
        d.rectangle([0, 0, 10, 8], fill=DBLUE)
        for y in range(1, 8, 2):
            for x in range(1, 10, 2): d.point((x + (y // 2) % 2, y), fill=WHITE)
    elif kind == 'ca':
        d.rectangle([0, 0, 5, FH - 1], fill=RED); d.rectangle([18, 0, FW - 1, FH - 1], fill=RED)
        d.polygon([(12, 2), (14, 6), (17, 5), (15, 10), (12, 12), (9, 10), (7, 5), (10, 6)], fill=RED); d.line([12, 11, 12, 14], fill=RED)
    elif kind == 'es':
        d.rectangle([0, 0, FW - 1, FH - 1], fill=RED); d.rectangle([0, 4, FW - 1, 11], fill=YELLOW)
        d.rectangle([5, 6, 7, 9], fill=RED)
    elif kind == 'jp':
        d.ellipse([7, 3, 16, 12], fill=RED)
    elif kind == 'br':
        d.rectangle([0, 0, FW - 1, FH - 1], fill=GREEN); d.polygon([(12, 1), (22, 8), (12, 14), (2, 8)], fill=YELLOW)
        d.ellipse([8, 4, 15, 11], fill=DBLUE)
    elif kind == 'au':
        d.rectangle([0, 0, FW - 1, FH - 1], fill=DBLUE)
        d.line([0, 0, 11, 7], fill=WHITE); d.line([0, 7, 11, 0], fill=WHITE)
        d.rectangle([5, 0, 6, 7], fill=RED); d.rectangle([0, 3, 11, 4], fill=RED)
        for (x, y) in ((5, 12), (17, 3), (20, 7), (16, 10), (18, 13)): d.point((x, y), fill=WHITE); d.point((x + 1, y), fill=WHITE)
    elif kind == 'ch':
        d.rectangle([0, 0, FW - 1, FH - 1], fill=RED); d.rectangle([10, 3, 13, 12], fill=WHITE); d.rectangle([6, 6, 17, 9], fill=WHITE)
    elif kind == 'mx':
        d.rectangle([0, 0, 7, FH - 1], fill=GREEN); d.rectangle([16, 0, FW - 1, FH - 1], fill=RED)
        d.ellipse([10, 6, 13, 9], fill=TRACKD)
    d.rectangle([0, 0, FW - 1, FH - 1], outline=BLACK)
    return im

# ------------------------------------------------------------------ backgrounds
def stadium(rgb, top=0, h=96, rows=True):
    d = ImageDraw.Draw(rgb)
    for y in range(top, top + h):
        k = (y - top) / h
        d.line([0, y, 319, y], fill=(int(30 + 30 * k), int(40 + 40 * k), int(80 + 60 * k)))
    for y in range(top + 6, top + h, 4):                      # rows of the stands
        d.line([0, y, 319, y], fill=(20, 25, 45))
    for i in range(3200 if rows else 0):                    # the crowd
        x = random.randrange(320); y = random.randrange(top + 4, top + h - 2)
        col = random.choice([(230, 60, 50), (240, 240, 240), (250, 200, 40), (60, 120, 220), (240, 140, 40), (40, 160, 80), (230, 190, 150)])
        d.point((x, y), fill=col)

def title_bg():
    rgb = Image.new('RGB', (320, 256)); d = ImageDraw.Draw(rgb)
    for y in range(256):                                      # evening sky
        k = y / 255
        d.line([0, y, 319, y], fill=(int(20 + 40 * k), int(30 + 60 * k), int(80 + 100 * k)))
    stadium(rgb, 92, 70)
    d.rectangle([0, 162, 319, 255], fill=(50, 140, 60))
    for y in range(170, 256, 14): d.rectangle([0, y, 319, y + 6], fill=(70, 170, 80))
    # floodlights
    for x in (18, 302):
        d.rectangle([x - 2, 40, x + 2, 160], fill=(80, 80, 90))
        d.rectangle([x - 12, 30, x + 12, 42], fill=(200, 200, 200))
        for i in range(4): d.ellipse([x - 11 + i * 6, 32, x - 7 + i * 6, 38], fill=(255, 255, 220))
    # the torch
    for tx in (40, 280):
        ty = 70
        d.polygon([(tx - 7, ty), (tx + 7, ty), (tx + 3, ty + 24), (tx - 3, ty + 24)], fill=(200, 160, 60))
        d.rectangle([tx - 9, ty - 4, tx + 9, ty], fill=(240, 200, 90))
        for r, col in ((11, (255, 120, 20)), (7, (255, 200, 40)), (3, (255, 250, 200))):
            d.polygon([(tx - r, ty - 4), (tx + r, ty - 4), (tx + r // 2, ty - 4 - 3 * r), (tx, ty - 4 - 2 * r), (tx - r // 3, ty - 4 - 3 * r - 3)], fill=col)
    im = quant(rgb)
    # title text, gold with a black outline
    t = Image.new('RGBA', (320, 70), (0, 0, 0, 0)); td = ImageDraw.Draw(t)
    f = g.ttf(26); f2 = g.ttf(30)
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            td.text((160 + dx, 14 + dy), "STRONKIE'S", font=f, fill=(0, 0, 0, 255), anchor='mm')
            td.text((160 + dx, 46 + dy), 'OLYMPICS', font=f2, fill=(0, 0, 0, 255), anchor='mm')
    td.text((160, 14), "STRONKIE'S", font=f, fill=(255, 210, 0, 255), anchor='mm')
    td.text((160, 46), 'OLYMPICS', font=f2, fill=(255, 210, 0, 255), anchor='mm')
    a = np.array(t); px = im.load()
    for y in range(70):
        for x in range(320):
            if a[y, x, 3] > 128:
                c = tuple(a[y, x, :3])
                px[x, y + 2] = BLACK if c == (0, 0, 0) else (GOLD if y % 8 < 5 else YELLOW)
    paste_logo(im, 236, 232)
    return im

LOGO_MAP = {(10, 10, 30): BLACK, (255, 226, 30): YELLOW, (40, 200, 240): LBLUE, (225, 150, 0): ORANGE,
            (255, 255, 255): WHITE, (0, 0, 0): BLACK}
def paste_logo(im, x0, y0):
    lg = Image.open(os.path.join(g.ROOT, 'assets', 'stronkiesoft_logo.png')).convert('RGBA')
    px = im.load(); lp = lg.load()
    for y in range(lg.height):
        for x in range(lg.width):
            r, gg, b, a = lp[x, y]
            if a > 128:
                best = min(LOGO_MAP, key=lambda k: sum((k[i] - (r, gg, b)[i]) ** 2 for i in range(3)))
                px[x0 + x, y0 + y] = LOGO_MAP[best]

def menu_bg():
    rgb = Image.new('RGB', (320, 256)); d = ImageDraw.Draw(rgb)
    stadium(rgb, 0, 40)
    d.rectangle([0, 40, 319, 255], fill=(20, 30, 60))
    for y in range(44, 256, 2): d.line([0, y, 319, y], fill=(24, 36, 70))
    im = quant(rgb, dither=False)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 40, 319, 41], fill=GOLD)
    d.rectangle([0, 246, 319, 255], fill=DBLUE); d.line([0, 246, 319, 246], fill=GOLD)
    return im

def podium_bg():
    rgb = Image.new('RGB', (320, 256)); d = ImageDraw.Draw(rgb)
    for y in range(256):
        k = y / 255
        d.line([0, y, 319, y], fill=(int(20 + 30 * k), int(30 + 50 * k), int(80 + 80 * k)))
    stadium(rgb, 60, 80)
    d.rectangle([0, 140, 319, 255], fill=(50, 140, 60))
    im = quant(rgb)
    d = ImageDraw.Draw(im)
    for (x0, x1, top, col, n) in ((40, 120, 196, SILVER, '2'), (120, 200, 176, GOLD, '1'), (200, 280, 208, BRONZE, '3')):
        d.rectangle([x0, top, x1 - 1, 239], fill=col, outline=BLACK)
        d.rectangle([x0, top, x1 - 1, top + 3], fill=WHITE)
        f = g.ttf(22); d.text(((x0 + x1) / 2, top + 22), n, font=f, fill=BLACK, anchor='mm')
    d.rectangle([0, 240, 319, 255], fill=DBLUE); d.line([0, 240, 319, 240], fill=GOLD)
    return im

# ------------------------------------------------------------------ icons of the events (32x24)
def icon(kind):
    im = g.bob_canvas(32, 24); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, 31, 23], 4, fill=DBLUE, outline=GOLD)
    if kind == 0:     # soccer ball
        d.ellipse([8, 3, 23, 18], fill=WHITE, outline=BLACK)
        d.polygon([(15, 8), (18, 10), (17, 13), (14, 13), (13, 10)], fill=BLACK)
        d.line([15, 8, 15, 4], fill=BLACK); d.line([18, 10, 22, 9], fill=BLACK); d.line([13, 10, 9, 9], fill=BLACK)
        d.line([17, 13, 19, 17], fill=BLACK); d.line([14, 13, 12, 17], fill=BLACK)
    elif kind == 1:   # basketball
        d.ellipse([8, 3, 23, 18], fill=ORANGE, outline=BLACK)
        d.line([8, 11, 23, 11], fill=BLACK); d.line([15, 3, 15, 18], fill=BLACK)
        d.arc([4, 3, 13, 18], -60, 60, fill=BLACK); d.arc([18, 3, 27, 18], 120, 240, fill=BLACK)
    elif kind == 2:   # volleyball
        d.ellipse([8, 3, 23, 18], fill=WHITE, outline=BLACK)
        d.arc([10, -4, 30, 14], 100, 200, fill=BLUE); d.arc([2, 6, 20, 26], 280, 20, fill=YELLOW); d.arc([6, 2, 26, 22], 160, 250, fill=BLUE)
    elif kind == 3:   # bowling pin and ball
        d.ellipse([12, 3, 17, 8], fill=WHITE, outline=BLACK); d.rectangle([13, 8, 16, 10], fill=WHITE)
        d.ellipse([10, 9, 19, 20], fill=WHITE, outline=BLACK); d.line([13, 8, 16, 8], fill=RED)
        d.ellipse([18, 11, 27, 20], fill=BLUE, outline=BLACK); d.point((21, 14), fill=BLACK); d.point((23, 14), fill=BLACK)
    elif kind == 4:   # surfboard on a wave
        d.arc([2, 8, 30, 36], 180, 360, fill=LBLUE, width=3)
        d.polygon([(6, 14), (26, 7), (27, 9), (8, 16)], fill=YELLOW, outline=BLACK)
    elif kind == 5:   # skateboard
        d.rounded_rectangle([4, 9, 27, 13], 2, fill=RED, outline=BLACK)
        d.ellipse([7, 13, 11, 17], fill=WHITE, outline=BLACK); d.ellipse([20, 13, 24, 17], fill=WHITE, outline=BLACK)
    return im

# ------------------------------------------------------------------ sounds
def sounds(o):
    R = 6000
    o.sample('cs_cheer', g.crowd(1.3, R, 3), R)
    clap = np.zeros(int(0.9 * R)); rng = np.random.default_rng(5)
    for i in range(70):
        p = rng.integers(0, len(clap) - 300); clap[p:p + 300] += g.noise(300, i) * np.exp(-np.arange(300) / 30) * rng.uniform(0.3, 1)
    clap *= np.minimum(1, np.linspace(1.6, 0, len(clap)))
    o.sample('cs_clap', g.tosamp(clap), R)
    R2 = 11025
    o.sample('cs_beep', g.beep(880, 0.08, R2), R2)
    o.sample('cs_beephi', g.beep(1760, 0.12, R2), R2)
    o.sample('cs_buzzer', g.tosamp(g.beep(110, 0.35, 8000) + g.beep(113, 0.35, 8000)), 8000)
    o.sample('cs_whistle', g.whistle(0.45, 8000), 8000)
    ooh = np.zeros(int(0.7 * R)); t = np.arange(len(ooh)) / R
    for i in range(8):
        f = 180 + i * 37
        ooh += np.sin(2 * np.pi * f * (1 + 0.15 * (1 - t)) * t) * 0.15
    ooh = ooh * np.minimum(1, t / 0.1) * np.exp(-t / 0.5) + g.bandnoise(len(ooh), 4, 40, 9) * 0.3 * np.exp(-t / 0.5)
    o.sample('cs_ooh', g.tosamp(ooh), R)
    V = 6000
    o.sample('cs_ready', g.speak('r e d i'), V)
    o.sample('cs_go', g.speak('g oU'), V)
    o.sample('cs_timeup', g.speak('t aI m V p'), V)
    o.sample('cs_great', g.speak('g r eI t'), V)
    o.sample('cs_ohno', g.speak('oU n oU'), V)
    o.sample('cs_gameover', g.speak('g eI m oU v @ r'), V)
    o.sample('v_gold', g.speak('g oU l d m e d @ l'), V)
    o.sample('v_silver', g.speak('s I l v @ r m e d @ l'), V)
    o.sample('v_bronze', g.speak('b r o n z m e d @ l'), V)
    o.sample('v_record', g.speak('n j u w @ r l d r e k o r d'), V)
    o.sample('v_title', g.speak('s t r o N k i z oU l I m p I k s'), V)
    o.raw('csnd_tab\tdc.l\tcs_cheer,cs_clap,cs_beep,cs_buzzer,cs_whistle,cs_ready,cs_go,cs_timeup,cs_great,cs_ohno,cs_gameover,cs_beephi,cs_ooh')

# ------------------------------------------------------------------ music (quiet: the game plays it at low volume)
# the title music: an original stadium fanfare by Stronkie Soft (brass melody, marching bass)
THEME_M = ('G4/2 C5/3 C5/1 C5/4 D5/2 E5/2 C5/4 G4/4 A4/2 B4/2 C5/2 D5/4 '
           'E5/3 F5/1 E5/2 D5/2 C5/4 B4/4 A4/2 B4/2 C5/2 D5/2 C5/8 '
           'E5/2 E5/1 E5/1 G5/4 E5/2 C5/2 D5/4 B4/4 C5/2 D5/2 E5/2 F5/2 E5/4 D5/4 '
           'G4/2 C5/3 C5/1 C5/4 D5/2 E5/2 F5/4 E5/2 D5/2 C5/8 -/8')
THEME_B = ('C3/8 E3/8 F3/8 G3/8 A2/8 E3/8 F3/4 G3/4 C3/8 '
           'C3/8 E3/8 G3/8 G2/8 C3/8 F3/8 G3/8 C3/8 -/8')
FANFARE_M = 'G4/2 G4/1 G4/1 C5/6 G4/2 C5/2 E5/8 D5/2 C5/2 D5/2 E5/2 C5/10 -/8'
FANFARE_B = 'C3/4 C3/4 C3/4 G2/4 C3/4 G2/4 F2/4 G2/4 C3/8 -/8'

def main():
    o = g.Out(OUT, 'main')
    # athletes for the creation screen and the title (player colours)
    o.bob('ath_man', g.athlete(g.pose_stand()))
    o.bob('ath_woman', g.athlete(g.pose_stand(), woman=True))
    o.bobs('runner', [g.athlete(p) for p in g.run_cycle(6)])
    o.bobs('runnerw', [g.athlete(p, woman=True) for p in g.run_cycle(6)])
    o.bobs('flag', [flag(c[1]) for c in C])
    o.bobs('icon', [icon(i) for i in range(6)])
    # medal
    for nm, col in (('medal_g', GOLD), ('medal_s', SILVER), ('medal_b', BRONZE)):
        im = g.bob_canvas(16, 16); d = ImageDraw.Draw(im)
        d.polygon([(4, 0), (7, 0), (8, 6), (5, 6)], fill=RED); d.polygon([(9, 0), (12, 0), (11, 6), (8, 6)], fill=BLUE)
        d.ellipse([3, 5, 12, 14], fill=col, outline=BLACK); d.point((6, 8), fill=WHITE)
        o.bob(nm, im)
    sounds(o)
    for line in g.song_lines('song_theme', THEME_M, THEME_B, 7): o.raw(line)
    for line in g.song_lines('song_fanfare', FANFARE_M, FANFARE_B, 6): o.raw(line)
    # tables
    o.raw(g.palette_line('pal_main', PAL))
    o.raw('hair_cols\tdc.w\t$111,$630,$ec6,$c51')
    o.raw('skin_cols\tdc.w\t$fc9,$c96,$c86,$964,$853,$532')
    kits = []
    for c in C:
        sh, so, se = c[2]
        kits += ['$%03x' % sh, '$%03x' % shade(sh), '$%03x' % so, '$%03x' % se]
    o.raw('kit_cols\tdc.w\t' + ','.join(kits))
    for i, c in enumerate(C):
        o.raw('ctry_n%d\tdc.b\t\'%s\',0' % (i, c[0]))
        o.raw('cpu_n%da\tdc.b\t\'%s\',0\ncpu_n%db\tdc.b\t\'%s\',0' % (i, c[3][0], i, c[3][1]))
    o.raw('\teven')
    o.raw('ctry_names\tdc.l\t' + ','.join('ctry_n%d' % i for i in range(NCTRY)))
    o.raw('cpu_names\tdc.l\t' + ','.join('cpu_n%da,cpu_n%db' % (i, i) for i in range(NCTRY)))
    dbl = []
    for b in range(256):
        v = 0
        for i in range(8):
            if b & (0x80 >> i): v |= 0xc000 >> (2 * i)
        dbl.append(v)
    for i in range(0, 256, 16): o.raw(('dbl_tab' if i == 0 else '') + '\tdc.w\t' + ','.join('$%04x' % v for v in dbl[i:i + 16]))
    # the starting world records: score, name (12), country
    recs = [(9, 'PELE JR', 13), (25, 'B.JORDAN', 5), (16, 'K.KIRALY', 5), (268, 'E.STRIKE', 0), (180, 'K.SLATER', 5), (170, 'T.HAWK', 5)]
    o.raw("def_records\tdc.b\t'SOR1'")
    for sc, nm, ct in recs:
        o.raw('\tdc.l\t%d\n\tdc.b\t\'%s\'%s\n\tdc.w\t%d,0' % (sc, nm, ',0' * (12 - len(nm)), ct))
    o.raw('\tdcb.b\t%d,0' % (128 - 4 - 6 * 20))
    o.raw('\teven')
    o.equ('NCTRY', NCTRY)
    n = o.write()
    # backgrounds
    for nm, im in (('title', title_bg()), ('menu', menu_bg()), ('podium', podium_bg())):
        g.save_screen(im, os.path.join(OUT, nm + '.rle'))
        g.preview(im, PAL, os.path.join(OUT, 'preview_%s.png' % nm))
    open(os.path.join(OUT, 'font8.bin'), 'wb').write(g.font_bin())
    open(os.path.join(OUT, 'build.i'), 'w').write('DEMO\tequ\t%d\nVERSION_STR\tmacro\n' % (1 if DEMO else 0))
    open(os.path.join(OUT, 'build.i'), 'w').write('DEMO\tequ\t%d\n' % (1 if DEMO else 0))
    open(os.path.join(OUT, 'version.i'), 'w').write("\tdc.b\t'V%s%s',0\n" % (VER, ' DEMO' if DEMO else ''))
    # preview sheet of the flags
    sheet = Image.new('P', (NCTRY * 26, 18), BG)
    for i, c in enumerate(C): sheet.paste(flag(c[1]), (i * 26, 1))
    g.preview(sheet, PAL, os.path.join(OUT, 'preview_flags.png'), 3)
    print('main: %d bytes chip data, %d countries' % (n, NCTRY))

if __name__ == '__main__':
    main()
