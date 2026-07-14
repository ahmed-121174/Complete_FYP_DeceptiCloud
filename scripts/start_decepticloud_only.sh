#!/bin/bash
# Quick start for DeceptiCloud services only (no Wazuh)

echo "🚀 Starting DeceptiCloud Services..."
echo ""

# Kill existing processes
pkill -f "python.*ml_api/app.py" 2>/dev/null
pkill -f "python.*proxy/routing_proxy.py" 2>/dev/null
pkill -f "python.*honeypot.*app.py" 2>/dev/null
sleep 2

# Create logs directory
mkdir -p logs

# Start ML API
echo "Starting ML API (port 5000)..."
nohup python3 ml_api/app.py > logs/ml_api.log 2>&1 &
sleep 2

# Start Routing Proxy
echo "Starting Routing Proxy (port 8080)..."
nohup python3 proxy/routing_proxy.py > logs/routing_proxy.log 2>&1 &
sleep 2

# Start Real Sites (ports 3001-3007)
echo "Starting Real Sites (ports 3001-3007)..."
for site in banking ecommerce healthcare blog api_service corporate admin_panel; do
    port=$((3001 + $(echo "banking ecommerce healthcare blog api_service corporate admin_panel" | tr ' ' '\n' | grep -n "^$site$" | cut -d: -f1) - 1))
    nohup python3 websites/${site}/app.py > logs/${site}_real.log 2>&1 &
done
sleep 2

# Start Honeypot Sites (ports 4001-4007)
echo "Starting Honeypot Sites (ports 4001-4007)..."
for site in banking ecommerce healthcare blog api_service corporate admin_panel; do
    port=$((4001 + $(echo "banking ecommerce healthcare blog api_service corporate admin_panel" | tr ' ' '\n' | grep -n "^$site$" | cut -d: -f1) - 1))
    nohup python3 honeypot/${site}/app.py > logs/${site}_honeypot.log 2>&1 &
done
sleep 3

# Check status
echo ""
echo "✅ Services started!"
echo ""
echo "Checking ports..."
for port in 5000 8080 9000 3001 3002 3003 3004 3005 3006 3007 4001 4002 4003 4004 4005 4006 4007; do
    if lsof -i:$port > /dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":$port"; then
        echo "  ✓ Port $port: UP"
    else
        echo "  ✗ Port $port: DOWN"
    fi
done

echo ""
echo "🌐 Dashboard: http://localhost:9000"
echo ""
