#!/bin/bash

# DeceptiCloud Unified Control Script v2.1
# Manages: Wazuh, DeceptiCloud Core (14 Sites, ML, Proxy), Dashboard, and Agents

# Auto-detect project root from script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WAZUH_DIR="$PROJECT_ROOT/wazuh-docker/single-node"
LOG_DIR="$PROJECT_ROOT/logs"
PID_DIR="$PROJECT_ROOT/pids"

mkdir -p "$LOG_DIR" "$PID_DIR"

# Configuration
NETWORK="single-node_wazuh-net"

# Use docker compose v2 (native command)
DOCKER_COMPOSE="docker compose"

# Agent Keys
declare -A AGENT_KEYS
AGENT_KEYS[001]="MDAxIGRjLXJlYWwtYmFua2luZyBhbnkgMDIwY2M1MzVjOTVmZjA5MWFiZjg0MTA3Y2U3NDhmYjc5Y2IxYmQ1ZWYzODZkNjU0OTFhMTliNTVhNmY0ZGI2Mw=="
AGENT_KEYS[002]="MDAyIGRjLWhwLWJhbmtpbmcgYW55IDRlOGFiMmMxOGI1MGQ0YWM5NDEzNTVkNWNiOTI0Nzk2YWNhMTdmMjVlYjljMDM0OTFhODgyOTM1NmQ1MDUyZjg="
AGENT_KEYS[003]="MDAzIGRjLXJlYWwtZWNvbW1lcmNlIGFueSAxODA1NjlmZWQ3OWE3NGE4YjIyYjQ4MzhlYzE3MzRmNWNlMDY3MGYwMDA3MjAwMWZhNmJiY2JmN2M2ZTVmM2U0"
AGENT_KEYS[004]="MDA0IGRjLWhwLWVjb21tZXJjZSBhbnkgYjJhZjRjNjc3NmQ4ZDM3N2I2MjcyMzEzOGVkYmVlZGJkMjgyZDcyODU1MTRmNzA1NDJmODMyYTRiOTQ1NGU3Yg=="
AGENT_KEYS[005]="MDA1IGRjLXJlYWwtaGVhbHRoY2FyZSBhbnkgMWRiNmJmYjE2OGMxOGQ1MjJjOTE0MjU2YTIxYjgxNzg3NjY1OWZmMWVhZDEwYWVhMjFjM2ViMzg5NDg5NDI3YQ=="
AGENT_KEYS[006]="MDA2IGRjLWhwLWhlYWx0aGNhcmUgYW55IGM4ZmUzYjZiZDQ3MDI0ODU0YjAyOTc3NzgxMjZmOWI2Y2U1M2ExNWNkNWRmZDRiOTk5NDIwY2Q4MzM4ZTZiYzA="
AGENT_KEYS[007]="MDA3IGRjLXJlYWwtYmxvZyBhbnkgNDkzNWIyZGM4ZmE5ZDg4YmNhYmFkN2RhNzljY2M2MzVjNTA0ZmYwMGZmNzRjOWM0MmQ5YmFmYjExMjc4YWRlNQ=="
AGENT_KEYS[008]="MDA4IGRjLWhwLWJsb2cgYW55IGE1MzFiYmE4NzVkZjc0ZTViZGRhODE3NzRmN2NjZjdjNGY5N2MwYzA1NTMwMzY3ODI1MzRmM2Q0MTViMDQwY2U="
AGENT_KEYS[009]="MDA5IGRjLXJlYWwtYXBpX3NlcnZpY2UgYW55IDUwN2ZhYjVlNGQzZDdhYTM3NDkwZmY4MDQyNjA5ZTJkOWFhODU3MmI1MjQyOGUzNzViNGY5YzcxYmU5Nzk4YWU="
AGENT_KEYS[010]="MDEwIGRjLWhwLWFwaV9zZXJ2aWNlIGFueSAxNzc0YWUzZGMwNzNhZjhlNzhiN2U5MWYzOWM4NWFkNGJmZDY0NWI0NGZjNGI1YjQ1MjQ4M2M4NzM2MTc5YjZm"
AGENT_KEYS[011]="MDExIGRjLXJlYWwtY29ycG9yYXRlIGFueSA1ZDI1MTRkNTE5NDQ0N2VjZGYyMjkyOTI5MmU5ZGYyZjllYjg4MWJkNTZjNzg0ZTBiYWM0MjgzMjgyNmZlYjVk"
AGENT_KEYS[012]="MDEyIGRjLWhwLWNvcnBvcmF0ZSBhbnkgNGUyOGJhNTM0ZWE0NGJiZTRlMjA5NGUzOWVjNGJjMDIzNjNiNWM5MWE3NGI2Mzc4ZTExMDRhYjdkYzQ0MWI3Mw=="
AGENT_KEYS[013]="MDEzIGRjLXJlYWwtYWRtaW5fcGFuZWwgYW55IDcwNTUwZjM5NTZjMDU3MDYxYzI2YmY5YWNjNjZiMzMwYmNiNjRjZDQzNzU5ZTZkOTIyY2IyNzQxNTBmNTUxNjU="
AGENT_KEYS[014]="MDE0IGRjLWhwLWFkbWluX3BhbmVsIGFueSAwYjQxZDRmODRhNDViZjY3MmY5YzVhZTQzOWY0NzE5ZGEwNTQ2OWI2NjJmMDJiOTZlZjk0NmE3NzNjOWViNWIy"

