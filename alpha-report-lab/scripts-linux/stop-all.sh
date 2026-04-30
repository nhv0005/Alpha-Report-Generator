#!/bin/bash
# stop-all.sh — Stop all running services

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "\n${CYAN}Stopping Alpha Report Lab services...${NC}"

# Stop Python/Uvicorn processes
if pgrep -f "uvicorn" > /dev/null; then
    pkill -f "uvicorn"
    echo -e "  ${GREEN}Alpha Engine stopped.${NC}"
else
    echo -e "  Alpha Engine was not running."
fi

# Stop Node processes
if pgrep -f "next-dev" > /dev/null || pgrep -f "next-server" > /dev/null; then
    pkill -f "next"
    echo -e "  ${GREEN}Alpha Frontend stopped.${NC}"
else
    echo -e "  Alpha Frontend was not running."
fi

echo -e "  ${CYAN}Done.${NC}\n"
