"""
Integration Tests for Proxy and ML API
Tests the integration between routing proxy and ML detection models
"""
import pytest
import requests
import time
import sys
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import ML_API_URL, PROXY_PORT


class TestProxyMLIntegration:
    """Test integration between proxy and ML API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for integration tests"""
        self.ml_api_url = ML_API_URL
        self.proxy_url = f"http://localhost:{PROXY_PORT}"
    
    def test_ml_api_health_check(self):
        """Test ML API health endpoint"""
        try:
            response = requests.get(f"{self.ml_api_url}/api/health", timeout=2)
            if response.status_code == 200:
                data = response.json()
                assert 'status' in data
                assert 'models' in data
        except requests.exceptions.ConnectionError:
            pytest.skip("ML API not running")
    
    def test_web_attack_detection_endpoint(self):
        """Test web attack detection endpoint"""
        try:
            # Create a feature vector (22 features as per FEATURE_ORDER)
            features = [30, 10, 5, 0, 5, 10, 0, 5, 0, 2, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0.1, 0.0, 0.0]
            
            response = requests.post(
                f"{self.ml_api_url}/api/detect/web-attack",
                json={'features': features},
                timeout=2
            )
            
            if response.status_code == 200:
                data = response.json()
                assert 'prediction' in data
                assert 'confidence' in data
                assert 'is_malicious' in data
                assert data['prediction'] in [0, 1]
                assert 0.0 <= data['confidence'] <= 1.0
        except requests.exceptions.ConnectionError:
            pytest.skip("ML API not running")
    
    def test_ddos_detection_endpoint(self):
        """Test DDoS detection endpoint"""
        try:
            # Create sample DDoS features
            features = [0.0] * 30  # DDoS model expects 30 features
            
            response = requests.post(
                f"{self.ml_api_url}/api/detect/ddos",
                json={'features': features},
                timeout=2
            )
            
            if response.status_code == 200:
                data = response.json()
                assert 'prediction' in data
                assert 'confidence' in data
                assert 'action' in data
        except requests.exceptions.ConnectionError:
            pytest.skip("ML API not running")
    
    def test_batch_detection(self):
        """Test batch detection endpoint"""
        try:
            samples = [
                {
                    'type': 'web-attack',
                    'features': [30, 10, 5, 0, 5, 10, 0, 5, 0, 2, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0.1, 0.0, 0.0]
                }
            ]
            
            response = requests.post(
                f"{self.ml_api_url}/api/detect/batch",
                json={'samples': samples},
                timeout=2
            )
            
            if response.status_code == 200:
                data = response.json()
                assert 'results' in data
                assert 'total' in data
                assert len(data['results']) == len(samples)
        except requests.exceptions.ConnectionError:
            pytest.skip("ML API not running")


class TestProxyClassification:
    """Test proxy classification integration"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for proxy tests"""
        self.proxy_url = f"http://localhost:{PROXY_PORT}"
    
    def test_proxy_status_endpoint(self):
        """Test proxy status endpoint"""
        try:
            response = requests.get(f"{self.proxy_url}/proxy/status", timeout=2)
            if response.status_code == 200:
                data = response.json()
                assert 'status' in data
                assert 'current_site' in data
                assert 'known_attackers' in data
        except requests.exceptions.ConnectionError:
            pytest.skip("Proxy not running")
    
    def test_proxy_classify_endpoint(self):
        """Test proxy classification endpoint"""
        try:
            payload = {
                'url': '/search?q=test',
                'user_agent': 'Mozilla/5.0',
                'method': 'GET'
            }
            
            response = requests.post(
                f"{self.proxy_url}/proxy/classify",
                json=payload,
                timeout=2
            )
            
            if response.status_code == 200:
                data = response.json()
                assert 'is_malicious' in data
                assert 'verdict' in data
                assert 'rule_score' in data
                assert 'confidence' in data
        except requests.exceptions.ConnectionError:
            pytest.skip("Proxy not running")
    
    def test_proxy_classify_sqli_attack(self):
        """Test proxy classification of SQLi attack"""
        try:
            payload = {
                'url': "/search?q=1' OR '1'='1",
                'user_agent': 'sqlmap/1.0',
                'method': 'GET'
            }
            
            response = requests.post(
                f"{self.proxy_url}/proxy/classify",
                json=payload,
                timeout=2
            )
            
            if response.status_code == 200:
                data = response.json()
                assert data['is_malicious'] == True
                assert 'SQLi' in data.get('attack_type', '')
                assert data['confidence'] > 0.5
        except requests.exceptions.ConnectionError:
            pytest.skip("Proxy not running")
    
    def test_proxy_classify_xss_attack(self):
        """Test proxy classification of XSS attack"""
        try:
            payload = {
                'url': "/search?q=<script>alert('xss')</script>",
                'user_agent': 'Mozilla/5.0',
                'method': 'GET'
            }
            
            response = requests.post(
                f"{self.proxy_url}/proxy/classify",
                json=payload,
                timeout=2
            )
            
            if response.status_code == 200:
                data = response.json()
                assert data['is_malicious'] == True
                assert 'XSS' in data.get('attack_type', '')
        except requests.exceptions.ConnectionError:
            pytest.skip("Proxy not running")


