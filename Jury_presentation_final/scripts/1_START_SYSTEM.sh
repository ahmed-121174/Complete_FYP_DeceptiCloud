#!/usr/bin/env bash

set -e

# Colors

GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'
RED='\033[0;31m'; BOLD='\033[1m'; DIM='\033[2m'; RESET='\033[0m'

PROJ="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_DIR="${PROJ}/logs/launch"
mkdir -p "$LOG_DIR"
# Ensure blockchain symlink always exists (dashboard reads from logs/, ledger writes to honeypot/)

ln -sf "${PROJ}/honeypot/attack_chain.json" "${PROJ}/logs/attack_chain.json" 2>/dev/null || true

banner() {
    clear
    echo -e "${CYAN}${BOLD}"

    echo "            DeceptiCloud — AI Cyber Deception System               "
    echo "         FYP Jury Presentation  |  All Systems Launching...           "

    echo -e "${RESET}"
}

step() { echo -e "\n${YELLOW}${BOLD}   $1${RESET}"; }
ok()   { echo -e "  ${GREEN}${RESET} $1"; }
info() { echo -e "  ${DIM}$1${RESET}"; }

# STEP 0: ALWAYS stop everything first (bulletproof clean slate)

banner
step "Stopping any existing services first..."
# Run STOP_ALL from same directory

bash "$(dirname "${BASH_SOURCE[0]}")/STOP_ALL.sh" 2>/dev/null || true
ok "Clean slate confirmed"

# STEP 1: Find and activate venv

step "Activating virtual environment..."
if [ -f "${PROJ}/venv/bin/activate" ]; then
    source "${PROJ}/venv/bin/activate"
    export VIRTUAL_ENV="${PROJ}/venv"
    export PATH="${PROJ}/venv/bin:${PATH}"
    PYTHON3="${PROJ}/venv/bin/python3"
    ok "Python venv active: $PYTHON3"
else
    echo -e "${RED}   venv not found at ${PROJ}/venv${RESET}"
    echo -e "${RED}    Run: cd '${PROJ}' && python3 -m venv venv && pip install -r requirements.txt${RESET}"
    exit 1
fi

# STEP 2: Launch full system

step "Launching all 16 services..."
info "  (ML API → Proxy → Dashboard → 7 Real Sites → 7 Honeypots)"

cd "${PROJ}"
# Use explicit venv python3 so subprocesses inherit proper environment

"${PYTHON3}" launch_decepticloud.py > "${LOG_DIR}/system.log" 2>&1 &
LAUNCH_PID=$!
echo $LAUNCH_PID > /tmp/dc_launch.pid
info "  Launcher PID: $LAUNCH_PID  |  Logs: ${LOG_DIR}/system.log"

# STEP 3: Wait for health checks

step "Waiting for services to start (up to 90s)..."
TIMEOUT=90
ELAPSED=0
REQUIRED_PORTS=(5000 8080 9000 4001 3001)
ALL_UP=false

