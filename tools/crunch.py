#!/usr/bin/env python3
"""crunch.py - the Stronkie Soft cruncher for Amiga hunk files.

Packs the contents of every HUNK_CODE / HUNK_DATA in an executable with a
small LZ77 packer ("SOPK"), so the floppy version fits on one disk.
The game's own hunk loaders (src/loader.s, src/kernel.s: depack.s) unpack
each hunk in place: the packed bytes are read to the END of the hunk's memory
and unpacked forwards from its start.  The packer works out how much extra
room (the margin) that needs, and adds it to the hunk size in the header.

A packed hunk:  HUNK_PACKED ($7e9 | the memory bits of the original type)
                 dc.l  original type ($3e9/$3ea)
                 dc.l  unpacked size in longs
                 dc.l  alloc size in longs (from the header, before the margin)
                 dc.l  packed size in bytes
                 the packed bytes, padded to a long

The packed stream (all read forwards):
  bits come MSB first from bytes (a byte is fetched when the bit buffer runs out);
  literal bytes and offset low bytes are separate bytes in the same stream.
  1st item is always a literal (no flag).  Then:
   0            literal: one byte
   1 0          match, new offset: gamma(hi+1), byte lo; offset = hi*256+lo+1
                length: gamma(len-1)   (len >= 2)
   1 1          match, same offset as the last one: gamma(len)  (len >= 1)
  gamma(v), v >= 1: for each bit of v after the top one: 1, bit ; then 0.
  The depacker stops when the output reaches the unpacked size.

  python3 tools/crunch.py in out      packs a hunk file
  python3 tools/crunch.py -t file...  tests (pack + unpack + in place check)
"""
import sys, struct

HUNK_PACKED = 0x7e9
MAXOFF = 1 << 16
MAXLEN = 1 << 16


class Bits:
    def __init__(self):
        self.out = bytearray()
        self.bpos = -1          # index of the current bit byte
        self.nb = 8

    def bit(self, b):
        if self.nb == 8:
            self.bpos = len(self.out)
            self.out.append(0)
            self.nb = 0
        if b:
            self.out[self.bpos] |= 0x80 >> self.nb
        self.nb += 1

    def byte(self, v):
        self.out.append(v & 255)

    def gamma(self, v):
        n = v.bit_length()
        for i in range(n - 2, -1, -1):
            self.bit(1)
            self.bit((v >> i) & 1)
        self.bit(0)


def gbits(v):
    return 2 * (v.bit_length() - 1) + 1


def match_cost(off, ln, rep):
    if rep:
        return 2 + gbits(ln)
    return 2 + gbits(((off - 1) >> 8) + 1) + 8 + gbits(ln - 1)


def parse(data):
    """Optimal parse (cost in bits) with a hash chain match finder, rep offsets."""
    n = len(data)
    INF = 1 << 60
    # candidate matches per position: list of (offset, maxlen)
    head = {}
    prev = [-1] * n
    cands = [None] * n
    DEPTH = int(__import__("os").environ.get("CRDEPTH", "48"))
    for i in range(n):
        if i + 2 >= n:
            cands[i] = ()
            continue
        key = data[i:i + 3]
        j = head.get(key, -1)
        prev[i] = j
        head[key] = i
        res = []
        best = 2
        d = 0
        while j >= 0 and d < DEPTH and i - j <= MAXOFF:
            # length
            if data[j + best] == data[i + best] if i + best < n else False:
                ln = 3
                lim = min(n - i, MAXLEN)
                while ln < lim and data[j + ln] == data[i + ln]:
                    ln += 1
                if ln > best:
                    best = ln
                    res.append((i - j, ln))
                    if ln == lim:
                        break
            j = prev[j]
            d += 1
        # short 2-byte matches close by
        if i >= 1 and i + 1 < n:
            for o in range(1, min(i, 256) + 1):
                if data[i - o] == data[i] and data[i - o + 1] == data[i + 1]:
                    if not res or res[0][0] > o:
                        res.insert(0, (o, 2))
                    break
        cands[i] = res
    # forward DP: cost[i], plus the last offset to take rep matches into account
    cost = [INF] * (n + 1)
    how = [None] * (n + 1)   # (kind, off, len, prevpos)
    lastoff = [0] * (n + 1)
    cost[1] = 8
    how[1] = ('L', 0, 1, 0)
    for i in range(1, n):
        c = cost[i]
        if c >= INF:
            continue
        lo = lastoff[i]
        # literal
        if c + 9 < cost[i + 1]:
            cost[i + 1] = c + 9
            how[i + 1] = ('L', 0, 1, i)
            lastoff[i + 1] = lo
        # rep match
        if lo and i >= lo:
            ln = 0
            lim = min(n - i, MAXLEN)
            while ln < lim and data[i + ln - lo] == data[i + ln]:
                ln += 1
            if ln >= 1:
                for l in set((ln, 1, 2, 3) if ln < 8 else (ln, ln - 1, 1, 2, 3, 4)):
                    if l < 1 or l > ln:
                        continue
                    cc = c + match_cost(lo, l, True)
                    if cc < cost[i + l]:
                        cost[i + l] = cc
                        how[i + l] = ('R', lo, l, i)
                        lastoff[i + l] = lo
        # new matches: try the full length and a few shorter ones
        prevlen = 1
        for off, ln in cands[i]:
            ls = set([ln])
            if ln > 2:
                ls.update(range(max(prevlen + 1, 2), min(ln, prevlen + 9)))
            for l in ls:
                if l < 2 or l > ln:
                    continue
                cc = c + match_cost(off, l, off == lo)
                if cc < cost[i + l]:
                    cost[i + l] = cc
                    how[i + l] = ('R' if off == lo else 'M', off, l, i)
                    lastoff[i + l] = off
            prevlen = ln
    seq = []
    p = n
    while p > 0:
        h = how[p]
        seq.append(h)
        p = h[3]
    seq.reverse()
    return seq


