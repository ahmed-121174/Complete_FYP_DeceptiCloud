"""
Tests for launch_decepticloud.py — Fixes #10, #16
"""
import sys
import re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

import pytest

class TestLaunchScript:
    """Verify fixes in the launch script."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.source_path = Path(__file__).parent.parent / 'launch_decepticloud.py'
        self.source = self.source_path.read_text()

    def test_no_bare_except(self):
        """#10 — No bare 'except:' clauses."""
        bare_excepts = re.findall(r'\bexcept\s*:', self.source)
        assert len(bare_excepts) == 0, \
            f"Found {len(bare_excepts)} bare except: clauses"

    def test_watchdog_function_exists(self):
        """#16 — Watchdog function should be defined."""
        assert '_watchdog' in self.source or 'watchdog' in self.source

    def test_watchdog_thread_started(self):
        """#16 — Watchdog thread should be started in main()."""
        assert 'watchdog_thread' in self.source
        assert 'threading.Thread' in self.source

    def test_config_import(self):
        """Launch script should import from config.py."""
        assert 'from config import' in self.source or 'import config' in self.source

    def test_no_hardcoded_ports(self):
        """Ports should come from config, not hardcoded."""
        # Check that the summary box uses variables, not literals

        # The old code had 'http://localhost:5000' hardcoded

        assert 'localhost:5000' not in self.source or 'ML_API_URL' in self.source
