"""
Tests for config.py — Central Configuration (#15)
Verifies all required constants are defined and have sane defaults.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

import config

class TestServicePorts:
    """Verify all service ports are configured."""

    def test_ml_api_port(self):
        assert isinstance(config.ML_API_PORT, int)
        assert 1024 <= config.ML_API_PORT <= 65535

    def test_proxy_port(self):
        assert isinstance(config.PROXY_PORT, int)
        assert 1024 <= config.PROXY_PORT <= 65535

    def test_dashboard_port(self):
        assert isinstance(config.DASHBOARD_PORT, int)
        assert 1024 <= config.DASHBOARD_PORT <= 65535

    def test_ports_are_unique(self):
        ports = [config.ML_API_PORT, config.PROXY_PORT, config.DASHBOARD_PORT]
        assert len(set(ports)) == len(ports), "Service ports must be unique"

class TestAuthentication:
    """Verify authentication config is present."""

    def test_dashboard_credentials_exist(self):
        assert config.DASHBOARD_DEFAULT_USERNAME
        assert config.DASHBOARD_DEFAULT_PASSWORD

    def test_proxy_api_key_exists(self):
        assert config.PROXY_API_KEY
        assert len(config.PROXY_API_KEY) >= 10

    def test_dashboard_secret_key_exists(self):
        assert config.DASHBOARD_SECRET_KEY
        assert len(config.DASHBOARD_SECRET_KEY) >= 10

class TestDetectionThresholds:
    """Verify detection thresholds are in valid ranges (#19)."""

    def test_rule_thresholds(self):
        assert 0.0 <= config.RULE_SCORE_LOW_THRESHOLD <= 1.0
        assert 0.0 <= config.RULE_SCORE_HIGH_THRESHOLD <= 1.0
        assert config.RULE_SCORE_LOW_THRESHOLD <= config.RULE_SCORE_HIGH_THRESHOLD

    def test_ml_confidence_threshold(self):
        assert 0.0 <= config.ML_CONFIDENCE_THRESHOLD <= 1.0

class TestRateLimiting:
    """Verify rate limit strings are present (#18)."""

    def test_rate_limits_defined(self):
        assert 'minute' in config.RATE_LIMIT_DEFAULT or 'second' in config.RATE_LIMIT_DEFAULT
        assert 'minute' in config.RATE_LIMIT_LOGIN or 'second' in config.RATE_LIMIT_LOGIN
        assert 'minute' in config.RATE_LIMIT_ML_API or 'second' in config.RATE_LIMIT_ML_API

class TestFeatureOrder:
    """Verify ML feature order constant (#13)."""

    def test_feature_order_is_list(self):
        assert isinstance(config.FEATURE_ORDER, list)

    def test_feature_order_not_empty(self):
        assert len(config.FEATURE_ORDER) > 0

    def test_feature_order_no_duplicates(self):
        assert len(set(config.FEATURE_ORDER)) == len(config.FEATURE_ORDER)

class TestGANSettings:
    """Verify GAN configuration values."""

    def test_watermark_decimal(self):
        assert 0 <= config.GAN_WATERMARK_DECIMAL <= 9

    def test_watermark_ratio(self):
        assert 0.0 < config.GAN_WATERMARK_RATIO < 1.0

    def test_default_epochs(self):
        assert config.GAN_DEFAULT_EPOCHS >= 100

    def test_mode_collapse_settings(self):
        assert config.GAN_MODE_COLLAPSE_CHECK_INTERVAL > 0
        assert config.GAN_MODE_COLLAPSE_STD_THRESHOLD > 0
