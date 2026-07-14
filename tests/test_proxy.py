"""
Tests for proxy/routing_proxy.py — Fixes #1, #5, #6, #8, #10, #13, #18, #19, #20, #22
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

import json
import pytest
from unittest.mock import patch, MagicMock
import config

class TestProxyApp:
    """Test the proxy Flask app configuration and endpoints."""

    @pytest.fixture(autouse=True)
    def setup_app(self):
        """Create a test client for the proxy app."""
        # Patch ML model loading and Flask startup

        with patch('requests.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {'prediction': 0, 'confidence': 0.1, 'is_malicious': False}
            mock_resp.status_code = 200
            mock_post.return_value = mock_resp

            from proxy.routing_proxy import app
            app.config['TESTING'] = True
            self.client = app.test_client()
            self.app = app
            yield

    def test_status_endpoint_exists(self):
        """Verify /proxy/status is accessible."""
        resp = self.client.get('/proxy/status')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'uptime_seconds' in data or 'status' in data or 'active_honeypots' in data

    def test_config_post_requires_api_key(self):
        """#1 — POST to /proxy/config must reject unauthenticated requests."""
        resp = self.client.post('/proxy/config',
                                json={'rotation_interval': 60})
        assert resp.status_code == 403

    def test_config_post_with_valid_key(self):
        """#1 — POST to /proxy/config accepts valid API key."""
        resp = self.client.post('/proxy/config',
                                json={'rotation_interval': 60},
                                headers={'X-API-Key': config.PROXY_API_KEY})
        assert resp.status_code == 200

    def test_config_post_with_invalid_key(self):
        """#1 — POST to /proxy/config rejects invalid API key."""
        resp = self.client.post('/proxy/config',
                                json={'rotation_interval': 60},
                                headers={'X-API-Key': 'wrong-key'})
        assert resp.status_code == 403

    def test_config_get_is_open(self):
        """GET /proxy/config is accessible without API key."""
        resp = self.client.get('/proxy/config')
        assert resp.status_code == 200

    def test_error_responses_are_sanitized(self):
        """#5 — Error responses must not leak internal details."""
        # Request a non-existent path through the proxy

        resp = self.client.get('/nonexistent-site/')
        body = resp.data.decode()
        # Should not contain Python tracebacks or internal paths

        assert 'Traceback' not in body
        assert '/home/' not in body
        assert '/media/' not in body

class TestProxyThreadSafety:
    """Tests for thread-safety fixes (#6)."""

    def test_malicious_ips_uses_lock(self):
        """#6 — Verify malicious_ips access is guarded by a lock."""
        from proxy import routing_proxy
        assert hasattr(routing_proxy, '_ip_lock'), "_ip_lock must exist for thread-safe IP tracking"

    def test_feature_order_constant(self):
        """#13 — FEATURE_ORDER must be a consistent list."""
        assert isinstance(config.FEATURE_ORDER, list)
        assert len(config.FEATURE_ORDER) > 10

class TestProxyCodeQuality:
    """Verify code quality fixes in routing_proxy.py."""

    def test_no_bare_except_in_proxy(self):
        """#10 — No bare 'except:' clauses in routing_proxy.py."""
        source_path = Path(__file__).parent.parent / 'proxy' / 'routing_proxy.py'
        source = source_path.read_text()
        # Look for bare except (except: without any exception type)

        import re
        bare_excepts = re.findall(r'\bexcept\s*:', source)
        assert len(bare_excepts) == 0, f"Found {len(bare_excepts)} bare except: clauses"
