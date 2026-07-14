#!/usr/bin/env python3
"""
Verify Data Synchronization
Checks that all data is correctly stored and accessible
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_service import get_db_service

def verify_data():
    """Verify all data is correctly stored"""
    print("🔍 Verifying DeceptiCloud Data...")
    print()
    
    db = get_db_service()
    all_good = True
    
    # Check attacks
    print("📊 Attacks:")
    with db.get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) as c FROM attacks WHERE captured=1").fetchone()['c']
        avg_conf = conn.execute(
            "SELECT AVG(confidence) as c FROM attacks WHERE captured=1 AND confidence>=0.85"
        ).fetchone()['c']
        
        print(f"  Total Attacks: {total}")
        print(f"  Avg Confidence: {avg_conf:.2%}")
        
        if total != 412:
            print(f"  ❌ Expected 412 attacks, got {total}")
            all_good = False
        else:
            print(f"  ✅ Attack count correct")
        
        if avg_conf < 0.90 or avg_conf > 0.99:
            print(f"  ⚠ Confidence {avg_conf:.2%} outside expected range (90-99%)")
        else:
            print(f"  ✅ Confidence in expected range")
    
    print()
    
    # Check profiles
    print("👤 Attacker Profiles:")
    profiles = db.get_attacker_profiles(limit=100)
    print(f"  Total Profiles: {len(profiles)}")
    
    if len(profiles) != 12:
        print(f"  ❌ Expected 12 profiles, got {len(profiles)}")
        all_good = False
    else:
        print(f"  ✅ Profile count correct")
    
    print()
    
    # Check clusters
    print("🔗 Clusters:")
    cluster_stats = db.get_cluster_stats()
    print(f"  Total Clusters: {cluster_stats['cluster_count']}")
    
    if cluster_stats['cluster_count'] != 5:
        print(f"  ❌ Expected 5 clusters, got {cluster_stats['cluster_count']}")
        all_good = False
    else:
        print(f"  ✅ Cluster count correct")
    
    # Show cluster distribution
    for cluster in cluster_stats['clusters']:
        print(f"    Cluster {cluster['id']}: {cluster['count']} profiles")
    
    print()
    
    # Check attack distribution
    print("🎯 Attack Type Distribution:")
    stats = db.get_attack_stats()
    for attack_type, count in sorted(stats['by_type'].items(), key=lambda x: x[1], reverse=True):
        pct = (count / stats['total']) * 100
        print(f"  {attack_type:20s}: {count:3d} ({pct:5.1f}%)")
    
    print()
    
    # Check Wazuh alerts
    print("🛡️ Wazuh Integration:")
    with db.get_connection() as conn:
        wazuh_count = conn.execute("SELECT COUNT(*) as c FROM wazuh_alerts").fetchone()['c']
        print(f"  Wazuh Alerts: {wazuh_count}")
        
        if wazuh_count == 0:
            print(f"  ⚠ No Wazuh alerts found. Run: python3 scripts/sync_wazuh_alerts.py")
        elif wazuh_count == total:
            print(f"  ✅ Wazuh alerts synced")
        else:
            print(f"  ⚠ Partial sync: {wazuh_count}/{total} alerts")
    
    print()
    print("=" * 60)
    
    if all_good:
        print("✅ All data verified successfully!")
        print()
        print("🌐 Access dashboards:")
        print("  • DeceptiCloud: http://localhost:9000")
        print("  • Wazuh: https://localhost")
    else:
        print("⚠ Some data issues detected. Re-run:")
        print("  python3 scripts/restore_overview_data.py")
    
    print("=" * 60)
    
    return 0 if all_good else 1

if __name__ == '__main__':
    sys.exit(verify_data())
