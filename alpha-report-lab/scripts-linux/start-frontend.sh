#!/bin/bash
# start-frontend.sh — Start Next.js Frontend

# Colors
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_PATH="$ROOT_DIR/alpha-frontend"

PORT=${ALPHA_FRONTEND_PORT:-3000}

echo -e "\n  ${CYAN}Starting Alpha Frontend on port $PORT...${NC}"
echo -e "  Open http://localhost:$PORT in your browser"
echo -e "  Press Ctrl+C to stop.\n"

cd "$FRONTEND_PATH" || exit
npm run dev -- -p "$PORT"
