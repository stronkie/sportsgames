# build the event files: sh tools/build_events.sh [names...]
set -e
cd "$(dirname "$0")/.."
mkdir -p build/gen build/disk
EVS=${*:-"soccer:Soccer basket:Basket volley:Volley bowling:Bowling surf:Surfing skate:Skate"}
for e in $EVS; do
  n=${e%%:*}; f=${e##*:}
  python3 tools/ev_$n.py build/gen >/dev/null
  python3 tools/fixbranch.py src/ev_$n.s -I build/gen -I src -o build/disk/$f.evt -map build/$f.map
done
