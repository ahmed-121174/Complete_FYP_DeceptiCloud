#!/bin/bash
################################################################################
# DeceptiCloud + Wazuh - Complete System Shutdown Script
# Stops all components: Dashboard + Adaptive Engine + Wazuh Stack
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
echo "  DeceptiCloud + Wazuh - System Shutdown"
echo "════════════════════════════════════════════════════════════════"
echo ""

################################################################################
# STEP 1: Stop DeceptiCloud Dashboard
################################################################################
log_info "Step 1/4: Stopping DeceptiCloud Dashboard..."

# Try to stop using PID file
if [ -f "logs/dashboard.pid" ]; then
    DASHBOARD_PID=$(cat logs/dashboard.pid)
    if ps -p $DASHBOARD_PID > /dev/null 2>&1; then
        log_info "Stopping Dashboard (PID: $DASHBOARD_PID)..."
        kill $DASHBOARD_PID 2>/dev/null || true
        sleep 2
        
        # Force kill if still running
        if ps -p $DASHBOARD_PID > /dev/null 2>&1; then
            log_warning "Dashboard didn't stop gracefully, forcing..."
            kill -9 $DASHBOARD_PID 2>/dev/null || true
        fi
        
        rm -f logs/dashboard.pid
        log_success "Dashboard stopped"
    else
        log_warning "Dashboard PID file exists but process not running"
        rm -f logs/dashboard.pid
    fi
else
    log_info "No Dashboard PID file found, searching for process..."
fi

# Kill any remaining dashboard processes
DASHBOARD_PIDS=$(pgrep -f "python.*dashboard/app.py" || echo "")
if [ -n "$DASHBOARD_PIDS" ]; then
    log_info "Found running Dashboard processes: $DASHBOARD_PIDS"
    for PID in $DASHBOARD_PIDS; do
        kill $PID 2>/dev/null || true
    done
    sleep 2
    
    # Force kill if still running
    DASHBOARD_PIDS=$(pgrep -f "python.*dashboard/app.py" || echo "")
    if [ -n "$DASHBOARD_PIDS" ]; then
        log_warning "Force killing Dashboard processes..."
        pkill -9 -f "python.*dashboard/app.py" 2>/dev/null || true
    fi
    log_success "All Dashboard processes stopped"
else
    log_info "No Dashboard processes found"
fi

# Clear port 9000 if still in use
if lsof -i:9000 > /dev/null 2>&1; then
    log_warning "Port 9000 still in use, clearing..."
    lsof -ti:9000 | xargs kill -9 2>/dev/null || true
fi

################################################################################
# STEP 2: Stop Adaptive Learning Engine
################################################################################
log_info "Step 2/4: Stopping Adaptive Learning Engine..."

# Try to stop using PID file
if [ -f "logs/adaptive_engine.pid" ]; then
    ENGINE_PID=$(cat logs/adaptive_engine.pid)
    if ps -p $ENGINE_PID > /dev/null 2>&1; then
        log_info "Stopping Adaptive Engine (PID: $ENGINE_PID)..."
        kill $ENGINE_PID 2>/dev/null || true
        sleep 2
        
        # Force kill if still running
        if ps -p $ENGINE_PID > /dev/null 2>&1; then
            log_warning "Engine didn't stop gracefully, forcing..."
            kill -9 $ENGINE_PID 2>/dev/null || true
        fi
        
        rm -f logs/adaptive_engine.pid
        log_success "Adaptive Engine stopped"
    else
        log_warning "Engine PID file exists but process not running"
        rm -f logs/adaptive_engine.pid
    fi
else
    log_info "No Engine PID file found, searching for process..."
fi

# Kill any remaining engine processes
ENGINE_PIDS=$(pgrep -f "python.*adaptive_engine/engine.py" || echo "")
if [ -n "$ENGINE_PIDS" ]; then
    log_info "Found running Engine processes: $ENGINE_PIDS"
    for PID in $ENGINE_PIDS; do
        kill $PID 2>/dev/null || true
    done
    sleep 2
    
    # Force kill if still running
    ENGINE_PIDS=$(pgrep -f "python.*adaptive_engine/engine.py" || echo "")
    if [ -n "$ENGINE_PIDS" ]; then
        log_warning "Force killing Engine processes..."
        pkill -9 -f "python.*adaptive_engine/engine.py" 2>/dev/null || true
    fi
    log_success "All Engine processes stopped"
else
    log_info "No Engine processes found"
fi

################################################################################
# STEP 3: Stop Wazuh Stack (Docker)
################################################################################
log_info "Step 3/4: Stopping Wazuh Stack..."

if ! command -v docker &> /dev/null; then
    log_warning "Docker is not installed or not in PATH, skipping Wazuh shutdown"
