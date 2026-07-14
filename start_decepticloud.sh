#!/bin/bash
# ============================================================
#  DeceptiCloud — Full System Launcher
#  Starts: Wazuh (backend+frontend) + DeceptiCloud (backend+frontend)
# ============================================================

set -e

CYAN='\033[96m'
GREEN='\033[92m'
YELLOW='\033[93m'
RED='\033[91m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE="$BASE_DIR/wazuh-docker/single-node/docker-compose.yml"
LOG_DIR="$BASE_DIR/logs/launch"
mkdir -p "$LOG_DIR"

print_section() { echo -e "\n${CYAN}${BOLD}═══ $1 ═══${RESET}"; }
ok()  { echo -e "  ${GREEN}✓${RESET} $1"; }
warn(){ echo -e "  ${YELLOW}⚠${RESET} $1"; }
err() { echo -e "  ${RED}✗${RESET} $1"; }
info(){ echo -e "  ${DIM}ℹ $1${RESET}"; }

echo -e "${CYAN}${BOLD}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║          DeceptiCloud — Full System Launcher         ║"
echo "║     Wazuh SIEM  +  AI Cyber Deception Platform       ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${RESET}"

# ─────────────────────────────────────────────
# STEP 1: Check Docker
# ─────────────────────────────────────────────
print_section "CHECKING DOCKER"
if ! docker info > /dev/null 2>&1; then
    err "Docker not accessible. Run: newgrp docker"
    exit 1
fi
ok "Docker is running"

# ─────────────────────────────────────────────
# STEP 2: Start Wazuh Stack (Backend + Frontend)
# ─────────────────────────────────────────────
print_section "STARTING WAZUH STACK"

# Stop any stale containers first
docker compose -f '$COMPOSE' down --remove-orphans > /dev/null 2>&1 || true

info "Starting Wazuh containers (indexer, manager, dashboard)..."
docker compose -f '$COMPOSE' up -d" 2>&1 | grep -E "✔|✗|error|Error || true

# Wait for indexer to be healthy (required before manager/dashboard work)
info "Waiting for Wazuh Indexer to become healthy (up to 3 min)..."
HEALTHY=false
for i in $(seq 1 36); do
    STATUS=$(docker inspect single-node-wazuh.indexer --format '{{.State.Health.Status}}'" 2>/dev/null || echo "unknown)
    if [ "$STATUS" = "healthy" ]; then
        HEALTHY=true
        break
    fi
    echo -ne "  ${DIM}  Waiting... ${i}/36 (${i}x5s)${RESET}\r"
    sleep 5
done
echo ""

if [ "$HEALTHY" = "true" ]; then
    ok "Wazuh Indexer is healthy"
else
    warn "Indexer health check timed out — continuing anyway"
fi

# Copy fixed custom rules/decoders into manager
info "Applying custom DeceptiCloud rules and decoders..."
docker cp '$BASE_DIR/wazuh/custom_decoders.xml' single-node-wazuh.manager:/var/ossec/etc/decoders/local_decoder.xml 2>/dev/null && \
docker cp '$BASE_DIR/wazuh/custom_rules.xml'    single-node-wazuh.manager:/var/ossec/etc/rules/local_rules.xml    2>/dev/null && \
docker restart single-node-wazuh.manager > /dev/null 2>&1 && \
ok "Custom rules/decoders applied, manager restarted" || \
warn "Could not apply custom rules (manager may not be ready yet)"

