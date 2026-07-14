# Live Threat Feed - Fix Applied

**Date**: April 20, 2026  
**Issue**: Live Threat Feed showing old/historical data instead of recent threats  
**Status**: ✅ FIXED

---

## 🎯 PROBLEM IDENTIFIED

The "Live Threat Feed" on the Overview page was showing **all attacks** from the database, including old historical data. This made it look like the feed was showing incorrect or stale information.

### Root Cause
```javascript
// OLD CODE - Showed all attacks
const atk = await fetch('/api/attacks?limit=20').then(r => r.json());
updateFeed(atk.attacks || []);
```

This fetched the **last 20 attacks** from the database, which could be hours or days old.

---

## ✅ SOLUTION APPLIED

### What Changed
The Live Threat Feed now shows **only attacks from the last 15 minutes**, making it truly "live":

```javascript
// NEW CODE - Shows only recent attacks (last 15 minutes)
const atk = await fetch('/api/attacks?limit=100').then(r => r.json());
const allAttacks = atk.attacks || [];

// Filter to last 15 minutes
const fifteenMinutesAgo = Date.now() - (15 * 60 * 1000);
const recentAttacks = allAttacks.filter(a => {
    const attackTime = new Date(a.timestamp).getTime();
    return attackTime >= fifteenMinutesAgo;
});

// Show recent attacks or fall back to latest 10
const feedAttacks = recentAttacks.length > 0 
    ? recentAttacks.slice(0, 20) 
    : allAttacks.slice(0, 10);
```

### Key Improvements

1. **Time-Based Filtering** ⏰
   - Only shows attacks from last 15 minutes
   - Makes the feed truly "live"

2. **Smart Fallback** 🔄
   - If no recent attacks, shows latest 10 historical attacks
   - Prevents empty feed during quiet periods

3. **Better Count Display** 📊
   - Shows: `"5 live events (412 total)"` when recent attacks exist
   - Shows: `"412 events"` when showing historical data

4. **Improved Empty State** 💬
   - Message: "No recent threats detected"
   - Subtitle: "Showing attacks from last 15 minutes"

---

## 🎨 HOW IT LOOKS NOW

### When Recent Attacks Exist (Active Period)
```
┌─────────────────────────────────────────┐
│ 🔴 Live Threat Feed    5 live events    │
│                        (412 total)      │
├─────────────────────────────────────────┤
│ 🔴 POST /api/login                      │
│    192.168.1.100  14:23:45  95%  [SQLi]│
│                                         │
│ 🔴 GET /admin/config                    │
│    10.0.0.50      14:22:10  88%  [XSS] │
│                                         │
│ 🔴 POST /search?q=<script>              │
│    172.16.0.25    14:21:33  92%  [XSS] │
└─────────────────────────────────────────┘
```

### When No Recent Attacks (Quiet Period)
```
┌─────────────────────────────────────────┐
│ 🔴 Live Threat Feed    412 events       │
├─────────────────────────────────────────┤
│ ℹ️  No recent threats detected          │
│    Showing attacks from last 15 minutes│
│                                         │
│ (Falls back to showing last 10 attacks)│
└─────────────────────────────────────────┘
```

---

## 🔧 ALTERNATIVE OPTIONS

If you want different behavior, here are other options:

### Option A: Change Time Window
Adjust the time window (currently 15 minutes):

```javascript
// 5 minutes (more strict)
const fiveMinutesAgo = Date.now() - (5 * 60 * 1000);

// 30 minutes (more lenient)
const thirtyMinutesAgo = Date.now() - (30 * 60 * 1000);

// 1 hour
const oneHourAgo = Date.now() - (60 * 60 * 1000);
```

**Location**: `dashboard/static/dashboard.js` line ~230

---

### Option B: Show Wazuh Alerts Instead
Use Wazuh SIEM alerts for the live feed:

```javascript
// Replace the fetch call with:
const alerts = await fetch('/api/adaptive/wazuh-alerts?limit=20&min_level=5')
    .then(r => r.json()).catch(() => []);

// Then format Wazuh alerts for display
const feedData = alerts.map(a => ({
    method: a.rule_id,
    path: a.rule_description,
    ip: a.ip,
    timestamp: a.timestamp,
    classification: {
        attack_types: a.groups || [],
        confidence: a.rule_level / 15  // Convert level to confidence
    }
}));

updateFeed(feedData);
```

