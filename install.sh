#!/usr/bin/env bash
set -euo pipefail

echo "==> Using Python: $(command -v python3 || true)"
echo "==> Using Pip:    $(command -v pip3 || true)"

# 1) Minimal system prerequisites (kept simple)
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python3 not found. Please install Python 3 first."
  exit 1
fi
if ! command -v python3 -m venv >/dev/null 2>&1; then
  echo "python3-venv not available. On Debian: sudo apt-get update && sudo apt-get install -y python3-venv"
  exit 1
fi

# 2) Create venv (if missing) and upgrade toolchain
if [ ! -d ".venv" ]; then
  echo "==> Creating virtual environment (.venv)…"
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel

# 3) Install requirements
if [ ! -f "requirements.txt" ]; then
  echo "requirements.txt not found in current directory."
  exit 1
fi

echo "==> Installing Python dependencies from requirements.txt…"
pip install -r requirements.txt

# 4) Validate imports (maps package names to import names)
python - <<'PY'
import sys, re

# Map package name -> import name(s)
NAME_MAP = {
    # common package -> module mappings
    'psycopg2-binary': ['psycopg2'],
    'python-dotenv':   ['dotenv'],
    'pyqt5':           ['PyQt5'],
    'pyqt6':           ['PyQt6'],
    'pygame':          ['pygame'],
    'qasync':          ['qasync'],
}

def parse_requirements(path="requirements.txt"):
    pkgs = []
    pat = re.compile(r'^\s*([A-Za-z0-9_.\-]+)')
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            s=line.strip()
            if not s or s.startswith('#'): 
                continue
            m = pat.match(s)
            if m:
                pkgs.append(m.group(1))
    return pkgs

failed = []
tested = []

for raw in parse_requirements():
    key = raw.lower()
    imports = NAME_MAP.get(key, [raw])  # default: try package name as import
    ok = False
    for mod in imports:
        try:
            __import__(mod)
            tested.append((raw, mod, "OK"))
            ok = True
            break
        except Exception as e:
            err = e
    if not ok:
        failed.append((raw, imports, str(err)))

if failed:
    print("\nValidation FAILED. The following imports could not be loaded:\n")
    for pkg, mods, err in failed:
        print(f" - package '{pkg}' -> tried imports {mods} -> error: {err}")
    sys.exit(1)

print("\nValidation OK. All required modules imported successfully:")
for pkg, mod, _ in tested:
    print(f" - {pkg} (import '{mod}')")
PY

echo ""
echo "✅ Install complete."
echo "To run:"
echo "  source .venv/bin/activate"
echo "  python3 main.py"
