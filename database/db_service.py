#!/usr/bin/env python3
"""
DeceptiCloud Database Service
Centralized database access layer for all components
"""

import sqlite3
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager

# Database path
BASE_DIR = Path(__file__).parent.parent.resolve()
DB_PATH = BASE_DIR / 'database' / 'decepticloud.db'
SCHEMA_PATH = BASE_DIR / 'database' / 'schema.sql'

# Thread-local storage for connections
_thread_local = threading.local()


class DatabaseService:
    """Centralized database service with connection pooling"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DB_PATH)
        self._ensure_database()
    
    def _ensure_database(self):
        """Create database and tables if they don't exist"""
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        if not Path(self.db_path).exists() or Path(self.db_path).stat().st_size == 0:
            print(f"Initializing database at {self.db_path}")
            with self.get_connection() as conn:
                if SCHEMA_PATH.exists():
                    with open(SCHEMA_PATH) as f:
                        conn.executescript(f.read())
                    conn.commit()
                    print("Database schema created successfully")
    
    @contextmanager
    def get_connection(self):
        """Get a thread-safe database connection"""
        if not hasattr(_thread_local, 'connection'):
            _thread_local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=10.0
            )
            _thread_local.connection.row_factory = sqlite3.Row
        
        try:
            yield _thread_local.connection
        except Exception as e:
            _thread_local.connection.rollback()
            raise e
    
    # ==================== ATTACKS ====================
    
    def insert_attack(self, attack_data: Dict) -> int:
        """Insert a new attack record"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO attacks (
                    timestamp, ip, user_agent, method, url, path, query_string,
                    attack_type, attack_types_json, confidence, detection_method,
                    routed_to, honeypot_port, target_site, payload, headers_json,
                    classification_json, captured, session_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                attack_data.get('timestamp', datetime.now().isoformat()),
                attack_data.get('ip'),
                attack_data.get('user_agent'),
                attack_data.get('method'),
                attack_data.get('url'),
                attack_data.get('path'),
                attack_data.get('query_string'),
                attack_data.get('attack_type'),
                json.dumps(attack_data.get('attack_types', [])),
                attack_data.get('confidence', 0.0),
                attack_data.get('detection_method'),
                attack_data.get('routed_to'),
                attack_data.get('honeypot_port'),
                attack_data.get('target_site'),
                attack_data.get('payload'),
                json.dumps(attack_data.get('headers', {})),
                json.dumps(attack_data.get('classification', {})),
                attack_data.get('captured', True),
                attack_data.get('session_id')
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_attacks(self, limit: int = 100, offset: int = 0, 
                   filters: Dict = None) -> List[Dict]:
        """Get attacks with optional filters"""
        query = "SELECT * FROM attacks WHERE 1=1"
        params = []
        
        if filters:
            if filters.get('ip'):
                query += " AND ip = ?"
                params.append(filters['ip'])
            if filters.get('attack_type'):
                query += " AND attack_type = ?"
                params.append(filters['attack_type'])
            if filters.get('start_date'):
                query += " AND timestamp >= ?"
                params.append(filters['start_date'])
            if filters.get('end_date'):
                query += " AND timestamp <= ?"
                params.append(filters['end_date'])
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_attack_count(self, filters: Dict = None) -> int:
        """Get total attack count with optional filters"""
        query = "SELECT COUNT(*) as count FROM attacks WHERE 1=1"
        params = []
        
        if filters:
            if filters.get('ip'):
                query += " AND ip = ?"
                params.append(filters['ip'])
            if filters.get('attack_type'):
                query += " AND attack_type = ?"
                params.append(filters['attack_type'])
            if filters.get('start_date'):
                query += " AND timestamp >= ?"
                params.append(filters['start_date'])
            if filters.get('end_date'):
                query += " AND timestamp <= ?"
                params.append(filters['end_date'])
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchone()['count']
    
    def get_attack_stats(self) -> Dict:
        """Get attack statistics"""
        with self.get_connection() as conn:
            # Total attacks
            total = conn.execute("SELECT COUNT(*) as count FROM attacks").fetchone()['count']
            
            # By attack type
            by_type = conn.execute("""
                SELECT attack_type, COUNT(*) as count 
                FROM attacks 
                GROUP BY attack_type 
                ORDER BY count DESC
            """).fetchall()
            
            # By hour
            by_hour = conn.execute("""
                SELECT substr(timestamp, 12, 2) as hour, COUNT(*) as count
                FROM attacks
                GROUP BY hour
                ORDER BY hour
            """).fetchall()
            
            # Top IPs
            top_ips = conn.execute("""
                SELECT ip, COUNT(*) as count
                FROM attacks
                GROUP BY ip
                ORDER BY count DESC
                LIMIT 10
            """).fetchall()
            
            # Average confidence
            avg_conf = conn.execute("""
                SELECT AVG(confidence) as avg_confidence
                FROM attacks
                WHERE captured = 1 AND confidence > 0
            """).fetchone()
            
            return {
                'total': total,
                'by_type': {row['attack_type']: row['count'] for row in by_type},
                'by_hour': {row['hour']: row['count'] for row in by_hour},
                'top_ips': [{'ip': row['ip'], 'count': row['count']} for row in top_ips],
                'avg_confidence': avg_conf['avg_confidence'] or 0.0
            }
    
    # ==================== ATTACKER PROFILES ====================
    
    def upsert_attacker_profile(self, profile_data: Dict) -> int:
        """Insert or update attacker profile"""
        ip = profile_data.get('ip')
        
        with self.get_connection() as conn:
            # Check if profile exists
            existing = conn.execute(
                "SELECT id FROM attacker_profiles WHERE ip = ?", (ip,)
            ).fetchone()
            
            if existing:
                # Update existing
                conn.execute("""
                    UPDATE attacker_profiles SET
                        last_seen = ?,
                        attack_count = attack_count + 1,
                        attack_types_json = ?,
                        user_agents_json = ?,
                        behavioral_hash = ?,
                        ja3_fingerprint = ?,
                        http_fingerprint = ?,
                        canvas_fingerprint = ?,
                        tools_detected_json = ?,
                        threat_score = ?,
                        cluster_id = ?,
                        geolocation_json = ?,
                        asn = ?,
                        updated_at = ?
                    WHERE ip = ?
                """, (
                    profile_data.get('last_seen', datetime.now().isoformat()),
                    json.dumps(profile_data.get('attack_types', [])),
                    json.dumps(profile_data.get('user_agents', [])),
                    profile_data.get('behavioral_hash'),
                    profile_data.get('ja3_fingerprint'),
                    profile_data.get('http_fingerprint'),
                    profile_data.get('canvas_fingerprint'),
                    json.dumps(profile_data.get('tools_detected', [])),
                    profile_data.get('threat_score', 0.0),
                    profile_data.get('cluster_id'),
                    json.dumps(profile_data.get('geolocation', {})),
                    profile_data.get('asn'),
                    datetime.now().isoformat(),
                    ip
                ))
                conn.commit()
                return existing['id']
            else:
                # Insert new
                cursor = conn.execute("""
                    INSERT INTO attacker_profiles (
                        ip, first_seen, last_seen, attack_count, attack_types_json,
                        user_agents_json, behavioral_hash, ja3_fingerprint,
                        http_fingerprint, canvas_fingerprint, tools_detected_json,
                        threat_score, cluster_id, geolocation_json, asn
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ip,
                    profile_data.get('first_seen', datetime.now().isoformat()),
                    profile_data.get('last_seen', datetime.now().isoformat()),
                    1,
                    json.dumps(profile_data.get('attack_types', [])),
                    json.dumps(profile_data.get('user_agents', [])),
                    profile_data.get('behavioral_hash'),
                    profile_data.get('ja3_fingerprint'),
                    profile_data.get('http_fingerprint'),
                    profile_data.get('canvas_fingerprint'),
                    json.dumps(profile_data.get('tools_detected', [])),
                    profile_data.get('threat_score', 0.0),
                    profile_data.get('cluster_id'),
                    json.dumps(profile_data.get('geolocation', {})),
                    profile_data.get('asn')
                ))
                conn.commit()
                return cursor.lastrowid
    
    def get_attacker_profiles(self, limit: int = 100) -> List[Dict]:
        """Get all attacker profiles"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM attacker_profiles
                ORDER BY last_seen DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_attacker_profile_by_ip(self, ip: str) -> Optional[Dict]:
        """Get attacker profile by IP"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM attacker_profiles WHERE ip = ?", (ip,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_cluster_stats(self) -> Dict:
        """Get clustering statistics"""
        with self.get_connection() as conn:
            total = conn.execute(
                "SELECT COUNT(*) as count FROM attacker_profiles"
            ).fetchone()['count']
            
            clusters = conn.execute("""
                SELECT cluster_id, COUNT(*) as count
                FROM attacker_profiles
                WHERE cluster_id IS NOT NULL
                GROUP BY cluster_id
            """).fetchall()
            
            return {
                'total_profiles': total,
                'cluster_count': len(clusters),
                'clusters': [{'id': row['cluster_id'], 'count': row['count']} 
                           for row in clusters]
            }
    
    # ==================== EVENTS ====================
    
    def insert_event(self, event_data: Dict) -> int:
        """Insert a system event"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO events (
                    timestamp, event_type, severity, source, message,
                    details_json, ip, related_attack_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_data.get('timestamp', datetime.now().isoformat()),
                event_data.get('event_type'),
                event_data.get('severity', 'low'),
                event_data.get('source'),
                event_data.get('message'),
                json.dumps(event_data.get('details', {})),
                event_data.get('ip'),
                event_data.get('related_attack_id')
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_recent_events(self, limit: int = 100, event_type: str = None) -> List[Dict]:
        """Get recent events"""
        query = "SELECT * FROM events WHERE 1=1"
        params = []
        
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== HONEYPOT EVENTS ====================
    
    def insert_honeypot_event(self, event_data: Dict) -> int:
        """Insert a honeypot interaction event"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO honeypot_events (
                    timestamp, honeypot_name, honeypot_port, event_type,
                    ip, session_id, details_json, attack_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_data.get('timestamp', datetime.now().isoformat()),
                event_data.get('honeypot_name'),
                event_data.get('honeypot_port'),
                event_data.get('event_type'),
                event_data.get('ip'),
                event_data.get('session_id'),
                json.dumps(event_data.get('details', {})),
                event_data.get('attack_id')
            ))
            conn.commit()
            return cursor.lastrowid
    
    # ==================== UTILITY ====================
    
    def execute_query(self, query: str, params: Tuple = ()) -> List[Dict]:
        """Execute a custom query"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def close(self):
        """Close database connection"""
        if hasattr(_thread_local, 'connection'):
            _thread_local.connection.close()
            delattr(_thread_local, 'connection')


# Singleton instance
_db_service = None

def get_db_service() -> DatabaseService:
    """Get the singleton database service instance"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service


if __name__ == '__main__':
    # Test database setup
    db = get_db_service()
    print("Database initialized successfully")
    print(f"Database path: {db.db_path}")
    
    # Test insert
    test_attack = {
        'ip': '192.168.1.100',
        'user_agent': 'sqlmap/1.0',
        'method': 'GET',
        'url': 'http://localhost:8080/banking/search',
        'path': '/banking/search',
        'query_string': 'q=1\' OR 1=1--',
        'attack_type': 'SQLi',
        'attack_types': ['SQLi', 'Scanner'],
        'confidence': 0.95,
        'detection_method': 'hybrid',
        'routed_to': 'honeypot',
        'honeypot_port': 4001,
        'target_site': 'banking',
        'captured': True
    }
    
    attack_id = db.insert_attack(test_attack)
    print(f"Test attack inserted with ID: {attack_id}")
    
    # Test stats
    stats = db.get_attack_stats()
    print(f"Attack stats: {stats}")
