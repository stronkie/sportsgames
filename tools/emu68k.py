#!/usr/bin/env python3
"""emu68k.py - a small 68000 + Amiga 500 test bench for Stronkie's Slot Machine.

It loads an Amiga hunk executable into a stock A500 memory map (512K chip RAM,
512K trapdoor "slow" RAM at $C00000), fakes the few exec / dos / graphics
calls a game makes before it takes over the machine, and emulates the parts
of the chipset the game uses: copper, bitplanes (to PNG), Paula audio (to WAV),
joystick port 2, fire button and the keyboard via CIA-A.

It is strict on purpose: odd word accesses, reads or writes outside RAM and
unknown opcodes stop the run with the PC, so bugs show up here and not on a
real machine.  It is a test tool, not a full emulator: timing is approximate.
"""
import struct, sys, os, wave

CHIP_SIZE = 0x80000
SLOW_BASE, SLOW_SIZE = 0xC00000, 0x80000
ROM_BASE = 0xF80000          # fake library bases / exec structures live here
CYC_LINE = 454               # CPU cycles per PAL raster line
LINES = 313
CYC_FRAME = CYC_LINE * LINES
AUDIO_RATE = 22050
PAULA_CLOCK = 3546895

class EmuError(Exception):
    pass

class Halt(Exception):
    pass

M32 = 0xffffffff

def sx8(v): return v - 0x100 if v & 0x80 else v
def sx16(v): return v - 0x10000 if v & 0x8000 else v
def sx32(v): return v - 0x100000000 if v & 0x80000000 else v
MASK = {1: 0xff, 2: 0xffff, 4: M32}
MSB = {1: 0x80, 2: 0x8000, 4: 0x80000000}

