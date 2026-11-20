"""voice.py - formant speech synthesis (from Stronkie's Battleships), used for the RUMMIKUB! call."""
import math
import numpy as np
SR = 8000
PH = {   # name: (ms, F1, F2, F3, voiced amp, noise amp, noise centre, kind)
    'I': (110, 400, 1900, 2550, 1.0, 0, 0, 'v'), 'i': (120, 290, 2250, 2900, 1.0, 0, 0, 'v'),
    'ae': (130, 660, 1700, 2400, 1.0, 0, 0, 'v'), 'V': (120, 640, 1200, 2400, 1.0, 0, 0, 'v'),
    'u': (150, 320, 900, 2200, 1.0, 0, 0, 'v'), '@': (90, 500, 1500, 2500, 0.8, 0, 0, 'v'),
    'a': (130, 750, 1200, 2500, 1.0, 0, 0, 'v'), 'e': (110, 500, 1850, 2500, 1.0, 0, 0, 'v'),
    'o': (130, 450, 850, 2400, 1.0, 0, 0, 'v'),
    'aI': (220, 0, 0, 0, 1.0, 0, 0, 'd'), 'oI': (220, 0, 0, 0, 1.0, 0, 0, 'd'), 'oU': (180, 0, 0, 0, 1.0, 0, 0, 'd'),
    'j': (60, 280, 2250, 2900, 0.7, 0, 0, 'v'), 'r': (70, 460, 1300, 1650, 0.7, 0, 0, 'v'),
    'l': (60, 380, 900, 2500, 0.7, 0, 0, 'v'), 'w': (60, 300, 700, 2200, 0.7, 0, 0, 'v'),
    'm': (80, 280, 1000, 2200, 0.45, 0, 0, 'n'), 'n': (80, 280, 1700, 2600, 0.45, 0, 0, 'n'),
    'N': (90, 280, 2300, 2750, 0.45, 0, 0, 'n'),
    's': (130, 0, 0, 0, 0, 0.55, 5500, 'f'), 'S': (130, 0, 0, 0, 0, 0.6, 3000, 'f'),
    'f': (110, 0, 0, 0, 0, 0.3, 4500, 'f'), 'h': (70, 500, 1500, 2500, 0, 0.35, 1500, 'f'),
    'z': (100, 280, 1700, 2600, 0.35, 0.35, 5000, 'f'), 'v': (80, 280, 1300, 2300, 0.4, 0.2, 4000, 'f'),
    't': (90, 0, 0, 0, 0, 0.6, 4000, 's'), 'k': (90, 0, 0, 0, 0, 0.6, 2200, 's'), 'p': (80, 0, 0, 0, 0, 0.5, 1200, 's'),
    'd': (70, 0, 0, 0, 0.3, 0.4, 3500, 's'), 'b': (70, 0, 0, 0, 0.3, 0.3, 1000, 's'),
    'g': (70, 0, 0, 0, 0.3, 0.4, 1800, 's'), 'eI': (200, 0, 0, 0, 1.0, 0, 0, 'd'),
}
DIPH = {'eI': ((500, 1850, 2500), (300, 2200, 2900)), 'aI': ((750, 1200, 2500), (330, 2100, 2800)), 'oI': ((480, 800, 2400), (320, 2100, 2800)),
        'oU': ((480, 900, 2400), (330, 800, 2200))}

def resonator(x, f, bw):
    """time varying 2 pole resonator: f, bw per sample arrays"""
    y = np.zeros_like(x); y1 = y2 = 0.0
    for n in range(len(x)):
        r = math.exp(-math.pi * bw[n] / SR); c = 2 * r * math.cos(2 * math.pi * f[n] / SR)
        v = (1 - r) * x[n] + c * y1 - r * r * y2
        y2 = y1; y1 = v; y[n] = v
    return y

def say(text):
    phs = text.split()
    segs = []
    for p in phs:
        ms, f1, f2, f3, va, na, nf, kind = PH[p]
        n = int(SR * ms / 1000)
        segs.append((p, n, f1, f2, f3, va, na, nf, kind))
    total = sum(s[1] for s in segs) + int(SR * 0.05)
    F = np.zeros((3, total)); VA = np.zeros(total); NA = np.zeros(total); NF = np.full(total, 3000.0)
    pos = 0; last = (500, 1500, 2500)
    for (p, n, f1, f2, f3, va, na, nf, kind) in segs:
        if kind == 'd':
            a, b = DIPH[p]
            for i in range(n):
                t = i / n
                for k in range(3): F[k, pos + i] = a[k] * (1 - t) + b[k] * t
            VA[pos:pos + n] = va; last = b
        elif kind == 's':
            gap = int(n * 0.55)
            for k in range(3): F[k, pos:pos + n] = last[k]
            VA[pos:pos + gap] = 0; VA[pos + gap:pos + n] = va
            NA[pos + gap:pos + n] = na * np.linspace(1, 0.2, n - gap); NF[pos:pos + n] = nf
        elif kind == 'f' and f1 == 0:
            for k in range(3): F[k, pos:pos + n] = last[k]
            NA[pos:pos + n] = na; NF[pos:pos + n] = nf
        else:
            tgt = (f1, f2, f3)
            tr = min(int(SR * 0.03), n // 2)
            for i in range(n):
                t = min(1.0, i / tr) if tr else 1.0
                for k in range(3): F[k, pos + i] = last[k] * (1 - t) + tgt[k] * t
            VA[pos:pos + n] = va; NA[pos:pos + n] = na; NF[pos:pos + n] = nf if nf else 3000
            last = tgt
        pos += n
    F[:, pos:] = np.array(last)[:, None]
    # smooth the amplitude steps a little
    k = np.ones(40) / 40
    VA = np.convolve(VA, k, 'same'); NA = np.convolve(NA, k, 'same')
    # robotic voice: steady pitch with a slight fall, buzzy pulse source
    f0 = np.linspace(118, 96, total)
    ph = np.cumsum(f0 / SR) % 1.0
    src = (ph < 0.08).astype(float) * 3.0 - 0.24
    src = resonator(src, np.full(total, 150.0), np.full(total, 400.0)) * 3   # glottal shaping
    v = src * VA
    out = resonator(v, F[0], np.full(total, 70.0))
    out = out + resonator(v, F[1], np.full(total, 100.0)) * 0.7
    out = out + resonator(v, F[2], np.full(total, 160.0)) * 0.35
    noise = np.random.default_rng(len(text)).uniform(-1, 1, total)
    out = out + resonator(noise, NF, np.full(total, 1500.0)) * NA * 2.0
    out = out / (np.max(np.abs(out)) + 1e-9)
    out = np.tanh(out * 1.6) / np.tanh(1.6)            # a little drive: more robot
    return out

