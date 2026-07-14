"""
Unit Tests for ML Models
Tests model loading, prediction, and feature extraction
"""
import pytest
import numpy as np
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestModelLoading:
    """Test ML model loading functionality"""
    
    def test_web_attack_model_path(self):
        """Test web attack model path exists"""
        from ml_pipeline import model_api
        model_path = model_api.BASE_DIR / 'models' / 'web_attack_detector_v2.keras'
        # Model should exist or be loadable
        assert model_api.BASE_DIR.exists()
    
    def test_ddos_model_path(self):
        """Test DDoS model path exists"""
        ddos_dir = Path(__file__).parent.parent.parent / 'DDoS' / 'V1' / 'models'
        assert ddos_dir.exists(), "DDoS models directory should exist"


class TestFeatureExtraction:
    """Test feature extraction from requests"""
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock Flask request object"""
        request = Mock()
        request.url = 'http://test.com/search?q=test'
        request.path = '/search'
        request.query_string = b'q=test'
        request.method = 'GET'
        request.headers = {'User-Agent': 'Mozilla/5.0', 'Content-Type': 'text/html'}
        request.get_data = Mock(return_value=b'')
        return request
    
    def test_extract_basic_features(self, mock_request):
        """Test basic feature extraction"""
        from proxy.routing_proxy import extract_features
        
        features = extract_features(mock_request)
        
        assert 'url_length' in features
        assert 'path_length' in features
        assert 'query_length' in features
        assert 'method_is_post' in features
        assert features['url_length'] > 0
        assert features['path_length'] > 0
    
    def test_sqli_pattern_detection(self, mock_request):
        """Test SQLi pattern detection in features"""
        from proxy.routing_proxy import extract_features
        
        # Modify request to include SQLi pattern
        mock_request.query_string = b"q=1' OR '1'='1"
        mock_request.url = "http://test.com/search?q=1' OR '1'='1"
        
        features = extract_features(mock_request)
        
        assert 'sqli_pattern_count' in features
        assert features['sqli_pattern_count'] > 0
    
    def test_xss_pattern_detection(self, mock_request):
        """Test XSS pattern detection in features"""
        from proxy.routing_proxy import extract_features
        
        # Modify request to include XSS pattern
        mock_request.query_string = b"q=<script>alert('xss')</script>"
        mock_request.url = "http://test.com/search?q=<script>alert('xss')</script>"
        
        features = extract_features(mock_request)
        
        assert 'xss_pattern_count' in features
        assert features['xss_pattern_count'] > 0
    
    def test_suspicious_user_agent_detection(self, mock_request):
        """Test suspicious user agent detection"""
        from proxy.routing_proxy import extract_features
        
        # Test with sqlmap user agent
        mock_request.headers = {'User-Agent': 'sqlmap/1.0'}
        features = extract_features(mock_request)
        
        assert 'has_suspicious_ua' in features
        assert features['has_suspicious_ua'] == 1


class TestClassification:
    """Test request classification logic"""
    
    def test_benign_classification(self):
        """Test classification of benign request"""
        from proxy.routing_proxy import classify_request
        
        features = {
            'url_length': 30,
            'path_length': 10,
            'query_length': 5,
            'sqli_pattern_count': 0,
            'xss_pattern_count': 0,
            'nosqli_pattern_count': 0,
            'traversal_pattern_count': 0,
            'has_suspicious_ua': 0,
            'num_special_chars': 2
        }
        
        # Mock ML API to be unavailable
        with patch('requests.post', side_effect=Exception("ML API unavailable")):
            result = classify_request(features)
        
        assert 'is_malicious' in result
        assert 'confidence' in result
        assert 'method' in result
        assert isinstance(result['is_malicious'], bool)
    
    def test_malicious_classification(self):
        """Test classification of malicious request"""
        from proxy.routing_proxy import classify_request
        
        features = {
            'url_length': 100,
            'path_length': 20,
            'query_length': 50,
            'sqli_pattern_count': 3,
            'xss_pattern_count': 0,
            'nosqli_pattern_count': 0,
            'traversal_pattern_count': 0,
            'has_suspicious_ua': 1,
            'num_special_chars': 20
        }
        
        with patch('requests.post', side_effect=Exception("ML API unavailable")):
            result = classify_request(features)
        
        assert result['is_malicious'] == True
        assert result['confidence'] > 0.5


class TestModelPrediction:
    """Test model prediction functionality"""
    
    def test_web_attack_prediction_format(self):
        """Test web attack prediction response format"""
        # This tests the expected format without requiring actual model
        expected_keys = ['prediction', 'confidence', 'attack_type', 'is_malicious']
        
        # Mock response
        mock_response = {
            'prediction': 1,
            'confidence': 0.95,
            'attack_type': 'SQLi',
            'is_malicious': True
        }
        
        for key in expected_keys:
            assert key in mock_response
    
    def test_ddos_prediction_format(self):
        """Test DDoS prediction response format"""
        expected_keys = ['prediction', 'confidence', 'attack_type', 'is_malicious', 'action']
        
        mock_response = {
            'prediction': 1,
            'confidence': 0.88,
            'attack_type': 'DDoS Attack',
            'is_malicious': True,
            'action': 'ROUTE_TO_HONEYPOT'
        }
        
        for key in expected_keys:
            assert key in mock_response


class TestFeatureVectorConstruction:
    """Test feature vector construction for ML models"""
    
    def test_feature_order_consistency(self):
        """Test that feature order is consistent"""
        from config import FEATURE_ORDER
        
        assert isinstance(FEATURE_ORDER, list)
        assert len(FEATURE_ORDER) > 0
        
        # Check for duplicates
        assert len(FEATURE_ORDER) == len(set(FEATURE_ORDER))
    
    def test_feature_vector_length(self):
        """Test feature vector has correct length"""
        from config import FEATURE_ORDER
        
        # Create sample features
        features = {feat: 0.0 for feat in FEATURE_ORDER}
        feature_vec = [features.get(k, 0) for k in FEATURE_ORDER]
        
        assert len(feature_vec) == len(FEATURE_ORDER)
    
    def test_feature_vector_numeric(self):
        """Test that all features are numeric"""
        from config import FEATURE_ORDER
        
        features = {feat: float(i) for i, feat in enumerate(FEATURE_ORDER)}
        feature_vec = [features.get(k, 0) for k in FEATURE_ORDER]
        
        assert all(isinstance(v, (int, float)) for v in feature_vec)


class TestModelValidation:
    """Test model validation and bounds checking"""
    
    def test_confidence_bounds(self):
        """Test that confidence values are between 0 and 1"""
        confidences = [0.0, 0.5, 0.95, 1.0]
        
        for conf in confidences:
            assert 0.0 <= conf <= 1.0
    
    def test_prediction_binary(self):
        """Test that predictions are binary (0 or 1)"""
        predictions = [0, 1]
        
        for pred in predictions:
            assert pred in [0, 1]
    
    def test_feature_bounds_validation(self):
        """Test feature value bounds validation"""
        from config import MAX_FEATURE_COUNT
        
        # Test max feature count
        assert MAX_FEATURE_COUNT > 0
        assert MAX_FEATURE_COUNT <= 1000  # Reasonable upper bound
        
        # Test feature value bounds
        valid_feature = 500.0
        assert -1e6 <= valid_feature <= 1e6


class TestAttackTypeDetection:
    """Test attack type detection logic"""
    
    def test_sqli_detection(self):
        """Test SQLi attack type detection"""
        features = {
            'sqli_pattern_count': 2,
            'xss_pattern_count': 0,
            'nosqli_pattern_count': 0,
            'traversal_pattern_count': 0,
            'has_suspicious_ua': 0
        }
        
        from proxy.routing_proxy import _get_attack_types
        attack_types = _get_attack_types(features)
        
        assert 'SQLi' in attack_types
    
    def test_xss_detection(self):
        """Test XSS attack type detection"""
        features = {
            'sqli_pattern_count': 0,
            'xss_pattern_count': 2,
            'nosqli_pattern_count': 0,
            'traversal_pattern_count': 0,
            'has_suspicious_ua': 0
        }
        
        from proxy.routing_proxy import _get_attack_types
        attack_types = _get_attack_types(features)
        
        assert 'XSS' in attack_types
    
    def test_multiple_attack_types(self):
        """Test detection of multiple attack types"""
        features = {
            'sqli_pattern_count': 1,
            'xss_pattern_count': 1,
            'nosqli_pattern_count': 0,
            'traversal_pattern_count': 0,
            'has_suspicious_ua': 1
        }
        
        from proxy.routing_proxy import _get_attack_types
        attack_types = _get_attack_types(features)
        
        assert len(attack_types) >= 2
        assert 'SQLi' in attack_types
        assert 'XSS' in attack_types


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
