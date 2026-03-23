#!/bin/bash
set -e

echo "🚀 Starting Oracle Free Tier Instance Creation Setup..."

# Check for python3
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed."
    exit 1
fi

# Check for venv
if ! python3 -m venv --help &> /dev/null; then
    echo "❌ Error: python3-venv is missing."
    echo "Please install it: sudo apt install python3-venv"
    exit 1
fi

echo "📦 Creating virtual environment (.venv)..."
python3 -m venv .venv

echo "🛠️ Installing dependencies..."
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt

echo "✅ Setup complete!"
echo "You can now run: ./.venv/bin/python3 manager.py link-argos"
