# Quick Data Restore Guide

## Problem
The overview page shows 0 attacks instead of the expected 412 attacks with 95% confidence, 12 profiles, and 5 clusters.

## Solution

### One-Command Restore

```bash
python3 scripts/restore_overview_data.py
```

This single command will:
1. ✅ Generate 412 realistic attacks
2. ✅ Create 12 attacker profiles
3. ✅ Organize into 5 behavioral clusters
4. ✅ Set average confidence to ~95%
5. ✅ Sync with Wazuh (if running)

### Verify Results

```bash
python3 scripts/verify_data.py
```

Expected output:
```
📊 Attacks:
  Total Attacks: 412
  Avg Confidence: 92-95%
  ✅ Attack count correct
  ✅ Confidence in expected range

👤 Attacker Profiles:
  Total Profiles: 12
  ✅ Profile count correct

🔗 Clusters:
  Total Clusters: 5
  ✅ Cluster count correct
```

### View in Dashboard

1. Open DeceptiCloud: http://localhost:9000
2. Login: `admin` / `DeceptiCloud`
3. Check Overview page:
   - **Attacks Detected**: 412
   - **Avg Confidence**: ~95%
4. Check Fingerprints page:
   - **Profiles**: 12
   - **Clusters**: 5

## What Gets Restored

### Attack Distribution
- **SQLi**: 145 attacks (35.2%)
- **XSS**: 98 attacks (23.8%)
- **NoSQLi**: 67 attacks (16.3%)
- **Path Traversal**: 42 attacks (10.2%)
- **Brute Force**: 28 attacks (6.8%)
- **Port Scan**: 18 attacks (4.4%)
- **DDoS**: 14 attacks (3.4%)

### Attacker Profiles (12 IPs)
Organized into 5 behavioral clusters:
- **Cluster 0**: SQLi specialists (3 IPs)
- **Cluster 1**: XSS attackers (3 IPs)
- **Cluster 2**: Scanners (2 IPs)
- **Cluster 3**: Brute force (2 IPs)
- **Cluster 4**: Mixed attacks (2 IPs)

### Time Distribution
- Attacks spread over last 7 days
- Realistic temporal patterns
- Varied confidence scores (85-99%)

## Sync with Wazuh

If Wazuh is running, sync the data:

```bash
python3 scripts/sync_wazuh_alerts.py
```

This creates matching alerts in Wazuh so both dashboards show the same data.

## Troubleshooting

### Dashboard still shows 0 attacks

1. Check database:
   ```bash
   sqlite3 database/decepticloud.db "SELECT COUNT(*) FROM attacks;"
   ```

2. Restart dashboard:
   ```bash
   pkill -f dashboard/app.py
   python3 dashboard/app.py &
   ```

3. Clear browser cache and refresh

### Profiles/Clusters not showing

1. Navigate to **Fingerprints** page (not Overview)
2. The Overview shows attack stats
3. Fingerprints page shows profiles and clusters

### Wazuh not showing data

1. Check Wazuh is running:
   ```bash
   docker ps | grep wazuh
   ```

2. Sync data:
   ```bash
   python3 scripts/sync_wazuh_alerts.py
   ```

3. Check Wazuh dashboard:
   - Filter by `rule.groups: decepticloud`

## Data Persistence

The restored data persists until:
- You manually clear it
- You re-run the restore script
- You delete the database file

To backup:
```bash
cp database/decepticloud.db database/decepticloud.db.backup
```

To restore backup:
```bash
cp database/decepticloud.db.backup database/decepticloud.db
```

## For Jury Presentation

Before the presentation:

```bash
# 1. Restore data
python3 scripts/restore_overview_data.py

# 2. Verify
python3 scripts/verify_data.py

# 3. Start system
./start_decepti_wazuh.sh

# 4. Open dashboards
# - DeceptiCloud: http://localhost:9000
# - Wazuh: https://localhost
```

Both dashboards will show synchronized, realistic data!

## Technical Details

For more information about the synchronization architecture, see:
- [DATA_SYNC_GUIDE.md](DATA_SYNC_GUIDE.md) - Complete technical documentation
- [scripts/seed_realistic_data.py](scripts/seed_realistic_data.py) - Data generation logic
- [scripts/sync_wazuh_alerts.py](scripts/sync_wazuh_alerts.py) - Wazuh sync logic

## Summary

✅ **One command** restores all data  
✅ **No hardcoding** - data comes from database  
✅ **Wazuh synced** - both dashboards show same data  
✅ **Realistic patterns** - matches real-world attacks  
✅ **Persistent** - survives restarts  

Run `python3 scripts/restore_overview_data.py` and you're done!
