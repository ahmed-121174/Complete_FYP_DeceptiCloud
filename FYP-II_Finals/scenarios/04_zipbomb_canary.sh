#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# DeceptiCloud — ZIP BOMB Canary Demo
# Run from Laptop B (attacker machine):
#   bash 04_zipbomb_canary.sh <DECEPTICLOUD_IP>
# ═══════════════════════════════════════════════════════════════════════════════

TARGET="${1:-localhost}"
PROXY="http://${TARGET}:8080"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; MAGENTA='\033[0;35m'; BOLD='\033[1m'; RESET='\033[0m'

clear
echo -e "${CYAN}${BOLD}"
echo "  ╔══════════════════════════════════════════════════════════════╗"
echo "  ║           DeceptiCloud — ZIP BOMB Canary Demo                ║"
echo "  ║     2.9 KB File → 10 TB Decompression Trap                  ║"
echo "  ╚══════════════════════════════════════════════════════════════╝"
echo -e "${RESET}"

echo -e "${YELLOW}[*] Target: ${PROXY}${RESET}"
echo -e "${YELLOW}[*] Phase 1: Reconnaissance — checking robots.txt for juicy paths...${RESET}\n"
sleep 1

# Step 1: Attacker reads robots.txt (triggers first canary)
echo -e "${CYAN}[ATTACKER]${RESET} curl ${PROXY}/robots.txt"
ROBOTS=$(curl -s "${PROXY}/robots.txt" 2>/dev/null)
echo "$ROBOTS" | head -10
echo ""
sleep 2

echo -e "${YELLOW}[*] Phase 2: Found /backup/ in robots.txt — enumerating backup files...${RESET}\n"
sleep 1

# Step 2: Attacker probes backup paths (triggers more canaries)
for path in /backup.sql /db.zip /.env /config.json; do
    echo -e "${CYAN}[ATTACKER]${RESET} Probing ${PROXY}${path}"
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${PROXY}${path}")
    echo -e "  → HTTP ${STATUS}"
    sleep 0.5
done
echo ""
sleep 1

# Step 3: Attacker finds and downloads the zip bomb
echo -e "${RED}${BOLD}[ATTACKER] Found: /backup/database_full_2026.zip — DOWNLOADING...${RESET}"
echo -e "${YELLOW}[*] Attacker thinks this is the full database backup!${RESET}\n"
sleep 1

echo -e "${CYAN}[ATTACKER]${RESET} wget -q ${PROXY}/backup/database_full_2026.zip -O stolen_db.zip"
curl -s -o /tmp/stolen_db.zip "${PROXY}/backup/database_full_2026.zip" 2>&1
DOWNLOADED_SIZE=$(stat -c%s /tmp/stolen_db.zip 2>/dev/null || echo 0)
echo -e "${GREEN}[ATTACKER]${RESET} Download complete! File size: ${DOWNLOADED_SIZE} bytes"
echo ""
sleep 1

# Step 4: Attacker checks what's inside
echo -e "${CYAN}[ATTACKER]${RESET} unzip -l stolen_db.zip  (checking contents)"
sleep 1
if command -v unzip &>/dev/null && [ -f /tmp/stolen_db.zip ]; then
    unzip -l /tmp/stolen_db.zip 2>/dev/null || echo "  (Zip structure visible to attacker's tool)"
fi
echo ""
sleep 1

# The reveal
echo -e "${RED}${BOLD}╔══════════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${RED}${BOLD}║  ⚠ ZIP BOMB DEPLOYED — CANARY TOKEN TRIGGERED                   ║${RESET}"
echo -e "${RED}${BOLD}╚══════════════════════════════════════════════════════════════════╝${RESET}"
echo ""
echo -e "${GREEN}[DECEPTICLOUD]${RESET} Attacker IP logged: ${TARGET} (Laptop B)"
echo -e "${GREEN}[DECEPTICLOUD]${RESET} File delivered:     database_full_2026.zip"
echo -e "${GREEN}[DECEPTICLOUD]${RESET} Actual file size:   ~3 KB"
echo -e "${GREEN}[DECEPTICLOUD]${RESET} Advertised size:    10 TB (10 files × 1 TB each)"
echo -e "${GREEN}[DECEPTICLOUD]${RESET} If extracted:       Would consume 10 TB of attacker disk!"
echo ""
echo -e "${MAGENTA}${BOLD}[NOW CHECK DASHBOARD]${RESET}"
echo -e " → Canary Tokens tab:  Shows 'zip_bomb_download' triggered"
echo -e " → Dashboard counter:  Canary trigger count incremented"
echo -e " → Attacker profiled:  IP recorded with CRITICAL severity"
echo -e " → Dashboard:          http://${TARGET}:9000"
echo ""

# Cleanup
rm -f /tmp/stolen_db.zip
