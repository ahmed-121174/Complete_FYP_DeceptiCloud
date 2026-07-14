# Site Logs Page & Model Drift Removal - Fix Summary

## Changes Made

### 1. ✅ Removed Model Drift Detection from Adaptive Engine Page

**Files Modified:**
- `dashboard/templates/dashboard.html` - Removed the entire "Model Drift Detection" card section
- `dashboard/static/dashboard.js` - Removed `aleLoadDrift()` function and its call from `aleRefresh()`

**What was removed:**
- The "📉 Model Drift Detection" card with monitoring badge
- The drift panel that displayed drift events
- The `aleLoadDrift()` JavaScript function
- The call to `aleLoadDrift()` in the `aleRefresh()` function

### 2. ✅ Fixed Site Logs Page - Now Fully Functional

**Problem:** 
- Site Logs page was not loading when clicked
- No site tabs were appearing
- Traffic logs were not being displayed

**Root Causes:**
1. The `sitelogs` page was not added to the `loadPageData()` switch statement
2. The `sitelogs` page was not in the titles object
3. There was a syntax error in `updateSiteTabsUI()` function (duplicate `getElementById` call)
4. Duplicate `DOMContentLoaded` event listener was causing conflicts

**Fixes Applied:**

#### A. Added sitelogs to loadPageData switch
```javascript
case 'sitelogs': initSiteLogs(); loadSiteLogsData(); break;
```

#### B. Added sitelogs to titles objects (2 locations)
```javascript
sitelogs: 'Site Logs & Telemetry'
```

#### C. Fixed syntax error in updateSiteTabsUI()
**Before:**
```javascript
const activeTab = document.getElementById(activeTabId);yId(activeTabId);
```

**After:**
```javascript
const activeTab = document.getElementById(activeTabId);
```

#### D. Removed duplicate DOMContentLoaded listener
Removed the standalone `initSiteLogs()` call at the end of the file since it's now called properly when the page loads.

## How Site Logs Page Works Now

### Page Structure

```
Site Logs Page
├── Site Selector Tabs (Top)
│   ├── Real Sites (7): banking, ecommerce, healthcare, blog, api_service, corporate, admin_panel
│   └── Honeypot Sites (7): Same sites with [HP] suffix
│
└── Content Tabs (Per Site)
    ├── Traffic Logs - All HTTP requests (Wazuh + Proxy logs)
    ├── Attack Events - High-severity alerts only
    └── Statistics - Charts and metrics
```

### Data Flow

1. **User clicks "Site Logs" in sidebar**
   - `navigateTo('sitelogs')` is called
   - `loadPageData('sitelogs')` executes
   - `initSiteLogs()` creates the 14 site tabs (7 real + 7 honeypot)
   - `loadSiteLogsData()` fetches data for the default site (banking)

2. **User clicks a site tab (e.g., "ecommerce")**
   - `selectSiteLog('ecommerce', false)` is called
   - Updates `currentSite` and `currentSiteIsHp` variables
   - `updateSiteTabsUI()` highlights the active tab
   - `loadSiteLogsData()` fetches data for the selected site

3. **User switches between Traffic/Attacks/Stats tabs**
   - `switchSiteSubtab('traffic')` is called
   - Shows/hides the appropriate content div
   - Calls the appropriate load function:
     - `loadSiteTraffic()` - Fetches traffic logs
     - `loadSiteAttacks()` - Fetches attack events
     - `loadSiteStats()` - Fetches statistics

### API Endpoints Used

**Backend:** `adaptive_engine/api/adaptive_api.py`

```python
@adaptive_bp.route('/api/adaptive/site-logs/<site_name>', methods=['GET'])
def ale_site_logs(site_name):
    # Parameters:
    # - type: 'traffic', 'attacks', or 'stats'
    # - honeypot: 'true' or 'false'
    # - limit: number of records (default 100)
```

**Example API Calls:**
- Traffic: `/api/adaptive/site-logs/banking?type=traffic&honeypot=false&limit=100`
- Attacks: `/api/adaptive/site-logs/banking?type=attacks&honeypot=false&limit=50`
- Stats: `/api/adaptive/site-logs/banking?type=stats&honeypot=false`

### Data Sources

The backend queries multiple database tables:

1. **Traffic Logs:**
   - `wazuh_alerts` table - SIEM alerts filtered by agent name
   - `attacks` table - Proxy detections filtered by routed_to port

2. **Attack Events:**
   - `attacks` table - Filtered by attack_type IS NOT NULL
   - `wazuh_alerts` table - Filtered by rule_level >= 7

3. **Statistics:**
   - Attack type distribution (GROUP BY attack_type)
   - Hourly attack counts (last 24 hours)
   - Wazuh severity distribution (GROUP BY rule_level)

### Site-to-Port Mapping

The backend uses this mapping to filter data:

```python
SITE_PORT_MAP = {
    'banking':     {'real': 3001, 'honeypot': 4001},
    'ecommerce':   {'real': 3002, 'honeypot': 4002},
    'healthcare':  {'real': 3003, 'honeypot': 4003},
    'blog':        {'real': 3004, 'honeypot': 4004},
    'api_service': {'real': 3005, 'honeypot': 4005},
    'corporate':   {'real': 3006, 'honeypot': 4006},
    'admin_panel': {'real': 3007, 'honeypot': 4007},
}
```

