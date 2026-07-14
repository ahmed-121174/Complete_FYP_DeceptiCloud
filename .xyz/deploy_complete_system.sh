#!/bin/bash

# AI-DRIVEN CYBER DECEPTION SYSTEM - MASTER DEPLOYMENT SCRIPT

# This script runs the ENTIRE project:

# 1. Environment setup

# 2. Train both ML models

# 3. Start ML API server

# 4. Start honeypot websites

# 5. Display access information

# Usage: ./deploy_complete_system.sh


set -e  # Exit on error

# Colors

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project root

PROJECT_ROOT="/home/irtaza-butt/Desktop/Ahmed Fype-II"
cd "$PROJECT_ROOT"

# Log file

LOG_FILE="logs/deployment_$(date +%Y%m%d_%H%M%S).log"
mkdir -p logs

# Function to log messages

log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

# Function to print section header

print_header() {
    log "\n${CYAN}================================================================================${NC}"
    log "${CYAN}$1${NC}"
    log "${CYAN}================================================================================${NC}\n"
}

# Cleanup function

cleanup() {
    log "\n${YELLOW}Cleaning up processes...${NC}"
    kill $(jobs -p) 2>/dev/null || true
    log "${GREEN} Cleanup complete${NC}"
}

# Trap cleanup on exit

trap cleanup EXIT

# MAIN DEPLOYMENT SCRIPT


print_header "AI-DRIVEN CYBER DECEPTION SYSTEM - COMPLETE DEPLOYMENT"
log "${BLUE}Started at: $(date)${NC}"
log "${BLUE}Log file: $LOG_FILE${NC}"

# STEP 1: Environment Setup

print_header "STEP 1/6: ENVIRONMENT SETUP"

log "${YELLOW}Creating virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    log "${GREEN} Virtual environment created${NC}"
else
    log "${GREEN} Virtual environment already exists${NC}"
fi

log "\n${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate
log "${GREEN} Virtual environment activated${NC}"

log "\n${YELLOW}Installing dependencies...${NC}"
pip install -q --upgrade pip setuptools wheel
pip install -q pandas numpy scikit-learn tensorflow matplotlib seaborn flask flask-cors pyyaml requests joblib 2>&1 | tee -a "$LOG_FILE"
log "${GREEN} Dependencies installed${NC}"

log "\n${YELLOW}Creating directory structure...${NC}"
mkdir -p models plots logs config
log "${GREEN} Directories created${NC}"

# STEP 2: Dataset Analysis (Quick)

print_header "STEP 2/6: DATASET ANALYSIS"

log "${YELLOW}Analyzing datasets...${NC}"
if [ -f "analyze_datasets.py" ]; then
    timeout 60 python analyze_datasets.py 2>&1 | head -100 | tee -a "$LOG_FILE" || log "${YELLOW}  Analysis timed out (non-critical)${NC}"
    log "${GREEN} Dataset analysis complete (or skipped)${NC}"
else
    log "${YELLOW}  Dataset analysis script not found (skipping)${NC}"
fi

# STEP 3: Train ML Models

print_header "STEP 3/6: TRAINING MACHINE LEARNING MODELS"

# Check if models already exist

if [ -f "models/web_attack_detector.keras" ] && [ -f "models/ddos_detector.keras" ]; then
    log "${YELLOW}Models already exist. Skipping training.${NC}"
    log "${BLUE}To retrain, delete models/ directory and run again.${NC}"
else
    log "${YELLOW}Training Web Attack Detection Model...${NC}"
    log "${BLUE}This may take 15-30 minutes. Please be patient...${NC}"
    cd ml_pipeline
    python train_web_attack.py 2>&1 | tee -a "../$LOG_FILE"
    cd ..
    log "${GREEN} Web Attack model trained${NC}"
    
    log "\n${YELLOW}Training DDoS Detection Model...${NC}"
    log "${BLUE}This may take 15-30 minutes. Please be patient...${NC}"
    cd ml_pipeline
    python train_ddos.py 2>&1 | tee -a "../$LOG_FILE"
    cd ..
    log "${GREEN} DDoS model trained${NC}"
fi

# Verify models

