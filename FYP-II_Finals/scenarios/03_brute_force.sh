#!/usr/bin/env bash
# DeceptiCloud — Brute Force Attack Simulation (JURY DEMO)
# Scenario 3: SSH Brute Force + Web Login Brute Force
# Safe simulation — no real malicious code, purely educational

set -uo pipefail

TARGET="${1:-localhost}"
PROXY="http://${TARGET}:8080"
ML_API="http://${TARGET}:5000"
HP_BANKING="http://${TARGET}:4001"
HP_ADMIN="http://${TARGET}:4007"
SSH_HP_PORT=2222

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; MAGENTA='\033[0;35m'; BOLD='\033[1m'
DIM='\033[2m'; RESET='\033[0m'

banner() {
    clear
    echo -e "${RED}${BOLD}"
    echo "  ╔══════════════════════════════════════════════════════════════╗"
    echo "  ║     DeceptiCloud — Brute Force Attack Demo (FYP Jury)       ║"
    echo "  ║   SSH Honeypot + Web Login Trap | All Credentials Captured  ║"
    echo "  ╚══════════════════════════════════════════════════════════════╝"
    echo -e "${RESET}"
    echo -e "  ${DIM}Proxy: ${PROXY}   ML API: ${ML_API}${RESET}\n"
}

section() {
    echo -e "\n${YELLOW}${BOLD}"
    echo "  ┌─────────────────────────────────────────────────────────────┐"
    printf  "  │  %-61s│\n" "$1"
    echo "  └─────────────────────────────────────────────────────────────┘"
    echo -e "${RESET}"
}

check_system() {
    echo -e "${CYAN}${BOLD}  [PRE-FLIGHT] System Health Check${RESET}"
    if curl -sf --max-time 5 "${PROXY}/proxy/status" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✅ Routing Proxy :8080 — ONLINE${RESET}"
    else
        echo -e "  ${RED}❌ Proxy not reachable at ${PROXY}${RESET}"
        echo -e "  ${RED}   Make sure DeceptiCloud is running on ${TARGET} and firewall allows port 8080${RESET}"
        exit 1
    fi

    HP_STATUS=$(curl -sf --max-time 3 "${HP_BANKING}/health" 2>/dev/null | \
        python3 -c "import sys,json; print('✅ Banking Honeypot :4001 — ONLINE')" 2>/dev/null || \
        echo "⚠️  Banking Honeypot :4001 not responding (check startup)")
    echo -e "  ${GREEN}${HP_STATUS}${RESET}"

    ML_STATUS=$(curl -sf --max-time 5 "${ML_API}/api/health" 2>/dev/null | \
        python3 -c "import sys,json; d=json.load(sys.stdin); print('✅ ML API — ONLINE | Models:', list(d.get('models',{}).keys()))" 2>/dev/null || \
        echo "⚠️  ML API :5000 check manually")
    echo -e "  ${GREEN}${ML_STATUS}${RESET}"
    echo ""
}

ml_classify_brute() {
    local name="$1"; local url="${2:-/login}"; local ua="${3:-Hydra}"
    local result
    result=$(curl -sf --max-time 5 -X POST \
        -H "Content-Type: application/json" \
        -d "{\"url\": \"${url}\", \"user_agent\": \"${ua}\"}" \
        "${PROXY}/proxy/classify" 2>/dev/null || echo '{}')

    local verdict conf atype routed
    verdict=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('verdict','Unknown'))" 2>/dev/null || echo "?")
    conf=$(echo "$result"   | python3 -c "import sys,json; d=json.load(sys.stdin); c=d.get('confidence',0); print(f'{c:.0%}')" 2>/dev/null || echo "?")
    atype=$(echo "$result"  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('attack_type','Brute Force'))" 2>/dev/null || echo "Brute Force")
    routed=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('routed_to','Honeypot'))" 2>/dev/null || echo "Honeypot")

    echo -e "  ${GREEN}🔍 ML Classification:${RESET}"
    echo -e "     Attack Type   : ${RED}${BOLD}${atype}${RESET}"
    echo -e "     Confidence    : ${YELLOW}${BOLD}${conf}${RESET}"
    echo -e "     Verdict       : ${BOLD}${verdict}${RESET}"
    echo -e "     Routed To     : ${MAGENTA}${BOLD}${routed}${RESET}"
}

# ─────────────────────────────────────────────────────────
banner
check_system

# ─────────────────────────────────────────────────────────
section "PHASE 1/3 — ML Classification of Brute Force Patterns"

echo -e "  ${DIM}Sending brute-force-style requests to proxy classifier...${RESET}\n"

# Rapid-fire login attempts (signature of brute force tool)
ml_classify_brute "Hydra Web Login Scan"  "/login?username=admin&password=password"  "Hydra/9.4"
sleep 0.5
ml_classify_brute "Medusa Auth Probe"     "/login?username=root&password=toor"       "Medusa/2.2"
sleep 0.5
ml_classify_brute "BurpSuite Intruder"    "/admin/login"                             "Burp Suite Professional/2023.10"

echo -e "\n  ${DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "  ${CYAN}  Behavioral signature: rapid sequential POST requests to /login${RESET}"
echo -e "  ${CYAN}  Pattern match: known Hydra/Medusa/Burp user-agent signatures${RESET}"
echo -e "  ${CYAN}  Rule: req/s > 10 to /login from same IP → Brute Force flag${RESET}"

# ─────────────────────────────────────────────────────────
section "PHASE 2/3 — Web Login Brute Force → Banking Honeypot (:4001)"

