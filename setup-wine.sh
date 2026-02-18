#!/usr/bin/env bash
# =============================================================================
# ReadToMe-TTS — One-time build environment setup
# =============================================================================
#
# Installs everything needed to cross-compile a Windows .exe from Linux:
#   1. Wine (via apt, requires sudo)
#   2. Wine prefix initialization
#   3. Windows Python 3.12 (inside Wine)
#   4. All pip dependencies + PyInstaller (inside Wine)
#   5. Inno Setup compiler (inside Wine)
#   6. Model files (downloaded if missing)
#
# Run once. After this, use build-linux.sh for subsequent builds.
#
# Usage:
#   chmod +x setup-wine.sh
#   ./setup-wine.sh
#
set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────────────
PYTHON_VERSION="3.12.8"
PYTHON_EMBED_URL="https://www.python.org/ftp/python/${PYTHON_VERSION}/python-${PYTHON_VERSION}-embed-amd64.zip"
GET_PIP_URL="https://bootstrap.pypa.io/get-pip.py"
INNO_SETUP_VERSION="6.4.3"
INNO_SETUP_URL="https://files.jrsoftware.org/is/6/innosetup-${INNO_SETUP_VERSION}.exe"

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
WINEPREFIX="${HOME}/.wine-readtome"
# Python installed via embeddable zip into the Wine C: drive
PYTHON_DIR="${WINEPREFIX}/drive_c/Python312"
WINE_PYTHON="C:\\Python312\\python.exe"
WINE_PIP="C:\\Python312\\Scripts\\pip.exe"
WINE_ISCC="C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe"

PIPER_VOICES_BASE="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US"
# Voices bundled with the installer
BUNDLED_VOICES=("amy" "kristin" "kusal" "ryan")

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
echo -e "${CYAN} ReadToMe-TTS — Build Environment Setup${NC}"
echo -e "${CYAN}============================================${NC}"

cd "$PROJECT_DIR"

# ── Step 0: Check for xvfb ────────────────────────────────────────────────
if [ -z "$DISPLAY" ] && ! command -v xvfb-run &>/dev/null; then
    fail "No display and xvfb not installed. Install it first:

    sudo apt-get install -y xvfb"
fi

# ── Step 1: Install Wine ──────────────────────────────────────────────────
step "Installing Wine..."
if command -v wine64 &>/dev/null || command -v wine &>/dev/null; then
    ok "Wine already installed: $(wine64 --version 2>/dev/null || wine --version 2>/dev/null)"
else
    echo "    Wine not found — installing via apt (requires sudo)..."
    sudo dpkg --add-architecture i386
    sudo mkdir -pm755 /etc/apt/keyrings
    sudo wget -O /etc/apt/keyrings/winehq-archive.key https://dl.winehq.org/wine-builds/winehq.key
    CODENAME=$(lsb_release -cs)
    sudo wget -NP /etc/apt/sources.list.d/ \
        "https://dl.winehq.org/wine-builds/ubuntu/dists/${CODENAME}/winehq-${CODENAME}.sources" 2>/dev/null || true
    sudo apt-get update -qq
    sudo apt-get install -y --install-recommends winehq-stable
    ok "Wine installed: $(wine64 --version 2>/dev/null || wine --version 2>/dev/null)"
fi

# ── Step 2: Initialize Wine prefix ────────────────────────────────────────
step "Initializing Wine prefix at ~/.wine-readtome/..."
if [ ! -d "$WINEPREFIX" ]; then
    wineboot --init 2>/dev/null
    wineserver --wait 2>/dev/null || true
    ok "Wine prefix created"
else
    ok "Wine prefix already exists"
fi

# ── Step 3: Install Windows Python (embeddable zip) ───────────────────────
step "Installing Windows Python ${PYTHON_VERSION}..."
if wine_run "$WINE_PYTHON" --version &>/dev/null; then
    ok "Already installed: $(wine_run "$WINE_PYTHON" --version 2>&1)"
