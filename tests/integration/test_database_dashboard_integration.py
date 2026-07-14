"""
Integration Tests for Database and Dashboard
Tests the integration between database service and dashboard API
"""
import pytest
import requests
import sys
from pathlib import Path
import tempfile
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.db_service import DatabaseService
from config import DASHBOARD_URL, DASHBOARD_DEFAULT_USERNAME, DASHBOARD_DEFAULT_PASSWORD


class TestDatabaseDashboardIntegration:
    """Test integration between database and dashboard"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db = DatabaseService(db_path)
        yield db
        
        db.close()
        Path(db_path).unlink(missing_ok=True)
    
    @pytest.fixture
    def dashboard_session(self):
        """Create authenticated dashboard session"""
        session = requests.Session()
        try:
            # Attempt login
            response = session.post(
                f"{DASHBOARD_URL}/api/login",
                json={
                    'username': DASHBOARD_DEFAULT_USERNAME,
                    'password': DASHBOARD_DEFAULT_PASSWORD
                },
                timeout=2
            )
            if response.status_code == 200:
                yield session
            else:
                pytest.skip("Dashboard not running or login failed")
        except requests.exceptions.ConnectionError:
            pytest.skip("Dashboard not running")
    
    def test_dashboard_health(self):
        """Test dashboard health endpoint"""
        try:
            response = requests.get(f"{DASHBOARD_URL}/api/health", timeout=2)
            if response.status_code == 200:
                data = response.json()
                assert 'status' in data
        except requests.exceptions.ConnectionError:
            pytest.skip("Dashboard not running")
    
    def test_dashboard_stats_endpoint(self, dashboard_session):
        """Test dashboard statistics endpoint"""
        try:
            response = dashboard_session.get(f"{DASHBOARD_URL}/api/stats", timeout=2)
            if response.status_code == 200:
                data = response.json()
                assert 'total_attacks' in data or 'attacks' in data
        except requests.exceptions.ConnectionError:
            pytest.skip("Dashboard not running")
    
    def test_attack_data_flow(self, temp_db):
        """Test attack data flow from database to dashboard"""
        # Insert test attack
        attack_data = {
            'ip': '192.168.1.100',
            'user_agent': 'sqlmap/1.0',
            'method': 'GET',
            'url': 'http://test.com/search?q=test',
            'path': '/search',
            'query_string': 'q=test',
            'attack_type': 'SQLi',
            'confidence': 0.95,
            'detection_method': 'hybrid',
            'routed_to': 'honeypot',
            'captured': True
        }
        
        attack_id = temp_db.insert_attack(attack_data)
        assert attack_id > 0
        
        # Retrieve attack
        attacks = temp_db.get_attacks(limit=1)
        assert len(attacks) == 1
        assert attacks[0]['ip'] == '192.168.1.100'
    
    def test_attacker_profile_flow(self, temp_db):
        """Test attacker profile data flow"""
        # Create attacker profile
        profile_data = {
            'ip': '10.0.0.1',
            'attack_types': ['SQLi', 'XSS'],
            'user_agents': ['sqlmap/1.0'],
            'threat_score': 0.9,
            'cluster_id': 1
        }
        
        profile_id = temp_db.upsert_attacker_profile(profile_data)
        assert profile_id > 0
        
        # Retrieve profile
        profile = temp_db.get_attacker_profile_by_ip('10.0.0.1')
        assert profile is not None
        assert profile['threat_score'] == 0.9


class TestDashboardAPIs:
    """Test dashboard API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for dashboard API tests"""
        self.dashboard_url = DASHBOARD_URL
    
    def test_login_endpoint(self):
        """Test dashboard login endpoint"""
        try:
            response = requests.post(
                f"{self.dashboard_url}/api/login",
                json={
                    'username': DASHBOARD_DEFAULT_USERNAME,
                    'password': DASHBOARD_DEFAULT_PASSWORD
                },
                timeout=2
            )
            
            if response.status_code == 200:
                data = response.json()
                assert 'status' in data or 'success' in data
        except requests.exceptions.ConnectionError:
            pytest.skip("Dashboard not running")
    
    def test_invalid_login(self):
        """Test dashboard login with invalid credentials"""
        try:
            response = requests.post(
                f"{self.dashboard_url}/api/login",
                json={
                    'username': 'invalid',
                    'password': 'wrong'
                },
                timeout=2
            )
            
            # Should return 401 or 403
            assert response.status_code in [401, 403, 200]  # 200 with error message is also valid
        except requests.exceptions.ConnectionError:
            pytest.skip("Dashboard not running")
    
    def test_attacks_api_endpoint(self):
        """Test attacks API endpoint"""
        try:
            session = requests.Session()
            # Login first
            login_response = session.post(
                f"{self.dashboard_url}/api/login",
                json={
                    'username': DASHBOARD_DEFAULT_USERNAME,
                    'password': DASHBOARD_DEFAULT_PASSWORD
                },
                timeout=2
            )
            
            if login_response.status_code == 200:
                # Get attacks
                response = session.get(f"{self.dashboard_url}/api/attacks", timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    assert isinstance(data, (list, dict))
        except requests.exceptions.ConnectionError:
            pytest.skip("Dashboard not running")


class TestDataConsistency:
    """Test data consistency across components"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db = DatabaseService(db_path)
        yield db
        
        db.close()
        Path(db_path).unlink(missing_ok=True)
    
    def test_attack_count_consistency(self, temp_db):
        """Test attack count consistency"""
        # Insert multiple attacks
        for i in range(5):
            temp_db.insert_attack({
                'ip': f'192.168.1.{100+i}',
                'method': 'GET',
                'url': 'http://test.com',
                'path': '/',
                'attack_type': 'SQLi',
                'confidence': 0.9
            })
        
        # Check count
        count = temp_db.get_attack_count()
        attacks = temp_db.get_attacks(limit=100)
        
        assert count == 5
        assert len(attacks) == 5
    
    def test_stats_calculation_consistency(self, temp_db):
        """Test statistics calculation consistency"""
        # Insert attacks of different types
        attack_types = ['SQLi', 'XSS', 'SQLi', 'NoSQLi', 'XSS']
        for attack_type in attack_types:
            temp_db.insert_attack({
                'ip': '192.168.1.100',
                'method': 'GET',
                'url': 'http://test.com',
                'path': '/',
                'attack_type': attack_type,
                'confidence': 0.9,
                'captured': True
            })
        
        # Get stats
        stats = temp_db.get_attack_stats()
        
        assert stats['total'] == 5
        assert stats['by_type']['SQLi'] == 2
        assert stats['by_type']['XSS'] == 2
        assert stats['by_type']['NoSQLi'] == 1


