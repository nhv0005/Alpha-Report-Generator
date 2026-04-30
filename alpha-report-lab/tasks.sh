#!/bin/bash
# tasks.sh — Alpha Report Lab Task Runner (Linux)

TASK=${1:-help}
SCRIPTS_DIR="$(dirname "${BASH_SOURCE[0]}")/scripts-linux"

# Ensure scripts are executable
chmod +x "$SCRIPTS_DIR"/*.sh 2>/dev/null

case $TASK in
    "setup")
        "$SCRIPTS_DIR/setup.sh"
        ;;
    "install")
        "$SCRIPTS_DIR/install.sh"
        ;;
    "run-engine")
        "$SCRIPTS_DIR/start-engine.sh"
        ;;
    "run-frontend")
        "$SCRIPTS_DIR/start-frontend.sh"
        ;;
    "run-all"|"start")
        "$SCRIPTS_DIR/start-all.sh"
        ;;
    "stop"|"stop-all")
        "$SCRIPTS_DIR/stop-all.sh"
        ;;
    "clean")
        "$SCRIPTS_DIR/clean.sh"
        ;;
    "help")
        echo ""
        echo -e "\033[0;36m=========================================\033[0m"
        echo -e "\033[0;36m  Alpha Report Lab - Task Runner (Linux)\033[0m"
        echo -e "\033[0;36m=========================================\033[0m"
        echo ""
        echo -e "\033[1;33mUsage: ./tasks.sh <task>\033[0m"
        echo ""
        echo -e "\033[0;32m  Setup & Install:\033[0m"
        echo "    setup          Create .env files from templates"
        echo "    install        Install Python + Node.js dependencies"
        echo ""
        echo -e "\033[0;32m  Run:\033[0m"
        echo "    run-engine     Start Python Alpha Engine (port 8000)"
        echo "    run-frontend   Start Next.js Frontend (port 3000)"
        echo "    run-all        Start both services"
        echo "    start          Start both (engine bg, frontend fg)"
        echo "    stop           Stop all running services"
        echo ""
        echo -e "\033[0;32m  Maintenance:\033[0m"
        echo "    clean          Remove build artifacts"
        echo "    help           Show this help message"
        echo ""
        ;;
    *)
        echo "Unknown task: $TASK"
        echo "Run './tasks.sh help' for usage"
        exit 1
        ;;
esac
