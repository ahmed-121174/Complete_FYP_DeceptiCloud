# SSH Honeypot - Impact Analysis

## What the SSH Honeypot Does

The SSH honeypot is a **standalone service** that:
- Listens on port **2222** (non-standard SSH port)
- Logs all SSH connection attempts to the database
- Does NOT interfere with any existing services
- Does NOT affect the web honeypots (ports 4001-4007)
- Does NOT affect the dashboard, proxy, or ML API

## Database Impact

The SSH honeypot ONLY writes to the `honeypot_events` table:
- Event types: `ssh_connection`, `ssh_banner`, `ssh_auth_attempt`, `ssh_disconnect`
- No modifications to existing data
- No impact on attacks, sessions, or routing_rules tables

## Service Independence

✓ **Completely isolated** - Runs in its own process
✓ **No dependencies** - Does not require other services
✓ **Safe to stop** - Can be terminated without affecting anything else
✓ **Port 2222** - Does not conflict with any existing services

## How to Control It

**Start:** `venv/bin/python3 honeypot/ssh_honeypot.py`
**Stop:** Press Ctrl+C or kill the process
**Check Status:** `lsof -i :2222`

## Jury Presentation Value

- Demonstrates **multi-protocol honeypot** capability
- Shows **SSH brute-force detection**
- Logs attacker reconnaissance attempts
- Adds to the "16 services" count (becomes 18 total)

## Risk Assessment: ZERO

- No impact on existing pages
- No data corruption risk
- Easy to start/stop
- Completely optional feature