if [ -f "models/web_attack_detector.keras" ] && [ -f "models/ddos_detector.keras" ]; then
    log "\n${GREEN} Both models are ready!${NC}"
    log "\n${BLUE}Model files:${NC}"
    ls -lh models/*.keras | tee -a "$LOG_FILE"
else
    log "${RED} Model training failed! Check logs.${NC}"
    exit 1
fi

# STEP 4: Start ML API Server

print_header "STEP 4/6: STARTING ML API SERVER"

log "${YELLOW}Starting ML API on port 5000...${NC}"
cd ml_pipeline
python model_api.py > "../logs/ml_api.log" 2>&1 &
ML_API_PID=$!
cd ..

# Wait for ML API to start

log "${YELLOW}Waiting for ML API to initialize...${NC}"
sleep 5

# Check if ML API is running

if kill -0 $ML_API_PID 2>/dev/null; then
    log "${GREEN} ML API started (PID: $ML_API_PID)${NC}"
    
    # Test health endpoint

    if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
        log "${GREEN} ML API health check passed${NC}"
    else
        log "${YELLOW}  ML API health check failed (may need more time)${NC}"
    fi
else
    log "${RED} ML API failed to start${NC}"
    exit 1
fi

# STEP 5: Start Honeypot Websites

print_header "STEP 5/6: STARTING HONEYPOT WEBSITES"

# Create simple honeypot templates directory

mkdir -p honeypot/templates/ecommerce
mkdir -p honeypot/templates/banking
mkdir -p honeypot/templates/admin

# Create basic HTML template if it doesn't exist

if [ ! -f "honeypot/templates/ecommerce/index.html" ]; then
    cat > honeypot/templates/ecommerce/index.html <<'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>SecureShop - E-Commerce Platform</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
        h1 { color: #333; }
        .product { display: inline-block; margin: 20px; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
        .search-box { padding: 10px; width: 300px; margin: 20px 0; }
        .login-link { float: right; color: #007bff; }
    </style>
</head>
<body>
    <div class="container">
        <h1> SecureShop</h1>
        <a href="/login" class="login-link">Login</a>
        <form action="/search" method="get">
            <input type="text" name="q" class="search-box" placeholder="Search products...">
            <button type="submit">Search</button>
        </form>
        <h2>Featured Products</h2>
        <div class="product">
            <h3>Laptop Pro</h3>
            <p>$999.99</p>
            <button>Add to Cart</button>
        </div>
        <div class="product">
            <h3>Smartphone X</h3>
            <p>$699.99</p>
            <button>Add to Cart</button>
        </div>
        <div class="product">
            <h3>Tablet Ultra</h3>
            <p>$499.99</p>
            <button>Add to Cart</button>
        </div>
    </div>
</body>
</html>
EOF
fi

# Copy templates for other services

cp -r honeypot/templates/ecommerce honeypot/templates/banking 2>/dev/null || true
cp -r honeypot/templates/ecommerce honeypot/templates/admin 2>/dev/null || true
cp -r honeypot/templates/ecommerce honeypot/templates/api 2>/dev/null || true
cp -r honeypot/templates/ecommerce honeypot/templates/corporate 2>/dev/null || true

# Start deceptive honeypots

log "${YELLOW}Starting 5 deceptive honeypots (ports 8080-8084)...${NC}"

for i in {0..4}; do
    PORT=$((8080 + i))
    SERVICES=("ecommerce" "banking" "admin" "api" "corporate")
    SERVICE=${SERVICES[$i]}
    
    cd honeypot
    HONEYPOT_TYPE=deceptive HONEYPOT_SERVICE=$SERVICE ML_API_URL=http://localhost:5000 PORT=$PORT \
        python app.py > "../logs/honeypot_deceptive_${SERVICE}.log" 2>&1 &
    HONEYPOT_PIDS[$i]=$!
    cd ..
    
    log "${GREEN} Deceptive honeypot #$((i+1)) ($SERVICE) started on port $PORT (PID: ${HONEYPOT_PIDS[$i]})${NC}"
    sleep 1
done

# Start legitimate honeypots

log "\n${YELLOW}Starting 5 legitimate honeypots (ports 8085-8089)...${NC}"

for i in {0..4}; do
    PORT=$((8085 + i))
    SERVICES=("ecommerce" "banking" "admin" "api" "corporate")
    SERVICE=${SERVICES[$i]}
    
    cd honeypot
    HONEYPOT_TYPE=legitimate HONEYPOT_SERVICE=$SERVICE ML_API_URL=http://localhost:5000 PORT=$PORT \
        python app.py > "../logs/honeypot_legitimate_${SERVICE}.log" 2>&1 &
    HONEYPOT_PIDS_LEG[$i]=$!
    cd ..
    
    log "${GREEN} Legitimate honeypot #$((i+1)) ($SERVICE) started on port $PORT (PID: ${HONEYPOT_PIDS_LEG[$i]})${NC}"
    sleep 1
done

# STEP 6: System Status & Access Information

print_header "STEP 6/6: SYSTEM STATUS"

log "${GREEN} ALL SYSTEMS DEPLOYED SUCCESSFULLY!${NC}\n"

log "${MAGENTA}${NC}"
log "${MAGENTA}                    SYSTEM ACCESS INFORMATION                              ${NC}"
log "${MAGENTA}${NC}"
log "${MAGENTA}                                                                           ${NC}"
log "${MAGENTA}  ${CYAN}ML API (Detection Engine):${NC}                                             ${MAGENTA}${NC}"
log "${MAGENTA}    ${GREEN}• http://localhost:5000${NC}                                              ${MAGENTA}${NC}"
log "${MAGENTA}    ${GREEN}• Health: http://localhost:5000/api/health${NC}                           ${MAGENTA}${NC}"
log "${MAGENTA}                                                                           ${NC}"
log "${MAGENTA}  ${CYAN}Deceptive Honeypots (Trap Attackers):${NC}                                  ${MAGENTA}${NC}"
log "${MAGENTA}    ${YELLOW}• E-commerce:  http://localhost:8080${NC}                                 ${MAGENTA}${NC}"
log "${MAGENTA}    ${YELLOW}• Banking:     http://localhost:8081${NC}                                 ${MAGENTA}${NC}"
log "${MAGENTA}    ${YELLOW}• Admin:       http://localhost:8082${NC}                                 ${MAGENTA}${NC}"
log "${MAGENTA}    ${YELLOW}• API:         http://localhost:8083${NC}                                 ${MAGENTA}${NC}"
log "${MAGENTA}    ${YELLOW}• Corporate:   http://localhost:8084${NC}                                 ${MAGENTA}${NC}"
log "${MAGENTA}                                                                           ${NC}"
log "${MAGENTA}  ${CYAN}Legitimate Honeypots (Serve Real Users):${NC}                                ${MAGENTA}${NC}"
log "${MAGENTA}    ${BLUE}• E-commerce:  http://localhost:8085${NC}                                 ${MAGENTA}${NC}"
log "${MAGENTA}    ${BLUE}• Banking:     http://localhost:8086${NC}                                 ${MAGENTA}${NC}"
log "${MAGENTA}    ${BLUE}• Admin:       http://localhost:8087${NC}                                 ${MAGENTA}${NC}"
log "${MAGENTA}    ${BLUE}• API:         http://localhost:8088${NC}                                 ${MAGENTA}${NC}"
log "${MAGENTA}    ${BLUE}• Corporate:   http://localhost:8089${NC}                                 ${MAGENTA}${NC}"
log "${MAGENTA}                                                                           ${NC}"
log "${MAGENTA}${NC}\n"

log "${BLUE} Model Performance:${NC}"
if [ -f "models/web_attack_detector.json" ]; then
    log "${GREEN}   • Web Attack Detector: Ready${NC}"
fi
if [ -f "models/ddos_detector.json" ]; then
    log "${GREEN}   • DDoS Detector: Ready${NC}"
fi

log "\n${BLUE} Log Files:${NC}"
log "   • Deployment: $LOG_FILE"
log "   • ML API: logs/ml_api.log"
log "   • Honeypots: logs/honeypot_*.log"
log "   • Training: logs/*_training.log"

log "\n${BLUE} Quick Tests:${NC}"
log "${YELLOW}# Test ML API${NC}"
log "curl http://localhost:5000/api/health"
log ""
log "${YELLOW}# Test Honeypot${NC}"
log "curl http://localhost:8080"
log ""
log "${YELLOW}# Simulate Attack${NC}"
log "curl \"http://localhost:8080/search?q='+UNION+SELECT+*+FROM+users--\""

log "\n${BLUE} Stop All Services:${NC}"
log "kill $ML_API_PID ${HONEYPOT_PIDS[@]} ${HONEYPOT_PIDS_LEG[@]}"

log "\n${GREEN} System is running. Press Ctrl+C to stop all services.${NC}"
log "${YELLOW} Keeping services alive...${NC}\n"

# Keep running and monitor


# Function to check service health

check_health() {
    local dead_services=0
    
    # Check ML API

    if ! kill -0 $ML_API_PID 2>/dev/null; then
        log "${RED} ML API died!${NC}"
        ((dead_services++))
    fi
    
    # Check honeypots

    for pid in ${HONEYPOT_PIDS[@]} ${HONEYPOT_PIDS_LEG[@]}; do
        if ! kill -0 $pid 2>/dev/null; then
            ((dead_services++))
        fi
    done
    
    if [ $dead_services -gt 0 ]; then
        log "${RED}  $dead_services service(s) died. Check logs.${NC}"
    fi
}

# Monitor services every 30 seconds

while true; do
    sleep 30
    check_health
done
