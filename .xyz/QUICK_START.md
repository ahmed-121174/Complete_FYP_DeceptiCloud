# DeceptiCloud - Quick Start Guide

**New Dashboard Pages**: Attack History & Attacker Profiles  
**Status**: ✅ Ready to Use

---

## 🚀 START IN 3 STEPS

### 1. Start Dashboard
```bash
python3 dashboard/app.py
```

### 2. Open Browser
Navigate to: **http://localhost:9000**

### 3. Login
- Username: `admin`
- Password: `DeceptiCloud`

---

## 📱 NEW PAGES

### Attack History
**Location**: Sidebar → "Attack History"

**Features**:
- 📊 View all attacks in a table
- 🔍 Filter by type, severity, IP, date
- 📄 Paginate through results (50 per page)
- 💾 Export to CSV or JSON
- 👁️ View detailed attack information

**Use Cases**:
- Investigate specific attacks
- Find attacks from a specific IP
- Export data for reports
- Analyze attack patterns

---

### Attacker Profiles
**Location**: Sidebar → "Attacker Profiles"

**Features**:
- 👤 View all attacker profiles
- 📈 See cluster visualization
- 🎯 Identify high-risk actors
- 📊 View attack statistics per attacker
- 💾 Export to CSV or JSON
- 👁️ View detailed profile information

**Use Cases**:
- Identify repeat attackers
- Analyze attacker behavior
- Group similar attackers
- Track high-risk IPs

---

## 🧪 TEST IT

### Quick Test
```bash
python3 test_dashboard_pages.py
```

Expected output: All ✓ checks pass

### Manual Test
1. Click "Attack History" → See attacks table
2. Try filters → Table updates
3. Click "Export CSV" → File downloads
4. Click "Attacker Profiles" → See profile cards
5. Click a profile card → See details

---

## 📊 WHAT YOU'LL SEE

### Attack History Page
```
┌─────────────────────────────────────────┐
│ Attack History          [Export CSV]    │
├─────────────────────────────────────────┤
│ Filters: Type | Severity | IP | Date    │
├─────────────────────────────────────────┤
│ Stats: 394 attacks | 12 IPs | 93.5%    │
├─────────────────────────────────────────┤
│ Table: Timestamp | IP | Request | ...   │
│        2026-04-18 | 192.168.1.1 | ...   │
│        2026-04-18 | 192.168.1.2 | ...   │
├─────────────────────────────────────────┤
│      [← Previous] Page 1 [Next →]       │
└─────────────────────────────────────────┘
```

### Attacker Profiles Page
```
┌─────────────────────────────────────────┐
│ Attacker Profiles       [Export CSV]    │
├─────────────────────────────────────────┤
│ Stats: 12 profiles | 3 clusters | ...   │
├─────────────────────────────────────────┤
│ [Cluster Chart]                         │
│ ▓▓▓▓▓▓▓▓ Cluster 0: 5 attackers        │
│ ▓▓▓▓▓ Cluster 1: 4 attackers           │
├─────────────────────────────────────────┤
│ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│ │192.168  │ │10.0.0.1 │ │172.16   │   │
│ │.1.100   │ │[MEDIUM] │ │.0.50    │   │
│ │[HIGH]   │ │3 attacks│ │[LOW]    │   │
│ │5 attacks│ │SQLi, XSS│ │1 attack │   │
│ └─────────┘ └─────────┘ └─────────┘   │
└─────────────────────────────────────────┘
```

---

## 🎯 KEY FEATURES

### Attack History
- ✅ **Filtering**: 4 filter types (type, severity, IP, date)
- ✅ **Pagination**: 50 attacks per page
- ✅ **Export**: CSV and JSON formats
- ✅ **Details**: Click "View" to see full attack info
- ✅ **Stats**: Real-time statistics cards

### Attacker Profiles
- ✅ **Clustering**: DBSCAN algorithm groups similar attackers
- ✅ **Visualization**: Bar chart shows cluster distribution
- ✅ **Risk Scoring**: Color-coded badges (red/yellow/green)
- ✅ **Export**: CSV and JSON formats
- ✅ **Details**: Click card to see full profile
- ✅ **Stats**: Real-time statistics cards

---

## 🔍 FILTERS EXPLAINED

### Attack Type
- **All Types**: Show everything
- **SQLi**: SQL injection attacks
- **XSS**: Cross-site scripting
- **NoSQLi**: NoSQL injection
- **Traversal**: Path traversal
- **Tool**: Scanner/tool detection

### Severity
- **Critical**: Confidence > 80%
- **High**: Confidence 50-80%
- **Medium**: Confidence 30-50%
- **Low**: Confidence < 30%

### Date Range
- **Last Hour**: Attacks in last 60 minutes
- **Last 24 Hours**: Attacks today
- **Last 7 Days**: Attacks this week
- **Last 30 Days**: Attacks this month

---

## 💾 EXPORT FORMATS

### CSV Format
```csv
id,timestamp,ip,attack_type,confidence,...
1,2026-04-18 10:30:00,192.168.1.1,sqli,0.95,...
2,2026-04-18 10:31:00,192.168.1.2,xss,0.87,...
```

### JSON Format
```json
[
  {
    "id": 1,
    "timestamp": "2026-04-18 10:30:00",
    "ip": "192.168.1.1",
    "attack_type": "sqli",
    "confidence": 0.95
  }
]
```

---

## 🎨 COLOR CODING

### Risk Levels (Attacker Profiles)
- 🔴 **Red**: High Risk (threat_score > 0.7)
- 🟡 **Yellow**: Medium Risk (threat_score 0.4-0.7)
- 🟢 **Green**: Low Risk (threat_score < 0.4)

### Severity Levels (Attack History)
- 🔴 **Critical**: Confidence > 80%
- 🟡 **High**: Confidence 50-80%
- 🟠 **Medium**: Confidence 30-50%
- 🔵 **Low**: Confidence < 30%

---

## 🐛 TROUBLESHOOTING

### "No attacks displayed"
**Solution**: Generate attacks first
```bash
python3 proxy/routing_proxy.py &
python3 attack_simulator.py
```

### "No profiles displayed"
**Solution**: Profiles are created from attacks. Generate attacks first.

### "Export downloads empty file"
**Solution**: No data exists. Generate attacks first.

### "Page won't load"
**Solution**: Check dashboard is running
```bash
# Check if running
ps aux | grep dashboard

# Restart if needed
python3 dashboard/app.py
```

---

## 📚 DOCUMENTATION

### Full Documentation
- `DASHBOARD_PAGES_COMPLETION.md` - Complete feature list
- `TESTING_GUIDE.md` - Detailed testing instructions
- `SESSION_COMPLETION_SUMMARY.md` - Implementation summary

### Test Script
```bash
python3 test_dashboard_pages.py
```

---

## ✅ CHECKLIST

Before using, verify:
- [ ] Dashboard is running (port 9000)
- [ ] Can login successfully
- [ ] "Attack History" appears in sidebar
- [ ] "Attacker Profiles" appears in sidebar
- [ ] Both pages load without errors

---

## 🎉 YOU'RE READY!

The new dashboard pages are complete and ready to use. Enjoy exploring your attack data!

**Questions?** Check the documentation files or run the test script.

**Next**: Build the Honeypot Management page (coming soon)

---

**Version**: 1.0  
**Date**: April 18, 2026  
**Status**: ✅ Production Ready
