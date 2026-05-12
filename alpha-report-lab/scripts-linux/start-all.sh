#!/bin/bash
# start-all.sh — Start both services (engine bg, frontend fg)

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENGINE_PATH="$ROOT_DIR/alpha-engine"
FRONTEND_PATH="$ROOT_DIR/alpha-frontend"
VENV_PATH="$ENGINE_PATH/.venv"
VENV_PYTHON="$VENV_PATH/bin/python"

# Ensure virtual environment exists
if [ ! -x "$VENV_PYTHON" ]; then
    echo -e "  ${CYAN}Creating Python virtual environment at .venv...${NC}"
    python3 -m venv "$VENV_PATH" || { echo "Failed to create venv. Is python3 installed?"; exit 1; }
    echo -e "  ${CYAN}Installing requirements into venv...${NC}"
    "$VENV_PYTHON" -m pip install --upgrade pip
    "$VENV_PYTHON" -m pip install -r "$ENGINE_PATH/requirements.txt"
fi

echo -e "\n${CYAN}=========================================${NC}"
echo -e "${CYAN}  Alpha Report Lab - Starting Services${NC}"
echo -e "${CYAN}=========================================\n${NC}"

# Load env variables for ports
ENV_FILE="$ENGINE_PATH/.env"
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | xargs)
fi

ENGINE_PORT=${ALPHA_ENGINE_PORT:-8000}
FRONTEND_PORT=${ALPHA_FRONTEND_PORT:-3000}

echo -e "  Starting Alpha Engine on port $ENGINE_PORT (background, venv)..."
cd "$ENGINE_PATH" || exit
export VIRTUAL_ENV="$VENV_PATH"
export PATH="$VENV_PATH/bin:$PATH"
"$VENV_PYTHON" -m uvicorn app.main:app --host 0.0.0.0 --port "$ENGINE_PORT" --reload > engine.log 2>&1 &
ENGINE_PID=$!

echo -e "  Engine Process ID: $ENGINE_PID"

echo -e "  Waiting for engine to be ready..."
READY=false
for i in {1..30}; do
    sleep 1
    if curl -s "http://localhost:$ENGINE_PORT/health" > /dev/null; then
        echo -e "  ${GREEN}Alpha Engine is ready.${NC}\n"
        READY=true
        break
    fi
done

if [ "$READY" = false ]; then
    echo -e "  ${YELLOW}Warning: Engine may not be ready yet. Check engine.log${NC}"
fi

echo -e "  Starting Alpha Frontend on port $FRONTEND_PORT (foreground)..."
echo -e "  Open http://localhost:$FRONTEND_PORT in your browser"
echo -e "  Press Ctrl+C to stop frontend. Then run: ./tasks.sh stop\n"

cd "$FRONTEND_PATH" || exit

# Cleanup function for background process
cleanup() {
    echo -e "\n  Stopping background engine process (PID $ENGINE_PID)..."
    kill $ENGINE_PID 2>/dev/null
    echo -e "  ${GREEN}Stopped.${NC}"
    exit
}

trap cleanup SIGINT SIGTERM

npm run dev -- -p "$FRONTEND_PORT"