def pack(data):
    data = bytes(data)
    if not data:
        return b''
    seq = parse(data)
    b = Bits()
    pos = 0
    first = True
    for kind, off, ln, _ in seq:
        if kind == 'L':
            if not first:
                b.bit(0)
            b.byte(data[pos])
        elif kind == 'R':
            b.bit(1); b.bit(1)
            b.gamma(ln)
        else:
            b.bit(1); b.bit(0)
            o = off - 1
            b.gamma((o >> 8) + 1)
            b.byte(o & 255)
            b.gamma(ln - 1)
        first = False
        pos += ln
    return bytes(b.out)


def unpack(src, ulen, trace=None):
    """Reference depacker.  trace(outpos, inpos) is called before every read of src."""
    out = bytearray()
    ip = 0
    bitbuf = 0
    nbits = 0

    def rbyte():
        nonlocal ip
        if trace:
            trace(len(out), ip)
        v = src[ip]
        ip += 1
        return v

    def rbit():
        nonlocal bitbuf, nbits
        if nbits == 0:
            bitbuf = rbyte()
            nbits = 8
        nbits -= 1
        return (bitbuf >> nbits) & 1

    def gamma():
        v = 1
        while rbit():
            v = v * 2 + rbit()
        return v

    if ulen == 0:
        return bytes(out)
    out.append(rbyte())
    last = 0
    while len(out) < ulen:
        if not rbit():
            out.append(rbyte())
            continue
        if rbit():
            off = last
            ln = gamma()
        else:
            hi = gamma() - 1
            off = hi * 256 + rbyte() + 1
            last = off
            ln = gamma() + 1
        for _ in range(ln):
            out.append(out[-off])
    return bytes(out)


def margin(src, ulen):
    """Room needed after the unpacked data, when the packed bytes sit at the end
    of a buffer of ulen+margin and are unpacked forwards from its start."""
    c = len(src)
    worst = [0]

    def tr(op, ip):
        # the packed byte ip lives at ulen+m-c+ip; output written so far ends at op
        # (the byte at op may be written before this read is used: count it)
        worst[0] = max(worst[0], (op + 1) - (ip + ulen - c))
    # a match can write up to len bytes before the next read: trace before every read,
    # plus the end
    unpack(src, ulen, tr)
    worst[0] = max(worst[0], ulen - (c + ulen - c))
    # matches: the writes between two reads.  Simulate exactly instead:
    return exact_margin(src, ulen)


def exact_margin(src, ulen):
    """Simulate writes and reads in order; packed data at ulen+m-c."""
    c = len(src)
    ip = 0
    op = 0
    bitbuf = 0
    nbits = 0
    need = 0      # max over reads of (op - ip) at the moment ip is read (op = bytes written)

    def rd():
        nonlocal ip, need
        # the byte at position ip must not have been overwritten: op <= base+ip
        need = max(need, op - ip)
        ip += 1
        return src[ip - 1]

    def rbit():
        nonlocal bitbuf, nbits
        if nbits == 0:
            bitbuf = rd()
            nbits = 8
        nbits -= 1
        return (bitbuf >> nbits) & 1

    def gamma():
        v = 1
        while rbit():
            v = v * 2 + rbit()
        return v
    rd(); op = 1
    last = 0
    while op < ulen:
        if not rbit():
            rd(); op += 1
            continue
        if rbit():
            op += gamma()
        else:
            hi = gamma() - 1
            rd()
            op += gamma() + 1
    # base = ulen + m - c must be >= need  ->  m >= need - ulen + c
    m = max(0, need - ulen + c)
    return (m + 3) & ~3


