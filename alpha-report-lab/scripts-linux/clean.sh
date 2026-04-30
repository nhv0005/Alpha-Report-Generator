#!/bin/bash
# clean.sh — Remove build artifacts

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "\n${CYAN}Cleaning build artifacts...${NC}"

# Cleanup frontend
FRONTEND_DIR="$ROOT_DIR/alpha-frontend"
if [ -d "$FRONTEND_DIR/node_modules" ]; then
    rm -rf "$FRONTEND_DIR/node_modules"
    echo -e "  Removed: alpha-frontend/node_modules"
fi
if [ -d "$FRONTEND_DIR/.next" ]; then
    rm -rf "$FRONTEND_DIR/.next"
    echo -e "  Removed: alpha-frontend/.next"
fi

# Cleanup engine
ENGINE_DIR="$ROOT_DIR/alpha-engine"
find "$ENGINE_DIR" -type d -name "__pycache__" -exec rm -rf {} + -print | sed 's/^/  Removed: /'
find "$ENGINE_DIR" -type f -name "*.pyc" -delete

echo -e "  ${GREEN}Done.${NC}\n"
