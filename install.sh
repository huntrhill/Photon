#!/usr/bin/env bash
set -euo pipefail

echo "==> Python: $(command -v python3 || true)"
echo "==> Pip:    $(command -v pip3 || true)"

# 0) sanity
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python3 not found. Install Python 3 and retry." >&2
  exit 1
fi
python3 - <<'PY' || { echo "python3-venv not available. On Debian: sudo apt-get install -y python3-venv"; exit 1; }
import sys, venv
PY

# 1) venv + toolchain
if [ ! -d ".venv" ]; then
  echo "==> Creating virtual environment (.venv)…"
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel

# 2) requirements present?
if [ ! -f "requirements.txt" ]; then
  echo "requirements.txt not found." >&2
  exit 1
fi

# 3) bulk install
echo "==> Installing dependencies from requirements.txt…"
if ! pip install -r requirements.txt; then
  echo "⚠️  Bulk install failed — retrying each package individually…"
  # Parse package names (strip comments/extras)
  pkgs=$(python - <<'PY'
import re, sys
pat = re.compile(r'^\s*([A-Za-z0-9_.\-]+)')
for line in open("requirements.txt", encoding="utf-8"):
    s=line.strip()
    if not s or s.startswith("#"): continue
    m=pat.match(s)
    if m: print(m.group(1))
PY
)
  failed=()
  for p in $pkgs; do
    echo "➡ pip install $p"
    if ! pip install --no-cache-dir "$p"; then
      echo "   ↳ retrying $p with no-binary fallback (may attempt source build)…"
      if ! pip install --no-binary=:all: --no-cache-dir "$p"; then
        echo "   ❌ FAILED: $p"
        failed+=("$p")
      else
        echo "   ✅ OK (from source): $p"
      fi
    else
      echo "   ✅ OK: $p"
    fi
  done
  if [ "${#failed[@]}" -ne 0 ]; then
    echo ""
    echo "❌ Some packages failed to install:"
    for f in "${failed[@]}"; do echo "   - $f"; done
    echo "Tip: these may need system libs/wheels. Install OS deps or adjust versions, then rerun."
    exit 1
  fi
fi

# 4) validate imports
echo "==> Validating imports…"
python - <<'PY'
import sys, re

NAME_MAP = {
    'psycopg2-binary': ['psycopg2'],
    'python-dotenv'  : ['dotenv'],
    'pyqt5'          : ['PyQt5'],
    'pyqt6'          : ['PyQt6'],
    'pygame'         : ['pygame'],
    'qasync'         : ['qasync'],
}

def req_names(path="requirements.txt"):
    pkgs=[]
    pat=re.compile(r'^\s*([A-Za-z0-9_.\-]+)')
    with open(path,encoding="utf-8") as f:
        for line in f:
            s=line.strip()
            if not s or s.startswith("#"): continue
            m=pat.match(s)
            if m: pkgs.append(m.group(1))
    return pkgs

failed=[]
ok=[]
for raw in req_names():
    key=raw.lower()
    mods=NAME_MAP.get(key,[raw])
    last_err=None
    for m in mods:
        try:
            __import__(m)
            ok.append((raw,m))
            break
        except Exception as e:
            last_err=e
    else:
        failed.append((raw,mods,str(last_err)))

if failed:
    print("Validation FAILED:", file=sys.stderr)
    for pkg,mods,err in failed:
        print(f" - {pkg} -> tried {mods} -> {err}", file=sys.stderr)
    sys.exit(1)

print("Validation OK:")
for pkg,mod in ok:
    print(f" - {pkg} (import '{mod}')")
PY

echo ""
echo "✅ Install complete."
echo "To run:"
echo "  source .venv/bin/activate"
echo "  python3 main.py"
