#!/usr/bin/env python3
"""fixbranch.py - assemble; on 'short branch out of range' make that branch a word branch, repeat."""
import re, subprocess, sys
args = sys.argv[1:]
for _ in range(300):
    r = subprocess.run([sys.executable, 'tools/asm68k.py'] + args, capture_output=True, text=True)
    m = re.findall(r'([\w/.]+\.s):(\d+)', r.stderr)
    if 'short branch out of range' in r.stderr and m:
        f, ln = m[-1]; ln = int(ln)
        L = open(f).read().split('\n')
        L[ln - 1] = re.sub(r'\b(b\w\w|bra|bsr)\.s\b', r'\1', L[ln - 1], count=1)
        open(f, 'w').write('\n'.join(L)); continue
    print(r.stdout + r.stderr, end=''); sys.exit(r.returncode)
