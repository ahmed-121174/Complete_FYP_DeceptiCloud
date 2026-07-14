# Browser Cache Clear Instructions

## ✅ Changes Applied

I've made two important changes to force your browser to load the new JavaScript file:

1. **Added Cache-Busting Version** - Changed `dashboard.js` to `dashboard.js?v=2.1`
2. **Added Cache Control Headers** - Flask now sends headers to prevent caching

## 🔄 How to Clear Browser Cache (Choose ONE method)

### Method 1: Hard Refresh (Quickest)
**For Chrome/Firefox on Linux:**
1. Go to `http://localhost:9000`
2. Press **Ctrl + Shift + R** (or **Ctrl + F5**)
3. This forces a complete reload bypassing cache

### Method 2: Clear Cache via Developer Tools (Recommended)
**For Chrome:**
1. Open the dashboard: `http://localhost:9000`
2. Press **F12** to open Developer Tools
3. **Right-click** on the refresh button (next to address bar)
4. Select **"Empty Cache and Hard Reload"**

**For Firefox:**
1. Open the dashboard: `http://localhost:9000`
2. Press **F12** to open Developer Tools
3. Go to **Network** tab
4. Check **"Disable Cache"** checkbox
5. Press **Ctrl + Shift + R** to reload

### Method 3: Clear All Browser Data (Nuclear Option)
**For Chrome:**
1. Press **Ctrl + Shift + Delete**
2. Select **"Cached images and files"**
3. Time range: **"Last hour"** or **"All time"**
4. Click **"Clear data"**
5. Reload the dashboard

**For Firefox:**
1. Press **Ctrl + Shift + Delete**
2. Select **"Cache"**
3. Time range: **"Everything"**
4. Click **"Clear Now"**
5. Reload the dashboard

### Method 4: Incognito/Private Window (Testing)
**Quick test to verify the fix works:**
1. Open a **new Incognito/Private window** (Ctrl + Shift + N in Chrome)
2. Go to `http://localhost:9000`
3. Login and check if the changes are visible
4. If yes, then it's just a cache issue in your regular browser

---

## ✅ What to Expect After Clearing Cache

Once you clear the cache and reload, you should see:

### Adaptive Engine Page:
- ✅ **Model Drift Detection** - REMOVED (no longer visible)
- ✅ **Behavioral Attacker Comparison** - REMOVED (no longer visible)
- ✅ **Active Attacker Session** - Shows real data or "No active attackers"
- ✅ **Attacker Cluster Analysis** - Shows real clusters or "No clusters yet"
- ✅ **Wazuh Live Alerts** - Shows real SIEM data or "No Wazuh alerts yet"

### Site Logs Page:
- ✅ **14 Site Tabs** - 7 real + 7 honeypot (with [HP] label)
- ✅ **Click any site** - Shows that site's specific logs
- ✅ **3 Subtabs** - Traffic Logs, Attack Events, Statistics
- ✅ **Real Data** - From database, or "No traffic logs found" if empty

---

## 🔍 How to Verify the New File is Loaded

### Check in Browser Developer Tools:
1. Press **F12** to open Developer Tools
2. Go to **Network** tab
3. Reload the page (**Ctrl + Shift + R**)
4. Look for **dashboard.js?v=2.1** in the list
5. Click on it and check the **Response** tab
6. You should see the updated code (no Model Drift functions)

### Check the Console:
1. Press **F12** to open Developer Tools
2. Go to **Console** tab
3. Type: `typeof aleLoadDrift`
4. Press Enter
5. Should show: **"undefined"** (function was removed)

---

## 🚨 If Still Not Working

If you still see the old interface after trying all methods:

### 1. Check if the file was actually updated:
```bash
cd "/media/amei-302/New Volume1/SEMESTER VIII/Ahmed Fype-II"
grep -n "aleLoadDrift" dashboard/static/dashboard.js
```
- Should return: **nothing** (function removed)

### 2. Check if Flask is serving the new file:
```bash
curl -I http://localhost:9000/static/dashboard.js?v=2.1
```
- Should show: **Cache-Control: no-store, no-cache**

### 3. Restart the browser completely:
- Close **all browser windows**
- Kill any background browser processes
- Reopen browser and try again

### 4. Check the launcher log:
```bash
tail -f logs/launch_v2.log
```
- Look for any errors related to the dashboard

---

## 📝 Quick Command Reference

```bash
# Check if services are running
./start_stop/decepticloud_control.sh status

# Restart services
./start_stop/decepticloud_control.sh restart

# View dashboard logs
tail -f logs/launch_v2.log

# Check if dashboard is responding
curl http://localhost:9000/api/stats
```

---

## ✅ Summary

**What I Fixed:**
1. ✅ Added `?v=2.1` to JavaScript file URL (cache-busting)
2. ✅ Added Flask cache control headers
3. ✅ Restarted all services

**What You Need to Do:**
1. Clear browser cache using one of the methods above
2. Reload the dashboard
3. Verify the changes are visible

**Expected Result:**
- Model Drift Detection section: **GONE**
- Behavioral Comparison section: **GONE**
- Site Logs page: **FULLY FUNCTIONAL**
- All data: **REAL-TIME FROM DATABASE**

---

**If you still see the old interface after clearing cache, let me know and I'll investigate further!**