### Agent Name Patterns

Wazuh agents are filtered by name patterns:
- Real sites: `dc-real-{site_name}` (e.g., `dc-real-banking`)
- Honeypot sites: `dc-hp-{site_name}` (e.g., `dc-hp-banking`)

## Testing Instructions

### 1. Test Model Drift Removal

1. Navigate to Adaptive Engine page
2. Verify that "Model Drift Detection" section is no longer visible
3. Verify that other sections (Training Data, Model History, etc.) still work

### 2. Test Site Logs Page

1. **Navigate to Site Logs:**
   - Click "Site Logs" in the sidebar
   - Page should load with 14 site tabs visible at the top

2. **Test Site Selection:**
   - Click on different site tabs (banking, ecommerce, etc.)
   - Active tab should be highlighted
   - Click on honeypot sites (with [HP] suffix)
   - Honeypot tabs should be highlighted in yellow/orange

3. **Test Traffic Logs Tab:**
   - Should show a table with columns: Timestamp, Source IP, Action/Path, Agent/Log
   - Data should come from Wazuh alerts and proxy attacks
   - If no data: "No traffic logs found" message should appear

4. **Test Attack Events Tab:**
   - Click "Attack Events" tab
   - Should show a table with: Timestamp, IP, Threat Type, Severity, Payload/Details
   - Only high-severity events should be shown
   - If no data: "No attacks recorded" message should appear

5. **Test Statistics Tab:**
   - Click "Statistics" tab
   - Should show:
     - Total Events count (24h)
     - Attack Types breakdown
     - Wazuh Severity Distribution bar chart
   - If no data: Appropriate "No data" messages should appear

6. **Test Refresh Button:**
   - Click the "↻ Refresh" button in the top right
   - Data should reload for the currently selected site

### 3. Generate Test Data (if needed)

If no data appears, you can generate test data:

```bash
# Run attack simulations
python attack_simulator.py

# Or manually insert test data into database
sqlite3 database/decepticloud.db
INSERT INTO attacks (timestamp, ip, attack_type, path, method, routed_to, honeypot_name, confidence, severity)
VALUES (datetime('now'), '192.168.1.100', 'SQLi', '/login', 'POST', 'honeypot:4001', 'dc-hp-banking', 0.95, 'high');
```

## Files Modified

1. **dashboard/templates/dashboard.html**
   - Removed Model Drift Detection card section

2. **dashboard/static/dashboard.js**
   - Removed `aleLoadDrift()` function
   - Removed `aleLoadDrift()` call from `aleRefresh()`
   - Added `sitelogs` case to `loadPageData()` switch
   - Added `sitelogs` to titles objects (2 locations)
   - Fixed syntax error in `updateSiteTabsUI()`
   - Removed duplicate `DOMContentLoaded` listener

## Expected Behavior

### Site Logs Page - Working Features

✅ **Site Tab Navigation**
- 14 tabs visible (7 real + 7 honeypot)
- Clicking tabs switches between sites
- Active tab is highlighted
- Real sites: cyan color
- Honeypot sites: yellow/orange color

✅ **Traffic Logs Tab**
- Shows all HTTP requests
- Combines Wazuh SIEM alerts and proxy logs
- Displays: timestamp, IP, action/path, agent info
- Auto-scrollable table (max 500px height)

✅ **Attack Events Tab**
- Shows only high-severity attacks
- Displays: timestamp, IP, threat type, severity, payload
- Color-coded severity levels
- Red background for attack rows

✅ **Statistics Tab**
- Total events counter (24h)
- Attack types breakdown
- Wazuh severity distribution chart
- Visual bar chart for severity levels

✅ **Refresh Functionality**
- Manual refresh button works
- Data reloads for current site
- No page reload required

### Adaptive Engine Page - After Drift Removal

✅ **Removed:**
- Model Drift Detection card
- Drift monitoring badge
- Drift data panel

✅ **Still Working:**
- Engine status indicators
- Training data pipeline
- Model retraining controls
- Model version history
- Wazuh live alerts feed
- Active attacker session
- Live attack stream
- Attacker cluster analysis

## Troubleshooting

### Issue: Site tabs not appearing
**Solution:** Check browser console for JavaScript errors. Ensure `SITES` array is defined.

### Issue: No data in traffic logs
**Possible causes:**
1. No attacks have been recorded yet
2. Wazuh is not running or not sending alerts
3. Site names don't match agent names in database

**Solution:** 
- Check `wazuh_alerts` table: `SELECT * FROM wazuh_alerts LIMIT 10;`
- Check `attacks` table: `SELECT * FROM attacks LIMIT 10;`
- Verify agent names match pattern: `dc-real-{site}` or `dc-hp-{site}`

### Issue: API returns error
**Solution:** Check backend logs for errors. Verify database connection is working.

## Conclusion

Both requested features have been successfully implemented:

1. ✅ **Model Drift Detection removed** from Adaptive Engine page
2. ✅ **Site Logs page fully functional** with:
   - Working site tab navigation (14 sites)
   - Traffic logs display
   - Attack events display
   - Statistics display
   - Real-time data from database
   - Proper error handling and empty state messages

The Site Logs page now provides comprehensive visibility into traffic and attacks for all 14 sites (7 real + 7 honeypot) with proper filtering and data visualization!
