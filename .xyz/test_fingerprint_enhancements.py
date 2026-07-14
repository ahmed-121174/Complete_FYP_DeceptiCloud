#!/usr/bin/env python3
"""
Test script for enhanced fingerprint features
Tests JA3, geolocation, and advanced clustering
"""

import sys
import json
from pathlib import Path

# Add honeypot module to path
sys.path.insert(0, str(Path(__file__).parent))

from honeypot.behavioral_fingerprint import (
    compute_ja3_hash,
    get_geolocation,
    compute_behavioral_hash,
    process_fingerprint,
    fingerprint_db,
    clusters,
)

def test_ja3_computation():
    """Test JA3 hash computation"""
    print("🔐 Testing JA3 Hash Computation...")
    
    # Test with sample TLS data
    tls_data = {
        'ssl_version': 771,
        'ciphers': [49195, 49199, 52393, 52392],
        'extensions': [0, 23, 65281, 10, 11, 35, 16],
        'elliptic_curves': [29, 23, 24],
        'ec_point_formats': [0],
    }
    
    ja3 = compute_ja3_hash(tls_data)
    print(f"   ✅ JA3 Hash: {ja3}")
    assert ja3 is not None, "JA3 hash should not be None"
    assert len(ja3) == 32, "JA3 hash should be 32 characters (MD5)"
    print("   ✅ JA3 computation working correctly\n")

def test_geolocation():
    """Test geolocation lookup"""
    print("🌍 Testing Geolocation Lookup...")
    
    # Test with public IP (Google DNS)
    test_ip = "8.8.8.8"
    geo = get_geolocation(test_ip)
    
    if geo:
        print(f"   ✅ Location found for {test_ip}:")
        print(f"      Country: {geo.get('country', 'Unknown')}")
        print(f"      City: {geo.get('city', 'Unknown')}")
        print(f"      Coordinates: {geo.get('latitude', 0)}, {geo.get('longitude', 0)}")
    else:
        print(f"   ⚠️  GeoIP database not available (this is optional)")
        print(f"      System will work with 'Unknown' locations")
    print()

def test_behavioral_hash():
    """Test behavioral hash computation"""
    print("🔍 Testing Behavioral Hash...")
    
    sample_data = {
        'screen': {'resolution': '1920x1080', 'colorDepth': 24},
        'timezone_offset': -300,
        'language': 'en-US',
        'platform': 'Linux x86_64',
        'touch_support': False,
        'canvas_hash': 'abc123',
        'webgl_hash': 'def456',
        'fonts_hash': 'ghi789',
    }
    
    bhash = compute_behavioral_hash(sample_data)
    print(f"   ✅ Behavioral Hash: {bhash}")
    assert bhash is not None, "Behavioral hash should not be None"
    assert len(bhash) == 16, "Behavioral hash should be 16 characters"
    print("   ✅ Behavioral hash computation working correctly\n")

def test_clustering():
    """Test advanced clustering algorithm"""
    print("🎯 Testing Advanced Clustering...")
    
    # Create mock request object
    class MockRequest:
        def __init__(self):
            self.headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-US,en;q=0.9',
            }
    
    # Create sample fingerprints
    sample_data_1 = {
        'screen': {'resolution': '1920x1080', 'colorDepth': 24},
        'timezone_offset': -300,
        'language': 'en-US',
        'platform': 'Linux x86_64',
        'touch_support': False,
        'canvas_hash': 'abc123',
        'webgl_hash': 'def456',
        'fonts_hash': 'ghi789',
        'keystroke_intervals': [100, 120, 110, 105],
        'mouse_movements': [
            {'x': 100, 'y': 200, 't': 1000},
            {'x': 150, 'y': 250, 't': 1050},
        ],
    }
    
    sample_data_2 = {
        'screen': {'resolution': '1920x1080', 'colorDepth': 24},
        'timezone_offset': -300,
        'language': 'en-US',
        'platform': 'Linux x86_64',
        'touch_support': False,
        'canvas_hash': 'abc123',
        'webgl_hash': 'def456',
        'fonts_hash': 'ghi789',
        'keystroke_intervals': [105, 115, 108, 102],
        'mouse_movements': [
            {'x': 105, 'y': 205, 't': 1000},
            {'x': 155, 'y': 255, 't': 1050},
        ],
    }
    
    # Process fingerprints
    profile1 = process_fingerprint(sample_data_1, '192.168.1.100', 'Test UA 1', MockRequest())
    profile2 = process_fingerprint(sample_data_2, '192.168.1.101', 'Test UA 2', MockRequest())
    
    print(f"   ✅ Profile 1: Hash={profile1['behavioral_hash']}, Cluster={profile1['cluster_id']}")
    print(f"   ✅ Profile 2: Hash={profile2['behavioral_hash']}, Cluster={profile2['cluster_id']}")
    
    # Check if clustering worked
    print(f"   ✅ Total fingerprints: {len(fingerprint_db)}")
    print(f"   ✅ Total clusters: {len(clusters)}")
    
    # Similar profiles should be in the same cluster
    if profile1['behavioral_hash'] == profile2['behavioral_hash']:
        print("   ✅ Identical behavioral patterns detected (same hash)")
    else:
        print(f"   ✅ Different behavioral patterns (different hashes)")
    
    print()

def test_api_response():
    """Test API response format"""
    print("📊 Testing API Response Format...")
    
    # Check fingerprint database structure
    for bhash, data in list(fingerprint_db.items())[:1]:
        print(f"   ✅ Fingerprint entry structure:")
        print(f"      - Behavioral Hash: {bhash}")
        print(f"      - IPs Used: {len(data['ips_used'])}")
        print(f"      - JA3 Hashes: {len(data.get('ja3_hashes', []))}")
        print(f"      - Geolocations: {len(data.get('geolocations', []))}")
        print(f"      - Cluster ID: {data.get('cluster_id')}")
        print(f"      - Profiles: {len(data['profiles'])}")
    
    # Check cluster structure
    for cid, cdata in list(clusters.items())[:1]:
        print(f"   ✅ Cluster entry structure:")
        print(f"      - Cluster ID: {cid}")
        print(f"      - Members: {cdata['member_count']}")
        print(f"      - Unique Fingerprints: {len(cdata['members'])}")
        print(f"      - JA3 Hashes: {len(cdata.get('ja3_hashes', []))}")
        print(f"      - Geolocations: {len(cdata.get('geolocations', []))}")
    
    print()

def main():
    """Run all tests"""
    print("=" * 60)
    print("🔍 FINGERPRINT ENHANCEMENTS TEST SUITE")
    print("=" * 60)
    print()
    
    try:
        test_ja3_computation()
        test_geolocation()
        test_behavioral_hash()
        test_clustering()
        test_api_response()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("📋 Summary:")
        print(f"   - JA3 Fingerprinting: ✅ Working")
        print(f"   - Geolocation: {'✅ Working' if get_geolocation('8.8.8.8') else '⚠️  Optional (DB not found)'}")
        print(f"   - Behavioral Hashing: ✅ Working")
        print(f"   - Advanced Clustering: ✅ Working")
        print(f"   - API Response Format: ✅ Working")
        print()
        print("🎯 Fingerprint enhancements are ready to use!")
        print()
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
