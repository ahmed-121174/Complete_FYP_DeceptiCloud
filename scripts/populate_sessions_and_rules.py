#!/usr/bin/env python3
"""
Populate Sessions and Routing Rules
Creates realistic active sessions and routing rules from existing attack data
"""

import sys
import json
import random
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_service import get_db_service

def populate_sessions():
    """Create realistic active sessions from recent attacks"""
    db = get_db_service()
    
    print("Creating active sessions from recent attacks...")
    
    with db.get_connection() as conn:
        # Get recent attacks grouped by IP
        cursor = conn.execute("""
            SELECT 
                ip,
                COUNT(*) as attack_count,
                MIN(timestamp) as first_attack,
                MAX(timestamp) as last_attack,
                GROUP_CONCAT(DISTINCT attack_type) as attack_types
            FROM attacks
            WHERE timestamp >= datetime('now', '-1 hour')
            GROUP BY ip
            HAVING attack_count >= 2
            ORDER BY attack_count DESC
            LIMIT 15
        """)
        
        recent_attackers = cursor.fetchall()
        
        if not recent_attackers:
            # If no recent attacks, use top attackers
            cursor = conn.execute("""
                SELECT 
                    ip,
                    COUNT(*) as attack_count,
                    MIN(timestamp) as first_attack,
                    MAX(timestamp) as last_attack,
                    GROUP_CONCAT(DISTINCT attack_type) as attack_types
                FROM attacks
                GROUP BY ip
                HAVING attack_count >= 3
                ORDER BY attack_count DESC
                LIMIT 15
            """)
            recent_attackers = cursor.fetchall()
        
        sessions_created = 0
        
        for attacker in recent_attackers:
            ip = attacker['ip']
            attack_count = attacker['attack_count']
            
            # Get profile_id
            cursor = conn.execute("SELECT id FROM attacker_profiles WHERE ip = ?", (ip,))
            profile = cursor.fetchone()
            profile_id = profile['id'] if profile else None
            
            # Generate session_id
            session_id = f"sess_{ip.replace('.', '_')}_{random.randint(1000, 9999)}"
            
            # Calculate session timing
            start_time = (datetime.now() - timedelta(minutes=random.randint(5, 45))).isoformat()
            
            # Get honeypots visited
            cursor = conn.execute("""
                SELECT DISTINCT target_site
                FROM attacks
                WHERE ip = ? AND routed_to = 'honeypot'
            """, (ip,))
            honeypots = [row['target_site'] for row in cursor.fetchall()]
            
            # Get actions
            cursor = conn.execute("""
                SELECT method, path, attack_type
                FROM attacks
                WHERE ip = ?
                ORDER BY timestamp DESC
                LIMIT 10
            """, (ip,))
            actions = []
            for row in cursor.fetchall():
                actions.append({
                    'method': row['method'],
                    'path': row['path'],
                    'attack_type': row['attack_type']
                })
            
            # Insert session
            conn.execute("""
                INSERT INTO sessions (
                    session_id, ip, profile_id, start_time, 
                    request_count, attack_count, honeypots_visited_json,
                    actions_json, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                session_id,
                ip,
                profile_id,
                start_time,
                attack_count + random.randint(5, 15),
                attack_count,
                json.dumps(honeypots),
                json.dumps(actions)
            ))
            
            sessions_created += 1
        
        conn.commit()
        print(f"✓ Created {sessions_created} active sessions")
        return sessions_created


def populate_routing_rules():
    """Create realistic routing rules"""
    db = get_db_service()
    
    print("Creating routing rules...")
    
    rules = [
        {
            'rule_name': 'High Threat Score to Honeypot',
            'priority': 100,
            'condition_json': json.dumps({
                'threat_score': {'min': 0.8},
                'description': 'Route attackers with high threat score to honeypot'
            }),
            'action': 'route_to_honeypot',
            'target_honeypot': 'auto',
            'is_active': True
        },
        {
            'rule_name': 'SQLi Attacks to Banking Honeypot',
            'priority': 90,
            'condition_json': json.dumps({
                'attack_types': ['SQLi'],
                'target_site': 'banking',
                'description': 'Route SQL injection attempts to banking honeypot'
            }),
            'action': 'route_to_honeypot',
            'target_honeypot': 'banking',
            'is_active': True
        },
        {
            'rule_name': 'XSS Attacks to E-commerce Honeypot',
            'priority': 85,
            'condition_json': json.dumps({
                'attack_types': ['XSS'],
                'target_site': 'ecommerce',
                'description': 'Route XSS attempts to e-commerce honeypot'
            }),
            'action': 'route_to_honeypot',
            'target_honeypot': 'ecommerce',
            'is_active': True
        },
        {
            'rule_name': 'Known Attacker IPs',
            'priority': 95,
            'condition_json': json.dumps({
                'ip_in_profile': True,
                'attack_count': {'min': 5},
                'description': 'Route known attackers to honeypot'
            }),
            'action': 'route_to_honeypot',
            'target_honeypot': 'auto',
            'is_active': True
        },
        {
            'rule_name': 'Scanner Tools Detection',
            'priority': 80,
            'condition_json': json.dumps({
                'user_agent_patterns': ['sqlmap', 'nikto', 'nmap', 'burp', 'metasploit'],
                'description': 'Route automated scanning tools to honeypot'
            }),
            'action': 'route_to_honeypot',
            'target_honeypot': 'auto',
            'is_active': True
        },
        {
            'rule_name': 'NoSQL Injection to API Honeypot',
            'priority': 85,
            'condition_json': json.dumps({
                'attack_types': ['NoSQLi'],
                'target_site': 'api_service',
                'description': 'Route NoSQL injection to API honeypot'
            }),
            'action': 'route_to_honeypot',
            'target_honeypot': 'api_service',
            'is_active': True
        },
        {
            'rule_name': 'Path Traversal to Admin Honeypot',
            'priority': 80,
            'condition_json': json.dumps({
                'attack_types': ['Path Traversal'],
                'path_patterns': ['/admin', '/config', '/backup'],
                'description': 'Route path traversal to admin honeypot'
            }),
            'action': 'route_to_honeypot',
            'target_honeypot': 'admin_panel',
            'is_active': True
        },
        {
            'rule_name': 'Low Confidence to Real Site',
            'priority': 30,
            'condition_json': json.dumps({
                'confidence': {'max': 0.6},
                'description': 'Route low confidence detections to real site'
            }),
            'action': 'route_to_real',
            'target_honeypot': None,
            'is_active': True
        },
        {
            'rule_name': 'Brute Force to Corporate Honeypot',
            'priority': 85,
            'condition_json': json.dumps({
                'attack_types': ['Brute Force'],
                'description': 'Route brute force attempts to corporate honeypot'
            }),
            'action': 'route_to_honeypot',
            'target_honeypot': 'corporate',
            'is_active': True
        },
        {
            'rule_name': 'Multiple Attack Types',
            'priority': 90,
            'condition_json': json.dumps({
                'attack_type_count': {'min': 3},
                'description': 'Route sophisticated multi-vector attacks to honeypot'
            }),
            'action': 'route_to_honeypot',
            'target_honeypot': 'auto',
            'is_active': True
        }
    ]
    
    with db.get_connection() as conn:
        rules_created = 0
        
        for rule in rules:
            try:
                conn.execute("""
                    INSERT INTO routing_rules (
                        rule_name, priority, condition_json, action,
                        target_honeypot, is_active, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rule['rule_name'],
                    rule['priority'],
                    rule['condition_json'],
                    rule['action'],
                    rule['target_honeypot'],
                    rule['is_active'],
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                rules_created += 1
            except Exception as e:
                if 'UNIQUE constraint' not in str(e):
                    print(f"Warning: Failed to create rule '{rule['rule_name']}': {e}")
        
        conn.commit()
        print(f"✓ Created {rules_created} routing rules")
        return rules_created


def main():
    print("=" * 60)
    print("POPULATING SESSIONS AND ROUTING RULES")
    print("=" * 60)
    
    # Populate sessions
    sessions_count = populate_sessions()
    
    # Populate routing rules
    rules_count = populate_routing_rules()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Active Sessions: {sessions_count}")
    print(f"Routing Rules: {rules_count}")
    print("\nData populated successfully!")


if __name__ == '__main__':
    main()
