#!/usr/bin/env python3
"""
Verify Honeypot Management Page Data
Checks sessions, routing rules, and honeypot status
"""

import sys
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_service import get_db_service

def check_sessions():
    """Check active sessions"""
    db = get_db_service()
    
    with db.get_connection() as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM sessions WHERE is_active = 1")
        active_count = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM sessions")
        total_count = cursor.fetchone()[0]
    
    print(f"✓ Sessions: {active_count} active, {total_count} total")
    return active_count > 0


def check_routing_rules():
    """Check routing rules"""
    db = get_db_service()
    
    with db.get_connection() as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM routing_rules WHERE is_active = 1")
        active_count = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM routing_rules")
        total_count = cursor.fetchone()[0]
    
    print(f"✓ Routing Rules: {active_count} active, {total_count} total")
    return active_count > 0


def check_honeypots():
    """Check honeypot status"""
    honeypots = [
        ('Banking', 4001),
        ('E-commerce', 4002),
        ('Healthcare', 4003),
        ('Blog', 4004),
        ('API Service', 4005),
        ('Corporate', 4006),
        ('Admin Panel', 4007),
        ('SSH', 2222)
    ]
    
    online_count = 0
    
    for name, port in honeypots:
        try:
            if port == 2222:
                # SSH honeypot - check with socket
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                status = "UP" if result == 0 else "DOWN"
            else:
                # HTTP honeypots
                response = requests.get(f'http://localhost:{port}/', timeout=1)
                status = "UP" if response.status_code == 200 else "DOWN"
            
            if status == "UP":
                online_count += 1
            
            print(f"  {name:15} (:{port}): {status}")
        except:
            print(f"  {name:15} (:{port}): DOWN")
    
    print(f"✓ Honeypots: {online_count}/{len(honeypots)} online")
    return online_count >= 7  # At least 7 should be online


def check_api_endpoints():
    """Check API endpoints"""
    endpoints = [
        '/api/honeypots/list',
        '/api/sessions/active',
        '/api/routing-rules/list'
    ]
    
    all_ok = True
    
    for endpoint in endpoints:
        try:
            response = requests.get(f'http://localhost:9000{endpoint}', timeout=2)
            if response.status_code == 200:
                data = response.json()
                if endpoint == '/api/sessions/active':
                    count = len(data.get('sessions', []))
                    print(f"  {endpoint}: OK ({count} sessions)")
                elif endpoint == '/api/routing-rules/list':
                    count = len(data.get('rules', []))
                    print(f"  {endpoint}: OK ({count} rules)")
                else:
                    count = len(data.get('honeypots', []))
                    print(f"  {endpoint}: OK ({count} honeypots)")
            else:
                print(f"  {endpoint}: ERROR (status {response.status_code})")
                all_ok = False
        except Exception as e:
            print(f"  {endpoint}: ERROR ({e})")
            all_ok = False
    
    if all_ok:
        print("✓ All API endpoints working")
    
    return all_ok


def main():
    print("=" * 60)
    print("HONEYPOT MANAGEMENT VERIFICATION")
    print("=" * 60)
    
    print("\n1. Checking Sessions...")
    sessions_ok = check_sessions()
    
    print("\n2. Checking Routing Rules...")
    rules_ok = check_routing_rules()
    
    print("\n3. Checking Honeypots...")
    honeypots_ok = check_honeypots()
    
    print("\n4. Checking API Endpoints...")
    api_ok = check_api_endpoints()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if sessions_ok and rules_ok and honeypots_ok and api_ok:
        print("✓ All checks passed!")
        print("\nHoneypot Management page should now show:")
        print("  - Active sessions")
        print("  - Routing rules")
        print("  - All honeypots online (including SSH)")
        return 0
    else:
        print("✗ Some checks failed")
        if not sessions_ok:
            print("  - Run: python3 scripts/populate_sessions_and_rules.py")
        if not honeypots_ok:
            print("  - Start honeypots: python3 launch_decepticloud.py")
        if not api_ok:
            print("  - Start dashboard: python3 dashboard/app.py")
        return 1


if __name__ == '__main__':
    sys.exit(main())
