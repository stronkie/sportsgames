#!/usr/bin/env python3
"""asm68k.py - a small Motorola-syntax 68000 assembler that writes Amiga
hunk executables.  Written for Stronkie's Slot Machine (Stronkie Soft).

Usage: python3 tools/asm68k.py src/main.s -o build/SSlots [-l listing.txt]

Supports the plain 68000 instruction set that the game uses, sections
(code / data / bss, with _c for chip memory), dc / ds / even / cnop /
incbin / include / equ / = / rept..endr, local labels (.name) and
expressions with + - * / % << >> & | ^ ~ and parentheses.
Branches without a size are .w, absolute addresses without .w are .l.
"""
import os, re, struct, sys

class AsmError(Exception):
    pass

# --------------------------------------------------------------- values
class Val:
    """A value: an integer plus the section it is relative to (None = absolute)."""
    __slots__ = ('v', 'sec')
    def __init__(self, v, sec=None):
        self.v = v; self.sec = sec
    def absolute(self, what='value'):
        if self.sec is not None:
            raise AsmError('%s must be absolute' % what)
        return self.v

def _bin(op, a, b):
    if op == '+':
        if a.sec is not None and b.sec is not None:
            raise AsmError('cannot add two relocatable values')
        return Val(a.v + b.v, a.sec if a.sec is not None else b.sec)
    if op == '-':
        if b.sec is not None:
            if a.sec is b.sec or a.sec is None:   # (None: a forward label on pass 1)
                return Val(a.v - b.v)
            raise AsmError('cannot subtract values from different sections')
        return Val(a.v - b.v, a.sec)
    x = a.absolute(); y = b.absolute()
    if op == '*': return Val(x * y)
    if op == '/':
        if y == 0: raise AsmError('division by zero')
        q = abs(x) // abs(y)
        return Val(q if (x >= 0) == (y >= 0) else -q)
    if op == '%': return Val(x % y)
    if op == '<<': return Val(x << y)
    if op == '>>': return Val(x >> y)
    if op == '&': return Val(x & y)
    if op == '|': return Val(x | y)
    if op == '^': return Val(x ^ y)
    if op == '==': return Val(-1 if x == y else 0)
    if op == '!=': return Val(-1 if x != y else 0)
    if op == '<': return Val(-1 if x < y else 0)
    if op == '>': return Val(-1 if x > y else 0)
    if op == '<=': return Val(-1 if x <= y else 0)
    if op == '>=': return Val(-1 if x >= y else 0)
    raise AsmError('bad operator ' + op)

PREC = [('|',), ('^',), ('&',), ('==', '!=', '<', '>', '<=', '>='), ('<<', '>>'), ('+', '-'), ('*', '/', '%')]
TOKRE = re.compile(r"\s*(?:(\$[0-9a-fA-F]+)|(%[01]+)|(\d+)|('(?:[^']|'')*'|\"[^\"]*\")|"
                   r"([A-Za-z_.][A-Za-z0-9_.@]*)|(<<|>>|==|!=|<=|>=|[-+*/%&|^~!()<>]))")

class Expr:
    def __init__(self, asm, text):
        self.asm = asm; self.text = text
        self.toks = []
        pos = 0; text = text.strip()
        while pos < len(text):
            m = TOKRE.match(text, pos)
            if not m or m.end() == pos:
                if text[pos:].strip() == '':
                    break
                raise AsmError('bad expression: ' + text)
            pos = m.end()
            if m.group(1): self.toks.append(('n', int(m.group(1)[1:], 16)))
            elif m.group(2): self.toks.append(('n', int(m.group(2)[1:], 2)))
            elif m.group(3): self.toks.append(('n', int(m.group(3))))
            elif m.group(4):
                s = m.group(4)[1:-1].replace("''", "'")
                v = 0
                for ch in s: v = (v << 8) | (ord(ch) & 255)
                self.toks.append(('n', v))
            elif m.group(5): self.toks.append(('s', m.group(5)))
            else: self.toks.append(('o', m.group(6)))
        self.i = 0

    def eval(self):
        self.i = 0
        v = self._level(0)
        if self.i != len(self.toks):
            raise AsmError('junk in expression: ' + self.text)
        return v

    def _peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else (None, None)

    def _level(self, n):
        if n == len(PREC):
            return self._unary()
        a = self._level(n + 1)
        while True:
            t, v = self._peek()
            if t == 'o' and v in PREC[n]:
                self.i += 1
                b = self._level(n + 1)
                a = _bin(v, a, b)
            else:
                return a

    def _unary(self):
        t, v = self._peek()
        if t == 'o' and v == '-':
            self.i += 1; x = self._unary(); return Val(-x.absolute())
        if t == 'o' and v == '+':
            self.i += 1; return self._unary()
        if t == 'o' and v == '~':
            self.i += 1; x = self._unary(); return Val(~x.absolute())
        if t == 'o' and v == '!':
            self.i += 1; x = self._unary(); return Val(0 if x.absolute() else -1)
        if t == 'o' and v == '(':
            self.i += 1; x = self._level(0)
            t2, v2 = self._peek()
            if v2 != ')': raise AsmError('missing ) in ' + self.text)
            self.i += 1; return x
        if t == 'o' and v == '*':
            self.i += 1; return Val(self.asm.pc, self.asm.cur)
        if t == 'n':
            self.i += 1; return Val(v)
        if t == 's':
            self.i += 1; return self.asm.lookup(v)
        raise AsmError('bad expression: ' + self.text)

