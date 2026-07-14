#!/usr/bin/env python3
"""
Test script for new ML models
Tests all 5 new detection endpoints
"""

import requests
import json

ML_API_URL = "http://localhost:5000"

def test_xss_detector():
    """Test XSS detector"""
    print("\n" + "="*60)
    print("TESTING XSS DETECTOR")
    print("="*60)
    
    # Test malicious XSS
    print("\n1. Testing malicious XSS payload...")
    response = requests.post(
        f"{ML_API_URL}/api/detect/xss",
        json={"text": "<script>alert(document.cookie)</script>"}
    )
    result = response.json()
    print(f"   Result: {result['attack_type']}")
    print(f"   Confidence: {result['confidence']:.4f}")
    print(f"   ✓ PASS" if result['is_malicious'] else "   ✗ FAIL")
    
    # Test benign text
    print("\n2. Testing benign text...")
    response = requests.post(
        f"{ML_API_URL}/api/detect/xss",
        json={"text": "Hello, this is a normal message"}
    )
    result = response.json()
    print(f"   Result: {result['attack_type']}")
    print(f"   Confidence: {result['confidence']:.4f}")
    print(f"   ✓ PASS" if not result['is_malicious'] else "   ✗ FAIL")

def test_brute_force_detector():
    """Test brute force detector"""
    print("\n" + "="*60)
    print("TESTING BRUTE FORCE DETECTOR")
    print("="*60)
    
    # Test malicious brute force (high attempts, low time between)
    print("\n1. Testing brute force attack pattern...")
    features = [
        50,      # num_attempts
        0.5,     # avg_time_between_attempts
        0.1,     # min_time_between_attempts
        2.0,     # max_time_between_attempts
        45,      # unique_usernames
        0.02,    # success_rate
        0.1,     # avg_response_time
        1,       # has_brute_force_ua
        60.0,    # attempts_per_minute
        5.0      # password_length_variance
    ]
    response = requests.post(
        f"{ML_API_URL}/api/detect/brute-force",
        json={"features": features}
    )
    result = response.json()
    print(f"   Result: {result['attack_type']}")
    print(f"   Confidence: {result['confidence']:.4f}")
    print(f"   ✓ PASS" if result['is_malicious'] else "   ✗ FAIL")
    
    # Test normal login
    print("\n2. Testing normal login pattern...")
    features = [
        3,       # num_attempts
        30.0,    # avg_time_between_attempts
        15.0,    # min_time_between_attempts
        60.0,    # max_time_between_attempts
        1,       # unique_usernames
        0.67,    # success_rate
        0.3,     # avg_response_time
        0,       # has_brute_force_ua
        2.0,     # attempts_per_minute
        2.0      # password_length_variance
    ]
    response = requests.post(
        f"{ML_API_URL}/api/detect/brute-force",
        json={"features": features}
    )
    result = response.json()
    print(f"   Result: {result['attack_type']}")
    print(f"   Confidence: {result['confidence']:.4f}")
    print(f"   ✓ PASS" if not result['is_malicious'] else "   ✗ FAIL")

def test_port_scan_detector():
    """Test port scan detector"""
    print("\n" + "="*60)
    print("TESTING PORT SCAN DETECTOR")
    print("="*60)
    
    # Test port scan
    print("\n1. Testing port scan pattern...")
    features = [
        50,      # num_ports_accessed
        50,      # unique_ports
        0.05,    # avg_time_between_accesses
        0.01,    # min_time_between_accesses
        0.1,     # max_time_between_accesses
        1.0,     # avg_port_diff (sequential)
        1,       # sequential_pattern
        10.0,    # ports_per_second
        1,       # has_scan_ua
        0.02,    # avg_response_time
        0.2,     # common_ports_ratio
        0.8      # high_port_ratio
    ]
    response = requests.post(
        f"{ML_API_URL}/api/detect/port-scan",
        json={"features": features}
    )
    result = response.json()
    print(f"   Result: {result['attack_type']}")
    print(f"   Confidence: {result['confidence']:.4f}")
    print(f"   ✓ PASS" if result['is_malicious'] else "   ✗ FAIL")
    
    # Test normal access
    print("\n2. Testing normal port access...")
    features = [
        3,       # num_ports_accessed
        3,       # unique_ports
        10.0,    # avg_time_between_accesses
        5.0,     # min_time_between_accesses
        20.0,    # max_time_between_accesses
        100.0,   # avg_port_diff
        0,       # sequential_pattern
        0.1,     # ports_per_second
        0,       # has_scan_ua
        0.2,     # avg_response_time
        1.0,     # common_ports_ratio
        0.0      # high_port_ratio
    ]
    response = requests.post(
        f"{ML_API_URL}/api/detect/port-scan",
        json={"features": features}
    )
    result = response.json()
    print(f"   Result: {result['attack_type']}")
    print(f"   Confidence: {result['confidence']:.4f}")
    print(f"   ✓ PASS" if not result['is_malicious'] else "   ✗ FAIL")

