#!/usr/bin/env python3
"""make_disk.py - builds the release files of Stronkie's Olympics:

  build/StronkiesOlympics_V<ver>_Disk1.adf / _Disk2.adf   the full game on 2 bootable OFS disks
  build/StronkiesOlympics_V<ver>_harddrive.zip            the drawer for a hard drive / CF card
  build/StronkiesOlympics_Demo.adf (+ _harddrive.zip)     the demo (DEMO=1: soccer only, 1 disk)

Writes its own Kickstart 1.3 bootblock, OFS file system and Workbench icons.
Usage: python3 tools/make_disk.py 0.1 [demo]
"""
import os, struct, subprocess, sys, zipfile
from PIL import Image, ImageDraw

VER = sys.argv[1] if len(sys.argv) > 1 else '1.0'
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
B = os.path.join(ROOT, os.environ.get('DISK_BUILD', 'build'))
GAME = 'SOlymp'
DRAWER = 'StronkiesOlympics'
def disk_list():
    """build/gen/disks.txt (tools/events.py): event file -> disk"""
    out = {}
    for l in open(os.path.join(ROOT, 'build', 'gen', 'disks.txt')):
        f, d = l.split(); out.setdefault(int(d), []).append(f)
    return out

# ---------------------------------------------------------------- icons
WB13 = [(0x00, 0x55, 0xaa), (0xff, 0xff, 0xff), (0x00, 0x00, 0x00), (0xff, 0x88, 0x00)]

def icon_image():
    """52x30, 2 planes, Workbench 1.3 colours: 0 blue, 1 white, 2 black, 3 orange: a torch with its flame."""
    W, H = 52, 30
    im = Image.new('P', (W, H), 0); d = ImageDraw.Draw(im)
    d.polygon([(19, 13), (33, 13), (29, 28), (23, 28)], fill=3, outline=2)
    d.rectangle([17, 10, 35, 13], fill=1, outline=2)
    d.polygon([(18, 10), (34, 10), (31, 3), (28, 6), (26, 0), (23, 5), (20, 2)], fill=3, outline=2)
    d.polygon([(22, 10), (30, 10), (26, 4)], fill=1)
    for x in (6, 44):
        d.line([x, 6, x, 22], fill=1); d.line([x - 3, 14, x + 3, 14], fill=1)
    return im

def drawer_image():
    W, H = 52, 24
    im = Image.new('P', (W, H), 0); d = ImageDraw.Draw(im)
    d.rectangle([4, 3, 47, 21], fill=3, outline=2)
    d.rectangle([4, 3, 47, 8], fill=1, outline=2)
    d.rectangle([20, 12, 31, 15], fill=2)
    d.text((14, 9), '', fill=2)
    return im

def install_image():
    """the installer: a floppy, an arrow, a hard disk."""
    W, H = 52, 26
    im = Image.new('P', (W, H), 0); d = ImageDraw.Draw(im)
    d.rectangle([2, 4, 19, 21], fill=2)                      # floppy
    d.rectangle([6, 4, 15, 10], fill=1); d.rectangle([12, 5, 14, 9], fill=2)
    d.rectangle([5, 13, 16, 20], fill=1)
    d.polygon([(22, 11), (29, 11), (29, 8), (34, 13), (29, 18), (29, 15), (22, 15)], fill=3)  # arrow
    d.rectangle([36, 7, 50, 19], fill=1, outline=2)          # hard disk
    d.line([38, 15, 48, 15], fill=2); d.rectangle([46, 17, 48, 17], fill=3)
    return im

def disk_image():
    W, H = 46, 24
    im = Image.new('P', (W, H), 0); d = ImageDraw.Draw(im)
    d.rectangle([4, 1, 41, 22], fill=2)
    d.rectangle([12, 1, 33, 8], fill=1); d.rectangle([26, 2, 30, 7], fill=2)
    d.rectangle([9, 11, 36, 21], fill=1)
    for i, col in enumerate((3, 2, 3)):                       # little tiles on the label
        d.rectangle([12 + i * 8, 13, 17 + i * 8, 20], fill=col)
    return im