class Amiga:
    def __init__(self, datadir='.'):
        self.mem = bytearray(0x1000000)
        self.d = [0] * 8
        self.a = [0] * 8
        self.pc = 0
        self.X = self.N = self.Z = self.V = self.C = 0
        self.cycles = 0
        self.frame = 0
        self.handlers = {}
        self.custom = [0] * 0x100     # word registers, index = offset/2
        self.dmacon = 0
        self.intena = 0
        self.datadir = datadir
        self.files = {}
        self.nextfh = 1
        self.joy = {'left': 0, 'right': 0, 'up': 0, 'down': 0, 'fire': 0}
        self.mouse = {'x': 0, 'y': 0, 'lb': 0, 'rb': 0}   # counters (mod 256) and buttons, port 1
        self.keyq = []               # raw keycodes (bit 7 = release) waiting to be sent
        self.sdr = 0; self.icr = 0; self.cra = 0; self.key_wait = 0
        self.chip_ptr = 0x4000
        self.slow_ptr = SLOW_BASE
        self.allocs = {}
        self.audio = [dict(on=False, pos=0.0, ptr=0, left=0, cur=0) for _ in range(4)]
        self.audio_out = None
        self.trace = []
        self.exited = False
        self.taken_over = False
        self.writes_log = []
        self.msgs = []
        self.setup_os()

    # ------------------------------------------------------------- memory
    def valid(self, a, n):
        if a + n <= CHIP_SIZE and a >= 0: return True
        if SLOW_BASE <= a and a + n <= SLOW_BASE + SLOW_SIZE: return True
        if ROM_BASE <= a and a + n <= 0x1000000: return True
        return False

    def bad(self, what, a):
        raise EmuError('%s at $%06x (pc=$%06x)' % (what, a, self.lastpc))

    def rb(self, a):
        a &= 0xffffff
        if 0xbf0000 <= a < 0xc00000: return self.cia_read(a)
        if 0xdff000 <= a < 0xe00000:
            w = self.custom_read(a & 0x1fe)
            return (w >> 8) if not a & 1 else w & 255
        if not self.valid(a, 1): self.bad('byte read', a)
        return self.mem[a]

    def rw(self, a):
        a &= 0xffffff
        if a & 1: self.bad('odd word read', a)
        if 0xdff000 <= a < 0xe00000: return self.custom_read(a & 0x1fe)
        if not self.valid(a, 2): self.bad('word read', a)
        m = self.mem
        return (m[a] << 8) | m[a + 1]

    def rl(self, a):
        a &= 0xffffff
        if a & 1: self.bad('odd long read', a)
        if 0xdff000 <= a < 0xe00000:
            return (self.custom_read(a & 0x1fe) << 16) | self.custom_read((a + 2) & 0x1fe)
        if not self.valid(a, 4): self.bad('long read', a)
        m = self.mem
        return (m[a] << 24) | (m[a + 1] << 16) | (m[a + 2] << 8) | m[a + 3]

    def wb(self, a, v):
        a &= 0xffffff
        if 0xbf0000 <= a < 0xc00000: return self.cia_write(a, v & 255)
        if 0xdff000 <= a < 0xe00000: self.bad('byte write to custom chips', a)
        if not self.valid(a, 1) or (a >= ROM_BASE and not (self.gfxbase <= a < self.gfxbase + 100 or self.proc <= a < self.proc + 256)): self.bad('byte write', a)
        self.mem[a] = v & 255

    def ww(self, a, v):
        a &= 0xffffff
        if a & 1: self.bad('odd word write', a)
        if 0xdff000 <= a < 0xe00000: return self.custom_write(a & 0x1fe, v & 0xffff)
        if not self.valid(a, 2) or (a >= ROM_BASE and not (self.gfxbase <= a < self.gfxbase + 100 or self.proc <= a < self.proc + 256)): self.bad('word write', a)
        self.mem[a] = (v >> 8) & 255; self.mem[a + 1] = v & 255

    def wl(self, a, v):
        a &= 0xffffff
        if a & 1: self.bad('odd long write', a)
        if 0xdff000 <= a < 0xe00000:
            self.custom_write(a & 0x1fe, (v >> 16) & 0xffff)
            self.custom_write((a + 2) & 0x1fe, v & 0xffff); return
        if not self.valid(a, 4) or (a >= ROM_BASE and not (self.gfxbase <= a < self.gfxbase + 100 or self.proc <= a < self.proc + 256)): self.bad('long write', a)
        self.mem[a:a + 4] = (v & M32).to_bytes(4, 'big')

    def rsz(self, a, s):
        return self.rb(a) if s == 1 else self.rw(a) if s == 2 else self.rl(a)
    def wsz(self, a, s, v):
        if s == 1: self.wb(a, v)
        elif s == 2: self.ww(a, v)
        else: self.wl(a, v)

    def fetch(self):
        pc = self.pc
        if pc & 1: self.bad('odd pc', pc)
        if not self.valid(pc, 2): self.bad('pc outside memory', pc)
        m = self.mem
        self.pc = pc + 2
        return (m[pc] << 8) | m[pc + 1]

    def fetchl(self):
        return (self.fetch() << 16) | self.fetch()

    # ------------------------------------------------------------- chipset
    def beam(self):
        c = self.cycles % CYC_FRAME
        return c // CYC_LINE, (c % CYC_LINE) // 2

    def custom_read(self, off):
        if off == 0x004:   # VPOSR
            line, h = self.beam()
            return (0x8000 if self.frame & 1 else 0) | (line >> 8)
        if off == 0x006:   # VHPOSR (polling loops: let time pass faster, but < 1 line)
            self.cycles += 200
            line, h = self.beam()
            return ((line & 255) << 8) | (h & 255)
        if off == 0x002: return self.dmacon      # blitter is never busy here (blits run at once)
        if off == 0x01c: return self.intena
        if off == 0x01e: return 0
        if off == 0x00c:   # JOY1DAT
            j = self.joy
            v = 0
            if j['right']: v |= 0x0002
            if j['left']: v |= 0x0200
            b1 = (v >> 1) & 1; b9 = (v >> 9) & 1
            v |= b1 ^ (1 if j['down'] else 0)          # bit 0 = X1 xor down
            v |= (b9 ^ (1 if j['up'] else 0)) << 8      # bit 8 = Y1 xor up
            return v
        if off == 0x00a: return ((self.mouse['y'] & 255) << 8) | (self.mouse['x'] & 255)
        if off == 0x016: return 0xff00 & ~(0x0400 if self.mouse['rb'] else 0)   # POTGOR: right mouse button = bit 10
        if off == 0x010: return 0
        return 0

    def custom_write(self, off, v):
        self.custom[off >> 1] = v
        if off == 0x096:
            old = self.dmacon
            if v & 0x8000: self.dmacon |= v & 0x7fff
            else: self.dmacon &= ~v & 0x7fff
            for ch in range(4):
                was = (old & 0x200) and (old & (1 << ch))
                now = (self.dmacon & 0x200) and (self.dmacon & (1 << ch))
                if now and not was: self.audio_start(ch)
                if was and not now: self.audio[ch]['on'] = False
        elif off == 0x09a:
            if v & 0x8000: self.intena |= v & 0x7fff
            else: self.intena &= ~v & 0x7fff
        elif off == 0x088:
            pass
        elif off == 0x058:
            self.blit(v)
        elif 0x0a0 <= off < 0x0e0:
            ch = (off - 0xa0) >> 4; r = off & 15
            if r == 0x0a and not self.dmacon & (1 << ch):
                pass

    def blit(self, size):
        """Blitter: area mode, ascending, any minterm, A/B shifts, first/last word masks.
        Runs at once.  Checks that every access is in chip RAM, as on the real thing."""
        if not self.dmacon & 0x40 or not self.dmacon & 0x200:
            raise EmuError('blit started with blitter DMA off (pc=$%06x)' % self.lastpc)
        con0 = self.creg(0x40); con1 = self.creg(0x42)
        if con1 & 1: raise EmuError('blitter line mode not supported (pc=$%06x)' % self.lastpc)
        if con1 & 2: raise EmuError('blitter descending mode not supported (pc=$%06x)' % self.lastpc)
        if con1 & 0x18: raise EmuError('blitter fill mode not supported (pc=$%06x)' % self.lastpc)
        h = (size >> 6) & 0x3ff or 1024; w = size & 0x3f or 64
        ash = con0 >> 12; bsh = con1 >> 12; lf = con0 & 0xff
        use = (con0 >> 8) & 15     # A B C D
        fwm = self.creg(0x44); lwm = self.creg(0x46)
        ptr = {'c': self.cregl(0x48) & 0x7fffe, 'b': self.cregl(0x4c) & 0x7fffe,
               'a': self.cregl(0x50) & 0x7fffe, 'd': self.cregl(0x54) & 0x7fffe}
        mod = {'c': sx16(self.creg(0x60)) & ~1, 'b': sx16(self.creg(0x62)) & ~1,
               'a': sx16(self.creg(0x64)) & ~1, 'd': sx16(self.creg(0x66)) & ~1}
        adat = self.creg(0x74); bdat = self.creg(0x72); cdat = self.creg(0x70)
        m = self.mem
        def rd(k):
            a = ptr[k]
            if a + 2 > CHIP_SIZE: raise EmuError('blitter reads outside chip RAM: $%06x (pc=$%06x)' % (a, self.lastpc))
            ptr[k] = a + 2
            return (m[a] << 8) | m[a + 1]
        for y in range(h):
            aprev = 0; bprev = 0
            for x in range(w):
                a = rd('a') if use & 8 else adat
                if x == 0: a &= fwm
                if x == w - 1: a &= lwm
                ash_v = ((aprev << 16) | a) >> ash & 0xffff; aprev = a
                b = rd('b') if use & 4 else bdat
                bsh_v = ((bprev << 16) | b) >> bsh & 0xffff; bprev = b
                c = rd('c') if use & 2 else cdat
                A, B, C = ash_v, bsh_v, c
                d = 0
                for k in range(8):
                    if lf >> k & 1:
                        t = (A if k & 4 else ~A) & (B if k & 2 else ~B) & (C if k & 1 else ~C)
                        d |= t
                d &= 0xffff
                if use & 1:
                    da = ptr['d']
                    if da + 2 > CHIP_SIZE: raise EmuError('blitter writes outside chip RAM: $%06x (pc=$%06x)' % (da, self.lastpc))
                    m[da] = d >> 8; m[da + 1] = d & 255
                    ptr['d'] = da + 2
            for k in 'abcd':
                if (k == 'a' and use & 8) or (k == 'b' and use & 4) or (k == 'c' and use & 2) or (k == 'd' and use & 1):
                    ptr[k] += mod[k]
        self.blits = getattr(self, 'blits', 0) + 1
        self.cycles += w * h * 2      # the CPU loses some bus time

    def creg(self, off): return self.custom[off >> 1]
    def cregl(self, off): return (self.custom[off >> 1] << 16) | self.custom[(off >> 1) + 1]

    def audio_start(self, ch):
        a = self.audio[ch]
        base = 0xa0 + ch * 16
        a['on'] = True
        a['ptr'] = self.cregl(base) & 0x7fffe
        a['left'] = (self.creg(base + 4) or 0x10000) * 2
        a['pos'] = 0.0

    def mix_frame(self):
        """Render one frame of Paula output (stereo)."""
        n = AUDIO_RATE // 50
        out = [[0] * n, [0] * n]
        for ch in range(4):
            a = self.audio[ch]
            if not a['on']: continue
            base = 0xa0 + ch * 16
            per = self.creg(base + 6) or 1
            vol = min(self.creg(base + 8), 64)
            step = PAULA_CLOCK / per / AUDIO_RATE
            side = out[0] if ch in (0, 3) else out[1]
            pos = a['pos']; ptr = a['ptr']; left = a['left']
            mem = self.mem
            for i in range(n):
                s = mem[ptr + int(pos)]
                if s > 127: s -= 256
                side[i] += s * vol
                pos += step
                while pos >= left:
                    pos -= left
                    ptr = self.cregl(base) & 0x7fffe
                    left = (self.creg(base + 4) or 0x10000) * 2
            a['pos'] = pos; a['ptr'] = ptr; a['left'] = left
        if self.audio_out is not None:
            buf = bytearray()
            for i in range(n):
                l = max(-32768, min(32767, out[0][i] * 2)); r = max(-32768, min(32767, out[1][i] * 2))
                buf += struct.pack('<hh', l, r)
            self.audio_out.append(bytes(buf))

    def cia_read(self, a):
        if a & 1 == 0: return 0xff   # CIA-B (even addresses) not used
        r = (a >> 8) & 15
        if 0xbfe000 <= a < 0xbff000:
            if r == 0:   # PRA
                v = 0xff
                if self.joy['fire']: v &= ~0x80
                if self.mouse['lb']: v &= ~0x40
                return v
            if r == 0xc: return self.sdr
            if r == 0xd:
                v = self.icr; self.icr = 0
                return (0x80 | v) if v else 0
            if r == 0xe: return self.cra
        return 0xff

    def cia_write(self, a, v):
        r = (a >> 8) & 15
        if 0xbfe000 <= a < 0xbff000:
            if r == 0xe:
                if (self.cra & 0x40) and not (v & 0x40):
                    self.key_wait = 0   # handshake done
                self.cra = v
            if r == 0xd: pass

    def key_tick(self):
        if self.keyq and self.key_wait == 0 and not (self.icr & 8):
            code = self.keyq.pop(0)
            raw = ((code << 1) | (code >> 7)) & 255
            self.sdr = (~raw) & 255
            self.icr |= 8
            self.key_wait = 1

    def render(self):
        """Run the copper list over a frame and return a 320x256 PIL image."""
        from PIL import Image
        img = Image.new('RGB', (320, 256))
        px = img.load()
        regs = list(self.custom)
        cop = self.cregl(0x80) & 0x7fffe
        bpl = [0] * 6
        cp = cop; waiting = None; done = False; pal0 = None
        def amiga_rgb(c):
            return (((c >> 8) & 15) * 17, ((c >> 4) & 15) * 17, (c & 15) * 17)
        copper_on = (self.dmacon & 0x280) == 0x280
        for line in range(LINES):
            # copper: execute until a wait for a later line
            steps = 0
            while copper_on and not done and steps < 1000:
                steps += 1
                w1 = (self.mem[cp] << 8) | self.mem[cp + 1]
                w2 = (self.mem[cp + 2] << 8) | self.mem[cp + 3]
                cp += 4
                if w1 & 1 == 0:
                    off = w1 & 0x1fe
                    regs[off >> 1] = w2
                    if 0xe0 <= off < 0xf8:
                        i = (off - 0xe0) >> 2
                        if off & 2: bpl[i] = (bpl[i] & 0xffff0000) | w2
                        else: bpl[i] = (bpl[i] & 0xffff) | (w2 << 16)
                elif w1 == 0xffff and w2 == 0xfffe:
                    done = True
                else:
                    vp = w1 >> 8
                    if (line & 0xff) < vp:
                        waiting = vp
                        cp -= 4
                        break
                    waiting = None
            y = line - 0x2c
            if 0 <= y < 256:
                nplanes = (regs[0x100 >> 1] >> 12) & 7
                pal = [amiga_rgb(regs[(0x180 >> 1) + i]) for i in range(32)]
                mod1 = sx16(regs[0x108 >> 1]); mod2 = sx16(regs[0x10a >> 1])
                rows = []
                for p in range(nplanes):
                    a0 = bpl[p] & 0xfffffe
                    rows.append(self.mem[a0:a0 + 40])
                for x in range(320):
                    c = 0
                    byte = x >> 3; bit = 7 - (x & 7)
                    for p in range(nplanes):
                        if (rows[p][byte] >> bit) & 1: c |= 1 << p
                    px[x, y] = pal[c]
                for p in range(nplanes):
                    bpl[p] += 40 + (mod1 if p % 2 == 0 else mod2)
                if y == 0: pal0 = pal
        # hardware sprites (one use per channel, 3 colours + transparent), in front
        if self.dmacon & 0x220 == 0x220:
            pal = pal0
            for n in range(7, -1, -1):
                sp = ((regs[(0x120 >> 1) + n * 2] << 16) | regs[(0x120 >> 1) + n * 2 + 1]) & 0x7fffe
                pos = self.rw(sp); ctl = self.rw(sp + 2)
                vs = (pos >> 8) | ((ctl & 4) << 6); ve = (ctl >> 8) | ((ctl & 2) << 7)
                hs = ((pos & 0xff) << 1) | (ctl & 1)
                if ve <= vs: continue
                a = sp + 4
                for v in range(vs, ve):
                    d0 = self.rw(a); d1 = self.rw(a + 2); a += 4
                    yy = v - 0x2c
                    if not 0 <= yy < 256: continue
                    for i in range(16):
                        c = ((d0 >> (15 - i)) & 1) | (((d1 >> (15 - i)) & 1) << 1)
                        xx = hs - 0x81 + i
                        if c and 0 <= xx < 320:
                            px[xx, yy] = pal[16 + (n >> 1) * 4 + c]
        return img

    # ------------------------------------------------------------- OS stubs
    def setup_os(self):
        self.stubs = {}
        self.romp = ROM_BASE
        def lib(name, funcs, size=600):
            nvec = 200
            base = self.romp + nvec * 6
            self.romp = base + size
            for lvo, fn in funcs.items():
                sid = len(self.stubs) + 1
                self.stubs[sid] = (name, fn)
                addr = base - lvo
                self.mem[addr:addr + 2] = (0xa000 | sid).to_bytes(2, 'big')
            return base
        self.execbase = lib('exec', {
            120: self.s_nop, 126: self.s_nop, 132: self.s_nop, 138: self.s_nop,
            198: self.s_allocmem, 210: self.s_freemem, 294: self.s_findtask,
            372: self.s_getmsg, 378: self.s_nop, 384: self.s_waitport,
            408: self.s_openlib, 414: self.s_nop, 552: self.s_openlib,
            456: self.s_nop, 462: self.s_nop, 534: self.s_nop})
        self.gfxbase = lib('graphics', {222: self.s_loadview, 270: self.s_waittof, 228: self.s_nop,
                                        456: self.s_nop, 462: self.s_nop,
                                        360: self.s_initview, 204: self.s_initvport, 390: self.s_initbitmap,
                                        570: self.s_getcolormap, 192: self.s_loadrgb4, 216: self.s_nop,
                                        210: self.s_mrgcop, 540: self.s_nop, 564: self.s_nop, 576: self.s_nop})
        self.dosbase = lib('dos', {30: self.s_open, 36: self.s_close, 42: self.s_read,
                                   48: self.s_write, 198: self.s_delay, 72: self.s_nop,
                                   66: self.s_seek, 126: self.s_currentdir})
        self.mem[4:8] = self.execbase.to_bytes(4, 'big')
        # fake graphics base: gb_ActiView (34) = 0, gb_copinit (38) = a tiny system copper list
        self.syscop = self.romp; self.romp += 16
        self.mem[self.syscop:self.syscop + 8] = bytes([0x01, 0x80, 0x05, 0x55, 0xff, 0xff, 0xff, 0xfe])
        self.mem[self.gfxbase + 34:self.gfxbase + 38] = (0x12340).to_bytes(4, 'big')
        self.mem[self.gfxbase + 38:self.gfxbase + 42] = self.syscop.to_bytes(4, 'big')
        # process structure
        self.proc = self.romp; self.romp += 256
        self.cli = True
        self.wbmsg = self.romp; self.romp += 64

    def set_wb_start(self):
        self.cli = False

    def s_nop(self): pass

    def s_findtask(self):
        p = self.proc
        self.mem[p + 172:p + 176] = ((1 if self.cli else 0)).to_bytes(4, 'big')
        self.d[0] = p

    def s_waitport(self):
        self.d[0] = self.wbmsg
    def s_getmsg(self):
        self.d[0] = self.wbmsg if not self.cli else 0

    def s_openlib(self):
        name = self.cstr(self.a[1])
        self.d[0] = {'graphics.library': self.gfxbase, 'dos.library': self.dosbase}.get(name, 0)
        self.msgs.append('OpenLibrary %s -> %x' % (name, self.d[0]))

    def s_allocmem(self):
        size = self.d[0]; flags = self.d[1]
        size = (size + 7) & ~7
        if flags & 2:
            p = self.chip_ptr; self.chip_ptr += size
            if self.chip_ptr > CHIP_SIZE: self.d[0] = 0; return
        else:
            p = self.slow_ptr; self.slow_ptr += size
            if self.slow_ptr > SLOW_BASE + SLOW_SIZE:
                p = self.chip_ptr; self.chip_ptr += size
        self.mem[p:p + size] = bytes(size)
        self.allocs[p] = size
        self.d[0] = p
        self.msgs.append('AllocMem %d flags %x -> %x' % (size, flags, p))

    def s_freemem(self):
        if self.a[1] not in self.allocs: raise EmuError('FreeMem of unknown block %x' % self.a[1])
        del self.allocs[self.a[1]]

    def s_loadview(self):
        v = self.a[1]
        if v in (0, 0x12340):
            cop = self.syscop
        else:
            cop = int.from_bytes(self.mem[v + 4:v + 8], 'big')
            self.dmacon |= 0x380
        self.custom[0x80 >> 1] = cop >> 16; self.custom[0x82 >> 1] = cop & 0xffff
        self.msgs.append('LoadView %x' % v)

    def s_initview(self):
        self.mem[self.a[1]:self.a[1] + 18] = bytes(18)
    def s_initvport(self):
        self.mem[self.a[0]:self.a[0] + 40] = bytes(40)
    def s_initbitmap(self):
        b = self.a[0]
        self.mem[b:b + 40] = bytes(40)
        self.mem[b:b + 2] = ((self.d[1] + 15) // 16 * 2).to_bytes(2, 'big')
        self.mem[b + 2:b + 4] = self.d[2].to_bytes(2, 'big')
        self.mem[b + 5] = self.d[0]
    def s_getcolormap(self):
        self.vpcolours = [0] * 32
        self.d[0] = 0x7f000
    def s_loadrgb4(self):
        for i in range(self.d[0] & 0xffff):
            self.vpcolours[i] = int.from_bytes(self.mem[self.a[1] + 2 * i:self.a[1] + 2 * i + 2], 'big')
    def s_mrgcop(self):
        v = self.a[1]
        vp = int.from_bytes(self.mem[v:v + 4], 'big')
        ri = int.from_bytes(self.mem[vp + 36:vp + 40], 'big')
        bm = int.from_bytes(self.mem[ri + 4:ri + 8], 'big')
        depth = self.mem[bm + 5]
        cl = [(0x100, (depth << 12) | 0x200), (0x108, 0), (0x10a, 0), (0x102, 0)]
        cl += [(0x180 + 2 * i, c) for i, c in enumerate(self.vpcolours)]
        for i in range(depth):
            pa = int.from_bytes(self.mem[bm + 8 + 4 * i:bm + 12 + 4 * i], 'big')
            cl += [(0xe0 + 4 * i, pa >> 16), (0xe2 + 4 * i, pa & 0xffff)]
        cop = self.chip_ptr; self.chip_ptr += (4 * len(cl) + 15) & ~7
        for i, (r, val) in enumerate(cl):
            self.mem[cop + 4 * i:cop + 4 * i + 4] = r.to_bytes(2, 'big') + val.to_bytes(2, 'big')
        self.mem[cop + 4 * len(cl):cop + 4 * len(cl) + 4] = b'\xff\xff\xff\xfe'
        self.mem[v + 4:v + 8] = cop.to_bytes(4, 'big')

    def s_seek(self):
        f = self.files[self.d[1]]
        old = f.tell()
        off = sx32(self.d[2]); mode = sx32(self.d[3])
        f.seek(off, {-1: 0, 0: 1, 1: 2}[mode])
        self.d[0] = old
    def s_currentdir(self):
        self.d[0] = 0
    def s_waittof(self):
        self.cycles += CYC_FRAME // 2

    def s_delay(self):
        self.cycles += self.d[1] * CYC_FRAME

    def cstr(self, a):
        s = b''
        while self.mem[a]: s += bytes([self.mem[a]]); a += 1
        return s.decode('latin-1')

    def s_open(self):
        name = self.cstr(self.d[1]); mode = self.d[2]
        path = os.path.join(self.datadir, name.split(':')[-1])
        self.msgs.append('Open %s %d' % (name, mode))
        try:
            if mode == 1006: f = open(path, 'w+b')
            else: f = open(path, 'r+b')
        except OSError:
            self.d[0] = 0; return
        fh = self.nextfh; self.nextfh += 1
        self.files[fh] = f
        self.d[0] = fh

    def s_close(self):
        f = self.files.pop(self.d[1], None)
        if f: f.close()
        self.d[0] = -1 & M32

    def s_read(self):
        f = self.files[self.d[1]]
        data = f.read(self.d[3])
        self.mem[self.d[2]:self.d[2] + len(data)] = data
        self.d[0] = len(data)
        rate = getattr(self, 'disk_rate', 0)     # bytes per frame, 0 = instant
        if rate: self.cycles += len(data) * CYC_FRAME // rate

    def s_write(self):
        f = self.files[self.d[1]]
        data = bytes(self.mem[self.d[2]:self.d[2] + self.d[3]])
        f.write(data)
        self.d[0] = len(data)

    # ------------------------------------------------------------- loader
    def load_hunks(self, path):
        data = open(path, 'rb').read()
        p = 0
        def L():
            nonlocal p
            v = struct.unpack('>I', data[p:p + 4])[0]; p += 4; return v
        if L() != 0x3f3: raise EmuError('not a hunk file')
        while L(): raise EmuError('resident libs not supported')
        n = L(); first = L(); last = L()
        sizes = [L() for _ in range(n)]
        bases = []
        for s in sizes:
            nbytes = (s & 0x3fffffff) * 4
            self.d[0] = nbytes + 8; self.d[1] = 2 if s & 0x40000000 else 0
            self.s_allocmem()
            bases.append(self.d[0] + 8)
            self.msgs.append('hunk %d: %d bytes at $%06x%s' % (len(bases) - 1, nbytes, self.d[0] + 8, ' (chip)' if s & 0x40000000 else ''))
        h = 0
        while p < len(data):
            t = L() & 0x3fffffff
            if t in (0x3e9, 0x3ea):
                nl = L(); b = bases[h]
                self.mem[b:b + nl * 4] = data[p:p + nl * 4]; p += nl * 4
            elif t == 0x3eb:
                L()
            elif t == 0x3ec:
                while True:
                    cnt = L()
                    if cnt == 0: break
                    tgt = L()
                    for _ in range(cnt):
                        off = L(); a = bases[h] + off
                        v = int.from_bytes(self.mem[a:a + 4], 'big') + bases[tgt]
                        self.mem[a:a + 4] = (v & M32).to_bytes(4, 'big')
            elif t == 0x3f2:
                h += 1
            elif t == 0x3f0:   # symbols
                while True:
                    nl = L()
                    if nl == 0: break
                    p += nl * 4 + 4
            else:
                raise EmuError('unknown hunk %x' % t)
        self.bases = bases
        # stack and return address
        sp = 0x3ff0
        self.exit_addr = self.romp; self.romp += 4
        self.mem[self.exit_addr:self.exit_addr + 2] = (0xa000 | 0xfff).to_bytes(2, 'big')
        sp -= 4; self.mem[sp:sp + 4] = self.exit_addr.to_bytes(4, 'big')
        self.a[7] = sp
        self.pc = bases[0]
        self.d[0] = 1; self.a[0] = self.romp; self.mem[self.romp] = 10; self.romp += 4
        return bases

    # ------------------------------------------------------------- CPU core
    def ccr(self):
        return (self.X << 4) | (self.N << 3) | (self.Z << 2) | (self.V << 1) | self.C

    def set_ccr(self, v):
        self.X = (v >> 4) & 1; self.N = (v >> 3) & 1; self.Z = (v >> 2) & 1
        self.V = (v >> 1) & 1; self.C = v & 1

    def cond(self, c):
        N, Z, V, C = self.N, self.Z, self.V, self.C
        if c == 0: return True
        if c == 1: return False
        if c == 2: return not C and not Z
        if c == 3: return C or Z
        if c == 4: return not C
        if c == 5: return bool(C)
        if c == 6: return not Z
        if c == 7: return bool(Z)
        if c == 8: return not V
        if c == 9: return bool(V)
        if c == 10: return not N
        if c == 11: return bool(N)
        if c == 12: return N == V
        if c == 13: return N != V
        if c == 14: return not Z and N == V
        return Z or N != V

    def ea_addr(self, mode, reg, size):
        """Address of a memory operand (modes 2-7, not immediate)."""
        if mode == 2: return self.a[reg]
        if mode == 3:
            a = self.a[reg]
            self.a[reg] = (a + (2 if size == 1 and reg == 7 else size)) & M32
            return a
        if mode == 4:
            a = (self.a[reg] - (2 if size == 1 and reg == 7 else size)) & M32
            self.a[reg] = a
            return a
        if mode == 5: return (self.a[reg] + sx16(self.fetch())) & M32
        if mode == 6: return self.index(self.a[reg])
        if mode == 7:
            if reg == 0: return sx16(self.fetch()) & M32
            if reg == 1: return self.fetchl()
            if reg == 2:
                base = self.pc; return (base + sx16(self.fetch())) & M32
            if reg == 3: return self.index(self.pc)
        raise EmuError('bad addressing mode %d/%d at $%06x' % (mode, reg, self.lastpc))

    def index(self, base):
        ext = self.fetch()
        r = (ext >> 12) & 15
        x = self.d[r] if r < 8 else self.a[r - 8]
        if not ext & 0x800: x = sx16(x & 0xffff)
        if ext & 0x700: raise EmuError('full extension word not on 68000 ($%06x)' % self.lastpc)
        return (base + x + sx8(ext & 255)) & M32

    def read_ea(self, mode, reg, size):
        """Returns (value, location) where location is used by write_loc."""
        if mode == 0: return self.d[reg] & MASK[size], ('d', reg)
        if mode == 1: return self.a[reg] & MASK[size], ('a', reg)
        if mode == 7 and reg == 4:
            if size == 4: return self.fetchl(), None
            w = self.fetch()
            return (w & 255 if size == 1 else w), None
        a = self.ea_addr(mode, reg, size)
        return self.rsz(a, size), ('m', a)

    def write_loc(self, loc, size, v):
        k, x = loc
        if k == 'd':
            m = MASK[size]
            self.d[x] = (self.d[x] & ~m & M32) | (v & m)
        elif k == 'a':
            self.a[x] = v & M32
        else:
            self.wsz(x, size, v)

    def write_ea(self, mode, reg, size, v):
        if mode == 0:
            m = MASK[size]; self.d[reg] = (self.d[reg] & ~m & M32) | (v & m)
        elif mode == 1:
            self.a[reg] = v & M32
        else:
            if mode == 7 and reg >= 2: raise EmuError('write to pc-relative/immediate at $%06x' % self.lastpc)
            self.wsz(self.ea_addr(mode, reg, size), size, v)

    def flags_logic(self, v, size):
        v &= MASK[size]
        self.N = 1 if v & MSB[size] else 0
        self.Z = 1 if v == 0 else 0
        self.V = 0; self.C = 0

    def do_add(self, s, d, size, x=0):
        m = MASK[size]; r = (s + d + x) & m; msb = MSB[size]
        self.C = self.X = 1 if s + d + x > m else 0
        self.V = 1 if (~(s ^ d) & (r ^ d)) & msb else 0
        self.N = 1 if r & msb else 0
        self.Z = 1 if r == 0 else 0
        return r

    def do_sub(self, s, d, size, setx=True):
        m = MASK[size]; r = (d - s) & m; msb = MSB[size]
        c = 1 if s > d else 0
        self.C = c
        if setx: self.X = c
        self.V = 1 if ((s ^ d) & (r ^ d)) & msb else 0
        self.N = 1 if r & msb else 0
        self.Z = 1 if r == 0 else 0
        return r

    def step(self):
        self.lastpc = self.pc
        op = self.fetch()
        h = self.handlers.get(op)
        if h is None:
            h = self.decode(op)
            self.handlers[op] = h
        h(op)

    def decode(self, op):
        hi = op >> 12
        if hi == 0: return self.op_0
        if hi in (1, 2, 3): return self.op_move
        if hi == 4: return self.op_4
        if hi == 5: return self.op_5
        if hi == 6: return self.op_bcc
        if hi == 7: return self.op_moveq
        if hi in (8, 9, 0xb, 0xc, 0xd): return self.op_arith
        if hi == 0xa: return self.op_linea
        if hi == 0xe: return self.op_shift
        return self.op_illegal

    def op_illegal(self, op):
        raise EmuError('illegal opcode $%04x at $%06x' % (op, self.lastpc))

    def op_linea(self, op):
        sid = op & 0xfff
        if sid == 0xfff:
            self.exited = True
            raise Halt('program returned d0=%d' % sx32(self.d[0]))
        name, fn = self.stubs[sid]
        fn()
        # stubs are reached by JSR: return to caller
        self.pc = self.rl(self.a[7]); self.a[7] = (self.a[7] + 4) & M32
        self.cycles += 100

    def op_moveq(self, op):
        if op & 0x100: self.op_illegal(op)
        v = sx8(op & 255) & M32
        self.d[(op >> 9) & 7] = v
        self.flags_logic(v, 4)
        self.cycles += 4

    def op_move(self, op):
        size = {1: 1, 3: 2, 2: 4}[op >> 12]
        sm = (op >> 3) & 7; sr = op & 7
        dm = (op >> 6) & 7; dr = (op >> 9) & 7
        v, _ = self.read_ea(sm, sr, size)
        if dm == 1:
            if size == 1: self.op_illegal(op)
            self.a[dr] = (sx16(v) & M32) if size == 2 else v
        else:
            self.write_ea(dm, dr, size, v)
            self.flags_logic(v, size)
        self.cycles += 8 if size < 4 else 12

    def op_bcc(self, op):
        c = (op >> 8) & 15
        d = op & 255
        base = self.pc
        if d == 0:
            d = sx16(self.fetch())
        else:
            d = sx8(d)
        self.cycles += 10
        if c == 1:   # BSR
            self.a[7] = (self.a[7] - 4) & M32
            self.wl(self.a[7], self.pc)
            self.pc = (base + d) & M32
            return
        if c == 0 or self.cond(c):
            self.pc = (base + d) & M32

    def op_5(self, op):
        size_code = (op >> 6) & 3
        mode = (op >> 3) & 7; reg = op & 7
        if size_code == 3:
            c = (op >> 8) & 15
            if mode == 1:   # DBcc
                base = self.pc
                d = sx16(self.fetch())
                self.cycles += 10
                if not self.cond(c):
                    v = (self.d[reg] - 1) & 0xffff
                    self.d[reg] = (self.d[reg] & 0xffff0000) | v
                    if v != 0xffff:
                        self.pc = (base + d) & M32
                return
            # Scc
            self.write_ea(mode, reg, 1, 0xff if self.cond(c) else 0)
            self.cycles += 6
            return
        size = (1, 2, 4)[size_code]
        q = (op >> 9) & 7 or 8
        if mode == 1:
            if op & 0x100: self.a[reg] = (self.a[reg] - q) & M32
            else: self.a[reg] = (self.a[reg] + q) & M32
            self.cycles += 8
            return
        v, loc = self.read_ea(mode, reg, size)
        r = self.do_sub(q, v, size) if op & 0x100 else self.do_add(q, v, size)
        self.write_loc(loc, size, r)
        self.cycles += 8

    def op_0(self, op):
        mode = (op >> 3) & 7; reg = op & 7
        if op & 0x100 or (op & 0xf00) == 0x800:
            # bit operations
            if op & 0x100:
                if mode == 1: raise EmuError('movep not supported at $%06x' % self.lastpc)
                bit = self.d[(op >> 9) & 7]
            else:
                bit = self.fetch() & 255
            tt = (op >> 6) & 3
            if mode == 0:
                bit &= 31
                v = self.d[reg]
                self.Z = 0 if (v >> bit) & 1 else 1
                if tt == 1: v ^= 1 << bit
                elif tt == 2: v &= ~(1 << bit)
                elif tt == 3: v |= 1 << bit
                self.d[reg] = v & M32
            else:
                bit &= 7
                if mode == 7 and reg == 4:
                    v = self.fetch() & 255; loc = None
                else:
                    a = self.ea_addr(mode, reg, 1); v = self.rb(a); loc = a
                self.Z = 0 if (v >> bit) & 1 else 1
                if tt:
                    if tt == 1: v ^= 1 << bit
                    elif tt == 2: v &= ~(1 << bit)
                    else: v |= 1 << bit
                    self.wb(loc, v)
            self.cycles += 10
            return
        kind = (op >> 9) & 7   # 0 ori 1 andi 2 subi 3 addi 5 eori 6 cmpi
        sc = (op >> 6) & 3
        if sc == 3: self.op_illegal(op)
        size = (1, 2, 4)[sc]
        if mode == 7 and reg == 4:   # to CCR / SR
            imm = self.fetch()
            v = self.ccr()
            if kind == 0: v |= imm
            elif kind == 1: v &= imm
            elif kind == 5: v ^= imm
            self.set_ccr(v & 0x1f)
            return
        imm = self.fetchl() if size == 4 else (self.fetch() & MASK[size])
        v, loc = self.read_ea(mode, reg, size)
        if kind == 0: r = v | imm; self.flags_logic(r, size)
        elif kind == 1: r = v & imm; self.flags_logic(r, size)
        elif kind == 5: r = v ^ imm; self.flags_logic(r, size)
        elif kind == 2: r = self.do_sub(imm, v, size)
        elif kind == 3: r = self.do_add(imm, v, size)
        elif kind == 6:
            self.do_sub(imm, v, size, setx=False); self.cycles += 8; return
        else: self.op_illegal(op)
        self.write_loc(loc, size, r)
        self.cycles += 12

    def op_4(self, op):
        mode = (op >> 3) & 7; reg = op & 7
        if op == 0x4e75:
            self.pc = self.rl(self.a[7]); self.a[7] = (self.a[7] + 4) & M32; self.cycles += 16; return
        if op == 0x4e71: self.cycles += 4; return
        if (op & 0xffc0) == 0x4e80 or (op & 0xffc0) == 0x4ec0:
            a = self.ea_addr(mode, reg, 4)
            if op & 0x40 == 0:
                self.a[7] = (self.a[7] - 4) & M32
                self.wl(self.a[7], self.pc)
            self.pc = a; self.cycles += 16; return
        if (op & 0xf1c0) == 0x41c0:
            self.a[(op >> 9) & 7] = self.ea_addr(mode, reg, 4); self.cycles += 4; return
        if (op & 0xfff8) == 0x4840:
            v = self.d[reg]; v = ((v >> 16) | (v << 16)) & M32
            self.d[reg] = v; self.flags_logic(v, 4); self.cycles += 4; return
        if (op & 0xffc0) == 0x4840:
            a = self.ea_addr(mode, reg, 4)
            self.a[7] = (self.a[7] - 4) & M32; self.wl(self.a[7], a); self.cycles += 12; return
        if (op & 0xfff8) == 0x4880:
            v = sx8(self.d[reg] & 255) & 0xffff
            self.d[reg] = (self.d[reg] & 0xffff0000) | v; self.flags_logic(v, 2); self.cycles += 4; return
        if (op & 0xfff8) == 0x48c0:
            v = sx16(self.d[reg] & 0xffff) & M32
            self.d[reg] = v; self.flags_logic(v, 4); self.cycles += 4; return
        if (op & 0xfb80) == 0x4880:   # movem
            size = 4 if op & 0x40 else 2
            mask = self.fetch()
            regs = [('d', i) for i in range(8)] + [('a', i) for i in range(8)]
            if op & 0x400:   # memory to registers
                if mode == 3: a = self.a[reg]
                else: a = self.ea_addr(mode, reg, size)
                for i in range(16):
                    if mask & (1 << i):
                        v = self.rsz(a, size)
                        if size == 2: v = sx16(v) & M32
                        k, n = regs[i]
                        if k == 'd': self.d[n] = v
                        else: self.a[n] = v
                        a += size
                if mode == 3: self.a[reg] = a & M32
                self.cycles += 12 + 4 * bin(mask).count('1') * (size // 2)
                return
            if mode == 4:
                a = self.a[reg]
                for i in range(16):
                    if mask & (1 << i):
                        k, n = regs[15 - i]
                        a -= size
                        v = self.d[n] if k == 'd' else self.a[n]
                        self.wsz(a, size, v)
                self.a[reg] = a & M32
            else:
                a = self.ea_addr(mode, reg, size)
                for i in range(16):
                    if mask & (1 << i):
                        k, n = regs[i]
                        v = self.d[n] if k == 'd' else self.a[n]
                        self.wsz(a, size, v); a += size
            self.cycles += 8 + 4 * bin(mask).count('1') * (size // 2)
            return
        if (op & 0xfff8) == 0x4e50:
            self.a[7] = (self.a[7] - 4) & M32; self.wl(self.a[7], self.a[reg])
            self.a[reg] = self.a[7]; self.a[7] = (self.a[7] + sx16(self.fetch())) & M32; return
        if (op & 0xfff8) == 0x4e58:
            self.a[7] = self.a[reg]; self.a[reg] = self.rl(self.a[7]); self.a[7] = (self.a[7] + 4) & M32; return
        if op == 0x4e73:
            if not getattr(self, 'in_irq', False): raise EmuError('rte outside an interrupt at $%06x' % self.lastpc)
            sr = self.rw(self.a[7]); self.pc = self.rl(self.a[7] + 2); self.a[7] = (self.a[7] + 6) & M32
            self.set_ccr(sr & 0x1f); self.in_irq = False; return
        if op == 0x4afc: raise EmuError('ILLEGAL at $%06x' % self.lastpc)
        if (op & 0xffc0) == 0x44c0:
            v, _ = self.read_ea(mode, reg, 2); self.set_ccr(v & 0x1f); return
        if (op & 0xffc0) in (0x40c0, 0x46c0):
            raise EmuError('privileged SR access at $%06x (crashes on a real 68000 in user mode)' % self.lastpc)
        sc = (op >> 6) & 3
        if sc == 3: self.op_illegal(op)
        size = (1, 2, 4)[sc]
        top = op & 0xff00
        if top == 0x4200:
            if mode == 1: self.op_illegal(op)
            self.write_ea(mode, reg, size, 0)
            self.N = 0; self.Z = 1; self.V = 0; self.C = 0; self.cycles += 6; return
        if top == 0x4a00:
            if mode == 1: self.op_illegal(op)
            v, _ = self.read_ea(mode, reg, size); self.flags_logic(v, size); self.cycles += 4; return
        if top in (0x4400, 0x4600, 0x4000):
            v, loc = self.read_ea(mode, reg, size)
            if top == 0x4600:
                r = ~v & MASK[size]; self.flags_logic(r, size)
            elif top == 0x4400:
                r = self.do_sub(v, 0, size)
            else:
                r = self.do_sub(v + self.X, 0, size)
            self.write_loc(loc, size, r); self.cycles += 6; return
        self.op_illegal(op)

    def op_arith(self, op):
        hi = op >> 12
        rn = (op >> 9) & 7
        opm = (op >> 6) & 7
        mode = (op >> 3) & 7; reg = op & 7
        if hi in (8, 0xc) and opm in (3, 7):   # mul / div
            s, _ = self.read_ea(mode, reg, 2)
            if mode == 1: self.op_illegal(op)
            if hi == 0xc:
                if opm == 3: r = (self.d[rn] & 0xffff) * s
                else: r = sx16(self.d[rn] & 0xffff) * sx16(s)
                r &= M32; self.d[rn] = r; self.flags_logic(r, 4); self.cycles += 70; return
            if s == 0: raise EmuError('division by zero at $%06x' % self.lastpc)
            dv = self.d[rn]
            if opm == 3:
                q, rem = divmod(dv, s)
                if q > 0xffff: self.V = 1; self.C = 0; return
            else:
                a = sx32(dv); b = sx16(s)
                q = abs(a) // abs(b); rem = abs(a) % abs(b)
                if (a < 0) != (b < 0): q = -q
                if a < 0: rem = -rem
                if not -32768 <= q <= 32767: self.V = 1; self.C = 0; return
            self.d[rn] = ((rem & 0xffff) << 16) | (q & 0xffff)
            self.flags_logic(q & 0xffff, 2); self.cycles += 140; return
        if hi == 0xc and (op & 0x130) == 0x100 and opm in (5, 6) and mode in (0, 1):
            # exg
            m = op & 0xf8
            if (op & 0x1f8) == 0x140: self.d[rn], self.d[reg] = self.d[reg], self.d[rn]
            elif (op & 0x1f8) == 0x148: self.a[rn], self.a[reg] = self.a[reg], self.a[rn]
            elif (op & 0x1f8) == 0x188: self.d[rn], self.a[reg] = self.a[reg], self.d[rn]
            else: self.op_illegal(op)
            self.cycles += 6; return
        if hi in (9, 0xb, 0xd) and opm in (3, 7):   # suba / cmpa / adda
            size = 4 if opm == 7 else 2
            s, _ = self.read_ea(mode, reg, size)
            if size == 2: s = sx16(s) & M32
            if hi == 0xd: self.a[rn] = (self.a[rn] + s) & M32
            elif hi == 9: self.a[rn] = (self.a[rn] - s) & M32
            else: self.do_sub(s, self.a[rn], 4, setx=False)
            self.cycles += 8; return
        size = (1, 2, 4)[opm & 3]
        if opm & 3 == 3: self.op_illegal(op)
        todn = opm < 4
        if hi == 0xb and not todn:   # eor Dn,<ea>  (cmpm when mode==1)
            if mode == 1: raise EmuError('cmpm not supported at $%06x' % self.lastpc)
            v, loc = self.read_ea(mode, reg, size)
            r = v ^ (self.d[rn] & MASK[size]); self.flags_logic(r, size)
            self.write_loc(loc, size, r); self.cycles += 8; return
        if not todn and mode == 0 and hi in (0xd, 9):   # addx / subx Dy,Dx
            m = MASK[size]; sv = self.d[reg] & m; dv = self.d[rn] & m; z = self.Z
            if hi == 0xd: r = self.do_add(sv, dv, size, self.X)
            else:
                r = (dv - sv - self.X) & m; c = 1 if sv + self.X > dv else 0
                self.C = self.X = c; self.N = 1 if r & MSB[size] else 0
                self.V = 1 if ((sv ^ dv) & (r ^ dv)) & MSB[size] else 0
            if r == 0: self.Z = z
            else: self.Z = 0
            self.d[rn] = (self.d[rn] & ~m & M32) | r
            self.cycles += 8 if size == 4 else 4; return
        if not todn and mode in (0, 1):
            raise EmuError('addx/subx/abcd/sbcd not supported at $%06x' % self.lastpc)
        if todn:
            s, _ = self.read_ea(mode, reg, size)
            d = self.d[rn] & MASK[size]
            if hi == 0xd: r = self.do_add(s, d, size)
            elif hi == 9: r = self.do_sub(s, d, size)
            elif hi == 0xb: self.do_sub(s, d, size, setx=False); self.cycles += 6; return
            elif hi == 0xc: r = s & d; self.flags_logic(r, size)
            else: r = s | d; self.flags_logic(r, size)
            m = MASK[size]; self.d[rn] = (self.d[rn] & ~m & M32) | r
            self.cycles += 6; return
        d, loc = self.read_ea(mode, reg, size)
        s = self.d[rn] & MASK[size]
        if hi == 0xd: r = self.do_add(s, d, size)
        elif hi == 9: r = self.do_sub(s, d, size)
        elif hi == 0xc: r = s & d; self.flags_logic(r, size)
        else: r = s | d; self.flags_logic(r, size)
        self.write_loc(loc, size, r); self.cycles += 10

    def op_shift(self, op):
        sc = (op >> 6) & 3
        left = (op >> 8) & 1
        if sc == 3:   # memory shift, word
            mode = (op >> 3) & 7; reg = op & 7
            tt = (op >> 9) & 3
            v, loc = self.read_ea(mode, reg, 2)
            r = self.shift(tt, left, v, 1, 2)
            self.write_loc(loc, 2, r); self.cycles += 8; return
        size = (1, 2, 4)[sc]
        tt = (op >> 3) & 3
        reg = op & 7
        cnt = (op >> 9) & 7
        if op & 0x20: cnt = self.d[cnt] & 63
        elif cnt == 0: cnt = 8
        v = self.d[reg] & MASK[size]
        r = self.shift(tt, left, v, cnt, size)
        m = MASK[size]; self.d[reg] = (self.d[reg] & ~m & M32) | r
        self.cycles += 6 + 2 * cnt

    def shift(self, tt, left, v, cnt, size):
        m = MASK[size]; bits = size * 8; msb = MSB[size]
        if cnt == 0:
            self.C = 0 if tt != 2 else self.X
            self.flags_logic_keepc(v, size); self.V = 0; return v
        if tt == 0 or tt == 1:   # AS / LS
            if left:
                r = (v << cnt)
                self.C = self.X = (r >> bits) & 1
                rr = r & m
                if tt == 0:
                    # V set if msb changed at any time
                    top = v >> (bits - cnt - 1) if cnt < bits else v
                    allbits = (1 << (cnt + 1)) - 1 if cnt < bits else None
                    if cnt >= bits: self.V = 1 if v else 0
                    else:
                        t = (v >> (bits - cnt - 1)) & ((1 << (cnt + 1)) - 1)
                        self.V = 0 if t in (0, (1 << (cnt + 1)) - 1) else 1
                else: self.V = 0
                r = rr
            else:
                if tt == 0 and v & msb: sv = v - (1 << bits)
                else: sv = v
                self.C = self.X = (sv >> (cnt - 1)) & 1 if cnt <= bits + 1 else (1 if sv < 0 else 0)
                r = (sv >> cnt) & m
                self.V = 0
        elif tt == 3:   # ROL / ROR
            c = cnt % bits
            r = ((v << c) | (v >> (bits - c))) & m if left else ((v >> c) | (v << (bits - c))) & m
            self.C = (r & 1) if left else (1 if r & msb else 0)
            self.V = 0
        else:   # ROXL / ROXR
            r = v; x = self.X
            for _ in range(cnt):
                if left:
                    nx = 1 if r & msb else 0; r = ((r << 1) | x) & m; x = nx
                else:
                    nx = r & 1; r = (r >> 1) | (msb if x else 0); x = nx
            self.X = self.C = x; self.V = 0
        self.N = 1 if r & msb else 0; self.Z = 1 if r == 0 else 0
        return r

    def flags_logic_keepc(self, v, size):
        self.N = 1 if v & MSB[size] else 0; self.Z = 1 if v == 0 else 0

    # ------------------------------------------------------------- running
    def run_frames(self, nframes, events=None, on_frame=None, max_instr_per_frame=400000):
        """Run until nframes more frames have passed.  events: {frame: callable(amiga)}."""
        target = self.frame + nframes
        n = 0
        while self.frame < target:
            fstart = self.frame
            while self.cycles < (self.frame + 1) * CYC_FRAME:
                self.step()
                n += 1
                if n > max_instr_per_frame:
                    raise EmuError('runaway: %d instructions without a frame end, pc=$%06x' % (n, self.pc))
            n = 0
            self.frame += 1
            # vertical blank interrupt (level 3) when the program enabled it: INTENA master + VERTB
            if (self.intena & 0x4020) == 0x4020 and not getattr(self, 'in_irq', False):
                vec = self.rl(0x6c)
                if vec:
                    self.a[7] = (self.a[7] - 6) & M32
                    self.ww(self.a[7], 0x2000 | self.ccr()); self.wl(self.a[7] + 2, self.pc)
                    self.pc = vec; self.in_irq = True; self.irqs = getattr(self, 'irqs', 0) + 1
            self.key_tick()
            self.mix_frame()
            if events and self.frame in events:
                events[self.frame](self)
            if on_frame: on_frame(self)

    def key(self, code, up=False):
        self.keyq.append(code | (0x80 if up else 0))

    def tap(self, code):
        self.key(code); self.key(code, True)

    def save_wav(self, path):
        with wave.open(path, 'wb') as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(AUDIO_RATE)
            w.writeframes(b''.join(self.audio_out))

if __name__ == '__main__':
    am = Amiga()
    am.load_hunks(sys.argv[1])
    try:
        am.run_frames(int(sys.argv[2]) if len(sys.argv) > 2 else 100)
    except Halt as h:
        print(h)
    print('\n'.join(am.msgs))
    am.render().save('/tmp/emu.png')
