#!/bin/bash
# Build script for GSlides AI macOS app
# Creates distributable .app for Intel and Apple Silicon Macs

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "======================================"
echo "  GSlides AI - macOS Build Script"
echo "======================================"
echo ""

# Build using PyInstaller
build_app() {
    local target_arch="${1:-}"
    
    echo "Building macOS app..."
    
    # Clean previous builds
    rm -rf build/GSlides\ AI dist/GSlides\ AI.app
    
    # Build with PyInstaller
    if [ -n "$target_arch" ]; then
        echo "Target architecture: $target_arch"
        pixi run pyinstaller gslides_ai.spec --noconfirm --target-arch "$target_arch"
    else
        pixi run pyinstaller gslides_ai.spec --noconfirm
    fi
    
    echo ""
    echo "✓ Build complete!"
    echo "Output: dist/GSlides AI.app"
}

# Create DMG for distribution
create_dmg() {
    local app_path="$1"
    local dmg_name="$2"
    
    if [ ! -d "$app_path" ]; then
        echo "Error: App not found at $app_path"
        exit 1
    fi
    
    echo "Creating DMG: $dmg_name..."
    
    # Create a temporary folder for DMG contents
    local dmg_temp="build/dmg_temp"
    rm -rf "$dmg_temp"
    mkdir -p "$dmg_temp"
    
    # Copy app to temp folder
    cp -R "$app_path" "$dmg_temp/"
    
    # Create symlink to Applications
    ln -s /Applications "$dmg_temp/Applications"
    
    # Create dist directory
    mkdir -p dist
    
    # Remove existing DMG if exists
    rm -f "dist/$dmg_name"
    
    # Create DMG
    hdiutil create -volname "GSlides AI" -srcfolder "$dmg_temp" -ov -format UDZO "dist/$dmg_name"
    
    # Cleanup
    rm -rf "$dmg_temp"
    
    echo "✓ Created dist/$dmg_name"
}

# Build for both architectures
build_universal() {
    echo "Building universal app (ARM64 + x86_64)..."
    echo ""
    
    # Build for ARM64
    echo "=== Building ARM64 (Apple Silicon) ==="
    build_app "arm64"
    mv "dist/GSlides AI.app" "dist/GSlides AI-arm64.app"
    
    # Build for x86_64
    echo ""
    echo "=== Building x86_64 (Intel) ==="
    build_app "x86_64"
    mv "dist/GSlides AI.app" "dist/GSlides AI-x86_64.app"
    
    echo ""
    echo "======================================"
    echo "  Universal Build Complete!"
    echo "======================================"
    echo ""
    echo "Output locations:"
    echo "  ARM64 (Apple Silicon): dist/GSlides AI-arm64.app"
    echo "  x86_64 (Intel):        dist/GSlides AI-x86_64.app"
    echo ""
}

# Main
case "${1:-native}" in
    "universal"|"both")
        build_universal
        ;;
    "arm64"|"arm")
        build_app "arm64"
        ;;
    "x86_64"|"intel")
        build_app "x86_64"
        ;;
    "native"|"")
        build_app
        ;;
    "dmg")
        mkdir -p dist
        if [ -d "dist/GSlides AI-arm64.app" ]; then
            create_dmg "dist/GSlides AI-arm64.app" "GSlides-AI-AppleSilicon.dmg"
        fi
        if [ -d "dist/GSlides AI-x86_64.app" ]; then
            create_dmg "dist/GSlides AI-x86_64.app" "GSlides-AI-Intel.dmg"
        fi
        if [ -d "dist/GSlides AI.app" ]; then
            create_dmg "dist/GSlides AI.app" "GSlides-AI.dmg"
        fi
        echo ""
        echo "DMG files created in dist/"
        ls -la dist/*.dmg 2>/dev/null || echo "No DMG files found"
        ;;
    "clean")
        echo "Cleaning build artifacts..."
        rm -rf build dist *.spec.bak
        echo "✓ Clean complete"
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  native     Build for current architecture (default)"
        echo "  universal  Build for both ARM64 and x86_64"
        echo "  arm64      Build for Apple Silicon only"
        echo "  x86_64     Build for Intel only"
        echo "  dmg        Create DMG files for distribution"
        echo "  clean      Remove build artifacts"
        echo "  help       Show this help message"
        echo ""
        ;;
    *)
        echo "Unknown command: $1"
        echo "Run '$0 help' for usage information."
        exit 1
        ;;
esac
