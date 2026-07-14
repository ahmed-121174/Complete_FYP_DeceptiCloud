# Site Logs Page - Updates Applied

## ✅ Changes Made

### 1. Two-Row Layout for Site Tabs
**Before:** All 14 sites in a single row  
**After:** 2 rows - Real sites on top, Honeypots below

**Implementation:**
- Row 1: 7 real sites (BANKING, ECOMMERCE, HEALTHCARE, BLOG, API_SERVICE, CORPORATE, ADMIN_PANEL)
- Row 2: 7 honeypot sites with [HP] label
- Each row has a label ("REAL SITES" / "HONEYPOT SITES")
- Better visual organization and easier navigation

### 2. Enhanced Traffic Logs Display
**New 6-column table showing:**
1. **Timestamp** - When the event occurred
2. **Source IP** - Attacker/visitor IP address
3. **Agent/Source** - Wazuh agent name or "Proxy"
4. **Level** - Wazuh alert level (color-coded)
5. **Description** - Rule description or HTTP request
6. **Rule ID** - Wazuh rule identifier

**Features:**
- Wazuh logs highlighted with blue background
- Alert levels color-coded (L0-L15)
- Real-time data from database
- Sorted by timestamp (most recent first)
- Shows "Loading..." state while fetching
- Shows "No traffic logs found" when empty

### 3. Wazuh Integration
**Data Source:** `wazuh_alerts` table in database  
**Query Pattern:** Filters by agent name (e.g., `dc-real-banking`, `dc-hp-ecommerce`)

**Agent Naming Convention:**
- Real sites: `dc-real-{site_name}`
- Honeypots: `dc-hp-{site_name}`

**Example agents:**
- dc-real-banking
- dc-hp-banking
- dc-real-ecommerce
- dc-hp-ecommerce
- etc.

---

## 📊 How It Works

### When You Click a Site Tab:

1. **Frontend (dashboard.js):**
   - Calls `selectSiteLog(site, isHoneypot)`
   - Updates UI to highlight selected tab
   - Calls `loadSiteLogsData()` → `loadSiteTraffic()`

2. **API Request:**
   ```
   GET /api/adaptive/site-logs/{site_name}?type=traffic&honeypot={true/false}&limit=100
   ```

3. **Backend (adaptive_api.py):**
   - Queries `wazuh_alerts` table with agent name pattern
   - Queries `attacks` table with port/site name
   - Merges and returns both datasets

4. **Frontend Display:**
   - Combines Wazuh logs + attack logs
   - Sorts by timestamp (newest first)
   - Renders in 6-column table with color coding

---

## 🔍 Data Flow

```
Wazuh SIEM → Wazuh Log Ingestion Service → wazuh_alerts table → API → Dashboard
```

### Required Services:
1. ✅ **Wazuh Manager** - Running in Docker
2. ✅ **14 Wazuh Agents** - One for each site (real + honeypot)
3. ⚠️ **Wazuh Log Ingestion Service** - Must be running to populate database
4. ✅ **Dashboard** - Displays the data

---

## 🚀 To See Wazuh Logs in Dashboard

### Step 1: Ensure All Services Are Running
```bash
cd "/media/amei-302/New Volume1/SEMESTER VIII/Ahmed Fype-II"
./start_stop/decepticloud_control.sh status
```

Should show:
- Wazuh Manager: Running
- 14 Agents: Running (dc-agent-001 through dc-agent-014)
- Dashboard: Port 9000 UP
- Proxy: Port 8080 UP

### Step 2: Verify Wazuh Agents Are Connected
Check Wazuh dashboard at: `https://localhost` (or your Wazuh URL)
- Login to Wazuh
- Go to Agents section
- Verify all 14 agents are "Active"

### Step 3: Generate Traffic
```bash
# Generate web attacks
./.JURY_PRESENTATION/2_WEB_ATTACKS.sh

# Or manually visit sites
curl http://localhost:3001  # Real banking site
curl http://localhost:4001  # Honeypot banking site
```

### Step 4: Check Database for Wazuh Logs
```bash
sqlite3 database/decepticloud.db "SELECT COUNT(*) FROM wazuh_alerts;"
```

If count is 0, the Wazuh log ingestion service may not be running.

