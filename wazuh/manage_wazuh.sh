#!/bin/bash
# DeceptiCloud - Wazuh Management Script
# Manage Wazuh Docker stack

set -e

CYAN='\033[96m'
GREEN='\033[92m'
YELLOW='\033[93m'
RED='\033[91m'
BOLD='\033[1m'
RESET='\033[0m'

cd "$(dirname "$0")"

show_usage() {
    echo -e "${CYAN}${BOLD}DeceptiCloud - Wazuh Management${RESET}"
    echo ""
    echo "Usage: $0 {start|stop|restart|status|logs|agents|backup|restore}"
    echo ""
    echo "Commands:"
    echo "  start    - Start Wazuh stack"
    echo "  stop     - Stop Wazuh stack"
    echo "  restart  - Restart Wazuh stack"
    echo "  status   - Show service status"
    echo "  logs     - Show logs (use -f to follow)"
    echo "  agents   - List connected agents"
    echo "  backup   - Backup Wazuh configuration"
    echo "  restore  - Restore Wazuh configuration"
    echo ""
}

start_wazuh() {
    echo -e "${CYAN}Starting Wazuh stack...${RESET}"
    docker-compose up -d
    echo -e "${GREEN}✓ Wazuh started${RESET}"
    echo ""
    docker-compose ps
}

stop_wazuh() {
    echo -e "${CYAN}Stopping Wazuh stack...${RESET}"
    docker-compose down
    echo -e "${GREEN}✓ Wazuh stopped${RESET}"
}

restart_wazuh() {
    echo -e "${CYAN}Restarting Wazuh stack...${RESET}"
    docker-compose restart
    echo -e "${GREEN}✓ Wazuh restarted${RESET}"
    echo ""
    docker-compose ps
}

show_status() {
    echo -e "${CYAN}Wazuh Service Status:${RESET}"
    echo ""
    docker-compose ps
    echo ""
    echo -e "${CYAN}Container Health:${RESET}"
    docker ps --filter "name=wazuh" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

show_logs() {
    if [ "$2" == "-f" ]; then
        docker-compose logs -f
    else
        docker-compose logs --tail=100
    fi
}

list_agents() {
    echo -e "${CYAN}Wazuh Agents:${RESET}"
    echo ""
    docker exec wazuh-manager /var/ossec/bin/agent_control -l 2>/dev/null || echo "Manager not running or no agents connected"
}

backup_config() {
    BACKUP_DIR="backups/wazuh_backup_$(date +%Y%m%d_%H%M%S)"
    echo -e "${CYAN}Creating backup in $BACKUP_DIR...${RESET}"
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup configuration files
    cp -r wazuh-config "$BACKUP_DIR/"
    cp docker-compose.yml "$BACKUP_DIR/"
    
    # Backup Docker volumes
    docker run --rm \
        -v wazuh_wazuh-manager-etc:/data \
        -v "$(pwd)/$BACKUP_DIR:/backup" \
        alpine tar czf /backup/manager-etc.tar.gz -C /data .
    
    docker run --rm \
        -v wazuh_wazuh-manager-data:/data \
        -v "$(pwd)/$BACKUP_DIR:/backup" \
        alpine tar czf /backup/manager-data.tar.gz -C /data .
    
    echo -e "${GREEN}✓ Backup created: $BACKUP_DIR${RESET}"
}

restore_config() {
    if [ -z "$2" ]; then
        echo -e "${RED}Error: Please specify backup directory${RESET}"
        echo "Usage: $0 restore <backup_directory>"
        exit 1
    fi
    
    BACKUP_DIR="$2"
    
    if [ ! -d "$BACKUP_DIR" ]; then
        echo -e "${RED}Error: Backup directory not found: $BACKUP_DIR${RESET}"
        exit 1
    fi
    
    echo -e "${YELLOW}Warning: This will overwrite current configuration${RESET}"
    read -p "Continue? (y/N) " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled"
        exit 0
    fi
    
    echo -e "${CYAN}Restoring from $BACKUP_DIR...${RESET}"
    
    # Stop services
    docker-compose down
    
    # Restore configuration files
    cp -r "$BACKUP_DIR/wazuh-config/"* wazuh-config/
    cp "$BACKUP_DIR/docker-compose.yml" .
    
    # Restore Docker volumes
    if [ -f "$BACKUP_DIR/manager-etc.tar.gz" ]; then
        docker run --rm \
            -v wazuh_wazuh-manager-etc:/data \
            -v "$(pwd)/$BACKUP_DIR:/backup" \
            alpine sh -c "cd /data && tar xzf /backup/manager-etc.tar.gz"
    fi
    
    if [ -f "$BACKUP_DIR/manager-data.tar.gz" ]; then
        docker run --rm \
            -v wazuh_wazuh-manager-data:/data \
            -v "$(pwd)/$BACKUP_DIR:/backup" \
            alpine sh -c "cd /data && tar xzf /backup/manager-data.tar.gz"
    fi
    
    # Start services
    docker-compose up -d
    
    echo -e "${GREEN}✓ Configuration restored${RESET}"
}

# Main
case "$1" in
    start)
        start_wazuh
        ;;
    stop)
        stop_wazuh
        ;;
    restart)
        restart_wazuh
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "$@"
        ;;
    agents)
        list_agents
        ;;
    backup)
        backup_config
        ;;
    restore)
        restore_config "$@"
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
