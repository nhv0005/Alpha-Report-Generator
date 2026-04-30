#!/bin/bash
# start-engine.sh — Start Python Alpha Engine

# Colors
CYAN='\033[0;36m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENGINE_PATH="$ROOT_DIR/alpha-engine"
ENV_FILE="$ENGINE_PATH/.env"

# Load environment variables from .env file
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | xargs)
fi

PORT=${ALPHA_ENGINE_PORT:-8000}

echo -e "\n  ${CYAN}Starting Alpha Engine on port $PORT...${NC}"
echo -e "  Press Ctrl+C to stop.\n"

cd "$ENGINE_PATH" || exit
uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --reload
