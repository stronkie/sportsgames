set -e
cd "$(dirname "$0")/.."
mkdir -p build/gen
python3 tools/make_main.py build/gen >/dev/null
python3 tools/fixbranch.py src/kernel.s -I build/gen -I src -o build/SOlymp.game -map build/SOlymp.map
