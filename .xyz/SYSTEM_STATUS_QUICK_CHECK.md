# DeceptiCloud System Status - Quick Check Guide

## ✅ SYSTEM FULLY OPERATIONAL

### Current Running Services

#### 1. Wazuh Stack (Docker)
```bash
# Check status
docker ps --filter "name=wazuh"

# Expected output: 3 containers running
# - single-node-wazuh.indexer (port 9200) - HEALTHY
# - single-node-wazuh.manager (port 55000) - UP
# - single-node-wazuh.dashboard (port 5601) - UP
```

#### 2. Adaptive Engine (Background Process)
```bash
# Check if running
ps aux | grep "adaptive_engine/engine.py" | grep -v grep

# Expected: One process running
# PID: 105464 (or similar)
# Status: Running since 19:44
```

#### 3. DeceptiCloud Dashboard (Port 9000)
```bash
# Check if running
ps aux | grep "dashboard/app.py" | grep -v grep

# Expected: One process running
# PID: 111463 (or similar)
# Listening on: http://localhost:9000
```

### Access URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| DeceptiCloud Dashboard | http://localhost:9000 | admin / DeceptiCloud |
| Wazuh Dashboard | http://localhost:5601 | admin / SecretPassword |
| Wazuh Manager API | http://localhost:55000 | (API token required) |
| Wazuh Indexer | http://localhost:9200 | (internal use) |

### Quick Health Check Commands

```bash
# 1. Check all services
curl -s http://localhost:9000/api/system-health | python3 -m json.tool

# 2. Check Adaptive Engine status
curl -s -c /tmp/cookies.txt -X POST http://localhost:9000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"DeceptiCloud"}' && \
curl -s -b /tmp/cookies.txt http://localhost:9000/api/adaptive/status | python3 -m json.tool

# 3. Check Wazuh alerts
curl -s -b /tmp/cookies.txt http://localhost:9000/api/adaptive/wazuh-alerts?limit=5 | python3 -m json.tool

# 4. Check attacker clusters
curl -s -b /tmp/cookies.txt http://localhost:9000/api/adaptive/clusters | python3 -m json.tool
```

### Current Data Status

| Metric | Count | Status |
|--------|-------|--------|
| Wazuh Alerts | 20 | ✅ Ingested |
| Training Samples | 11 | ✅ Available |
| Attacker Profiles | 13 | ✅ Updated |
| Behavioral Clusters | 5 | ✅ Active |
| Unprocessed Alerts | 20 | ⏳ Pending classification |

### Adaptive Engine Activity

The engine is running with 4 worker threads:

1. **Wazuh Consumer** - Polls Wazuh API every 30s for new alerts
2. **Drift Detector** - Checks for model drift every 5 minutes
3. **Retraining Worker** - Automatically retrains models when drift detected
4. **Profile Updater** - Updates attacker profiles every 2 minutes using DBSCAN clustering

**Last Activity:**
- Started: 2026-04-18 14:44:53
- Last Profile Update: 2026-04-18 15:11:26
- Last Drift Check: 2026-04-18 15:09:53
- Alerts Ingested: 1
- Profiles Updated: 13

### Dashboard Pages Status

| Page | Status | Notes |
|------|--------|-------|
| Overview | ✅ Working | Shows 13 profiles, 5 clusters |
| Fingerprints | ✅ Working | Shows 13 profiles, 5 clusters (fixed) |
| ML Models | ✅ Working | Shows real accuracy (84-89%) |
| Adaptive Engine | ✅ Working | All endpoints responding |
| Wazuh Dashboard | ✅ Working | Accessible at port 5601 |

### Troubleshooting

#### If Dashboard Not Responding
```bash
# Restart dashboard
pkill -f "dashboard/app.py"
venv/bin/python3 dashboard/app.py > /tmp/dashboard.log 2>&1 &
```

#### If Adaptive Engine Stopped
```bash
# Restart engine
pkill -f "adaptive_engine/engine.py"
venv/bin/python3 adaptive_engine/engine.py > /tmp/engine.log 2>&1 &
```

#### If Wazuh Containers Down
```bash
# Restart Wazuh stack
cd wazuh-docker/single-node
docker compose down
docker compose up -d
```

### Start All Services (One Command)

```bash
# Use the existing start script
./start_decepticloud.sh
```

### Stop All Services

```bash
# Use the existing stop script
./stop_decepticloud.sh
```

## Recent Fixes Applied

1. ✅ **Cluster Count Discrepancy** - Fixed inconsistency between Overview and Fingerprints pages
2. ✅ **ML Models Accuracy** - Fixed 0.0% display, now showing real accuracy (84-89%)
3. ✅ **Wazuh Dashboard** - Fixed "Application Not Found" error, now accessible
4. ✅ **Adaptive Engine API Deadlock** - Fixed 20-minute hang, all endpoints now respond in < 1 second

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DeceptiCloud Platform                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │
│  │   Wazuh      │─────▶│  Adaptive    │─────▶│ Dashboard │ │
│  │   Stack      │      │   Engine     │      │  (Flask)  │ │
│  │              │      │              │      │           │ │
│  │ • Indexer    │      │ • Consumer   │      │ Port 9000 │ │
│  │ • Manager    │      │ • Detector   │      │           │ │
│  │ • Dashboard  │      │ • Retrainer  │      │           │ │
│  └──────────────┘      │ • Profiler   │      └───────────┘ │
│   Ports: 9200,         └──────────────┘                     │
│   55000, 5601               ▲                                │
│                             │                                │
│                      ┌──────┴──────┐                        │
│                      │   SQLite    │                        │
│                      │  Database   │                        │
│                      └─────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

## Next Steps

1. **Access the dashboards** using the URLs above
2. **Verify Adaptive Engine page** shows real-time data
3. **Run attack simulations** to generate more data (optional)
4. **Monitor continuous operation** - engine updates automatically

---

**Last Updated:** 2026-04-18 20:12:00
**System Status:** ✅ FULLY OPERATIONAL