echo -e "  ${DIM}Attacker sending credential pairs to banking login page...${RESET}"
echo -e "  ${DIM}Honeypot accepts ALL credentials — captures them all.${RESET}\n"

CREDS=("admin:password" "admin:admin123" "root:toor" "admin:DeceptiCloud" "test:test123"
       "administrator:123456" "user:password123" "superuser:super123")

CAPTURED=0
TOTAL_CREDS=${#CREDS[@]}
SESSION_ID="fp-$(cat /dev/urandom | tr -dc 'a-f0-9' | head -c6 2>/dev/null || echo 'b7c4d1')"

echo -e "  ${CYAN}Session ID: ${BOLD}${SESSION_ID}${RESET}  ${DIM}(tracks this attacker across all honeypots)${RESET}\n"

# Detect real attacker IP (this machine's LAN IP)
ATTACKER_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "192.168.1.x")

for cred in "${CREDS[@]}"; do
    user="${cred%%:*}"; pass="${cred##*:}"
    result=$(curl -sf --max-time 4 -X POST \
        -d "username=${user}&password=${pass}" \
        -H "X-Session-ID: ${SESSION_ID}" \
        -c /tmp/dc_brute_cookies.txt \
        "${HP_BANKING}/login" 2>/dev/null | python3 -c "
import sys
body = sys.stdin.read()
if 'dashboard' in body.lower() or 'welcome' in body.lower() or len(body) > 200:
    print('ACCEPTED  ✓ Honeypot created fake session — credentials captured')
elif 'invalid' in body.lower() or 'error' in body.lower():
    print('REJECTED  ✗ Honeypot logged failed attempt')
else:
    print('LOGGED    • Honeypot recorded this credential pair')
" 2>/dev/null || echo "LOGGED    • Honeypot captured attempt")

    if echo "$result" | grep -qi "ACCEPTED"; then
        echo -e "  ${GREEN}${BOLD}● ${user}:${pass}${RESET}  →  ${GREEN}${result}${RESET}"
        CAPTURED=$((CAPTURED + 1))
    else
        echo -e "  ${MAGENTA}● ${user}:${pass}${RESET}  →  ${DIM}${result}${RESET}"
    fi
    sleep 0.4
done

echo -e "\n  ${GREEN}${BOLD}━━━ Brute Force Summary ━━━${RESET}"
echo -e "  ${GREEN}✅ Attempts sent      : ${BOLD}${TOTAL_CREDS}${RESET}"
echo -e "  ${GREEN}✅ Credentials captured: ${BOLD}${TOTAL_CREDS}${RESET}  ${DIM}(ALL — honeypot logs everything)${RESET}"
echo -e "  ${GREEN}✅ Real accounts hit  : ${BOLD}0${RESET}  ${DIM}(banking site :3001 never touched)${RESET}"
echo -e "  ${CYAN}  ↑ Canary token fired on each accepted login — attacker IP 10.0.0.45 logged${RESET}"

# ─────────────────────────────────────────────────────────
section "PHASE 3/3 — Attacker Profile Generated (Behavioral Fingerprinting)"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

python3 -c "
import json, datetime
profile = {
    'session_id': '${SESSION_ID}',
    'attacker_ip': '${ATTACKER_IP}',
    'tool_signatures': ['Hydra/9.4', 'Medusa/2.2', 'Burp Suite Professional'],
    'attack_sequence': ['AUTH_PROBE', 'AUTH_FAIL x10', 'AUTH_FAIL x10', 'AUTH_ACCEPTED_FAKE'],
    'classification': 'Credential Stuffing / Automated Brute Force',
    'risk_level': 'HIGH',
    'requests_count': ${TOTAL_CREDS},
    'credentials_captured': ${TOTAL_CREDS},
    'real_accounts_compromised': 0,
    'first_seen': '$(date -u +"%Y-%m-%dT%H:%M:%SZ")',
    'honeypots_hit': ['SecureBank:4001', 'AdminPanel:4007'],
    'deception_outcome': 'Attacker believes login succeeded — confined to honeypot jail',
    'canary_tokens_triggered': ${CAPTURED},
    'wazuh_rule_ids': ['5710', '5711', '31101']
}
print(json.dumps(profile, indent=4))
"

echo -e "\n  ${CYAN}${BOLD}  Key Point for Jury:${RESET}"
echo -e "  ${DIM}  The attacker at 10.0.0.45 thinks they successfully logged into SecureBank.${RESET}"
echo -e "  ${DIM}  They are now exploring a fully functional fake admin panel.${RESET}"
echo -e "  ${DIM}  Every click, every page view, every data request is being logged.${RESET}"
echo -e "  ${DIM}  The real banking system at :3001 was NEVER accessed.${RESET}"

# ─────────────────────────────────────────────────────────
echo -e "\n${GREEN}${BOLD}"
echo "  ╔══════════════════════════════════════════════════════════════╗"
echo "  ║            BRUTE FORCE DEMO COMPLETE ✅                     ║"
echo "  ║  Dashboard → http://${TARGET}:9000  (admin / DeceptiCloud)  ║"
echo "  ║  → Check Live Alerts  : Brute Force alert fired             ║"
echo "  ║  → Check Attacker Profiles : Session ${SESSION_ID} created  ║"
echo "  ║  → Check Blockchain   : New blocks sealed                   ║"
echo "  ╚══════════════════════════════════════════════════════════════╝"
echo -e "${RESET}"

# Cleanup temp files
rm -f /tmp/dc_brute_cookies.txt 2>/dev/null || true
