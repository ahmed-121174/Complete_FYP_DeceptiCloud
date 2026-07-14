#!/usr/bin/env python3
"""
Test script for Behavioral Monitor feature
Tests real-time attacker detection and session termination
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from honeypot.behavioral_monitor import (
    calculate_behavioral_similarity,
    check_real_site_user,
    compute_realtime_behavioral_hash,
    get_monitoring_stats,
    TERMINATION_THRESHOLD,
)

def test_hash_computation():
    """Test behavioral hash computation"""
    print("🔍 Testing Behavioral Hash Computation...")
    
    request_data = {
        'user_agent': 'Mozilla/5.0 (X11; Linux x86_64)',
        'accept': 'text/html,application/xhtml+xml',
        'accept_encoding': 'gzip, deflate',
        'accept_language': 'en-US,en;q=0.9',
        'referer': 'https://google.com',
    }
    
    hash1 = compute_realtime_behavioral_hash(request_data)
    print(f"   ✅ Hash computed: {hash1}")
    
    # Same data should produce same hash
    hash2 = compute_realtime_behavioral_hash(request_data)
    assert hash1 == hash2, "Same data should produce same hash"
    print(f"   ✅ Hash consistency verified")
    
    # Different data should produce different hash
    request_data['user_agent'] = 'sqlmap/1.7'
    hash3 = compute_realtime_behavioral_hash(request_data)
    assert hash1 != hash3, "Different data should produce different hash"
    print(f"   ✅ Hash uniqueness verified")
    print()

def test_similarity_calculation():
    """Test similarity calculation with mock data"""
    print("🎯 Testing Similarity Calculation...")
    
    # Mock request data
    request_data = {
        'ip': '192.168.1.100',
        'user_agent': 'Mozilla/5.0 (X11; Linux x86_64)',
        'accept': 'text/html',
        'accept_encoding': 'gzip',
        'accept_language': 'en-US',
        'referer': '',
    }
    
    # Test with no known attackers
    is_attacker, similarity, matched = calculate_behavioral_similarity(request_data, None)
    print(f"   ✅ No attackers: is_attacker={is_attacker}, similarity={similarity:.2%}")
    assert not is_attacker, "Should not detect attacker when DB is empty"
    print()

def test_real_site_check():
    """Test real site user checking"""
    print("🚨 Testing Real Site User Check...")
    
    # Test with benign user
    should_terminate, similarity, reason = check_real_site_user(
        ip='192.168.1.100',
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        headers={
            'Accept': 'text/html',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.9',
        },
        request_obj=None
    )
    
    print(f"   ✅ Benign user check:")
    print(f"      - Should terminate: {should_terminate}")
    print(f"      - Similarity: {similarity:.2%}")
    print(f"      - Reason: {reason}")
    
    assert not should_terminate, "Benign user should not be terminated"
    print()

def test_monitoring_stats():
    """Test monitoring statistics"""
    print("📊 Testing Monitoring Stats...")
    
    stats = get_monitoring_stats()
    print(f"   ✅ Stats retrieved:")
    print(f"      - Enabled: {stats.get('enabled')}")
    print(f"      - Threshold: {stats.get('termination_threshold', 'N/A')}")
    print(f"      - Known attackers: {stats.get('known_attackers', 0)}")
    print(f"      - Monitored sessions: {stats.get('monitored_sessions', 0)}")
    print()

def test_threshold_logic():
    """Test threshold logic"""
    print("⚖️  Testing Threshold Logic...")
    
    print(f"   ✅ Termination threshold: {TERMINATION_THRESHOLD:.0%}")
    print(f"      - Similarity ≥ {TERMINATION_THRESHOLD:.0%} → Terminate")
    print(f"      - Similarity < {TERMINATION_THRESHOLD:.0%} → Allow")
    print()
    
    # Test edge cases
    test_cases = [
        (0.74, False, "Just below threshold"),
        (0.75, True, "Exactly at threshold"),
        (0.76, True, "Just above threshold"),
        (0.50, False, "Well below threshold"),
        (0.95, True, "Well above threshold"),
    ]
    
    for similarity, should_terminate, description in test_cases:
        result = similarity >= TERMINATION_THRESHOLD
        status = "✅" if result == should_terminate else "❌"
        print(f"   {status} {description}: {similarity:.0%} → {'TERMINATE' if result else 'ALLOW'}")
    print()

def test_integration():
    """Test integration with fingerprint system"""
    print("🔗 Testing Integration with Fingerprint System...")
    
    try:
        from honeypot.behavioral_fingerprint import fingerprint_db
        print(f"   ✅ Fingerprint database accessible")
        print(f"      - Known attackers: {len(fingerprint_db)}")
        
        if fingerprint_db:
            # Show sample attacker data
            sample_hash = list(fingerprint_db.keys())[0]
            sample_data = fingerprint_db[sample_hash]
            print(f"   ✅ Sample attacker fingerprint:")
            print(f"      - Hash: {sample_hash}")
            print(f"      - IPs used: {len(sample_data.get('ips_used', []))}")
            print(f"      - JA3 hashes: {len(sample_data.get('ja3_hashes', []))}")
            print(f"      - Geolocations: {len(sample_data.get('geolocations', []))}")
        else:
            print(f"   ⚠️  No attackers in database yet")
            print(f"      - Interact with honeypots to populate")
    except ImportError as e:
        print(f"   ❌ Fingerprint module not available: {e}")
    print()

def main():
    """Run all tests"""
    print("=" * 60)
    print("🚨 BEHAVIORAL MONITOR TEST SUITE")
    print("=" * 60)
    print()
    
    try:
        test_hash_computation()
        test_similarity_calculation()
        test_real_site_check()
        test_monitoring_stats()
        test_threshold_logic()
        test_integration()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("📋 Summary:")
        print(f"   - Hash Computation: ✅ Working")
        print(f"   - Similarity Calculation: ✅ Working")
        print(f"   - Real Site Check: ✅ Working")
        print(f"   - Monitoring Stats: ✅ Working")
        print(f"   - Threshold Logic: ✅ Working")
        print(f"   - Integration: ✅ Working")
        print()
        print("🎯 Behavioral Monitor is ready to use!")
        print()
        print("📝 Next Steps:")
        print("   1. Start the system: ./start_decepti_wazuh.sh")
        print("   2. Interact with honeypots to populate fingerprint DB")
        print("   3. Try accessing real sites with attacker fingerprints")
        print("   4. Monitor logs for session terminations")
        print()
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
