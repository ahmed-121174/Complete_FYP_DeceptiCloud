# DeceptiCloud Issues Analysis & Fixes

## Issue #1: Cluster Count Discrepancy (Overview: 12 vs Fingerprints: 2)

### Root Cause
Two different data sources and calculation methods:

**Overview Page** (`/api/phase2-stats`):
- Reads from `proxy/logs/proxy_attacks.jsonl` file
- Counts clusters as: IPs with 3+ attacks = 1 cluster each
- Logic: `fp_clusters = sum(1 for p in ip_profiles.values() if p['attacks'] >= 3)`
- Result: **12 clusters** (12 IPs have 3+ attacks)

**Fingerprints Page** (`/api/attacker-profiles/list`):
- Reads from `attacker_profiles` database table
- Counts DISTINCT cluster_id values from DBSCAN clustering
- Query: `SELECT COUNT(DISTINCT cluster_id) FROM attacker_profiles WHERE cluster_id >= 0`
- Result: **2 clusters** (DBSCAN grouped 12 profiles into 2 behavioral clusters)

### Why This Happens
- **Overview** uses a simple threshold (3+ attacks = cluster)
- **Fingerprints** uses DBSCAN machine learning clustering based on behavioral similarity
- DBSCAN groups similar attackers together → 12 profiles grouped into 2 actual clusters

### Fix Strategy
**Option A (Recommended)**: Make Overview use database cluster count
**Option B**: Update Fingerprints to use same logic as Overview
**Option C**: Show both metrics with labels ("Profiles: 12, Clusters: 2")

---

## Issue #2: ML Models Data Not Showing

### Root Cause
Frontend expects 7 models but backend only returns 2:

**Backend Returns** (`/api/model-info`):
```json
{
  "web_attack": {...},
  "ddos": {...}
}
```

**Frontend Expects**:
```javascript
const wa = data.web_attack || {};
const dd = data.ddos || {};
const xss = data.xss || {};           // ❌ Missing
const bf = data.brute_force || {};    // ❌ Missing
const ps = data.port_scan || {};      // ❌ Missing
const cs = data.credential_stuffing || {}; // ❌ Missing
const an = data.anomaly || {};        // ❌ Missing
```

When models are missing, JavaScript sets them to `{}`, resulting in:
- `(undefined * 100).toFixed(1) + '%'` → `"NaN%"`
- Bar widths: `undefined * 100 + '%'` → `"NaN%"` (invisible bars)

### Why This Happens
The ML API at `http://localhost:5000/api/model-info` only has 2 trained models:
1. Web Attack Detector V2 (SQLi, NoSQLi, XSS combined)
2. DDoS Detector V1

The other 5 models (XSS standalone, Brute Force, Port Scan, Credential Stuffing, Anomaly) were never trained or don't exist.

### Fix Strategy
**Option A**: Return placeholder data for missing models with 0% metrics
**Option B**: Update frontend to only show available models dynamically
**Option C**: Train the missing 5 models

---

## Detailed Fixes

### Fix #1: Unify Cluster Counting

**File**: `dashboard/app.py`

**Change in `/api/phase2-stats`** (line ~430):

```python
# OLD CODE (counts IPs with 3+ attacks as separate clusters)
fp_clusters = sum(1 for p in ip_profiles.values() if p['attacks'] >= 3)

# NEW CODE (use database cluster count)
from database.db_service import get_db_service
db = get_db_service()
with db.get_connection() as conn:
    cursor = conn.execute("""
        SELECT COUNT(DISTINCT cluster_id) as count
        FROM attacker_profiles
        WHERE cluster_id IS NOT NULL AND cluster_id >= 0
    """)
    fp_clusters = cursor.fetchone()['count']
```

---

### Fix #2: Add Placeholder Data for Missing Models

**File**: `dashboard/app.py`

**Add to `/api/model-info`** (after line ~770):

```python
# Add placeholder data for models not yet trained
result['xss'] = {
    'name': 'XSS Detector',
    'architecture': 'Pending Training',
    'input_features': 0,
    'output': 'Binary (Attack/Benign)',
    'attack_types': ['XSS'],
    'accuracy': 0.0,
    'precision': 0.0,
    'recall': 0.0,
    'f1_score': 0.0,
}

result['brute_force'] = {
    'name': 'Brute Force Detector',
    'architecture': 'Pending Training',
    'input_features': 0,
    'output': 'Binary (Attack/Benign)',
    'attack_types': ['Brute Force'],
    'accuracy': 0.0,
    'precision': 0.0,
    'recall': 0.0,
    'f1_score': 0.0,
}

result['port_scan'] = {
    'name': 'Port Scan Detector',
    'architecture': 'Pending Training',
    'input_features': 0,
    'output': 'Binary (Attack/Benign)',
    'attack_types': ['Port Scan'],
    'accuracy': 0.0,
    'precision': 0.0,
    'recall': 0.0,
    'f1_score': 0.0,
}

result['credential_stuffing'] = {
    'name': 'Credential Stuffing Detector',
    'architecture': 'Pending Training',
    'input_features': 0,
    'output': 'Binary (Attack/Benign)',
    'attack_types': ['Credential Stuffing'],
    'accuracy': 0.0,
    'precision': 0.0,
    'recall': 0.0,
    'f1_score': 0.0,
}

result['anomaly'] = {
    'name': 'Anomaly Detector',
    'architecture': 'Pending Training',
    'input_features': 0,
    'output': 'Binary (Attack/Benign)',
    'attack_types': ['Anomaly'],
    'accuracy': 0.0,
    'precision': 0.0,
    'recall': 0.0,
    'f1_score': 0.0,
}
```

---

## Summary

| Issue | Root Cause | Impact | Fix |
|-------|------------|--------|-----|
| Cluster count mismatch | Different data sources (file vs DB) | Confusing metrics | Unify to use DB cluster count |
| ML models not showing | Missing 5 models in backend response | NaN% displayed | Add placeholder data with 0% |

Both fixes are minimal code changes to existing files, no new files needed.
