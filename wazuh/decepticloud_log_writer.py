#!/usr/bin/env python3
"""
DeceptiCloud → Wazuh Log Writer
Tails the attacks table and writes new events to a log file that Wazuh monitors.
This gives Wazuh real-time visibility into DeceptiCloud-detected attacks.

Run this alongside the main system:
    nohup venv/bin/python3 wazuh/decepticloud_log_writer.py > logs/wazuh_writer.log 2>&1 &
"""

import sys
import json
import time
import os
import subprocess
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_service import get_db_service

# Where Wazuh agent picks up logs — inside the container this maps to /var/ossec/logs/
# We write to a local path that's volume-mounted into the Wazuh container
WAZUH_LOG_FILE = Path(__file__).parent.parent / 'logs' / 'decepticloud_wazuh.log'

# How often to poll for new attacks
POLL_INTERVAL = 5  # seconds

# Track last seen attack ID so we don't re-emit already-written events
STATE_FILE = Path(__file__).parent.parent / 'logs' / 'wazuh_writer_state.json'


def load_state() -> dict:
    """Load persisted state (last emitted attack ID)."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {'last_id': 0}


def save_state(state: dict):
    """Persist state so we survive restarts."""
    STATE_FILE.write_text(json.dumps(state))


def map_attack_to_rule_level(attack_type: str, confidence: float) -> int:
    """Map DeceptiCloud attack type + confidence → Wazuh rule level (0-15)."""
    base_levels = {
        'SQLi':    12,
        'NoSQLi':  11,
        'XSS':     10,
        'DDoS':    13,
        'BruteForce': 11,
        'Scanner': 8,
        'Anomaly': 7,
    }
    level = base_levels.get(attack_type, 9)
    # High confidence bumps level
    if confidence >= 0.95:
        level = min(level + 1, 15)
    elif confidence < 0.88:
        level = max(level - 1, 5)
    return level


def format_wazuh_log_line(attack: dict) -> str:
    """
    Format a DeceptiCloud attack record as a Wazuh-compatible syslog JSON line.
    Wazuh's localfile reader will pick this up and our custom decoder will parse it.
    """
    attack_type = attack.get('attack_type', 'Unknown')
    confidence = float(attack.get('confidence') or 0.0)
    rule_level = map_attack_to_rule_level(attack_type, confidence)

    timestamp = attack.get('timestamp', datetime.now().isoformat())
    ip = attack.get('ip', 'unknown')
    path = attack.get('path', '/')
    method = attack.get('method', 'GET')
    detection_method = attack.get('detection_method', 'ml')
    target_site = attack.get('target_site', 'unknown')
    honeypot_port = attack.get('honeypot_port', 0)

    payload = {
        'timestamp': timestamp,
        'program': 'decepticloud',
        'event': 'attack_detected',
        'rule_level': rule_level,
        'attack_type': attack_type,
        'confidence': round(confidence, 4),
        'src_ip': ip,
        'method': method,
        'path': path,
        'detection_method': detection_method,
        'target_site': target_site,
        'honeypot_port': honeypot_port,
        'captured': True,
        'description': f'DeceptiCloud detected {attack_type} attack from {ip} on {target_site} (confidence: {confidence*100:.1f}%)',
    }
    return json.dumps(payload)


def inject_into_wazuh_container(log_line: str):
    """
    Inject a log line directly into the Wazuh manager container using docker exec.
    This simulates what a Wazuh agent would send.
    Uses the Wazuh manager's event injection endpoint via ossec-logtest or direct log append.
    """
    try:
        # Write to a file inside the container that Wazuh monitors
        cmd = [
            'docker', 'exec', 'single-node-wazuh.manager',
            'bash', '-c',
            f'echo \'{log_line}\' >> /var/ossec/logs/decepticloud.log'
        ]
        subprocess.run(cmd, capture_output=True, timeout=5)
    except Exception as e:
        # Non-fatal — local log file is always written
        pass


def ensure_wazuh_log_configured():
    """
    Add decepticloud.log to Wazuh manager's monitored files if not already configured.
    Uses docker exec to check and update ossec.conf inside the container.
    """
    check_cmd = [
        'docker', 'exec', 'single-node-wazuh.manager',
        'bash', '-c',
        'grep -q "decepticloud.log" /var/ossec/etc/ossec.conf && echo "found" || echo "not_found"'
    ]
    try:
        result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=10)
        if 'not_found' in result.stdout:
            # Add localfile config for decepticloud log
            add_cmd = [
                'docker', 'exec', 'single-node-wazuh.manager',
                'bash', '-c',
                r"""
                sed -i 's|</ossec_config>|  <localfile>\n    <log_format>syslog</log_format>\n    <location>/var/ossec/logs/decepticloud.log</location>\n  </localfile>\n</ossec_config>|' /var/ossec/etc/ossec.conf
                """
            ]
            subprocess.run(add_cmd, capture_output=True, timeout=10)
            # Restart wazuh-analysisd to pick up new config
            subprocess.run(
                ['docker', 'exec', 'single-node-wazuh.manager', 'bash', '-c',
                 '/var/ossec/bin/wazuh-control restart'],
                capture_output=True, timeout=30
            )
            print("Configured Wazuh to monitor decepticloud.log")
        else:
            print("Wazuh already configured to monitor decepticloud.log")
    except Exception as e:
        print(f"Could not configure Wazuh log monitoring: {e}")


def main():
    print("=" * 60)
    print("DeceptiCloud → Wazuh Log Writer")
    print("=" * 60)

    # Ensure log directory exists
    WAZUH_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Configure Wazuh to monitor our log file
    ensure_wazuh_log_configured()

    db = get_db_service()
    state = load_state()
    print(f"Resuming from attack ID: {state['last_id']}")
    print(f"Writing logs to: {WAZUH_LOG_FILE}")
    print(f"Poll interval: {POLL_INTERVAL}s\n")

    emitted_total = 0

    while True:
        try:
            with db.get_connection() as conn:
                rows = conn.execute(
                    "SELECT * FROM attacks WHERE id > ? AND captured = 1 ORDER BY id ASC LIMIT 100",
                    (state['last_id'],)
                ).fetchall()

            if rows:
                with open(WAZUH_LOG_FILE, 'a') as f:
                    for row in rows:
                        attack = dict(row)
                        log_line = format_wazuh_log_line(attack)
                        f.write(log_line + '\n')
                        inject_into_wazuh_container(log_line)
                        state['last_id'] = attack['id']
                        emitted_total += 1

                save_state(state)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Emitted {len(rows)} events "
                      f"(total: {emitted_total}, last_id: {state['last_id']})")

        except KeyboardInterrupt:
            print(f"\nStopped. Total events emitted: {emitted_total}")
            break
        except Exception as e:
            print(f"Error: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    main()
