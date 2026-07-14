# Wazuh Dashboard Fix - COMPLETED

## ✅ What Was Done

### 1. Configured Wazuh API Connection
Created the Wazuh API registry file with correct credentials:
- **File**: `/usr/share/wazuh-dashboard/data/wazuh/config/wazuh-registry.json`
- **API URL**: https://wazuh.manager:55000
- **Username**: admin
- **Password**: SecretPassword1!

### 2. Restarted Wazuh Dashboard
Restarted the dashboard container to load the new configuration.

### 3. Verified Plugin Loading
Confirmed that the Wazuh plugin is loading correctly.

---

## 🎯 How to Access Wazuh Dashboard

### Step 1: Open Browser
Navigate to:
```
http://localhost:5601
```

### Step 2: Login
**Credentials:**
- Username: `admin`
- Password: `SecretPassword1!`

### Step 3: Access Wazuh App
After login, you should be redirected to the Wazuh app, or navigate to:
```
http://localhost:5601/app/wazuh
```

---

## 📊 What You Should See

### Wazuh Dashboard Interface

Once logged in, you'll see:

#### 1. **Overview Page**
- Security events summary
- Alert statistics
- Top agents
- Recent alerts

#### 2. **Security Events**
- **Raw logs** from Wazuh Manager
- Alert details with:
  - Timestamp
  - Rule ID and description
  - Agent name
  - Source IP
  - Alert level
  - Full log data

#### 3. **Agents**
- List of monitored agents
- Agent status (active/disconnected)
- Agent details
- Configuration

#### 4. **Management**
- **Rules**: Security rules configuration
- **Decoders**: Log parsing rules
- **CDB Lists**: Custom lists
- **Groups**: Agent groups
- **Configuration**: Wazuh settings

#### 5. **Settings**
- API configuration
- Index pattern management
- About Wazuh

---

## 🔍 Verifying It Works

### Test 1: Check Dashboard Access
```bash
# Should return HTML (not "Application Not Found")
curl -s http://localhost:5601/app/wazuh | head -20
```

### Test 2: Check API Configuration
```bash
# View the configuration file
docker exec single-node-wazuh.dashboard cat /usr/share/wazuh-dashboard/data/wazuh/config/wazuh-registry.json
```

Expected output:
```json
{
  "hosts": {
    "default": {
      "id": "default",
      "url": "https://wazuh.manager",
      "port": 55000,
      "username": "admin",
      "password": "SecretPassword1!",
      "run_as": false
    }
  }
}
```

### Test 3: Check Wazuh Plugin Status
```bash
docker logs single-node-wazuh.dashboard 2>&1 | grep -i "wazuh.*plugin"
```

Expected: Should show Wazuh plugin initialized

---

## 🚨 If Still Seeing "Application Not Found"

### Solution 1: Clear Browser Cache
1. Press `Ctrl + Shift + Delete`
2. Clear all cached data
3. Close and reopen browser
4. Navigate to http://localhost:5601

### Solution 2: Wait for Full Initialization
The Wazuh dashboard may take 30-60 seconds to fully initialize after restart.

```bash
# Wait and check logs
sleep 30
docker logs single-node-wazuh.dashboard 2>&1 | tail -20
```

### Solution 3: Verify All Containers Running
```bash
docker ps --filter "name=wazuh"
```

Expected: All 3 containers should be "Up"

### Solution 4: Check Wazuh Manager API
```bash
# Test API connectivity
docker exec single-node-wazuh.dashboard curl -k https://wazuh.manager:55000/
```

Expected: Should return JSON response (even if unauthorized)

---

## 📝 System Status

### Current Configuration

**Wazuh Stack:**
- ✅ Indexer: Running on port 9200
- ✅ Manager: Running on port 55000
- ✅ Dashboard: Running on port 5601
- ✅ API Configuration: Added

**DeceptiCloud:**
- ✅ Adaptive Engine: Running (NOT TOUCHED)
- ✅ Dashboard: Running on port 9000
- ✅ All APIs: Working correctly

---

