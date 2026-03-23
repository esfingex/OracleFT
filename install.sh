#!/bin/bash
set -e

echo "🚀 Starting OracleFT Professional Installation..."

# 1. Base Checks
if [ "$EUID" -ne 0 ]; then
  echo "⚠️  Please run with sudo: sudo ./install.sh"
  exit 1
fi

TARGET_DIR="/opt/oracleft"
USER_NAME=$(logname || echo $SUDO_USER)

echo "📦 Creating application directory at $TARGET_DIR..."
mkdir -p "$TARGET_DIR"

echo "📂 Copying files..."
cp -r . "$TARGET_DIR/"
chown -R "$USER_NAME:$USER_NAME" "$TARGET_DIR"

echo "🐍 Setting up Virtual Environment in $TARGET_DIR..."
# Ensure we use the target directory's python
sudo -u "$USER_NAME" python3 -m venv "$TARGET_DIR/.venv" --system-site-packages
sudo -u "$USER_NAME" "$TARGET_DIR/.venv/bin/pip" install --upgrade pip
sudo -u "$USER_NAME" "$TARGET_DIR/.venv/bin/pip" install -r "$TARGET_DIR/requirements.txt"

echo "⚙️  Configuring System Services..."
# Delegate complex logic to manager.py install
sudo -u "$USER_NAME" "$TARGET_DIR/.venv/bin/python3" "$TARGET_DIR/manager.py" install

echo ""
echo "✅ OracleFT has been successfully installed in $TARGET_DIR"
echo "🌟 You can now launch the tray icon by running: oracleft-tray"
echo "   (Or simply restart your session to see it automatically)"

# Create a symlink in /usr/local/bin for easy access
ln -sf "$TARGET_DIR/.venv/bin/python3" /usr/local/bin/oracleft-python
ln -sf "$TARGET_DIR/manager.py" /usr/local/bin/oracleft
chmod +x "$TARGET_DIR/manager.py"

echo "🚀 Done! Your Oracle Instance Automator is now a system command: 'oracleft'"
