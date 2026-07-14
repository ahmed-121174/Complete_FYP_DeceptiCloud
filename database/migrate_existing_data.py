#!/usr/bin/env python3
"""
Migrate existing JSONL attack logs to the new database
"""

import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_service import get_db_service

BASE_DIR = Path(__file__).parent.parent.resolve()

def migrate_proxy_attacks():
    """Migrate attacks from proxy/logs/proxy_attacks.jsonl"""
    db = get_db_service()
    
    attack_log = BASE_DIR / 'proxy' / 'logs' / 'proxy_attacks.jsonl'
    if not attack_log.exists():
        attack_log = BASE_DIR / 'logs' / 'proxy_attacks.jsonl'
    
    if not attack_log.exists():
        print(f"No attack log found at {attack_log}")
        return 0
    
    print(f"Migrating attacks from {attack_log}")
    count = 0
    
    with open(attack_log) as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                
                # Extract classification data
                cls = entry.get('classification', {})
                attack_types = cls.get('attack_types', [])
                
                # Build attack data
                attack_data = {
                    'timestamp': entry.get('timestamp', datetime.now().isoformat()),
                    'ip': entry.get('ip', ''),
                    'user_agent': entry.get('user_agent', ''),
                    'method': entry.get('method', 'GET'),
                    'url': entry.get('url', ''),
                    'path': entry.get('path', ''),
                    'query_string': entry.get('query_string', ''),
                    'attack_type': attack_types[0] if attack_types else 'Unknown',
                    'attack_types': attack_types,
                    'confidence': cls.get('confidence', 0.0),
                    'detection_method': cls.get('method', 'unknown'),
                    'routed_to': entry.get('routed_to', 'honeypot'),
                    'honeypot_port': entry.get('honeypot_port'),
                    'target_site': entry.get('target', ''),
                    'payload': entry.get('payload', ''),
                    'headers': entry.get('headers', {}),
                    'classification': cls,
                    'captured': entry.get('captured', True),
                    'session_id': entry.get('session_id')
                }
                
                db.insert_attack(attack_data)
                count += 1
                
                # Also create/update attacker profile
                if attack_data['ip']:
                    profile_data = {
                        'ip': attack_data['ip'],
                        'first_seen': attack_data['timestamp'],
                        'last_seen': attack_data['timestamp'],
                        'attack_types': attack_types,
                        'user_agents': [attack_data['user_agent']] if attack_data['user_agent'] else [],
                        'threat_score': attack_data['confidence']
                    }
                    db.upsert_attacker_profile(profile_data)
                
            except Exception as e:
                print(f"Error migrating entry: {e}")
                continue
    
    print(f"Migrated {count} attacks")
    return count

def main():
    print("=" * 60)
    print("DeceptiCloud Data Migration")
    print("=" * 60)
    
    total = migrate_proxy_attacks()
    
    print("\n" + "=" * 60)
    print(f"Migration complete: {total} records migrated")
    print("=" * 60)
    
    # Show stats
    db = get_db_service()
    stats = db.get_attack_stats()
    print(f"\nDatabase Statistics:")
    print(f"  Total attacks: {stats['total']}")
    print(f"  Attack types: {len(stats['by_type'])}")
    print(f"  Unique IPs: {len(stats['top_ips'])}")
    print(f"  Avg confidence: {stats['avg_confidence']:.2%}")

if __name__ == '__main__':
    main()
