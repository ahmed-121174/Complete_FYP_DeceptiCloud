# DeceptiCloud + Wazuh - Startup Guide

## Quick Start

### Start the Complete System
```bash
./start_decepti_wazuh.sh
```

This single command will:
1. ✅ Start Wazuh Stack (3 Docker containers)
2. ✅ Start Adaptive Learning Engine
3. ✅ Start DeceptiCloud Dashboard
4. ✅ Perform health checks
5. ✅ Display access information

### Stop the Complete System
```bash
./stop_decepti_wazuh.sh
```

This will gracefully stop all components in the correct order.

---

## What Gets Started

### 1. Wazuh Stack (Docker)
- **Wazuh Indexer** (Port 9200) - Data storage
- **Wazuh Manager** (Port 55000) - Security monitoring
- **Wazuh Dashboard** (Port 5601) - Web interface

### 2. Adaptive Learning Engine
- Background process with 4 worker threads
- Polls Wazuh for alerts every 30 seconds
- Updates attacker profiles every 2 minutes
- Checks for model drift every 5 minutes
- Logs: `logs/adaptive_engine.log`

### 3. DeceptiCloud Dashboard
- Flask web application (Port 9000)
- Provides unified interface for all components
- Real-time API endpoints
- Logs: `logs/dashboard.log`

---

## Access Information

### DeceptiCloud Dashboard
- **URL**: http://localhost:9000
- **Username**: admin
- **Password**: DeceptiCloud

**Features**:
- Overview of all attacks
- Attacker fingerprints and profiles
- ML model performance metrics
- Adaptive engine status
- Real-time alerts

### Wazuh Dashboard
- **URL**: http://localhost:5601
- **Username**: admin
- **Password**: SecretPassword

**Features**:
- Security event monitoring
- Agent management
- Rule configuration
- Alert analysis

---

## Startup Process Details

### Phase 1: Wazuh Stack (30-45 seconds)
```
Starting Wazuh Docker containers...
Waiting for Wazuh Indexer to be healthy...
Waiting for services to initialize...
✓ Wazuh Stack is running
```

### Phase 2: Adaptive Engine (5 seconds)
```
Starting Adaptive Engine...
✓ Adaptive Engine started (PID: XXXXX)
✓ Engine state file created
```

### Phase 3: DeceptiCloud Dashboard (5 seconds)
```
Starting Dashboard...
✓ Dashboard started (PID: XXXXX)
✓ Dashboard listening on port 9000
```

### Phase 4: Health Check
```
✓ Wazuh Stack:        RUNNING (3/3 containers)
✓ Adaptive Engine:    RUNNING
✓ DeceptiCloud:       RUNNING
✓ Dashboard API:      RESPONDING
```

---

## Logs and Monitoring

### View Real-time Logs

**Dashboard logs**:
```bash
tail -f logs/dashboard.log
```

**Adaptive Engine logs**:
```bash
tail -f logs/adaptive_engine.log
```

**Wazuh Manager logs**:
```bash
docker logs -f single-node-wazuh.manager
```

**Wazuh Dashboard logs**:
```bash
docker logs -f single-node-wazuh.dashboard
```

### Check System Status

**All processes**:
```bash
ps aux | grep -E "(dashboard|adaptive_engine)" | grep python
```

**Docker containers**:
```bash
docker ps --filter "name=wazuh"
```

**Ports in use**:
```bash
lsof -i:9000,5601,9200,55000
```

---

## Troubleshooting

### Script Fails to Start

**Check prerequisites**:
```bash
# Virtual environment exists?
ls -la venv/

# Docker is running?
docker ps

# Correct directory?
ls dashboard/app.py adaptive_engine/engine.py
```

### Wazuh Fails to Start

**Check Docker**:
```bash
docker ps -a --filter "name=wazuh"
docker logs single-node-wazuh.indexer
```

**Restart Wazuh manually**:
```bash
cd wazuh-docker/single-node
docker compose down
docker compose up -d
cd ../..
```

### Dashboard Not Responding

**Check if running**:
```bash
ps aux | grep "dashboard/app.py"
cat logs/dashboard.log
```

**Restart manually**:
```bash
pkill -f "dashboard/app.py"
venv/bin/python3 dashboard/app.py > logs/dashboard.log 2>&1 &
```

### Adaptive Engine Not Running

**Check logs**:
```bash
cat logs/adaptive_engine.log
```

**Restart manually**:
```bash
pkill -f "adaptive_engine/engine.py"
venv/bin/python3 adaptive_engine/engine.py > logs/adaptive_engine.log 2>&1 &
```

### Port Already in Use

**Find what's using the port**:
```bash
lsof -i:9000  # Dashboard
lsof -i:5601  # Wazuh Dashboard
```

