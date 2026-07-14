# DeceptiCloud Dashboard - Testing Guide

**Date**: April 18, 2026  
**Pages**: Attack History & Attacker Profiles

---

## 🚀 QUICK START

### 1. Start the Dashboard

```bash
# Make sure you're in the project root directory
python3 dashboard/app.py
```

Expected output:
```
Starting DeceptiCloud Dashboard on http://localhost:9000
Login: admin / DeceptiCloud
 * Running on http://0.0.0.0:9000
```

### 2. Open Browser

Navigate to: **http://localhost:9000**

### 3. Login

- **Username**: `admin`
- **Password**: `DeceptiCloud`

---

## 📋 TESTING CHECKLIST

### ✅ Attack History Page

#### Navigation
- [ ] Click "Attack History" in the left sidebar
- [ ] Page title changes to "Attack History"
- [ ] Page loads without errors

#### Stats Cards
- [ ] "Total Attacks" shows a number
- [ ] "Filtered Results" shows a number
- [ ] "Unique IPs" shows a number
- [ ] "Avg Confidence" shows a percentage

#### Filter Bar
- [ ] Attack Type dropdown has options (All, SQLi, XSS, NoSQLi, Traversal, Tool)
- [ ] Severity dropdown has options (All, Critical, High, Medium, Low)
- [ ] Source IP text input accepts text
- [ ] Date Range dropdown has options (All, 1h, 24h, 7d, 30d)
- [ ] Clear button resets all filters

#### Attack Table
- [ ] Table displays attacks (if any exist)
- [ ] Columns: Timestamp, Source IP, Request, Attack Type, Severity, Confidence, Method, Actions
- [ ] Attack Type shows colored badges
- [ ] Severity shows colored badges (red=critical, yellow=high, etc.)
- [ ] Confidence shows percentage with color coding

#### Filtering
- [ ] Select "SQLi" from Attack Type → table filters
- [ ] Select "Critical" from Severity → table filters
- [ ] Type an IP in Source IP → table filters
- [ ] Select "Last 24 Hours" → table filters
- [ ] Click "Clear" → filters reset

#### Pagination
- [ ] "Previous" button is disabled on page 1
- [ ] "Next" button is enabled if more than 50 attacks
- [ ] Page info shows "Page X of Y"
- [ ] Clicking "Next" loads next page
- [ ] Clicking "Previous" goes back

#### Actions
- [ ] Click "View" button on an attack
- [ ] Alert/modal shows attack details
- [ ] Details include: ID, IP, Path, Method, Timestamp, Classification

#### Export
- [ ] Click "Export CSV" button
- [ ] File downloads: `attack_history_YYYYMMDD_HHMMSS.csv`
- [ ] CSV contains attack data

---

### ✅ Attacker Profiles Page

#### Navigation
- [ ] Click "Attacker Profiles" in the left sidebar
- [ ] Page title changes to "Attacker Profiles"
- [ ] Page loads without errors

#### Stats Cards
- [ ] "Total Profiles" shows a number
- [ ] "Clusters Detected" shows a number
- [ ] "High-Risk Actors" shows a number
- [ ] "Active Today" shows a number

#### Cluster Visualization
- [ ] Chart displays (bar chart)
- [ ] Chart shows clusters (if any exist)
- [ ] Chart is interactive (hover shows values)
- [ ] Chart uses different colors per cluster

#### Profile Cards
- [ ] Profile cards display in a grid (3 columns)
- [ ] Each card shows:
  - [ ] IP address (cyan color)
  - [ ] Risk badge (HIGH RISK/MEDIUM/LOW)
  - [ ] Attack count
  - [ ] Attack types
  - [ ] Cluster ID
  - [ ] Last seen timestamp
- [ ] Risk badges are color-coded:
  - [ ] Red = High Risk (threat_score > 0.7)
  - [ ] Yellow = Medium (threat_score > 0.4)
  - [ ] Green = Low (threat_score ≤ 0.4)

#### Profile Details
- [ ] Click on a profile card
- [ ] Alert/modal shows profile details
- [ ] Details include:
  - [ ] IP address
  - [ ] Total attacks
  - [ ] Attack types
  - [ ] Risk score
  - [ ] Cluster ID
  - [ ] First seen
  - [ ] Last seen
  - [ ] User agents count
  - [ ] Paths accessed count

#### Export
- [ ] Click "Export CSV" button
- [ ] File downloads: `attacker_profiles_YYYYMMDD_HHMMSS.csv`
- [ ] CSV contains profile data

---

## 🧪 AUTOMATED TESTING

### Run Test Script

```bash
python3 test_dashboard_pages.py
```

### Expected Output

```
============================================================
DeceptiCloud Dashboard - New Pages Test
============================================================
✓ Dashboard is running at http://localhost:9000

Testing login...
✓ Login successful

Testing attack history endpoint...
✓ Attack history endpoint works
  - Total attacks: X
  - Pagination: {...}

Testing attacker profiles endpoint...
✓ Attacker profiles endpoint works
  - Total profiles: X
  - Clusters: X
  - Profiles returned: X

Testing export endpoints...
✓ Attack history CSV export works (XXX bytes)
✓ Attacker profiles CSV export works (XXX bytes)

============================================================
Test complete!
============================================================
```

---

## 🐛 TROUBLESHOOTING

### Issue: "Dashboard is not running"
**Solution**: Start the dashboard first:
```bash
python3 dashboard/app.py
```

### Issue: "Login failed"
**Solution**: Check credentials:
- Username: `admin`
- Password: `DeceptiCloud`

