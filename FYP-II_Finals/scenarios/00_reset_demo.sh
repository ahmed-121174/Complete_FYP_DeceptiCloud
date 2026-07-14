#!/usr/bin/env bash
# DeceptiCloud — Demo Reset Script
# Clears attack logs and resets counters for a clean jury run
# Safe: does NOT stop services, only wipes logs

set -uo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'
BOLD='\033[1m'; DIM='\033[2m'; RESET='\033[0m'; RED='\033[0;31m'

echo -e "${CYAN}${BOLD}"
echo "  ╔══════════════════════════════════════════════════════════╗"
echo "  ║      DeceptiCloud — Demo Reset for Jury Presentation    ║"
echo "  ║          Clears logs, resets counters, keeps services   ║"
echo "  ╚══════════════════════════════════════════════════════════╝"
echo -e "${RESET}"

echo -e "${YELLOW}  Resetting attack logs...${RESET}"

# 1. Clear proxy attack log
PROXY_LOG="${PROJECT_DIR}/proxy/logs/proxy_attacks.jsonl"
if [ -f "$PROXY_LOG" ]; then
    > "$PROXY_LOG"
    echo -e "  ${GREEN}✅ Proxy attack log cleared${RESET}  ${DIM}(${PROXY_LOG})${RESET}"
else
    echo -e "  ${DIM}  Proxy log not found (will be created fresh on first attack)${RESET}"
fi

# 2. Clear benign requests log
BENIGN_LOG="${PROJECT_DIR}/proxy/logs/benign_requests.jsonl"
if [ -f "$BENIGN_LOG" ]; then
    > "$BENIGN_LOG"
    echo -e "  ${GREEN}✅ Benign request log cleared${RESET}"
fi

# 3. Reset LLM stats
LLM_STATS="${PROJECT_DIR}/logs/llm_stats.json"
if [ -f "$LLM_STATS" ]; then
    echo '{"total_requests":0,"successful_responses":0,"fallbacks":0,"cached_responses":0}' > "$LLM_STATS"
    echo -e "  ${GREEN}✅ LLM stats reset to zero${RESET}"
fi

# 4. Reset blockchain (fresh genesis block)
CHAIN="${PROJECT_DIR}/honeypot/attack_chain.json"
if [ -f "$CHAIN" ]; then
    GENESIS_HASH=$(python3 -c "import hashlib,json,time; data={'index':0,'timestamp':time.time(),'data':'GENESIS','previous_hash':'0'}; print(hashlib.sha256(json.dumps(data).encode()).hexdigest())" 2>/dev/null || echo "0000000000000000")
    GENESIS_TS=$(python3 -c "import time; print(time.time())" 2>/dev/null || echo "0")
    python3 -c "
import json, hashlib, time
genesis = {
    'index': 0,
    'timestamp': time.time(),
    'data': {'event': 'GENESIS', 'description': 'DeceptiCloud Blockchain Initialized'},
    'previous_hash': '0' * 64,
    'hash': ''
}
raw = json.dumps({k:v for k,v in genesis.items() if k != 'hash'}, sort_keys=True)
genesis['hash'] = hashlib.sha256(raw.encode()).hexdigest()
with open('${CHAIN}', 'w') as f:
    json.dump([genesis], f, indent=2)
print('  Genesis block created — hash:', genesis['hash'][:32] + '...')
" 2>/dev/null && echo -e "  ${GREEN}✅ Blockchain reset (fresh genesis block)${RESET}" || \
    echo -e "  ${DIM}  Blockchain will reset on next system start${RESET}"
fi

# 5. Clear canary trigger log
CANARY_LOG="${PROJECT_DIR}/logs/canary_triggers.jsonl"
if [ -f "$CANARY_LOG" ]; then
    > "$CANARY_LOG"
    echo -e "  ${GREEN}✅ Canary trigger log cleared${RESET}"
fi

# 6. Clear adaptive engine state
AE_STATE="${PROJECT_DIR}/adaptive_engine/engine_state.json"
if [ -f "$AE_STATE" ]; then
    python3 -c "
import json
state = {
    'attacks_processed': 0,
    'rules_learned': 0,
    'last_retrain': None,
    'threat_landscape': {},
    'watchlist_ips': [],
    'confidence_threshold': 0.5,
    'initialized': True
}
with open('${AE_STATE}', 'w') as f:
    json.dump(state, f, indent=2)
print('  Adaptive engine state reset')
" 2>/dev/null && echo -e "  ${GREEN}✅ Adaptive engine state reset${RESET}" || \
    echo -e "  ${DIM}  Adaptive engine state will reset on next start${RESET}"
fi

# 7. Clear temp files
rm -f /tmp/dc_*.txt /tmp/dc_*.pid /tmp/dc_*.log /tmp/dc_*.cnt 2>/dev/null || true
echo -e "  ${GREEN}✅ Temporary files cleared${RESET}"

# 8. Reset proxy in-memory counters via API
echo -e "\n${YELLOW}  Resetting in-memory counters via proxy API...${RESET}"
RESET_RESULT=$(curl -sf --max-time 5 -X POST \
    "http://localhost:8080/proxy/reset" 2>/dev/null | \
    python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('message','Reset complete'))" 2>/dev/null || \
    echo "Proxy will reflect new clean state on next attack")
echo -e "  ${GREEN}✅ ${RESET_RESULT}${RESET}"

echo -e "\n${GREEN}${BOLD}"
echo "  ╔══════════════════════════════════════════════════════════╗"
echo "  ║              RESET COMPLETE ✅                          ║"
echo "  ║  Dashboard counters will show 0 on next refresh         ║"
echo "  ║  All 17 services remain running — NO restart needed     ║"
echo "  ║  Ready for clean jury demonstration                     ║"
echo "  ╚══════════════════════════════════════════════════════════╝"
echo -e "${RESET}"
echo -e "  ${DIM}Next step: Open http://localhost:9000 and verify counters are 0${RESET}\n"
