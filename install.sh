#!/usr/bin/env bash
set -euo pipefail

echo "==> Python: $(command -v python3 || true)"
echo "==> Pip:    $(command -v pip3 || true)"

# --- sanity ---------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python3 not found. Install Python 3 and retry." >&2
  exit 1
fi
python3 - <<'PY' || { echo "python3-venv not available. On Debian: sudo apt-get install -y python3-venv"; exit 1; }
import venv
PY

# --- venv & tooling -------------------------------------------------
if [ ! -d ".venv" ]; then
  echo "==> Creating virtual environment (.venv)…"
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel

# --- requirements present? -----------------------------------------
if [ ! -f "requirements.txt" ]; then
  echo "requirements.txt not found." >&2
  exit 1
fi

# We prefer wheels to avoid building heavy things from source
export PIP_ONLY_BINARY=":all:"

# --- bulk install ---------------------------------------------------
echo "==> Installing dependencies from requirements.txt…"
bulk_ok=1
if ! pip install -r requirements.txt; then
  bulk_ok=0
  echo "Bulk install failed — retrying each package individually…"
fi

# --- retry individually if needed ----------------------------------
need_system_pyqt5=0
if [ "$bulk_ok" -eq 0 ]; then
  # Parse package names (keep pins, strip comments)
  mapfile -t pkgs < <(python - <<'PY'
import re
pat = re.compile(r'^\s*([A-Za-z0-9_.\-]+(?:\[.*?\])?(?:==[^;#\s]+)?)')
with open("requirements.txt", encoding="utf-8") as f:
    for line in f:
        s=line.strip()
        if not s or s.startswith("#"): continue
        m=pat.match(s)
        if m: print(m.group(1))
PY
)
  failed=()
  for p in "${pkgs[@]}"; do
    name_lc="$(echo "$p" | tr '[:upper:]' '[:lower:]')"
    echo "➡ pip install $p"
    if ! pip install --no-cache-dir "$p"; then
      # Special handling for PyQt5 (pip wheels often unavailable on school VMs)
      if [[ "$name_lc" == pyqt5* ]]; then
        echo "   ↳ PyQt5 via pip failed; will try Debian system package."
        need_system_pyqt5=1
        continue
      fi
      echo "   ↳ retrying $p with no-binary (source build)…"
      if ! pip install --no-binary=:all: --no-cache-dir "$p"; then
        echo "   FAILED: $p"
        failed+=("$p")
      else
        echo "   OK (from source): $p"
      fi
    else
      echo "   OK: $p"
    fi
  done

  # If PyQt5 needed, install system package and rebuild venv to see it
  if [ "$need_system_pyqt5" -eq 1 ]; then
    echo "==> Installing Debian's PyQt5 (requires sudo)…"
    sudo apt-get update -y
    sudo apt-get install -y python3-pyqt5 python3-pyqt5.qtmultimedia

    echo "==> Recreating venv with --system-site-packages so PyQt5 is visible…"
    deactivate || true
    rm -rf .venv
    python3 -m venv .venv --system-site-packages
    # shellcheck disable=SC1091
    source .venv/bin/activate
    python -m pip install --upgrade pip setuptools wheel

    # Reinstall remaining requirements EXCEPT PyQt5 (now provided by system)
    echo "==> Reinstalling remaining pip packages (excluding PyQt5)…"
    python - <<'PY'
import re, subprocess, sys
pat = re.compile(r'^\s*([A-Za-z0-9_.\-]+)')
keep = []
with open("requirements.txt", encoding="utf-8") as f:
    for line in f:
        s=line.strip()
        if not s or s.startswith("#"): continue
        name = pat.match(s).group(1).lower()
        if name == "pyqt5":  # skip, provided by system
            continue
        keep.append(s)
if keep:
    subprocess.check_call([sys.executable, "-m", "pip", "install", *keep])
PY
  fi

  if [ "${#failed[@]}" -ne 0 ]; then
    echo ""
    echo "Some packages failed to install:"
    for f in "${failed[@]}"; do echo "   - $f"; done
    echo "Tip: these may need OS libs or different pins. Install OS deps or adjust versions, then rerun."
    exit 1
  fi
fi

# --- validation (import check) -------------------------------------
echo "==> Validating imports…"
python - <<'PY'
import sys, re

NAME_MAP = {
    'psycopg2-binary': ['psycopg2'],
    'python-dotenv'  : ['dotenv'],
    'pyqt5'          : ['PyQt5'],
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
            if m: pkgs.append(m.group(1).lower())
    return pkgs

failed=[]
ok=[]
for raw in req_names():
    mods = NAME_MAP.get(raw, [raw])
    last_err=None
    for m in mods:
        try:
            __import__(m)
            ok.append((raw,m))
            break
        except Exception as e:
            last_err=e
    else:
        # If PyQt5 not in requirements but we installed system PyQt5, still test it
        failed.append((raw,mods,str(last_err)))

# If PyQt5 was NOT listed (because we skipped), still verify it's importable
try:
    import PyQt5  # noqa
    ok.append(("pyqt5(system)", "PyQt5"))
except Exception as e:
    pass

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
echo "Install complete."
echo "To run:"
echo "  source .venv/bin/activate"
echo "  python3 main.py"
