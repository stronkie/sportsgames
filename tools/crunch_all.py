#!/usr/bin/env python3
"""crunch_all.py src_dir dst_dir file...  - crunches hunk files (tools/crunch.py) for the floppy
version, in parallel, and keeps the result while the input stays the same (dst/.cache)."""
import hashlib, os, sys
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crunch

def one(args):
    src, dst = args
    b = open(src, 'rb').read()
    h = hashlib.sha1(b + open(crunch.__file__, 'rb').read()).hexdigest()
    hf = dst + '.sha1'
    if os.path.exists(dst) and os.path.exists(hf) and open(hf).read() == h:
        return os.path.basename(src), len(b), os.path.getsize(dst), 'cached'
    pk = crunch.crunch_exe(b)[0]
    open(dst, 'wb').write(pk); open(hf, 'w').write(h)
    return os.path.basename(src), len(b), len(pk), 'packed'

if __name__ == '__main__':
    s, d = sys.argv[1], sys.argv[2]
    os.makedirs(d, exist_ok=True)
    jobs = sorted([(os.path.join(s, f), os.path.join(d, f)) for f in sys.argv[3:]], key=lambda j: -os.path.getsize(j[0]))
    with Pool() as p:
        for name, a, b, how in p.imap_unordered(one, jobs):
            print('crunch: %-16s %7d -> %7d  %s' % (name, a, b, how))
