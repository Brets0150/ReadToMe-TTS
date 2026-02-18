#!/usr/bin/env bash
# =============================================================================
# ReadToMe-TTS — Build Windows installer from Linux
# =============================================================================
#
# Compiles the project into a Windows .exe and installer using the Wine-based
# build environment created by setup-wine.sh.
#
# Usage:
#   ./build-linux.sh
#
# Prerequisites:
#   Run setup-wine.sh first (one-time).
#
# Output:
#   dist/ReadToMe/ReadToMe.exe              — Portable Windows app
#   dist/installer/ReadToMe_Setup_0.2.0.exe — Windows installer
#
set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────────────
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
WINEPREFIX="${HOME}/.wine-readtome"
WINE_PYTHON="C:\\Python312\\python.exe"
WINE_ISCC="C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe"

export WINEPREFIX
export WINEDEBUG="-all"
export WINEARCH="win64"

# ── Helpers ────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

step_num=0
step() {
    step_num=$((step_num + 1))
    echo -e "\n${CYAN}[${step_num}] $1${NC}"
}

ok()   { echo -e "    ${GREEN}✓ $1${NC}"; }
warn() { echo -e "    ${YELLOW}⚠ $1${NC}"; }
fail() { echo -e "    ${RED}✗ $1${NC}"; exit 1; }

wine_run() {
    local wine_cmd=""
    if command -v wine64 &>/dev/null; then
        wine_cmd="wine64"
    elif command -v wine &>/dev/null; then
        wine_cmd="wine"
    else
        echo "ERROR: wine not found" >&2; return 1
    fi
    if [ -z "${DISPLAY:-}" ] && command -v xvfb-run &>/dev/null; then
        xvfb-run -a "$wine_cmd" "$@" 2>/dev/null
    else
        "$wine_cmd" "$@" 2>/dev/null
    fi
}

# ── Start ──────────────────────────────────────────────────────────────────
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN} ReadToMe-TTS — Build Windows Installer${NC}"
echo -e "${CYAN}============================================${NC}"

cd "$PROJECT_DIR"

# ── Pre-flight checks ─────────────────────────────────────────────────────
step "Checking build environment..."

if ! command -v wine64 &>/dev/null && ! command -v wine &>/dev/null; then
    fail "Wine is not installed. Run setup-wine.sh first."
fi
ok "Wine found"

if [ ! -d "$WINEPREFIX" ]; then
    fail "Wine prefix not found at ~/.wine-readtome/. Run setup-wine.sh first."
fi
ok "Wine prefix exists"

if ! wine_run "$WINE_PYTHON" --version &>/dev/null; then
    fail "Windows Python not found in Wine. Run setup-wine.sh first."
fi
ok "Windows Python: $(wine_run "$WINE_PYTHON" --version 2>&1)"

if ! ls models/en_US-*.onnx &>/dev/null; then
    fail "No Piper voice models in models/. Run ./download-voices.sh first."
fi
ok "Piper voice model(s) present"

# ── Clean previous builds ─────────────────────────────────────────────────
step "Cleaning previous builds..."
rm -rf dist build
ok "Clean"

# ── Copy to local filesystem for speed ────────────────────────────────────
# Wine + PyInstaller is extremely slow on network/SMB mounts.
# We copy source files to /tmp, build there, then copy results back.
BUILD_TMP="/tmp/readtome-build-$$"
step "Preparing build workspace..."
rm -rf "$BUILD_TMP"
mkdir -p "$BUILD_TMP"
cp -r readtome models readtome.spec installer "$BUILD_TMP/"
ok "Copied source to $BUILD_TMP"

# ── Run PyInstaller ────────────────────────────────────────────────────────
step "Running PyInstaller (this takes a few minutes)..."
(cd "$BUILD_TMP" && wine_run "$WINE_PYTHON" -m PyInstaller readtome.spec --noconfirm) \
    || fail "PyInstaller build failed"

if [ -f "$BUILD_TMP/dist/ReadToMe/ReadToMe.exe" ]; then
    ok "Build complete: ReadToMe.exe"
    echo "    Size: $(du -sh "$BUILD_TMP/dist/ReadToMe/" | cut -f1) total"
else
    fail "ReadToMe.exe not found in build output"
fi

# ── Run Inno Setup ─────────────────────────────────────────────────────────
step "Building Windows installer with Inno Setup..."
mkdir -p "$BUILD_TMP/dist/installer"

(cd "$BUILD_TMP" && wine_run "$WINE_ISCC" "installer\\ReadToMe_Setup.iss") \
    || fail "Inno Setup compilation failed"

if [ -f "$BUILD_TMP/dist/installer/ReadToMe_Setup_0.2.0.exe" ]; then
    ok "Installer built successfully"
else
    fail "Installer .exe not found in build output"
fi

# ── Copy results back ─────────────────────────────────────────────────────
step "Copying build output to project directory..."
cp -r "$BUILD_TMP/dist" "$PROJECT_DIR/"
rm -rf "$BUILD_TMP"

INSTALLER_EXE="dist/installer/ReadToMe_Setup_0.2.0.exe"
ok "Portable app:  dist/ReadToMe/ReadToMe.exe ($(du -h dist/ReadToMe/ReadToMe.exe | cut -f1))"
ok "Installer:     ${INSTALLER_EXE} ($(du -h "$INSTALLER_EXE" | cut -f1))"

# ── Done ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN} Build complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "  Portable app:  ${CYAN}dist/ReadToMe/ReadToMe.exe${NC}"
echo -e "  Installer:     ${CYAN}${INSTALLER_EXE}${NC}"
echo ""
echo "  Copy the installer to a Windows machine and run it."
echo ""
