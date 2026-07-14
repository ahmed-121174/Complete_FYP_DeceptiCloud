#!/usr/bin/env bash
# DeceptiCloud — Unified System Launcher

# FYP Presentation Script

# Usage:

# bash run.sh              # Start natively (Python — recommended for demo)

# bash run.sh --docker     # Start via Docker Compose

# bash run.sh --stop       # Stop all services

# bash run.sh --test       # Start + run built-in attack simulation

# bash run.sh --status     # Check service health only

# After launching, run attack scripts:

# bash attacks/web_attacks.sh

# bash attacks/ddos_attack.sh


set -euo pipefail

# Colors

RED='\033[0;31m';    GREEN='\033[0;32m';   YELLOW='\033[1;33m'
CYAN='\033[0;36m';   MAGENTA='\033[0;35m'; BLUE='\033[0;34m'
BOLD='\033[1m';      DIM='\033[2m';        RESET='\033[0m'

# Config

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USE_DOCKER=false
STOP_MODE=false
TEST_MODE=false
STATUS_MODE=false

for arg in "$@"; do
    case "$arg" in
        --docker) USE_DOCKER=true ;;
        --stop)   STOP_MODE=true  ;;
        --test)   TEST_MODE=true  ;;
        --status) STATUS_MODE=true ;;
    esac
done

# Banner

print_banner() {
clear
echo -e "${CYAN}${BOLD}"
cat << 'BANNER'
                
BANNER
echo -e "${RESET}"
echo -e "  ${CYAN}AI-Driven Cyber Deception System for Cloud Infrastructures${RESET}"
echo -e "  ${DIM}FYP-II — FAST NUCES | 2026${RESET}\n"
}

# Helpers

check_ok()   { echo -e "  ${GREEN}${RESET} $1"; }
check_fail() { echo -e "  ${RED}${RESET} $1"; }
info()       { echo -e "  ${CYAN}ℹ${RESET}  $1"; }
section()    { echo -e "\n${YELLOW}${BOLD}   $1${RESET}\n  $(printf '%.0s' {1..60})"; }

wait_for_url() {
    local url="$1"
    local label="$2"
    local max_tries="${3:-30}"
    local i=0
    printf "  ${CYAN} Waiting for ${label}${RESET}"
    while ! curl -sf "$url" > /dev/null 2>&1; do
        sleep 1
        i=$((i+1))
        printf "."
        if [ "$i" -ge "$max_tries" ]; then
            echo -e " ${RED}TIMEOUT${RESET}"
            return 1
        fi
    done
    echo -e " ${GREEN}${RESET}"
}

# Status Check

check_status() {
    section "SYSTEM HEALTH CHECK"
    local all_ok=true

    check_url() {
        local url="$1"; local label="$2"
        if curl -sf "$url" > /dev/null 2>&1; then
            check_ok "$label"
        else
            check_fail "$label — NOT RUNNING"
            all_ok=false
        fi
    }

    check_url "http://localhost:5000/api/health"    "ML API          :5000"
    check_url "http://localhost:8080/proxy/status"  "Routing Proxy   :8080"
    check_url "http://localhost:9000/"              "Dashboard       :9000"
    for port in 3001 3002 3003 3004 3005 3006 3007; do
        check_url "http://localhost:${port}/" "Real Site       :${port}"
    done
    for port in 4001 4002 4003 4004 4005 4006 4007; do
        check_url "http://localhost:${port}/" "Honeypot        :${port}"
    done

    if $all_ok; then
        echo -e "\n  ${GREEN}${BOLD} All 16 services are ONLINE${RESET}"
    else
        echo -e "\n  ${YELLOW}  Some services are not running${RESET}"
    fi
}

# Stop

stop_services() {
    section "STOPPING ALL SERVICES"
    if $USE_DOCKER; then
        cd "$SCRIPT_DIR/docker"
        docker compose down
        check_ok "Docker services stopped"
    else
        info "Terminating Python processes on DeceptiCloud ports..."
        lsof -ti:3001,3002,3003,3004,3005,3006,3007,4001,4002,4003,4004,4005,4006,4007,5000,8080,9000 \
            2>/dev/null | xargs -r kill -9 2>/dev/null || true
        check_ok "All services stopped"
    fi
    exit 0
}

# Native Launch

