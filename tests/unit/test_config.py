"""
Unit Tests for Configuration Module
Tests all configuration values and environment variable handling
"""
import pytest
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import config


class TestConfigValues:
    """Test configuration value loading"""
    
    def test_ml_api_port(self):
        """Test ML API port configuration"""
        assert isinstance(config.ML_API_PORT, int)
        assert 1024 <= config.ML_API_PORT <= 65535
    
    def test_proxy_port(self):
        """Test proxy port configuration"""
        assert isinstance(config.PROXY_PORT, int)
        assert 1024 <= config.PROXY_PORT <= 65535
    
    def test_dashboard_port(self):
        """Test dashboard port configuration"""
        assert isinstance(config.DASHBOARD_PORT, int)
        assert 1024 <= config.DASHBOARD_PORT <= 65535
    
    def test_ports_unique(self):
        """Test that all service ports are unique"""
        ports = [config.ML_API_PORT, config.PROXY_PORT, config.DASHBOARD_PORT]
        assert len(ports) == len(set(ports)), "Service ports must be unique"
    
    def test_site_types(self):
        """Test site types configuration"""
        assert isinstance(config.SITE_TYPES, list)
        assert len(config.SITE_TYPES) == 7
        expected_sites = ['banking', 'ecommerce', 'healthcare', 'blog', 'api_service', 'corporate', 'admin_panel']
        assert config.SITE_TYPES == expected_sites
    
    def test_honeypot_ports(self):
        """Test honeypot ports configuration"""
        assert isinstance(config.HONEYPOT_PORTS, list)
        assert len(config.HONEYPOT_PORTS) == len(config.SITE_TYPES)
        # All ports should be sequential
        for i, port in enumerate(config.HONEYPOT_PORTS):
            assert port == config.HONEYPOT_SITE_BASE_PORT + i


class TestThresholds:
    """Test detection threshold configurations"""
    
    def test_rule_score_thresholds(self):
        """Test rule-based detection thresholds"""
        assert 0.0 <= config.RULE_SCORE_HIGH_THRESHOLD <= 1.0
        assert 0.0 <= config.RULE_SCORE_LOW_THRESHOLD <= 1.0
        assert config.RULE_SCORE_LOW_THRESHOLD < config.RULE_SCORE_HIGH_THRESHOLD
    
    def test_ml_confidence_threshold(self):
        """Test ML confidence threshold"""
        assert 0.0 <= config.ML_CONFIDENCE_THRESHOLD <= 1.0
    
    def test_gan_settings(self):
        """Test GAN configuration"""
        assert isinstance(config.GAN_WATERMARK_DECIMAL, int)
        assert 0 <= config.GAN_WATERMARK_DECIMAL <= 9
        assert 0.0 <= config.GAN_WATERMARK_RATIO <= 1.0
        assert config.GAN_DEFAULT_EPOCHS > 0


class TestFeatureOrder:
    """Test feature extraction configuration"""
    
    def test_feature_order_exists(self):
        """Test that feature order is defined"""
        assert hasattr(config, 'FEATURE_ORDER')
        assert isinstance(config.FEATURE_ORDER, list)
        assert len(config.FEATURE_ORDER) > 0
    
    def test_feature_order_unique(self):
        """Test that all features are unique"""
        assert len(config.FEATURE_ORDER) == len(set(config.FEATURE_ORDER))
    
    def test_expected_features(self):
        """Test that expected features are present"""
        expected = ['url_length', 'path_length', 'query_length', 'sqli_score', 'xss_score']
        for feat in expected:
            assert feat in config.FEATURE_ORDER


class TestURLs:
    """Test service URL configurations"""
    
    def test_ml_api_url(self):
        """Test ML API URL format"""
        assert config.ML_API_URL.startswith('http')
        assert str(config.ML_API_PORT) in config.ML_API_URL
    
    def test_proxy_url(self):
        """Test proxy URL format"""
        assert config.PROXY_URL.startswith('http')
        assert str(config.PROXY_PORT) in config.PROXY_URL
    
    def test_dashboard_url(self):
        """Test dashboard URL format"""
        assert config.DASHBOARD_URL.startswith('http')
        assert str(config.DASHBOARD_PORT) in config.DASHBOARD_URL


class TestAuthentication:
    """Test authentication configuration"""
    
    def test_dashboard_credentials(self):
        """Test dashboard default credentials exist"""
        assert isinstance(config.DASHBOARD_DEFAULT_USERNAME, str)
        assert len(config.DASHBOARD_DEFAULT_USERNAME) > 0
        assert isinstance(config.DASHBOARD_DEFAULT_PASSWORD, str)
        assert len(config.DASHBOARD_DEFAULT_PASSWORD) > 0
    
    def test_secret_key(self):
        """Test dashboard secret key"""
        assert isinstance(config.DASHBOARD_SECRET_KEY, str)
        assert len(config.DASHBOARD_SECRET_KEY) >= 16
    
    def test_proxy_api_key(self):
        """Test proxy API key"""
        assert isinstance(config.PROXY_API_KEY, str)
        assert len(config.PROXY_API_KEY) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
