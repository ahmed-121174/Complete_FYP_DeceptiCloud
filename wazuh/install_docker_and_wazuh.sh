#!/bin/bash
# DeceptiCloud - Docker and Wazuh Installation Script
# Installs Docker, Docker Compose, and starts Wazuh stack

set -e

CYAN='\033[96m'
GREEN='\033[92m'
YELLOW='\033[93m'
RED='\033[91m'
BOLD='\033[1m'
RESET='\033[0m'

echo -e "${CYAN}${BOLD}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         DeceptiCloud - Docker & Wazuh Installation          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${RESET}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${RESET}"
    exit 1
fi

# Step 1: Install Docker
echo -e "\n${CYAN}[1/6] Installing Docker...${RESET}"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker already installed${RESET}"
    docker --version
else
    echo "Installing Docker..."
    apt-get update
    apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release

    # Add Docker's official GPG key
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

    # Set up repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Install Docker Engine
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Start and enable Docker
    systemctl start docker
    systemctl enable docker

    echo -e "${GREEN}✓ Docker installed successfully${RESET}"
    docker --version
fi

# Step 2: Install Docker Compose (standalone)
echo -e "\n${CYAN}[2/6] Installing Docker Compose...${RESET}"
if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✓ Docker Compose already installed${RESET}"
    docker-compose --version
else
    echo "Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    echo -e "${GREEN}✓ Docker Compose installed successfully${RESET}"
    docker-compose --version
fi

# Step 3: Add current user to docker group
echo -e "\n${CYAN}[3/6] Configuring Docker permissions...${RESET}"
ACTUAL_USER=$(logname 2>/dev/null || echo $SUDO_USER)
if [ -n "$ACTUAL_USER" ]; then
    usermod -aG docker $ACTUAL_USER
    echo -e "${GREEN}✓ User $ACTUAL_USER added to docker group${RESET}"
    echo -e "${YELLOW}Note: You may need to log out and back in for group changes to take effect${RESET}"
fi

# Step 4: Configure system for Wazuh
echo -e "\n${CYAN}[4/6] Configuring system for Wazuh...${RESET}"

# Increase vm.max_map_count for OpenSearch
sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" >> /etc/sysctl.conf

# Disable swap for better performance
swapoff -a

echo -e "${GREEN}✓ System configured${RESET}"

# Step 5: Create necessary directories
echo -e "\n${CYAN}[5/6] Creating directories...${RESET}"
cd "$(dirname "$0")"
mkdir -p wazuh-config
mkdir -p ../logs

echo -e "${GREEN}✓ Directories created${RESET}"

# Step 6: Start Wazuh stack
echo -e "\n${CYAN}[6/6] Starting Wazuh stack...${RESET}"
echo "This may take 2-5 minutes for first-time setup..."

docker-compose up -d

echo ""
echo "Waiting for services to start..."
sleep 30

# Check service status
echo ""
echo -e "${CYAN}Checking service status...${RESET}"
docker-compose ps

echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${GREEN}${BOLD}║              Installation Complete!                          ║${RESET}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════════════════╝${RESET}"
echo ""
echo -e "${CYAN}Wazuh Services:${RESET}"
echo -e "  ${GREEN}Manager:${RESET}    http://localhost:55000 (API)"
echo -e "  ${GREEN}Dashboard:${RESET}  http://localhost:5601"
echo -e "  ${GREEN}Indexer:${RESET}   http://localhost:9200"
echo ""
echo -e "${CYAN}Default Credentials:${RESET}"
echo -e "  ${GREEN}API Username:${RESET}  wazuh-api"
echo -e "  ${GREEN}API Password:${RESET}  DeceptiCloudWazuh2026"
echo -e "  ${GREEN}Dashboard:${RESET}     admin / SecretPassword"
echo ""
echo -e "${CYAN}Agents Deployed:${RESET}"
echo -e "  ${GREEN}✓${RESET} decepticloud-proxy"
echo -e "  ${GREEN}✓${RESET} banking-honeypot"
echo -e "  ${GREEN}✓${RESET} ecommerce-honeypot"
echo -e "  ${GREEN}✓${RESET} healthcare-honeypot"
echo -e "  ${GREEN}✓${RESET} blog-honeypot"
echo -e "  ${GREEN}✓${RESET} api-service-honeypot"
echo -e "  ${GREEN}✓${RESET} corporate-honeypot"
echo -e "  ${GREEN}✓${RESET} admin-panel-honeypot"
echo ""
echo -e "${CYAN}Useful Commands:${RESET}"
echo -e "  ${GREEN}View logs:${RESET}        docker-compose logs -f"
echo -e "  ${GREEN}Stop services:${RESET}    docker-compose down"
echo -e "  ${GREEN}Restart:${RESET}          docker-compose restart"
echo -e "  ${GREEN}Check status:${RESET}     docker-compose ps"
echo ""
echo -e "${CYAN}Next Steps:${RESET}"
echo -e "  1. Access Wazuh Dashboard at http://localhost:5601"
echo -e "  2. Start log ingestion: python3 ../wazuh/log_ingestion_service.py"
echo -e "  3. Check agent status in Wazuh Dashboard"
echo ""
