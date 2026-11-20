"""harness.py - drive build/SOlymp.game in tools/emu68k.py: symbols, keys, joystick, screenshots."""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))
import emu68k

class Game:
    def __init__(self, exe='build/SOlymp.game', mapf='build/SOlymp.map', out='build/test', datadir='build/disk'):
        os.makedirs(out, exist_ok=True); self.out = out
        self.sym = {}; names = None
        for l in open(mapf):
            if l.startswith('#sections'): names = l.split()[1:]; continue
            p = l.split()
            if len(p) == 3: self.sym[p[2]] = (p[0], int(p[1], 16))
        self.am = emu68k.Amiga(datadir); self.am.load_hunks(exe)
        self.base = {}
        for m in self.am.msgs:
            r = re.match(r'hunk (\d+): \d+ bytes at \$([0-9a-f]+)', m)
            if r: self.base[names[int(r.group(1))]] = int(r.group(2), 16)
    def A(self, n): s, o = self.sym[n]; return self.base[s] + o
    def w(self, n): return self.am.rw(self.A(n))
    def b(self, n): return self.am.rb(self.A(n))
    def l(self, n): return self.am.rl(self.A(n))
    def run(self, n): self.am.run_frames(n)
    def key(self, k, n=6): self.am.tap(k); self.run(n)
    def fire(self, n=10):
        self.am.joy['fire'] = 1; self.run(3); self.am.joy['fire'] = 0; self.run(n)
    def joy(self, d, n=3, after=6):
        self.am.joy[d] = 1; self.run(n); self.am.joy[d] = 0; self.run(after)
    def shot(self, name): self.am.render().resize((640, 512), 0).save(os.path.join(self.out, name + '.png'))
    def pc_where(self):
        pc = self.am.pc; best = None
        for k, (s, o) in self.sym.items():
            a = self.base.get(s, 0) + o
            if a <= pc and (best is None or a > best[1]): best = (k, a)
        return '%s+%x' % (best[0], pc - best[1]) if best else hex(pc)

    def hook(self, names):
        """count entries of routines: self.hits[name]"""
        self.hits = {n: 0 for n in names}
        addr = {self.A(n): n for n in names}
        orig = self.am.step
        def step():
            n = addr.get(self.am.pc)
            if n: self.hits[n] += 1
            orig()
        self.am.step = step
    def until(self, name, count=1, mx=2000):
        start = self.hits[name]; f = 0
        while self.hits[name] - start < count and f < mx: self.run(1); f += 1
        return f < mx

    def idle(self, mx=1500):
        """run until the program polls the input again and again (a screen waiting for the player)"""
        if not hasattr(self, 'hits') or 'k_input' not in self.hits: self.hook(['k_input'])
        f = 0
        while f < mx:
            a = self.hits['k_input']; self.run(6); f += 6
            if self.hits['k_input'] - a >= 3: return True
        return False

def event_game(n, **kw):
    """a game that goes straight into event n (1 = soccer ...)"""
    g = Game(**kw)
    g.am.ww(g.A('dbg_event'), n)
    g.hook(['k_input'])
    return g

def ev_addr(g, mapf):
    """-> function name -> address in the loaded event"""
    hb = [g.am.rl(g.A('hunk_base') + 4 * i) for i in range(8)]
    names = open(mapf).readline().split()[1:]
    sym = {}
    for l in open(mapf):
        p = l.split()
        if len(p) == 3: sym[p[2]] = (p[0], int(p[1], 16))
    return lambda n: hb[names.index(sym[n][0])] + sym[n][1]