### Step 5: View in Dashboard
1. Open dashboard: `http://localhost:9000`
2. Login
3. Go to **Site Logs** page
4. Click any site (e.g., BANKING or BANKING [HP])
5. Should see Wazuh logs with blue background

---

## 🎨 Visual Changes

### Site Tabs Layout:
```
┌─────────────────────────────────────────────────────────┐
│ REAL SITES                                              │
│ [BANKING] [ECOMMERCE] [HEALTHCARE] [BLOG] ...          │
│                                                         │
│ HONEYPOT SITES                                          │
│ [BANKING [HP]] [ECOMMERCE [HP]] [HEALTHCARE [HP]] ...  │
└─────────────────────────────────────────────────────────┘
```

### Traffic Logs Table:
```
┌──────────────┬────────────┬──────────────┬───────┬─────────────────┬─────────┐
│ Timestamp    │ Source IP  │ Agent/Source │ Level │ Description     │ Rule ID │
├──────────────┼────────────┼──────────────┼───────┼─────────────────┼─────────┤
│ 2024-04-20   │ 192.168... │ dc-real-...  │  L7   │ SQL injection   │  31103  │
│ 13:45:23     │            │              │       │ attempt         │         │
├──────────────┼────────────┼──────────────┼───────┼─────────────────┼─────────┤
│ 2024-04-20   │ 10.0.0.5   │ Proxy        │   —   │ GET /login      │ Normal  │
│ 13:45:20     │            │              │       │                 │         │
└──────────────┴────────────┴──────────────┴───────┴─────────────────┴─────────┘
```

---

## 📝 Files Modified

### 1. dashboard/static/dashboard.js
**Changes:**
- Updated `initSiteLogs()` - Two-row layout with labels
- Updated `loadSiteTraffic()` - 6-column display with Wazuh details
- Added loading states and better error handling
- Improved color coding for alert levels

### 2. dashboard/templates/dashboard.html
**Changes:**
- Updated traffic table headers (6 columns)
- Added column widths for better layout
- Updated cache-busting version to `v=2.2`

---

## ✅ Expected Behavior

### When Database Has Data:
- Click any site → See Wazuh logs with blue background
- Wazuh logs show: agent name, rule level, rule description, rule ID
- Proxy logs show: HTTP method, path, attack type
- All sorted by timestamp (newest first)

### When Database Is Empty:
- Click any site → See "No traffic logs found for this site"
- This is normal if:
  - No traffic has been generated yet
  - Wazuh log ingestion service not running
  - Agents not connected to Wazuh manager

---

## 🔧 Troubleshooting

### Issue: "No traffic logs found"

**Possible Causes:**
1. No traffic generated yet
2. Wazuh agents not connected
3. Wazuh log ingestion service not running
4. Database not populated

**Solutions:**
1. Generate traffic using attack scripts
2. Check agent status in Wazuh dashboard
3. Verify log ingestion service is running
4. Check database: `sqlite3 database/decepticloud.db "SELECT * FROM wazuh_alerts LIMIT 5;"`

### Issue: Only seeing proxy logs, no Wazuh logs

**Cause:** Wazuh log ingestion service not running

**Solution:**
Check if `wazuh/log_ingestion_service.py` is running:
```bash
ps aux | grep log_ingestion_service
```

If not running, it should be started by `launch_decepticloud_v2.py`

---

## 🎯 Next Steps

1. **Clear browser cache** - Press Ctrl + Shift + R
2. **Restart services** - `./start_stop/decepticloud_control.sh restart`
3. **Generate traffic** - Use attack scripts or manual requests
4. **View logs** - Go to Site Logs page and click any site
5. **Verify Wazuh data** - Should see blue-highlighted Wazuh logs

---

## 📊 Summary

**Status:** ✅ Updates Applied  
**Cache Version:** v=2.2  
**Layout:** 2 rows (Real + Honeypot)  
**Columns:** 6 (Timestamp, IP, Agent, Level, Description, Rule ID)  
**Data Source:** Real-time from `wazuh_alerts` table  
**Color Coding:** Blue for Wazuh, Yellow for Proxy  

**Ready for testing!** 🚀

---

**Created:** Site Logs Update Session  
**Files Modified:** 2 (dashboard.js, dashboard.html)  
**Action Required:** Clear cache and restart services
