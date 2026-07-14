# DeceptiCloud Startup Fix Applied

## Issues Fixed

### 1. Hardcoded Path Issue
**Problem**: Script had hardcoded path `/media/amei-302/New Volume1/` but system is on `/media/amei-302/New Volume2/`

**Solution**: Changed to auto-detect project root from script location:
```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
```

### 2. Docker Compose Version Compatibility
**Problem**: Script used `docker-compose` (v1) but system may have v2 (`docker compose`)

**Solution**: Added auto-detection for both versions:
```bash
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
fi
```

### 3. Permission Issues
**Problem**: Permission denied errors when writing to logs/pids

**Solution**: Auto-detection ensures paths are relative to current location, not hardcoded

## How to Start the System

```bash
# From project root
./start_stop/decepticloud_control.sh start
```

## What Gets Started

1. **Wazuh Docker Stack** (3 containers)
   - wazuh.indexer (port 9200)
   - wazuh.manager (ports 1514, 1515, 514, 55000)
   - wazuh.dashboard (port 5601)

2. **14 Wazuh Agent Containers**
   - dc-agent-001 through dc-agent-014
   - 7 real sites + 7 honeypot sites

3. **DeceptiCloud Services**
   - 14 Website containers (real + honeypot)
   - ML API (port 5000)
   - Routing Proxy (port 9000)
   - Dashboard (port 8080)
   - Adaptive Learning Engine
   - Log Ingestion Service

## Troubleshooting

If you still see errors:

1. **Check Docker is running**:
   ```bash
   docker ps
   ```

2. **Check certificates exist**:
   ```bash
   ls -la wazuh-docker/single-node/config/wazuh_indexer_ssl_certs/
   ```

3. **View logs**:
   ```bash
   tail -f logs/launch_v2.log
   ```

4. **Check system status**:
   ```bash
   ./start_stop/decepticloud_control.sh status
   ```

5. **Stop everything and restart**:
   ```bash
   ./start_stop/decepticloud_control.sh stop
   ./start_stop/decepticloud_control.sh start
   ```

## Expected Startup Time

- Wazuh stack: ~30 seconds
- Agents: ~20 seconds
- DeceptiCloud services: ~15 seconds
- **Total**: ~1-2 minutes for full system

## Verification

After startup, check:
- Wazuh Dashboard: http://localhost:5601
- DeceptiCloud Dashboard: http://localhost:8080
- ML API: http://localhost:5000/health
- Proxy: http://localhost:9000

## Notes

- The script now works regardless of which "Volume" you're on
- All paths are dynamically detected
- Compatible with both docker-compose v1 and v2
