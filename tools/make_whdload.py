"""make_whdload.py - the WHDLoad version of Stronkie's Olympics.

  build/whdload/StronkiesOlympics/              the install drawer
      StronkiesOlympics.slave                   (src/whdload.s)
      StronkiesOlympics.info                    project icon: WHDLoad, SLAVE=..., PRELOAD
      ReadMe / ReadMe.info
      data/SOlymp.game + data/*.evt                            the game (records are saved here too)
  build/whdload/StronkiesOlympics.info          drawer icon
  build/StronkiesOlympics_V<ver>_WHDLoad.lha    all of it (LhA level 2, stored)
  build/StronkiesOlympics_V<ver>_WHDLoad.zip    the same as a zip

Usage: python3 tools/make_whdload.py [version] [demo]
Created By Mark Stronks, Stronkie Soft 2026
"""
import os, shutil, struct, subprocess, sys, time, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_disk as md

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
B = os.path.join(ROOT, 'build')
VER = sys.argv[1] if len(sys.argv) > 1 else md.VER
PKG = 'StronkiesOlympics'
DEMO = len(sys.argv) > 2 and sys.argv[2] == 'demo'
EVS = ['Ceremony.evt', 'Soccer.evt'] if DEMO else ['Ceremony.evt', 'Soccer.evt', 'Basket.evt', 'Volley.evt', 'Bowling.evt', 'Surfing.evt', 'Skate.evt']
SRC = os.path.join(ROOT, 'build', 'demo' if DEMO else 'full')
SLAVE = PKG + '.slave'

README = """STRONKIE'S OLYMPICS  V{ver}{demo} - WHDLoad version
Created By Mark Stronks, Stronkie Soft (c) 2026

WHAT YOU NEED
  WHDLoad (www.whdload.de) installed on your hard drive, and 1 MB of
  free memory for the game (512K chip + 512K any). No Kickstart image
  is needed: the game brings everything it needs.

INSTALL
  Copy the drawer StronkiesOlympics (with its icon) anywhere on your
  hard drive, for example to Games:. Or unpack the .lha there:
      lha x StronkiesOlympics_V{ver}_WHDLoad.lha Games:

PLAY
  Double click the StronkiesOlympics icon in the drawer.
  F10 quits back to Workbench.
  The world records are saved in data/Olympics.dat.

  From the CLI:  cd Games:StronkiesOlympics
                 WHDLoad StronkiesOlympics.slave PRELOAD

FILES
  StronkiesOlympics.slave   the WHDLoad slave (source: src/whdload.s
                            on github.com/stronkie/sportsgames)
  data/SOlymp.game          the game
  data/*.evt                the ceremonies and the events, loaded one
                            at a time

Created By Mark Stronks, Stronkie Soft
"""

def text_icon():
    from PIL import Image, ImageDraw
    im = Image.new('P', (30, 22), 0); d = ImageDraw.Draw(im)
    d.rectangle([3, 1, 26, 20], fill=2); d.rectangle([4, 2, 25, 19], fill=1)
    for y in range(5, 18, 3): d.line([7, y, 22, y], fill=2)
    return im

# ------------------------------------------------------------------ LhA (level 2 headers, -lh0- stored)
def crc16(data, crc=0):
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc

def lha_entry(path, data, is_dir=False, mtime=None):
    mtime = int(mtime or time.time())
    parts = path.split('/')
    dirs, name = (parts, '') if is_dir else (parts[:-1], parts[-1])
    ext = b''
    def exth(t, body):
        return bytes([t]) + body
    exts = [exth(0x00, b'\0\0')]                       # header CRC (filled in below)
    if name: exts.append(exth(0x01, name.encode('latin-1')))
    if dirs: exts.append(exth(0x02, b''.join(p.encode('latin-1') + b'\xff' for p in dirs)))
    # each extension: [next size (2)] then type+body; the last next size is 0
    blob = b''
    for e in exts:
        blob += struct.pack('<H', len(e) + 2) + e
    blob += struct.pack('<H', 0)
    method = b'-lhd-' if is_dir else b'-lh0-'
    base = method + struct.pack('<IIIBBHB', len(data), len(data), mtime, 0x20, 2, crc16(data), ord('A'))
    total = 2 + len(base) + len(blob)
    hdr = bytearray(struct.pack('<H', total) + base + blob)
    crcpos = 2 + len(base) + 2 + 1                     # the common extension's body
    hdr[crcpos:crcpos + 2] = struct.pack('<H', crc16(bytes(hdr)))
    return bytes(hdr) + data

