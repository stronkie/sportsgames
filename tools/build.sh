#!/bin/sh
# Build Stronkie's Olympics:  sh tools/build.sh   (VER=0.1 by default)
# Needs python3 with Pillow and numpy.  The assembler, the disk tools and the emulator are in tools/.
#   tools/make_main.py      -> build/gen: the main program's screens, flags, sounds, music
#   tools/make_loading.py   -> build/gen/loadpic.*: the loading picture (and itch/cover*.png)
#   tools/ev_*.py           -> build/gen: the graphics and sounds of every event and the ceremonies
#   tools/asm68k.py         -> SOlymp (loader), SOlymp.game (kernel.s + main.s), *.evt (ev_*.s)
#   tools/make_disk.py      -> the ADFs (full game: 2 disks, demo: 1 disk) and the hard drive zips
#   tools/make_whdload.py   -> the WHDLoad versions (slave: src/whdload.s)
set -e
cd "$(dirname "$0")/.."
export VER=${VER:-0.1}
ASM="python3 tools/fixbranch.py"
mkdir -p build/gen build/full build/demo
for e in soccer basket volley bowling surf skate ceremony; do python3 tools/ev_$e.py build/gen; done
for e in soccer:Soccer basket:Basket volley:Volley bowling:Bowling surf:Surfing skate:Skate ceremony:Ceremony; do
  n=${e%%:*}; f=${e##*:}
  $ASM src/ev_$n.s -I build/gen -I src -o build/full/$f.evt -map build/$f.map
  cp build/full/$f.evt build/demo/$f.evt
done
for v in full demo; do
  if [ $v = demo ]; then export DEMO=1; else export DEMO=0; fi
  python3 tools/make_main.py build/gen
  python3 tools/make_loading.py build/gen
  $ASM src/kernel.s -I build/gen -I src -o build/$v/SOlymp.game -map build/$v/SOlymp.map
  $ASM src/loader.s -I build/gen -I src -o build/$v/SOlymp
done
cp build/full/SOlymp.map build/SOlymp.map; cp build/full/SOlymp.game build/SOlymp.game
mkdir -p build/disk; cp build/full/*.evt build/disk/
python3 tools/make_disk.py "$VER"
python3 tools/make_disk.py "$VER" demo
python3 tools/make_whdload.py "$VER"
python3 tools/make_whdload.py "$VER" demo
