#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  PixArchive — Linux / macOS build script
#  Run from the project root directory.
#
#  Requirements:
#    pip install pyinstaller gallery-dl PyQt6
#
#  Output:
#    dist/pixarchive/          ← portable folder
#    dist/pixarchive.tar.gz    ← portable tarball
#    dist/pixarchive.AppImage  ← AppImage (Linux only, if appimagetool found)
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC}  $*"; }
info() { echo -e "${BOLD}[INFO]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
fail() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

echo ""
echo -e "${BOLD} PixArchive — Build Script${NC}"
echo " ══════════════════════════════════"
echo ""

# ── Check Python ──────────────────────────────────────────────────────────────
python3 --version >/dev/null 2>&1 || fail "Python 3 not found."
ok "Python: $(python3 --version)"

# ── Check / install PyInstaller ───────────────────────────────────────────────
if ! pyinstaller --version >/dev/null 2>&1; then
    info "Installing PyInstaller..."
    pip install pyinstaller || fail "Failed to install PyInstaller."
fi
ok "PyInstaller: $(pyinstaller --version)"

# ── Download gallery-dl binary ────────────────────────────────────────────────
info "Downloading gallery-dl standalone binary..."
python3 download_gallery_dl.py || fail "Failed to download gallery-dl binary."

# ── Clean ─────────────────────────────────────────────────────────────────────
info "Cleaning previous build..."
rm -rf build dist

# ── Build ─────────────────────────────────────────────────────────────────────
info "Running PyInstaller..."
pyinstaller pixarchive.spec --noconfirm
ok "Build complete → dist/pixarchive/"

# ── Portable tarball ─────────────────────────────────────────────────────────
info "Creating portable tarball..."
cd dist
tar -czf pixarchive.tar.gz pixarchive/
cd ..
ok "Tarball → dist/pixarchive.tar.gz"

# ── AppImage (Linux only) ─────────────────────────────────────────────────────
if [[ "$(uname)" == "Linux" ]]; then
    if command -v appimagetool >/dev/null 2>&1; then
        info "Building AppImage..."

        # Create AppDir structure
        APPDIR="dist/pixarchive.AppDir"
        rm -rf "$APPDIR"
        mkdir -p "$APPDIR/usr/bin"
        cp -r dist/pixarchive/* "$APPDIR/usr/bin/"

        # AppRun entry point
        cat > "$APPDIR/AppRun" << 'APPRUN'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=$(dirname "$SELF")
exec "$HERE/usr/bin/pixarchive" "$@"
APPRUN
        chmod +x "$APPDIR/AppRun"

        # Desktop file
        cat > "$APPDIR/pixarchive.desktop" << 'DESKTOP'
[Desktop Entry]
Name=PixArchive
Comment=GUI for gallery-dl — download galleries from 100+ sites
Exec=pixarchive
Icon=pixarchive
Type=Application
Categories=Network;FileTransfer;
DESKTOP

        # Placeholder icon (replace with real .png for production)
        touch "$APPDIR/pixarchive.png"

        appimagetool "$APPDIR" dist/pixarchive.AppImage
        ok "AppImage → dist/pixarchive.AppImage"
    else
        warn "appimagetool not found — skipping AppImage."
        warn "Download from: https://github.com/AppImage/AppImageKit/releases"
    fi
fi

# ── macOS .app bundle (macOS only) ────────────────────────────────────────────
if [[ "$(uname)" == "Darwin" ]]; then
    info "Creating macOS DMG..."
    if command -v create-dmg >/dev/null 2>&1; then
        create-dmg \
            --volname "PixArchive" \
            --window-size 540 380 \
            --icon-size 128 \
            --app-drop-link 380 160 \
            "dist/pixarchive.dmg" \
            "dist/pixarchive/"
        ok "DMG → dist/pixarchive.dmg"
    else
        warn "create-dmg not found — skipping DMG."
        warn "Install with: brew install create-dmg"
    fi
fi

echo ""
echo -e "${BOLD} Build complete!${NC}"
echo " ──────────────────────────────────────────────────────"
echo "  Portable:  dist/pixarchive.tar.gz"
[[ -f "dist/pixarchive.AppImage" ]] && echo "  AppImage:  dist/pixarchive.AppImage"
[[ -f "dist/pixarchive.dmg"      ]] && echo "  DMG:       dist/pixarchive.dmg"
echo ""