launch_native() {
    section "SEEDING DATABASES"
    cd "$SCRIPT_DIR"
    python3 websites/shared/db_seeder.py 2>&1 | tail -5 || true
    check_ok "Databases ready"

    section "LAUNCHING SERVICES (Native Python)"

    # Kill anything on our ports first

    lsof -ti:3001,3002,3003,3004,3005,3006,3007,4001,4002,4003,4004,4005,4006,4007,5000,8080,9000 \
        2>/dev/null | xargs -r kill -9 2>/dev/null || true
    sleep 1

    # Activate venv if present

    if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
        source "$SCRIPT_DIR/venv/bin/activate"
    fi

    # ML API

    nohup python3 "$SCRIPT_DIR/ml_pipeline/model_api.py" \
        > "$SCRIPT_DIR/logs/ml_api.log" 2>&1 &
    echo $! > /tmp/dc_ml_api.pid

    # Wait for ML API

    wait_for_url "http://localhost:5000/api/health" "ML API" 45

    # Routing Proxy

    nohup python3 "$SCRIPT_DIR/proxy/routing_proxy.py" \
        > "$SCRIPT_DIR/logs/proxy.log" 2>&1 &
    echo $! > /tmp/dc_proxy.pid
    wait_for_url "http://localhost:8080/proxy/status" "Routing Proxy" 30

    # Dashboard

    nohup python3 "$SCRIPT_DIR/dashboard/app.py" \
        > "$SCRIPT_DIR/logs/dashboard.log" 2>&1 &
    echo $! > /tmp/dc_dashboard.pid
    wait_for_url "http://localhost:9000/" "Dashboard" 20

    # Websites (14 total)

    SITE_TYPES=(banking ecommerce healthcare blog api_service corporate admin_panel)
    REAL_PORTS=(3001 3002 3003 3004 3005 3006 3007)
    HP_PORTS=(4001 4002 4003 4004 4005 4006 4007)

    for i in "${!SITE_TYPES[@]}"; do
        SITE="${SITE_TYPES[$i]}"
        RPORT="${REAL_PORTS[$i]}"
        HPORT="${HP_PORTS[$i]}"

        SITE_TYPE="$SITE" SITE_VARIANT="real"     SITE_PORT="$RPORT" IS_HONEYPOT="false" \
            nohup python3 -c "
import os,sys; sys.path.insert(0,'/$(pwd)/websites'); from shared.site_factory import create_app
import sys; sys.path.insert(0,'$(pwd)')
app=create_app({'name':'$SITE','type':'$SITE','is_honeypot':False,'db_path':'$(pwd)/websites/databases/${SITE}_real.db','port':$RPORT,'theme_color':'#1a5276','tagline':'','icon':'','items_label':'Items'})
app.run(host='0.0.0.0',port=$RPORT)
" > "$SCRIPT_DIR/logs/${SITE}_real.log" 2>&1 &

        SITE_TYPE="$SITE" SITE_VARIANT="honeypot" SITE_PORT="$HPORT" IS_HONEYPOT="true" \
            nohup python3 -c "
import os,sys; sys.path.insert(0,'$(pwd)/websites'); from shared.site_factory import create_app
import sys; sys.path.insert(0,'$(pwd)')
app=create_app({'name':'$SITE','type':'$SITE','is_honeypot':True,'db_path':'$(pwd)/websites/databases/${SITE}_honeypot.db','port':$HPORT,'theme_color':'#c0392b','tagline':'','icon':'','items_label':'Items'})
app.run(host='0.0.0.0',port=$HPORT)
" > "$SCRIPT_DIR/logs/${SITE}_honeypot.log" 2>&1 &
    done

    sleep 5
    check_ok "All 14 websites launching"
}

# Docker Launch

launch_docker() {
    section "CHECKING DOCKER"

    if ! command -v docker &> /dev/null; then
        check_fail "Docker not installed"
        info "Install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi

    if ! docker info &> /dev/null 2>&1; then
        check_fail "Docker daemon not running — start Docker first"
        exit 1
    fi
    check_ok "Docker is running"

    section "BUILDING & LAUNCHING (Docker Compose)"
    cd "$SCRIPT_DIR/docker"

    docker compose down --remove-orphans 2>/dev/null || true

    info "Building images (first run takes 5-10 minutes)..."
    docker compose build --parallel 2>&1 | grep -E "Successfully|error|ERROR|Step" || true

    info "Starting all containers..."
    docker compose up -d

    section "WAITING FOR SERVICES"
    wait_for_url "http://localhost:5000/api/health"   "ML API"         60
    wait_for_url "http://localhost:8080/proxy/status" "Routing Proxy"  30
    wait_for_url "http://localhost:9000/"             "Dashboard"      30
    wait_for_url "http://localhost:3001/"             "Real Sites"     30
    wait_for_url "http://localhost:4001/"             "Honeypots"      30

    check_ok "All Docker containers healthy"
    cd "$SCRIPT_DIR"
}

