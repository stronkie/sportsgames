"""gfxlib.py - shared helpers for the graphics, sounds and music of Stronkie's Olympics.
Created By Mark Stronks, Stronkie Soft.

Screens are 320x256, 32 colours, 5 interleaved bitplanes (row = plane0..plane4, 40 bytes each).
Bobs: image interleaved (W words per plane row), mask one plane (W words per row).
Colours 25..31 of every palette are the player's colours (filled in by the game):
  25 hair, 26 skin, 27 skin shade, 28 shirt, 29 shirt shade, 30 shorts, 31 shoes / dark
"""
import math, os, random, re, struct, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
FONTDIR = '/usr/share/fonts/truetype/dejavu/'
HAIR, SKIN, SKIND, SHIRT, SHIRTD, SHORTS, SHOES = range(25, 32)
TRANSP = 255          # transparent pixel in bob images

def rgb12(c): return (((c >> 8) & 15) * 17, ((c >> 4) & 15) * 17, (c & 15) * 17)
def to12(rgb): return (min(15, (rgb[0] + 8) // 17) << 8) | (min(15, (rgb[1] + 8) // 17) << 4) | min(15, (rgb[2] + 8) // 17)

# default player colours for previews (Netherlands, light skin, brown hair)
DEF_PLAYER = [0x630, 0xfc9, 0xc96, 0xf70, 0xb40, 0xfff, 0x222]

def full_pal(pal):
    p = list(pal) + [0] * (32 - len(pal))
    p[25:32] = DEF_PLAYER
    return p

def rgbpal(pal):
    out = []
    for c in full_pal(pal): out += list(rgb12(c))
    return out + [0] * (768 - len(out))

# ------------------------------------------------------------------ packing
def rle(data):
    """literal: n (0..127) then n+1 bytes; run: $80|(n-3) (n = 3..130) then the byte"""
    out = bytearray(); i = 0; lit = bytearray(); n = len(data)
    def flush():
        nonlocal lit
        while lit:
            c = lit[:128]; out.append(len(c) - 1); out.extend(c); lit = lit[128:]
    while i < n:
        j = i
        while j < n and j - i < 130 and data[j] == data[i]: j += 1
        if j - i >= 3:
            flush(); out.append(0x80 | (j - i - 3)); out.append(data[i]); i = j
        else:
            lit.append(data[i]); i += 1
    flush()
    return bytes(out)

def screen_planes(im):
    """P image 320x256 -> interleaved planes (51200 bytes)"""
    a = np.array(im, dtype=np.uint8)
    assert a.shape == (256, 320), a.shape
    out = np.zeros((256, 5, 40), dtype=np.uint8)
    for p in range(5):
        bits = (a >> p) & 1
        out[:, p, :] = np.packbits(bits, axis=1)
    return out.tobytes()

def topbar_to_copper(im):
    """the top bar (rows 0-22) in colour 0, so the copper gradient shows there"""
    a = np.array(im); bar = a[5, 2]
    a[0:23][a[0:23] == bar] = 0
    im.paste(Image.fromarray(a, 'P'))

def save_screen(im, path):
    open(path, 'wb').write(rle(screen_planes(im)))

def bob_data(im):
    """P image with TRANSP for see-through -> (W words, H, image bytes, mask bytes)"""
    a = np.array(im, dtype=np.int32)
    H, w = a.shape
    W = (w + 15) // 16
    pad = np.full((H, W * 16), TRANSP, dtype=np.int32); pad[:, :w] = a
    m = (pad != TRANSP).astype(np.uint8)
    v = np.where(pad == TRANSP, 0, pad).astype(np.uint8)
    img = np.zeros((H, 5, W * 2), dtype=np.uint8)
    for p in range(5):
        img[:, p, :] = np.packbits((v >> p) & 1, axis=1)
    mask = np.packbits(m, axis=1)
    return W, H, img.tobytes(), mask.tobytes()

class Out:
    """collects bobs, samples and raw data for one include file (+ binary blob for the chip hunk)"""
    def __init__(self, outdir, prefix):
        self.dir = outdir; self.prefix = prefix
        self.chip = bytearray(); self.lines = []; self.data_lines = []
        self.chip_labels = []
        os.makedirs(outdir, exist_ok=True)
    def _chip(self, b, label):
        if len(self.chip) & 1: self.chip.append(0)
        off = len(self.chip); self.chip += b
        if len(self.chip) & 1: self.chip.append(0)
        self.chip_labels.append((label, off))
        return off
    def bob(self, name, im):
        W, H, img, mask = bob_data(im)
        oi = self._chip(img, name + '_i'); om = self._chip(mask, name + '_m')
        self.data_lines.append('%s\tdc.w\t%d,%d\n\tdc.l\t%s_chip+%d,%s_chip+%d' % (name, W, H, self.prefix, oi, self.prefix, om))
        return W, H
    def bobs(self, name, ims):
        for i, im in enumerate(ims): self.bob('%s%d' % (name, i), im)
        self.data_lines.append('%s_tab\tdc.l\t%s' % (name, ','.join('%s%d' % (name, i) for i in range(len(ims)))))
    def sample(self, name, x, rate):
        """float array -1..1 -> signed 8 bit; struct: ptr.l, words.w, period.w"""
        s = np.clip(np.round(np.asarray(x) * 127), -128, 127).astype(np.int8).tobytes()
        if len(s) & 1: s += b'\0'
        s = b'\0\0' + s          # (starts on silence)
        o = self._chip(s, name + '_s')
        per = int(round(3546895 / rate))
        self.data_lines.append('%s\tdc.l\t%s_chip+%d\n\tdc.w\t%d,%d' % (name, self.prefix, o, len(s) // 2, per))
    def equ(self, name, v): self.lines.append('%s\tequ\t%d' % (name, v))
    def raw(self, s): self.data_lines.append(s)
    def write(self):
        open(os.path.join(self.dir, self.prefix + '_chip.bin'), 'wb').write(bytes(self.chip))
        L = ['; generated by tools (Stronkie\'s Olympics) - do not edit'] + self.lines
        open(os.path.join(self.dir, self.prefix + '_equ.i'), 'w').write('\n'.join(L) + '\n')
        if not any(l.startswith('grad_ev') for l in self.data_lines):     # (the copper top bar of every event screen)
            c0 = 0x112
            for l in self.data_lines:
                if l.startswith('pal_') and '\tdc.w\t' in l: c0 = int(l.split('\tdc.w\t')[1].split(',')[0][1:], 16); break
            self.data_lines.append(grad_lines('grad_ev', topbar_grad(c0)))
        D = ['; generated - data'] + self.data_lines
        open(os.path.join(self.dir, self.prefix + '_data.i'), 'w').write('\n'.join(D) + '\n')
        return len(self.chip)

def palette_line(label, pal):
    return '%s\tdc.w\t%s' % (label, ','.join('$%03x' % c for c in (list(pal) + [0] * 32)[:32]))

def grad_lines(label, items):
    """items: [(y, colour12)] -> dc.w y,col ... -1"""
    v = []
    for y, c in items: v += ['%d' % y, '$%03x' % c]
    return '%s\tdc.w\t%s,-1' % (label, ','.join(v))

# ------------------------------------------------------------------ fonts
def ttf(size, bold=True, serif=False, cond=False):
    name = 'DejaVu' + ('Serif' if serif else 'Sans') + ('Condensed' if cond else '') + ('-Bold' if bold else '') + '.ttf'
    return ImageFont.truetype(os.path.join(FONTDIR, name), size)

def load_font():
    txt = open(os.path.join(ROOT, 'assets', 'font_gz.txt')).read()
    vals = [int(v, 16) for v in re.findall(r'\$([0-9a-f]{2})', txt)]
    g = [vals[i * 8:i * 8 + 8] for i in range(96)]
    fix = {'$': [0x18, 0x3e, 0x60, 0x3c, 0x06, 0x7c, 0x18, 0x00], '?': [0x3c, 0x66, 0x06, 0x0c, 0x18, 0x00, 0x18, 0x00],
           "'": [0x18, 0x18, 0x30, 0x00, 0x00, 0x00, 0x00, 0x00], '_': [0, 0, 0, 0, 0, 0, 0, 0x7e],
           '%': [0x62, 0x66, 0x0c, 0x18, 0x30, 0x66, 0x46, 0x00],
           '{': [0x00, 0x10, 0x30, 0x7f, 0x30, 0x10, 0x00, 0x00], '}': [0x00, 0x08, 0x0c, 0xfe, 0x0c, 0x08, 0x00, 0x00],
           '^': [0x18, 0x3c, 0x7e, 0xff, 0x18, 0x18, 0x18, 0x00], '`': [0x18, 0x18, 0x18, 0xff, 0x7e, 0x3c, 0x18, 0x00],
           '|': [0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18], '~': [0x00, 0x3c, 0x7e, 0x7e, 0x7e, 0x7e, 0x3c, 0x00]}
    for ch, gl in fix.items(): g[ord(ch) - 32] = gl
    return g
FONT = load_font()

def font_bin():
    return bytes(v for gl in FONT for v in gl)

def text8(im, x, y, s, col):
    px = im.load()
    for i, ch in enumerate(s):
        o = ord(ch) - 32
        if not 0 <= o < 96: continue
        for r in range(8):
            b = FONT[o][r]
            for c in range(8):
                if b & (0x80 >> c):
                    xx, yy = x + i * 8 + c, y + r
                    if 0 <= xx < im.width and 0 <= yy < im.height: px[xx, yy] = col

def quantize_to(im_rgb, pal):
    """RGB image -> P image using exactly the given palette (list of 12 bit colours)"""
    p = Image.new('P', (1, 1)); flat = []
    for c in full_pal(pal): flat += list(rgb12(c))
    p.putpalette(flat + [0] * (768 - len(flat)))
    return im_rgb.quantize(palette=p, dither=Image.NONE)

def quantize_dither(im_rgb, pal):
    p = Image.new('P', (1, 1)); flat = []
    for c in full_pal(pal): flat += list(rgb12(c))
    p.putpalette(flat + [0] * (768 - len(flat)))
    return im_rgb.quantize(palette=p, dither=Image.FLOYDSTEINBERG)

def preview(im, pal, path, scale=2):
    q = im.copy(); q.putpalette(rgbpal(pal))
    q.convert('RGB').resize((im.width * scale, im.height * scale), Image.NEAREST).save(path)

def bob_canvas(w, h): return Image.new('P', (w, h), TRANSP)

# ------------------------------------------------------------------ the athlete (stick figure with volume)
def athlete(pose, w=32, h=48, woman=False, scale=1.0, flip=False, kit=None, outline=1, ball=None, back=False):
    """pose: dict of joint -> (x, y) in a 32x48 box (feet at y 46): head, neck, hip, lsh/rsh not needed:
    keys: head, neck, hip, lel, lha, rel, rha, lkn, lft, rkn, rft.  'l' = the far limb (drawn first).
    kit: dict of colour roles (defaults: player colours)."""
    k = dict(hair=HAIR, skin=SKIN, skind=SKIND, shirt=SHIRT, shirtd=SHIRTD, shorts=SHORTS, shoes=SHOES, out=1)
    if kit: k.update(kit)
    S = 4                                    # draw at 4x, then shrink without smoothing
    big = Image.new('P', (w * S, h * S), TRANSP); d = ImageDraw.Draw(big)
    def P(n):
        x, y = pose[n]
        if flip: x = 32 - x
        return ((x * scale) * S, (y * scale) * S)
    def limb(a, b, col, width, oc=None):
        d.line([P(a), P(b)], fill=col, width=int(width * S * scale))
        r = width * S * scale / 2
        for q in (P(a), P(b)): d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=col)
    oc = k['out']
    # outline pass: everything slightly thicker in the outline colour
    if outline:
        for a, b, wd in (('hip', 'lkn', 3.6), ('lkn', 'lft', 3.0), ('neck', 'lel', 3.0), ('lel', 'lha', 2.6),
                         ('neck', 'hip', 6.2), ('hip', 'rkn', 3.6), ('rkn', 'rft', 3.0), ('neck', 'rel', 3.0), ('rel', 'rha', 2.6)):
            limb(a, b, oc, wd + 1.4)
        hx, hy = P('head'); r = 3.9 * S * scale
        d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=oc)
    # far limbs (darker)
    limb('hip', 'lkn', k['skind'], 3.0); limb('lkn', 'lft', k['skind'], 2.4)
    fx, fy = P('lft'); d.ellipse([fx - 2.2 * S * scale, fy - 1.5 * S * scale, fx + 2.2 * S * scale, fy + 1.5 * S * scale], fill=k['shoes'])
    limb('neck', 'lel', k['shirtd'], 2.6); limb('lel', 'lha', k['skind'], 2.0)
    # body, with its shadow side (the back) in the darker shirt colour
    limb('neck', 'hip', k['shirt'], 5.6)
    dirb = 1 if (pose['head'][0] >= pose['neck'][0]) != flip else -1
    (nx, ny), (hx0, hy0) = P('neck'), P('hip')
    off = -dirb * 1.7 * S * scale
    d.line([(nx + off, ny + 1.2 * S), (hx0 + off, hy0 - 0.5 * S)], fill=k['shirtd'], width=int(1.6 * S * scale))
    # shorts: a short thick piece from the hip down both thighs
    hx, hy = P('hip')
    for kn in ('lkn', 'rkn'):
        kx, ky = P(kn); mx, my = hx + (kx - hx) * 0.45, hy + (ky - hy) * 0.45
        d.line([(hx, hy), (mx, my)], fill=k['shorts'], width=int(4.2 * S * scale))
    d.ellipse([hx - 2.6 * S * scale, hy - 2.2 * S * scale, hx + 2.6 * S * scale, hy + 2.2 * S * scale], fill=k['shorts'])
    # near limbs
    limb('hip', 'rkn', k['skin'], 3.0); limb('rkn', 'rft', k['skin'], 2.4)
    (kx, ky), (fx2, fy2) = P('rkn'), P('rft')
    d.line([(kx - dirb * 0.9 * S * scale, ky), (fx2 - dirb * 0.8 * S * scale, fy2 - 1.2 * S)], fill=k['skind'], width=max(1, int(0.9 * S * scale)))
    for kn in ('rkn',):
        kx, ky = P(kn); mx, my = hx + (kx - hx) * 0.45, hy + (ky - hy) * 0.45
        d.line([(hx, hy), (mx, my)], fill=k['shorts'], width=int(4.2 * S * scale))
    fx, fy = P('rft'); d.ellipse([fx - 2.2 * S * scale, fy - 1.5 * S * scale, fx + 2.2 * S * scale, fy + 1.5 * S * scale], fill=k['shoes'])
    limb('neck', 'rel', k['shirt'], 2.6); limb('rel', 'rha', k['skin'], 2.0)
    # head and hair
    hx, hy = P('head'); r = 3.3 * S * scale
    d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=k['skin'])
    dirx = 1 if (pose['head'][0] >= pose['neck'][0]) != flip else -1
    d.chord([hx - r, hy - r - 0.6 * S, hx + r, hy + r * 0.6], 180, 360, fill=k['hair'])
    if back:
        d.ellipse([hx - r, hy - r - 0.6 * S, hx + r, hy + r * 0.8], fill=k['hair'])
        if woman: d.ellipse([hx - 1.6 * S * scale, hy, hx + 1.6 * S * scale, hy + 5.5 * S * scale], fill=k['hair'])
    elif woman:      # a pony tail at the back of the head
        bx = hx - dirx * r * 0.9
        d.ellipse([bx - 1.8 * S * scale, hy - 0.5 * S, bx + 1.8 * S * scale, hy + 4.5 * S * scale], fill=k['hair'])
    else:
        xa, xb = sorted((hx - dirx * r, hx - dirx * r * 0.55)); d.rectangle([xa, hy - r * 0.3, xb, hy + r * 0.2], fill=k['hair'])
    if not back:                                  # an eye
        ex, ey = hx + dirx * r * 0.5, hy + 0.1 * S
        d.rectangle([ex - 0.45 * S * scale, ey - 0.45 * S * scale, ex + 0.45 * S * scale, ey + 0.55 * S * scale], fill=oc)
    if ball:
        bx, by, br, bc = ball
        bx = (32 - bx if flip else bx) * scale * S; by = by * scale * S; br = br * scale * S
        d.ellipse([bx - br - S, by - br - S, bx + br + S, by + br + S], fill=oc)
        d.ellipse([bx - br, by - br, bx + br, by + br], fill=bc)
    small = big.resize((w, h), Image.NEAREST)
    return small

# common poses (32x48 box, feet at y ~46)
def pose_stand():
    return dict(head=(16, 6), neck=(16, 12), hip=(16, 26), lel=(13, 19), lha=(12, 26), rel=(19, 19), rha=(20, 26),
                lkn=(14, 36), lft=(14, 45), rkn=(18, 36), rft=(18, 45))

def lerp_pose(a, b, t):
    return {k: (a[k][0] + (b[k][0] - a[k][0]) * t, a[k][1] + (b[k][1] - a[k][1]) * t) for k in a}

def run_cycle(n=6, lean=2):
    out = []
    for i in range(n):
        ph = 2 * math.pi * i / n
        s = math.sin(ph); c = math.cos(ph)
        p = dict(head=(17 + lean, 6), neck=(16 + lean, 12), hip=(15, 26))
        p['rkn'] = (15 + 6 * s, 35 - 2 * max(0, s)); p['rft'] = (15 + 7 * s - 3 * max(0, c), 45 - 4 * max(0, -c))
        p['lkn'] = (15 - 6 * s, 35 - 2 * max(0, -s)); p['lft'] = (15 - 7 * s - 3 * max(0, -c), 45 - 4 * max(0, c))
        p['rel'] = (16 + lean - 5 * s, 18); p['rha'] = (17 + lean - 7 * s, 22 - 2 * abs(s))
        p['lel'] = (16 + lean + 5 * s, 18); p['lha'] = (17 + lean + 7 * s, 22 - 2 * abs(s))
        out.append(p)
    return out

# ------------------------------------------------------------------ sound
def tosamp(x, gain=1.0):
    x = np.asarray(x, dtype=float) * gain
    m = np.max(np.abs(x)) + 1e-9
    return x / m * 0.95 if m > 0.95 else x

def env(n, a=0.005, dcy=0.2, rate=11025):
    t = np.arange(n) / rate
    e = np.minimum(1.0, t / max(a, 1e-4)) * np.exp(-t / dcy)
    return e

def noise(n, seed=1):
    return np.random.default_rng(seed).uniform(-1, 1, n)

def lowpass(x, k):
    if k <= 1: return np.asarray(x)
    return np.convolve(x, np.ones(k) / k, 'same')

def bandnoise(n, lo_k, hi_k, seed=1):
    x = noise(n, seed)
    return lowpass(x, lo_k) - lowpass(x, hi_k)

def thump(n, f0, f1, dcy, rate=11025):
    t = np.arange(n) / rate
    f = f0 + (f1 - f0) * np.minimum(1, t / 0.05)
    return np.sin(2 * np.pi * np.cumsum(f) / rate) * np.exp(-t / dcy)

def crowd(seconds, rate=8000, seed=3, swell=True):
    n = int(seconds * rate)
    x = np.zeros(n)
    rng = np.random.default_rng(seed)
    base = bandnoise(n, 3, 30, seed)
    # many voices: amplitude modulated noise bands
    for i in range(10):
        f = rng.uniform(300, 900)
        t = np.arange(n) / rate
        car = np.sin(2 * np.pi * (f + 40 * np.sin(2 * np.pi * rng.uniform(0.5, 2) * t)) * t)
        x += car * (0.5 + 0.5 * np.sin(2 * np.pi * rng.uniform(1, 4) * t + rng.uniform(0, 6))) * 0.08
    x += base * 0.9
    e = np.ones(n)
    if swell:
        a = int(0.15 * rate); e[:a] = np.linspace(0, 1, a)
        r = int(seconds * 0.5 * rate); e[-r:] = np.linspace(1, 0, r) ** 1.5
    return tosamp(x * e)

def whistle(seconds=0.6, rate=11025):
    n = int(seconds * rate); t = np.arange(n) / rate
    f = 2900 + 120 * np.sign(np.sin(2 * np.pi * 28 * t))
    x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / rate)) * 0.6 + noise(n, 7) * 0.15
    e = np.minimum(1, t / 0.02) * np.minimum(1, (seconds - t) / 0.08)
    return tosamp(lowpass(x, 2) * e)

