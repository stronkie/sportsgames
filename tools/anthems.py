#!/usr/bin/env python3
"""anthems.py - the national anthems of the 20 countries of Stronkie's Olympics, played at the medal
ceremony for the country that wins gold.  The melodies come from the scores in tools/anthems/*.ly
(all these anthems are old enough to be free to use); the bass is made here: the chord under each
part of a bar (I, IV, V7, ii, vi), its root.  Played once (an end mark), quietly, like all the music.
anthem_lines() -> the dc.w lines: anthem_tab (melody, bass for every country) and the songs.
Created By Mark Stronks, Stronkie Soft."""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lily, gfxlib as g

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'anthems')
N = 'C C# D D# E F F# G G# A A# B'.split()
END = 0xfffe                                       # (the player: stop here)

# country (in the order of make_main.C) -> file, tempo (quarter notes a minute), the most quarter notes to play
ANTHEMS = [('NETHERLANDS', 'nl', 72, None), ('GERMANY', 'de', 76, None), ('BELGIUM', 'be', 96, 48),
           ('FRANCE', 'fr', 108, None), ('BRITAIN', 'gb', 72, None), ('USA', 'us', 100, None), ('CANADA', 'ca', 92, 48),
           ('ITALY', 'it', 100, None), ('SPAIN', 'es', 100, None), ('SWEDEN', 'se', 76, None), ('NORWAY', 'no', 84, 48),
           ('DENMARK', 'dk', 80, None), ('JAPAN', 'jp', 60, None), ('BRAZIL', 'br', 100, 48), ('AUSTRALIA', 'au', 100, None),
           ('POLAND', 'pl', 100, 48), ('SWITZERLAND', 'ch', 84, None), ('AUSTRIA', 'at', 92, None), ('IRELAND', 'ie', 84, None),
           ('MEXICO', 'mx', 100, 48)]
DRONE = {'jp'}                                      # (no major-key chords: a drone on the tonic and the fifth)