else
    # Check if Wazuh containers are running
    WAZUH_RUNNING=$(docker ps --filter "name=wazuh" --format "{{.Names}}" | wc -l)
    
    if [ "$WAZUH_RUNNING" -eq 0 ]; then
        log_info "No Wazuh containers running"
    else
        log_info "Stopping $WAZUH_RUNNING Wazuh container(s)..."
        
        # Stop containers gracefully
        docker stop single-node-wazuh.dashboard 2>/dev/null || log_warning "Dashboard container not found"
        docker stop single-node-wazuh.manager 2>/dev/null || log_warning "Manager container not found"
        docker stop single-node-wazuh.indexer 2>/dev/null || log_warning "Indexer container not found"
        
        log_success "Wazuh containers stopped"
    fi
fi

################################################################################
# STEP 4: Cleanup and Verification
################################################################################
log_info "Step 4/4: Cleanup and verification..."

# Clean up any remaining Python processes related to the project
log_info "Checking for any remaining project processes..."
REMAINING=$(ps aux | grep -E "(dashboard|adaptive_engine)" | grep python | grep -v grep | wc -l)

if [ "$REMAINING" -gt 0 ]; then
    log_warning "Found $REMAINING remaining processes, cleaning up..."
    pkill -f "python.*dashboard" 2>/dev/null || true
    pkill -f "python.*adaptive_engine" 2>/dev/null || true
    sleep 1
fi

# Verify all stopped
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Shutdown Status"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check Dashboard
DASHBOARD_RUNNING=$(pgrep -f "python.*dashboard/app.py" | wc -l)
if [ "$DASHBOARD_RUNNING" -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} Dashboard:          STOPPED"
else
    echo -e "  ${RED}✗${NC} Dashboard:          STILL RUNNING ($DASHBOARD_RUNNING processes)"
fi

# Check Engine
ENGINE_RUNNING=$(pgrep -f "python.*adaptive_engine/engine.py" | wc -l)
if [ "$ENGINE_RUNNING" -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} Adaptive Engine:    STOPPED"
else
    echo -e "  ${RED}✗${NC} Adaptive Engine:    STILL RUNNING ($ENGINE_RUNNING processes)"
fi

# Check Wazuh
if command -v docker &> /dev/null; then
    WAZUH_RUNNING=$(docker ps --filter "name=wazuh" --format "{{.Names}}" | wc -l)
    if [ "$WAZUH_RUNNING" -eq 0 ]; then
        echo -e "  ${GREEN}✓${NC} Wazuh Stack:        STOPPED"
    else
        echo -e "  ${RED}✗${NC} Wazuh Stack:        STILL RUNNING ($WAZUH_RUNNING containers)"
    fi
else
    echo -e "  ${YELLOW}⚠${NC} Wazuh Stack:        DOCKER NOT AVAILABLE"
fi

# Check ports
PORT_9000=$(lsof -i:9000 2>/dev/null | wc -l)
PORT_5601=$(lsof -i:5601 2>/dev/null | wc -l)

if [ "$PORT_9000" -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} Port 9000:          FREE"
else
    echo -e "  ${YELLOW}⚠${NC} Port 9000:          IN USE"
fi

if [ "$PORT_5601" -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} Port 5601:          FREE"
else
    echo -e "  ${YELLOW}⚠${NC} Port 5601:          IN USE"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Additional Information"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "  Logs preserved in:  logs/"
echo "  State file:         adaptive_engine/engine_state.json"
echo "  Database:           database/decepticloud.db"
echo ""
echo "  To restart system:  ./start_decepti_wazuh.sh"
echo ""

# Calculate total stopped
TOTAL_STOPPED=0
if [ "$DASHBOARD_RUNNING" -eq 0 ]; then TOTAL_STOPPED=$((TOTAL_STOPPED + 1)); fi
if [ "$ENGINE_RUNNING" -eq 0 ]; then TOTAL_STOPPED=$((TOTAL_STOPPED + 1)); fi
if command -v docker &> /dev/null && [ "$WAZUH_RUNNING" -eq 0 ]; then TOTAL_STOPPED=$((TOTAL_STOPPED + 1)); fi

if [ $TOTAL_STOPPED -eq 3 ]; then
    log_success "All systems stopped successfully! ✓"
    exit 0
elif [ $TOTAL_STOPPED -ge 2 ]; then
    log_warning "Most systems stopped. Some processes may still be running."
    echo ""
    echo "To force kill all remaining processes, run:"
    echo "  pkill -9 -f 'python.*(dashboard|adaptive_engine)'"
    echo "  docker stop \$(docker ps -q --filter 'name=wazuh')"
    exit 0
else
    log_error "Failed to stop some systems. Manual intervention may be required."
    echo ""
    echo "Check running processes:"
    echo "  ps aux | grep -E '(dashboard|adaptive_engine|wazuh)'"
    echo ""
    echo "Force stop commands:"
    echo "  pkill -9 -f 'python.*(dashboard|adaptive_engine)'"
    echo "  docker stop \$(docker ps -q --filter 'name=wazuh')"
    exit 1
fi
