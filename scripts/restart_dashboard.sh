#!/bin/bash
# Restart Dashboard to pick up new data

echo "Stopping dashboard..."
pkill -f "dashboard/app.py"
sleep 2

echo "Starting dashboard..."
nohup python3 dashboard/app.py > logs/dashboard.log 2>&1 &

sleep 3

echo "Checking dashboard status..."
if lsof -i:9000 > /dev/null 2>&1; then
    echo "✓ Dashboard is running on port 9000"
else
    echo "✗ Dashboard failed to start"
    exit 1
fi

echo ""
echo "Dashboard restarted successfully!"
echo "Access at: http://localhost:9000"
