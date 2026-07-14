# DeceptiCloud ↔ Wazuh Data Synchronization Guide

## Overview

This guide explains how DeceptiCloud and Wazuh are synchronized to show consistent data across both interfaces.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Flow Architecture                    │
└─────────────────────────────────────────────────────────────┘

    ┌──────────────┐         ┌──────────────┐
    │  Attacks     │────────▶│  Database    │
    │  (Real-time) │         │  (SQLite)    │
    └──────────────┘         └──────┬───────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
            ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
            │   Attacks    │ │   Profiles   │ │  Wazuh       │
            │   Table      │ │   Table      │ │  Alerts      │
            └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
                   │                │                │
                   └────────────────┼────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
            ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
            │ DeceptiCloud │ │   Wazuh      │ │  Adaptive    │
            │  Dashboard   │ │  Dashboard   │ │   Engine     │
            └──────────────┘ └──────────────┘ └──────────────┘
```

## Data Synchronization

### 1. Database as Single Source of Truth

All attack data is stored in the centralized SQLite database (`database/decepticloud.db`):

- **attacks** table: All detected attacks with full details
- **attacker_profiles** table: Behavioral profiles with clustering
- **wazuh_alerts** table: Wazuh alerts synced from attacks

### 2. Real-time Flow

```
Attack Detected → Routing Proxy → ML Classification → Database
                                                          │
                                                          ├─→ DeceptiCloud Dashboard
                                                          ├─→ Wazuh Indexer
                                                          └─→ Adaptive Engine
```

### 3. Wazuh Integration

The system integrates with Wazuh in two ways:

#### A. Outbound: DeceptiCloud → Wazuh
- Attacks are converted to Wazuh alert format
- Indexed to Wazuh OpenSearch (`wazuh-alerts-*` indices)
- Visible in Wazuh dashboard

#### B. Inbound: Wazuh → DeceptiCloud
- Adaptive Engine polls Wazuh API
- Extracts ML features from alerts
- Stores in `training_data` table for continuous learning

## Restored Data Specifications

### Overview Page Stats

| Metric | Value | Source |
|--------|-------|--------|
| Total Attacks | 412 | `SELECT COUNT(*) FROM attacks WHERE captured=1` |
| Avg Confidence | ~95% | `SELECT AVG(confidence) FROM attacks WHERE captured=1 AND confidence>=0.85` |
| Attacker Profiles | 12 | `SELECT COUNT(*) FROM attacker_profiles` |
| Clusters | 5 | `SELECT COUNT(DISTINCT cluster_id) FROM attacker_profiles WHERE cluster_id IS NOT NULL` |

### Attack Distribution

| Attack Type | Count | Percentage |
|-------------|-------|------------|
| SQLi | 145 | 35.2% |
| XSS | 98 | 23.8% |
| NoSQLi | 67 | 16.3% |
| Path Traversal | 42 | 10.2% |
| Brute Force | 28 | 6.8% |
| Port Scan | 18 | 4.4% |
| DDoS | 14 | 3.4% |
| **Total** | **412** | **100%** |

### Cluster Distribution

| Cluster ID | Description | IPs | Attack Types |
|------------|-------------|-----|--------------|
| 0 | SQLi Specialists | 3 | SQLi, NoSQLi |
| 1 | XSS Attackers | 3 | XSS, Path Traversal |
| 2 | Scanners | 2 | Port Scan, DDoS |
| 3 | Brute Force | 2 | Brute Force, Credential Stuffing |
| 4 | Mixed Attacks | 2 | Multiple types |

## Usage

### Quick Restore

Restore all data with one command:

```bash
python3 scripts/restore_overview_data.py
```

This will:
1. Clear existing data
2. Generate 412 realistic attacks
3. Create 12 attacker profiles with 5 clusters
4. Sync all data to Wazuh
5. Verify the results

### Manual Steps

If you prefer to run steps individually:

#### Step 1: Seed Database

```bash
python3 scripts/seed_realistic_data.py
```

Generates:
- 412 attacks with realistic distribution
- 12 attacker profiles
- 5 behavioral clusters
- Proper timestamps (last 7 days)

#### Step 2: Sync to Wazuh

```bash
python3 scripts/sync_wazuh_alerts.py
```

Syncs:
- All attacks → Wazuh alerts
- Proper rule IDs and levels
- Full alert context

### Verification

#### Check DeceptiCloud Dashboard

```bash
# Access dashboard
open http://localhost:9000

# Login: admin / DeceptiCloud
```

Expected Overview stats:
- ✅ Attacks Detected: 412
- ✅ Avg Confidence: ~95%
- ✅ Attacker Profiles: 12 (in Fingerprints page)
- ✅ Clusters: 5 (in Fingerprints page)

#### Check Wazuh Dashboard

```bash
# Access Wazuh
open https://localhost

# Login: admin / SecretPassword1!
```

Navigate to:
1. **Security Events** → Should show 412 DeceptiCloud alerts
2. **Threat Hunting** → Filter by `rule.groups: decepticloud`
3. **Dashboard** → Custom dashboard shows attack distribution

#### Check Database

```bash
sqlite3 database/decepticloud.db

# Check attacks
SELECT COUNT(*) FROM attacks WHERE captured=1;
-- Expected: 412

# Check profiles
SELECT COUNT(*) FROM attacker_profiles;
-- Expected: 12

# Check clusters
SELECT COUNT(DISTINCT cluster_id) FROM attacker_profiles WHERE cluster_id IS NOT NULL;
-- Expected: 5

# Check Wazuh alerts
SELECT COUNT(*) FROM wazuh_alerts;
-- Expected: 412

