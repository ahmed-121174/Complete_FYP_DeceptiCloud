#!/bin/bash
# Quick start all DeceptiCloud services

echo "🚀 Starting DeceptiCloud..."

# Kill existing
pkill -f "launch_decepticloud.py" 2>/dev/null
pkill -f "model_api.py" 2>/dev/null
sleep 2

# Start main system
nohup python3 launch_decepticloud.py > logs/system.log 2>&1 &
echo "  ⏳ Starting websites and services..."
sleep 15

# Start ML API with venv
nohup venv/bin/python3 ml_pipeline/model_api.py > logs/ml_api.log 2>&1 &
echo "  ⏳ Starting ML API..."
sleep 15

# Verify
echo ""
echo "✅ Services started!"
echo ""
python3 scripts/fix_overview_live_data.py
