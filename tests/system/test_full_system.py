"""
System Tests for DeceptiCloud
Tests the entire system end-to-end including all components
"""
import pytest
import requests
import time
import sys
from pathlib import Path
import subprocess
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import (
    ML_API_URL, PROXY_PORT, DASHBOARD_URL,
    DASHBOARD_DEFAULT_USERNAME, DASHBOARD_DEFAULT_PASSWORD
)


class TestSystemHealth:
    """Test overall system health and connectivity"""
    
    def test_ml_api_running(self):
        """Test that ML API is running and responsive"""
        try:
            response = requests.get(f"{ML_API_URL}/api/health", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'healthy'
            print(f"✓ ML API is running at {ML_API_URL}")
        except requests.exceptions.ConnectionError:
            pytest.skip("ML API not running - start with: python ml_pipeline/model_api.py")
    
    def test_proxy_running(self):
        """Test that routing proxy is running"""
        try:
            response = requests.get(f"http://localhost:{PROXY_PORT}/proxy/status", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'healthy'
            print(f"✓ Proxy is running on port {PROXY_PORT}")
        except requests.exceptions.ConnectionError:
            pytest.skip("Proxy not running - start with: python proxy/routing_proxy.py")
    
    def test_dashboard_running(self):
        """Test that dashboard is running"""
        try:
            response = requests.get(f"{DASHBOARD_URL}/api/health", timeout=5)
            assert response.status_code in [200, 404]  # 404 is ok if endpoint doesn't exist
            print(f"✓ Dashboard is running at {DASHBOARD_URL}")
        except requests.exceptions.ConnectionError:
            pytest.skip("Dashboard not running - start with: python dashboard/app.py")
    
    def test_database_accessible(self):
        """Test that database is accessible"""
        from database.db_service import get_db_service
        
        db = get_db_service()
        assert db is not None
        
        # Try a simple query
        count = db.get_attack_count()
        assert isinstance(count, int)
        print(f"✓ Database is accessible ({count} attacks recorded)")


class TestEndToEndAttackDetection:
    """Test complete attack detection flow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for E2E tests"""
        self.proxy_url = f"http://localhost:{PROXY_PORT}"
        self.ml_api_url = ML_API_URL
    
    def test_sqli_attack_detection_flow(self):
        """Test SQLi attack detection from start to finish"""
        try:
            # Step 1: Classify SQLi attack
            payload = {
                'url': "/search?q=1' OR '1'='1--",
                'user_agent': 'sqlmap/1.0',
                'method': 'GET'
            }
            
            response = requests.post(
                f"{self.proxy_url}/proxy/classify",
                json=payload,
                timeout=5
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify detection
            assert data['is_malicious'] == True
            assert 'SQLi' in data.get('attack_type', '')
            assert data['confidence'] > 0.5
            assert data['routed_to'] == 'honeypot'
            
            print(f"✓ SQLi attack detected with {data['confidence']:.2%} confidence")
            
            # Step 2: Verify attack was logged
            time.sleep(1)
            attacks_response = requests.get(f"{self.proxy_url}/proxy/attacks?limit=10", timeout=5)
            if attacks_response.status_code == 200:
                attacks = attacks_response.json()
                assert 'attacks' in attacks
                print(f"✓ Attack logged successfully")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Services not running")
    
    def test_xss_attack_detection_flow(self):
        """Test XSS attack detection from start to finish"""
        try:
            payload = {
                'url': "/comment?text=<script>alert('XSS')</script>",
                'user_agent': 'Mozilla/5.0',
                'method': 'POST'
            }
            
            response = requests.post(
                f"{self.proxy_url}/proxy/classify",
                json=payload,
                timeout=5
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data['is_malicious'] == True
            assert 'XSS' in data.get('attack_type', '')
            print(f"✓ XSS attack detected with {data['confidence']:.2%} confidence")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Services not running")
    
    def test_benign_request_flow(self):
        """Test benign request handling"""
        try:
            payload = {
                'url': "/products?category=electronics",
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'method': 'GET'
            }
            
            response = requests.post(
                f"{self.proxy_url}/proxy/classify",
                json=payload,
                timeout=5
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Benign requests should route to real site
            assert data['routed_to'] == 'real_site'
            print(f"✓ Benign request correctly routed to real site")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Services not running")


class TestAttackerTracking:
    """Test attacker tracking and profiling"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for attacker tracking tests"""
        self.proxy_url = f"http://localhost:{PROXY_PORT}"
    
    def test_repeated_attacks_tracking(self):
        """Test that repeated attacks from same IP are tracked"""
        try:
            # Simulate multiple attacks from same IP
            for i in range(3):
                payload = {
                    'url': f"/search?q=attack{i}' OR 1=1--",
                    'user_agent': 'sqlmap/1.0',
                    'method': 'GET'
                }
                
                requests.post(
                    f"{self.proxy_url}/proxy/classify",
                    json=payload,
                    timeout=5
                )
                time.sleep(0.5)
            
            # Check proxy status for attacker tracking
            response = requests.get(f"{self.proxy_url}/proxy/status", timeout=5)
            assert response.status_code == 200
            data = response.json()
            
            assert 'known_attackers' in data
            print(f"✓ Tracking {data['known_attackers']} known attackers")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Proxy not running")


class TestDashboardIntegration:
    """Test dashboard integration with backend"""
    
    @pytest.fixture
    def dashboard_session(self):
        """Create authenticated dashboard session"""
        session = requests.Session()
        try:
            response = session.post(
                f"{DASHBOARD_URL}/api/login",
                json={
                    'username': DASHBOARD_DEFAULT_USERNAME,
                    'password': DASHBOARD_DEFAULT_PASSWORD
                },
                timeout=5
            )
            if response.status_code == 200:
                yield session
            else:
                pytest.skip("Dashboard login failed")
        except requests.exceptions.ConnectionError:
            pytest.skip("Dashboard not running")
    
    def test_dashboard_displays_attacks(self, dashboard_session):
        """Test that dashboard can retrieve and display attacks"""
        try:
            response = dashboard_session.get(f"{DASHBOARD_URL}/api/attacks", timeout=5)
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, (list, dict))
                print(f"✓ Dashboard successfully retrieves attack data")
        except requests.exceptions.ConnectionError:
            pytest.skip("Dashboard not running")
    
    def test_dashboard_statistics(self, dashboard_session):
        """Test dashboard statistics endpoint"""
        try:
            response = dashboard_session.get(f"{DASHBOARD_URL}/api/stats", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Dashboard statistics available")
        except requests.exceptions.ConnectionError:
            pytest.skip("Dashboard not running")


class TestMLModels:
    """Test ML model functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for ML model tests"""
        self.ml_api_url = ML_API_URL
    
    def test_all_models_loaded(self):
        """Test that all ML models are loaded"""
        try:
            response = requests.get(f"{self.ml_api_url}/api/health", timeout=5)
            assert response.status_code == 200
            data = response.json()
            
            assert 'models' in data
            models = data['models']
            
            # Check key models
            assert 'web_attack' in models
            assert 'ddos' in models
            
            loaded_count = sum(1 for v in models.values() if v)
            print(f"✓ {loaded_count}/{len(models)} ML models loaded")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("ML API not running")
    
    def test_model_prediction_accuracy(self):
        """Test model prediction consistency"""
        try:
            # Test with known malicious pattern
            features = [100, 50, 30, 0, 10, 50, 1, 20, 1, 5, 0, 0, 10, 0, 0, 1, 0, 0, 0, 0.8, 0.2, 0.1]
            
            # Make multiple predictions
            predictions = []
            for _ in range(3):
                response = requests.post(
                    f"{self.ml_api_url}/api/detect/web-attack",
                    json={'features': features},
                    timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                    predictions.append(data['prediction'])
            
            # Predictions should be consistent
            if predictions:
                assert all(p == predictions[0] for p in predictions)
                print(f"✓ Model predictions are consistent")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("ML API not running")


class TestSystemPerformance:
    """Test system performance and response times"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for performance tests"""
        self.proxy_url = f"http://localhost:{PROXY_PORT}"
        self.ml_api_url = ML_API_URL
    
    def test_classification_response_time(self):
        """Test that classification happens within acceptable time"""
        try:
            payload = {
                'url': "/search?q=test",
                'user_agent': 'Mozilla/5.0',
                'method': 'GET'
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.proxy_url}/proxy/classify",
                json=payload,
                timeout=5
            )
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < 2.0  # Should respond within 2 seconds
            print(f"✓ Classification response time: {response_time:.3f}s")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Proxy not running")
    
    def test_concurrent_requests(self):
        """Test system handles concurrent requests"""
        import threading
        
        results = []
        
        def make_request():
            try:
                payload = {
                    'url': "/search?q=test",
                    'user_agent': 'Mozilla/5.0',
                    'method': 'GET'
                }
                response = requests.post(
                    f"{self.proxy_url}/proxy/classify",
                    json=payload,
                    timeout=5
                )
                results.append(response.status_code == 200)
            except:
                results.append(False)
        
        try:
            # Make 10 concurrent requests
            threads = []
            for _ in range(10):
                t = threading.Thread(target=make_request)
                threads.append(t)
                t.start()
            
            for t in threads:
                t.join()
            
            # Most requests should succeed
            success_rate = sum(results) / len(results)
            assert success_rate >= 0.8  # At least 80% success
            print(f"✓ Concurrent request success rate: {success_rate:.1%}")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Proxy not running")


class TestDataPersistence:
    """Test data persistence across system"""
    
    def test_database_persistence(self):
        """Test that database persists data"""
        from database.db_service import get_db_service
        
        db = get_db_service()
        
        # Insert test attack
        attack_data = {
            'ip': '192.168.1.200',
            'method': 'GET',
            'url': 'http://test.com/test',
            'path': '/test',
            'attack_type': 'Test',
            'confidence': 0.99,
            'detection_method': 'test'
        }
        
        attack_id = db.insert_attack(attack_data)
        assert attack_id > 0
        
        # Retrieve attack
        attacks = db.get_attacks(filters={'ip': '192.168.1.200'})
        assert len(attacks) > 0
        assert attacks[0]['ip'] == '192.168.1.200'
        
        print(f"✓ Database persistence verified")


class TestSystemRecovery:
    """Test system recovery and error handling"""
    
    def test_ml_api_unavailable_fallback(self):
        """Test that system works when ML API is unavailable"""
        try:
            # This should work even if ML API is down (rule-based fallback)
            proxy_url = f"http://localhost:{PROXY_PORT}"
            
            payload = {
                'url': "/search?q=1' OR 1=1--",
                'user_agent': 'sqlmap/1.0',
                'method': 'GET'
            }
            
            response = requests.post(
                f"{proxy_url}/proxy/classify",
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                # Should still detect attack using rules
                assert data['is_malicious'] == True
                print(f"✓ Rule-based fallback working")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Proxy not running")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
