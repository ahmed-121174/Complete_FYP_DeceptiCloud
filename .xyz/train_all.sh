#!/bin/bash

# Complete Training Script - Runs Everything in Sequence

# This script will train both ML models from scratch


set -e  # Exit on any error


echo "AI-DRIVEN CYBER DECEPTION SYSTEM - COMPLETE TRAINING"


# Colors

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Navigate to project directory

cd "/home/irtaza-butt/Desktop/Ahmed Fype-II"

echo -e "\n${YELLOW}[1/7] Setting up virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN} Virtual environment created${NC}"
else
    echo -e "${GREEN} Virtual environment exists${NC}"
fi

echo -e "\n${YELLOW}[2/7] Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN} Virtual environment activated${NC}"

echo -e "\n${YELLOW}[3/7] Installing dependencies...${NC}"
pip install -q --upgrade pip
pip install -q pandas numpy scikit-learn tensorflow matplotlib seaborn flask flask-cors pyyaml requests joblib
echo -e "${GREEN} Dependencies installed${NC}"

echo -e "\n${YELLOW}[4/7] Creating directories...${NC}"
mkdir -p models plots logs config
echo -e "${GREEN} Directories created${NC}"

echo -e "\n${YELLOW}[5/7] Training Web Attack Detection Model...${NC}"
echo "This may take 15-30 minutes..."
cd ml_pipeline
python train_web_attack.py 2>&1 | tee ../logs/web_attack_training.log
cd ..
echo -e "${GREEN} Web Attack model trained${NC}"

echo -e "\n${YELLOW}[6/7] Training DDoS Detection Model...${NC}"
echo "This may take 15-30 minutes..."
cd ml_pipeline
python train_ddos.py 2>&1 | tee ../logs/ddos_training.log
cd ..
echo -e "${GREEN} DDoS model trained${NC}"

echo -e "\n${YELLOW}[7/7] Verifying trained models...${NC}"
if [ -f "models/web_attack_detector.keras" ] && [ -f "models/ddos_detector.keras" ]; then
    echo -e "${GREEN} Both models successfully trained!${NC}"

    echo "Trained files:"
    ls -lh models/

    echo "Training plots:"
    ls -lh plots/
else
    echo " Some models are missing!"
    exit 1
fi


echo " TRAINING COMPLETE!"


echo "Models saved to:"
echo "  - models/web_attack_detector.keras"
echo "  - models/ddos_detector.keras"

echo "Training logs saved to:"
echo "  - logs/web_attack_training.log"
echo "  - logs/ddos_training.log"

echo "Next steps:"
echo "  1. Start ML API: cd ml_pipeline && python model_api.py"
echo "  2. Start Honeypot: cd honeypot && python app.py"
echo "  3. Or use Docker: docker-compose -f docker/docker-compose.yml up"

