#!/bin/bash

# Quick Status Check Script

# Checks the status of all running services


echo "SYSTEM STATUS CHECK"


# Check if processes are running

echo " Checking running processes..."


# ML API

if pgrep -f "model_api.py" > /dev/null; then
    ML_API_PID=$(pgrep -f "model_api.py")
    echo " ML API is running (PID: $ML_API_PID)"
    echo "   URL: http://localhost:5000"
    
    # Test health

    if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
        echo "   Health:  OK"
    else
        echo "   Health:   Not responding"
    fi
else
    echo " ML API is NOT running"
fi


# Honeypots

HONEYPOT_COUNT=$(pgrep -f "honeypot/app.py" | wc -l)
if [ $HONEYPOT_COUNT -gt 0 ]; then
    echo " Honeypots running: $HONEYPOT_COUNT/10"
    
    # Check each port

    for port in {8080..8089}; do
        if nc -z localhost $port 2>/dev/null; then
            echo "    Port $port: Active"
        else
            echo "    Port $port: Inactive"
        fi
    done
else
    echo " No honeypots are running"
fi


echo " Log Files:"

ls -lht logs/ | head -10


echo " Latest Deployment Log:"

LATEST_LOG=$(ls -t logs/deployment_*.log 2>/dev/null | head -1)
if [ -f "$LATEST_LOG" ]; then
    echo "File: $LATEST_LOG"

    tail -30 "$LATEST_LOG"
else
    echo "No deployment log found"
fi


echo " Quick Commands:"

echo "# View ML API log:"
echo "tail -f logs/ml_api.log"

echo "# View deployment log:"
echo "tail -f $LATEST_LOG"

echo "# Test ML API:"
echo "curl http://localhost:5000/api/health"

echo "# Test honeypot:"
echo "curl http://localhost:8080"

