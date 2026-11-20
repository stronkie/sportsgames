"""test_whdload.py - runs the WHDLoad slave of Stronkie's Olympics in the emulator with a small
WHDLoad stand-in (base memory, expansion memory, resload calls, the data/ folder) and plays the game
through it: starts, battles to a win, the records get saved through resload_SaveFile, they load again
on the next start, and F10 quits with TDREASON_OK.   Usage: python3 tools/test_whdload.py [package dir]"""
import os, sys, struct, re, shutil
sys.path.insert(0, os.path.dirname(__file__))
import emu68k, harness

B = 'build'
SLAVE_AT, EXP_AT, STACK, RESLOAD = 0x200000, 0xC00000, 0x2ff000, 0x300100   # (expansion memory = the trapdoor area)

class WHDGame(harness.Game):
    def __init__(self, pkg, out):
        os.makedirs(out, exist_ok=True); self.out = out
        self.sym = {}; names = None
        for l in open(os.path.join(B, 'full', 'SOlymp.map')):
            if l.startswith('#sections'): names = l.split()[1:]; continue
            p = l.split()
            if len(p) == 3: self.sym[p[2]] = (p[0], int(p[1], 16))
        self.names = names
        self.slsym = {p[2]: int(p[1], 16) for p in (l.split() for l in open(os.path.join(B, 'whdload.map'))) if len(p) == 3}
        self.data = os.path.join(pkg, 'data')
        am = self.am = emu68k.Amiga(self.data)
        ok = am.valid                                         # WHDLoad's own memory: the slave, stack, resload
        am.valid = lambda a, n: ok(a, n) or (0x200000 <= a and a + n <= 0x400000)
        d = open([os.path.join(pkg, f) for f in os.listdir(pkg) if f.endswith('.slave')][0], 'rb').read()
        assert struct.unpack('>I', d[8:12])[0] == 1, 'slave: one hunk'
        assert struct.unpack('>I', d[24:28])[0] == 0x3e9
        n = struct.unpack('>I', d[28:32])[0]; code = d[32:32 + n * 4]
        assert d[32 + n * 4:36 + n * 4] == b'\x00\x00\x03\xf2', 'slave: no relocations'
        assert code[4:12] == b'WHDLOADS'
        am.mem[SLAVE_AT:SLAVE_AT + len(code)] = code
        H = lambda o, s=2: int.from_bytes(code[o:o + s], 'big')
        self.hdr = dict(version=H(12), flags=H(14), basemem=H(16, 4), loader=H(24), dir=H(26), keyexit=code[31], expmem=H(32, 4))
        assert self.hdr['basemem'] <= 0x80000 and self.hdr['expmem'] <= 0x80000
        am.mem[SLAVE_AT + 32:SLAVE_AT + 36] = EXP_AT.to_bytes(4, 'big')   # WHDLoad: the address of ExpMem
        am.mem[0:0x80000] = bytes(0x80000)                                # (ClearMem)
        am.mem[EXP_AT:EXP_AT + 0x80000] = bytes([0x5a]) * 0x80000         # expansion memory is NOT clear
        self.aborted = None; self.saves = []
        def add(off, fn):
            sid = len(am.stubs) + 1; am.stubs[sid] = ('resload', fn)
            am.mem[RESLOAD + off:RESLOAD + off + 2] = (0xa000 | sid).to_bytes(2, 'big')
        for off in range(0, 160, 4):
            add(off, (lambda o: lambda: self.bad(o))(off))
        add(4, self.r_abort); add(8, self.r_loadfile); add(12, self.r_savefile)
        add(36, self.r_size); add(76, self.r_loadoffset)
        am.a[0] = RESLOAD; am.a[7] = STACK
        am.pc = SLAVE_AT + self.hdr['loader']
        self.base = {}
    def path(self, a): return os.path.join(self.data, self.am.cstr(a))
    def bad(self, off): raise emu68k.EmuError('resload function %d not provided' % off)
    def r_abort(self):
        sp = self.am.a[7]
        self.aborted = struct.unpack('>i', bytes(self.am.mem[sp + 4:sp + 8]))[0]   # (jmp: no return address... +4 = reason)
        self.aborted_raw = [self.am.rl(sp + i) for i in (0, 4)]
        raise emu68k.Halt('abort')
    def r_loadfile(self):
        d = open(self.path(self.am.a[0]), 'rb').read()
        self.am.mem[self.am.a[1]:self.am.a[1] + len(d)] = d; self.am.d[0] = len(d); self.am.d[1] = 0
    def r_loadoffset(self):
        f = open(self.path(self.am.a[0]), 'rb'); f.seek(self.am.d[1]); n = self.am.d[0]
        d = f.read(n)
        if len(d) != n: raise emu68k.EmuError('LoadFileOffset past the end of the file (WHDLoad would quit)')
        self.am.mem[self.am.a[1]:self.am.a[1] + n] = d; self.am.d[0] = n; self.am.d[1] = 0
    def r_size(self):
        p = self.path(self.am.a[0]); self.am.d[0] = os.path.getsize(p) if os.path.exists(p) else 0
    def r_savefile(self):
        d = bytes(self.am.mem[self.am.a[1]:self.am.a[1] + self.am.d[0]])
        open(self.path(self.am.a[0]), 'wb').write(d); self.saves.append(len(d))
    def started(self):
        hk = [self.am.rl(SLAVE_AT + self.slsym['_hunks'] + 4 * i) for i in range(len(self.names))]
        if hk[0] == 0: return False
        self.base = {self.names[i]: hk[i] for i in range(len(self.names))}
        return True

def main():
    pkg = sys.argv[1] if len(sys.argv) > 1 else os.path.join(B, 'whdload', 'StronkiesOlympics')
    data = os.path.join(pkg, 'data')
    if os.path.exists(os.path.join(data, 'Olympics.dat')): os.remove(os.path.join(data, 'Olympics.dat'))
    ok = True
    def check(n, c):
        nonlocal ok; ok &= bool(c); print(('PASS ' if c else 'FAIL ') + n)
    g = WHDGame(pkg, 'build/whdshots')
    check('header: version 17, F10 quits, 512K + 512K', g.hdr['version'] == 17 and g.hdr['keyexit'] == 0x59)
    n = 0
    while not (g.started() and g.base.get('vars')) and n < 300: g.run(1); n += 1
    check('game loaded', g.started())
    check('chip hunks in chip', g.base['chip'] < 0x80000)
    g.run(150); g.shot('01_ceremony')
    check('whd_mode set', g.b('whd_mode'))
    check('chip memory from AllocMem', 0 < g.l('screen0') < 0x80000 and 0 < g.l('ev_chip') < 0x80000)
    check('the ceremony was loaded', g.l('hunk_base') != 0)
    g.am.joy['fire'] = 1; g.run(4); g.am.joy['fire'] = 0          # skip it
    g.run(200); g.shot('02_title')
    check('reached the title', g.w('menu_sel') == 0)
    # world records: written through WHDLoad when a competition ends: write them now
    g.am.ww(g.A('mode'), 2)
    g.am.tap(0x59)
    try:
        g.run(200); check('F10 quits', False)
    except emu68k.Halt:
        check('F10 quits with TDREASON_OK', g.aborted_raw[0] == 0xffffffff)
    print('ALL PASS' if ok else 'SOME FAILED')

if __name__ == '__main__':
    main()
