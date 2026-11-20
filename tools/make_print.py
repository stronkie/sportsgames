#!/usr/bin/env python3
"""make_print.py - the print kit of Stronkie's Olympics, like the old boxed games:
  print/StronkiesOlympics_Manual.pdf      the manual: an A5 booklet of 24 pages
  print/StronkiesOlympics_DiskLabels.pdf  3.5" disk labels (A4: a colour page and a black-and-white page)
  print/StronkiesOlympics_Box.pdf         the box (A3): page 1 the flat box to cut and fold, page 2 the box in 3D
Created By Mark Stronks, Stronkie Soft."""
import os, sys, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import events

_paste = Image.Image.paste
def _ipaste(self, im, box=None, mask=None):
    if isinstance(box, tuple): box = tuple(int(round(v)) for v in box)
    return _paste(self, im, box, mask)
Image.Image.paste = _ipaste

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SHOT = os.path.join(ROOT, 'screenshots')
GEN = os.path.join(ROOT, 'build', 'gen')
OUT = os.path.join(ROOT, 'print')
TMP = os.path.join(ROOT, 'build', 'print')
os.makedirs(OUT, exist_ok=True); os.makedirs(TMP, exist_ok=True)
VER = os.environ.get('VER', '0.4')
F = '/usr/share/fonts/truetype/dejavu/'
for n, f in (('Sans', 'DejaVuSans.ttf'), ('SansB', 'DejaVuSans-Bold.ttf'), ('SansC', 'DejaVuSansCondensed.ttf'),
             ('SansCB', 'DejaVuSansCondensed-Bold.ttf'), ('Serif', 'DejaVuSerif.ttf'), ('SerifB', 'DejaVuSerif-Bold.ttf'),
             ('SerifI', 'DejaVuSerif-Italic.ttf'), ('Mono', 'DejaVuSansMono.ttf')):
    pdfmetrics.registerFont(TTFont(n, F + f))
COUNTRIES = ['NETHERLANDS', 'GERMANY', 'BELGIUM', 'FRANCE', 'BRITAIN', 'USA', 'CANADA', 'ITALY', 'SPAIN', 'SWEDEN', 'NORWAY',
             'DENMARK', 'JAPAN', 'BRAZIL', 'AUSTRALIA', 'POLAND', 'SWITZERLAND', 'AUSTRIA', 'IRELAND', 'MEXICO']
NAVY, GOLD, RED, CREAM, INK = (0.07, 0.11, 0.30), (0.98, 0.78, 0.10), (0.80, 0.12, 0.12), (0.99, 0.97, 0.90), (0.10, 0.09, 0.08)
DISKS = {}
for l in open(os.path.join(GEN, 'disks.txt')):
    f, d = l.split(); DISKS[f] = int(d)

def ctitle(n): return 'USA' if n == 'USA' else n.title()

def shot(name): return Image.open(os.path.join(SHOT, name + '.png')).convert('RGB')
def gen(name): return Image.open(os.path.join(GEN, name)).convert('RGB')
def img(im, key):
    p = os.path.join(TMP, key + '.png'); im.save(p); return p

def logo(rgba=False):
    """the game's logo, cut from the loading picture: STRONKIE'S (torch) OLYMPICS"""
    im = gen('preview_loading.png').crop((36, 84, 604, 188))
    if not rgba: return im
    a = np.array(im).astype(int); bg = a[2, 2]
    # (the night sky behind it: dark blue; everything brighter or warmer is the logo)
    lum = a.sum(2); keep = (lum > 200) | (a[:, :, 0] > 120)
    m = Image.fromarray((keep * 255).astype('uint8'), 'L').filter(ImageFilter.MaxFilter(3))
    out = im.convert('RGBA'); out.putalpha(m); return out

def robot():
    """the Stronkie Soft logo (the robot and the name) from the loading picture"""
    return gen('preview_loading.png').crop((150, 0, 490, 76))

def flags():
    return gen('preview_flags.png')

def pix(im, scale):
    return im.resize((im.size[0] * scale, im.size[1] * scale), Image.NEAREST)

# ------------------------------------------------------------------ text helpers
def wrap(c, text, font, size, width):
    out = []
    for para in text.split('\n'):
        words = para.split(' '); line = ''
        for w in words:
            t = (line + ' ' + w).strip()
            if c.stringWidth(t, font, size) <= width: line = t
            else:
                if line: out.append(line)
                line = w
        out.append(line)
    return out

def para(c, x, y, w, text, font='Serif', size=8.6, lead=None, color=INK):
    lead = lead or size * 1.32
    c.setFillColorRGB(*color); c.setFont(font, size)
    for l in wrap(c, text, font, size, w):
        c.drawString(x, y, l); y -= lead
    return y

def head(c, x, y, text, size=13, color=NAVY, font='SansB'):
    c.setFillColorRGB(*color); c.setFont(font, size); c.drawString(x, y, text)
    return y - size * 1.25

def picture(c, im, x, y, w, frame=True, key=None):
    """the image with its top left at x, y (points), w wide; -> the y under it"""
    h = w * im.size[1] / im.size[0]
    c.drawImage(ImageReader(im), x, y - h, w, h, mask='auto' if im.mode == 'RGBA' else None)
    if frame:
        c.setStrokeColorRGB(*INK); c.setLineWidth(0.8); c.rect(x, y - h, w, h)
    return y - h

# ------------------------------------------------------------------ the manual (A5)
A5W, A5H = 148 * mm, 210 * mm
M = 13 * mm

def page_frame(c, n, title=None):
    c.setFillColorRGB(*CREAM); c.rect(0, 0, A5W, A5H, fill=1, stroke=0)
    c.setFillColorRGB(*NAVY); c.rect(0, A5H - 9 * mm, A5W, 9 * mm, fill=1, stroke=0)
    c.setFillColorRGB(*GOLD); c.rect(0, A5H - 9.8 * mm, A5W, 0.8 * mm, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1); c.setFont('SansB', 7.5)
    c.drawString(M, A5H - 6 * mm, "STRONKIE'S OLYMPICS")
    if title: c.drawRightString(A5W - M, A5H - 6 * mm, title.upper())
    c.setFillColorRGB(*NAVY); c.setFont('SansB', 8); c.drawCentredString(A5W / 2, 7 * mm, '- %d -' % n)
    # the five-coloured stripe at the bottom (not the rings: stripes)
    for i, col in enumerate([(0.1, 0.4, 0.8), (0.95, 0.75, 0.1), (0.1, 0.1, 0.1), (0.1, 0.6, 0.25), (0.85, 0.15, 0.15)]):
        c.setFillColorRGB(*col); c.rect(i * A5W / 5, 0, A5W / 5, 2.2 * mm, fill=1, stroke=0)

def box_note(c, x, y, w, title, text, size=8):
    lines = wrap(c, text, 'Serif', size, w - 6 * mm)
    h = len(lines) * size * 1.3 + 13 * mm / 1.6
    c.setFillColorRGB(1, 0.95, 0.75); c.setStrokeColorRGB(*NAVY); c.setLineWidth(1)
    c.roundRect(x, y - h, w, h, 2 * mm, fill=1, stroke=1)
    c.setFillColorRGB(*RED); c.setFont('SansB', 8.5); c.drawString(x + 3 * mm, y - 5 * mm, title)
    yy = y - 9.5 * mm
    c.setFillColorRGB(*INK); c.setFont('Serif', size)
    for l in lines: c.drawString(x + 3 * mm, yy, l); yy -= size * 1.3
    return y - h