def name(m): return N[m % 12] + str(m // 12 - 1)

def read(code):
    p = os.path.join(DIR, code + '.notes')         # (from a MIDI file: 'time 4 partial 1', then midi/quarters ...)
    if os.path.exists(p):
        ls = [l for l in open(p) if not l.startswith('%')]
        h = ls[0].split(); beats, partial = float(h[1]), float(h[3])
        mel = []
        for tok in ' '.join(ls[1:]).split():
            a, d = tok.split('/')
            if float(d) > 0: mel.append((None if a == 'r' else int(a), float(d)))
        return mel, beats, partial
    p = os.path.join(DIR, code + '.ly')
    if not os.path.exists(p): return None
    t = open(p).read()
    if '\\language "deutsch"' in t:                 # (German names: b = B flat, h = B)
        t = re.sub(r'(?<![\\a-z])b(?=(es|is)?[\',]*\d*\.*[\s\[\(\)\]~|}])', 'bes', t.replace('\\language "deutsch"', ''))
        t = re.sub(r'(?<![\\a-z])h(?=(is)?[\',]*\d*\.*[\s\[\(\)\]~|}])', 'b', t)
    mel = lily.melody(t)
    while mel and mel[0][0] is None: mel = mel[1:]   # (no rests at the start or the end)
    while mel and mel[-1][0] is None: mel = mel[:-1]
    tm = re.search(r'\\time\s+(\d+)/(\d+)', t)
    beats = int(tm.group(1)) * 4 / int(tm.group(2)) if tm else 4.0
    pm = re.search(r'\\partial\s+(\d+)(\.?)', t)
    partial = (4 / int(pm.group(1))) * (1.5 if pm.group(2) else 1) if pm else 0.0
    return mel, beats, partial

def fit(mel):
    """octaves so that the tune lies in C4 .. G5 as far as it goes"""
    ps = [p for p, _ in mel if p is not None]
    hi, lo = max(ps), min(ps)
    sh = 0
    while hi + sh > 81: sh -= 12                     # A5 (the highest note Paula plays here)
    while lo + sh < 57 and hi + sh + 12 <= 81: sh += 12
    return [(None if p is None else p + sh, d) for p, d in mel]

CHORDS = [(0, (0, 4, 7), 3), (7, (7, 11, 2, 5), 2), (5, (5, 9, 0), 2), (2, (2, 5, 9), 0), (9, (9, 0, 4), 0)]

def bass(mel, beats, partial, key, drone=False):
    """[(midi, quarters)]: the root of the best chord for every half bar (every bar in 3/4)"""
    seg = beats / 2 if beats == 4 else beats
    total = sum(d for _, d in mel)
    out = []
    if partial: out.append((None, partial))
    t0 = partial; k = 0
    while t0 < total - 1e-6:
        t1 = min(t0 + seg, total)
        if drone:
            root = key if k % 2 == 0 else key + 7
        else:
            w = {}
            t = 0.0
            for p, d in mel:                         # how long each pitch class sounds in [t0, t1)
                a, b = max(t, t0), min(t + d, t1)
                if p is not None and b > a: w[(p - key) % 12] = w.get((p - key) % 12, 0) + (b - a) * (1.5 if abs(t - t0) < 1e-6 else 1)
                t += d
            best = max(CHORDS, key=lambda c: (sum(w.get(x, 0) for x in c[1]), c[2]))
            root = key + best[0]
        r = 36 + (root % 12)                          # C2 .. B2
        if r < 40: r += 12                            # (E2 .. D#3)
        out.append((r, t1 - t0))
        t0 = t1; k += 1
    return out

def words(seq, bpm):
    fr = 3000.0 / bpm                                 # frames (50 a second) for a quarter note
    out = []; carry = 0.0
    for p, d in seq:
        f = d * fr + carry; n = int(round(f)); carry = f - n
        if n <= 0: continue
        if p is None: out += [0, n]
        else:
            n1 = max(1, n - 2) if n > 4 else n        # (a little gap: repeated notes are heard)
            out += [g.period(name(p)), n1]
            if n1 < n: out += [0, n - n1]
    return out

def anthem_lines(nctry):
    lines = ['anthem_tab']
    songs = []
    for i, (ctry, code, bpm, most) in enumerate(ANTHEMS[:nctry]):
        r = read(code)
        if not r:
            lines.append('\tdc.l\tsong_fanfare_m,song_fanfare_b\t; %s: (no anthem)' % ctry); continue
        mel, beats, partial = r
        if most:                                      # (the first part only: stop at a long note after 'most')
            t = 0.0; cut = len(mel)
            for j, (p, d) in enumerate(mel):
                t += d
                if t >= most and d >= 1.5: cut = j + 1; break
            mel = mel[:cut]
        mel = fit(mel)
        key = [p for p, _ in mel if p is not None][-1] % 12   # (anthems end on the key note)
        b = bass(mel, beats, partial, key, code in DRONE)
        m_w = words(mel, bpm) + [0, 25, END]
        b_w = words(b, bpm)
        lm = sum(m_w[1:-1:2]); lb = sum(b_w[1::2])
        if lb < lm: b_w += [0, lm - lb]
        b_w += [END]
        lines.append('\tdc.l\tanthem_%s_m,anthem_%s_b\t; %s' % (code, code, ctry))
        songs.append('anthem_%s_m\tdc.w\t%s' % (code, ','.join(str(v) for v in m_w)))
        songs.append('anthem_%s_b\tdc.w\t%s' % (code, ','.join(str(v) for v in b_w)))
    return lines + songs

if __name__ == '__main__':
    for ctry, code, bpm, most in ANTHEMS:
        r = read(code)
        if not r: print('%-12s -' % ctry); continue
        mel, beats, partial = r
        q = sum(d for _, d in mel)
        print('%-12s %3d notes %5.1f quarters %4.1f s  %s' % (ctry, len(mel), q, q * 60 / bpm,
              ' '.join(('-' if p is None else name(p)) + '/%g' % d for p, d in fit(mel)[:14])))
