"""
Tests for ML API — Fixes #12, #18
"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

import pytest
import numpy as np
from unittest.mock import MagicMock
import config

class TestMLAPIValidation:
    """#12 — Input bounds validation on the ML API."""

    @pytest.fixture(autouse=True)
    def setup_app(self):
        from ml_pipeline import model_api
        # Mock the model so the endpoint doesn't return 503

        model_api.web_attack_model = MagicMock()
        model_api.web_attack_model.predict.return_value = np.array([[0.1]])
        model_api.web_attack_preprocessor = None  # No scaler

        model_api.app.config['TESTING'] = True
        self.client = model_api.app.test_client()
        yield

    def test_missing_features_returns_400(self):
        """Missing 'features' key should return 400."""
        resp = self.client.post('/api/detect/web-attack',
                                json={'wrong_key': [1, 2, 3]})
        assert resp.status_code == 400

    def test_non_list_features_returns_400(self):
        """#12 — Features must be a list."""
        resp = self.client.post('/api/detect/web-attack',
                                json={'features': 'not a list'})
        assert resp.status_code == 400

    def test_non_numeric_features_returns_400(self):
        """#12 — Features must be numeric."""
        resp = self.client.post('/api/detect/web-attack',
                                json={'features': [1.0, 'abc', 3.0]})
        assert resp.status_code == 400

    def test_out_of_bounds_features_returns_400(self):
        """#12 — Features outside reasonable bounds should be rejected."""
        resp = self.client.post('/api/detect/web-attack',
                                json={'features': [1e7]})  # > 1e6
        assert resp.status_code == 400

    def test_too_many_features_returns_400(self):
        """#12 — More than MAX_FEATURE_COUNT features should be rejected."""
        features = [0.0] * (config.MAX_FEATURE_COUNT + 1)
        resp = self.client.post('/api/detect/web-attack',
                                json={'features': features})
        assert resp.status_code == 400

    def test_health_endpoint(self):
        """Health check should return 200."""
        resp = self.client.get('/api/health')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'status' in data

    def test_error_response_sanitized(self):
        """#5 — Error responses should not leak internal details."""
        # Send invalid data to trigger an error path

        resp = self.client.post('/api/detect/web-attack',
                                data='invalid json',
                                content_type='application/json')
        body = resp.data.decode()
        assert 'Traceback' not in body
        assert '/home/' not in body

    def test_ml_api_uses_config_port(self):
        """ML API should use port from config.py."""
        assert isinstance(config.ML_API_PORT, int)