def planes(im, depth=2):
    W, H = im.size; px = im.load(); wpr = (W + 15) // 16
    out = bytearray()
    for p in range(depth):
        for y in range(H):
            for w in range(wpr):
                v = 0
                for i in range(16):
                    x = w * 16 + i
                    if x < W and (px[x, y] >> p) & 1: v |= 0x8000 >> i
                out += struct.pack('>H', v)
    return bytes(out)

def diskobject(kind, im, stack=8192, tool=None, tooltypes=()):
    """kind: 4 = WBPROJECT, 3 = WBTOOL, 2 = WBDRAWER, 1 = WBDISK."""
    W, H = im.size
    o = struct.pack('>HH', 0xe310, 1)
    # Gadget
    o += struct.pack('>IhhhhHHHIIIiIHI', 0, 0, 0, W, H, 5, 3, 1, 1, 0, 0, 0, 0, 0, 0)
    o += struct.pack('>BB', kind, 0)
    o += struct.pack('>IIiiIIi', 1 if tool else 0, 1 if tooltypes else 0, -0x80000000, -0x80000000,
                     1 if kind in (1, 2) else 0, 0, stack)
    assert len(o) == 78
    if kind in (1, 2):
        nw = struct.pack('>hhhhBBIIIIIIIhhhhH', 50, 30, 360, 120, 255, 255, 0, 0x5f, 0, 0, 0, 0, 0, 90, 40, -1, -1, 1)
        o += nw + struct.pack('>ii', 0, 0)
    o += struct.pack('>hhhhhIBBI', 0, 0, W, H, 2, 1, 3, 0, 0)
    o += planes(im)
    if tool:
        t = tool.encode('latin-1') + b'\0'; o += struct.pack('>I', len(t)) + t
    if tooltypes:
        o += struct.pack('>I', (len(tooltypes) + 1) * 4)
        for tt in tooltypes:
            t = tt.encode('latin-1') + b'\0'; o += struct.pack('>I', len(t)) + t
    return o

# ---------------------------------------------------------------- OFS
BS = 512
NBLK = 1760

def csum(block):
    s = 0
    for i in range(0, BS, 4):
        s = (s + struct.unpack('>I', block[i:i + 4])[0]) & 0xffffffff
    return (-s) & 0xffffffff

def bootsum(bb):
    s = 0
    for i in range(0, 1024, 4):
        s += struct.unpack('>I', bb[i:i + 4])[0]
        if s > 0xffffffff: s = (s + 1) & 0xffffffff
    return (~s) & 0xffffffff

def name_hash(name):
    h = len(name)
    for c in name.upper():
        h = (h * 13 + ord(c)) & 0x7ff
    return h % 72

def bcpl(name, n=31):
    b = name.encode('latin-1')[:n - 1]
    return bytes([len(b)]) + b + bytes(n - 1 - len(b))

