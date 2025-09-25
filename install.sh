#!/usr/bin/env bash
set -euo pipefail

banner() { echo -e "\n\033[1;36m$*\033[0m"; }
warn()   { echo -e "\n\033[1;33m$*\033[0m"; }
die()    { echo -e "\n\033[1;31m$*\033[0m"; exit 1; }

banner "✓ Updating apt (requires sudo)…"
sudo apt-get update -y

banner "✓ Installing base system deps…"
sudo apt-get install -y \
  python3-venv python3-dev python3-pip \
  build-essential libpq-dev \
  libgl1 libglib2.0-0 libx11-xcb1 libxkbcommon-x11-0 \
  libpulse0 libasound2 \
  mpg123 git curl ca-certificates

# (Re)create venv — may be recreated later if we fall back to system PyQt5
if [ ! -d ".venv" ]; then
  banner "✓ Creating Python virtual environment (.venv)…"
  python3 -m venv .venv
fi

banner "✓ Activating venv & upgrading pip toolchain…"
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel

# Ensure requirements exist
if [ ! -f "requirements.txt" ]; then
  cat > requirements.txt <<'REQ'
PyQt5==5.15.11
psycopg2-binary==2.9.9
pygame==2.6.1
python-dotenv==1.0.1
REQ
fi

# Prefer binary wheels to avoid heavy source builds
export PIP_ONLY_BINARY=":all:"

banner "✓ Installing Python deps from requirements.txt (prefer wheels)…"
if ! pip install -r requirements.txt; then
  warn "⚠️ Bulk pip install failed — installing one by one with fallbacks…"

  # Track whether we had to fall back to system packages
  NEED_SYSTEM_PYQT5=0
  NEED_SYSTEM_PYGAME=0

  # ---- PyQt5 ----
  if ! pip install "PyQt5==5.15.11"; then
    warn "⚠️ PyQt5 wheel failed. Trying alternate wheel 5.15.10…"
    if ! pip install "PyQt5==5.15.10"; then
      warn "⚠️ PyQt5 wheels unavailable; falling back to Debian system PyQt5."
      NEED_SYSTEM_PYQT5=1
    fi
  fi

  # ---- pygame ----
  if ! pip install "pygame==2.6.1"; then
    warn "⚠️ pygame wheel failed; will try Debian system pygame."
    NEED_SYSTEM_PYGAME=1
  fi

  # ---- Remaining pure-python deps ----
  pip install "psycopg2-binary==2.9.9" "python-dotenv==1.0.1" || true

  # ---- System fallbacks (if needed) ----
  if [ "$NEED_SYSTEM_PYQT5" -eq 1 ]; then
    banner "✓ Installing Debian's PyQt5…"
    sudo apt-get install -y python3-pyqt5 python3-pyqt5.qtmultimedia
  fi

  if [ "$NEED_SYSTEM_PYGAME" -eq 1 ]; then
    banner "✓ Installing Debian's pygame…"
    sudo apt-get install -y python3-pygame
  fi

  # If we needed *any* system GUI/audio libs, rebuild venv to see system packages
  if [ "$NEED_SYSTEM_PYQT5" -eq 1 ] || [ "$NEED_SYSTEM_PYGAME" -eq 1 ]; then
    warn "⚠️ Recreating venv with --system-site-packages so Python sees system PyQt5/pygame…"
    deactivate || true
    rm -rf .venv
    python3 -m venv .venv --system-site-packages
    # shellcheck disable=SC1091
    source .venv/bin/activate
    python -m pip install --upgrade pip setuptools wheel
    # Re-install only the remaining pip deps (avoid re-pulling PyQt5/pygame)
    pip install "psycopg2-binary==2.9.9" "python-dotenv==1.0.1"
  fi
fi

banner "✓ Verifying imports…"
python - <<'PY'
try:
    import PyQt5, pygame, psycopg2
    print("Imports OK: PyQt5, pygame, psycopg2")
except Exception as e:
    raise SystemExit(f"Import check failed: {e}")
PY

banner "✅ Install complete!"
echo "To run:"
echo "  source .venv/bin/activate"
echo "  python3 main.py"