def beep(f, seconds, rate=11025, sq=True):
    n = int(seconds * rate); t = np.arange(n) / rate
    x = np.sign(np.sin(2 * np.pi * f * t)) if sq else np.sin(2 * np.pi * f * t)
    e = np.minimum(1, (seconds - t) / 0.02)
    return x * 0.7 * e

# speech (the formant robot voice of Stronkie Soft)
sys.path.insert(0, HERE)
import voice

def speak(phon, rate=6000, speed=1.0):
    x = voice.say(phon)
    if rate != 8000:
        idx = np.arange(0, len(x), 8000 / rate); x = np.interp(idx, np.arange(len(x)), x)
    if speed != 1.0:
        idx = np.arange(0, len(x), speed); x = np.interp(idx, np.arange(len(x)), x)
    return tosamp(x)

# ------------------------------------------------------------------ music
NOTES = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}
def period(note, inst_len=32):
    """note like 'C3' -> Paula period for an instrument loop of inst_len bytes"""
    name, octv = note[:-1], int(note[-1])
    f = 440.0 * 2 ** ((NOTES[name] + 12 * (octv - 4) - 9) / 12)
    return int(round(3546895 / (f * inst_len)))

def seq(s, tick=6, inst_len=32):
    """'C4/2 E4/1 -/1 ...' -> words: period, ticks ... (0 = rest), $ffff = loop"""
    out = []
    for tok in s.split():
        n, l = tok.split('/')
        out += [0 if n == '-' else period(n, inst_len), int(float(l) * tick)]
    return out + [0xffff]