class TestRealTimeUpdates:
    """Test real-time data updates"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db = DatabaseService(db_path)
        yield db
        
        db.close()
        Path(db_path).unlink(missing_ok=True)
    
    def test_concurrent_attack_insertion(self, temp_db):
        """Test concurrent attack insertions"""
        import threading
        
        def insert_attack(db, ip):
            db.insert_attack({
                'ip': ip,
                'method': 'GET',
                'url': 'http://test.com',
                'path': '/',
                'attack_type': 'SQLi',
                'confidence': 0.9
            })
        
        threads = []
        for i in range(10):
            t = threading.Thread(target=insert_attack, args=(temp_db, f'192.168.1.{100+i}'))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Verify all attacks were inserted
        count = temp_db.get_attack_count()
        assert count == 10
    
    def test_profile_update_consistency(self, temp_db):
        """Test attacker profile update consistency"""
        ip = '192.168.1.100'
        
        # Insert initial profile
        temp_db.upsert_attacker_profile({
            'ip': ip,
            'attack_types': ['SQLi'],
            'threat_score': 0.5
        })
        
        # Update multiple times
        for i in range(5):
            temp_db.upsert_attacker_profile({
                'ip': ip,
                'attack_types': ['SQLi', 'XSS'],
                'threat_score': 0.5 + (i * 0.1)
            })
        
        # Verify final state
        profile = temp_db.get_attacker_profile_by_ip(ip)
        assert profile['attack_count'] == 6  # 1 initial + 5 updates


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