class ADF:
    def __init__(self, volume):
        self.img = bytearray(NBLK * BS)
        self.used = {0, 1, 880, 881}
        self.next = 882
        self.dirs = {880: {}}     # dir block -> {hash: [entry blocks]}
        self.headers = {}         # block -> bytearray
        self.volume = volume

    def alloc(self):
        while self.next in self.used:
            self.next += 1
            if self.next >= NBLK: self.next = 2
        b = self.next; self.used.add(b); return b

    def put(self, blk, data):
        self.img[blk * BS:(blk + 1) * BS] = data

    def link(self, parent, name, blk):
        self.dirs[parent].setdefault(name_hash(name), []).append(blk)

    def mkdir(self, parent, name):
        blk = self.alloc()
        h = bytearray(BS)
        struct.pack_into('>II', h, 0, 2, blk)
        h[432:432 + 31] = bcpl(name)
        struct.pack_into('>I', h, 500, parent)
        struct.pack_into('>i', h, 508, 2)
        self.headers[blk] = h; self.dirs[blk] = {}
        self.link(parent, name, blk)
        return blk

    def addfile(self, parent, name, data):
        hdr = self.alloc()
        chunks = [data[i:i + 488] for i in range(0, len(data), 488)] or [b'']
        dblocks = [self.alloc() for _ in chunks]
        for i, (blk, c) in enumerate(zip(dblocks, chunks)):
            d = bytearray(BS)
            nxt = dblocks[i + 1] if i + 1 < len(dblocks) else 0
            struct.pack_into('>IIIII', d, 0, 8, hdr, i + 1, len(c), nxt)
            d[24:24 + len(c)] = c
            struct.pack_into('>I', d, 20, csum(d))
            self.put(blk, d)
        # header + extension blocks, 72 data pointers each, stored backwards
        groups = [dblocks[i:i + 72] for i in range(0, len(dblocks), 72)]
        h = bytearray(BS)
        struct.pack_into('>IIII', h, 0, 2, hdr, len(groups[0]), 0)
        struct.pack_into('>I', h, 16, dblocks[0])
        for i, b in enumerate(groups[0]):
            struct.pack_into('>I', h, 24 + (71 - i) * 4, b)
        struct.pack_into('>I', h, 324, len(data))
        h[432:432 + 31] = bcpl(name)
        struct.pack_into('>I', h, 500, parent)
        struct.pack_into('>i', h, 508, -3)
        prev = h; exts = []
        for g in groups[1:]:
            eb = self.alloc(); e = bytearray(BS)
            struct.pack_into('>III', e, 0, 16, eb, len(g))
            for i, b in enumerate(g):
                struct.pack_into('>I', e, 24 + (71 - i) * 4, b)
            struct.pack_into('>I', e, 500, hdr)
            struct.pack_into('>i', e, 508, -3)
            struct.pack_into('>I', prev, 504, eb)
            exts.append((eb, e)); prev = e
        for eb, e in exts:
            struct.pack_into('>I', e, 20, 0); struct.pack_into('>I', e, 20, csum(e)); self.put(eb, e)
        self.headers[hdr] = h
        self.link(parent, name, hdr)
        return hdr

    def finish(self, bootcode):
        # hash tables and chains
        root = bytearray(BS)
        struct.pack_into('>IIIII', root, 0, 2, 0, 0, 72, 0)
        tables = {880: root}
        for dblk, table in self.dirs.items():
            t = tables.get(dblk) or self.headers[dblk]
            for hsh, entries in table.items():
                struct.pack_into('>I', t, 24 + hsh * 4, entries[0])
                for a, b in zip(entries, entries[1:]):
                    struct.pack_into('>I', self.headers[a], 496, b)
        for blk, h in self.headers.items():
            struct.pack_into('>I', h, 20, 0); struct.pack_into('>I', h, 20, csum(h)); self.put(blk, h)
        # bitmap (1 = free), blocks 2..1759
        bm = bytearray(BS)
        for blk in range(2, NBLK):
            if blk not in self.used:
                i = blk - 2
                w = 4 + (i // 32) * 4
                v = struct.unpack('>I', bm[w:w + 4])[0] | (1 << (i % 32))
                struct.pack_into('>I', bm, w, v)
        struct.pack_into('>I', bm, 0, csum(bm))
        self.put(881, bm)
        struct.pack_into('>i', root, 312, -1)
        struct.pack_into('>I', root, 316, 881)
        days, mins = 17485, 20 * 60      # 14 Nov 2025-ish, constant so builds are reproducible
        struct.pack_into('>III', root, 420, days, mins, 0)
        root[432:432 + 31] = bcpl(self.volume)
        struct.pack_into('>III', root, 472, days, mins, 0)
        struct.pack_into('>III', root, 484, days, mins, 0)
        struct.pack_into('>I', root, 508, 1)
        struct.pack_into('>I', root, 20, csum(root))
        self.put(880, root)
        # bootblock
        bb = bytearray(1024)
        bb[0:4] = b'DOS\0'
        struct.pack_into('>I', bb, 8, 880)
        bb[12:12 + len(bootcode)] = bootcode
        struct.pack_into('>I', bb, 4, bootsum(bb))
        self.img[0:1024] = bb
        return bytes(self.img)

BOOT_SRC = """
; Kickstart 1.3 bootblock code: find dos.library and start it
	lea	dosname(pc),a1
	jsr	-96(a6)			; FindResident
	tst.l	d0
	beq.s	.err
	move.l	d0,a0
	move.l	22(a0),a0		; RT_INIT
	moveq	#0,d0
	rts
.err	moveq	#-1,d0
	rts
dosname	dc.b	'dos.library',0
	even
"""

def build_adf(volume, files, readme, boot, startup=True):
    adf = ADF(volume)
    for name, data in files: adf.addfile(880, name, data)
    adf.addfile(880, 'ReadMe.txt', readme)
    adf.addfile(880, 'Disk.info', diskobject(1, disk_image()))
    if startup:
        s = adf.mkdir(880, 'S')
        adf.addfile(s, 'Startup-Sequence', (GAME + '\n').encode())
    img = adf.finish(boot)
    assert len(adf.used) < NBLK - 2, '%s is full' % volume
    return img, len(adf.used)

def main():
    demo = len(sys.argv) > 2 and sys.argv[2] == 'demo'
    B2 = os.path.join(ROOT, 'build', 'demo' if demo else 'full')
    rd = lambda n: open(os.path.join(B2, n), 'rb').read()
    readme = open(os.path.join(ROOT, 'ReadMe_Demo.txt' if demo else 'ReadMe.txt'), 'rb').read().replace(b'\r\n', b'\n')
    bsrc = os.path.join(B, 'boot.s')
    open(bsrc, 'w').write(BOOT_SRC)
    subprocess.check_call([sys.executable, os.path.join(ROOT, 'tools', 'asm68k.py'), bsrc, '-raw', '-o', os.path.join(B, 'boot.bin')], stdout=subprocess.DEVNULL)
    boot = open(os.path.join(B, 'boot.bin'), 'rb').read()
    tool_icon = diskobject(3, icon_image())
    drawer_icon = diskobject(2, drawer_image())
    open(os.path.join(B2, GAME + '.info'), 'wb').write(tool_icon)
    main_files = [(GAME, rd(GAME)), (GAME + '.game', rd(GAME + '.game')), (GAME + '.info', tool_icon)]
    out = []
    if demo:
        img, used = build_adf('Olympics1', main_files + [(f, rd(f)) for f in ('Ceremony.evt', 'Soccer.evt')], readme, boot)
        name = 'StronkiesOlympics_Demo'
        open(os.path.join(B, name + '.adf'), 'wb').write(img); out.append((name + '.adf', used))
        evs = ['Ceremony.evt', 'Soccer.evt']
    else:
        name = 'StronkiesOlympics_V%s' % VER
        dl = disk_list(); evs = ['Ceremony.evt']
        for k in sorted(dl):
            files = [(f, rd(f)) for f in dl[k]]
            if k == 1: files = main_files + [('Ceremony.evt', rd('Ceremony.evt'))] + files
            img, used = build_adf('Olympics%d' % k, files, readme, boot, startup=(k == 1))
            fn = name + '_Disk%d.adf' % k
            open(os.path.join(B, fn), 'wb').write(img); out.append((fn, used))
            evs += dl[k]
    zname = os.path.join(B, name + '_harddrive.zip')
    with zipfile.ZipFile(zname, 'w', zipfile.ZIP_DEFLATED) as z:
        for n, data in main_files: z.writestr(DRAWER + '/' + n, data)
        for f in evs: z.writestr(DRAWER + '/' + f, rd(f))
        z.writestr(DRAWER + '/ReadMe.txt', readme)
        z.writestr(DRAWER + '.info', drawer_icon)
    for n, u in out: print('%s: %d of %d blocks used' % (n, u, NBLK))
    print(os.path.basename(zname))
    ic = icon_image().copy(); ic.putpalette(sum(WB13, ()) + (0, 0, 0) * 252)
    ic.convert('RGB').resize((52 * 4, 30 * 4), Image.NEAREST).save(os.path.join(B, 'icon_preview.png'))

if __name__ == '__main__':
    main()
