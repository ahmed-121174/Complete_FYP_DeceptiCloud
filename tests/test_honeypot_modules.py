"""
Tests for honeypot modules — Fixes #3, #7, #9, #11, #14, #25
"""
import sys
import re
import json
import time
import tempfile
import threading
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

import pytest

# BLOCKCHAIN LEDGER TESTS (#7, #11)

class TestBlockchainSingleton:
    """#7 — Thread-safe singleton for AttackLedger."""

    def test_singleton_returns_same_instance(self):
        from honeypot.blockchain_ledger import get_ledger
        import honeypot.blockchain_ledger as bl_mod
        bl_mod._ledger_instance = None

        l1 = get_ledger()
        l2 = get_ledger()
        assert l1 is l2

    def test_singleton_thread_safety(self):
        from honeypot.blockchain_ledger import get_ledger
        import honeypot.blockchain_ledger as bl_mod
        bl_mod._ledger_instance = None

        results = []

        def get_it():
            results.append(get_ledger())

        threads = [threading.Thread(target=get_it) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 10
        assert all(r is results[0] for r in results)

# BEHAVIORAL FINGERPRINT TESTS (#9)

class TestBehavioralFingerprint:
    """#9 — JSON serialization fix (set → list)."""

    def test_fingerprint_db_uses_lists(self):
        """ips_used should be a list, not a set."""
        from honeypot.behavioral_fingerprint import fingerprint_db

        # Create a new entry

        entry = fingerprint_db['test_hash']
        assert isinstance(entry['ips_used'], list), "ips_used should be a list, not a set"

    def test_fingerprint_stats_serializable(self):
        """Stats endpoint data must be JSON-serializable."""
        from honeypot.behavioral_fingerprint import fingerprint_db, process_fingerprint

        # Process a dummy fingerprint

        raw_data = {
            'screen': {'resolution': '1920x1080', 'colorDepth': 24},
            'timezone_offset': -300,
            'language': 'en-US',
            'platform': 'Linux',
            'touch_support': False,
            'canvas_hash': 'abc123',
            'webgl_hash': 'def456',
            'fonts_hash': 'ghi789',
        }
        profile = process_fingerprint(raw_data, '127.0.0.1', 'TestAgent')

        # The stats should be JSON-serializable (no sets)

        bhash = profile['behavioral_hash']
        entry = fingerprint_db[bhash]
        data = {
            'ips_used': entry['ips_used'],
            'cluster_id': entry['cluster_id'],
        }
        # This should NOT raise TypeError

        json.dumps(data)

    def test_cluster_members_are_lists(self):
        """Cluster members should be lists, not sets."""
        from honeypot.behavioral_fingerprint import clusters

        for cid, cdata in clusters.items():
            assert isinstance(cdata['members'], list), \
                f"Cluster {cid} members should be a list"

# CANARY TOKENS TESTS (#14)

class TestCanaryTokens:
    """#14 — Stats reconstruction from log file."""

    def test_canary_stats_structure(self):
        """canary_stats should have the required keys."""
        from honeypot.canary_tokens import canary_stats

        assert 'total_triggers' in canary_stats
        assert 'by_type' in canary_stats
        assert 'recent_alerts' in canary_stats
        assert isinstance(canary_stats['total_triggers'], int)
        assert isinstance(canary_stats['by_type'], dict)
        assert isinstance(canary_stats['recent_alerts'], list)

    def test_reconstruct_function_exists(self):
        """_reconstruct_stats function should exist."""
        from honeypot.canary_tokens import _reconstruct_stats
        assert callable(_reconstruct_stats)

# LLM RESPONSE ENGINE TESTS (#3, #25)

class TestLLMEngine:
    """Tests for LLM response engine fixes."""

    def test_payload_sanitization_truncation(self):
        """#3 — Attacker payloads must be truncated to max length."""
        from honeypot.llm_response_engine import _sanitize_payload

        long_payload = "A" * 500
        sanitized = _sanitize_payload(long_payload, max_len=200)
        assert len(sanitized) <= 200

    def test_payload_sanitization_strips_newlines(self):
        """#3 — Newlines must be stripped from payloads."""
        from honeypot.llm_response_engine import _sanitize_payload

        payload = "line1\nline2\rline3"
        sanitized = _sanitize_payload(payload)
        assert '\n' not in sanitized
        assert '\r' not in sanitized

    def test_payload_sanitization_empty(self):
        """#3 — Empty payload should return '(empty)'."""
        from honeypot.llm_response_engine import _sanitize_payload
        assert _sanitize_payload('') == '(empty)'
        assert _sanitize_payload(None) == '(empty)'

    def test_cache_ttl_defined(self):
        """#25 — Cache should have a TTL."""
        from honeypot.llm_response_engine import _CACHE_TTL
        assert isinstance(_CACHE_TTL, (int, float))
        assert _CACHE_TTL > 0

# CODE QUALITY — NO BARE EXCEPT (#10)

class TestNoBareExcepts:
    """#10 — Verify no bare 'except:' clauses in critical files."""

    @pytest.mark.parametrize("filepath", [
        'proxy/routing_proxy.py',
        'honeypot/llm_response_engine.py',
        'honeypot/blockchain_ledger.py',
        'launch_decepticloud.py',
    ])
    def test_no_bare_except(self, filepath):
        source_path = Path(__file__).parent.parent / filepath
        if not source_path.exists():
            pytest.skip(f"{filepath} not found")
        source = source_path.read_text()
        bare_excepts = re.findall(r'\bexcept\s*:', source)
        assert len(bare_excepts) == 0, \
            f"Found {len(bare_excepts)} bare except: in {filepath}"
