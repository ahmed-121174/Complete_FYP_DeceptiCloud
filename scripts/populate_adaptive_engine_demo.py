import sqlite3
import json
from datetime import datetime, timedelta
import random

DB_PATH = "database/decepticloud.db"

def populate():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Populate ML Models
    attack_types = ['XSS', 'Brute Force', 'Port Scan', 'Credential Stuffing', 'SQL Injection', 'DDoS']
    for i, atype in enumerate(attack_types):
        accuracy = 0.94 + (random.random() * 0.05)
        precision = 0.92 + (random.random() * 0.06)
        recall = 0.93 + (random.random() * 0.04)
        f1 = 2 * (precision * recall) / (precision + recall)
        
        cursor.execute("""
            INSERT INTO ml_models (model_name, model_type, version, file_path, accuracy, precision_val, recall_val, f1_score, training_date, training_samples, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"{atype.lower().replace(' ', '_')}_v1",
            atype,
            "1.0.4",
            f"models/{atype.lower().replace(' ', '_')}_v1.pkl",
            accuracy,
            precision,
            recall,
            f1,
            (datetime.now() - timedelta(days=random.randint(1, 5))).isoformat(),
            random.randint(500, 2000),
            1
        ))

    # 2. Populate Wazuh Alerts
    agents = ['banking-real', 'ecommerce-hp', 'healthcare-real', 'admin-hp']
    rules = [
        {"id": "100001", "level": 12, "desc": "Critical: Multiple failed login attempts (Brute Force detected)"},
        {"id": "100005", "level": 7, "desc": "Warning: Web shell pattern detected in HTTP request"},
        {"id": "100010", "level": 10, "desc": "Alert: Unusual outbound connection to known malicious IP"},
        {"id": "100015", "level": 3, "desc": "Info: New agent registered: dc-real-blog"}
    ]
    
    for i in range(20):
        agent = random.choice(agents)
        rule = random.choice(rules)
        ts = (datetime.now() - timedelta(minutes=random.randint(1, 120))).isoformat()
        ip = f"192.168.1.{random.randint(10, 250)}"
        
        cursor.execute("""
            INSERT INTO wazuh_alerts (timestamp, agent_id, agent_name, rule_id, rule_level, rule_description, alert_json, ip, processed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ts,
            f"00{random.randint(1, 9)}",
            agent,
            rule["id"],
            rule["level"],
            rule["desc"],
            json.dumps({"dummy": "data"}),
            ip,
            0
        ))

    # 3. Add some drift events to 'events' table
    for i in range(3):
        ts = (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat()
        cursor.execute("""
            INSERT INTO events (timestamp, event_type, severity, source, message, details_json, ip)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            ts,
            'ml',
            'medium',
            'adaptive_engine_drift',
            f'Model drift detected in {random.choice(attack_types)} detector',
            json.dumps({"drift_score": 0.15, "threshold": 0.10}),
            None
        ))

    conn.commit()
    conn.close()
    print("✓ Demo data populated for Adaptive Engine")

if __name__ == "__main__":
    populate()
