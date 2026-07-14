#!/bin/bash
# Start Adaptive Engine and Wazuh Log Ingestion

cd "$(dirname "$0")/.."

echo "Starting Adaptive Engine..."
nohup python3 adaptive_engine/engine.py > logs/adaptive_engine.log 2>&1 &
echo $! > logs/adaptive_engine.pid

echo "Starting Wazuh Log Ingestion Service..."
nohup python3 wazuh/log_ingestion_service.py > logs/log_ingestion.log 2>&1 &
echo $! > logs/log_ingestion.pid

echo "Services started successfully."
