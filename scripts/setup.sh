#!/bin/bash

# AI-Driven Cyber Deception System - Setup Script

# This script sets up the entire system from scratch


set -e  # Exit on error


echo "AI-DRIVEN CYBER DECEPTION SYSTEM - SETUP"


# Colors for output

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output

print_success() {
    echo -e "${GREEN} $1${NC}"
}

print_error() {
    echo -e "${RED} $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ  $1${NC}"
}

# Check prerequisites


print_info "Checking prerequisites..."

# Check Python

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    exit 1
fi
print_success "Python 3 found"

# Check virtual environment

if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment exists"
fi

# Activate virtual environment

print_info "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Install Python dependencies

print_info "Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
print_success "Python dependencies installed"

# Create necessary directories

print_info "Creating directory structure..."
mkdir -p models plots logs config
print_success "Directories created"

# Dataset Analysis


echo "DATASET ANALYSIS"

print_info "Analyzing datasets..."
python analyze_datasets.py
print_success "Dataset analysis complete"

# Train Web Attack Model


echo "CHECKING WEB ATTACK DETECTION MODEL"

if [ -f "ml_pipeline/models/web_attack_detector_v2.keras" ]; then
    print_success "Web Attack model (V2) already exists. Skipping training."
else
    print_info "Training Web Attack Model V2..."
    print_info "This may take 15-30 minutes depending on your hardware..."
    cd ml_pipeline
    python train_web_attack_v2.py
    cd ..
    print_success "Web Attack model trained"
fi

# Train DDoS Model


echo "CHECKING DDOS DETECTION MODEL"

if [ -f "ml_pipeline/models/ddos_detector.keras" ]; then
    print_success "DDoS model already exists. Skipping training."
else
    print_info "Training DDoS Model..."
    print_info "This may take 15-30 minutes depending on your hardware..."
    cd ml_pipeline
    # Using the sampled training script to ensure completion

    if [ -f "train_ddos_sampled.py" ]; then
        python train_ddos_sampled.py
    else
        python train_ddos.py
    fi
    cd ..
    print_success "DDoS model trained"
fi

# Create rotation configuration


print_info "Creating rotation configuration..."
cat > config/rotation_config.json <<EOF
{
  "rotation_interval_seconds": 300,
  "ip_pool": [
    "10.0.1.10", "10.0.1.11", "10.0.1.12", "10.0.1.13", "10.0.1.14",
    "10.0.1.15", "10.0.1.16", "10.0.1.17", "10.0.1.18", "10.0.1.19"
  ],
  "port_pool": [8080, 8081, 8082, 8083, 8084, 8085, 8086, 8087, 8088, 8089],
  "kubernetes_enabled": false,
  "kubernetes_namespace": "cyberdefense",
  "service_name": "honeypot-service"
}
EOF
print_success "Rotation configuration created"

# Summary


echo "SETUP COMPLETE!"


print_success "Models trained and saved to models/ directory"
print_success "Configuration files created in config/ directory"

print_info "Next steps:"
echo "  1. Start ML API:     cd ml_pipeline && python model_api.py"
echo "  2. Start Honeypot:   cd honeypot && python app.py"
echo "  3. Or use Docker:    docker-compose -f docker/docker-compose.yml up"
echo "  4. Or deploy to K8s: kubectl apply -f kubernetes/"

print_info "Access points:"
echo "  - ML API:      http://localhost:5000"
echo "  - Honeypots:   http://localhost:8080-8089"