# --------------------------------------------------------------- sections
class Section:
    def __init__(self, name, kind, chip, index):
        self.name = name; self.kind = kind; self.chip = chip; self.index = index
        self.data = bytearray(); self.size = 0
        self.relocs = []  # (offset, target section)

# --------------------------------------------------------------- operands
DREG = {'d%d' % i: i for i in range(8)}
AREG = {'a%d' % i: i for i in range(8)}
AREG['sp'] = 7

class Op:
    # kinds: dn an ind postinc predec disp index absw absl pcdisp pcindex imm reglist
    def __init__(self, kind, reg=0, expr=None, xreg=None, xlong=False, mask=0):
        self.kind = kind; self.reg = reg; self.expr = expr
        self.xreg = xreg; self.xlong = xlong; self.mask = mask

def split_operands(s):
    out = []; depth = 0; cur = ''; q = None
    for ch in s:
        if q:
            cur += ch
            if ch == q: q = None
            continue
        if ch in '\'"':
            q = ch; cur += ch; continue
        if ch == '(': depth += 1
        elif ch == ')': depth -= 1
        if ch == ',' and depth == 0:
            out.append(cur.strip()); cur = ''
        else:
            cur += ch
    if cur.strip(): out.append(cur.strip())
    return out

def parse_reglist(s):
    mask = 0
    for part in s.lower().split('/'):
        part = part.strip()
        if '-' in part:
            a, b = part.split('-')
            ra = reg_num(a); rb = reg_num(b)
            if ra is None or rb is None: return None
            for r in range(min(ra, rb), max(ra, rb) + 1): mask |= 1 << r
        else:
            r = reg_num(part)
            if r is None: return None
            mask |= 1 << r
    return mask

def reg_num(s):
    s = s.strip().lower()
    if s in DREG: return DREG[s]
    if s in AREG: return 8 + AREG[s]
    return None

def parse_index(s):
    s = s.strip().lower(); xl = False
    if s.endswith('.l'): xl = True; s = s[:-2]
    elif s.endswith('.w'): s = s[:-2]
    r = reg_num(s)
    if r is None: raise AsmError('bad index register ' + s)
    return r, xl

def parse_operand(s):
    t = s.strip(); low = t.lower()
    if low.startswith('#'):
        return Op('imm', expr=t[1:])
    if low in DREG: return Op('dn', DREG[low])
    if low in AREG: return Op('an', AREG[low])
    if low in ('sr', 'ccr', 'usp'): return Op(low)
    m = re.fullmatch(r'\(\s*(a[0-7]|sp)\s*\)', low)
    if m: return Op('ind', AREG[m.group(1)])
    m = re.fullmatch(r'\(\s*(a[0-7]|sp)\s*\)\+', low)
    if m: return Op('postinc', AREG[m.group(1)])
    m = re.fullmatch(r'-\(\s*(a[0-7]|sp)\s*\)', low)
    if m: return Op('predec', AREG[m.group(1)])
    # (d,An) / (d,An,Xn) / (d,pc) forms
    m = re.fullmatch(r'\((.*)\)', t)
    if m and '(' not in m.group(1):
        parts = [p.strip() for p in m.group(1).split(',')]
        if len(parts) >= 2:
            base = parts[1].lower(); disp = parts[0]
            if len(parts) == 2 and (base in AREG or base == 'pc'):
                return Op('pcdisp' if base == 'pc' else 'disp', AREG.get(base, 0), expr=disp)
            if len(parts) == 3:
                xr, xl = parse_index(parts[2])
                return Op('pcindex' if base == 'pc' else 'index', AREG.get(base, 0), expr=disp, xreg=xr, xlong=xl)
        if len(parts) == 2 and parts[0].lower() in AREG:
            xr, xl = parse_index(parts[1])
            return Op('index', AREG[parts[0].lower()], expr='0', xreg=xr, xlong=xl)
    # d(An) / d(An,Xn) / d(pc)
    m = re.fullmatch(r'(.*)\(\s*([A-Za-z0-9]+)\s*(?:,\s*([A-Za-z0-9.]+)\s*)?\)', t)
    if m and m.group(2).lower() in list(AREG) + ['pc']:
        disp = m.group(1).strip() or '0'; base = m.group(2).lower()
        if m.group(3):
            xr, xl = parse_index(m.group(3))
            return Op('pcindex' if base == 'pc' else 'index', AREG.get(base, 0), expr=disp, xreg=xr, xlong=xl)
        return Op('pcdisp' if base == 'pc' else 'disp', AREG.get(base, 0), expr=disp)
    if re.fullmatch(r'[dDaAsS][0-7pP]?.*[-/].*', t):
        mask = parse_reglist(t)
        if mask is not None:
            return Op('reglist', mask=mask)
    if low.endswith('.w'): return Op('absw', expr=t[:-2])
    if low.endswith('.l'): return Op('absl', expr=t[:-2])
    return Op('absl', expr=t)

