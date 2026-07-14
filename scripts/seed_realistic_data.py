#!/usr/bin/env python3
"""
Seed Realistic Data for DeceptiCloud
Generates 412 attacks with realistic distribution, 12 attacker profiles, and 5 clusters
This data will be synced with Wazuh through the adaptive engine
"""

import sys
import json
import random
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_service import get_db_service

# Attack type distribution (realistic)
ATTACK_TYPES = {
    'SQLi': 145,
    'XSS': 98,
    'NoSQLi': 67,
    'Path Traversal': 42,
    'Brute Force': 28,
    'Port Scan': 18,
    'DDoS': 14,
}

# Attacker IPs (12 profiles)
ATTACKER_IPS = [
    '45.142.212.61',   # Cluster 0 - SQLi specialists
    '185.220.101.42',  # Cluster 0
    '192.241.234.167', # Cluster 0
    '104.248.144.120', # Cluster 1 - XSS attackers
    '167.99.172.201',  # Cluster 1
    '159.89.202.34',   # Cluster 1
    '178.128.83.165',  # Cluster 2 - Scanners
    '206.189.156.78',  # Cluster 2
    '142.93.129.45',   # Cluster 3 - Brute force
    '68.183.44.201',   # Cluster 3
    '134.209.24.123',  # Cluster 4 - Mixed attacks
    '157.230.39.201',  # Cluster 4
]

# Cluster assignments
CLUSTERS = {
    0: [0, 1, 2],      # SQLi specialists
    1: [3, 4, 5],      # XSS attackers
    2: [6, 7],         # Scanners
    3: [8, 9],         # Brute force
    4: [10, 11],       # Mixed attacks
}

# User agents by cluster
USER_AGENTS = {
    0: ['sqlmap/1.4.7', 'Mozilla/5.0 (compatible; sqlmap/1.4.7)', 'python-requests/2.25.1'],
    1: ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'curl/7.68.0'],
    2: ['Nmap Scripting Engine', 'masscan/1.0.5', 'nikto/2.1.6'],
    3: ['Hydra v9.1', 'Mozilla/5.0 (X11; Linux x86_64)', 'python-requests/2.26.0'],
    4: ['Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', 'Burp Suite Professional'],
}

# Sites
SITES = ['banking', 'ecommerce', 'healthcare', 'blog', 'api_service', 'corporate', 'admin_panel']

# SQL injection payloads
SQLI_PAYLOADS = [
    "' OR '1'='1",
    "1' UNION SELECT NULL,NULL,NULL--",
    "admin'--",
    "' OR 1=1--",
    "1' AND '1'='1",
    "; DROP TABLE users--",
]

# XSS payloads
XSS_PAYLOADS = [
    "<script>alert('XSS')</script>",
    "<img src=x onerror=alert(1)>",
    "javascript:alert(document.cookie)",
    "<svg onload=alert(1)>",
]

# NoSQLi payloads
NOSQLI_PAYLOADS = [
    "{'$gt':''}",
    "{'$ne':null}",
    "{'$where':'1==1'}",
]

def generate_attack_data(attack_type: str, ip: str, cluster_id: int, timestamp: datetime) -> dict:
    """Generate realistic attack data"""
    site = random.choice(SITES)
    method = 'POST' if attack_type in ['SQLi', 'NoSQLi', 'Brute Force'] else 'GET'
    
    # Generate payload based on attack type
    if attack_type == 'SQLi':
        payload = random.choice(SQLI_PAYLOADS)
        path = f'/{site}/search'
        query = f'q={payload}'
    elif attack_type == 'XSS':
        payload = random.choice(XSS_PAYLOADS)
        path = f'/{site}/comment'
        query = f'text={payload}'
    elif attack_type == 'NoSQLi':
        payload = random.choice(NOSQLI_PAYLOADS)
        path = f'/{site}/api/users'
        query = f'filter={payload}'
    elif attack_type == 'Path Traversal':
        payload = '../../../etc/passwd'
        path = f'/{site}/download'
        query = f'file={payload}'
    elif attack_type == 'Brute Force':
        payload = f'password{random.randint(1, 999)}'
        path = f'/{site}/login'
        query = f'username=admin&password={payload}'
    elif attack_type == 'Port Scan':
        payload = ''
        path = f'/{site}/'
        query = ''
    elif attack_type == 'DDoS':
        payload = 'A' * 10000
        path = f'/{site}/api/data'
        query = f'data={payload}'
    else:
        payload = ''
        path = f'/{site}/'
        query = ''
    
    url = f'http://localhost:8080{path}?{query}' if query else f'http://localhost:8080{path}'
    
    # Confidence varies by detection method
    confidence = random.uniform(0.85, 0.99)
    
    # Detection method distribution
    detection_methods = ['ml_model', 'signature', 'hybrid', 'anomaly']
    detection_method = random.choices(
        detection_methods,
        weights=[0.45, 0.25, 0.25, 0.05]
    )[0]
    
    # User agent from cluster
    user_agent = random.choice(USER_AGENTS.get(cluster_id, USER_AGENTS[4]))
    
    return {
        'timestamp': timestamp.isoformat(),
        'ip': ip,
        'user_agent': user_agent,
        'method': method,
        'url': url,
        'path': path,
        'query_string': query,
        'attack_type': attack_type,
        'attack_types': [attack_type],
        'confidence': confidence,
        'detection_method': detection_method,
        'routed_to': 'honeypot',
        'honeypot_port': 4001 + SITES.index(site),
        'target_site': site,
        'payload': payload,
        'headers': {
            'User-Agent': user_agent,
            'Host': 'localhost:8080',
            'Accept': '*/*',
        },
        'classification': {
            'attack_types': [attack_type],
            'confidence': confidence,
            'method': detection_method,
        },
        'captured': True,
        'session_id': f'sess_{ip.replace(".", "_")}_{timestamp.strftime("%Y%m%d%H%M%S")}',
    }