class TestEndToEndFlow:
    """Test end-to-end request flow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for end-to-end tests"""
        self.proxy_url = f"http://localhost:{PROXY_PORT}"
        self.ml_api_url = ML_API_URL
    
    def test_benign_request_flow(self):
        """Test flow of benign request through system"""
        try:
            # Check both services are running
            ml_health = requests.get(f"{self.ml_api_url}/api/health", timeout=1)
            proxy_status = requests.get(f"{self.proxy_url}/proxy/status", timeout=1)
            
            if ml_health.status_code == 200 and proxy_status.status_code == 200:
                # Classify a benign request
                payload = {
                    'url': '/products',
                    'user_agent': 'Mozilla/5.0',
                    'method': 'GET'
                }
                
                response = requests.post(
                    f"{self.proxy_url}/proxy/classify",
                    json=payload,
                    timeout=2
                )
                
                assert response.status_code == 200
                data = response.json()
                assert 'routed_to' in data
        except requests.exceptions.ConnectionError:
            pytest.skip("Services not running")
    
    def test_malicious_request_flow(self):
        """Test flow of malicious request through system"""
        try:
            # Check both services are running
            ml_health = requests.get(f"{self.ml_api_url}/api/health", timeout=1)
            proxy_status = requests.get(f"{self.proxy_url}/proxy/status", timeout=1)
            
            if ml_health.status_code == 200 and proxy_status.status_code == 200:
                # Classify a malicious request
                payload = {
                    'url': "/admin?id=1' UNION SELECT * FROM users--",
                    'user_agent': 'sqlmap/1.0',
                    'method': 'GET'
                }
                
                response = requests.post(
                    f"{self.proxy_url}/proxy/classify",
                    json=payload,
                    timeout=2
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data['is_malicious'] == True
                assert data['routed_to'] == 'honeypot'
        except requests.exceptions.ConnectionError:
            pytest.skip("Services not running")


class TestDataPersistence:
    """Test data persistence across components"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for persistence tests"""
        self.proxy_url = f"http://localhost:{PROXY_PORT}"
    
    def test_attack_logging(self):
        """Test that attacks are logged"""
        try:
            # Trigger an attack classification
            payload = {
                'url': "/search?q=1' OR 1=1--",
                'user_agent': 'sqlmap/1.0',
                'method': 'GET'
            }
            
            requests.post(
                f"{self.proxy_url}/proxy/classify",
                json=payload,
                timeout=2
            )
            
            # Check if attack was logged
            time.sleep(0.5)  # Give time for logging
            
            response = requests.get(f"{self.proxy_url}/proxy/attacks?limit=10", timeout=2)
            if response.status_code == 200:
                data = response.json()
                assert 'attacks' in data
        except requests.exceptions.ConnectionError:
            pytest.skip("Proxy not running")
    
    def test_attacker_tracking(self):
        """Test that attackers are tracked"""
        try:
            # Check proxy status for attacker tracking
            response = requests.get(f"{self.proxy_url}/proxy/status", timeout=2)
            if response.status_code == 200:
                data = response.json()
                assert 'known_attackers' in data
                assert isinstance(data['known_attackers'], int)
        except requests.exceptions.ConnectionError:
            pytest.skip("Proxy not running")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