COND = {'t': 0, 'f': 1, 'hi': 2, 'ls': 3, 'cc': 4, 'hs': 4, 'cs': 5, 'lo': 5, 'ne': 6, 'eq': 7,
        'vc': 8, 'vs': 9, 'pl': 10, 'mi': 11, 'ge': 12, 'lt': 13, 'gt': 14, 'le': 15}
SZ = {'b': 0, 'w': 1, 'l': 2}

# --------------------------------------------------------------- assembler
class Assembler:
    def __init__(self, incdirs=()):
        self.incdirs = list(incdirs)
        self.syms = {}
        self.sections = []
        self.listing = []

    # symbols ---------------------------------------------------------------
    def fullname(self, name):
        if name.startswith('.'):
            return (self.lastglobal or '') + name
        return name

    def lookup(self, name):
        n = self.fullname(name)
        if n in self.syms:
            return self.syms[n]
        if self.final:
            raise AsmError('undefined symbol ' + n)
        self.undefined = True
        return Val(0)

    def define(self, name, val, label=False):
        n = self.fullname(name)
        if not name.startswith('.') and label:
            self.lastglobal = name
        if self.passno == 1 and n in self.syms and label:
            raise AsmError('symbol defined twice: ' + n)
        self.syms[n] = val

    def eval(self, text):
        return Expr(self, text).eval()

    # output ----------------------------------------------------------------
    def emit(self, b):
        sec = self.cur
        if self.passno == 2:
            if sec.kind == 'bss':
                if any(b): raise AsmError('data in a bss section')
            else:
                sec.data[self.pc:self.pc + len(b)] = b
        self.pc += len(b)

    def w16(self, v): return struct.pack('>H', v & 0xffff)
    def w32(self, v): return struct.pack('>I', v & 0xffffffff)

    def reloc(self, offset, val):
        if self.passno == 2 and val.sec is not None:
            self.cur.relocs.append((offset, val.sec))

    # files -----------------------------------------------------------------
    def find(self, fname, base):
        for d in [base] + self.incdirs:
            p = os.path.join(d, fname)
            if os.path.exists(p): return p
        raise AsmError('file not found: ' + fname)

    def readlines(self, path):
        out = []
        with open(path, encoding='latin-1') as f:
            for i, line in enumerate(f):
                out.append((path, i + 1, line.rstrip('\n').rstrip('\r')))
        return out

    def run(self, path):
        for self.passno in (1, 2):
            self.final = self.passno == 2
            self.lastglobal = None
            if self.passno == 1:
                self.sections = []
            for s in self.sections:
                s.size = s.size
                if s.kind != 'bss': s.data = bytearray(s.size)
                s.relocs = []
            self.secmap = {s.name: s for s in self.sections}
            self.cur = None
            self.pc = 0
            self.set_section('code', 'code', False)
            self.process(self.readlines(path), os.path.dirname(path))
            self.cur.size = max(self.cur.size, self.pc)
            for s in self.sections:
                pass
        return self

    def set_section(self, name, kind, chip):
        if self.cur is not None:
            self.cur.size = max(self.cur.size, self.pc)
            self.cur.pcsave = self.pc
        if name in self.secmap:
            self.cur = self.secmap[name]
            self.pc = getattr(self.cur, 'pcsave', 0) if self.cur.started == self.passno else 0
        else:
            if self.passno == 2: raise AsmError('new section in pass 2')
            s = Section(name, kind, chip, len(self.sections))
            self.sections.append(s); self.secmap[name] = s
            self.cur = s; self.pc = 0
        self.cur.started = self.passno

    def process(self, lines, base):
        i = 0
        while i < len(lines):
            path, ln, line = lines[i]
            i += 1
            try:
                r = self.line(line, base, lines, i)
                if isinstance(r, int):
                    i = r
            except AsmError as e:
                raise AsmError('%s:%d: %s\n    %s' % (path, ln, e, line.strip()))

    def strip_comment(self, line):
        if line.lstrip().startswith('*') and (line.startswith('*')):
            return ''
        out = ''; q = None
        for ch in line:
            if q:
                out += ch
                if ch == q: q = None
                continue
            if ch in '\'"': q = ch
            elif ch == ';': break
            out += ch
        return out.rstrip()

    def line(self, raw, base, lines, nexti):
        line = self.strip_comment(raw)
        if not line.strip():
            return
        label = None
        if not line[0].isspace():
            m = re.match(r'([A-Za-z_.][A-Za-z0-9_.@]*):?', line)
            if not m: raise AsmError('bad label')
            label = m.group(1); line = line[m.end():]
        else:
            m = re.match(r'\s+([A-Za-z_.][A-Za-z0-9_.@]*):(.*)', line)
            if m:
                label = m.group(1); line = m.group(2)
        parts = line.strip().split(None, 1)
        mnem = parts[0].lower() if parts else ''
        args = parts[1].strip() if len(parts) > 1 else ''
        # equates
        if mnem in ('equ', '=', 'set') or (mnem.startswith('=') and label):
            if mnem.startswith('=') and mnem != '=':
                args = mnem[1:] + ' ' + args
            if not label: raise AsmError('equ without a name')
            v = self.eval(args)
            n = self.fullname(label)
            self.syms[n] = v
            return
        if label:
            self.define(label, Val(self.pc, self.cur), label=True)
        if not mnem:
            return
        size = None
        if '.' in mnem and not mnem.startswith('.'):
            mnem, size = mnem.split('.', 1)
        return self.statement(mnem, size, args, base, lines, nexti)

    # directives ---------------------------------------------------------------
    def statement(self, mnem, size, args, base, lines, nexti):
        if mnem == 'section':
            a = [x.strip().lower() for x in args.split(',')]
            name = a[0]; t = a[1] if len(a) > 1 else 'code'
            chip = t.endswith('_c')
            kind = t.split('_')[0]
            if kind not in ('code', 'data', 'bss'): raise AsmError('bad section type')
            self.set_section(name, kind, chip)
            return
        if mnem in ('code', 'data', 'bss'):
            self.set_section(mnem, mnem, False); return
        if mnem in ('xdef', 'xref', 'opt', 'machine', 'output', 'list', 'nolist', 'idnt', 'end'):
            return
        if mnem == 'even':
            if self.pc & 1: self.emit(b'\0')
            return
        if mnem == 'cnop':
            a = split_operands(args)
            off = self.eval(a[0]).absolute(); al = self.eval(a[1]).absolute()
            while (self.pc - off) % al: self.emit(b'\0')
            return
        if mnem == 'dc':
            sz = size or 'w'
            for item in split_operands(args):
                if sz == 'b' and item[0] in '\'"' and item[-1] == item[0] and len(item) >= 2:
                    s = item[1:-1]
                    if item[0] == "'": s = s.replace("''", "'")
                    self.emit(s.encode('latin-1'))
                    continue
                v = self.eval(item)
                if sz == 'b':
                    x = v.absolute()
                    if not -128 <= x <= 255 and self.final: raise AsmError('byte out of range')
                    self.emit(bytes([x & 255]))
                elif sz == 'w':
                    if self.pc & 1: raise AsmError('odd address')
                    x = v.absolute()
                    if not -32768 <= x <= 65535 and self.final: raise AsmError('word out of range')
                    self.emit(self.w16(x))
                else:
                    if self.pc & 1: raise AsmError('odd address')
                    self.reloc(self.pc, v)
                    self.emit(self.w32(v.v))
            return
        if mnem in ('ds', 'dcb'):
            sz = {'b': 1, 'w': 2, 'l': 4}[size or 'w']
            a = split_operands(args)
            n = self.eval(a[0]).absolute()
            fill = self.eval(a[1]).absolute() if len(a) > 1 else 0
            if sz > 1 and self.pc & 1: raise AsmError('odd address')
            if fill == 0:
                self.emit(bytes(n * sz))
            else:
                one = fill.to_bytes(sz, 'big', signed=fill < 0)
                self.emit(one * n)
            return
        if mnem == 'incbin':
            a = split_operands(args)
            fn = a[0].strip('"\'')
            data = open(self.find(fn, base), 'rb').read()
            if len(a) > 1:
                off = self.eval(a[1]).absolute()
                ln = self.eval(a[2]).absolute() if len(a) > 2 else len(data) - off
                data = data[off:off + ln]
            self.emit(data)
            return
        if mnem == 'include':
            fn = args.strip().strip('"\'')
            p = self.find(fn, base)
            self.process(self.readlines(p), os.path.dirname(p))
            return
        if mnem == 'rept':
            n = self.eval(args).absolute()
            depth = 1; j = nexti; body = []
            while j < len(lines):
                t = self.strip_comment(lines[j][2]).strip().lower()
                w = t.split()[0] if t.split() else ''
                if w == 'rept': depth += 1
                if w == 'endr':
                    depth -= 1
                    if depth == 0: break
                body.append(lines[j]); j += 1
            else:
                raise AsmError('rept without endr')
            for _ in range(n):
                self.process(body, base)
            return j + 1
        if mnem == 'endr':
            raise AsmError('endr without rept')
        if mnem == 'fail':
            raise AsmError('fail: ' + args)
        if mnem == 'assert':
            if self.final and not self.eval(args).absolute():
                raise AsmError('assertion failed: ' + args)
            return
        return self.instruction(mnem, size, args)

    # effective addresses ----------------------------------------------------
    def ea(self, op, size, extoff):
        """Return (mode, reg, extbytes) for an operand.  extoff = byte offset
        of the first extension word of this operand from the instruction start."""
        k = op.kind
        if k == 'dn': return 0, op.reg, b''
        if k == 'an': return 1, op.reg, b''
        if k == 'ind': return 2, op.reg, b''
        if k == 'postinc': return 3, op.reg, b''
        if k == 'predec': return 4, op.reg, b''
        if k == 'disp':
            d = self.eval(op.expr).absolute('displacement')
            if self.final and not -32768 <= d <= 32767: raise AsmError('displacement out of range')
            return 5, op.reg, self.w16(d)
        if k == 'index':
            d = self.eval(op.expr).absolute('displacement')
            if self.final and not -128 <= d <= 127: raise AsmError('index displacement out of range')
            return 6, op.reg, self.w16(self.brief(op, d))
        if k == 'absw':
            v = self.eval(op.expr).absolute('short address')
            if self.final and not (-32768 <= v <= 32767 or 0xffff8000 <= v <= 0xffffffff):
                raise AsmError('short address out of range')
            return 7, 0, self.w16(v)
        if k == 'absl':
            v = self.eval(op.expr)
            self.reloc(self.pc + extoff, v)
            return 7, 1, self.w32(v.v)
        if k in ('pcdisp', 'pcindex'):
            v = self.eval(op.expr)
            if v.sec is not None and v.sec is not self.cur:
                raise AsmError('pc-relative to another section')
            d = v.v - (self.pc + extoff)
            if k == 'pcdisp':
                if self.final and not -32768 <= d <= 32767: raise AsmError('pc displacement out of range')
                return 7, 2, self.w16(d)
            if self.final and not -128 <= d <= 127: raise AsmError('pc index displacement out of range')
            return 7, 3, self.w16(self.brief(op, d))
        if k == 'imm':
            v = self.eval(op.expr)
            if size == 'l':
                self.reloc(self.pc + extoff, v)
                return 7, 4, self.w32(v.v)
            x = v.absolute('immediate')
            if self.final:
                lim = (-128, 255) if size == 'b' else (-32768, 65535)
                if not lim[0] <= x <= lim[1]: raise AsmError('immediate out of range')
            if size == 'b': return 7, 4, self.w16(x & 255)
            return 7, 4, self.w16(x)
        raise AsmError('operand not allowed here')

    def brief(self, op, d):
        return (op.xreg << 12) | (0x800 if op.xlong else 0) | (d & 255)

    def eabits(self, op, size, extoff):
        m, r, ext = self.ea(op, size, extoff)
        return (m << 3) | r, ext

    # instructions -----------------------------------------------------------
    def out(self, words, *exts):
        b = b''.join(self.w16(w) for w in words) + b''.join(exts)
        self.emit(b)

    def instruction(self, mnem, size, args):
        if self.pc & 1: raise AsmError('instruction at odd address')
        ops = [parse_operand(x) for x in split_operands(args)] if args else []
        n = len(ops)
        sz = size
        def need(c):
            if n != c: raise AsmError('%s needs %d operands' % (mnem, c))
        def szc():
            if (sz or 'w') not in SZ: raise AsmError('bad size')
            return SZ[sz or 'w']
        def kinds(i, *ks):
            if ops[i].kind not in ks: raise AsmError('bad operand %d for %s' % (i + 1, mnem))

        simple = {'rts': 0x4e75, 'rte': 0x4e73, 'nop': 0x4e71, 'illegal': 0x4afc, 'rtr': 0x4e77, 'reset': 0x4e70}
        if mnem in simple:
            return self.out([simple[mnem]])

        if mnem in ('move', 'movea'):
            need(2)
            s, d = ops
            if s.kind in ('sr', 'ccr', 'usp') or d.kind in ('sr', 'ccr', 'usp'):
                if s.kind == 'sr':
                    eb, ext = self.eabits(d, 'w', 2); return self.out([0x40c0 | eb], ext)
                if d.kind == 'sr':
                    eb, ext = self.eabits(s, 'w', 2); return self.out([0x46c0 | eb], ext)
                if d.kind == 'ccr':
                    eb, ext = self.eabits(s, 'w', 2); return self.out([0x44c0 | eb], ext)
                raise AsmError('unsupported special move')
            sz = sz or 'w'
            code = {'b': 1, 'l': 2, 'w': 3}[sz]
            if d.kind == 'an' and sz == 'b': raise AsmError('move.b to address register')
            if s.kind == 'an' and sz == 'b': raise AsmError('move.b from address register')
            sm, sr, sext = self.ea(s, sz, 2)
            if d.kind in ('imm', 'pcdisp', 'pcindex'): raise AsmError('bad move destination')
            dm, dr, dext = self.ea(d, sz, 2 + len(sext))
            return self.out([(code << 12) | (dr << 9) | (dm << 6) | (sm << 3) | sr], sext, dext)

        if mnem == 'moveq':
            need(2); kinds(0, 'imm'); kinds(1, 'dn')
            v = self.eval(ops[0].expr).absolute()
            if self.final and not -128 <= v <= 255: raise AsmError('moveq out of range')
            if self.final and v > 127: raise AsmError('moveq value > 127 (use -%d)' % (256 - v))
            return self.out([0x7000 | (ops[1].reg << 9) | (v & 255)])

        if mnem == 'lea':
            need(2); kinds(1, 'an')
            eb, ext = self.eabits(ops[0], 'l', 2)
            return self.out([0x41c0 | (ops[1].reg << 9) | eb], ext)
        if mnem == 'pea':
            need(1); eb, ext = self.eabits(ops[0], 'l', 2)
            return self.out([0x4840 | eb], ext)
        if mnem in ('jmp', 'jsr'):
            need(1); eb, ext = self.eabits(ops[0], 'l', 2)
            return self.out([(0x4ec0 if mnem == 'jmp' else 0x4e80) | eb], ext)

        if mnem in ('clr', 'neg', 'not', 'tst', 'negx'):
            need(1)
            base = {'clr': 0x4200, 'neg': 0x4400, 'not': 0x4600, 'tst': 0x4a00, 'negx': 0x4000}[mnem]
            if ops[0].kind == 'an': raise AsmError('address register not allowed')
            eb, ext = self.eabits(ops[0], sz or 'w', 2)
            return self.out([base | (szc() << 6) | eb], ext)

        if mnem == 'ext':
            need(1); kinds(0, 'dn')
            return self.out([(0x48c0 if sz == 'l' else 0x4880) | ops[0].reg])
        if mnem == 'swap':
            need(1); kinds(0, 'dn'); return self.out([0x4840 | ops[0].reg])
        if mnem == 'exg':
            need(2)
            a, b = ops
            if a.kind == 'dn' and b.kind == 'dn': return self.out([0xc140 | (a.reg << 9) | b.reg])
            if a.kind == 'an' and b.kind == 'an': return self.out([0xc148 | (a.reg << 9) | b.reg])
            if a.kind == 'an' and b.kind == 'dn': a, b = b, a
            if a.kind == 'dn' and b.kind == 'an': return self.out([0xc188 | (a.reg << 9) | b.reg])
            raise AsmError('bad exg')
        if mnem == 'link':
            need(2); kinds(0, 'an'); kinds(1, 'imm')
            return self.out([0x4e50 | ops[0].reg, self.eval(ops[1].expr).absolute()])
        if mnem == 'unlk':
            need(1); kinds(0, 'an'); return self.out([0x4e58 | ops[0].reg])

        if mnem == 'movem':
            need(2)
            s, d = ops
            L = 1 if sz == 'l' else 0
            def mask_of(o):
                if o.kind == 'reglist': return o.mask
                if o.kind == 'dn': return 1 << o.reg
                if o.kind == 'an': return 1 << (8 + o.reg)
                return None
            ms = mask_of(s)
            if ms is not None and d.kind not in ('dn', 'an', 'reglist'):
                if d.kind == 'predec':
                    ms = int('{:016b}'.format(ms)[::-1], 2)
                elif d.kind in ('postinc', 'imm', 'pcdisp', 'pcindex'):
                    raise AsmError('bad movem destination')
                eb, ext = self.eabits(d, 'l', 4)
                return self.out([0x4880 | (L << 6) | eb, ms], ext)
            md = mask_of(d)
            if md is None or s.kind in ('predec',): raise AsmError('bad movem')
            eb, ext = self.eabits(s, 'l', 4)
            return self.out([0x4c80 | (L << 6) | eb, md], ext)

        if mnem in ('add', 'sub', 'and', 'or', 'cmp', 'eor', 'adda', 'suba', 'cmpa',
                    'addi', 'subi', 'andi', 'ori', 'cmpi', 'eori'):
            need(2)
            s, d = ops
            root = mnem.rstrip('ai') if mnem not in ('and', 'andi') else 'and'
            if mnem in ('adda', 'suba', 'cmpa'): root = mnem[:-1]
            if mnem in ('addi', 'subi', 'andi', 'ori', 'cmpi', 'eori'): root = mnem[:-1]
            if root == 'o': root = 'or'
            if root == 'eor' and mnem == 'eor': pass
            sz = sz or 'w'
            # to SR / CCR
            if d.kind in ('sr', 'ccr') and s.kind == 'imm' and root in ('and', 'or', 'eor'):
                base = {'and': 0x0200, 'or': 0x0000, 'eor': 0x0a00}[root]
                v = self.eval(s.expr).absolute()
                return self.out([base | (0x7c if d.kind == 'sr' else 0x3c), v & 0xffff])
            if d.kind == 'an' and root in ('add', 'sub', 'cmp'):
                if sz == 'b': raise AsmError('byte op on address register')
                base = {'add': 0xd000, 'sub': 0x9000, 'cmp': 0xb000}[root]
                eb, ext = self.eabits(s, sz, 2)
                return self.out([base | (d.reg << 9) | ((7 if sz == 'l' else 3) << 6) | eb], ext)
            if s.kind == 'imm' and not (d.kind == 'dn' and mnem in ('add', 'sub', 'and', 'or', 'cmp') and False):
                if root in ('add', 'sub') and mnem in ('add', 'sub'):
                    pass  # assemble as addi/subi (always correct, 68000 has no auto-quick here)
                base = {'add': 0x0600, 'sub': 0x0400, 'and': 0x0200, 'or': 0x0000, 'cmp': 0x0c00, 'eor': 0x0a00}[root]
                if d.kind in ('an', 'imm', 'pcdisp', 'pcindex') and root != 'cmp': raise AsmError('bad destination')
                if d.kind in ('an', 'imm'): raise AsmError('bad destination')
                m, r, iext = self.ea(s, sz, 2)
                eb, dext = self.eabits(d, sz, 2 + len(iext))
                return self.out([base | (SZ[sz] << 6) | eb], iext, dext)
            base = {'add': 0xd000, 'sub': 0x9000, 'and': 0xc000, 'or': 0x8000, 'cmp': 0xb000, 'eor': 0xb000}[root]
            if root == 'eor':
                if s.kind != 'dn': raise AsmError('eor source must be a data register')
                eb, ext = self.eabits(d, sz, 2)
                return self.out([0xb100 | (s.reg << 9) | (SZ[sz] << 6) | eb], ext)
            if d.kind == 'dn':
                if s.kind == 'an' and sz == 'b': raise AsmError('byte op from address register')
                if s.kind == 'an' and root in ('and', 'or'): raise AsmError('address register not allowed')
                eb, ext = self.eabits(s, sz, 2)
                return self.out([base | (d.reg << 9) | (SZ[sz] << 6) | eb], ext)
            if s.kind == 'dn' and root != 'cmp':
                eb, ext = self.eabits(d, sz, 2)
                return self.out([base | (s.reg << 9) | ((4 + SZ[sz]) << 6) | eb], ext)
            raise AsmError('bad operands for ' + mnem)

        if mnem in ('addq', 'subq'):
            need(2); kinds(0, 'imm')
            v = self.eval(ops[0].expr).absolute()
            if self.final and not 1 <= v <= 8: raise AsmError('quick value must be 1..8')
            sz = sz or 'w'
            if ops[1].kind == 'an' and sz == 'b': raise AsmError('byte op on address register')
            eb, ext = self.eabits(ops[1], sz, 2)
            return self.out([0x5000 | ((v & 7) << 9) | (0x100 if mnem == 'subq' else 0) | (SZ[sz] << 6) | eb], ext)

        if mnem in ('mulu', 'muls', 'divu', 'divs'):
            need(2); kinds(1, 'dn')
            if ops[0].kind == 'an': raise AsmError('address register not allowed')
            base = {'mulu': 0xc0c0, 'muls': 0xc1c0, 'divu': 0x80c0, 'divs': 0x81c0}[mnem]
            eb, ext = self.eabits(ops[0], 'w', 2)
            return self.out([base | (ops[1].reg << 9) | eb], ext)

        if mnem in ('btst', 'bchg', 'bclr', 'bset'):
            need(2)
            tt = {'btst': 0, 'bchg': 1, 'bclr': 2, 'bset': 3}[mnem]
            if ops[1].kind == 'an': raise AsmError('address register not allowed')
            if ops[0].kind == 'dn':
                eb, ext = self.eabits(ops[1], 'b', 2)
                return self.out([0x0100 | (ops[0].reg << 9) | (tt << 6) | eb], ext)
            kinds(0, 'imm')
            bit = self.eval(ops[0].expr).absolute()
            eb, ext = self.eabits(ops[1], 'b', 4)
            return self.out([0x0800 | (tt << 6) | eb, bit & 255], ext)

        if mnem in ('asl', 'asr', 'lsl', 'lsr', 'rol', 'ror', 'roxl', 'roxr'):
            tt = {'as': 0, 'ls': 1, 'rox': 2, 'ro': 3}[mnem[:-1]]
            dr = 1 if mnem.endswith('l') else 0
            if n == 1:
                eb, ext = self.eabits(ops[0], 'w', 2)
                return self.out([0xe0c0 | (tt << 9) | (dr << 8) | eb], ext)
            need(2); kinds(1, 'dn')
            sz = sz or 'w'
            if ops[0].kind == 'imm':
                c = self.eval(ops[0].expr).absolute()
                if self.final and not 1 <= c <= 8: raise AsmError('shift count must be 1..8')
                return self.out([0xe000 | ((c & 7) << 9) | (dr << 8) | (SZ[sz] << 6) | (tt << 3) | ops[1].reg])
            kinds(0, 'dn')
            return self.out([0xe020 | (ops[0].reg << 9) | (dr << 8) | (SZ[sz] << 6) | (tt << 3) | ops[1].reg])

        if mnem.startswith('db') and (mnem[2:] in COND or mnem == 'dbra'):
            need(2); kinds(0, 'dn')
            c = 1 if mnem == 'dbra' else COND[mnem[2:]]
            v = self.eval(split_operands(args)[1])
            d = v.v - (self.pc + 2)
            if self.final:
                if v.sec is not self.cur: raise AsmError('branch to another section')
                if not -32768 <= d <= 32767: raise AsmError('branch out of range')
            return self.out([0x50c8 | (c << 8) | ops[0].reg, d & 0xffff])

        if mnem == 'bra' or mnem == 'bsr' or (mnem[0] == 'b' and mnem[1:] in COND and mnem[1:] not in ('t', 'f')):
            need(1)
            c = 0 if mnem == 'bra' else 1 if mnem == 'bsr' else COND[mnem[1:]]
            v = self.eval(args)
            d = v.v - (self.pc + 2)
            if self.final and v.sec is not self.cur: raise AsmError('branch to another section')
            if sz == 's' or sz == 'b':
                if self.final and (not -128 <= d <= 127 or d == 0):
                    raise AsmError('short branch out of range (%d)' % d)
                return self.out([0x6000 | (c << 8) | (d & 255)])
            if self.final and not -32768 <= d <= 32767: raise AsmError('branch out of range')
            return self.out([0x6000 | (c << 8), d & 0xffff])

        if mnem[0] == 's' and mnem[1:] in COND:
            need(1)
            eb, ext = self.eabits(ops[0], 'b', 2)
            return self.out([0x50c0 | (COND[mnem[1:]] << 8) | eb], ext)

        raise AsmError('unknown instruction ' + mnem)

    # hunk file ---------------------------------------------------------------
    def hunkfile(self):
        secs = [s for s in self.sections if s.size > 0 or s.index == 0]
        idx = {id(s): i for i, s in enumerate(secs)}
        L = lambda v: struct.pack('>I', v & 0xffffffff)
        out = bytearray()
        out += L(0x3f3) + L(0) + L(len(secs)) + L(0) + L(len(secs) - 1)
        for s in secs:
            out += L(((s.size + 3) // 4) | (0x40000000 if s.chip else 0))
        for s in secs:
            nl = (s.size + 3) // 4
            if s.kind == 'bss':
                out += L(0x3eb) + L(nl)
            else:
                out += L(0x3e9 if s.kind == 'code' else 0x3ea) + L(nl)
                d = bytes(s.data) + bytes(nl * 4 - len(s.data))
                out += d
                # relocations add the target base to the stored offset
                if s.relocs:
                    out += L(0x3ec)
                    byt = {}
                    for off, tgt in s.relocs:
                        byt.setdefault(idx[id(tgt)], []).append(off)
                    for t, offs in sorted(byt.items()):
                        out += L(len(offs)) + L(t)
                        for o in sorted(offs): out += L(o)
                    out += L(0)
            out += L(0x3f2)
        return bytes(out)

    def raw(self):
        """Flat binary of the first section (for the bootblock); no relocations allowed."""
        s = self.sections[0]
        if s.relocs: raise AsmError('raw output cannot have relocations')
        return bytes(s.data)

    def symbol_map(self):
        out = ['#sections ' + ' '.join(s.name for s in self.sections if s.size > 0 or s.index == 0)]
        for n, v in sorted(self.syms.items(), key=lambda kv: (kv[1].sec.index if kv[1].sec else -1, kv[1].v)):
            if v.sec is not None:
                out.append('%-8s %08x %s' % (v.sec.name, v.v, n))
        return '\n'.join(out) + '\n'

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('-o', required=True)
    ap.add_argument('-raw', action='store_true', help='write a flat binary of the first section')
    ap.add_argument('-map'); ap.add_argument('-I', action='append', default=[])
    a = ap.parse_args()
    asm = Assembler(a.I)
    try:
        asm.run(a.src)
        data = asm.raw() if a.raw else asm.hunkfile()
    except AsmError as e:
        print('error: %s' % e, file=sys.stderr); sys.exit(1)
    open(a.o, 'wb').write(data)
    if a.map: open(a.map, 'w').write(asm.symbol_map())
    tot = sum(s.size for s in asm.sections)
    print('%s: %d bytes (%s)' % (a.o, len(data), ', '.join('%s %d%s' % (s.name, s.size, ' chip' if s.chip else '') for s in asm.sections)))

if __name__ == '__main__':
    main()
