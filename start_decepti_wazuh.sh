#!/bin/bash
################################################################################
# DeceptiCloud + Wazuh - Complete System Startup Script
# Starts all components: Wazuh Stack + Adaptive Engine + Dashboard
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
echo "════════════════════════════════════════════════════════════════"
echo "  DeceptiCloud + Wazuh - System Startup"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check if running from correct directory
if [ ! -f "dashboard/app.py" ] || [ ! -f "adaptive_engine/engine.py" ]; then
    log_error "Please run this script from the project root directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    log_error "Virtual environment not found. Please create it first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

################################################################################
# STEP 1: Start Wazuh Stack (Docker)
################################################################################
log_info "Step 1/4: Starting Wazuh Stack..."

if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed or not in PATH"
    exit 1
fi

# Check if Wazuh containers are already running
WAZUH_RUNNING=$(docker ps --filter "name=wazuh" --format "{{.Names}}" | wc -l)

if [ "$WAZUH_RUNNING" -eq 3 ]; then
    log_warning "Wazuh containers already running. Skipping..."
else
    log_info "Starting Wazuh Docker containers..."
    cd wazuh-docker/single-node
    docker compose up -d
    cd ../..
    
    log_info "Waiting for Wazuh Indexer to be healthy..."
    RETRY_COUNT=0
    MAX_RETRIES=30
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        HEALTH=$(docker inspect --format='{{.State.Health.Status}}' single-node-wazuh.indexer 2>/dev/null || echo "starting")
        if [ "$HEALTH" = "healthy" ]; then
            log_success "Wazuh Indexer is healthy"
            break
        fi
        echo -n "."
        sleep 2
        RETRY_COUNT=$((RETRY_COUNT + 1))
    done
    echo ""
    
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        log_error "Wazuh Indexer failed to become healthy"
        exit 1
    fi
    
    log_info "Waiting for Wazuh services to initialize (15 seconds)..."
    sleep 15
fi

# Verify Wazuh containers
INDEXER_STATUS=$(docker inspect --format='{{.State.Status}}' single-node-wazuh.indexer 2>/dev/null || echo "not found")
MANAGER_STATUS=$(docker inspect --format='{{.State.Status}}' single-node-wazuh.manager 2>/dev/null || echo "not found")
DASHBOARD_STATUS=$(docker inspect --format='{{.State.Status}}' single-node-wazuh.dashboard 2>/dev/null || echo "not found")

if [ "$INDEXER_STATUS" = "running" ] && [ "$MANAGER_STATUS" = "running" ] && [ "$DASHBOARD_STATUS" = "running" ]; then
    log_success "Wazuh Stack is running"
    echo "  ✓ Indexer:   Port 9200"
    echo "  ✓ Manager:   Port 55000"
    echo "  ✓ Dashboard: Port 5601"
else
    log_error "Wazuh containers failed to start properly"
    echo "  Indexer:   $INDEXER_STATUS"
    echo "  Manager:   $MANAGER_STATUS"
    echo "  Dashboard: $DASHBOARD_STATUS"
    exit 1
fi

################################################################################
# STEP 2: Start Adaptive Learning Engine
################################################################################
log_info "Step 2/4: Starting Adaptive Learning Engine..."

# Check if already running
ENGINE_PID=$(pgrep -f "python.*adaptive_engine/engine.py" || echo "")

if [ -n "$ENGINE_PID" ]; then
    log_warning "Adaptive Engine already running (PID: $ENGINE_PID). Skipping..."
else
    log_info "Starting Adaptive Engine..."
    
    # Create logs directory if it doesn't exist
    mkdir -p logs
    
    # Start engine in background
    nohup venv/bin/python3 adaptive_engine/engine.py > logs/adaptive_engine.log 2>&1 &
    ENGINE_PID=$!
    echo $ENGINE_PID > logs/adaptive_engine.pid
    
    log_info "Waiting for Adaptive Engine to initialize..."
    sleep 5
    
    # Verify it's running
    if ps -p $ENGINE_PID > /dev/null 2>&1; then
        log_success "Adaptive Engine started (PID: $ENGINE_PID)"
        
        # Check if state file is being created
        if [ -f "adaptive_engine/engine_state.json" ]; then
            log_success "Engine state file created"
        else
            log_warning "Engine state file not yet created (will be created within 60 seconds)"
        fi
    else
        log_error "Adaptive Engine failed to start. Check logs/adaptive_engine.log"
        exit 1
    fi
fi

################################################################################
# STEP 3: Start DeceptiCloud Dashboard
################################################################################
log_info "Step 3/4: Starting DeceptiCloud Dashboard..."

# Check if already running
DASHBOARD_PID=$(pgrep -f "python.*dashboard/app.py" || echo "")

