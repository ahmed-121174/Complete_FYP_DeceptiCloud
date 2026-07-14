"""
Tests for GAN Data Generator — Fixes #26, #27, #28, #29, #31, #32, #33
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

import pytest
import threading
import config

class TestGANGenerator:
    """Test GAN synthetic user generation."""

    @pytest.fixture(autouse=True)
    def setup_factory(self):
        from honeypot.gan_data_generator import SyntheticUserFactory
        self.factory = SyntheticUserFactory(model_name='test_model')
        yield

    def test_gan_prefix_in_all_names(self):
        """#26 — All generated users should have [GAN] prefix in full_name."""
        # Train with minimal data

        seed = [
            ('u1', 'p1', 'e1@test.com', 'User One', 'user', 5000.0),
            ('u2', 'p2', 'e2@test.com', 'User Two', 'user', 8000.0),
            ('u3', 'p3', 'e3@test.com', 'User Three', 'user', 3000.0),
        ]
        self.factory.train(seed, epochs=50, verbose=False)
        users = self.factory.generate_users(20)

        for u in users:
            assert u['full_name'].startswith('[GAN]'), \
                f"User {u['username']} missing [GAN] prefix: {u['full_name']}"

    def test_partial_watermark_ratio(self):
        """#28 — Only ~WATERMARK_RATIO of users should be watermarked."""
        seed = [
            ('u1', 'p1', 'e1@test.com', 'User One', 'user', 5000.0),
            ('u2', 'p2', 'e2@test.com', 'User Two', 'user', 8000.0),
            ('u3', 'p3', 'e3@test.com', 'User Three', 'user', 3000.0),
        ]
        self.factory.train(seed, epochs=50, verbose=False)
        users = self.factory.generate_users(200)  # Large sample for statistical test

        watermarked = sum(
            1 for u in users
            if round(u['balance'] * 100) % 10 == config.GAN_WATERMARK_DECIMAL
        )
        ratio = watermarked / len(users)
        expected = config.GAN_WATERMARK_RATIO
        # Allow ±15% tolerance

        assert abs(ratio - expected) < 0.20, \
            f"Watermark ratio {ratio:.2f} too far from expected {expected:.2f}"

    def test_name_diversity(self):
        """#32 — Generated names should have good diversity (200+ name pool)."""
        seed = [
            ('u1', 'p1', 'e1@test.com', 'User One', 'user', 5000.0),
            ('u2', 'p2', 'e2@test.com', 'User Two', 'user', 8000.0),
            ('u3', 'p3', 'e3@test.com', 'User Three', 'user', 3000.0),
        ]
        self.factory.train(seed, epochs=50, verbose=False)
        users = self.factory.generate_users(100)

        # Check that we have reasonable diversity in names

        first_names = set(u['full_name'].replace('[GAN] ', '').split()[0] for u in users)
        last_names = set(u['full_name'].replace('[GAN] ', '').split()[-1] for u in users)
        assert len(first_names) >= 10, f"Only {len(first_names)} unique first names in 100 users"
        assert len(last_names) >= 10, f"Only {len(last_names)} unique last names in 100 users"

    def test_validation_uses_training_data(self):
        """#27 — validate() should use stored training data when available."""
        seed = [
            ('u1', 'p1', 'e1@test.com', 'User One', 'user', 5000.0),
            ('u2', 'p2', 'e2@test.com', 'User Two', 'user', 8000.0),
        ]
        self.factory.train(seed, epochs=50, verbose=False)

        # After training, _training_data_raw should be set

        assert hasattr(self.factory, '_training_data_raw')
        assert self.factory._training_data_raw is not None

        # validate() should work without seed_data argument

        metrics = self.factory.validate(n_samples=10)
        assert 'error' not in metrics
        assert 'Balance' in metrics
        assert 'watermark_integrity' in metrics

    def test_user_fields_complete(self):
        """All generated users should have required fields."""
        seed = [
            ('u1', 'p1', 'e1@test.com', 'User One', 'user', 5000.0),
        ]
        self.factory.train(seed, epochs=50, verbose=False)
        users = self.factory.generate_users(5)

        required_fields = ['username', 'password', 'email', 'full_name', 'role', 'balance', 'credit_score', 'age']
        for u in users:
            for field in required_fields:
                assert field in u, f"Missing field '{field}' in generated user"

    def test_credit_score_bounds(self):
        """Credit scores must be within 300-850."""
        seed = [
            ('u1', 'p1', 'e1@test.com', 'User One', 'user', 5000.0),
        ]
        self.factory.train(seed, epochs=50, verbose=False)
        users = self.factory.generate_users(50)

        for u in users:
            assert 300 <= u['credit_score'] <= 850, f"Credit score {u['credit_score']} out of bounds"

    def test_age_bounds(self):
        """Ages must be within 18-85."""
        seed = [
            ('u1', 'p1', 'e1@test.com', 'User One', 'user', 5000.0),
        ]
        self.factory.train(seed, epochs=50, verbose=False)
        users = self.factory.generate_users(50)

        for u in users:
            assert 18 <= u['age'] <= 85, f"Age {u['age']} out of bounds"

class TestGANSingleton:
    """#33 — Thread-safe singleton for GAN factory."""

    def test_singleton_returns_same_instance(self):
        from honeypot.gan_data_generator import get_gan_factory
        import honeypot.gan_data_generator as gan_mod
        # Reset singleton

        gan_mod._factory_instance = None

        f1 = get_gan_factory('test')
        f2 = get_gan_factory('test')
        assert f1 is f2

    def test_singleton_thread_safety(self):
        """#33 — Concurrent calls should return the same instance."""
        from honeypot.gan_data_generator import get_gan_factory
        import honeypot.gan_data_generator as gan_mod
        gan_mod._factory_instance = None

        results = []
        errors = []

        def get_factory():
            try:
                results.append(get_gan_factory('thread_test'))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=get_factory) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors in threads: {errors}"
        assert len(results) == 10
        # All should be the same instance

        assert all(r is results[0] for r in results)
