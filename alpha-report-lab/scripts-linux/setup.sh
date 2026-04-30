#!/bin/bash
# setup.sh — Create .env files from examples

# Colors for output
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "\n${CYAN}=========================================${NC}"
echo -e "${CYAN}  Alpha Report Lab - Linux Setup${NC}"
echo -e "${CYAN}=========================================\n${NC}"

# Get the root directory (parent of this script's directory)
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Define environment file mappings
declare -A MAPPINGS=(
    [".env.example"]=".env"
    ["alpha-engine/.env.example"]="alpha-engine/.env"
    ["alpha-frontend/.env.local.example"]="alpha-frontend/.env.local"
)

for SRC in "${!MAPPINGS[@]}"; do
    DST="${MAPPINGS[$SRC]}"
    SRC_PATH="$ROOT_DIR/$SRC"
    DST_PATH="$ROOT_DIR/$DST"

    if [ ! -f "$DST_PATH" ]; then
        if [ -f "$SRC_PATH" ]; then
            cp "$SRC_PATH" "$DST_PATH"
            echo -e "  ${GREEN}Created:${NC} $DST"
        else
            echo -e "  ${YELLOW}Warning:${NC} $SRC not found"
        fi
    else
        echo -e "  Exists:  $DST (skipped)"
    fi
done

echo -e "\n  ${YELLOW}Next steps:${NC}"
echo -e "    1. Edit .env with your OpenAI API key and Dynatrace credentials"
echo -e "    2. Run: ./tasks.sh install"
echo -e "    3. Run: ./tasks.sh run-all\n"
