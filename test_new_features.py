#!/usr/bin/env python3
"""
Test script for new DeceptiCloud features
Tests honeypot enhancements and dashboard APIs
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def test_honeypot_logger():
    """Test enhanced honeypot logger"""
    print("\n" + "="*60)
    print("Testing Enhanced Honeypot Logger")
    print("="*60)
    
    try:
        from honeypot.enhanced_logger import get_honeypot_logger
        
        logger = get_honeypot_logger('banking', 4001)
        
        # Test login attempt
        logger.log_login_attempt(
            ip='192.168.1.100',
            username='admin',
            password='password123',
            success=False,
            user_agent='Mozilla/5.0'
        )
        print("✓ Login attempt logged")
        
        # Test API call
        logger.log_api_call(
            ip='192.168.1.100',
            endpoint='/api/users',
            method='GET',
            user_agent='sqlmap/1.0'
        )
        print("✓ API call logged")
        
        # Test form submit
        logger.log_form_submit(
            ip='192.168.1.100',
            form_data={'username': 'test', 'password': 'secret'},
            user_agent='Mozilla/5.0'
        )
        print("✓ Form submission logged")
        
        print("\n✅ Honeypot Logger: PASSED")
        return True
    
    except Exception as e:
        print(f"\n❌ Honeypot Logger: FAILED - {e}")
        return False


def test_canary_manager():
    """Test canary token manager"""
    print("\n" + "="*60)
    print("Testing Canary Token Manager")
    print("="*60)
    
    try:
        from honeypot.canary_manager import get_canary_manager
        
        manager = get_canary_manager()
        
        # Create tokens
        url_token = manager.create_token('url', 'banking', 'Test URL token')
        print(f"✓ URL token created: {url_token}")
        
        email_token = manager.create_token('email', 'ecommerce', 'Test email token')
        print(f"✓ Email token created: {email_token}")
        
        api_token = manager.create_token('api_key', 'api_service', 'Test API token')
        print(f"✓ API key token created: {api_token}")
        
        # Test trigger
        manager.trigger_token(url_token, '192.168.1.100', 'Mozilla/5.0')
        print("✓ Token trigger recorded")
        
        # Get all tokens
        tokens = manager.get_all_tokens()
        print(f"✓ Total tokens: {len(tokens)}")
        
        # Get triggers
        triggers = manager.get_triggers()
        print(f"✓ Total triggers: {len(triggers)}")
        
        print("\n✅ Canary Manager: PASSED")
        return True
    
    except Exception as e:
        print(f"\n❌ Canary Manager: FAILED - {e}")
        return False


def test_database_integration():
    """Test database integration"""
    print("\n" + "="*60)
    print("Testing Database Integration")
    print("="*60)
    
    try:
        from database.db_service import get_db_service
        
        db = get_db_service()
        
        # Test attack stats
        stats = db.get_attack_stats()
        print(f"✓ Total attacks: {stats['total']}")
        print(f"✓ Attack types: {len(stats['by_type'])}")
        print(f"✓ Unique IPs: {len(stats['top_ips'])}")
        
        # Test attacker profiles
        profiles = db.get_attacker_profiles(limit=10)
        print(f"✓ Attacker profiles: {len(profiles)}")
        
        # Test cluster stats
        cluster_stats = db.get_cluster_stats()
        print(f"✓ Total profiles: {cluster_stats['total_profiles']}")
        print(f"✓ Clusters: {cluster_stats['cluster_count']}")
        
        print("\n✅ Database Integration: PASSED")
        return True
    
    except Exception as e:
        print(f"\n❌ Database Integration: FAILED - {e}")
        return False


def test_attack_history_api():
    """Test attack history API (without Flask app)"""
    print("\n" + "="*60)
    print("Testing Attack History API Logic")
    print("="*60)
    
    try:
        from database.db_service import get_db_service
        
        db = get_db_service()
        
        # Test get attacks with filters
        attacks = db.get_attacks(limit=10)
        print(f"✓ Retrieved {len(attacks)} attacks")
        
        # Test attack count
        count = db.get_attack_count()
        print(f"✓ Total attack count: {count}")
        
        # Test with filters
        if attacks:
            ip = attacks[0]['ip']
            filtered = db.get_attacks(limit=10, filters={'ip': ip})
            print(f"✓ Filtered attacks by IP: {len(filtered)}")
        
        print("\n✅ Attack History API Logic: PASSED")
        return True
    
    except Exception as e:
        print(f"\n❌ Attack History API Logic: FAILED - {e}")
        return False


def test_attacker_profiles_api():
    """Test attacker profiles API (without Flask app)"""
    print("\n" + "="*60)
    print("Testing Attacker Profiles API Logic")
    print("="*60)
    
    try:
        from database.db_service import get_db_service
        
        db = get_db_service()
        
        # Test get profiles
        profiles = db.get_attacker_profiles(limit=10)
        print(f"✓ Retrieved {len(profiles)} profiles")
        
        # Test get profile by IP
        if profiles:
            ip = profiles[0]['ip']
            profile = db.get_attacker_profile_by_ip(ip)
            print(f"✓ Retrieved profile for IP: {ip}")
            print(f"  - Attack count: {profile['attack_count']}")
            print(f"  - Threat score: {profile['threat_score']:.2f}")
        
        # Test cluster stats
        cluster_stats = db.get_cluster_stats()
        print(f"✓ Cluster statistics retrieved")
        print(f"  - Total profiles: {cluster_stats['total_profiles']}")
        print(f"  - Clusters: {cluster_stats['cluster_count']}")
        
        print("\n✅ Attacker Profiles API Logic: PASSED")
        return True
    
    except Exception as e:
        print(f"\n❌ Attacker Profiles API Logic: FAILED - {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("DECEPTICLOUD - NEW FEATURES TEST SUITE")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Database Integration", test_database_integration()))
    results.append(("Honeypot Logger", test_honeypot_logger()))
    results.append(("Canary Manager", test_canary_manager()))
    results.append(("Attack History API", test_attack_history_api()))
    results.append(("Attacker Profiles API", test_attacker_profiles_api()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name:30s} {status}")
    
    print("\n" + "="*60)
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("="*60)
    
    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
