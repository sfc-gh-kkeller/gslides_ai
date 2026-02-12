#!/bin/bash
# Create a DMG installer for GSlides AI
# Usage: ./create_dmg.sh [arm64|intel]

set -e

APP_NAME="GSlides AI"
DMG_NAME="GSlides-AI-Installer"
VERSION="1.0.0"

ARCH="${1:-arm64}"
APP_DIR="dist/${ARCH}"
APP_PATH="${APP_DIR}/${APP_NAME}.app"

if [ ! -d "$APP_PATH" ]; then
    echo "Error: App not found at $APP_PATH"
    echo "Build the app first with: pixi run pyinstaller gslides_ai.spec --distpath dist/${ARCH}"
    exit 1
fi

# Create temp directory for DMG contents
DMG_DIR="$(mktemp -d)"
trap "rm -rf '$DMG_DIR'" EXIT

# Copy app to DMG directory
echo "Copying app to DMG staging area..."
cp -R "$APP_PATH" "$DMG_DIR/"

# Create symbolic link to Applications folder
ln -s /Applications "$DMG_DIR/Applications"

# Create DMG
echo "Creating DMG..."
DMG_PATH="dist/${DMG_NAME}-${VERSION}-${ARCH}.dmg"
mkdir -p dist

# Remove old DMG if exists
rm -f "$DMG_PATH"

# Create DMG with hdiutil using a temp file first
TEMP_DMG="$(mktemp).dmg"
hdiutil create -volname "$APP_NAME" \
    -srcfolder "$DMG_DIR" \
    -ov -format UDRW \
    "$TEMP_DMG"

# Convert to compressed format
hdiutil convert "$TEMP_DMG" -format UDZO -o "$DMG_PATH"
rm -f "$TEMP_DMG"

echo ""
echo "DMG created: $DMG_PATH"
echo ""
echo "Size: $(du -h "$DMG_PATH" | cut -f1)"

# Also create a zip for direct download
echo ""
echo "Creating zip archive..."
ZIP_PATH="dist/GSlides-AI-macOS-${ARCH}.zip"
rm -f "$ZIP_PATH"
cd "$APP_DIR" && zip -r -q "../../$ZIP_PATH" "${APP_NAME}.app" -x "*.DS_Store"
cd - > /dev/null

echo "ZIP created: $ZIP_PATH"
echo "Size: $(du -h "$ZIP_PATH" | cut -f1)"
