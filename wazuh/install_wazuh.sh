#!/bin/bash
# DeceptiCloud - Wazuh Manager Installation Script
# Installs Wazuh Manager 4.x on Ubuntu/Debian systems

set -e

echo "=========================================="
echo "DeceptiCloud - Wazuh Manager Installation"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Install dependencies
echo "[1/6] Installing dependencies..."
apt-get update
apt-get install -y curl apt-transport-https lsb-release gnupg

# Add Wazuh repository
echo "[2/6] Adding Wazuh repository..."
curl -s https://packages.wazuh.com/key/GPG-KEY-WAZUH | gpg --no-default-keyring --keyring gnupg-ring:/usr/share/keyrings/wazuh.gpg --import && chmod 644 /usr/share/keyrings/wazuh.gpg
echo "deb [signed-by=/usr/share/keyrings/wazuh.gpg] https://packages.wazuh.com/4.x/apt/ stable main" | tee -a /etc/apt/sources.list.d/wazuh.list
apt-get update

# Install Wazuh Manager
echo "[3/6] Installing Wazuh Manager..."
apt-get install -y wazuh-manager

# Start Wazuh Manager
echo "[4/6] Starting Wazuh Manager..."
systemctl daemon-reload
systemctl enable wazuh-manager
systemctl start wazuh-manager

# Install Wazuh API (Filebeat + Elasticsearch optional for full setup)
echo "[5/6] Installing Wazuh API..."
apt-get install -y wazuh-api

# Configure Wazuh API
echo "[6/6] Configuring Wazuh API..."
systemctl enable wazuh-api
systemctl start wazuh-api

# Check status
echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Wazuh Manager Status:"
systemctl status wazuh-manager --no-pager | head -n 5
echo ""
echo "Wazuh API Status:"
systemctl status wazuh-api --no-pager | head -n 5
echo ""
echo "Wazuh Manager: Running on port 1514 (agent communication)"
echo "Wazuh API: Running on port 55000"
echo ""
echo "Next steps:"
echo "1. Configure custom rules: /var/ossec/etc/rules/local_rules.xml"
echo "2. Configure custom decoders: /var/ossec/etc/decoders/local_decoder.xml"
echo "3. Deploy agents using: wazuh/deploy_agents.sh"
echo "4. Start log ingestion service: python3 wazuh/log_ingestion_service.py"
echo ""
