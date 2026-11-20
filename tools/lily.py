#!/usr/bin/env python3
"""lily.py - reads the melody out of a small LilyPond score (the kind on Wikipedia pages:
\\relative c' { ... } or absolute notes), for the national anthems of Stronkie's Olympics.
melody(text) -> [(midi note or None for a rest, length in quarter notes), ...]
Only the first voice is read; lyrics, chords and markup are skipped.
Created By Mark Stronks, Stronkie Soft."""
import re

STEP = {'c': 0, 'd': 1, 'e': 2, 'f': 3, 'g': 4, 'a': 5, 'b': 6}
SEMI = [0, 2, 4, 5, 7, 9, 11]
ACC = [('isis', 2), ('eses', -2), ('ses', -2), ('is', 1), ('es', -1), ('s', -1)]   # (dutch names; 'es', 'as' = e flat, a flat)
NOTE_RE = re.compile(r"^([a-g])((?:isis|eses|is|es|s)?)([',]*)(=[',]*)?(\d+\.*)?(\*\d+(?:/\d+)?)?")
SKIP_ARGS = {'key': 2, 'time': 1, 'partial': 1, 'clef': 1, 'tempo': 1, 'bar': 1, 'mark': 1, 'set': 3, 'override': 3,
             'numericTimeSignature': 0, 'autoBeamOff': 0, 'autoBeamOn': 0, 'stemUp': 0, 'stemDown': 0, 'voiceOne': 0,
             'voiceTwo': 0, 'oneVoice': 0, 'break': 0, 'fermata': 0, 'once': 0, 'unset': 2, 'transpose': 2,
             'tieUp': 0, 'tieDown': 0, 'slurUp': 0, 'slurDown': 0, 'phrasingSlurUp': 0, 'noBeam': 0, 'mf': 0, 'f': 0,
             'p': 0, 'ff': 0, 'pp': 0, 'mp': 0, 'fff': 0, 'sf': 0, 'sfz': 0, 'cresc': 0, 'dim': 0, 'accent': 0,
             'staccato': 0, 'tenuto': 0, 'marcato': 0, 'trill': 0, 'breathe': 0, 'arpeggio': 0, 'markup': 1,
             'omit': 1, 'hide': 1, 'tweak': 2, 'shape': 2, 'sustainOn': 0, 'sustainOff': 0, 'italianChordNames': 0}

def tokens(t):
    t = re.sub(r'%\{.*?%\}', ' ', t, flags=re.S)
    t = re.sub(r'%[^\n]*', ' ', t)
    out = []; i = 0
    while i < len(t):
        c = t[i]
        if c.isspace(): i += 1; continue
        if c == '"':
            j = t.index('"', i + 1); out.append(t[i:j + 1]); i = j + 1; continue
        if t.startswith('<<', i) or t.startswith('>>', i): out.append(t[i:i + 2]); i += 2; continue
        if c in '{}<>|~()[]': out.append(c); i += 1; continue
        if c == '\\':
            m = re.match(r'\\[A-Za-z]+|\\.', t[i:]); out.append(m.group(0)); i += len(m.group(0)); continue
        m = re.match(r'[^\s{}<>|~()\[\]"\\]+', t[i:]); out.append(m.group(0)); i += len(m.group(0))
    return out

def block(tk, i):
    """tk[i] == '{': the index after the matching '}'"""
    d = 0
    for j in range(i, len(tk)):
        if tk[j] in ('{', '<<'): d += 1
        elif tk[j] in ('}', '>>'):
            d -= 1
            if d == 0: return j + 1
    return len(tk)

def pitch_abs(step, oct_):          # step 0-6, octave: c' = 4 (middle C)
    return step, oct_