def song_lines(label, melody, bass, tick=6):
    m = seq(melody, tick); b = seq(bass, tick)
    lm = sum(m[1:-1:2]); lb = sum(b[1:-1:2])           # (keep both loops the same length)
    if lb < lm: b = b[:-1] + [0, lm - lb, 0xffff]
    if lm < lb: m = m[:-1] + [0, lb - lm, 0xffff]
    return ['%s_m\tdc.w\t%s' % (label, ','.join(str(v) for v in m)),
            '%s_b\tdc.w\t%s' % (label, ','.join(str(v) for v in b))]

# ------------------------------------------------------------------ scenery (the Amiga look)
# Painted in full colour, then put into the palette with ordered (Bayer) dithering, like the
# Amiga artists did by hand.  Only the event's own colours are used (never the player colours).
BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0 - 0.47

def pal_rgb(pal):
    return np.array([rgb12(c) for c in pal], float)

DYNAMIC = set()        # colours the event changes while it runs (the rival's kit...): never in the scenery

def to_indices(rgb, pal, allowed=None, spread=26, x0=0, y0=0):
    """rgb: HxWx3 float array -> HxW palette indices (nearest of the allowed colours, Bayer dithered)"""
    P = pal_rgb(pal)
    idx = np.array(allowed if allowed is not None else [i for i in range(min(25, len(pal))) if i not in DYNAMIC])
    h, w, _ = rgb.shape
    by = BAYER4[(np.arange(h)[:, None] + y0) % 4, (np.arange(w)[None, :] + x0) % 4][:, :, None]
    v = rgb + by * spread
    d = ((v[:, :, None, :] - P[idx][None, None, :, :]) ** 2).sum(3)
    return idx[d.argmin(2)].astype('uint8')

