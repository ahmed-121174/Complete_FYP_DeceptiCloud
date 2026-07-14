# DeceptiCloud System Startup - FIXED ✓

## Problem Summary

After laptop shutdown, the DeceptiCloud system failed to start with these errors:
1. **"no configuration file provided: not found"** - Docker Compose couldn't find/parse the config
2. **"Permission denied"** - Trying to write to wrong path (`New Volume1` instead of `New Volume2`)
3. **"invalid IP"** - Wazuh Manager container wasn't starting, so no IP could be detected

## Root Causes

### 1. Hardcoded Paths
The control script had hardcoded paths pointing to the old drive location:
```bash
PROJECT_ROOT="/media/amei-302/New Volume1/SEMESTER VIII/Ahmed Fype-II"
```

### 2. Wrong Docker Compose File
Script was using `wazuh-docker/single-node/docker-compose.yml` which had format issues with Docker Compose v2

### 3. Old Containers with Wrong Mounts
Existing containers were created with old paths and couldn't mount config files from the new location

## Solutions Applied

### 1. Dynamic Path Detection
Changed to auto-detect project root:
```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
```

### 2. Switched to Working Docker Compose File
Changed from `wazuh-docker/single-node/` to `wazuh/docker-compose.yml`:
```bash
WAZUH_DIR="$PROJECT_ROOT/wazuh"
```

### 3. Updated Docker Compose Command
Using native Docker Compose v2 command:
```bash
DOCKER_COMPOSE="docker compose"
```

### 4. Fixed Container Names
Updated to match the new docker-compose file:
- `single-node-wazuh.manager` → `wazuh-manager`
- `single-node-wazuh.indexer` → `wazuh-indexer`
- `single-node-wazuh.dashboard` → `wazuh-dashboard`

### 5. Removed Old Containers
Deleted containers with wrong path mounts to allow recreation with correct paths

## Current System Status

### ✓ Running Services

**Wazuh Stack (3 containers)**
- wazuh-indexer: Up and running
- wazuh-manager: Up and running (IP: 172.25.0.3)
- wazuh-dashboard: Up and running

**Wazuh Agents (23 containers total)**
- 14 dc-agent containers (dc-agent-001 through dc-agent-014)
- 9 named agent containers for honeypots and proxy

**DeceptiCloud Core Services**
- Port 9000: Routing Proxy [UP]
- Port 5000: ML API [UP]
- Port 8080: Dashboard [UP]
- Port 3001: Service [UP]
- Port 4001: Service [UP]

## How to Use

### Start System
```bash
./start_stop/decepticloud_control.sh start
```

### Stop System
```bash
./start_stop/decepticloud_control.sh stop
```

### Check Status
```bash
./start_stop/decepticloud_control.sh status
```

### Restart System
```bash
./start_stop/decepticloud_control.sh restart
```

## Access Points

- **Wazuh Dashboard**: http://localhost:5601
  - Username: admin
  - Password: SecretPassword (check wazuh/docker-compose.yml for exact password)

- **DeceptiCloud Dashboard**: http://localhost:8080

- **ML API Health**: http://localhost:5000/health

- **Routing Proxy**: http://localhost:9000

## Startup Sequence

1. **Wazuh Stack** (~30 seconds)
   - Indexer starts first
   - Manager starts and gets IP
   - Dashboard starts (may restart once during initialization)

2. **Agent Containers** (~20 seconds)
   - 14 dc-agent containers start
   - Connect to Wazuh Manager

3. **DeceptiCloud Services** (~15 seconds)
   - 14 website containers (7 real + 7 honeypot)
   - ML API service
   - Routing proxy
   - Dashboard
   - Adaptive Learning Engine
   - Log Ingestion Service

**Total startup time**: ~1-2 minutes

## Troubleshooting

### If Wazuh Dashboard keeps restarting
Wait 1-2 minutes - it's normal during first startup as it connects to the indexer

### If services don't start
```bash
# Check logs
tail -f logs/launch_v2.log

# Check Docker logs
docker logs wazuh-manager
docker logs wazuh-indexer
```

### If you move to another drive again
No action needed! The script now auto-detects the correct path.

### To completely reset
```bash
# Stop everything
./start_stop/decepticloud_control.sh stop

# Remove all containers
docker rm -f $(docker ps -aq | grep -E "wazuh|dc-agent")

# Start fresh
./start_stop/decepticloud_control.sh start
```

## Files Modified

1. `start_stop/decepticloud_control.sh` - Fixed paths and Docker Compose usage
2. `wazuh-docker/single-node/docker-compose.yml` - Added version field (though not used anymore)

## Benefits of the Fix

✓ **Portable**: Works on any drive/path
✓ **Reliable**: Uses validated docker-compose file
✓ **Compatible**: Works with Docker Compose v2
✓ **Maintainable**: No hardcoded paths to update
✓ **Resilient**: Survives system restarts and drive changes

## Next Steps

The system is now running and ready for:
- Jury presentation
- Attack demonstrations
- Dashboard monitoring
- ML model testing

All services are operational and the system will now start correctly after any restart or drive change.
