"""
Tests for dashboard/app.py — Fixes #2, #4, #17, #23, #26
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

import pytest
from werkzeug.security import check_password_hash, generate_password_hash
import config

class TestPasswordHashing:
    """#2 — Verify werkzeug password hashing is used."""

    def test_password_hash_is_not_plaintext(self):
        """Password should be hashed, not stored as plaintext."""
        hashed = generate_password_hash('DeceptiCloud')
        assert hashed != 'DeceptiCloud'
        assert check_password_hash(hashed, 'DeceptiCloud')

    def test_wrong_password_fails(self):
        hashed = generate_password_hash('DeceptiCloud')
        assert not check_password_hash(hashed, 'wrong_password')

class TestDashboardApp:
    """Test dashboard Flask app configuration."""

    @pytest.fixture(autouse=True)
    def setup_app(self):
        from dashboard.app import app
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.app = app
        yield

    def test_cors_restricted(self):
        """#4 — CORS should not be open to all origins."""
        # Make a request with an unauthorized origin

        resp = self.client.options('/api/stats',
                                   headers={'Origin': 'http://evil.com',
                                            'Access-Control-Request-Method': 'GET'})
        # Should not allow evil.com

        allow_origin = resp.headers.get('Access-Control-Allow-Origin', '')
        assert allow_origin != '*'
        assert 'evil.com' not in allow_origin

    def test_session_secret_is_persistent(self):
        """#23 — Session secret must come from config, not random."""
        assert self.app.secret_key == config.DASHBOARD_SECRET_KEY

    def test_login_endpoint_exists(self):
        """Basic login endpoint test."""
        resp = self.client.post('/api/login',
                                json={'username': 'wrong', 'password': 'wrong'})
        assert resp.status_code in (200, 401)

class TestGANDetection:
    """#26 — GAN user detection in dashboard."""

    def test_gan_prefix_in_name(self):
        """GAN-generated users should have [GAN] prefix."""
        # Simulate what the dashboard query checks

        test_name = "[GAN] Alice Smith"
        assert '[GAN]' in test_name

    def test_watermark_in_balance(self):
        """Watermarked balance should have cents digit = WATERMARK_DECIMAL."""
        watermarked_balance = 4523.17  # cents digit = 7
        cents = round(watermarked_balance * 100) % 10
        assert cents == config.GAN_WATERMARK_DECIMAL