function start_all() {
    echo "--- Starting DeceptiCloud Full Ecosystem ---"

    # 1. Start Wazuh Stack
    echo "[1/3] Starting Wazuh Docker Stack..."
    cd "$WAZUH_DIR" && $DOCKER_COMPOSE up -d
    
    # Wait for manager to get an IP
    echo "Waiting for Wazuh Manager IP..."
    sleep 10
    MANAGER_IP=$(docker inspect single-node-wazuh.manager --format '{{ range .NetworkSettings.Networks }}{{ .IPAddress }}{{ end }}')
    echo "Detected Manager IP: $MANAGER_IP"

    if [ -z "$MANAGER_IP" ]; then
        echo "Error: Could not detect Wazuh Manager IP. Make sure the container is running."
        exit 1
    fi

    # 2. Start 14 Agents
    echo "[2/3] Starting 14 Wazuh Agent Containers..."
    for id in "${!AGENT_KEYS[@]}"; do
        if [ ! "$(docker ps -q -f name=dc-agent-$id)" ]; then
            if [ "$(docker ps -aq -f name=dc-agent-$id)" ]; then
                docker start "dc-agent-$id"
            else
                docker run -d --name "dc-agent-$id" \
                    --network "$NETWORK" \
                    -e WAZUH_MANAGER="$MANAGER_IP" \
                    --memory 64m \
                    wazuh/wazuh-agent:4.14.4
                
                # Setup agent key
                decoded_key=$(echo "${AGENT_KEYS[$id]}" | base64 -d)
                docker exec "dc-agent-$id" bash -c "echo '$decoded_key' > /var/ossec/etc/client.keys"
                docker exec "dc-agent-$id" sed -i "s|<address></address>|<address>$MANAGER_IP</address>|" /var/ossec/etc/ossec.conf
                docker exec "dc-agent-$id" /var/ossec/bin/wazuh-control restart
            fi
        fi
    done

    # Update all agents with current manager IP and restart
    echo "Updating agent configurations with Manager IP: $MANAGER_IP"
    for id in "${!AGENT_KEYS[@]}"; do
        docker exec "dc-agent-$id" sed -i "s|<address>.*</address>|<address>$MANAGER_IP</address>|" /var/ossec/etc/ossec.conf 2>/dev/null
        docker exec "dc-agent-$id" /var/ossec/bin/wazuh-control restart > /dev/null 2>&1 &
    done
    wait
    echo "All agents connected to manager."

    # 3. Start DeceptiCloud v2 (Sites, ML, Proxy, Dashboard, ALE)
    echo "[3/3] Launching DeceptiCloud Services (v2 Launcher)..."
    cd "$PROJECT_ROOT"
    
    # Use venv Python if available
    venv_python="$PROJECT_ROOT/venv/bin/python3"
    python_exec="python3"
    [ -f "$venv_python" ] && python_exec="$venv_python"

    # Ensure geoip2 is installed in the venv (required for geographic fingerprint data)
    if ! "$python_exec" -c "import geoip2" 2>/dev/null; then
        echo "Installing geoip2 for geographic fingerprint lookups..."
        "$python_exec" -m pip install geoip2 --quiet
    fi

    nohup "$python_exec" launch_decepticloud_v2.py > "$LOG_DIR/launch_v2.log" 2>&1 &
    echo $! > "$PID_DIR/launch_v2.pid"

    echo "Waiting for services to initialize..."
    sleep 15
    echo "✓ All services should be running."
}

function stop_all() {
    echo "--- Stopping DeceptiCloud Full Ecosystem ---"

    # Stop Launcher v2 and its children
    if [ -f "$PID_DIR/launch_v2.pid" ]; then
        PID=$(cat "$PID_DIR/launch_v2.pid")
        echo "Stopping DeceptiCloud Core (PID $PID)..."
        kill -SIGINT $PID 2>/dev/null
        sleep 5
        kill -9 $PID 2>/dev/null
        rm "$PID_DIR/launch_v2.pid"
    fi

    # Cleanup any lingering Python processes
    echo "Cleaning up lingering Python processes..."
    pkill -f "launch_decepticloud_v2.py"
    pkill -f "dashboard/app.py"
    pkill -f "adaptive_engine/engine.py"
    pkill -f "wazuh/log_ingestion_service.py"
    pkill -f "ml_pipeline/model_api.py"
    pkill -f "proxy/routing_proxy.py"
    pkill -f "shared/site_factory.py"

    # Stop Agents
    echo "Stopping 14 Agent containers..."
    docker stop $(docker ps -q -f name=dc-agent-)

    # Stop Wazuh Stack
    echo "Stopping Wazuh Docker stack..."
    cd "$WAZUH_DIR" && $DOCKER_COMPOSE stop

    echo "✓ All services stopped."
}

function status() {
    echo "--- System Status ---"
    echo "Docker Containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "dc-agent|wazuh"
    echo ""
    echo "Core Services (Ports):"
    for port in 9000 5000 8080 3001 4001; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
            echo "Port $port: [UP]"
        else
            echo "Port $port: [DOWN]"
        fi
    done
}

case "$1" in
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    restart)
        stop_all
        sleep 5
        start_all
        ;;
    status)
        status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
esac
