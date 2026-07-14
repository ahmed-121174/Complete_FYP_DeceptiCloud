"""
Unit Tests for Database Service
Tests database operations, CRUD functionality, and data integrity
"""
import pytest
import sqlite3
import tempfile
import json
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.db_service import DatabaseService, get_db_service


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    # Initialize database with schema
    db = DatabaseService(db_path)
    yield db
    
    # Cleanup
    db.close()
    Path(db_path).unlink(missing_ok=True)


class TestDatabaseInitialization:
    """Test database initialization and schema creation"""
    
    def test_database_creation(self, temp_db):
        """Test that database file is created"""
        assert Path(temp_db.db_path).exists()
    
    def test_tables_exist(self, temp_db):
        """Test that all required tables are created"""
        with temp_db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row['name'] for row in cursor.fetchall()}
        
        required_tables = {'attacks', 'attacker_profiles', 'events'}
        assert required_tables.issubset(tables), f"Missing tables: {required_tables - tables}"


class TestAttackOperations:
    """Test attack-related database operations"""
    
    def test_insert_attack(self, temp_db):
        """Test inserting an attack record"""
        attack_data = {
            'ip': '192.168.1.100',
            'user_agent': 'sqlmap/1.0',
            'method': 'GET',
            'url': 'http://test.com/search?q=1\' OR 1=1--',
            'path': '/search',
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
        
        attack_id = temp_db.insert_attack(attack_data)
        assert attack_id > 0
    
    def test_get_attacks(self, temp_db):
        """Test retrieving attacks"""
        # Insert test attacks
        for i in range(5):
            temp_db.insert_attack({
                'ip': f'192.168.1.{100+i}',
                'method': 'GET',
                'url': f'http://test.com/page{i}',
                'path': f'/page{i}',
                'attack_type': 'SQLi',
                'confidence': 0.9,
                'detection_method': 'rule_based'
            })
        
        attacks = temp_db.get_attacks(limit=10)
        assert len(attacks) == 5
        assert all(isinstance(a, dict) for a in attacks)
    
    def test_get_attack_count(self, temp_db):
        """Test counting attacks"""
        # Insert test attacks
        for i in range(3):
            temp_db.insert_attack({
                'ip': '192.168.1.100',
                'method': 'GET',
                'url': 'http://test.com',
                'path': '/',
                'attack_type': 'XSS',
                'confidence': 0.8
            })
        
        count = temp_db.get_attack_count()
        assert count == 3
    
    def test_get_attacks_with_filters(self, temp_db):
        """Test filtering attacks"""
        # Insert attacks with different IPs
        temp_db.insert_attack({
            'ip': '10.0.0.1',
            'method': 'GET',
            'url': 'http://test.com',
            'path': '/',
            'attack_type': 'SQLi',
            'confidence': 0.9
        })
        temp_db.insert_attack({
            'ip': '10.0.0.2',
            'method': 'GET',
            'url': 'http://test.com',
            'path': '/',
            'attack_type': 'XSS',
            'confidence': 0.8
        })
        
        # Filter by IP
        filtered = temp_db.get_attacks(filters={'ip': '10.0.0.1'})
        assert len(filtered) == 1
        assert filtered[0]['ip'] == '10.0.0.1'
    
    def test_get_attack_stats(self, temp_db):
        """Test attack statistics"""
        # Insert various attacks
        for attack_type in ['SQLi', 'XSS', 'SQLi', 'NoSQLi']:
            temp_db.insert_attack({
                'ip': '192.168.1.100',
                'method': 'GET',
                'url': 'http://test.com',
                'path': '/',
                'attack_type': attack_type,
                'confidence': 0.9,
                'captured': True
            })
        
        stats = temp_db.get_attack_stats()
        assert stats['total'] == 4
        assert 'by_type' in stats
        assert stats['by_type']['SQLi'] == 2
        assert 'top_ips' in stats


class TestAttackerProfiles:
    """Test attacker profile operations"""
    
    def test_insert_attacker_profile(self, temp_db):
        """Test inserting a new attacker profile"""
        profile_data = {
            'ip': '192.168.1.100',
            'attack_types': ['SQLi', 'XSS'],
            'user_agents': ['sqlmap/1.0'],
            'behavioral_hash': 'abc123',
            'threat_score': 0.85,
            'cluster_id': 1
        }
        
        profile_id = temp_db.upsert_attacker_profile(profile_data)
        assert profile_id > 0
    
    def test_update_attacker_profile(self, temp_db):
        """Test updating an existing attacker profile"""
        ip = '192.168.1.100'
        
        # Insert initial profile
        temp_db.upsert_attacker_profile({
            'ip': ip,
            'attack_types': ['SQLi'],
            'threat_score': 0.5
        })
        
        # Update profile
        temp_db.upsert_attacker_profile({
            'ip': ip,
            'attack_types': ['SQLi', 'XSS'],
            'threat_score': 0.9
        })
        
        # Verify update
        profile = temp_db.get_attacker_profile_by_ip(ip)
        assert profile is not None
        assert profile['attack_count'] == 2  # Should increment
    
    def test_get_attacker_profiles(self, temp_db):
        """Test retrieving all attacker profiles"""
        # Insert multiple profiles
        for i in range(3):
            temp_db.upsert_attacker_profile({
                'ip': f'192.168.1.{100+i}',
                'attack_types': ['SQLi'],
                'threat_score': 0.7
            })
        
        profiles = temp_db.get_attacker_profiles(limit=10)
        assert len(profiles) == 3
    
    def test_get_cluster_stats(self, temp_db):
        """Test cluster statistics"""
        # Insert profiles with clusters
        for i in range(5):
            temp_db.upsert_attacker_profile({
                'ip': f'192.168.1.{100+i}',
                'attack_types': ['SQLi'],
                'cluster_id': i % 2  # 2 clusters
            })
        
        stats = temp_db.get_cluster_stats()
        assert stats['total_profiles'] == 5
        assert stats['cluster_count'] == 2


class TestEventOperations:
    """Test event logging operations"""
    
    def test_insert_event(self, temp_db):
        """Test inserting an event"""
        event_data = {
            'event_type': 'attack_detected',
            'severity': 'high',
            'source': 'proxy',
            'message': 'SQLi attack detected',
            'details': {'confidence': 0.95},
            'ip': '192.168.1.100'
        }
        
        event_id = temp_db.insert_event(event_data)
        assert event_id > 0
    
    def test_get_recent_events(self, temp_db):
        """Test retrieving recent events"""
        # Insert multiple events
        for i in range(5):
            temp_db.insert_event({
                'event_type': 'test_event',
                'severity': 'low',
                'source': 'test',
                'message': f'Test event {i}'
            })
        
        events = temp_db.get_recent_events(limit=10)
        assert len(events) == 5
    
    def test_filter_events_by_type(self, temp_db):
        """Test filtering events by type"""
        temp_db.insert_event({
            'event_type': 'attack',
            'severity': 'high',
            'source': 'proxy',
            'message': 'Attack detected'
        })
        temp_db.insert_event({
            'event_type': 'system',
            'severity': 'low',
            'source': 'dashboard',
            'message': 'System event'
        })
        
        attack_events = temp_db.get_recent_events(event_type='attack')
        assert len(attack_events) == 1
        assert attack_events[0]['event_type'] == 'attack'


class TestDataIntegrity:
    """Test data integrity and constraints"""
    
    def test_json_serialization(self, temp_db):
        """Test JSON field serialization"""
        attack_data = {
            'ip': '192.168.1.100',
            'method': 'GET',
            'url': 'http://test.com',
            'path': '/',
            'attack_type': 'SQLi',
            'attack_types': ['SQLi', 'XSS', 'NoSQLi'],
            'headers': {'User-Agent': 'test', 'X-Custom': 'value'},
            'classification': {'confidence': 0.95, 'method': 'hybrid'}
        }
        
        attack_id = temp_db.insert_attack(attack_data)
        attacks = temp_db.get_attacks(limit=1)
        
        assert len(attacks) == 1
        attack = attacks[0]
        
        # Verify JSON fields are properly stored and retrieved
        assert 'attack_types_json' in attack
        assert 'headers_json' in attack
        assert 'classification_json' in attack
    
    def test_timestamp_format(self, temp_db):
        """Test timestamp format consistency"""
        temp_db.insert_attack({
            'ip': '192.168.1.100',
            'method': 'GET',
            'url': 'http://test.com',
            'path': '/',
            'attack_type': 'SQLi'
        })
        
        attacks = temp_db.get_attacks(limit=1)
        timestamp = attacks[0]['timestamp']
        
        # Verify ISO format
        try:
            datetime.fromisoformat(timestamp)
        except ValueError:
            pytest.fail("Timestamp is not in ISO format")


class TestThreadSafety:
    """Test thread-safe operations"""
    
    def test_concurrent_inserts(self, temp_db):
        """Test concurrent attack insertions"""
        import threading
        
        def insert_attacks(db, count):
            for i in range(count):
                db.insert_attack({
                    'ip': f'192.168.1.{i}',
                    'method': 'GET',
                    'url': 'http://test.com',
                    'path': '/',
                    'attack_type': 'SQLi',
                    'confidence': 0.9
                })
        
        threads = []
        for _ in range(3):
            t = threading.Thread(target=insert_attacks, args=(temp_db, 5))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Verify all inserts succeeded
        count = temp_db.get_attack_count()
        assert count == 15


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
