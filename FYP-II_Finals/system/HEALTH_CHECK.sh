#!/usr/bin/env bash
# DeceptiCloud — Pre-Demo Health Check
# Verifies ALL services are online before jury enters
# Usage: bash FYP-II_Finals/system/HEALTH_CHECK.sh
#        bash FYP-II_Finals/system/HEALTH_CHECK.sh <hostname>

TARGET="${1:-localhost}"

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; DIM='\033[2m'; RESET='\033[0m'

PASS=0; FAIL=0

banner() {
    clear
    echo -e "${CYAN}${BOLD}"
    echo "  ╔══════════════════════════════════════════════════════════════╗"
    echo "  ║     DeceptiCloud — Pre-Jury Health Check (17 Services)      ║"
    echo "  ╚══════════════════════════════════════════════════════════════╝"
    echo -e "${RESET}"
}

check_port() {
    local port=$1; local name=$2; local type=$3
    local start_ms; start_ms=$(date +%s%3N 2>/dev/null || echo 0)
    local ok=false

    for path in "/" "/health" "/proxy/status" "/api/health"; do
        if curl -sf --max-time 3 "http://${TARGET}:${port}${path}" > /dev/null 2>&1; then
            ok=true; break
        fi
    done

    local end_ms; end_ms=$(date +%s%3N 2>/dev/null || echo 0)
    local ms=$(( end_ms - start_ms ))

    if $ok; then
        printf "  ${GREEN}✅${RESET}  [%-6s] %-35s ${DIM}%dms${RESET}\n" "$type" "$name :${port}" "$ms"
        PASS=$((PASS + 1))
    else
        printf "  ${RED}❌${RESET}  [%-6s] %-35s ${RED}OFFLINE${RESET}\n" "$type" "$name :${port}"
        FAIL=$((FAIL + 1))
    fi
}

# ─────────────────────────────────────────────────────────────────
banner

echo -e "${CYAN}${BOLD}  ── Core Infrastructure ──${RESET}"
check_port 5000  "ML API (Web-Attack + DDoS)"   "ML"
check_port 8080  "Routing Proxy (AI Gateway)"   "PROXY"
check_port 9000  "Security Dashboard (SOC UI)"  "UI"

echo -e "\n${CYAN}${BOLD}  ── Real Sites (Protected) ──${RESET}"
REAL_SITES=("SecureBank" "ShopEase" "MedCore" "TechBlog" "DataAPI" "NexaGen Corp" "AdminPanel")
for i in "${!REAL_SITES[@]}"; do
    check_port $((3001+i)) "${REAL_SITES[$i]}" "REAL"
done

echo -e "\n${CYAN}${BOLD}  ── Honeypot Clones (Deception Layer) ──${RESET}"
HP_SITES=("SecureBank HP" "ShopEase HP" "MedCore HP" "TechBlog HP" "DataAPI HP" "NexaGen HP" "AdminPanel HP")
for i in "${!HP_SITES[@]}"; do
    check_port $((4001+i)) "${HP_SITES[$i]}" "HP"
done

echo -e "\n${CYAN}${BOLD}  ── Additional Services ──${RESET}"
# Wazuh dashboard (optional)
if curl -sf --max-time 5 -k "https://${TARGET}:443" > /dev/null 2>&1; then
    echo -e "  ${GREEN}✅${RESET}  [WAZUH] Wazuh SIEM Dashboard :443              ${DIM}ONLINE${RESET}"
    PASS=$((PASS + 1))
else
    echo -e "  ${YELLOW}⚠️ ${RESET}  [WAZUH] Wazuh SIEM :443                       ${DIM}(check docker: docker ps | grep wazuh)${RESET}"
fi

# SSH honeypot (optional)
if command -v nc > /dev/null 2>&1 && nc -z -w 2 "${TARGET}" 2222 2>/dev/null; then
    echo -e "  ${GREEN}✅${RESET}  [SSH]   SSH Honeypot :2222                      ${DIM}ONLINE${RESET}"
    PASS=$((PASS + 1))
else
    echo -e "  ${DIM}⚠️ ${RESET}  [SSH]   SSH Honeypot :2222                      ${DIM}(optional for brute-force demo)${RESET}"
fi

# ─── Summary ───────────────────────────────────────────────────
TOTAL=$((PASS + FAIL))
echo ""
echo -e "${CYAN}${BOLD}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "  Services checked : ${BOLD}${TOTAL}${RESET}"
echo -e "  Online           : ${GREEN}${BOLD}${PASS}${RESET}"

if [ "$FAIL" -gt 0 ]; then
    echo -e "  Offline          : ${RED}${BOLD}${FAIL}${RESET}"
    echo ""
    echo -e "  ${RED}${BOLD}⚠️  ACTION REQUIRED — some services are offline:${RESET}"
    echo -e "  ${RED}  Fix: bash FYP-II_Finals/system/STOP.sh${RESET}"
    echo -e "  ${RED}        bash FYP-II_Finals/system/START.sh${RESET}"
else
    echo -e "  Offline          : ${GREEN}${BOLD}0${RESET}"
    echo ""
    echo -e "${GREEN}${BOLD}"
    echo "  ╔══════════════════════════════════════════════════════════════╗"
    echo "  ║          ALL SYSTEMS ONLINE — READY FOR JURY ✅             ║"
    echo "  ║                                                              ║"
    echo "  ║  Dashboard  : http://localhost:9000                         ║"
    echo "  ║  Login      : admin / DeceptiCloud                          ║"
    echo "  ║                                                              ║"
    echo "  ║  Run demos  :                                                ║"
    echo "  ║    bash FYP-II_Finals/scenarios/01_web_injection.sh         ║"
    echo "  ║    bash FYP-II_Finals/scenarios/02_ddos_attack.sh low       ║"
    echo "  ║    bash FYP-II_Finals/scenarios/03_brute_force.sh           ║"
    echo "  ╚══════════════════════════════════════════════════════════════╝"
    echo -e "${RESET}"
fi

# ─── ML Models Status ──────────────────────────────────────────
echo -e "\n${CYAN}${BOLD}  ── ML Models Status ──${RESET}"
ML_HEALTH=$(curl -sf --max-time 5 "http://${TARGET}:5000/api/health" 2>/dev/null || echo '{}')
echo "$ML_HEALTH" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    models = d.get('models', {})
    for name, loaded in models.items():
        icon = '✅' if loaded else '❌'
        print(f'  {icon}  Model: {name:<25} {\"LOADED\" if loaded else \"NOT LOADED\"}')
    if not models:
        print('  ⚠️  No model data — ML API may still be starting up (wait 10s and retry)')
except Exception as e:
    print(f'  ⚠️  ML API not responding yet: {e}')
" 2>/dev/null

echo ""
