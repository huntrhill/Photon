#!/usr/bin/env bash
set -euo pipefail

echo "🔧 Updating apt..."
sudo apt-get update -y

echo "🔧 Installing system dependencies..."
sudo apt-get install -y \
    python3-venv \
    python3-dev \
    python3-pip \
    libpq-dev \
    mpg123 \
    git

# Create venv if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "🔧 Creating Python virtual environment..."
    python3 -m venv .venv
fi

echo "🔧 Activating virtual environment..."
source .venv/bin/activate

echo "🔧 Upgrading pip..."
pip install --upgrade pip

# Ensure requirements.txt exists
if [ ! -f "requirements.txt" ]; then
cat > requirements.txt <<'REQ'
PyQt5==5.15.11
psycopg2-binary==2.9.9
pygame==2.6.1
python-dotenv==1.0.1
REQ
fi

echo "🔧 Installing Python dependencies..."
pip install -r requirements.txt

echo "✅ Install complete!"
echo "➡ To run the project:"
echo "   source .venv/bin/activate"
echo "   python3 main.py"