def test_credential_stuffing_detector():
    """Test credential stuffing detector"""
    print("\n" + "="*60)
    print("TESTING CREDENTIAL STUFFING DETECTOR")
    print("="*60)
    
    # Test credential stuffing
    print("\n1. Testing credential stuffing pattern...")
    features = [
        100,     # num_attempts
        0.5,     # avg_time_between_attempts
        0.1,     # min_time_between_attempts
        120.0,   # attempts_per_minute
        10,      # unique_ips
        5,       # unique_user_agents
        80,      # unique_usernames
        0.1,     # ip_rotation_rate
        0.05,    # ua_rotation_rate
        0.8,     # username_rotation_rate
        0.05,    # success_rate
        0.1      # avg_response_time
    ]
    response = requests.post(
        f"{ML_API_URL}/api/detect/credential-stuffing",
        json={"features": features}
    )
    result = response.json()
    print(f"   Result: {result['attack_type']}")
    print(f"   Confidence: {result['confidence']:.4f}")
    print(f"   ✓ PASS" if result['is_malicious'] else "   ✗ FAIL")
    
    # Test normal login
    print("\n2. Testing normal login pattern...")
    features = [
        5,       # num_attempts
        30.0,    # avg_time_between_attempts
        10.0,    # min_time_between_attempts
        2.0,     # attempts_per_minute
        1,       # unique_ips
        1,       # unique_user_agents
        1,       # unique_usernames
        0.2,     # ip_rotation_rate
        0.2,     # ua_rotation_rate
        0.2,     # username_rotation_rate
        0.6,     # success_rate
        0.3      # avg_response_time
    ]
    response = requests.post(
        f"{ML_API_URL}/api/detect/credential-stuffing",
        json={"features": features}
    )
    result = response.json()
    print(f"   Result: {result['attack_type']}")
    print(f"   Confidence: {result['confidence']:.4f}")
    print(f"   ✓ PASS" if not result['is_malicious'] else "   ✗ FAIL")

def test_anomaly_detector():
    """Test anomaly detector"""
    print("\n" + "="*60)
    print("TESTING ANOMALY DETECTOR")
    print("="*60)
    
    # Test anomalous request
    print("\n1. Testing anomalous request...")
    features = [
        0,       # method_is_get
        0,       # method_is_post
        1,       # method_is_unusual
        5000,    # query_length
        50000,   # body_length
        30,      # num_headers
        0,       # has_auth
        404,     # response_code
        0.01,    # response_time
        50,      # num_params
        200,     # special_chars_count
        10,      # path_depth
        200,     # path_length
        1,       # has_suspicious_ua
        50,      # ua_length
        1,       # has_suspicious_path
        1,       # has_traversal
        1,       # response_is_error
        0,       # response_is_redirect
        1,       # fast_response
        0        # slow_response
    ]
    response = requests.post(
        f"{ML_API_URL}/api/detect/anomaly",
        json={"features": features}
    )
    result = response.json()
    print(f"   Result: {result['attack_type']}")
    print(f"   Confidence: {result['confidence']:.4f}")
    print(f"   Anomaly Score: {result['anomaly_score']:.4f}")
    print(f"   ✓ PASS" if result['is_malicious'] else "   ✗ FAIL (expected anomaly)")
    
    # Test normal request
    print("\n2. Testing normal request...")
    features = [
        1,       # method_is_get
        0,       # method_is_post
        0,       # method_is_unusual
        20,      # query_length
        100,     # body_length
        10,      # num_headers
        1,       # has_auth
        200,     # response_code
        0.2,     # response_time
        2,       # num_params
        5,       # special_chars_count
        2,       # path_depth
        30,      # path_length
        0,       # has_suspicious_ua
        100,     # ua_length
        0,       # has_suspicious_path
        0,       # has_traversal
        0,       # response_is_error
        0,       # response_is_redirect
        0,       # fast_response
        0        # slow_response
    ]
    response = requests.post(
        f"{ML_API_URL}/api/detect/anomaly",
        json={"features": features}
    )
    result = response.json()
    print(f"   Result: {result['attack_type']}")
    print(f"   Confidence: {result['confidence']:.4f}")
    print(f"   Anomaly Score: {result['anomaly_score']:.4f}")
    print(f"   ✓ PASS" if not result['is_malicious'] else "   ✗ FAIL (expected normal)")

def main():
    print("\n" + "="*60)
    print("ML MODELS TEST SUITE")
    print("Testing 5 New Detection Models")
    print("="*60)
    
    try:
        # Test health
        print("\nChecking ML API health...")
        response = requests.get(f"{ML_API_URL}/api/health")
        health = response.json()
        print(f"Status: {health['status']}")
        print(f"Models loaded: {sum(health['models'].values())}/7")
        
        # Run tests
        test_xss_detector()
        test_brute_force_detector()
        test_port_scan_detector()
        test_credential_stuffing_detector()
        test_anomaly_detector()
        
        print("\n" + "="*60)
        print("ALL TESTS COMPLETED")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        print("Make sure ML API is running on port 5000")

if __name__ == '__main__':
    main()
