#!/usr/bin/env python3
"""
Quick test script to verify the new dashboard pages work
"""

import requests
import json

BASE_URL = "http://localhost:9000"

def test_login():
    """Test login functionality"""
    print("Testing login...")
    response = requests.post(f"{BASE_URL}/api/login", json={
        "username": "admin",
        "password": "DeceptiCloud"
    })
    
    if response.status_code == 200:
        print("✓ Login successful")
        return response.cookies
    else:
        print(f"✗ Login failed: {response.status_code}")
        return None

def test_attack_history(cookies):
    """Test attack history endpoint"""
    print("\nTesting attack history endpoint...")
    response = requests.get(f"{BASE_URL}/api/attack-history/list?limit=10", cookies=cookies)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Attack history endpoint works")
        print(f"  - Total attacks: {len(data.get('attacks', []))}")
        print(f"  - Pagination: {data.get('pagination', {})}")
    else:
        print(f"✗ Attack history failed: {response.status_code}")

def test_attacker_profiles(cookies):
    """Test attacker profiles endpoint"""
    print("\nTesting attacker profiles endpoint...")
    response = requests.get(f"{BASE_URL}/api/attacker-profiles/list", cookies=cookies)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Attacker profiles endpoint works")
        print(f"  - Total profiles: {data.get('total', 0)}")
        print(f"  - Clusters: {data.get('cluster_count', 0)}")
        print(f"  - Profiles returned: {len(data.get('profiles', []))}")
    else:
        print(f"✗ Attacker profiles failed: {response.status_code}")

def test_export(cookies):
    """Test export functionality"""
    print("\nTesting export endpoints...")
    
    # Test attack history export
    response = requests.get(f"{BASE_URL}/api/attack-history/export?format=csv", cookies=cookies)
    if response.status_code == 200:
        print(f"✓ Attack history CSV export works ({len(response.content)} bytes)")
    else:
        print(f"✗ Attack history export failed: {response.status_code}")
    
    # Test profiles export
    response = requests.get(f"{BASE_URL}/api/attacker-profiles/export?format=csv", cookies=cookies)
    if response.status_code == 200:
        print(f"✓ Attacker profiles CSV export works ({len(response.content)} bytes)")
    else:
        print(f"✗ Attacker profiles export failed: {response.status_code}")

def main():
    print("=" * 60)
    print("DeceptiCloud Dashboard - New Pages Test")
    print("=" * 60)
    
    # Check if dashboard is running
    try:
        response = requests.get(BASE_URL, timeout=2)
        print(f"✓ Dashboard is running at {BASE_URL}")
    except requests.exceptions.RequestException:
        print(f"✗ Dashboard is not running at {BASE_URL}")
        print("  Please start the dashboard first: python3 dashboard/app.py")
        return
    
    # Test login
    cookies = test_login()
    if not cookies:
        print("\n✗ Cannot proceed without login")
        return
    
    # Test new endpoints
    test_attack_history(cookies)
    test_attacker_profiles(cookies)
    test_export(cookies)
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)
    print("\nTo view the new pages:")
    print("1. Open http://localhost:9000 in your browser")
    print("2. Login with: admin / DeceptiCloud")
    print("3. Click 'Attack History' in the sidebar")
    print("4. Click 'Attacker Profiles' in the sidebar")

if __name__ == "__main__":
    main()
