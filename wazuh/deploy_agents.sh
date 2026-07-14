#!/bin/bash
# DeceptiCloud - Wazuh Agent Deployment Script
# Deploys and configures Wazuh agents for all 14 nodes

set -e

WAZUH_MANAGER="localhost"
AGENT_NAMES=(
    "honeypot-banking-01"
    "honeypot-ecommerce-01"
    "honeypot-healthcare-01"
    "honeypot-blog-01"
    "honeypot-api-01"
    "honeypot-corporate-01"
    "honeypot-admin-01"
    "real-banking-01"
    "real-ecommerce-01"
    "real-healthcare-01"
    "real-blog-01"
    "real-api-01"
    "real-corporate-01"
    "real-admin-01"
)

echo "=========================================="
echo "DeceptiCloud - Wazuh Agent Deployment"
echo "=========================================="
echo ""
echo "This script will register 14 Wazuh agents"
echo "Manager: $WAZUH_MANAGER"
echo ""

# Check if Wazuh Manager is running
if ! systemctl is-active --quiet wazuh-manager; then
    echo "Error: Wazuh Manager is not running"
    echo "Start it with: sudo systemctl start wazuh-manager"
    exit 1
fi

echo "Registering agents..."
echo ""

for AGENT_NAME in "${AGENT_NAMES[@]}"; do
    echo "Registering: $AGENT_NAME"
    
    # Register agent with Wazuh Manager
    /var/ossec/bin/agent-auth -m $WAZUH_MANAGER -A $AGENT_NAME
    
    echo "  ✓ $AGENT_NAME registered"
done

echo ""
echo "=========================================="
echo "Agent Registration Complete!"
echo "=========================================="
echo ""
echo "Registered agents:"
/var/ossec/bin/agent_control -l
echo ""
echo "Note: In a production environment, you would install"
echo "the Wazuh agent software on each actual node and"
echo "configure them to connect to this manager."
echo ""
echo "For this demo, agents are registered but running"
echo "on the same host as the manager."
echo ""
echo "Next steps:"
echo "1. Configure log forwarding on each agent"
echo "2. Start the log ingestion service:"
echo "   python3 wazuh/log_ingestion_service.py"
echo ""