**Benefits**: 
- Shows SIEM-level security events
- Includes system-level threats
- Professional security monitoring data

---

### Option C: Show High-Severity Only
Filter by confidence/severity:

```javascript
// Only show high-confidence attacks (>80%)
const highSeverityAttacks = allAttacks.filter(a => {
    const conf = a.classification?.confidence || 0;
    return conf > 0.8;
});
```

**Benefits**:
- Reduces noise
- Focuses on critical threats
- Better for executive dashboards

---

### Option D: Combine Multiple Sources
Show both recent attacks AND Wazuh alerts:

```javascript
// Fetch both
const [attacks, wazuhAlerts] = await Promise.all([
    fetch('/api/attacks?limit=50').then(r => r.json()),
    fetch('/api/adaptive/wazuh-alerts?limit=20').then(r => r.json())
]);

// Merge and sort by timestamp
const combined = [
    ...attacks.attacks.map(a => ({...a, source: 'ml'})),
    ...wazuhAlerts.map(a => ({...a, source: 'wazuh'}))
].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

// Filter to last 15 minutes
const recent = combined.filter(/* time filter */);
```

**Benefits**:
- Comprehensive threat view
- Shows both ML and SIEM detections
- Most complete picture

---

## 📊 TESTING

### Test 1: Generate Fresh Attacks
```bash
# Run attack simulation
bash attacks/web_attacks.sh

# Refresh dashboard - should see attacks in Live Threat Feed
```

### Test 2: Wait 15 Minutes
```bash
# Wait 15+ minutes without generating attacks
# Refresh dashboard - should show "No recent threats detected"
# Should fall back to showing last 10 historical attacks
```

### Test 3: Check Count Display
```bash
# With recent attacks: "5 live events (412 total)"
# Without recent attacks: "412 events"
```

---

## 🎯 RECOMMENDATION

**Current Implementation (15-minute window)** is the best choice because:

✅ **Truly "Live"** - Shows only recent activity  
✅ **Smart Fallback** - Never shows empty feed  
✅ **Clear Labeling** - Users know what they're seeing  
✅ **Balanced** - 15 minutes is neither too strict nor too lenient  
✅ **Demo-Friendly** - Works well for presentations  

---

## 📝 FILES MODIFIED

### 1. `dashboard/static/dashboard.js`
**Lines Changed**: ~228-245

**Changes**:
- Added time-based filtering (last 15 minutes)
- Added smart fallback logic
- Updated count display format
- Improved empty state message

---

## 🚀 DEPLOYMENT

### No Restart Required
Changes are in JavaScript - just **refresh the browser**:

1. Open dashboard: http://localhost:9000
2. Press `Ctrl+Shift+R` (hard refresh)
3. Navigate to Overview page
4. Check Live Threat Feed

### If You Want to Restart Anyway
```bash
# Stop system
./start_stop/decepticloud_control.sh stop

# Start system
./start_stop/decepticloud_control.sh start

# Wait 15 seconds, then open dashboard
```

---

## 🎓 CONCLUSION

**Status**: ✅ **FIXED**

The Live Threat Feed now:
- Shows only attacks from last 15 minutes
- Falls back to recent attacks if no live threats
- Displays clear count information
- Has informative empty state

**Result**: The feed is now truly "live" and shows accurate, recent threat data.

---

## 💡 NEXT STEPS (OPTIONAL)

If you want to enhance further:

1. **Add Auto-Refresh** - Update feed every 5 seconds
2. **Add Sound Alerts** - Play sound on new threats
3. **Add Animations** - Highlight new entries
4. **Add Filters** - Filter by attack type
5. **Add Export** - Export live feed to CSV

Let me know if you want any of these enhancements!

---

**Fixed By**: Kiro AI Assistant  
**Date**: April 20, 2026  
**Time**: ~5 minutes  
**Status**: ✅ COMPLETE