# Check average confidence
SELECT AVG(confidence) FROM attacks WHERE captured=1 AND confidence>=0.85;
-- Expected: ~0.95
```

## Data Consistency

### Ensuring Sync

The system maintains consistency through:

1. **Single Database**: All components read from same SQLite database
2. **Atomic Writes**: Transactions ensure data integrity
3. **Background Sync**: Adaptive Engine continuously syncs with Wazuh
4. **Idempotent Operations**: Re-running scripts is safe

### Monitoring Sync Status

Check if data is in sync:

```bash
# Compare counts
python3 -c "
from database.db_service import get_db_service
db = get_db_service()
with db.get_connection() as conn:
    attacks = conn.execute('SELECT COUNT(*) as c FROM attacks').fetchone()['c']
    wazuh = conn.execute('SELECT COUNT(*) as c FROM wazuh_alerts').fetchone()['c']
    print(f'Attacks: {attacks}')
    print(f'Wazuh Alerts: {wazuh}')
    print(f'Synced: {attacks == wazuh}')
"
```

## Troubleshooting

### Issue: Dashboard shows 0 attacks

**Solution:**
```bash
# Re-seed database
python3 scripts/seed_realistic_data.py

# Restart dashboard
pkill -f dashboard/app.py
python3 dashboard/app.py &
```

### Issue: Wazuh shows no DeceptiCloud alerts

**Solution:**
```bash
# Check Wazuh is running
docker ps | grep wazuh

# Re-sync to Wazuh
python3 scripts/sync_wazuh_alerts.py

# Check Wazuh indexer
curl -k -u admin:SecretPassword1! \
  'https://localhost:9200/wazuh-alerts-*/_count?q=rule.groups:decepticloud'
```

### Issue: Profiles/Clusters count is wrong

**Solution:**
```bash
# Verify database
sqlite3 database/decepticloud.db "
SELECT 
  COUNT(*) as profiles,
  COUNT(DISTINCT cluster_id) as clusters
FROM attacker_profiles
WHERE cluster_id IS NOT NULL;
"

# If wrong, re-seed
python3 scripts/restore_overview_data.py
```

### Issue: Confidence is not ~95%

**Solution:**
```bash
# Check confidence distribution
sqlite3 database/decepticloud.db "
SELECT 
  AVG(confidence) as avg_conf,
  MIN(confidence) as min_conf,
  MAX(confidence) as max_conf
FROM attacks
WHERE captured=1 AND confidence>=0.85;
"

# Should show avg ~0.95
```

## API Endpoints

### Get Overview Stats

```bash
curl http://localhost:9000/api/stats
```

Returns:
```json
{
  "total_attacks": 412,
  "avg_confidence": 0.95,
  "attack_types": {...},
  "top_ips": [...]
}
```

### Get Phase 2 Stats

```bash
curl http://localhost:9000/api/phase2-stats
```

Returns:
```json
{
  "fingerprints": {
    "total": 12,
    "clusters": 5
  }
}
```

### Get Attacker Profiles

```bash
curl http://localhost:9000/api/attacker-profiles
```

Returns all 12 profiles with cluster assignments.

## Continuous Operation

### Real-time Sync

When the system is running normally:

1. **Routing Proxy** detects attacks → Database
2. **Dashboard** reads from Database → Shows real-time stats
3. **Adaptive Engine** polls Wazuh → Ingests new alerts
4. **Wazuh Consumer** extracts features → Training data

### Maintaining Data

The seeded data persists until:
- Database is cleared manually
- Scripts are re-run
- System is reset

To preserve data:
```bash
# Backup database
cp database/decepticloud.db database/decepticloud.db.backup

# Restore later
cp database/decepticloud.db.backup database/decepticloud.db
```

## Advanced Configuration

### Customize Attack Distribution

Edit `scripts/seed_realistic_data.py`:

```python
# Change attack counts
ATTACK_TYPES = {
    'SQLi': 200,    # Increase SQLi attacks
    'XSS': 150,     # Increase XSS attacks
    # ...
}

# Change number of profiles
ATTACKER_IPS = [
    # Add more IPs for more profiles
]

# Change cluster count
CLUSTERS = {
    # Add more clusters
}
```

### Adjust Confidence Levels

```python
# In generate_attack_data()
confidence = random.uniform(0.90, 0.99)  # Higher confidence
```

### Change Time Range

```python
# In seed_data()
start_time = datetime.now() - timedelta(days=30)  # Last 30 days
```

## Integration with Jury Presentation

The restored data is perfect for demonstrations:

1. **Consistent Numbers**: Both dashboards show same stats
2. **Realistic Distribution**: Attack types match real-world patterns
3. **Behavioral Clustering**: Shows ML capabilities
4. **Time-based Analysis**: Attacks distributed over time

### Demo Script

```bash
# 1. Restore data
python3 scripts/restore_overview_data.py

# 2. Start system
./start_decepti_wazuh.sh

# 3. Show DeceptiCloud dashboard
# - Overview: 412 attacks, 95% confidence
# - Fingerprints: 12 profiles, 5 clusters
# - Attack Analysis: Detailed breakdown

# 4. Show Wazuh dashboard
# - Same 412 alerts
# - Filtered by DeceptiCloud rules
# - Correlated with system events
```

## Conclusion

This synchronization system ensures:
- ✅ **Consistency**: Both dashboards show identical data
- ✅ **Realism**: Attack patterns match real-world scenarios
- ✅ **Persistence**: Data survives restarts
- ✅ **Scalability**: Easy to add more data
- ✅ **Maintainability**: Simple scripts, clear documentation

For questions or issues, refer to the main project documentation or contact the development team.