def rec_text(e):
    v, who, ctry = e[5]
    if e[3] == 1: s = '%d.%02d S' % (v // 100, v % 100)
    elif e[3] == 2: s = '%d.%02d M' % (v // 100, v % 100)
    else: s = '%d %s' % (v, e[2])
    return '%s  -  %s (%s)' % (s, who, ctitle(COUNTRIES[ctry]))

EV_SHOT = {'SOCCER': '05_soccer_shot', 'BASKETBALL': '07_basketball', 'VOLLEYBALL': '08_volleyball', 'BOWLING': '09_bowling',
           'SURFING': '10_surfing', 'SKATEBOARDING': '11_skateboarding', '100M SPRINT': '13_sprint', 'HURDLES': '14_hurdles',
           'LONG JUMP': '15_longjump', 'JAVELIN': '16_javelin', 'ARCHERY': '17_archery', 'SWIMMING': '18_swimming',
           'WEIGHTLIFTING': '19_weightlifting', 'CYCLING': '20_cycling', 'ROOT BEER SPRINT': '21_rootbeer',
           'PIE DODGE': '22_piedodge', 'PENGUIN CURLING': '23_curling', 'TOILET PAPER THROW': '24_toiletpaper'}
TIPS = {
 'SOCCER': 'The keeper guesses too. Aim for a corner and keep the power just under the bar.',
 'BASKETBALL': 'Find the rhythm of the green zone on the first rack - it is the same for every ball.',
 'VOLLEYBALL': 'Jump early: a hit at the top of your jump becomes a spike.',
 'BOWLING': 'A little spin into the pocket between the 1 and 3 pins knocks down the most.',
 'SURFING': 'Stay close to the curl for the big points, but not too close...',
 'SKATEBOARDING': 'Pump low in the pipe: speed first, tricks later.',
 '100M SPRINT': 'A steady fast waggle beats a wild one. Wait for GO - or it is a false start!',
 'HURDLES': 'Jump a little before each hurdle. Hitting one costs half your speed.',
 'LONG JUMP': 'Full speed, fire right at the board, and let go of fire at about 45.',
 'JAVELIN': 'The same as the long jump: speed, the line, 45 - and watch it fly.',
 'ARCHERY': 'Steer against the sway and aim a little into the wind: >>> means aim left.',
 'SWIMMING': 'Breathe before the AIR bar runs out - out of air you swim very slowly.',
 'WEIGHTLIFTING': 'Do not fire too soon: wait until the bar turns green over the line.',
 'CYCLING': 'Start in gear 1 and change up as you pick up speed. Gear 4 or 5 for the finish.',
 'ROOT BEER SPRINT': 'Sip, do not chug: drink until the HIC bar is red, let go, drink again.',
 'PIE DODGE': 'Pies fly straight up and down: watch the gaps, then dash across.',
 'PENGUIN CURLING': 'Better too short than too long: sweeping makes it slide further, nothing makes it slow down.',
 'TOILET PAPER THROW': 'With the wind at your back (+) go for it; against the wind a lower angle helps.'}
ABOUT = {
 'SOCCER': 'A penalty shoot-out against another country. Five shots each, then sudden death - and you are the keeper too.',
 'BASKETBALL': 'The three point shoot-out: five racks of five balls in 60 seconds. The last ball of each rack is the money ball.',
 'VOLLEYBALL': 'Beach volleyball, one against one. The first to 7 points wins.',
 'BOWLING': 'Ten pin bowling, ten frames, with real strikes and spares.',
 'SURFING': 'Ride the wave for 60 seconds: turns, airs off the lip and spins. Three wipe-outs and you are out.',
 'SKATEBOARDING': 'The half pipe: pump, fly over the lip, turn, grab and spin. Three falls and you are out.',
 '100M SPRINT': 'Ten seconds of pure joystick power against a runner from another country.',
 'HURDLES': '110 metres and ten hurdles. Speed AND timing.',
 'LONG JUMP': 'Run, jump from the white board, land in the sand. Three jumps, the best one counts.',
 'JAVELIN': 'Run, throw at the line and watch your javelin fly over the field. Three throws.',
 'ARCHERY': 'Six arrows at the target. The sight sways and the wind blows.',
 'SWIMMING': '50 metres freestyle: dive in at GO, swim - and do not forget to breathe!',
 'WEIGHTLIFTING': 'Clean and jerk. After every good lift the bar gets 30 kg heavier.',
 'CYCLING': '500 metres on the wooden velodrome, with five gears.',
 'ROOT BEER SPRINT': "Drink, run, don't hiccup. First your mug, then the track.",
 'PIE DODGE': 'Cross the arena as often as you can in 60 seconds while 22 clowns throw cream pies at you.',
 'PENGUIN CURLING': 'Curling, but with penguins. Slide six of them into the house.',
 'TOILET PAPER THROW': 'The javelin with a toilet roll. It unrolls in the air - and the wind decides the rest.'}

def event_block(c, e, x, y, w):
    name = e[0]
    c.setFillColorRGB(*NAVY); c.rect(x, y - 7 * mm, w, 7 * mm, fill=1, stroke=0)
    c.setFillColorRGB(*GOLD); c.setFont('SansB', 10.5); c.drawString(x + 2.5 * mm, y - 5 * mm, name)
    tag = 'SILLY EVENT' if name in ('ROOT BEER SPRINT', 'PIE DODGE', 'PENGUIN CURLING', 'TOILET PAPER THROW') else 'DISK %d' % DISKS[e[1]]
    if 'SILLY' in tag: tag += '  -  DISK %d' % DISKS[e[1]]
    c.setFillColorRGB(1, 1, 1); c.setFont('Sans', 6.5); c.drawRightString(x + w - 2.5 * mm, y - 4.8 * mm, tag)
    y -= 9 * mm
    pw = w * 0.42
    bottom = picture(c, shot(EV_SHOT[name]), x, y, pw)
    tx = x + pw + 3 * mm; tw = w - pw - 3 * mm
    yy = para(c, tx, y - 7, tw, ABOUT[name], 'SerifI', 7.6)
    yy -= 2
    c.setFillColorRGB(*RED); c.setFont('SansB', 7); c.drawString(tx, yy, 'HOW TO PLAY'); yy -= 9
    yy = para(c, tx, yy, tw, sentence(e[6]), 'Serif', 7.1, 8.8)
    yy = min(yy, bottom - 3 * mm)
    c.setFillColorRGB(*RED); c.setFont('SansB', 7); c.drawString(x, yy, 'TIP:')
    yy = para(c, x + 7 * mm, yy, w - 7 * mm, TIPS[name], 'Serif', 7.3, 9)
    c.setFillColorRGB(*NAVY); c.setFont('SansB', 7); c.drawString(x, yy - 1, 'WORLD RECORD:')
    c.setFont('Sans', 7); c.drawString(x + 24 * mm, yy - 1, rec_text(e))
    return yy - 6 * mm

def sentence(lines):
    """the help lines of the game (capitals) as a sentence for the manual"""
    t = ' '.join(l.strip() for l in lines if l.strip())
    out = []; cap = True
    for ch in t.lower():
        out.append(ch.upper() if cap and ch.isalpha() else ch)
        if ch.isalpha(): cap = False
        if ch in '.!?:': cap = True
    s = ''.join(out)
    for w in ('Gold', 'GO', 'Esc'): pass
    return s.replace(' at go', ' at GO').replace('hic!', 'HIC!').replace(' esc', ' ESC').replace('Let go', 'let go')

def manual():
    path = os.path.join(OUT, 'StronkiesOlympics_Manual.pdf')
    c = canvas.Canvas(path, pagesize=(A5W, A5H))
    c.setTitle("Stronkie's Olympics - Manual"); c.setAuthor('Mark Stronks, Stronkie Soft')
    W = A5W - 2 * M
    # 1 the cover
    c.setFillColorRGB(*NAVY); c.rect(0, 0, A5W, A5H, fill=1, stroke=0)
    lg = logo(True); picture(c, pix(lg, 2), 8 * mm, A5H - 9 * mm, A5W - 16 * mm, frame=False)
    c.setFillColorRGB(1, 1, 1); c.setFont('SansB', 9.5); c.drawCentredString(A5W / 2, A5H - 42 * mm, 'THE SPORTS GAME FOR THE AMIGA 500')
    y = picture(c, shot('03_opening'), 12 * mm, A5H - 47 * mm, A5W - 24 * mm)
    c.setFillColorRGB(*GOLD); c.setFont('SansB', 22); c.drawCentredString(A5W / 2, y - 12 * mm, '18 EVENTS')
    c.setFillColorRGB(1, 1, 1); c.setFont('Sans', 8.5)
    c.drawCentredString(A5W / 2, y - 18 * mm, 'from the 100m sprint to penguin curling')
    picture(c, flags(), 12 * mm, y - 22 * mm, A5W - 24 * mm, frame=False)
    c.setFillColorRGB(*GOLD); c.rect(0, 27 * mm, A5W, 0.6 * mm, fill=1, stroke=0)
    c.setFont('SansB', 13); c.drawCentredString(A5W / 2, 19 * mm, 'INSTRUCTION MANUAL')
    picture(c, robot(), A5W / 2 - 17 * mm, 15 * mm, 34 * mm, frame=False)
    c.showPage()
    # 2 contents
    page_frame(c, 2, 'Contents')
    y = head(c, M, A5H - 22 * mm, 'CONTENTS', 15)
    toc = [('Welcome to the Games', 3), ('Getting started', 4), ('The main menu', 5), ('Your athlete', 6), ('Playing the Games', 7),
           ('The events', 8), ('  The first six', 8), ('  The classic Olympic events', 11), ('  The silly events', 15),
           ('The ceremonies', 17), ('Did you know?', 18), ('From the dev log', 19), ('Hints and tips', 21),
           ('Hall of Fame', 22), ('Credits', 23)]
    c.setFont('Serif', 10)
    for t, p in toc:
        y -= 4 * mm
        c.setFillColorRGB(*INK); c.drawString(M + 2 * mm, y, t)
        dots = '.' * int((W - c.stringWidth(t, 'Serif', 10) - 12 * mm) / c.stringWidth('.', 'Serif', 10))
        c.setFillColorRGB(0.5, 0.5, 0.5); c.drawString(M + 3 * mm + c.stringWidth(t, 'Serif', 10), y, dots)
        c.setFillColorRGB(*NAVY); c.drawRightString(A5W - M, y, str(p))
    y -= 12 * mm
    box_note(c, M, y, W, 'ON THESE DISKS', 'Disk 1 boots the game: the main program, the opening and closing ceremonies, the world '
             'records and the first five events. Disk 2 holds skateboarding and twelve more events, disk 3 the toilet paper throw. '
             'The game tells you when it needs another disk.')
    c.showPage()
    # 3 welcome
    page_frame(c, 3, 'Welcome')
    y = head(c, M, A5H - 22 * mm, 'WELCOME TO THE GAMES!', 15)
    y = para(c, M, y - 2, W,
             "The torch is lit, the crowd is on its feet and twenty countries march into the stadium. One of the flags "
             "is yours. Somewhere between them walks an athlete with your name on the shirt - an athlete who has trained "
             "for years, who has given up chips, sweets and late nights, and who has never once thrown a toilet roll in "
             "anger.\n\nUntil today.\n\nStronkie's Olympics takes you through eighteen events: the classics everybody knows - "
             "the 100 metres, the hurdles, the long jump, the javelin, swimming, archery, weightlifting and cycling - six "
             "sports from the beach and the street, and four events that the real Olympic committee has, for some reason, "
             "never said yes to. Root beer. Pies. Penguins. Toilet paper.\n\nPlay alone or with up to four friends on one "
             "joystick, each with your own athlete and your own country. Win gold and you stand on the highest step of the "
             "podium while your national anthem plays. Break a world record and your name stays on disk - until someone "
             "else breaks it.\n\nGood luck. Do not forget to breathe.", 'Serif', 9.2, 12.4)
    picture(c, shot('01_title'), M + 12 * mm, y - 4 * mm, W - 24 * mm)
    c.showPage()
    # 4 getting started
    page_frame(c, 4, 'Getting started')
    y = head(c, M, A5H - 22 * mm, 'GETTING STARTED', 15)
    y = head(c, M, y - 2, 'What you need', 10.5, RED)
    y = para(c, M, y, W, 'An Amiga 500 (or any Amiga with a 68000) with Kickstart 1.3 or higher and 1 MB of memory: '
             '512K chip memory plus the 512K trapdoor expansion. A joystick in port 2 - or the cursor keys and RETURN.')
    y = head(c, M, y - 6, 'From floppy disk', 10.5, RED)
    y = para(c, M, y, W, 'Switch on the Amiga and put in disk 1. The loading picture appears and the opening ceremony starts '
             '(press fire to skip it). When the game needs disk 2 or disk 3 it says "PLEASE INSERT DISK 2": swap the disk in the '
             'drive and the game goes on by itself. Keep disk 1 write-enabled if you want your world records saved.')
    y = head(c, M, y - 6, 'From hard drive', 10.5, RED)
    y = para(c, M, y, W, 'Copy the drawer StronkiesOlympics (from the hard drive zip) to your hard drive or CF card and '
             'double click SOlymp. All events are in that one drawer: no disk swapping.')
    y = head(c, M, y - 6, 'With WHDLoad', 10.5, RED)
    y = para(c, M, y, W, 'Unpack the WHDLoad archive and start the icon StronkiesOlympics. No Kickstart image is needed. '
             'F10 quits back to Workbench.')
    y = head(c, M, y - 6, 'The controls', 10.5, RED)
    rows = [('Joystick left / right', 'run, swim, pedal, lift, sweep: left, right, left, right... as fast as you can'),
            ('Fire', 'jump, throw, shoot, breathe, drink - every event explains it before it starts'),
            ('Joystick up / down', 'aim, steer, change gear'), ('ESC', 'give up the event (or skip a screen)'),
            ('M', 'music on / off'), ('RETURN, cursor keys', 'the same as fire and the joystick')]
    for k, v in rows:
        c.setFillColorRGB(*NAVY); c.setFont('SansB', 7.8); c.drawString(M, y - 2, k)
        y = para(c, M + 33 * mm, y - 2, W - 33 * mm, v, 'Serif', 7.8, 9.5) - 1
    c.showPage()
    # 5 the main menu
    page_frame(c, 5, 'The main menu')
    y = head(c, M, A5H - 22 * mm, 'THE MAIN MENU', 15)
    y = picture(c, shot('01_title'), M + 10 * mm, y - 2, W - 20 * mm) - 5 * mm
    items = [('ALL 18 EVENTS', 'the full Games: every event, one after the other, with medals after each one'),
             ('THE CLASSIC EVENTS (14)', 'the 14 serious ones (well...): the first six and the eight Olympic classics'),
             ('THE SILLY GAMES (4)', 'just the four silly ones: root beer, pies, penguins and toilet paper'),
             ('CHOOSE YOUR EVENTS', 'pick your own programme: tick the events you want, then START'),
             ('PRACTICE ONE EVENT', 'one event on your own, as often as you like - no medals, no records'),
             ('PLAYERS', '1 to 4 players take turns on one joystick'),
             ('LEVEL', 'easy, normal or hard: how good the athletes from the other countries are'),
             ('WORLD RECORDS', 'the best of all time in every event, with the name and the flag'),
             ('HOW TO PLAY', 'the controls of every event, on screen'), ('MUSIC', 'on or off (or press M)'),
             ('QUIT', 'back to Workbench')]
    for k, v in items:
        c.setFillColorRGB(*RED); c.setFont('SansB', 7.2); c.drawString(M, y, k)
        y = para(c, M + 41 * mm, y, W - 41 * mm, v, 'Serif', 7.6, 9.2) - 1.5
    c.showPage()
    # 6 your athlete
    page_frame(c, 6, 'Your athlete')
    y = head(c, M, A5H - 22 * mm, 'YOUR ATHLETE', 15)
    y = para(c, M, y - 2, W, 'Before the Games begin, every player makes an athlete. Type a name (up to 8 letters) and use '
             'left and right to choose your country, man or woman, the colour of the skin and the hair. Your kit gets '
             'the colours of your country, and your flag goes up at the medal ceremony.')
    y = picture(c, shot('02_create'), M + 10 * mm, y - 4, W - 20 * mm) - 6 * mm
    y = head(c, M, y, 'THE 20 COUNTRIES', 10.5, RED)
    fl = flags(); fw = fl.size[0] // 20
    cw = W / 4
    for i, cn in enumerate(COUNTRIES):
        col, row = i % 4, i // 4
        x = M + col * cw; yy = y - row * 9.5 * mm
        c.drawImage(ImageReader(fl.crop((i * fw + 2, 2, i * fw + fw - 2, fl.size[1] - 2))), x, yy - 5.5 * mm, 8.5 * mm, 5.5 * mm)
        c.setFillColorRGB(*INK); c.setFont('SansC', 6.6); c.drawString(x + 10 * mm, yy - 3.7 * mm, ctitle(cn))
    c.showPage()
    # 7 playing the games
    page_frame(c, 7, 'Playing the Games')
    y = head(c, M, A5H - 22 * mm, 'PLAYING THE GAMES', 15)
    y = para(c, M, y - 2, W, 'Before every event a screen tells you what to do. In every event you meet three athletes from '
             'other countries; how good they are depends on the level. After the event comes the results list - fastest '
             'time, longest distance or most points first - and then the medal ceremony.')
    y = picture(c, shot('04_anthem'), M + 14 * mm, y - 4, W - 28 * mm) - 5 * mm
    y = head(c, M, y, 'Medals and anthems', 10.5, RED)
    y = para(c, M, y, W, 'Gold, silver and bronze go to the best three. The flags are raised on the podium and the '
             'national anthem of the gold medal winner plays. At the end of the Games the medal table shows which '
             'country won the most, and the champion is announced.')
    y = head(c, M, y - 6, 'World records', 10.5, RED)
    y = para(c, M, y, W, 'Beat the world record and the stadium goes wild. Your name, your flag and your result are saved '
             'on disk 1 (keep it write-enabled). WORLD RECORDS in the menu shows them all.')
    c.showPage()
    # 8-16 the events: two a page
    evs = events.EVENTS
    groups = [('THE FIRST SIX', evs[0:6]), ('THE CLASSIC OLYMPIC EVENTS', evs[6:14]), ('THE SILLY EVENTS', evs[14:18])]
    n = 8
    order = []
    for gname, lst in groups:
        for i in range(0, len(lst), 2): order.append((gname, lst[i:i + 2], i == 0))
    for gname, pair, first in order:
        page_frame(c, n, 'The events')
        y = A5H - 15 * mm
        if first:
            c.setFillColorRGB(*RED); c.setFont('SansB', 12); c.drawString(M, y - 4 * mm, gname); y -= 9 * mm
        for e in pair:
            y = event_block(c, e, M, y, W) - 2 * mm
        c.showPage(); n += 1
    # 17 the ceremonies
    page_frame(c, 17, 'The ceremonies')
    y = head(c, M, A5H - 22 * mm, 'THE CEREMONIES', 15)
    y = para(c, M, y - 2, W, 'Every Games begins with the opening ceremony. The athletes of all twenty countries march into '
             'the stadium behind their flags. Your athlete carries the torch up the long stairs, lights the flame, and the '
             'doves fly up into the sky - to music written for this game.')
    y = picture(c, shot('03_opening'), M + 8 * mm, y - 4, W - 16 * mm) - 5 * mm
    y = para(c, M, y, W, 'When the last event is over, the stadium goes dark for the closing ceremony. Fireworks light up '
             'the sky, the athletes walk out one last time and the flame slowly goes out. See you at the next Games!')
    picture(c, shot('12_closing'), M + 8 * mm, y - 4, W - 16 * mm)
    c.showPage()
    # 18 did you know
    page_frame(c, 18, 'Did you know?')
    y = head(c, M, A5H - 22 * mm, 'DID YOU KNOW?', 15)
    facts = [
        'The root beer mug holds exactly 80 sips. Drink too fast and the fizz meter hits 100: HIC! One hiccup costs you 1.6 seconds.',
        'In Pie Dodge 22 clowns throw pies at you - 11 at the top of the arena and 11 at the bottom. None of them has ever said sorry.',
        'A good toilet roll throw leaves a trail of up to 70 sheets of paper on the field. The groundsmen of the stadium are not amused.',
        'Your swimmer can hold their breath for 4.8 seconds. After that: very, very slow swimming.',
        'The javelin turns while it flies: the game has it in 8 different angles, from 60 degrees up to 45 degrees down.',
        'The archery target has ten rings, each one exactly 7 pixels wide. The gold is 14 pixels across.',
        'Every event is a separate file that is loaded when the event starts. All 18 together are about 1.1 MB - on a 512K + 512K Amiga.',
        'The national anthems were read note by note out of old sheet music by a small program. Seventeen of them made it into the game.',
        'No penguins were harmed in the making of Penguin Curling. They slide on their bellies and they love it.',
        'The game runs at 25 frames a second, with the screen drawn in the background while you look at the one before it.',
        'The world record holders are all made up - but F. Flash really does run the 100m in 9.58 seconds.']
    for f_ in facts:
        c.setFillColorRGB(*GOLD); c.circle(M + 1.5 * mm, y - 1.1 * mm, 1.3 * mm, fill=1, stroke=0)
        y = para(c, M + 5 * mm, y - 2, W - 5 * mm, f_, 'Serif', 8.3, 10.6) - 4
    c.showPage()
    # 19-20 dev log
    page_frame(c, 19, 'From the dev log')
    y = head(c, M, A5H - 22 * mm, 'FROM THE DEV LOG', 15)
    log1 = [('V0.1 - Six sports and a flame',
             'It started with six events: soccer, basketball, volleyball, bowling, surfing and skateboarding, each one '
             'its own file on the disk, loaded when you need it, so the game fits a 1 MB Amiga 500. Then the opening '
             'ceremony: athletes marching in, a torch, a flame and doves - and the same at night when it is all over.'),
            ('The surfer who could not surf',
             'In the first tests the surfer never reached the top of the wave: the push up the wave was just too weak. '
             'A bit more power and an easier take-off at the lip, and the airs finally worked.'),
            ('V0.2 - Twelve more events',
             'Then came the classics - sprint, hurdles, long jump, javelin, archery, swimming, weightlifting, cycling - '
             'and four silly ones. The races share one race engine, the long jump, javelin and toilet paper throw one '
             'run-up engine. Eighteen events no longer fit on two disks: the game now comes on three.')]
    for t, s in log1:
        y = head(c, M, y - 2, t, 10, RED)
        y = para(c, M, y, W, s, 'Serif', 8.4, 10.8) - 6
    im = Image.new('RGB', (4 * 48 + 3 * 8, 48), (240, 236, 220))
    for i, (f_, k) in enumerate((('preview_cyc_bikes.png', 0), ('preview_rbr_men.png', 7), ('preview_wgt_men.png', 4), ('preview_ljp_men.png', 7))):
        pass
    sheet = gen('preview_rbr_men.png')
    y = picture(c, sheet, M, y - 2, W)
    c.setFillColorRGB(0.35, 0.35, 0.35); c.setFont('SerifI', 7); c.drawString(M, y - 9, 'The root beer sprinter, from the first drawings: running, ready, drinking and the hiccup.')
    c.showPage()
    page_frame(c, 20, 'From the dev log')
    y = A5H - 18 * mm
    log2 = [('The rival who stood still',
             'A funny bug in the first races: as soon as YOU crossed the finish line, your rival stopped running and '
             'waited. Whoever came second... still lost to you. Every single time. Fixed before anyone could get used to it.'),
            ('All or nothing',
             'The first sprinter knew two speeds: standing still and top speed. Waggle a little too slow and you went '
             'nowhere, a little faster and you flew. Now your speed follows how fast you waggle, step by step.'),
            ('Sip, do not chug',
             'The test robot drank its root beer in two ways. Chugging it in one go: 16.64 seconds and two hiccups. '
             'Sipping it: 14.48 seconds. The robot now only sips.'),
            ('Too heavy',
             'The first weightlifter could only lift 150 kg with very fast arms. The bar was made a bit kinder: now '
             'a good player lifts around 200 kg.'),
            ('V0.3 - Anthems',
             'The gold medal winner now hears their national anthem. The melodies were read from old sheet music on '
             'the internet by a small program written for this game, and all of them are old enough to be free to use.')]
    for t, s in log2:
        y = head(c, M, y - 2, t, 10, RED)
        y = para(c, M, y, W, s, 'Serif', 8.4, 10.8) - 6
    y = picture(c, gen('preview_cyc_bikes.png').crop((0, 0, 48 * 7, 48)), M + 10 * mm, y - 2, W - 20 * mm)
    c.setFillColorRGB(0.35, 0.35, 0.35); c.setFont('SerifI', 7); c.drawString(M + 10 * mm, y - 9, 'Six frames of pedalling and one of standing still.')
    c.showPage()
    # 21 hints and tips
    page_frame(c, 21, 'Hints and tips')
    y = head(c, M, A5H - 22 * mm, 'HINTS AND TIPS', 15)
    tips = [('Waggling', 'Hold the joystick base firmly with one hand and rock the stick left and right with the other. '
             'Short, quick movements beat big ones. Six times a second is good, eight is great.'),
            ('Races', 'Watch out for false starts: do not move before GO. Your rival from another country is fast at '
             'the start but you can catch them at the end.'),
            ('Field events', 'The take-off or throw counts from the line: every centimetre before it is lost. Best: '
             'full speed, fire at the line, angle about 45.'),
            ('The level', 'On EASY the others are beatable for everybody, on HARD only a world class waggler wins gold.'),
            ('With friends', 'Up to 4 players take turns. The medal table at the end shows which country is the best.'),
            ('World records', 'Records are only saved when disk 1 is write-enabled (or from hard drive / WHDLoad).'),
            ('Give up?', 'ESC ends the event: you get no result for it, but the Games go on.')]
    for t, s in tips:
        y = head(c, M, y - 2, t, 10, RED)
        y = para(c, M, y, W, s, 'Serif', 8.5, 11) - 5
    c.showPage()
    # 22 hall of fame
    page_frame(c, 22, 'Hall of Fame')
    y = head(c, M, A5H - 22 * mm, 'HALL OF FAME', 15)
    y = para(c, M, y - 2, W, 'Write down your best results - and who beat them.', 'SerifI', 8.5)
    y -= 3 * mm
    c.setStrokeColorRGB(*NAVY); c.setLineWidth(0.6)
    cols = [M, M + 38 * mm, M + 62 * mm, M + 98 * mm, A5W - M]
    c.setFillColorRGB(*NAVY); c.rect(M, y - 6 * mm, W, 6 * mm, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1); c.setFont('SansB', 7)
    for x, t in zip(cols, ('EVENT', 'RESULT', 'NAME', 'DATE')): c.drawString(x + 1.5 * mm, y - 4.2 * mm, t)
    y -= 6 * mm
    for e in evs:
        c.setFillColorRGB(*INK); c.setFont('SansC', 7); c.drawString(M + 1.5 * mm, y - 4.6 * mm, e[0].title())
        c.line(M, y - 7 * mm, A5W - M, y - 7 * mm)
        for x in cols: c.line(x, y, x, y - 7 * mm)
        y -= 7 * mm
    c.showPage()
    # 23 credits
    page_frame(c, 23, 'Credits')
    y = head(c, M, A5H - 22 * mm, 'CREDITS', 15)
    rows = [('Game design, code, graphics, sound', 'Mark Stronks'), ('Published by', 'Stronkie Soft'),
            ('Music', 'written for this game by Stronkie Soft'),
            ('The national anthems', 'traditional and old melodies, free to use - arranged for this game'),
            ('Made for', 'the Amiga 500, Kickstart 1.3, 512K + 512K trapdoor'),
            ('Testers', 'everybody who played it and left a comment on itch.io - thank you!')]
    for k, v in rows:
        c.setFillColorRGB(*NAVY); c.setFont('SansB', 8.5); c.drawString(M, y, k)
        y = para(c, M, y - 11, W, v, 'Serif', 9) - 7
    y -= 4 * mm
    picture(c, pix(robot(), 1), A5W / 2 - 30 * mm, y, 60 * mm, frame=False)
    y -= 26 * mm
    c.setFillColorRGB(*INK); c.setFont('SerifI', 8.5)
    c.drawCentredString(A5W / 2, y, 'More Stronkie Soft games: https://stronkie.itch.io/')
    c.setFont('Serif', 7.5); c.setFillColorRGB(0.35, 0.35, 0.35)
    for i, l in enumerate(['Stronkie\'s Olympics V%s - (c) 2026 Stronkie Soft. Created By Mark Stronks.' % VER,
                           'This game is not connected to any Olympic committee or sports organisation.',
                           'All athletes, record holders and clowns are made up.']):
        c.drawCentredString(A5W / 2, y - (6 + i * 4) * mm, l)
    c.showPage()
    # 24 back cover
    c.setFillColorRGB(*NAVY); c.rect(0, 0, A5W, A5H, fill=1, stroke=0)
    picture(c, pix(lg, 2), 14 * mm, A5H - 12 * mm, A5W - 28 * mm, frame=False)
    xs = ['13_sprint', '21_rootbeer', '18_swimming', '23_curling']
    for i, s in enumerate(xs):
        picture(c, shot(s), M + (i % 2) * (W / 2 + 1 * mm), A5H - 70 * mm - (i // 2) * 43 * mm, W / 2 - 1 * mm)
    c.setFillColorRGB(*GOLD); c.setFont('SansB', 11); c.drawCentredString(A5W / 2, 40 * mm, 'GO FOR GOLD!')
    picture(c, pix(robot(), 1), A5W / 2 - 22 * mm, 34 * mm, 44 * mm, frame=False)
    c.setFillColorRGB(1, 1, 1); c.setFont('Sans', 7); c.drawCentredString(A5W / 2, 9 * mm, 'Created By Mark Stronks, Stronkie Soft  -  stronkie.itch.io')
    c.showPage()
    c.save()
    return path

# ------------------------------------------------------------------ disk labels (A4)
LW, LH, STRIP = 70 * mm, 70 * mm, 16 * mm

def label(c, x, y, disk, bw):
    """one label, x, y its bottom left; disk: 1, 2, 3 or 'DEMO'"""
    ink = (0, 0, 0)
    bg = (1, 1, 1) if bw else (0.99, 0.97, 0.90)
    top = NAVY if not bw else (0, 0, 0)
    c.setFillColorRGB(*bg); c.setStrokeColorRGB(0.6, 0.6, 0.6); c.setLineWidth(0.3); c.setDash()
    c.rect(x, y, LW, LH, fill=1, stroke=1)
    # the strip that folds over the top of the disk
    c.setFillColorRGB(*top); c.rect(x, y + LH - STRIP, LW, STRIP, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1); c.setFont('SansB', 9)
    c.drawCentredString(x + LW / 2, y + LH - 7 * mm, "STRONKIE'S OLYMPICS")
    c.setFont('Sans', 6.5)
    c.drawCentredString(x + LW / 2, y + LH - 12 * mm, ('DEMO DISK' if disk == 'DEMO' else 'DISK %d OF 3' % disk) + '   -   STRONKIE SOFT')
    c.setStrokeColorRGB(0.4, 0.4, 0.4); c.setDash(1, 2); c.line(x, y + LH - STRIP, x + LW, y + LH - STRIP); c.setDash()
    c.setFillColorRGB(0.45, 0.45, 0.45); c.setFont('Sans', 4.3); c.drawRightString(x + LW - 1.5 * mm, y + LH - STRIP - 2.5 * mm, 'fold')
    # the front
    yy = y + LH - STRIP - 3 * mm
    lg = logo()
    if bw:
        from PIL import ImageOps
        lg = ImageOps.autocontrast(lg.convert('L'), cutoff=2).convert('RGB')
    h = picture(c, lg, x + 4 * mm, yy, LW - 8 * mm, frame=False)
    yy = h - 4.5 * mm
    c.setFillColorRGB(*(RED if not bw else ink)); c.setFont('SansB', 11)
    c.drawString(x + 4 * mm, yy, 'DEMO' if disk == 'DEMO' else 'DISK %d' % disk)
    c.setFillColorRGB(*ink); c.setFont('Sans', 6.2)
    c.drawRightString(x + LW - 4 * mm, yy, 'AMIGA 500  -  V%s' % ('DEMO' if disk == 'DEMO' else VER))
    yy -= 5 * mm
    if disk == 'DEMO': lines = ['Opening ceremony + Soccer (free demo)', 'Bootable in DF0:', 'The full game: 18 events on 3 disks']
    elif disk == 1: lines = ['BOOT DISK: game, ceremonies, records', 'Soccer, Basketball, Volleyball,', 'Bowling, Surfing',
                             'Write-enable to save world records']
    elif disk == 2: lines = ['Skateboarding, 100m Sprint, Hurdles,', 'Long Jump, Javelin, Archery, Swimming,',
                             'Weightlifting, Cycling, Root Beer Sprint,', 'Pie Dodge, Penguin Curling']
    else: lines = ['Toilet Paper Throw', '', 'The game asks for this disk', 'when it needs it']
    c.setFont('SansC', 6)
    for l in lines: c.drawString(x + 4 * mm, yy, l); yy -= 2.7 * mm
    c.setStrokeColorRGB(*ink); c.setLineWidth(0.4); c.line(x + 4 * mm, y + 9.5 * mm, x + LW - 4 * mm, y + 9.5 * mm)
    c.setFont('Sans', 5.2)
    c.drawString(x + 4 * mm, y + 6.5 * mm, 'Kickstart 1.3+  -  1 MB (512K + 512K)  -  PAL  -  Joystick port 2')
    c.drawString(x + 4 * mm, y + 3.5 * mm, 'Created By Mark Stronks, Stronkie Soft  (c) 2026')

def labels():
    path = os.path.join(OUT, 'StronkiesOlympics_DiskLabels.pdf')
    W, H = 210 * mm, 297 * mm
    c = canvas.Canvas(path, pagesize=(W, H))
    c.setTitle("Stronkie's Olympics - Disk labels"); c.setAuthor('Mark Stronks, Stronkie Soft')
    for bw in (False, True):
        c.setFont('SansB', 10); c.setFillColorRGB(0, 0, 0)
        c.drawString(20 * mm, H - 14 * mm, "STRONKIE'S OLYMPICS - DISK LABELS (%s)" % ('BLACK AND WHITE' if bw else 'COLOUR'))
        c.setFont('Sans', 7.5)
        c.drawString(20 * mm, H - 19 * mm, 'Print at 100% (actual size, not "fit to page"). Each label is 70 x 70 mm; the top strip folds over the top edge of the disk.')
        gx, gy = 30 * mm, 14 * mm
        x0 = (W - 2 * LW - gx) / 2
        for i, d in enumerate([1, 2, 3, 'DEMO', 1, 2]):
            col, row = i % 2, i // 2
            label(c, x0 + col * (LW + gx), H - 30 * mm - (row + 1) * LH - row * gy, d, bw)
        c.showPage()
    c.save()
    return path

# ------------------------------------------------------------------ the box
BW_, BH_, BD_ = 140, 190, 36            # mm: front width, height, depth
DPI = 8                                 # pixels per mm for the box pictures

def font(sz, bold=True, cond=False):
    n = 'DejaVuSansCondensed-Bold.ttf' if (cond and bold) else 'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'
    return ImageFont.truetype(F + n, int(sz))

def ctext(d, cx, y, t, f, fill, stroke=0, sfill=(0, 0, 0)):
    w = d.textlength(t, font=f); d.text((cx - w / 2, y), t, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)

def starburst(d, cx, cy, r, n, fill):
    pts = []
    for i in range(n * 2):
        a = math.pi * i / n; rr = r if i % 2 == 0 else r * 0.78
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=fill, outline=(0, 0, 0))

def gradient(w, h, top, bot):
    a = np.linspace(0, 1, h)[:, None, None]
    arr = (np.array(top)[None, None, :] * (1 - a) + np.array(bot)[None, None, :] * a) * np.ones((1, w, 1))
    return Image.fromarray(arr.astype('uint8'), 'RGB')

def front_art():
    W, H = BW_ * DPI, BH_ * DPI
    im = gradient(W, H, (14, 22, 70), (30, 50, 120)); d = ImageDraw.Draw(im)
    random.seed(3)
    for i in range(300):                                  # (a starry night over the stadium)
        d.point((random.randrange(W), random.randrange(int(H * 0.3))), fill=(255, 255, 220))
    lg = logo(True); s = (W - 10 * DPI) / lg.size[0]
    lg2 = lg.resize((int(lg.size[0] * s), int(lg.size[1] * s)), Image.NEAREST)
    im.paste(lg2, (5 * DPI, 8 * DPI), lg2)
    ctext(d, W / 2, 38 * DPI, 'THE SPORTS GAME FOR THE AMIGA 500', font(5 * DPI), (255, 255, 255))
    ow = 118 * DPI; op = shot('03_opening').resize((ow, ow * 512 // 640), Image.NEAREST)
    ox, oy = (W - ow) // 2, 47 * DPI
    im.paste(op, (ox, oy)); d.rectangle([ox, oy, ox + ow, oy + op.size[1]], outline=(250, 200, 30), width=6)
    y = oy + op.size[1] + 4 * DPI
    shots = ['13_sprint', '18_swimming', '21_rootbeer', '23_curling']
    tw = (ow - 3 * 3 * DPI) // 4; th = tw * 512 // 640
    for i, s_ in enumerate(shots):
        x = ox + i * (tw + 3 * DPI)
        im.paste(shot(s_).resize((tw, th), Image.LANCZOS), (x, y)); d.rectangle([x, y, x + tw, y + th], outline=(255, 255, 255), width=3)
    cx, cy = W - 21 * DPI, oy + 26 * DPI
    starburst(d, cx, cy, 20 * DPI, 14, (250, 200, 30))
    ctext(d, cx, cy - 13 * DPI, '18', font(12 * DPI), (200, 20, 20))
    ctext(d, cx, cy + 1 * DPI, 'EVENTS!', font(4.4 * DPI), (20, 20, 60))
    ctext(d, cx, cy + 6.5 * DPI, 'incl. 4 silly ones', font(2.7 * DPI, False), (20, 20, 60))
    # the bottom band: Amiga 500, Stronkie Soft
    d.rectangle([0, H - 18 * DPI, W, H], fill=(10, 14, 40)); d.rectangle([0, H - 18.6 * DPI, W, H - 18 * DPI], fill=(250, 200, 30))
    d.rounded_rectangle([5 * DPI, H - 15 * DPI, 46 * DPI, H - 3.5 * DPI], 2 * DPI, fill=(200, 20, 20))
    ctext(d, 25.5 * DPI, H - 14.3 * DPI, 'AMIGA', font(5 * DPI), (255, 255, 255)); ctext(d, 25.5 * DPI, H - 8.6 * DPI, '500 · 1 MB', font(3.4 * DPI), (255, 255, 255))
    fl = flags(); fw = 40 * DPI; fl2 = fl.resize((fw, int(fl.size[1] * fw / fl.size[0])), Image.LANCZOS)
    im.paste(fl2, (int(W / 2 - fw / 2 + 1 * DPI), int(H - 11 * DPI)))
    ctext(d, W / 2 + 1 * DPI, H - 16 * DPI, '20 COUNTRIES', font(3 * DPI), (250, 200, 30))
    rb = robot(); s = 12 * DPI / rb.size[1]; rb2 = rb.resize((int(rb.size[0] * s), int(12 * DPI)), Image.NEAREST)
    im.paste(rb2, (W - rb2.size[0] - 4 * DPI, H - 15 * DPI))
    return im

def back_art():
    W, H = BW_ * DPI, BH_ * DPI
    im = gradient(W, H, (14, 22, 70), (8, 12, 40)); d = ImageDraw.Draw(im)
    lg = logo(True); s = (W * 0.62) / lg.size[0]; lg2 = lg.resize((int(lg.size[0] * s), int(lg.size[1] * s)), Image.NEAREST)
    im.paste(lg2, ((W - lg2.size[0]) // 2, 5 * DPI), lg2)
    y = 5 * DPI + lg2.size[1] + 3 * DPI
    blurb = ("The torch is lit and twenty countries march into the stadium. One of the flags is yours! Make your own athlete and "
             "go for gold in eighteen events: from the 100 metres, the hurdles and the javelin to the beach, the half pipe - "
             "and four events no real Olympics ever dared: root beer chugging, pie dodging, penguin curling and the toilet paper throw.")
    f = font(3.3 * DPI, False)
    words = blurb.split(); line = ''; lines = []
    for w_ in words:
        t = (line + ' ' + w_).strip()
        if d.textlength(t, font=f) < W - 14 * DPI: line = t
        else: lines.append(line); line = w_
    lines.append(line)
    for l in lines: ctext(d, W / 2, y, l, f, (255, 255, 255)); y += 4.4 * DPI
    y += 3 * DPI
    shots = ['05_soccer_shot', '16_javelin', '17_archery', '19_weightlifting', '22_piedodge', '24_toiletpaper']
    tw = (W - 14 * DPI - 2 * 3 * DPI) // 3; th = tw * 512 // 640
    for i, s_ in enumerate(shots):
        x = 7 * DPI + (i % 3) * (tw + 3 * DPI); yy = y + (i // 3) * (th + 3 * DPI)
        im.paste(shot(s_).resize((tw, th), Image.LANCZOS), (x, yy)); d.rectangle([x, yy, x + tw, yy + th], outline=(250, 200, 30), width=3)
    y += 2 * (th + 3 * DPI) + 3 * DPI
    feats = ['18 events, each loaded from disk when it starts', 'Make your own athlete: 20 countries, your kit, your flag',
             '1 to 4 players, 3 levels, rivals from other countries', 'Medal ceremonies with the national anthems',
             'World records saved on disk', 'Opening and closing ceremony, voices and a cheering crowd']
    fb = font(3.2 * DPI, False)
    for t in feats:
        d.ellipse([9 * DPI, y + 1 * DPI, 11 * DPI, y + 3 * DPI], fill=(250, 200, 30)); d.text((13 * DPI, y), t, font=fb, fill=(255, 255, 255)); y += 4.3 * DPI
    d.rectangle([0, H - 13 * DPI, W, H], fill=(250, 200, 30))
    d.text((6 * DPI, H - 11 * DPI), 'Amiga 500 · Kickstart 1.3 · 1 MB (512K + 512K) · 3 disks · hard drive & WHDLoad', font=font(2.8 * DPI), fill=(10, 14, 40))
    d.text((6 * DPI, H - 6.5 * DPI), "Created By Mark Stronks, Stronkie Soft © 2026 · stronkie.itch.io", font=font(2.8 * DPI, False), fill=(10, 14, 40))
    return im

def spine_art(rot=True):
    W, H = BD_ * DPI, BH_ * DPI
    im = gradient(W, H, (14, 22, 70), (30, 50, 120)); d = ImageDraw.Draw(im)
    t = Image.new('RGB', (H, W), (0, 0, 0)); td = ImageDraw.Draw(t)
    t.paste(gradient(H, W, (14, 22, 70), (30, 50, 120)))
    td.text((8 * DPI, 11 * DPI), "STRONKIE'S OLYMPICS", font=font(9.5 * DPI), fill=(250, 200, 30), stroke_width=2, stroke_fill=(0, 0, 0))
    td.text((H - 40 * DPI, 14 * DPI), 'AMIGA 500', font=font(5.5 * DPI), fill=(255, 255, 255))
    im = t.rotate(-90, expand=True)
    return im

def side_art():
    W, H = BD_ * DPI, BH_ * DPI
    im = Image.new('RGB', (W, H), (250, 200, 30)); d = ImageDraw.Draw(im)
    t = Image.new('RGB', (H, W), (250, 200, 30)); td = ImageDraw.Draw(t)
    td.text((6 * DPI, 3 * DPI), 'SYSTEM REQUIREMENTS', font=font(4.4 * DPI), fill=(10, 14, 40))
    rows = ['Amiga 500 (or any Amiga with a 68000)', 'Kickstart / Workbench 1.3 or higher', '1 MB: 512K chip + 512K trapdoor expansion',
            'Joystick in port 2 (or keyboard)', 'PAL', '3 disks (3.5" DD) - also for hard drive and WHDLoad']
    for i, r in enumerate(rows):
        td.text((6 * DPI + (i // 3) * 92 * DPI, 10 * DPI + (i % 3) * 5.6 * DPI), '· ' + r, font=font(3.4 * DPI, False), fill=(10, 14, 40))
    return t.rotate(90, expand=True)

def topflap_art():
    W, H = BW_ * DPI, BD_ * DPI
    im = gradient(W, H, (14, 22, 70), (30, 50, 120)); d = ImageDraw.Draw(im)
    ctext(d, W / 2, 8 * DPI, "STRONKIE'S OLYMPICS", font(9 * DPI), (250, 200, 30), 2)
    ctext(d, W / 2, 22 * DPI, 'Stronkie Soft  ·  Amiga 500', font(4 * DPI, False), (255, 255, 255))
    return im

def box():
    path = os.path.join(OUT, 'StronkiesOlympics_Box.pdf')
    PW, PH = 420 * mm, 297 * mm
    c = canvas.Canvas(path, pagesize=(PW, PH))
    c.setTitle("Stronkie's Olympics - Box"); c.setAuthor('Mark Stronks, Stronkie Soft')
    fr, bk, sp, sd, tp = front_art(), back_art(), spine_art(), side_art(), topflap_art()
    for im, k in ((fr, 'front'), (bk, 'back'), (sp, 'spine'), (sd, 'side'), (tp, 'top')): im.save(os.path.join(TMP, 'box_%s.png' % k))
    tab = 12
    total = tab + BD_ + BW_ + BD_ + BW_
    x0 = (420 - total) / 2; y0 = (297 - (BD_ + BH_ + BD_)) / 2       # mm
    X = lambda v: (x0 + v) * mm; Y = lambda v: (y0 + v) * mm
    # panels: glue tab | side | front | spine | back
    panels = [(tab, sd), (tab + BD_, fr), (tab + BD_ + BW_, sp), (tab + 2 * BD_ + BW_, bk)]
    for x, im in panels:
        w = im.size[0] / DPI
        c.drawImage(ImageReader(im), X(x), Y(BD_), w * mm, BH_ * mm)
    # the flaps: top and bottom of the front and the back (the box closes at both ends)
    fx0, bx0 = tab + BD_, tab + 2 * BD_ + BW_
    c.drawImage(ImageReader(tp), X(bx0), Y(BD_ + BH_), BW_ * mm, BD_ * mm)              # the top: on the back, folds forward
    c.drawImage(ImageReader(tp.rotate(180)), X(fx0), Y(0), BW_ * mm, BD_ * mm)          # the bottom: on the front
    # the glue tab
    c.setFillColorRGB(0.9, 0.9, 0.9); p = c.beginPath()
    p.moveTo(X(tab), Y(BD_)); p.lineTo(X(0), Y(BD_ + 8)); p.lineTo(X(0), Y(BD_ + BH_ - 8)); p.lineTo(X(tab), Y(BD_ + BH_)); p.close()
    c.drawPath(p, fill=1, stroke=0)
    c.setFillColorRGB(0.4, 0.4, 0.4); c.setFont('Sans', 8)
    c.saveState(); c.translate(X(6), Y(BD_ + BH_ / 2)); c.rotate(90); c.drawCentredString(0, 0, 'GLUE'); c.restoreState()
    # cut lines (solid) and fold lines (dashed)
    c.setStrokeColorRGB(0, 0, 0); c.setLineWidth(0.6); c.setDash()
    out = [((tab, BD_), (tab, 0)), ((tab, 0), (tab + BD_ + BW_, 0))]
    c.setDash();
    def L(a, b): c.line(X(a[0]), Y(a[1]), X(b[0]), Y(b[1]))
    # outline of the whole net
    fx, bx = tab + BD_, tab + 2 * BD_ + BW_
    pts = [(tab, BD_), (0, BD_ + 8), (0, BD_ + BH_ - 8), (tab, BD_ + BH_), (bx, BD_ + BH_), (bx, 2 * BD_ + BH_),
           (bx + BW_, 2 * BD_ + BH_), (bx + BW_, BD_), (fx + BW_, BD_), (fx + BW_, 0), (fx, 0), (fx, BD_), (tab, BD_)]
    for a, b in zip(pts, pts[1:]): L(a, b)
    c.setDash(3, 3); c.setStrokeColorRGB(0.2, 0.2, 0.2)
    for x in (tab, fx, fx + BW_, bx): L((x, BD_), (x, BD_ + BH_))
    L((fx, BD_), (fx + BW_, BD_)); L((bx, BD_ + BH_), (bx + BW_, BD_ + BH_))
    c.setDash()
    c.setFillColorRGB(0, 0, 0); c.setFont('SansB', 9)
    c.drawString(10 * mm, PH - 9 * mm, "STRONKIE'S OLYMPICS - THE BOX  (A3, print at 100%)")
    c.setFont('Sans', 7.5)
    c.drawString(10 * mm, PH - 13 * mm, 'Cut along the solid lines, fold along the dashed lines and glue the tab inside the free edge of the back. The top flap folds forward, the bottom flap backward. '
                 'Box: %d x %d x %d mm. Print on thick paper or card.' % (BW_, BH_, BD_))
    c.showPage()
    # page 2: the box in 3D
    c.setFillColorRGB(0.93, 0.93, 0.95); c.rect(0, 0, PW, PH, fill=1, stroke=0)
    r = render3d(fr, sp, tp)
    p = os.path.join(TMP, 'box3d.png'); r.save(p)
    w = 300 * mm; h = w * r.size[1] / r.size[0]
    if h > PH - 30 * mm: h = PH - 30 * mm; w = h * r.size[0] / r.size[1]
    c.drawImage(ImageReader(r), (PW - w) / 2, 12 * mm, w, h, mask='auto')
    c.setFillColorRGB(*NAVY); c.setFont('SansB', 14); c.drawString(14 * mm, PH - 14 * mm, "STRONKIE'S OLYMPICS - THE BOX")
    c.setFont('Sans', 9); c.drawString(14 * mm, PH - 20 * mm, 'Amiga 500 · 3 disks · manual · Created By Mark Stronks, Stronkie Soft')
    c.showPage()
    c.save()
    return path

def persp_coeffs(src, dst):
    """coefficients for Image.transform(PERSPECTIVE): maps dst -> src"""
    A = []; B = []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()

def warp(img_, quad, size):
    w, h = img_.size
    co = persp_coeffs([(0, 0), (w, 0), (w, h), (0, h)], quad)
    rgba = img_.convert('RGBA')
    return rgba.transform(size, Image.PERSPECTIVE, co, Image.BICUBIC)

def render3d(front, spine, top):
    S = 2400, 1700
    out = Image.new('RGBA', S, (0, 0, 0, 0))
    # the box: the front facing a little to the right, the spine on the left, the top visible
    fq = [(700, 330), (1500, 400), (1500, 1520), (700, 1560)]
    sq = [(520, 250), (700, 330), (700, 1560), (520, 1440)]
    tq = [(520, 250), (1330, 190), (1500, 400), (700, 330)]
    shadow = Image.new('RGBA', S, (0, 0, 0, 0)); sd = ImageDraw.Draw(shadow)
    sd.polygon([(520, 1440), (700, 1560), (1500, 1520), (1750, 1460), (900, 1400)], fill=(0, 0, 0, 120))
    out = Image.alpha_composite(out, shadow.filter(ImageFilter.GaussianBlur(25)))
    sp_dark = Image.eval(spine, lambda v: int(v * 0.75))
    top_l = Image.eval(top, lambda v: min(255, int(v * 1.15)))
    for im, q in ((sp_dark, sq), (top_l, tq), (front, fq)):
        out = Image.alpha_composite(out, warp(im, q, S))
    d = ImageDraw.Draw(out)
    for q in (fq, sq, tq): d.line(q + [q[0]], fill=(0, 0, 0, 255), width=3)
    # a disk in front of the box, with its label
    disk = Image.new('RGBA', (520, 540), (0, 0, 0, 0)); dd = ImageDraw.Draw(disk)
    dd.rounded_rectangle([0, 0, 519, 539], 18, fill=(40, 40, 46, 255))
    dd.rectangle([120, 0, 400, 150], fill=(170, 170, 180, 255)); dd.rectangle([300, 20, 360, 130], fill=(40, 40, 46, 255))
    lab = Image.new('RGB', (440, 330), (250, 246, 230)); ld = ImageDraw.Draw(lab)
    ld.rectangle([0, 0, 440, 70], fill=(18, 28, 76)); ctext(ld, 220, 18, "STRONKIE'S OLYMPICS", font(30), (250, 200, 30))
    lg = logo(True).resize((400, int(400 * 104 / 568)), Image.LANCZOS); lab.paste(lg, (20, 85), lg)
    ld.text((22, 190), 'DISK 1', font=font(34), fill=(200, 20, 20)); ld.text((22, 240), 'BOOT DISK · AMIGA 500 · V%s' % VER, font=font(18, False), fill=(0, 0, 0))
    ld.text((22, 275), 'Created By Mark Stronks, Stronkie Soft', font=font(16, False), fill=(0, 0, 0))
    disk.paste(lab, (40, 180))
    dq = [(1560, 1000), (1990, 1080), (1960, 1590), (1520, 1520)]
    out = Image.alpha_composite(out, warp(disk, dq, S))
    return out.crop((420, 120, 2100, 1660))

if __name__ == '__main__':
    for f in (manual, labels, box):
        print(f())
