#!/usr/bin/env bash
set -euo pipefail

echo "🔧 Updating apt..."
sudo apt-get update -y

echo "🔧 Installing system dependencies..."
# Build tools + headers for any source builds
sudo apt-get install -y \
    python3-venv python3-dev python3-pip \
    build-essential \
    libpq-dev \
    # Qt/GL/audio libs commonly needed at runtime for PyQt5/pygame
    libgl1 \
    libglib2.0-0 \
    libx11-xcb1 \
    libxkbcommon-x11-0 \
    libpulse0 \
    libasound2 \
    mpg123 \
    git

# Create venv if it doesn't exist
if [ ! -d ".venv" ]; then
  echo "🔧 Creating Python virtual environment..."
  python3 -m venv .venv
fi

echo "🔧 Activating virtual environment..."
# shellcheck disable=SC1091
source .venv/bin/activate

echo "🔧 Upgrading pip toolchain..."
python -m pip install --upgrade pip setuptools wheel

# Ensure requirements.txt exists (keep your pinned list)
if [ ! -f "requirements.txt" ]; then
cat > requirements.txt <<'REQ'
PyQt5==5.15.11
psycopg2-binary==2.9.9
pygame==2.6.1
python-dotenv==1.0.1
REQ
fi

# Prefer binary wheels for problematic packages (avoid building from source)
export PIP_ONLY_BINARY=":all:"

echo "🔧 Installing Python dependencies (prefer wheels)..."
# Try the whole file first
if ! pip install -r requirements.txt; then
  echo "⚠️  Bulk install failed — installing packages one by one for better diagnostics..."
  # Install one-by-one so we can see exactly which one fails and apply a fallback
  for pkg in PyQt5==5.15.11 psycopg2-binary==2.9.9 pygame==2.6.1 python-dotenv==1.0.1; do
    echo "➡ Installing $pkg ..."
    if ! pip install "$pkg"; then
      echo "❌ $pkg failed with wheels-only. Attempting source build with toolchain..."
      # Allow source build for this package only
      PIP_ONLY_BINARY="" pip install --no-binary=:all: "$pkg"
    fi
  done
fi

echo "✅ Install complete!"
echo "➡ To run the project:"
echo "   source .venv/bin/activate"
echo "   python3 main.py"
