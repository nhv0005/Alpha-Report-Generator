#!/bin/bash
# install.sh — Install all dependencies

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "\n${CYAN}Installing Python dependencies...${NC}"
cd "$ROOT_DIR/alpha-engine" || exit
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
else
    echo "Error: requirements.txt not found in alpha-engine"
    exit 1
fi

echo -e "\n${CYAN}Installing Node.js dependencies...${NC}"
cd "$ROOT_DIR/alpha-frontend" || exit
if [ -f "package.json" ]; then
    npm install
else
    echo "Error: package.json not found in alpha-frontend"
    exit 1
fi

echo -e "\n  ${GREEN}All dependencies installed.${NC}\n"
