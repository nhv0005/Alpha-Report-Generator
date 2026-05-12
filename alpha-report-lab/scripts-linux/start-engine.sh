#!/bin/bash
# start-engine.sh — Start Python Alpha Engine

# Colors
CYAN='\033[0;36m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENGINE_PATH="$ROOT_DIR/alpha-engine"
ENV_FILE="$ENGINE_PATH/.env"
VENV_PATH="$ENGINE_PATH/.venv"
VENV_PYTHON="$VENV_PATH/bin/python"

# Load environment variables from .env file
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | xargs)
fi

# Ensure virtual environment exists
if [ ! -x "$VENV_PYTHON" ]; then
    echo -e "\n  ${CYAN}Creating Python virtual environment at .venv...${NC}"
    python3 -m venv "$VENV_PATH" || { echo "Failed to create venv. Is python3 installed?"; exit 1; }
    echo -e "  ${CYAN}Installing requirements into venv...${NC}"
    "$VENV_PYTHON" -m pip install --upgrade pip
    "$VENV_PYTHON" -m pip install -r "$ENGINE_PATH/requirements.txt"
fi

# Activate venv for this process
export VIRTUAL_ENV="$VENV_PATH"
export PATH="$VENV_PATH/bin:$PATH"

PORT=${ALPHA_ENGINE_PORT:-8000}

echo -e "\n  ${CYAN}Starting Alpha Engine on port $PORT (venv)...${NC}"
echo -e "  Press Ctrl+C to stop.\n"

cd "$ENGINE_PATH" || exit
"$VENV_PYTHON" -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --reload
