#!/usr/bin/env bash
# DeceptiCloud — STOP wrapper for FYP-II_Finals

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR"
echo "[DeceptiCloud] Stopping all services..."
bash start_stop/decepticloud_control.sh stop
echo "[DeceptiCloud] ✅ All services stopped."