def read_hunks(b):
    """-> list of hunk records for a simple executable (as our assembler writes)."""
    p = 0

    def L():
        nonlocal p
        v = struct.unpack('>L', b[p:p + 4])[0]
        p += 4
        return v
    assert L() == 0x3f3
    assert L() == 0
    n = L()
    first, last = L(), L()
    sizes = [L() for _ in range(n)]
    items = []          # per hunk: list of (type, payload)
    for h in range(n):
        blocks = []
        while True:
            t = L()
            tt = t & 0x3fffffff
            if tt in (0x3e9, 0x3ea):
                ln = L()
                blocks.append((t, b[p:p + ln * 4]))
                p += ln * 4
            elif tt == 0x3eb:
                blocks.append((t, L()))
            elif tt == 0x3ec:
                rel = []
                while True:
                    cnt = L()
                    if cnt == 0:
                        break
                    tgt = L()
                    rel.append((tgt, [L() for _ in range(cnt)]))
                blocks.append((t, rel))
            elif tt == 0x3f2:
                break
            else:
                raise ValueError('hunk type %x' % t)
        items.append(blocks)
    return sizes, items


def crunch_exe(b):
    sizes, items = read_hunks(b)
    out = bytearray()

    def L(v):
        out.extend(struct.pack('>L', v))
    newsizes = list(sizes)
    body = bytearray()

    def BL(v):
        body.extend(struct.pack('>L', v))
    for h, blocks in enumerate(items):
        for t, pl in blocks:
            tt = t & 0x3fffffff
            if tt in (0x3e9, 0x3ea):
                pk = pack(pl)
                if len(pk) + 16 >= len(pl):         # does not pack: keep it as it is
                    BL(t); BL(len(pl) // 4); body.extend(pl)
                    continue
                alloc = sizes[h] & 0x3fffffff
                pk = pk + bytes(-len(pk) & 3)        # the loader reads it padded to a long
                m = exact_margin(pk, len(pl))
                # the packed bytes go to the end of the hunk memory: alloc*4 + room
                room = max(0, len(pl) + m - alloc * 4)
                newsizes[h] = (sizes[h] & 0xc0000000) | (alloc + (room + 3) // 4)
                BL((HUNK_PACKED) | (t & 0xc0000000))
                BL(tt)
                BL(len(pl) // 4)
                BL(alloc)
                BL(len(pk))
                body.extend(pk)
            elif tt == 0x3eb:
                BL(t); BL(pl)
            elif tt == 0x3ec:
                BL(t)
                for tgt, offs in pl:
                    BL(len(offs)); BL(tgt)
                    for o in offs:
                        BL(o)
                BL(0)
        BL(0x3f2)
    L(0x3f3); L(0); L(len(sizes)); L(0); L(len(sizes) - 1)
    for s in newsizes:
        L(s)
    out.extend(body)
    return bytes(out), sizes, newsizes


def test(paths):
    import time
    tot = tp = 0
    for f in paths:
        b = open(f, 'rb').read()
        t = time.time()
        pk, s0, s1 = crunch_exe(b)
        # verify every hunk
        sizes, items = read_hunks(b)
        for blocks in items:
            for tt, pl in blocks:
                if (tt & 0x3fffffff) in (0x3e9, 0x3ea):
                    q = pack(pl)
                    assert unpack(q, len(pl)) == pl, f
        extra = sum((a & 0x3fffffff) - (c & 0x3fffffff) for a, c in zip(s1, s0)) * 4
        print('%-22s %7d -> %7d  %3d%%  +%d bytes room  %.1fs' % (f.split('/')[-1], len(b), len(pk), 100 * len(pk) // len(b), extra, time.time() - t))
        tot += len(b); tp += len(pk)
    print('TOTAL %d -> %d (%d%%)' % (tot, tp, 100 * tp // tot))


if __name__ == '__main__':
    if sys.argv[1] == '-t':
        test(sys.argv[2:])
    else:
        b = open(sys.argv[1], 'rb').read()
        pk = crunch_exe(b)[0]
        open(sys.argv[2], 'wb').write(pk)
