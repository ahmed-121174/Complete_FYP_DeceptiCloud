#!/bin/bash
# ============================================================
#  DeceptiCloud — Full System Stop
# ============================================================

CYAN='\033[96m'; GREEN='\033[92m'; YELLOW='\033[93m'; RESET='\033[0m'; BOLD='\033[1m'
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE="$BASE_DIR/wazuh-docker/single-node/docker-compose.yml"
LOG_DIR="$BASE_DIR/logs/launch"

echo -e "${YELLOW}${BOLD}Stopping DeceptiCloud + Wazuh...${RESET}\n"

# Stop DeceptiCloud processes
echo -e "  ${CYAN}Stopping DeceptiCloud services...${RESET}"
pkill -f "launch_decepticloud_v2.py" 2>/dev/null && echo -e "  ${GREEN}✓${RESET} DeceptiCloud launcher stopped" || true
pkill -f "model_api.py"              2>/dev/null || true
pkill -f "routing_proxy.py"          2>/dev/null || true
pkill -f "dashboard/app.py"          2>/dev/null || true
pkill -f "log_ingestion_service.py"  2>/dev/null && echo -e "  ${GREEN}✓${RESET} Wazuh ingestion stopped" || true
pkill -f "adaptive_engine/engine.py" 2>/dev/null || true

# Stop Wazuh Docker stack
echo -e "  ${CYAN}Stopping Wazuh containers...${RESET}"
sg docker -c "docker compose -f '$COMPOSE' down" 2>&1 | grep -E "✔|Stopped|Removed" || true
echo -e "  ${GREEN}✓${RESET} Wazuh containers stopped"

# Clean up PID files
rm -f "$LOG_DIR"/*.pid 2>/dev/null || true

echo -e "\n  ${GREEN}✓ All services stopped.${RESET}\n"
