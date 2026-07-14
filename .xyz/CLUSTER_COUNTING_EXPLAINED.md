# Cluster & Profile Counting - Complete Explanation

## ✅ Current Status (After Fix)

All dashboard pages now show **consistent** data:
- **Overview Page**: 13 profiles, 5 clusters
- **Fingerprints Page**: 13 profiles, 5 clusters  
- **Attacker Profiles Page**: 13 profiles, 5 clusters

---

## 📊 What Are Profiles and Clusters?

### Profiles
**Definition**: One profile = One unique attacker IP address

**Stored in**: `attacker_profiles` table in database

**Counting Method**:
```sql
SELECT COUNT(*) FROM attacker_profiles
```

**What it contains**:
- IP address (unique identifier)
- First seen / Last seen timestamps
- Attack count (number of attacks from this IP)
- Attack types used (SQLi, XSS, etc.)
- User agents
- Behavioral hash
- Threat score
- Cluster assignment (cluster_id)

**Example**:
```
IP: 127.0.0.1     → Profile 1
IP: 192.168.1.5   → Profile 2
IP: 10.0.0.3      → Profile 3
...
Total: 13 profiles (13 unique IPs)
```

---

### Clusters
**Definition**: Groups of profiles with similar attack behavior

**Algorithm**: DBSCAN (Density-Based Spatial Clustering of Applications with Noise)

**Counting Method**:
```sql
SELECT COUNT(DISTINCT cluster_id) 
FROM attacker_profiles 
WHERE cluster_id IS NOT NULL AND cluster_id >= 0
```

**How DBSCAN Works**:
1. Extracts behavioral features from each profile:
   - Attack count
   - Threat score
   - Number of attack types used
   - Number of user agents
   - (More features can be added)

2. Normalizes features to same scale

3. Groups profiles that are "close" in feature space:
   - `eps` parameter: Maximum distance between profiles in same cluster
   - `min_samples` parameter: Minimum profiles needed to form a cluster

4. Assigns cluster IDs:
   - `cluster_id = 0, 1, 2, 3, 4...` for valid clusters
   - `cluster_id = -1` for noise/outliers (not counted)

**Example**:
```
Profile 1 (IP: 127.0.0.1)    → Cluster 1 (high-volume attacker)
Profile 2 (IP: 192.168.1.5)  → Cluster 1 (high-volume attacker)
Profile 3 (IP: 10.0.0.3)     → Cluster 1 (high-volume attacker)
Profile 4 (IP: 172.16.0.1)   → Cluster 2 (scanner)
Profile 5 (IP: 172.16.0.2)   → Cluster 2 (scanner)
Profile 6 (IP: 8.8.8.8)      → Cluster 3 (SQLi specialist)
...
Profile 13 (IP: 1.2.3.4)     → Cluster 5 (mixed attacks)

Total: 13 profiles grouped into 5 behavioral clusters
```

---

## 🔧 How Clustering is Performed

### Endpoint: `/api/attacker-profiles/clustering` (POST)

**Location**: `dashboard/attacker_profiles_api.py`

**Process**:
1. Fetch all profiles from database
2. Extract feature vectors for each profile
3. Normalize features
4. Run DBSCAN clustering algorithm
5. Update database with cluster assignments
6. Return cluster statistics

**Parameters**:
- `eps`: 0.5 (default) - Maximum distance between profiles
- `min_samples`: 2 (default) - Minimum profiles per cluster

**Example Request**:
```bash
curl -X POST http://localhost:9000/api/attacker-profiles/clustering \
  -H "Content-Type: application/json" \
  -d '{"eps": 0.5, "min_samples": 2}'
```

**Example Response**:
```json
{
  "clusters": [
    {"cluster_id": 0, "size": 3},
    {"cluster_id": 1, "size": 5},
    {"cluster_id": 2, "size": 2},
    {"cluster_id": 3, "size": 1},
    {"cluster_id": 4, "size": 2}
  ],
  "total_clusters": 5,
  "noise_points": 0,
  "total_profiles": 13
}
```

---

## 🐛 What Was Wrong (Before Fix)

### Problem 1: Hardcoded Cluster Assignment

**File**: `dashboard/app.py` - `/api/fingerprints` endpoint