def lha_write(path, entries):
    with open(path, 'wb') as f:
        for e in entries: f.write(lha_entry(*e))
        f.write(b'\0')

def lha_read(path):
    """-> [(path, data, is_dir)], checking every CRC."""
    d = open(path, 'rb').read(); p = 0; out = []
    while d[p] != 0:
        total = struct.unpack('<H', d[p:p + 2])[0]
        method = d[p + 2:p + 7]; csize, osize, mt, attr, lvl, fcrc, osid = struct.unpack('<IIIBBHB', d[p + 7:p + 24])
        assert lvl == 2 and method in (b'-lh0-', b'-lhd-')
        hdr = bytearray(d[p:p + total]); q = 24; nxt = struct.unpack('<H', hdr[q:q + 2])[0]; q += 2
        name = ''; dirs = ''; hcrc = None
        while nxt:
            t = hdr[q]; body = bytes(hdr[q + 1:q + nxt - 2])
            if t == 0: hcrc = struct.unpack('<H', body[:2])[0]; hdr[q + 1:q + 3] = b'\0\0'
            if t == 1: name = body.decode('latin-1')
            if t == 2: dirs = body.replace(b'\xff', b'/').decode('latin-1')
            nxt = struct.unpack('<H', hdr[q + nxt - 2:q + nxt])[0]; q += len(body) + 3
        assert hcrc == crc16(bytes(hdr)), 'header CRC'
        data = d[p + total:p + total + csize]
        assert crc16(data) == fcrc, 'file CRC'
        out.append((dirs + name, data, method == b'-lhd-'))
        p += total + csize
    return out

# ------------------------------------------------------------------ the package
def main():
    root = os.path.join(B, 'whdload_demo' if DEMO else 'whdload'); shutil.rmtree(root, ignore_errors=True)
    pkg = os.path.join(root, PKG); os.makedirs(os.path.join(pkg, 'data'))
    subprocess.check_call([sys.executable, os.path.join(ROOT, 'tools', 'asm68k.py'), os.path.join(ROOT, 'src', 'whdload.s'),
                           '-o', os.path.join(B, SLAVE), '-map', os.path.join(B, 'whdload.map')], stdout=subprocess.DEVNULL)
    files = {
        PKG + '/' + SLAVE: open(os.path.join(B, SLAVE), 'rb').read(),
        PKG + '/' + PKG + '.info': md.diskobject(4, md.icon_image(), stack=10240, tool='WHDLoad',
                                                 tooltypes=('SLAVE=' + SLAVE, 'PRELOAD')),
        PKG + '/ReadMe.info': md.diskobject(4, text_icon(), stack=4096, tool='SYS:Utilities/More'),
        PKG + '/data/SOlymp.game': open(os.path.join(SRC, 'SOlymp.game'), 'rb').read(),
        PKG + '.info': md.diskobject(2, md.drawer_image()),
    }
    for e in EVS: files[PKG + '/data/' + e] = open(os.path.join(SRC, e), 'rb').read()
    files[PKG + '/ReadMe'] = README.format(ver=VER, demo=' DEMO' if DEMO else '').encode('latin-1')
    for n, d in files.items():
        open(os.path.join(root, n), 'wb').write(d)
    now = time.time()
    order = [(PKG, b'', True, now), (PKG + '.info', files[PKG + '.info'], False, now)]
    order += [(PKG + '/data', b'', True, now)]
    order += [(n, files[n], False, now) for n in sorted(files) if n.startswith(PKG + '/')]
    base = '%s_Demo' % PKG if DEMO else '%s_V%s' % (PKG, VER)
    lname = os.path.join(B, base + '_WHDLoad.lha')
    lha_write(lname, order)
    back = {n: d for n, d, isdir in lha_read(lname) if not isdir}
    assert back == files, 'the archive does not give back the files'
    zname = os.path.join(B, base + '_WHDLoad.zip')
    with zipfile.ZipFile(zname, 'w', zipfile.ZIP_DEFLATED) as z:
        for n in sorted(files): z.writestr(n, files[n])
    print('%s (%d bytes), %s' % (os.path.basename(lname), os.path.getsize(lname), os.path.basename(zname)))

if __name__ == '__main__':
    main()