def generate_attacker_profile(ip: str, cluster_id: int, attack_count: int, attack_types: list) -> dict:
    """Generate attacker profile"""
    first_seen = datetime.now() - timedelta(days=random.randint(1, 30))
    last_seen = datetime.now() - timedelta(hours=random.randint(0, 24))
    
    # Threat score based on attack count and types
    base_score = min(attack_count / 50.0, 0.6)
    type_score = len(attack_types) * 0.1
    threat_score = min(base_score + type_score, 1.0)
    
    # Behavioral hash (simulated)
    behavioral_hash = f'bh_{ip.replace(".", "")}_{cluster_id}'
    
    # User agents from cluster
    user_agents = USER_AGENTS.get(cluster_id, USER_AGENTS[4])
    
    return {
        'ip': ip,
        'first_seen': first_seen.isoformat(),
        'last_seen': last_seen.isoformat(),
        'attack_count': attack_count,
        'attack_types': attack_types,
        'user_agents': user_agents,
        'behavioral_hash': behavioral_hash,
        'ja3_fingerprint': f'ja3_{random.randint(10000, 99999)}',
        'http_fingerprint': f'http_{random.randint(10000, 99999)}',
        'canvas_fingerprint': None,
        'tools_detected': ['sqlmap'] if cluster_id == 0 else ['nmap'] if cluster_id == 2 else [],
        'threat_score': threat_score,
        'cluster_id': cluster_id,
        'geolocation': {
            'country': random.choice(['US', 'RU', 'CN', 'BR', 'IN']),
            'city': random.choice(['New York', 'Moscow', 'Beijing', 'São Paulo', 'Mumbai']),
        },
        'asn': f'AS{random.randint(10000, 99999)}',
    }

def seed_data():
    """Seed the database with realistic data"""
    print("🌱 Seeding DeceptiCloud database with realistic data...")
    
    db = get_db_service()
    
    # Clear existing data
    print("  Clearing existing data...")
    with db.get_connection() as conn:
        conn.execute("DELETE FROM attacks")
        conn.execute("DELETE FROM attacker_profiles")
        conn.execute("DELETE FROM wazuh_alerts")
        conn.commit()
    
    # Generate attacks
    print(f"  Generating 412 attacks...")
    attacks_generated = 0
    attack_distribution = {}
    
    # Distribute attacks across time (last 7 days)
    start_time = datetime.now() - timedelta(days=7)
    
    for attack_type, count in ATTACK_TYPES.items():
        attack_distribution[attack_type] = []
        
        for i in range(count):
            # Select random attacker from appropriate cluster
            if attack_type == 'SQLi':
                cluster_id = 0
            elif attack_type == 'XSS':
                cluster_id = 1
            elif attack_type in ['Port Scan']:
                cluster_id = 2
            elif attack_type == 'Brute Force':
                cluster_id = 3
            else:
                cluster_id = 4
            
            ip_indices = CLUSTERS[cluster_id]
            ip = ATTACKER_IPS[random.choice(ip_indices)]
            
            # Generate timestamp (distributed over 7 days)
            timestamp = start_time + timedelta(
                seconds=random.randint(0, 7 * 24 * 60 * 60)
            )
            
            attack_data = generate_attack_data(attack_type, ip, cluster_id, timestamp)
            attack_id = db.insert_attack(attack_data)
            attack_distribution[attack_type].append((ip, attack_id))
            attacks_generated += 1
    
    print(f"  ✓ Generated {attacks_generated} attacks")
    
    # Generate attacker profiles (12 profiles, 5 clusters)
    print(f"  Generating 12 attacker profiles with 5 clusters...")
    
    for cluster_id, ip_indices in CLUSTERS.items():
        for ip_idx in ip_indices:
            ip = ATTACKER_IPS[ip_idx]
            
            # Count attacks for this IP
            attack_count = sum(
                1 for attacks in attack_distribution.values()
                for attacker_ip, _ in attacks
                if attacker_ip == ip
            )
            
            # Get attack types for this IP
            attack_types = list(set(
                attack_type
                for attack_type, attacks in attack_distribution.items()
                for attacker_ip, _ in attacks
                if attacker_ip == ip
            ))
            
            profile_data = generate_attacker_profile(ip, cluster_id, attack_count, attack_types)
            
            # Insert profile with correct attack count
            profile_data['attack_count'] = attack_count
            db.upsert_attacker_profile(profile_data)
    
    print(f"  ✓ Generated 12 attacker profiles across 5 clusters")
    
    # Verify data
    print("\n📊 Data Summary:")
    stats = db.get_attack_stats()
    print(f"  Total Attacks: {stats['total']}")
    print(f"  Attack Types: {len(stats['by_type'])}")
    print(f"  Unique IPs: {len(stats['top_ips'])}")
    print(f"  Avg Confidence: {stats['avg_confidence']:.2%}")
    
    profiles = db.get_attacker_profiles(limit=100)
    print(f"  Attacker Profiles: {len(profiles)}")
    
    cluster_stats = db.get_cluster_stats()
    print(f"  Clusters: {cluster_stats['cluster_count']}")
    
    print("\n✅ Data seeding complete!")
    print("\n💡 Next steps:")
    print("  1. Start the adaptive engine to sync with Wazuh")
    print("  2. Run: python3 scripts/sync_wazuh_alerts.py")
    print("  3. Refresh the dashboard to see the data")

if __name__ == '__main__':
    seed_data()