if [ -n "$DASHBOARD_PID" ]; then
    log_warning "Dashboard already running (PID: $DASHBOARD_PID). Skipping..."
else
    log_info "Starting Dashboard..."
    
    # Start dashboard in background
    nohup venv/bin/python3 dashboard/app.py > logs/dashboard.log 2>&1 &
    DASHBOARD_PID=$!
    echo $DASHBOARD_PID > logs/dashboard.pid
    
    log_info "Waiting for Dashboard to initialize..."
    sleep 5
    
    # Verify it's running
    if ps -p $DASHBOARD_PID > /dev/null 2>&1; then
        log_success "Dashboard started (PID: $DASHBOARD_PID)"
        
        # Check if port 9000 is listening
        if lsof -i:9000 > /dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":9000"; then
            log_success "Dashboard listening on port 9000"
        else
            log_warning "Dashboard may not be listening on port 9000 yet"
        fi
    else
        log_error "Dashboard failed to start. Check logs/dashboard.log"
        exit 1
    fi
fi

################################################################################
# STEP 4: System Health Check
################################################################################
log_info "Step 4/4: Running system health check..."

sleep 3

# Check Wazuh
WAZUH_HEALTH=0
if docker ps --filter "name=wazuh" --format "{{.Names}}" | grep -q "wazuh.indexer"; then
    WAZUH_HEALTH=$((WAZUH_HEALTH + 1))
fi
if docker ps --filter "name=wazuh" --format "{{.Names}}" | grep -q "wazuh.manager"; then
    WAZUH_HEALTH=$((WAZUH_HEALTH + 1))
fi
if docker ps --filter "name=wazuh" --format "{{.Names}}" | grep -q "wazuh.dashboard"; then
    WAZUH_HEALTH=$((WAZUH_HEALTH + 1))
fi

# Check Adaptive Engine
ENGINE_RUNNING=0
if pgrep -f "python.*adaptive_engine/engine.py" > /dev/null; then
    ENGINE_RUNNING=1
fi

# Check Dashboard
DASHBOARD_RUNNING=0
if pgrep -f "python.*dashboard/app.py" > /dev/null; then
    DASHBOARD_RUNNING=1
fi

# Test Dashboard API
API_WORKING=0
if curl -s http://localhost:9000 > /dev/null 2>&1; then
    API_WORKING=1
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  System Status"
echo "════════════════════════════════════════════════════════════════"
echo ""

if [ $WAZUH_HEALTH -eq 3 ]; then
    echo -e "  ${GREEN}✓${NC} Wazuh Stack:        RUNNING (3/3 containers)"
else
    echo -e "  ${RED}✗${NC} Wazuh Stack:        PARTIAL ($WAZUH_HEALTH/3 containers)"
fi

if [ $ENGINE_RUNNING -eq 1 ]; then
    echo -e "  ${GREEN}✓${NC} Adaptive Engine:    RUNNING"
else
    echo -e "  ${RED}✗${NC} Adaptive Engine:    NOT RUNNING"
fi

if [ $DASHBOARD_RUNNING -eq 1 ]; then
    echo -e "  ${GREEN}✓${NC} DeceptiCloud:       RUNNING"
else
    echo -e "  ${RED}✗${NC} DeceptiCloud:       NOT RUNNING"
fi

if [ $API_WORKING -eq 1 ]; then
    echo -e "  ${GREEN}✓${NC} Dashboard API:      RESPONDING"
else
    echo -e "  ${YELLOW}⚠${NC} Dashboard API:      NOT RESPONDING YET"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Access Information"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "  DeceptiCloud Dashboard:"
echo "    URL:      http://localhost:9000"
echo "    Login:    admin / DeceptiCloud"
echo ""
echo "  Wazuh Dashboard:"
echo "    URL:      http://localhost:5601"
echo "    Login:    admin / SecretPassword"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Logs"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "  Adaptive Engine:  logs/adaptive_engine.log"
echo "  Dashboard:        logs/dashboard.log"
echo "  Wazuh:            docker logs single-node-wazuh.manager"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Management"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "  Stop system:      ./stop_decepti_wazuh.sh"
echo "  View logs:        tail -f logs/dashboard.log"
echo "  Check status:     docker ps && ps aux | grep python"
echo ""

# Final status
TOTAL_HEALTH=$((WAZUH_HEALTH + ENGINE_RUNNING + DASHBOARD_RUNNING))

if [ $TOTAL_HEALTH -eq 5 ]; then
    log_success "All systems operational! 🎉"
    exit 0
elif [ $TOTAL_HEALTH -ge 3 ]; then
    log_warning "System partially operational. Check logs for details."
    exit 0
else
    log_error "System failed to start properly. Check logs for details."
    exit 1
fi
