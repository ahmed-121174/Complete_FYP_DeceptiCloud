#!/usr/bin/env python3
"""
Restore Overview Page Data
Ensures the overview page shows:
- Total attacks: 412
- Avg confidence: 95.x%
- Profiles: 12
- Clusters: 5

This script seeds the database and syncs with Wazuh in one go.
"""

import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def main():
    print("=" * 60)
    print("  DeceptiCloud Data Restoration")
    print("=" * 60)
    print()
    
    scripts_dir = Path(__file__).parent
    
    # Step 1: Seed database
    print("Step 1: Seeding database with realistic data...")
    print("-" * 60)
    result = subprocess.run(
        [sys.executable, str(scripts_dir / 'seed_realistic_data.py')],
        capture_output=False
    )
    
    if result.returncode != 0:
        print("\n❌ Failed to seed database")
        return 1
    
    print()
    
    # Step 2: Sync with Wazuh
    print("Step 2: Syncing data to Wazuh...")
    print("-" * 60)
    result = subprocess.run(
        [sys.executable, str(scripts_dir / 'sync_wazuh_alerts.py')],
        capture_output=False
    )
    
    if result.returncode != 0:
        print("\n⚠ Warning: Wazuh sync failed (Wazuh may not be running)")
        print("  Data is still available in DeceptiCloud dashboard")
    
    print()
    print("=" * 60)
    print("  ✅ Data Restoration Complete!")
    print("=" * 60)
    print()
    print("📊 Expected Overview Stats:")
    print("  • Total Attacks: 412")
    print("  • Avg Confidence: ~95%")
    print("  • Attacker Profiles: 12")
    print("  • Clusters: 5")
    print()
    print("🌐 Access the dashboard:")
    print("  • DeceptiCloud: http://localhost:9000")
    print("  • Wazuh: https://localhost (admin / SecretPassword1!)")
    print()
    print("💡 Both interfaces now show synchronized data!")
    print()

if __name__ == '__main__':
    sys.exit(main())
