"""
Shared fixtures for DeceptiCloud test suite.
"""
import sys
from pathlib import Path

# Ensure project root is on the path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'websites'))

import pytest

@pytest.fixture
def project_root():
    """Return the absolute path to the project root."""
    return PROJECT_ROOT

@pytest.fixture
def sample_seed_data():
    """Sample user tuples matching the db_seeder format."""
    return [
        ('alice', 'pass1', 'alice@test.com', 'Alice Smith', 'user', 5000.0),
        ('bob', 'pass2', 'bob@test.com', 'Bob Jones', 'admin', 12000.0),
        ('carol', 'pass3', 'carol@test.com', 'Carol Davis', 'user', 800.0),
        ('dave', 'pass4', 'dave@test.com', 'Dave Wilson', 'user', 25000.0),
        ('eve', 'pass5', 'eve@test.com', 'Eve Garcia', 'manager', 3500.0),
    ]