# Wait for Wazuh API to respond
info "Waiting for Wazuh Manager API (port 55000)..."
API_UP=false
for i in $(seq 1 24); do
    CODE=$(curl -sk -o /dev/null -w "%{http_code}" -X POST \
        -u "wazuh-wui:MyS3cr37P450r.*-" \
        https://localhost:55000/security/user/authenticate 2>/dev/null || echo "000")
    if [ "$CODE" = "200" ]; then
        API_UP=true
        break
    fi
    sleep 5
done

if [ "$API_UP" = "true" ]; then
    ok "Wazuh Manager API is up (port 55000)"
else
    warn "Wazuh Manager API not responding yet — it may still be starting"
fi

# Wait for Wazuh Dashboard
info "Waiting for Wazuh Dashboard (port 5601)..."
DASH_UP=false
for i in $(seq 1 24); do
    CODE=$(curl -sk -o /dev/null -w "%{http_code}" http://localhost:5601/ 2>/dev/null || echo "000")
    if [ "$CODE" = "200" ] || [ "$CODE" = "302" ]; then
        DASH_UP=true
        break
    fi
    sleep 5
done

if [ "$DASH_UP" = "true" ]; then
    ok "Wazuh Dashboard is up (port 5601)"
else
    warn "Wazuh Dashboard not responding yet — it may still be loading"
fi

# ─────────────────────────────────────────────
# STEP 3: Start DeceptiCloud (Backend + Frontend)
# ─────────────────────────────────────────────
print_section "STARTING DECEPTICLOUD"

# Kill any existing DeceptiCloud processes
pkill -f "launch_decepticloud_v2.py" 2>/dev/null || true
pkill -f "model_api.py"              2>/dev/null || true
pkill -f "routing_proxy.py"          2>/dev/null || true
pkill -f "dashboard/app.py"          2>/dev/null || true
pkill -f "log_ingestion_service.py"  2>/dev/null || true
sleep 2

# Use venv Python if available
PYTHON="$BASE_DIR/venv/bin/python3"
[ -f "$PYTHON" ] || PYTHON="python3"
info "Using Python: $PYTHON"

# Launch DeceptiCloud (all services in one process)
info "Launching DeceptiCloud platform..."
nohup "$PYTHON" "$BASE_DIR/launch_decepticloud_v2.py" \
    > "$LOG_DIR/decepticloud.log" 2>&1 &
DECEPTICLOUD_PID=$!
echo $DECEPTICLOUD_PID > "$LOG_DIR/decepticloud.pid"
info "DeceptiCloud PID: $DECEPTICLOUD_PID"

# Wait for ML API (heaviest component — TF model loading)
info "Waiting for ML API to load TensorFlow models (up to 60s)..."
ML_UP=false
for i in $(seq 1 20); do
    CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/health 2>/dev/null || echo "000")
    if [ "$CODE" = "200" ]; then
        ML_UP=true
        break
    fi
    sleep 3
done
[ "$ML_UP" = "true" ] && ok "ML Detection API is up (port 5000)" || warn "ML API still loading..."

# Wait for Routing Proxy
info "Waiting for Routing Proxy..."
PROXY_UP=false
for i in $(seq 1 10); do
    CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ 2>/dev/null || echo "000")
    if [ "$CODE" = "200" ] || [ "$CODE" = "404" ]; then
        PROXY_UP=true
        break
    fi
    sleep 2
done
[ "$PROXY_UP" = "true" ] && ok "Routing Proxy is up (port 8080)" || warn "Proxy still starting..."

# Wait for DeceptiCloud Dashboard
info "Waiting for DeceptiCloud Dashboard..."
DC_DASH_UP=false
for i in $(seq 1 10); do
    CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/ 2>/dev/null || echo "000")
    if [ "$CODE" = "200" ] || [ "$CODE" = "302" ]; then
        DC_DASH_UP=true
        break
    fi
    sleep 2
done
[ "$DC_DASH_UP" = "true" ] && ok "DeceptiCloud Dashboard is up (port 9000)" || warn "Dashboard still starting..."

# Start Wazuh Log Ingestion (connects Wazuh alerts → DeceptiCloud DB)
info "Starting Wazuh log ingestion service..."
nohup "$PYTHON" "$BASE_DIR/wazuh/log_ingestion_service.py" \
    > "$LOG_DIR/wazuh_ingestion.log" 2>&1 &
echo $! > "$LOG_DIR/wazuh_ingestion.pid"
ok "Wazuh log ingestion service started"

# ─────────────────────────────────────────────
# STEP 4: Summary
# ─────────────────────────────────────────────
print_section "SYSTEM READY"

echo -e "
  ${BOLD}${CYAN}WAZUH SIEM${RESET}
  ${GREEN}  Dashboard  →${RESET}  http://localhost:5601        ${DIM}(admin / SecretPassword1!)${RESET}
  ${GREEN}  Manager API→${RESET}  https://localhost:55000
  ${GREEN}  Indexer    →${RESET}  https://localhost:9200

  ${BOLD}${CYAN}DECEPTICLOUD PLATFORM${RESET}
  ${GREEN}  Dashboard  →${RESET}  http://localhost:9000        ${DIM}(admin / DeceptiCloud)${RESET}
  ${GREEN}  ML API     →${RESET}  http://localhost:5000
  ${GREEN}  Proxy      →${RESET}  http://localhost:8080
  ${GREEN}  Real Sites →${RESET}  http://localhost:3001–3007
  ${YELLOW}  Honeypots  →${RESET}  http://localhost:4001–4007

  ${DIM}Logs: $LOG_DIR/${RESET}
  ${DIM}To stop everything: bash stop_decepticloud.sh${RESET}
"
