#!/usr/bin/env python3
"""
Sync DeceptiCloud Attacks to Wazuh Alerts
Creates corresponding Wazuh alerts for all attacks in the database
This ensures both systems show the same data
"""

import sys
import json
import requests
import urllib3
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_service import get_db_service

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Wazuh configuration
WAZUH_INDEXER_URL = 'https://localhost:9200'
WAZUH_INDEXER_USER = 'admin'
WAZUH_INDEXER_PASS = 'SecretPassword1!'

# Attack type to Wazuh rule ID mapping
ATTACK_TO_RULE = {
    'SQLi': 100001,
    'XSS': 100010,
    'NoSQLi': 100002,
    'Path Traversal': 100020,
    'Command Injection': 100030,
    'DDoS': 100040,
    'Brute Force': 100050,
    'Port Scan': 100060,
    'Credential Stuffing': 100070,
}

# Rule level mapping
CONFIDENCE_TO_LEVEL = {
    (0.95, 1.0): 12,   # Critical
    (0.85, 0.95): 10,  # High
    (0.70, 0.85): 7,   # Medium
    (0.50, 0.70): 5,   # Low
}

def get_rule_level(confidence: float) -> int:
    """Map confidence to Wazuh rule level"""
    for (min_conf, max_conf), level in CONFIDENCE_TO_LEVEL.items():
        if min_conf <= confidence < max_conf:
            return level
    return 5

def create_wazuh_alert(attack: dict) -> dict:
    """Convert DeceptiCloud attack to Wazuh alert format"""
    attack_type = attack.get('attack_type', 'Unknown')
    rule_id = ATTACK_TO_RULE.get(attack_type, 100001)
    confidence = attack.get('confidence', 0.5)
    rule_level = get_rule_level(confidence)
    
    # Parse timestamp
    timestamp = attack.get('timestamp', datetime.now().isoformat())
    
    alert = {
        'timestamp': timestamp,
        'rule': {
            'id': str(rule_id),
            'level': rule_level,
            'description': f'DeceptiCloud: {attack_type} attack detected',
            'groups': ['decepticloud', 'web', 'attack'],
            'firedtimes': 1,
        },
        'agent': {
            'id': '000',
            'name': 'decepticloud-proxy',
            'ip': '127.0.0.1',
        },
        'manager': {
            'name': 'wazuh-manager',
        },
        'data': {
            'srcip': attack.get('ip', ''),
            'url': attack.get('url', ''),
            'method': attack.get('method', 'GET'),
            'request': attack.get('path', ''),
            'user_agent': attack.get('user_agent', ''),
            'payload': attack.get('payload', ''),
            'confidence': confidence,
            'detection_method': attack.get('detection_method', 'ml_model'),
            'target_site': attack.get('target_site', ''),
        },
        'decoder': {
            'name': 'decepticloud',
        },
        'location': 'decepticloud-proxy',
        'full_log': f"{attack.get('method', 'GET')} {attack.get('url', '')} - {attack_type} detected (confidence: {confidence:.2%})",
    }
    
    return alert

def index_alert_to_wazuh(alert: dict) -> bool:
    """Index alert directly to Wazuh OpenSearch"""
    try:
        # Use current date for index name
        index_name = f"wazuh-alerts-4.x-{datetime.now().strftime('%Y.%m.%d')}"
        
        response = requests.post(
            f'{WAZUH_INDEXER_URL}/{index_name}/_doc',
            auth=(WAZUH_INDEXER_USER, WAZUH_INDEXER_PASS),
            json=alert,
            verify=False,
            timeout=5
        )
        
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"  ⚠ Failed to index alert: {e}")
        return False

def store_alert_in_db(alert: dict, attack_id: int):
    """Store Wazuh alert in DeceptiCloud database"""
    db = get_db_service()
    
    with db.get_connection() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO wazuh_alerts (
                timestamp, agent_id, agent_name, rule_id, rule_level,
                rule_description, alert_json, ip, processed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            alert['timestamp'],
            alert['agent']['id'],
            alert['agent']['name'],
            alert['rule']['id'],
            alert['rule']['level'],
            alert['rule']['description'],
            json.dumps(alert),
            alert['data']['srcip']
        ))
        conn.commit()

def sync_attacks_to_wazuh():
    """Sync all attacks from database to Wazuh"""
    print("🔄 Syncing DeceptiCloud attacks to Wazuh...")
    
    db = get_db_service()
    
    # Get all attacks
    attacks = db.get_attacks(limit=10000)
    print(f"  Found {len(attacks)} attacks to sync")
    
    synced = 0
    failed = 0
    
    for attack in attacks:
        # Create Wazuh alert
        alert = create_wazuh_alert(attack)
        
        # Index to Wazuh OpenSearch
        if index_alert_to_wazuh(alert):
            # Store in local database
            store_alert_in_db(alert, attack['id'])
            synced += 1
        else:
            failed += 1
        
        # Progress indicator
        if (synced + failed) % 50 == 0:
            print(f"  Progress: {synced + failed}/{len(attacks)} ({synced} synced, {failed} failed)")
    
    print(f"\n✅ Sync complete!")
    print(f"  Synced: {synced}")
    print(f"  Failed: {failed}")
    print(f"  Total: {len(attacks)}")
    
    # Verify in database
    with db.get_connection() as conn:
        wazuh_count = conn.execute("SELECT COUNT(*) as c FROM wazuh_alerts").fetchone()['c']
        print(f"\n📊 Wazuh alerts in database: {wazuh_count}")

if __name__ == '__main__':
    sync_attacks_to_wazuh()