def melody(text, limit=None):
    tk = tokens(text)
    # the music: the first \relative / { ... } before any \addlyrics, \lyricmode, \new Lyrics
    notes = []
    st = dict(rel=None, dur=1.0)     # rel: (step, octave) of the previous note, or None (absolute)
    def parse(i, end, scale=1.0):
        prev_chord = None
        while i < end:
            x = tk[i]
            if x in ('\\addlyrics', '\\lyricmode', '\\lyricsto', '\\lyrics', '\\chordmode', '\\figuremode', '\\drummode', '\\midi', '\\layout', '\\header', '\\paper'):
                return end                                     # (the rest is not the melody)
            if x == '\\new':
                kind = tk[i + 1] if i + 1 < end else ''
                if kind in ('Lyrics', 'ChordNames', 'FiguredBass'): return end
                i += 2
                if i < end and tk[i] == '=': i += 2
                continue
            if x == '\\relative':
                m = NOTE_RE.match(tk[i + 1]) if i + 1 < end else None
                if m and tk[i + 1] != '{':
                    st['rel'] = (STEP[m.group(1)], 3 + m.group(3).count("'") - m.group(3).count(','))
                    i += 2
                else:
                    st['rel'] = (0, 4); i += 1                  # (\relative without a pitch: c')
                continue
            if x in ('\\times', '\\tuplet'):
                fr = tk[i + 1]; a, b = [int(v) for v in fr.split('/')]
                f = a / b if x == '\\times' else b / a
                j = i + 2
                if tk[j] == '{':
                    k = block(tk, j); parse(j + 1, k - 1, scale * f); i = k
                else: i = j
                continue
            if x == '\\repeat':                               # volta / unfold n { }: n times (the first ending)
                n = int(tk[i + 2]) if i + 2 < end and tk[i + 2].isdigit() else 2
                j = i + 3
                if j < end and tk[j] == '{':
                    k = block(tk, j)
                    alt = k < end and tk[k] == '\\alternative'
                    rel0 = st['rel']
                    for rep in range(n):
                        st['rel'] = rel0                       # (every pass: the same notes)
                        parse(j + 1, k - 1, scale)
                        if alt and tk[k + 1] == '{':
                            ends = []; a = k + 2
                            while a < end and tk[a] == '{':
                                b = block(tk, a); ends.append((a, b)); a = b
                            a, b = ends[min(rep, len(ends) - 1)]
                            parse(a + 1, b - 1, scale)
                    i = block(tk, k + 1) if alt else k
                else:
                    i = j
                continue
            if x in ('\\alternative',):
                j = i + 1
                if tk[j] == '{':
                    k = block(tk, j)
                    # the first ending only
                    if tk[j + 1] == '{':
                        kk = block(tk, j + 1); parse(j + 2, kk - 1, scale)
                    i = k
                else: i = j
                continue
            if x in ('\\grace', '\\acciaccatura', '\\appoggiatura', '\\afterGrace'):
                j = i + 1
                i = block(tk, j) if tk[j] == '{' else j + 1
                continue
            if x == '<<':                                       # parallel music: the first part only
                k = block(tk, i); j = i + 1
                if tk[j] == '{':
                    kk = block(tk, j); parse(j + 1, kk - 1, scale)
                else:
                    parse(j, k - 1, scale)
                i = k; continue
            if x.startswith('\\'):
                n = SKIP_ARGS.get(x[1:], 0)
                i += 1
                if x == '\\time' and i < end and tk[i].startswith('#'): i += 1
                if x == '\\tempo':                             # \tempo "text" 4 = 100, \tempo 4 = 100, \tempo "text"
                    if i < end and tk[i].startswith('"'): i += 1
                    if i < end and re.match(r'^\d+\.*$', tk[i]) and i + 1 < end and tk[i + 1] in ('=',): i += 3
                    elif i < end and re.match(r'^\d+\.*=\d+', tk[i]): i += 1
                    continue
                if x in ('\\set', '\\override', '\\once', '\\unset'):
                    while i < end and not tk[i].startswith('#') and tk[i] not in ('=',): i += 1
                    if i < end and tk[i] == '=': i += 1
                    if i < end and tk[i].startswith('#'):
                        if tk[i] in ('#', "#'") and i + 1 < end and tk[i + 1] == '(':
                            d = 0
                            while i < end:
                                if tk[i] == '(': d += 1
                                if tk[i] == ')':
                                    d -= 1
                                    if d == 0: break
                                i += 1
                        i += 1
                    continue
                if x == '\\markup':
                    if i < end and tk[i] == '{': i = block(tk, i)
                    else: i += 1
                    continue
                i += n; continue
            if x == '{':
                k = block(tk, i); parse(i + 1, k - 1, scale); i = k; continue
            if x == '~':
                if notes and notes[-1][0] is not None: notes[-1] = (notes[-1][0], notes[-1][1], True)
                i += 1; continue
            if x in ('}', '|', '(', ')', '[', ']', '>>') or x.startswith('-') or x.startswith('^') or x.startswith('_') or x.startswith('#'):
                i += 1; continue
            if x == '<':                                        # a chord: its first (top-most written) note
                j = i + 1; first = None
                while j < end and tk[j] != '>':
                    if first is None and NOTE_RE.match(tk[j]): first = tk[j]
                    j += 1
                dur = tk[j + 1] if j + 1 < end and re.match(r'^\d+\.*', tk[j + 1]) else ''
                if first:
                    note(first + re.match(r'^(\d*\.*)', dur).group(1) if dur else first, scale)
                i = j + (2 if dur else 1); continue
            m = re.match(r'^([rRs])(\d+\.*)?(\*\d+(?:/\d+)?)?', x)
            if m and (len(x) == 1 or x[1].isdigit() or x[1] == '*'):
                d = dur_of(m.group(2), m.group(3))
                notes.append((None, d * scale, False)); i += 1; continue
            if NOTE_RE.match(x):
                note(x, scale); i += 1; continue
            if re.match(r'^\d+\.*$', x):                       # a lone duration (after a chord): skip
                i += 1; continue
            i += 1
        return end
    def dur_of(ds, mul):
        if ds:
            n = int(ds.rstrip('.')); dots = ds.count('.')
            base = 4.0 / n; d = base; add = base
            for _ in range(dots): add /= 2; d += add
            st['dur'] = d
        d = st['dur']
        if mul:
            a, _, b = mul[1:].partition('/'); d = d * int(a) / (int(b) if b else 1)
        return d
    def note(x, scale):
        m = NOTE_RE.match(x)
        step = STEP[m.group(1)]; acc = 0
        for name, v in ACC:
            if m.group(2) == name: acc = v; break
        if m.group(1) in ('e', 'a') and m.group(2) == 's': acc = -1
        marks = m.group(3)
        if st['rel'] is None:
            oct_ = 3 + marks.count("'") - marks.count(',')
        else:
            ps, po = st['rel']
            # the octave that puts the note closest (within a fourth) to the previous one
            best = None
            for o in (po - 1, po, po + 1):
                dist = (o * 7 + step) - (po * 7 + ps)
                if -3 <= dist <= 3: best = o
            oct_ = best + marks.count("'") - marks.count(',')
            st['rel'] = (step, oct_)
        d = dur_of(m.group(5), m.group(6)) * scale
        midi = 12 * (oct_ + 1) + SEMI[step] + acc
        if notes and notes[-1][0] == midi and notes[-1][2]:       # (tied to the one before)
            p, dd, _ = notes[-1]; notes[-1] = (p, dd + d, False)
        else:
            notes.append((midi, d, False))
    # find the start: the first { or \relative
    i = 0
    tk2 = tk
    # ties: mark the note before a ~
    parse(0, len(tk2))
    out = [(n[0], n[1]) for n in notes]
    return out[:limit] if limit else out

def ties(text):
    return text

if __name__ == '__main__':
    import sys
    t = open(sys.argv[1]).read()
    print(melody(t))
