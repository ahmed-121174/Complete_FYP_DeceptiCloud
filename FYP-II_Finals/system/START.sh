#!/usr/bin/env bash
# DeceptiCloud — START wrapper for FYP-II_Finals

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR"
echo "[DeceptiCloud] Starting all services..."
bash start_stop/decepticloud_control.sh start
echo ""
echo "[DeceptiCloud] ✅ Done. Run health check:"
echo "  bash FYP-II_Finals/system/HEALTH_CHECK.sh"
