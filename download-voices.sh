#!/usr/bin/env bash
# =============================================================================
# ReadToMe-TTS — Download All Piper English (US) Voices
# =============================================================================
#
# Downloads all available en_US voice models from Hugging Face into the
# models/ directory. Each voice requires two files: .onnx and .onnx.json
#
# Usage:
#   chmod +x download-voices.sh
#   ./download-voices.sh
#
# Source: https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US
#
set -euo pipefail

BASE_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODELS_DIR="${PROJECT_DIR}/models"

# ── Colors ───────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m'

# ── All available en_US voices ───────────────────────────────────────────
# Format: "voice_name:quality1,quality2,..."
VOICES=(
    "amy:low,medium"
    "arctic:medium"
    "bryce:medium"
    "danny:low"
    "hfc_female:medium"
    "hfc_male:medium"
    "joe:medium"
    "john:medium"
    "kathleen:low"
    "kristin:medium"
    "kusal:medium"
    "l2arctic:medium"
    "lessac:low,medium,high"
    "libritts:high"
    "libritts_r:medium"
    "ljspeech:high,medium"
    "norman:medium"
    "reza_ibrahim:medium"
    "ryan:low,medium,high"
    "sam:medium"
)

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN} ReadToMe-TTS — Download All Voices${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

mkdir -p "$MODELS_DIR"

# Count total
total=0
for entry in "${VOICES[@]}"; do
    qualities="${entry#*:}"
    IFS=',' read -ra quals <<< "$qualities"
    total=$((total + ${#quals[@]}))
done

echo "  Found ${#VOICES[@]} voices ($total model variants)"
echo "  Destination: $MODELS_DIR"
echo ""

downloaded=0
skipped=0
failed=0

for entry in "${VOICES[@]}"; do
    voice_name="${entry%%:*}"
    qualities="${entry#*:}"
    IFS=',' read -ra quals <<< "$qualities"

    for quality in "${quals[@]}"; do
        filename="en_US-${voice_name}-${quality}"
        onnx_file="${filename}.onnx"
        json_file="${filename}.onnx.json"
        onnx_path="${MODELS_DIR}/${onnx_file}"
        json_path="${MODELS_DIR}/${json_file}"

        # Skip if both files already exist
        if [ -f "$onnx_path" ] && [ -f "$json_path" ]; then
            echo -e "  ${GRAY}[SKIP] ${filename} (already downloaded)${NC}"
            skipped=$((skipped + 1))
            continue
        fi

        onnx_url="${BASE_URL}/${voice_name}/${quality}/${onnx_file}"
        json_url="${BASE_URL}/${voice_name}/${quality}/${json_file}"

        echo -ne "  ${YELLOW}[DOWN] ${filename}${NC}"

        if [ ! -f "$json_path" ]; then
            if ! wget -q -O "$json_path" "$json_url" 2>/dev/null; then
                echo -e "\r  ${RED}[FAIL] ${filename} — download error${NC}"
                rm -f "$onnx_path" "$json_path"
                failed=$((failed + 1))
                continue
            fi
        fi

        if [ ! -f "$onnx_path" ]; then
            if ! wget -q --show-progress -O "$onnx_path" "$onnx_url"; then
                echo -e "\r  ${RED}[FAIL] ${filename} — download error${NC}"
                rm -f "$onnx_path" "$json_path"
                failed=$((failed + 1))
                continue
            fi
        fi

        echo -e "\r  ${GREEN}[ OK ] ${filename}${NC}                    "
        downloaded=$((downloaded + 1))
    done
done

echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN} Download Complete${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""
echo -e "  ${GREEN}Downloaded: ${downloaded}${NC}"
echo -e "  ${GRAY}Skipped:    ${skipped}${NC}"
if [ "$failed" -gt 0 ]; then
    echo -e "  ${RED}Failed:     ${failed}${NC}"
fi
echo ""
echo "  Voices are ready in: $MODELS_DIR"
echo "  Restart ReadToMe to see them in the Voice menu."
echo ""
