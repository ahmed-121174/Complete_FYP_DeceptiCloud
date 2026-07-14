#!/usr/bin/env bash
# DeceptiCloud — STOP ALL SERVICES  (bulletproof version)

echo -e "\n\033[1;31m  Stopping all DeceptiCloud services...\033[0m"

# 0. Clear any iptables rules left by DDoS demo (port 3006 block)

iptables -D INPUT -p tcp --dport 3006 -j REJECT 2>/dev/null || true
iptables -D OUTPUT -p tcp --sport 3006 -j REJECT 2>/dev/null || true
# Kill any lingering DDoS-related watchdog/attack processes

pkill -9 -f "ddos_attack\|k8s_watch\|VICTIM_PORT"  2>/dev/null || true

# 1. Kill by process name first (catches launch script + children)

pkill -9 -f "launch_decepticloud.py"  2>/dev/null || true
pkill -9 -f "routing_proxy.py"        2>/dev/null || true
pkill -9 -f "dashboard/app.py"        2>/dev/null || true
pkill -9 -f "model_api.py"            2>/dev/null || true
pkill -9 -f "websites/banking"        2>/dev/null || true
pkill -9 -f "websites/ecommerce"      2>/dev/null || true
pkill -9 -f "websites/healthcare"     2>/dev/null || true
pkill -9 -f "websites/blog"           2>/dev/null || true
pkill -9 -f "websites/api_service"    2>/dev/null || true
pkill -9 -f "websites/corporate"      2>/dev/null || true
pkill -9 -f "websites/admin_panel"    2>/dev/null || true

# 2. Kill by PID files

for pidfile in /tmp/dc_launch.pid /tmp/dc_k8s_watchdog.pid /tmp/dc_site_*.pid; do
    [ -f "$pidfile" ] && kill -9 "$(cat "$pidfile")" 2>/dev/null || true
done

# 3. Force-release all ports (catches anything missed above)

for port in 5000 8080 9000 3001 3002 3003 3004 3005 3006 3007 4001 4002 4003 4004 4005 4006 4007; do
    fuser -k "${port}/tcp" 2>/dev/null || true
done

# 4. Wait for OS to release ports

sleep 3

# 5. Confirm ports are free

echo -e "\n  Port status:"
ALL_FREE=true
for port in 5000 8080 9000; do
    if ss -tlnp 2>/dev/null | grep -q ":${port} "; then
        echo -e "  \033[1;31m\033[0m  Port $port still in use — trying again..."
        fuser -k "${port}/tcp" 2>/dev/null || true
        ALL_FREE=false
    else
        echo -e "  \033[0;32m\033[0m  Port $port free"
    fi
done

# Cleanup temp files

rm -f /tmp/dc_launch.pid /tmp/dc_k8s_watchdog.pid /tmp/dc_ddos_cnt* /tmp/dc_site_*.pid

[ "$ALL_FREE" = true ] && \
    echo -e "\n  \033[0;32m All services stopped cleanly.\033[0m\n" || \
    echo -e "\n  \033[1;33m Some ports may still need a moment. Wait 5s and try again.\033[0m\n"