**Kill process on port**:
```bash
lsof -ti:9000 | xargs kill -9
```

---

## Advanced Usage

### Start Only Specific Components

**Only Wazuh**:
```bash
cd wazuh-docker/single-node
docker compose up -d
```

**Only Adaptive Engine**:
```bash
venv/bin/python3 adaptive_engine/engine.py > logs/adaptive_engine.log 2>&1 &
```

**Only Dashboard**:
```bash
venv/bin/python3 dashboard/app.py > logs/dashboard.log 2>&1 &
```

### Stop Only Specific Components

**Only Dashboard**:
```bash
pkill -f "dashboard/app.py"
```

**Only Adaptive Engine**:
```bash
pkill -f "adaptive_engine/engine.py"
```

**Only Wazuh**:
```bash
docker stop single-node-wazuh.dashboard single-node-wazuh.manager single-node-wazuh.indexer
```

---

## System Requirements

### Minimum
- **RAM**: 4GB
- **CPU**: 2 cores
- **Disk**: 10GB free space
- **OS**: Linux (Ubuntu 20.04+)

### Recommended
- **RAM**: 8GB
- **CPU**: 4 cores
- **Disk**: 20GB free space
- **OS**: Linux (Ubuntu 22.04+)

### Software Dependencies
- Python 3.8+
- Docker 20.10+
- Docker Compose 2.0+
- Virtual environment with all requirements installed

---

## Performance Notes

### Startup Times
- **Wazuh Stack**: 30-45 seconds
- **Adaptive Engine**: 5 seconds
- **Dashboard**: 5 seconds
- **Total**: ~45-60 seconds

### Resource Usage (Idle)
- **Wazuh Indexer**: ~1.5GB RAM
- **Wazuh Manager**: ~200MB RAM
- **Wazuh Dashboard**: ~200MB RAM
- **Adaptive Engine**: ~160MB RAM
- **DeceptiCloud Dashboard**: ~170MB RAM
- **Total**: ~2.2GB RAM

### API Response Times
- All endpoints: < 100ms
- No blocking or hanging
- Real-time updates

---

## Security Notes

### Default Credentials
⚠️ **Change these in production!**

**DeceptiCloud**:
- Username: admin
- Password: DeceptiCloud
- Location: `dashboard/app.py` (hardcoded for demo)

**Wazuh**:
- Username: admin
- Password: SecretPassword
- Location: Wazuh configuration files

### Network Exposure
By default, all services bind to `0.0.0.0` (all interfaces):
- Dashboard: 0.0.0.0:9000
- Wazuh Dashboard: 0.0.0.0:5601

For production, configure firewall rules or bind to localhost only.

---

## Data Persistence

### What Gets Saved
- **Database**: `database/decepticloud.db` (SQLite)
- **Engine State**: `adaptive_engine/engine_state.json`
- **Logs**: `logs/` directory
- **Wazuh Data**: Docker volumes

### What Gets Reset
- Process IDs (PIDs)
- In-memory caches
- Active connections

### Backup Important Data
```bash
# Backup database
cp database/decepticloud.db database/decepticloud.db.backup

# Backup logs
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/

# Backup Wazuh data
docker run --rm -v single-node-wazuh-indexer-data:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/wazuh_data_backup.tar.gz /data
```

---

## For Jury Presentation

### Pre-Presentation Checklist
1. ✅ Run `./start_decepti_wazuh.sh`
2. ✅ Wait for "All systems operational! 🎉"
3. ✅ Open http://localhost:9000 in browser
4. ✅ Verify all dashboard pages load
5. ✅ Open http://localhost:5601 in another tab
6. ✅ Have both tabs ready to demonstrate

### Demo Flow
1. Show DeceptiCloud Overview page (attack statistics)
2. Navigate to Fingerprints (13 profiles, 5 clusters)
3. Show ML Models page (84-89% accuracy)
4. Demonstrate Adaptive Engine page (real-time metrics)
5. Switch to Wazuh Dashboard (security monitoring)
6. Show integration between both systems

### If Something Goes Wrong
```bash
# Quick restart
./stop_decepti_wazuh.sh
sleep 5
./start_decepti_wazuh.sh
```

---

## Support

### Check System Health
```bash
./start_decepti_wazuh.sh  # Shows health check at end
```

### View All Logs
```bash
tail -f logs/*.log
```

### Complete Reset
```bash
./stop_decepti_wazuh.sh
pkill -9 -f "python.*(dashboard|adaptive_engine)"
docker stop $(docker ps -q --filter "name=wazuh")
./start_decepti_wazuh.sh
```

---

**Created**: 2026-04-18  
**Version**: 1.0  
**Status**: Production Ready ✅