## 🔗 Integration Status

### Data Flow

```
Security Events
      ↓
Wazuh Manager (Port 55000)
      ↓
Wazuh Indexer (Port 9200)
      ↓
┌─────────────────┬─────────────────┐
│                 │                 │
Wazuh Dashboard   Adaptive Engine
(Port 5601)       (Background)
Raw Logs          ↓
                  DeceptiCloud Dashboard
                  (Port 9000)
                  ML Insights
```

### What Each Dashboard Shows

**Wazuh Dashboard (localhost:5601):**
- ✅ Raw security logs
- ✅ All alerts from Wazuh Manager
- ✅ Rule triggers
- ✅ Agent status
- ✅ Configuration management

**DeceptiCloud Dashboard (localhost:9000):**
- ✅ Processed attack data
- ✅ ML model predictions
- ✅ Attacker profiles (13 profiles)
- ✅ Behavioral clusters (5 clusters)
- ✅ Adaptive learning metrics
- ✅ Training pipeline status

---

## 🎓 For Your Jury Presentation

### Demo Flow

1. **Start with DeceptiCloud** (http://localhost:9000)
   - Show Overview: Attack statistics
   - Show Fingerprints: 13 profiles, 5 clusters
   - Show ML Models: 84-89% accuracy
   - Show Adaptive Engine: Real-time metrics ✅

2. **Switch to Wazuh** (http://localhost:5601)
   - Login with admin / SecretPassword1!
   - Show Security Events: Raw logs
   - Show Agents: Monitored systems
   - Show Management: Rules and configuration

3. **Explain Integration**
   - Wazuh collects raw security events
   - Adaptive Engine processes with ML
   - DeceptiCloud shows intelligent insights
   - Both dashboards complement each other

---

## 🔧 Troubleshooting Commands

### Restart Wazuh Dashboard
```bash
docker restart single-node-wazuh.dashboard
sleep 30
```

### View Dashboard Logs
```bash
docker logs -f single-node-wazuh.dashboard
```

### Check API Configuration
```bash
docker exec single-node-wazuh.dashboard cat /usr/share/wazuh-dashboard/data/wazuh/config/wazuh-registry.json
```

### Test Wazuh Manager API
```bash
curl -k https://localhost:55000/
```

### Reconfigure API (if needed)
```bash
docker exec -u root single-node-wazuh.dashboard bash -c 'cat > /usr/share/wazuh-dashboard/data/wazuh/config/wazuh-registry.json << "EOF"
{
  "hosts": {
    "default": {
      "id": "default",
      "url": "https://wazuh.manager",
      "port": 55000,
      "username": "admin",
      "password": "SecretPassword1!",
      "run_as": false
    }
  }
}
EOF
chown wazuh-dashboard:wazuh-dashboard /usr/share/wazuh-dashboard/data/wazuh/config/wazuh-registry.json'

docker restart single-node-wazuh.dashboard
```

---

## ✅ Verification Checklist

Before your presentation:

- [ ] Wazuh dashboard accessible at http://localhost:5601
- [ ] Can login with admin / SecretPassword1!
- [ ] Wazuh app loads (no "Application Not Found")
- [ ] Can see security events/logs
- [ ] Can see agents list
- [ ] Can access Management section
- [ ] DeceptiCloud still working at http://localhost:9000
- [ ] Adaptive Engine page still showing data

---

## 📞 Quick Reference

### URLs
- **Wazuh**: http://localhost:5601
- **DeceptiCloud**: http://localhost:9000

### Credentials
- **Wazuh**: admin / SecretPassword1!
- **DeceptiCloud**: admin / DeceptiCloud

### Docker Commands
```bash
# Status
docker ps --filter "name=wazuh"

# Logs
docker logs single-node-wazuh.dashboard

# Restart
docker restart single-node-wazuh.dashboard
```

---

**Status**: ✅ WAZUH DASHBOARD CONFIGURED  
**Next Step**: Open http://localhost:5601 in your browser and login!  
**Note**: Adaptive Engine page remains untouched and working ✅
