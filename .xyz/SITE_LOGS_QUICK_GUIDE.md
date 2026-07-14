# Site Logs Page - Quick Action Guide

## ✅ Changes Applied Successfully!

### What's New:
1. ✅ **2-Row Layout** - Real sites on top, honeypots below
2. ✅ **Enhanced Table** - 6 columns showing Wazuh details
3. ✅ **Real-time Data** - Fetches from Wazuh alerts table
4. ✅ **Color Coding** - Blue for Wazuh, Yellow for Proxy
5. ✅ **Services Restarted** - All running

---

## 🚀 What To Do NOW

### Step 1: Clear Browser Cache
**Press:** `Ctrl + Shift + R` (or `Ctrl + F5`)

This will load the new version (v=2.2) with the updated layout.

### Step 2: View the New Layout
1. Open dashboard: `http://localhost:9000`
2. Login
3. Go to **Site Logs** page
4. You should now see:
   - **Row 1:** BANKING, ECOMMERCE, HEALTHCARE, BLOG, API_SERVICE, CORPORATE, ADMIN_PANEL
   - **Row 2:** BANKING [HP], ECOMMERCE [HP], HEALTHCARE [HP], etc.

### Step 3: Click Any Site
- Click **BANKING** (real site)
- Or click **BANKING [HP]** (honeypot)
- Should see traffic logs table with 6 columns

---

## 📊 What You'll See

### If Database Has Wazuh Data:
```
┌──────────────┬────────────┬──────────────┬───────┬─────────────────┬─────────┐
│ Timestamp    │ Source IP  │ Agent/Source │ Level │ Description     │ Rule ID │
├──────────────┼────────────┼──────────────┼───────┼─────────────────┼─────────┤
│ 2024-04-20   │ 192.168... │ dc-real-...  │  L7   │ SQL injection   │  31103  │
│ 13:45:23     │            │              │       │ attempt         │         │
└──────────────┴────────────┴──────────────┴───────┴─────────────────┴─────────┘
```

### If Database Is Empty:
```
No traffic logs found for this site
```

This is normal if:
- No traffic generated yet
- Wazuh agents just started (need time to connect)
- Wazuh log ingestion service starting up

---

## 🎯 To Generate Wazuh Logs

### Option 1: Use Attack Scripts
```bash
cd "/media/amei-302/New Volume1/SEMESTER VIII/Ahmed Fype-II"
./.JURY_PRESENTATION/2_WEB_ATTACKS.sh
```

### Option 2: Manual Requests
```bash
# Real banking site
curl http://localhost:3001

# Honeypot banking site
curl http://localhost:4001

# Try SQL injection (will trigger Wazuh alert)
curl "http://localhost:3001/login?user=admin' OR '1'='1"
```

### Option 3: Visit in Browser
- Open: `http://localhost:3001` (real banking)
- Open: `http://localhost:4001` (honeypot banking)
- Try different paths, forms, etc.

---

## 🔍 Verify Wazuh Integration

### Check Wazuh Agents Status:
```bash
# List running agent containers
docker ps | grep dc-agent

# Should show 14 agents running
```

### Check Database for Wazuh Logs:
```bash
cd "/media/amei-302/New Volume1/SEMESTER VIII/Ahmed Fype-II"
sqlite3 database/decepticloud.db "SELECT COUNT(*) FROM wazuh_alerts;"
```

If count > 0, you have Wazuh data!

### View Sample Wazuh Logs:
```bash
sqlite3 database/decepticloud.db "SELECT timestamp, agent_name, rule_level, rule_description FROM wazuh_alerts LIMIT 5;"
```

---

## 🎨 Visual Comparison

### Before:
```
[BANKING] [ECOMMERCE] [HEALTHCARE] [BLOG] [API_SERVICE] [CORPORATE] [ADMIN_PANEL] [BANKING [HP]] [ECOMMERCE [HP]] ...
```
All in one long row, hard to distinguish real from honeypot.

### After:
```
REAL SITES
[BANKING] [ECOMMERCE] [HEALTHCARE] [BLOG] [API_SERVICE] [CORPORATE] [ADMIN_PANEL]

HONEYPOT SITES
[BANKING [HP]] [ECOMMERCE [HP]] [HEALTHCARE [HP]] [BLOG [HP]] [API_SERVICE [HP]] [CORPORATE [HP]] [ADMIN_PANEL [HP]]
```
Clear separation, easy to navigate.

---

## 🔧 Troubleshooting

### Issue: Still seeing old layout

**Solution:**
1. Clear browser cache: `Ctrl + Shift + R`
2. Try incognito window: `Ctrl + Shift + N`
3. Check browser console (F12) for errors

### Issue: "No traffic logs found"

**This is normal if:**
- Services just started (wait 1-2 minutes)
- No traffic generated yet
- Wazuh agents connecting to manager

**To fix:**
1. Wait 2 minutes for agents to connect
2. Generate traffic (see above)
3. Refresh page

### Issue: Only seeing proxy logs, no Wazuh logs

**Cause:** Wazuh log ingestion service may not be running

**Check:**
```bash
ps aux | grep log_ingestion_service
```

**Should be started automatically by launcher**

---

## 📝 Technical Details

### Agent Name Mapping:
| Site | Real Agent | Honeypot Agent |
|------|-----------|----------------|
| banking | dc-real-banking | dc-hp-banking |
| ecommerce | dc-real-ecommerce | dc-hp-ecommerce |
| healthcare | dc-real-healthcare | dc-hp-healthcare |
| blog | dc-real-blog | dc-hp-blog |
| api_service | dc-real-api_service | dc-hp-api_service |
| corporate | dc-real-corporate | dc-hp-corporate |
| admin_panel | dc-real-admin_panel | dc-hp-admin_panel |

### Port Mapping:
| Site | Real Port | Honeypot Port |
|------|-----------|---------------|
| banking | 3001 | 4001 |
| ecommerce | 3002 | 4002 |
| healthcare | 3003 | 4003 |
| blog | 3004 | 4004 |
| api_service | 3005 | 4005 |
| corporate | 3006 | 4006 |
| admin_panel | 3007 | 4007 |

---

## ✅ Summary

**Status:** ✅ All Changes Applied  
**Services:** ✅ Running  
**Cache Version:** v=2.2  
**Layout:** ✅ 2 Rows  
**Columns:** ✅ 6 (with Wazuh details)  

**Next Steps:**
1. Clear browser cache (Ctrl + Shift + R)
2. View Site Logs page
3. Click any site to see logs
4. Generate traffic to populate data

**Ready for your jury presentation!** 🎉

---

**Created:** Site Logs Update Session  
**Action Required:** Clear browser cache and test