def paint(im, x0, y0, rgb, pal, allowed=None, spread=26, mask=None):
    """put an RGB array into the P image at x0, y0 (mask: HxW bool, where to paint)"""
    a = np.array(im)
    q = to_indices(np.asarray(rgb, float), pal, allowed, spread, x0, y0)
    h, w = q.shape
    region = a[y0:y0 + h, x0:x0 + w]
    if mask is None: region[:] = q
    else: region[mask] = q[mask]
    im.paste(Image.fromarray(a, 'P'))

def vgrad(w, h, stops):
    """stops: [(t 0..1, (r, g, b)), ...] -> HxWx3 vertical gradient"""
    ts = np.linspace(0, 1, h)
    out = np.zeros((h, w, 3))
    for c in range(3):
        out[:, :, c] = np.interp(ts, [s[0] for s in stops], [s[1][c] for s in stops])[:, None]
    return out

def stands_rgb(w, h, seed=7, roof=True, light=1.0, night=False):
    """a stadium stand: the roof with its lights, rows of spectators, aisles, the front wall"""
    rnd = random.Random(seed)
    a = np.zeros((h, w, 3)); a[:] = (40, 44, 64) if not night else (18, 20, 34)
    top = 0
    if roof:                                         # the roof: dark, with a steel truss and lights
        rh = max(8, h // 7)
        a[:rh] = (34, 36, 52) if not night else (14, 15, 26)
        for x in range(-rh, w, 8):
            for i in range(rh):
                for xx in (x + i, x + 2 * rh - i):
                    if 0 <= xx < w and i < rh - 2: a[i, xx] = (78, 82, 104) if not night else (40, 42, 60)
        a[rh - 2:rh] = (150, 150, 170) if not night else (70, 70, 90)
        for x in range(30, w, 72):                    # floodlights with a glow
            for yy in range(rh - 6, min(h, rh + 10)):
                for xx in range(x - 14, x + 15):
                    if 0 <= xx < w:
                        dd = ((xx - x) / 14.0) ** 2 + ((yy - (rh - 3)) / 8.0) ** 2
                        if dd < 1: a[yy, xx] = a[yy, xx] * dd + np.array((255, 250, 220)) * (1 - dd) * (0.35 if not night else 0.55)
            a[rh - 5:rh - 2, x - 6:x + 7] = (255, 255, 235)
        top = rh
    shirts = [(220, 40, 40), (40, 90, 220), (250, 210, 40), (240, 240, 240), (40, 170, 70), (250, 130, 30), (170, 60, 200), (60, 200, 220)]
    skins = [(250, 200, 160), (220, 160, 110), (160, 100, 60), (110, 70, 40)]
    row = 5
    nrows = (h - top - 3) // row
    for r in range(nrows):
        y = top + r * row
        dep = (r + 1) / nrows                         # 0 at the back (dark) .. 1 at the front
        f = (0.45 + 0.55 * dep) * light * (0.6 if night else 1)
        a[y:y + row] = np.array((60, 66, 96)) * f     # the seats
        a[y + row - 1] = np.array((30, 32, 50)) * f   # the step
        x = rnd.randrange(3)
        while x < w - 3:
            if rnd.random() < 0.88:
                sh = np.array(rnd.choice(shirts)) * f; sk = np.array(rnd.choice(skins)) * f
                up = rnd.random() < 0.12
                a[y + 2:y + 4, x:x + 3] = sh          # the body
                a[y, x + 1] = sk; a[y + 1, x:x + 2] = sk; a[y + 1, x + 1] = sk * 1.05   # the head
                if up: a[max(top, y - 1), x + 2] = sk  # an arm in the air
            x += 3 + (1 if rnd.random() < 0.3 else 0)
    for x in range(52, w, 104):                       # the aisles
        for y in range(top, top + nrows * row):
            a[y, x:x + 4] = (120, 120, 140) if (y % row) < 3 else (80, 80, 100)
    yb = top + nrows * row
    a[yb:] = (70, 74, 96); a[yb] = (190, 190, 200)
    return np.clip(a, 0, 255)

def stands(im, y0, y1, pal, allowed=None, seed=7, roof=True, light=1.0, night=False, x0=0, x1=320):
    paint(im, x0, y0, stands_rgb(x1 - x0, y1 - y0, seed, roof, light, night), pal, allowed, 20)

SPONSORS = ['STRONKIE SOFT', 'BURP ROOT BEER', 'PENGUIN ICE', 'SOFTY ROLLS', 'GOLD RUSH', 'TRAPDOOR RAM', 'PIE CO.']

def ad_boards(im, y, pal, names=None, h=10, seed=1, x0=0, x1=320):
    """a row of advertising boards (exact palette colours: bright board, dark letters or the other way)"""
    d = ImageDraw.Draw(im)
    P = pal_rgb(pal)
    def near(rgb, excl=()):
        dd = ((P - np.array(rgb)) ** 2).sum(1)
        for e in list(excl) + list(DYNAMIC) + list(range(25, len(dd))): dd[e] = 1e9
        return int(dd.argmin())
    schemes = [((20, 40, 120), (255, 255, 255)), ((220, 30, 30), (255, 240, 120)), ((250, 210, 40), (20, 20, 30)),
               ((240, 240, 240), (200, 20, 20)), ((20, 20, 30), (250, 210, 40)), ((40, 150, 60), (255, 255, 255))]
    names = names or SPONSORS
    rnd = random.Random(seed); x = x0; i = 0
    while x < x1:
        t = names[i % len(names)]; i += 1
        bw = len(t) * 8 + 12
        if x + bw > x1 and x1 < 320:                  # (a board that does not fit: an empty one up to x1)
            d.rectangle([x, y, x1 - 1, y + h - 1], fill=near((20, 20, 30))); break
        bg, fg = schemes[(i + seed) % len(schemes)]
        bi = near(bg); fi = near(fg, (bi,))
        d.rectangle([x, y, min(x1, x + bw) - 1, y + h - 1], fill=bi)
        d.line([x, y, min(x1, x + bw) - 1, y], fill=near((255, 255, 255)) if bi != near((255, 255, 255)) else near((200, 200, 200)))
        text8(im, x + 6, y + (h - 8) // 2 + 1, t, fi)
        d.line([x + bw - 1, y, x + bw - 1, y + h - 1], fill=near((10, 10, 10)))
        x += bw

def ground(im, box, pal, stops, allowed=None, stripes=None, noise=0, seed=3, spread=30):
    """a dithered band (grass, track, sand, water...): stops = vertical colour stops;
    stripes: (width, (r, g, b) to add) for mowing stripes"""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    a = vgrad(w, h, stops)
    if stripes:
        sw, add = stripes
        for x in range(w):
            if ((x + x0) // sw) % 2: a[:, x] += add
    if noise:
        rng = np.random.default_rng(seed); a += rng.normal(0, noise, a.shape[:2])[:, :, None]
    paint(im, x0, y0, np.clip(a, 0, 255), pal, allowed, spread)

def topbar_grad(c0):
    """the copper gradient of the top bar (lines 0-22, colour 0), then colour 0 back to c0"""
    top = [(0, 0x58b), (1, 0x8bd), (2, 0x47a)]
    ramp = [0x469, 0x458, 0x358, 0x347, 0x346, 0x236, 0x235, 0x225, 0x224, 0x224, 0x124, 0x123, 0x123, 0x113,
            0x113, 0x112, 0x112, 0x112, 0x223, 0x334]
    return top + [(3 + i, c) for i, c in enumerate(ramp)] + [(24, c0)]

def with_topbar(items, c0=0x112):
    """an event's own copper gradient (from line 24 on) with the copper top bar in front of it"""
    return topbar_grad(c0)[:-1] + [it for it in items if it[0] >= 24]