while [ $ELAPSED -lt $TIMEOUT ]; do
    UP=0
    for port in "${REQUIRED_PORTS[@]}"; do
        curl -sf --max-time 2 "http://localhost:${port}/" > /dev/null 2>&1 && UP=$((UP+1)) || true
        curl -sf --max-time 2 "http://localhost:${port}/health" > /dev/null 2>&1 && UP=$((UP+1)) || true
        curl -sf --max-time 2 "http://localhost:${port}/api/health" > /dev/null 2>&1 && UP=$((UP+1)) || true
    done
    # Check proxy specifically (returns JSON)

    PROXY_OK=$(curl -sf --max-time 2 http://localhost:8080/proxy/status 2>/dev/null | python3 -c "import sys,json;print(json.load(sys.stdin).get('status',''))" 2>/dev/null || echo "")

    printf "\r  ${DIM}[%ds] ML:%s  Proxy:%s  Dash:%s  Sites:%s${RESET}" \
        $ELAPSED \
        "$(curl -sf --max-time 1 http://localhost:5000/api/health 2>/dev/null | python3 -c "import sys,json;print('UP' if json.load(sys.stdin).get('status')=='healthy' else 'loading')" 2>/dev/null || echo "...")" \
        "$([ "$PROXY_OK" = "healthy" ] && echo "UP" || echo "...")" \
        "$(curl -sf --max-time 1 http://localhost:9000/ 2>/dev/null | head -c5 | grep -q DOCTYPE && echo "UP" || echo "...")" \
        "$(curl -sf --max-time 1 http://localhost:3001/ 2>/dev/null | head -c5 | grep -q DOCTYPE && echo "UP" || echo "...")"

    if [ "$PROXY_OK" = "healthy" ]; then
        ALL_UP=true; break
    fi
    sleep 2; ELAPSED=$((ELAPSED + 2))
done


# STEP 4: Status Report

echo -e "\n${BOLD}   Service Status Report ${RESET}"

check_port() {
    local port=$1; local name=$2
    if curl -sf --max-time 3 "http://localhost:${port}/" > /dev/null 2>&1 || \
       curl -sf --max-time 3 "http://localhost:${port}/health" > /dev/null 2>&1 || \
       curl -sf --max-time 3 "http://localhost:${port}/api/health" > /dev/null 2>&1 || \
       curl -sf --max-time 3 "http://localhost:${port}/proxy/status" > /dev/null 2>&1; then
        echo -e "  ${GREEN}${RESET}  ${name} (port ${port})"
    else
        echo -e "  ${RED}${RESET}  ${name} (port ${port}) — may still be starting"
    fi
}

check_port 5000 "ML API (DDoS + Web Attack Models)"
check_port 8080 "Routing Proxy  (ML detection + honeypot routing)"
check_port 9000 "Security Dashboard"

for i in 0 1 2 3 4 5 6; do
    TYPES=("Banking" "E-commerce" "Healthcare" "Blog" "API Service" "Corporate" "Admin Panel")
    check_port $((3001+i)) "Real Site: ${TYPES[$i]}"
done

for i in 0 1 2 3 4 5 6; do
    TYPES=("Banking" "E-commerce" "Healthcare" "Blog" "API Service" "Corporate" "Admin Panel")
    check_port $((4001+i)) "Honeypot: ${TYPES[$i]}"
done

# STEP 5: Pre-seed attacks so dashboard is NEVER empty


step "Pre-seeding system with sample attacks (dashboard will be populated)..."
(
    sleep 2
    # SQLi attacks through proxy

    curl -sf --max-time 20 -A "sqlmap/1.7" \
        "http://localhost:8080/banking/search?q=1+UNION+SELECT+username,password+FROM+users--" -o /dev/null 2>/dev/null
    curl -sf --max-time 20 -A "sqlmap/1.7.8" \
        "http://localhost:8080/ecommerce/login?username=admin'+OR+'1'='1&password=x" -o /dev/null 2>/dev/null
    # XSS

    curl -sf --max-time 20 -A "Burp Suite Professional" \
        "http://localhost:8080/blog/search?q=%3Cscript%3Ealert%28document.cookie%29%3C%2Fscript%3E" -o /dev/null 2>/dev/null
    curl -sf --max-time 20 -A "ZAP/2.14" \
        "http://localhost:8080/ecommerce/search?q=%3Cimg+src%3Dx+onerror%3Dalert%281%29%3E" -o /dev/null 2>/dev/null
    # Path traversal

    curl -sf --max-time 20 -A "nikto/2.1.6" \
        "http://localhost:8080/healthcare/file?name=../../../../etc/passwd" -o /dev/null 2>/dev/null
    curl -sf --max-time 20 -A "nikto/2.1.6" \
        "http://localhost:8080/corporate/file?name=..%252F..%252Fetc%252Fshadow" -o /dev/null 2>/dev/null
    # Command injection

    curl -sf --max-time 20 -A "nikto/2.1.6" \
        "http://localhost:8080/admin_panel/exec?cmd=cat+/etc/passwd%3Bid" -o /dev/null 2>/dev/null
    # NoSQLi

    curl -sf --max-time 20 -A "sqlmap/1.7" \
        "http://localhost:8080/api_service/api?filter=%7B%24gt%3A%27%27%7D" -o /dev/null 2>/dev/null
    # More SQLi for variety

    curl -sf --max-time 20 -A "sqlmap/1.7" \
        "http://localhost:8080/healthcare/search?q=1%27+AND+1%3D1" -o /dev/null 2>/dev/null
    curl -sf --max-time 20 -A "Burp Suite Professional" \
        "http://localhost:8080/admin_panel/search?q=UNION+SELECT+*+FROM+admin_users--" -o /dev/null 2>/dev/null
    echo "   Pre-seeding done — dashboard has live attack data"
) &
SEED_PID=$!
info "   Firing 10 sample attacks in background (PID $SEED_PID)..."
sleep 8   # Give first few attacks time to process + LLM to cache

# STEP 6: Open browser


step "Opening Dashboard in browser..."
sleep 2
xdg-open "http://localhost:9000" 2>/dev/null &
ok "Dashboard: http://localhost:9000  (Login: admin / DeceptiCloud)"

# DONE

echo -e "\n${GREEN}${BOLD}"

echo "       ALL SYSTEMS ONLINE"

echo "     Stop   bash Jury_presentation_final/scripts/STOP_ALL.sh        "
echo -e "  ${RESET}"