# Print Summary

print_summary() {
    echo -e "\n${CYAN}${BOLD}"
    cat << 'EOF'
  
                  DECEPTICLOUD IS FULLY OPERATIONAL              
  
EOF
    echo -e "    ${BOLD} Dashboard:${RESET}${CYAN}    http://localhost:9000                      ${RESET}"
    echo -e "${CYAN}    ${BOLD} Login:${RESET}${CYAN}        admin / DeceptiCloud                     ${RESET}"
    echo -e "${CYAN}    ${BOLD} ML API:${RESET}${CYAN}       http://localhost:5000/api/health          ${RESET}"
    echo -e "${CYAN}    ${BOLD} Proxy:${RESET}${CYAN}        http://localhost:8080                     ${RESET}"
    echo -e "${CYAN}    ${BOLD} Real Sites:${RESET}${CYAN}   http://localhost:3001 → :3007             ${RESET}"
    echo -e "${CYAN}    ${BOLD} Honeypots:${RESET}${CYAN}    http://localhost:4001 → :4007             ${RESET}"
    echo -e "${CYAN}  ${RESET}"
    echo -e "${CYAN}    ${BOLD}  Attack Scripts (run in a new terminal):${RESET}${CYAN}               ${RESET}"
    echo -e "${CYAN}    ${MAGENTA}  bash attacks/web_attacks.sh${RESET}${CYAN}                            ${RESET}"
    echo -e "${CYAN}    ${RED}  bash attacks/ddos_attack.sh${RESET}${CYAN}                            ${RESET}"
    echo -e "${CYAN}    ${BOLD} Run Tests:${RESET}${CYAN}                                            ${RESET}"
    echo -e "${CYAN}    ${DIM}  python3 -m pytest tests/ -v              # Unit tests${RESET}${CYAN}    ${RESET}"
    echo -e "${CYAN}    ${DIM}  python3 -m pytest tests/integration/ -v  # Integration${RESET}${CYAN}  ${RESET}"
    echo -e "${CYAN}    ${DIM}  python3 -m pytest tests/system/ -v       # System tests${RESET}${CYAN} ${RESET}"
    echo -e "${CYAN}  ${RESET}"
    echo -e "${CYAN}    ${DIM}Press Ctrl+C to stop all services${RESET}${CYAN}                         ${RESET}"
    echo -e "${CYAN}  ${RESET}\n"
}

# Open Browser

open_browser() {
    sleep 2
    if command -v xdg-open &> /dev/null; then
        xdg-open "http://localhost:9000" &> /dev/null &
    elif command -v open &> /dev/null; then
        open "http://localhost:9000" &
    fi
}

# Main

mkdir -p "$SCRIPT_DIR/logs"
print_banner

if $STATUS_MODE; then
    check_status
    exit 0
fi

if $STOP_MODE; then
    stop_services
fi

if $USE_DOCKER; then
    launch_docker
else
    launch_native
fi

print_summary
check_status
open_browser

if $TEST_MODE; then
    section "RUNNING BUILT-IN ATTACK SIMULATION"
    sleep 3
    bash "$SCRIPT_DIR/attacks/web_attacks.sh"
fi

# Keep alive (native mode only)

if ! $USE_DOCKER; then
    echo -e "  ${DIM}System running. Press Ctrl+C to stop.${RESET}\n"
    trap 'echo -e "\n${YELLOW}  Stopping all services...${RESET}"; lsof -ti:3001,3002,3003,3004,3005,3006,3007,4001,4002,4003,4004,4005,4006,4007,5000,8080,9000 2>/dev/null | xargs -r kill -9 2>/dev/null || true; echo -e "${GREEN}  Done!${RESET}"; exit 0' INT
    while true; do sleep 1; done
fi