else
    PYTHON_ZIP="/tmp/python-${PYTHON_VERSION}-embed-amd64.zip"
    if [ ! -f "$PYTHON_ZIP" ]; then
        echo "    Downloading Python ${PYTHON_VERSION} embeddable zip..."
        wget -q --show-progress -O "$PYTHON_ZIP" "$PYTHON_EMBED_URL"
    fi
    echo "    Extracting to ${PYTHON_DIR}..."
    mkdir -p "$PYTHON_DIR"
    python3 -c "import zipfile; zipfile.ZipFile('$PYTHON_ZIP').extractall('$PYTHON_DIR')"

    # Enable pip: uncomment "import site" in python312._pth
    PTH_FILE="${PYTHON_DIR}/python312._pth"
    if [ -f "$PTH_FILE" ]; then
        sed -i 's/^#import site/import site/' "$PTH_FILE"
        # Also add Lib\site-packages so pip-installed packages are found
        if ! grep -q "Lib\\\\site-packages" "$PTH_FILE"; then
            echo "Lib\\site-packages" >> "$PTH_FILE"
        fi
    fi

    # Install pip via get-pip.py
    GET_PIP="/tmp/get-pip.py"
    if [ ! -f "$GET_PIP" ]; then
        echo "    Downloading get-pip.py..."
        wget -q -O "$GET_PIP" "$GET_PIP_URL"
    fi
    echo "    Installing pip..."
    wine_run "$WINE_PYTHON" "Z:\\tmp\\get-pip.py" --no-warn-script-location 2>&1 | tail -3
    wineserver --wait 2>/dev/null || true

    ok "Python ${PYTHON_VERSION} installed"
fi

# Verify
wine_run "$WINE_PYTHON" -c "import sys; print(f'    Python {sys.version} on {sys.platform}')" \
    || fail "Python installation broken"

# ── Step 4: Install pip dependencies + PyInstaller ────────────────────────
step "Installing Python packages (pip)..."
echo "    This may take a few minutes on first run..."
wine_run "$WINE_PYTHON" -m pip install \
    piper-tts \
    sounddevice \
    keyboard \
    pyperclip \
    pystray \
    Pillow \
    numpy \
    pyinstaller \
    --no-warn-script-location \
    2>&1 | tail -5
ok "All pip packages installed"

# ── Step 5: Install Inno Setup ────────────────────────────────────────────
step "Installing Inno Setup ${INNO_SETUP_VERSION}..."
if wine_run "$WINE_ISCC" /? &>/dev/null; then
    ok "Inno Setup already installed"
else
    INNO_INSTALLER="/tmp/innosetup-${INNO_SETUP_VERSION}.exe"
    if [ ! -f "$INNO_INSTALLER" ]; then
        echo "    Downloading Inno Setup..."
        wget -q --show-progress -O "$INNO_INSTALLER" "$INNO_SETUP_URL"
    fi
    echo "    Running Inno Setup installer (silent)..."
    wine_run "$INNO_INSTALLER" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
    wineserver --wait 2>/dev/null || true
    ok "Inno Setup installed"
fi

# ── Step 6: Download model files ──────────────────────────────────────────
step "Downloading bundled Piper voice models..."
mkdir -p models

for voice in "${BUNDLED_VOICES[@]}"; do
    onnx_file="en_US-${voice}-medium.onnx"
    json_file="en_US-${voice}-medium.onnx.json"
    onnx_url="${PIPER_VOICES_BASE}/${voice}/medium/${onnx_file}"
    json_url="${PIPER_VOICES_BASE}/${voice}/medium/${json_file}"

    if [ -f "models/${onnx_file}" ] && [ -f "models/${json_file}" ]; then
        ok "${voice}: already downloaded"
        continue
    fi

    echo "    Downloading ${voice}..."
    if [ ! -f "models/${json_file}" ]; then
        wget -q -O "models/${json_file}" "$json_url"
    fi
    if [ ! -f "models/${onnx_file}" ]; then
        wget -q --show-progress -O "models/${onnx_file}" "$onnx_url"
    fi
    ok "${voice}: downloaded"
done

echo "    Run ./download-voices.sh to get additional voices."

# ── Done ──────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN} Setup complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "  Build environment is ready. Now run:"
echo ""
echo -e "    ${CYAN}./build-linux.sh${NC}"
echo ""
echo "  to compile the Windows installer."
echo ""
