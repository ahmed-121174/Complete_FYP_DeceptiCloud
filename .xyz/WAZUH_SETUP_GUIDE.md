# Wazuh Dashboard Setup Guide

## Issue: "Application Not Found" at localhost:5601/app/wazuh

This error occurs because the Wazuh dashboard needs to be configured with the Wazuh Manager API connection on first use.

---

## Solution: Configure Wazuh API Through Browser

### Step 1: Access Wazuh Dashboard Root
Open your browser and go to:
```
http://localhost:5601
```

**Expected**: You should see either:
- A login page, OR
- A redirect to `/app/home` or `/app/wazuh`

### Step 2: Login to Wazuh Dashboard
**Credentials:**
- Username: `admin`
- Password: `SecretPassword1!`

### Step 3: Configure Wazuh API (If Prompted)

If you see a setup screen asking for API configuration, enter:

```
API URL:      https://wazuh.manager
Port:         55000
Username:     admin  
Password:     SecretPassword1!
```

Then click "Save" or "Add API"

### Step 4: Access Wazuh App

After configuration, navigate to:
```
http://localhost:5601/app/wazuh
```

You should now see the full Wazuh interface with:
- Security Events
- Agents
- Management
- Rules
- Decoders
- etc.

---

## Alternative: Direct Configuration via Docker

If the UI method doesn't work, you can configure it directly:

### Method 1: Using Docker Exec

```bash
# Enter the Wazuh dashboard container
docker exec -it single-node-wazuh.dashboard bash

# Create API configuration
cat > /usr/share/wazuh-dashboard/data/wazuh/config/wazuh-registry.json << 'EOF'
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

# Set correct permissions
chown wazuh-dashboard:wazuh-dashboard /usr/share/wazuh-dashboard/data/wazuh/config/wazuh-registry.json

# Exit container
exit

# Restart Wazuh dashboard
docker restart single-node-wazuh.dashboard

# Wait 30 seconds
sleep 30

# Now access http://localhost:5601/app/wazuh
```

### Method 2: Using Wazuh API Endpoint

```bash
# Get a session cookie by logging in
curl -c /tmp/wazuh_cookie.txt -X POST "http://localhost:5601/auth/login" \
  -H "Content-Type: application/json" \
  -H "osd-xsrf: true" \
  -d '{
    "username": "admin",
    "password": "SecretPassword1!"
  }'

# Add API host
curl -b /tmp/wazuh_cookie.txt -X POST "http://localhost:5601/api/v1/configuration/hosts/apis" \
  -H "Content-Type: application/json" \
  -H "osd-xsrf: true" \
  -d '{
    "id": "default",
    "url": "https://wazuh.manager",
    "port": 55000,
    "username": "admin",
    "password": "SecretPassword1!",
    "run_as": false
  }'
```

---

## Verification

After configuration, verify Wazuh is working:

### 1. Check API Connection
```bash
curl -s "http://localhost:5601/api/v1/configuration/hosts" \
  -H "osd-xsrf: true" | python3 -m json.tool
```

### 2. Access Wazuh Dashboard
Open browser: `http://localhost:5601/app/wazuh`

**Expected to see:**
- Overview dashboard
- Security events
- Agents list
- Management options

### 3. Check Wazuh Alerts
In the Wazuh dashboard, navigate to:
- **Security Events** → Should show alerts
- **Agents** → Should show wazuh.manager
- **Management** → Rules, Decoders, etc.

---

## What You Should See in Wazuh

Once properly configured, the Wazuh dashboard will show:

### 1. Overview Page
- Security events summary
- Top agents
- Alert statistics
- Recent alerts

### 2. Security Events
- **Raw logs** from Wazuh Manager
- Alert details
- Rule information
- Agent information
- Timestamps

### 3. Agents
- List of monitored agents
- Agent status
- Agent configuration

### 4. Management
- Rules configuration
- Decoders
- CDB lists
- Groups
- Configuration

### 5. Settings
- API configuration
- Pattern management
- About

---

## Troubleshooting

### Issue: Still seeing "Application Not Found"

**Solution 1: Clear browser cache**
```
Ctrl + Shift + Delete (Chrome/Firefox)
Clear all cached data
Reload page
```

**Solution 2: Restart Wazuh dashboard**
```bash
docker restart single-node-wazuh.dashboard
sleep 30
# Then access http://localhost:5601
```

**Solution 3: Check Wazuh plugin is loaded**
```bash
docker logs single-node-wazuh.dashboard 2>&1 | grep -i "wazuh.*plugin"
```

Expected output should include:
```
[info][plugins][wazuh] Plugin initialized
```

### Issue: Can't login

**Check credentials:**
- Username: `admin`
- Password: `SecretPassword1!` (with exclamation mark)

**Reset password if needed:**
```bash
docker exec single-node-wazuh.indexer bash -c \
  "export JAVA_HOME=/usr/share/wazuh-indexer/jdk && \
   /usr/share/wazuh-indexer/plugins/opensearch-security/tools/hash.sh -p SecretPassword1!"
```

### Issue: API connection error

**Check Wazuh Manager is running:**
```bash
docker ps --filter "name=wazuh.manager"
```

**Check API is accessible:**
```bash
curl -k -u admin:SecretPassword1! -X GET "https://localhost:55000/" 2>&1
```

**Check from dashboard container:**
```bash
docker exec single-node-wazuh.dashboard curl -k https://wazuh.manager:55000/
```

---

## Integration with DeceptiCloud

Once Wazuh is working, both dashboards will show security data:

### Wazuh Dashboard (localhost:5601)
- **Raw security logs** from all sources
- **Alert management**
- **Rule configuration**
- **Agent monitoring**

### DeceptiCloud Dashboard (localhost:9000)
- **Processed attack data**
- **ML-based classification**
- **Attacker profiling**
- **Behavioral clustering**
- **Adaptive learning metrics**

### Data Flow
```
Security Events → Wazuh Manager → Wazuh Indexer
                       ↓
                 Wazuh Dashboard (Raw logs)
                       ↓
              Adaptive Engine (Processing)
                       ↓
           DeceptiCloud Dashboard (ML insights)
```

---

## Quick Reference

### URLs
- **Wazuh Dashboard**: http://localhost:5601
- **Wazuh API**: https://localhost:55000
- **Wazuh Indexer**: http://localhost:9200
- **DeceptiCloud**: http://localhost:9000

### Credentials
- **Wazuh Dashboard**: admin / SecretPassword1!
- **Wazuh API**: admin / SecretPassword1!
- **DeceptiCloud**: admin / DeceptiCloud

### Docker Commands
```bash
# Check status
docker ps --filter "name=wazuh"

# View logs
docker logs single-node-wazuh.dashboard
docker logs single-node-wazuh.manager

# Restart services
docker restart single-node-wazuh.dashboard
docker restart single-node-wazuh.manager

# Access container
docker exec -it single-node-wazuh.dashboard bash
```

---

## Next Steps

1. ✅ Access http://localhost:5601
2. ✅ Login with admin / SecretPassword1!
3. ✅ Configure Wazuh API if prompted
4. ✅ Navigate to /app/wazuh
5. ✅ Verify you see security events and logs
6. ✅ Check that DeceptiCloud Adaptive Engine is still working (don't touch it!)

---

**Note**: The Adaptive Engine page in DeceptiCloud is working correctly - we're only fixing the Wazuh dashboard access!