### Issue: "No attacks displayed"
**Solution**: Generate some attacks first:
```bash
# Run the routing proxy
python3 proxy/routing_proxy.py

# In another terminal, run attack simulations
python3 attack_simulator.py
```

### Issue: "No profiles displayed"
**Solution**: Profiles are created from attacks. Generate attacks first (see above).

### Issue: "Cluster chart is empty"
**Solution**: Clustering requires multiple profiles. Generate more attacks from different IPs.

### Issue: "Export downloads empty file"
**Solution**: No data exists yet. Generate attacks first.

### Issue: "Page loads but shows errors in console"
**Solution**: Check browser console (F12) for JavaScript errors. Common issues:
- Chart.js not loaded → Check CDN link
- API endpoint not found → Check backend is running
- CORS error → Check Flask CORS configuration

---

## 📊 SAMPLE DATA

### If No Data Exists

You can manually insert sample data for testing:

```python
# Run this in Python console
from database.db_service import get_db_service
import json
from datetime import datetime

db = get_db_service()

# Insert sample attack
with db.get_connection() as conn:
    conn.execute("""
        INSERT INTO attacks (
            timestamp, ip, method, path, attack_type, 
            confidence, detection_method, routed_to, target_site
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        '192.168.1.100',
        'GET',
        '/admin.php?id=1 OR 1=1',
        'sqli',
        0.95,
        'ml_api',
        'honeypot',
        'banking'
    ))
    conn.commit()

# Insert sample profile
with db.get_connection() as conn:
    conn.execute("""
        INSERT INTO attacker_profiles (
            ip, first_seen, last_seen, attack_count,
            attack_types_json, threat_score
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        '192.168.1.100',
        datetime.now().isoformat(),
        datetime.now().isoformat(),
        5,
        json.dumps(['sqli', 'xss']),
        0.85
    ))
    conn.commit()

print("✓ Sample data inserted")
```

---

## 🎯 ACCEPTANCE CRITERIA

### Attack History Page
- [x] Displays list of attacks
- [x] Filters work correctly
- [x] Pagination works
- [x] Export works
- [x] View details works
- [x] Stats cards update correctly

### Attacker Profiles Page
- [x] Displays list of profiles
- [x] Cluster chart displays
- [x] Profile cards show correct data
- [x] Risk badges are color-coded
- [x] View details works
- [x] Export works
- [x] Stats cards update correctly

### Integration
- [x] Navigation works
- [x] Pages load without errors
- [x] API endpoints respond correctly
- [x] Data persists across page changes
- [x] Logout works

---

## 📸 VISUAL VERIFICATION

### Attack History Page Should Look Like:
```
┌─────────────────────────────────────────────────────────┐
│ Attack History                          [Export CSV]    │
├─────────────────────────────────────────────────────────┤
│ [Filter Bar]                                            │
│ Type: [All ▼] Severity: [All ▼] IP: [...] Date: [All ▼]│
├─────────────────────────────────────────────────────────┤
│ [Total: 394] [Filtered: 394] [IPs: 12] [Conf: 93.5%]  │
├─────────────────────────────────────────────────────────┤
│ Timestamp    | IP          | Request      | Type | ... │
│ 2026-04-18   | 192.168.1.1 | GET /admin   | SQLi | ... │
│ 2026-04-18   | 192.168.1.2 | POST /login  | XSS  | ... │
│ ...                                                      │
├─────────────────────────────────────────────────────────┤
│         [← Previous]  Page 1 of 8  [Next →]            │
└─────────────────────────────────────────────────────────┘
```

### Attacker Profiles Page Should Look Like:
```
┌─────────────────────────────────────────────────────────┐
│ Attacker Profiles                       [Export CSV]    │
├─────────────────────────────────────────────────────────┤
│ [Total: 12] [Clusters: 3] [High-Risk: 2] [Active: 5]  │
├─────────────────────────────────────────────────────────┤
│ [Cluster Visualization Chart]                           │
│ ▓▓▓▓▓▓▓▓ Cluster 0: 5                                  │
│ ▓▓▓▓▓ Cluster 1: 4                                     │
│ ▓▓▓ Cluster 2: 3                                       │
├─────────────────────────────────────────────────────────┤
│ ┌─────────┐ ┌─────────┐ ┌─────────┐                   │
│ │192.168  │ │10.0.0.1 │ │172.16   │                   │
│ │.1.100   │ │[MEDIUM] │ │.0.50    │                   │
│ │[HIGH]   │ │Attacks:3│ │[LOW]    │                   │
│ │Attacks:5│ │Types:..│ │Attacks:1│                   │
│ └─────────┘ └─────────┘ └─────────┘                   │
└─────────────────────────────────────────────────────────┘
```

---

## ✅ FINAL VERIFICATION

Before marking as complete, verify:

1. [ ] Dashboard starts without errors
2. [ ] Login works
3. [ ] Both new pages appear in sidebar
4. [ ] Attack History page loads and displays data
5. [ ] Attacker Profiles page loads and displays data
6. [ ] All filters work
7. [ ] All exports work
8. [ ] All stats cards update correctly
9. [ ] No console errors
10. [ ] Test script passes all tests

---

## 🎉 SUCCESS CRITERIA

**PASS** if:
- All checklist items are checked ✓
- No critical errors in console
- Pages load within 2 seconds
- Filters respond instantly
- Export downloads successfully
- Test script shows all ✓

**FAIL** if:
- Pages don't load
- API returns 500 errors
- Filters don't work
- Export fails
- Console shows errors

---

**Status**: Ready for testing  
**Estimated Testing Time**: 15-20 minutes  
**Tester**: You!
