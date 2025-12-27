#!/usr/bin/env bash
set -e

# Set directories
APP_NAME="z13-led-gui"
BIN_DIR="$HOME/.local/bin"
ICON_DIR="$HOME/.local/share/icons/hicolor"
DESKTOP_DIR="$HOME/.local/share/applications"

echo "Installing $APP_NAME..."

# Create folders
mkdir -p "$BIN_DIR"
mkdir -p "$ICON_DIR/scalable/apps"
mkdir -p "$ICON_DIR/symbolic/apps"
mkdir -p "$DESKTOP_DIR"

# Install executable
install -m 755 gui.py "$BIN_DIR/z13-led-gui"

# Install icons
install -m 644 icons/rog.svg \
  "$ICON_DIR/scalable/apps/rog.svg"

install -m 644 icons/rog-symbolic.svg \
  "$ICON_DIR/symbolic/apps/rog-symbolic.svg"

# Install desktop entry
install -m 644 z13-led-gui.desktop \
  "$DESKTOP_DIR/z13-led-gui.desktop"

# Update icon cache if available
if command -v gtk-update-icon-cache >/dev/null; then
  gtk-update-icon-cache "$HOME/.local/share/icons/hicolor" || true
fi

echo "Installed successfully!"
echo "You can now run: z13-led-gui"
