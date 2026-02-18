#!/usr/bin/env bash
# =============================================================================
# ReadToMe-TTS - Developer Setup & Launch
# =============================================================================
#
# Complete developer setup script. Creates a virtual environment, installs all
# dependencies (including build tools), downloads the 4 bundled voice models,
# and launches ReadToMe in debug mode.
#
# After running this script once, you can:
#   - Run the app:       .venv/bin/python -m readtome --debug
#   - Build installer:   ./build-linux.sh  (cross-compile via Wine)
#   - Download all 20+   ./download-voices.sh
#     US English voices
#
# Usage:
#   chmod +x run-dev.sh
#   ./run-dev.sh                # Full setup + launch in debug mode
#   ./run-dev.sh --no-launch    # Setup only, don't launch the app
#
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="${PROJECT_DIR}/.venv"
MODELS_DIR="${PROJECT_DIR}/models"

# The 4 bundled voices (medium quality)
BUNDLED_VOICES=("amy" "kristin" "kusal" "ryan")
QUALITY="medium"
BASE_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US"

# ── Colors ───────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
WHITE='\033[1;37m'
NC='\033[0m'

# ── Parse arguments ──────────────────────────────────────────────────────
NO_LAUNCH=false
for arg in "$@"; do
    case "$arg" in
        --no-launch) NO_LAUNCH=true ;;
    esac
done

STEP_COUNT=4
if $NO_LAUNCH; then
    STEP_COUNT=3
fi

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN} ReadToMe-TTS - Developer Setup${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

# ── Step 1: Create virtual environment ────────────────────────────────────
step=1
if [ ! -f "${VENV_DIR}/bin/python" ]; then
    echo -e "${YELLOW}[${step}/${STEP_COUNT}] Creating virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}      Created: ${VENV_DIR}${NC}"
else
    echo -e "${GREEN}[${step}/${STEP_COUNT}] Virtual environment exists${NC}"
fi

# ── Step 2: Install all dependencies (including dev/build tools) ──────────
step=2
echo -e "${YELLOW}[${step}/${STEP_COUNT}] Installing dependencies...${NC}"
"${VENV_DIR}/bin/pip" install -e ".[dev]" --quiet 2>/dev/null || {
    echo -e "${YELLOW}      Retrying with verbose output...${NC}"
    "${VENV_DIR}/bin/pip" install -e ".[dev]"
}
echo -e "${GREEN}      All packages installed (piper-tts, sounddevice, pyinstaller, etc.)${NC}"

# ── Step 3: Download the 4 bundled voice models ──────────────────────────
step=3
mkdir -p "$MODELS_DIR"

all_present=true
for voice in "${BUNDLED_VOICES[@]}"; do
    filename="en_US-${voice}-${QUALITY}"
    if [ ! -f "${MODELS_DIR}/${filename}.onnx" ] || [ ! -f "${MODELS_DIR}/${filename}.onnx.json" ]; then
        all_present=false
        break
    fi
done

if $all_present; then
    voice_list=$(IFS=", "; echo "${BUNDLED_VOICES[*]}")
    echo -e "${GREEN}[${step}/${STEP_COUNT}] All 4 bundled voices present (${voice_list})${NC}"
else
    echo -e "${YELLOW}[${step}/${STEP_COUNT}] Downloading bundled voice models...${NC}"
    for voice in "${BUNDLED_VOICES[@]}"; do
        filename="en_US-${voice}-${QUALITY}"
        onnx_file="${filename}.onnx"
        json_file="${filename}.onnx.json"
        onnx_path="${MODELS_DIR}/${onnx_file}"
        json_path="${MODELS_DIR}/${json_file}"

        if [ -f "$onnx_path" ] && [ -f "$json_path" ]; then
            echo -e "      ${GRAY}[SKIP] ${filename} (already downloaded)${NC}"
            continue
        fi

        voice_url="${BASE_URL}/${voice}/${QUALITY}"
        echo -ne "      ${YELLOW}[DOWN] ${filename} ...${NC}"

        # Download JSON config
        if [ ! -f "$json_path" ]; then
            if ! wget -q -O "$json_path" "${voice_url}/${json_file}" 2>/dev/null && \
               ! curl -sL -o "$json_path" "${voice_url}/${json_file}" 2>/dev/null; then
                echo -e "\r      ${RED}[FAIL] ${filename} - download error${NC}                    "
                rm -f "$onnx_path" "$json_path"
                continue
            fi
        fi

        # Download ONNX model
        if [ ! -f "$onnx_path" ]; then
            if ! wget -q --show-progress -O "$onnx_path" "${voice_url}/${onnx_file}" 2>/dev/null && \
               ! curl -L --progress-bar -o "$onnx_path" "${voice_url}/${onnx_file}" 2>/dev/null; then
                echo -e "\r      ${RED}[FAIL] ${filename} - download error${NC}                    "
                rm -f "$onnx_path" "$json_path"
                continue
            fi
        fi

        echo -e "\r      ${GREEN}[ OK ] ${filename}${NC}                    "
    done
fi

# ── Summary ──────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN} Setup Complete${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

voice_count=$(find "$MODELS_DIR" -name "*.onnx" 2>/dev/null | wc -l)
echo -e "  ${WHITE}Voice models:  ${voice_count} found in models/${NC}"
echo -e "  ${WHITE}Virtual env:   ${VENV_DIR}${NC}"
echo ""
echo -e "  ${WHITE}Run app:       .venv/bin/python -m readtome --debug${NC}"
echo -e "  ${WHITE}Cross-compile: ./build-linux.sh${NC}"
echo -e "  ${WHITE}More voices:   ./download-voices.sh${NC}"
echo ""

# ── Step 4: Launch in debug mode ──────────────────────────────────────────
if ! $NO_LAUNCH; then
    step=4
    echo -e "${YELLOW}[${step}/${STEP_COUNT}] Launching ReadToMe in debug mode...${NC}"
    echo ""
    echo -e "  ${GRAY}Press Ctrl+C to stop.${NC}"
    echo ""
    "${VENV_DIR}/bin/python" -m readtome --debug
else
    echo -e "  ${GRAY}Skipping launch (--no-launch).${NC}"
fi