**Old Code** (line ~645):
```python
# WRONG: Hardcoded cluster assignment based on attack count
for ip, p in ip_profiles.items():
    cid = 1 if p['attacks'] >= 3 else 0  # Only 2 clusters: 0 or 1
    all_profiles.append({
        'cluster_id': cid,
        ...
    })
    max_clusters = max(max_clusters, cid + 1)  # Always 2
```

**Result**: 
- IPs with 3+ attacks → Cluster 1
- IPs with <3 attacks → Cluster 0
- **Always showed 2 clusters** regardless of actual behavioral similarity

---

### Problem 2: Different Data Sources

**Overview Page** (`/api/phase2-stats`):
- Read from `proxy/logs/proxy_attacks.jsonl` file
- Counted IPs with 3+ attacks as separate clusters
- Result: 12 clusters (12 IPs had 3+ attacks)

**Fingerprints Page** (`/api/fingerprints`):
- Read from same file
- Used hardcoded cluster assignment (0 or 1)
- Result: 2 clusters

**Attacker Profiles Page** (`/api/attacker-profiles/list`):
- Read from database `attacker_profiles` table
- Used DBSCAN cluster_id from database
- Result: 5 clusters (actual behavioral clustering)

---

## ✅ What Was Fixed

### Fix 1: Unified Data Source
All three endpoints now read from the **database** instead of files:

```python
from database.db_service import get_db_service
db = get_db_service()

# Get profiles from database
profiles = db.get_attacker_profiles(limit=1000)

# Get cluster count from database
with db.get_connection() as conn:
    cursor = conn.execute("""
        SELECT COUNT(DISTINCT cluster_id) as count
        FROM attacker_profiles
        WHERE cluster_id IS NOT NULL AND cluster_id >= 0
    """)
    cluster_count = cursor.fetchone()['count']
```

### Fix 2: Removed Hardcoded Logic
Replaced hardcoded cluster assignment with actual database cluster_id:

**Before**:
```python
cid = 1 if p['attacks'] >= 3 else 0  # Hardcoded
```

**After**:
```python
cluster_id = profile.get('cluster_id')  # From database
```

### Fix 3: Added Fallback
If database is unavailable, falls back to file-based logic (but without hardcoded clustering):

```python
except Exception:
    # Fallback to file-based logic
    # But don't assign fake cluster IDs
    cluster_id = None  # Unknown cluster
```

---

## 📈 Data Flow

```
Attack Occurs
    ↓
Proxy Logs to File (proxy_attacks.jsonl)
    ↓
Proxy Creates/Updates Profile in Database
    ↓
Profile Stored with cluster_id = NULL initially
    ↓
Admin Runs Clustering (POST /api/attacker-profiles/clustering)
    ↓
DBSCAN Algorithm Analyzes All Profiles
    ↓
Database Updated with cluster_id (0, 1, 2, 3, 4, -1)
    ↓
Dashboard Reads from Database
    ↓
All Pages Show Consistent Cluster Count
```

---

## 🎯 Key Takeaways

1. **Profiles = Unique IPs**: One profile per attacker IP address
2. **Clusters = Behavioral Groups**: Profiles grouped by attack patterns
3. **DBSCAN Clustering**: Machine learning algorithm groups similar attackers
4. **Database is Source of Truth**: All endpoints now read from database
5. **No Hardcoded Logic**: Cluster IDs come from actual clustering algorithm
6. **Consistent Across Pages**: All dashboard pages show same counts

---

## 🔍 How to Verify

### Check Database Directly
```bash
sqlite3 database/decepticloud.db "
  SELECT 
    COUNT(*) as total_profiles,
    COUNT(DISTINCT cluster_id) as total_clusters
  FROM attacker_profiles 
  WHERE cluster_id >= 0;
"
```

### Check API Endpoints
```bash
# Overview
curl -b cookies.txt http://localhost:9000/api/phase2-stats | jq '.fingerprints'

# Fingerprints
curl -b cookies.txt http://localhost:9000/api/fingerprints | jq '{total, clusters}'

# Attacker Profiles
curl -b cookies.txt http://localhost:9000/api/attacker-profiles/list | jq '{total, cluster_count}'
```

All three should return identical counts.

---

## 📝 Files Modified

1. **dashboard/app.py**
   - Line ~410: `/api/phase2-stats` - Use database cluster count
   - Line ~605: `/api/fingerprints` - Use database profiles and clusters
   - Line ~770: `/api/model-info` - Added placeholder models

---

**Last Updated**: 2026-04-18  
**Status**: ✅ All Issues Fixed
