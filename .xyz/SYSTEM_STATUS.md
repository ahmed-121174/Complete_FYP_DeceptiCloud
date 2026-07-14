# DeceptiCloud + Wazuh System Status

## 🟢 System Overview

| Component | Status | Port | URL |
|-----------|--------|------|-----|
| **Wazuh Indexer** | ✅ Running (Healthy) | 9200 | https://localhost:9200 |
| **Wazuh Manager** | ✅ Running + API Active | 55000 | https://localhost:55000 |
| **Wazuh Dashboard** | ✅ Running (HTTP) | 5601 | http://localhost:5601 |
| **DeceptiCloud Dashboard** | ✅ Running | 9000 | http://localhost:9000 |
| **ML Detection API** | ✅ Running | 5000 | http://localhost:5000 |
| **Routing Proxy** | ✅ Running | 8080 | http://localhost:8080 |
| **Real Websites** | ✅ Running | 3001-3007 | http://localhost:3001-3007 |
| **Honeypots** | ✅ Running | 4001-4007 | http://localhost:4001-4007 |

---

## 🔐 Credentials

### Wazuh Dashboard
```
URL: http://localhost:5601
Username: admin
Password: SecretPassword1!
```

### DeceptiCloud Dashboard
```
URL: http://localhost:9000
Username: admin
Password: DeceptiCloud
```

---

## 🐛 Issues Fixed

### ✅ Issue #1: Cluster Count Discrepancy
**Problem**: Overview showed 12 clusters, Fingerprints showed 2 clusters  
**Root Cause**: Different data sources (file vs database)  
**Fix**: Unified both to use database DBSCAN cluster count  
**Result**: Both now show 5 clusters consistently

### ✅ Issue #2: ML Models Not Showing
**Problem**: 5 out of 7 models showed "NaN%"  
**Root Cause**: Backend only returned 2 models, frontend expected 7  
**Fix**: Added placeholder data for untrained models  
**Result**: All 7 models now display (2 trained, 5 pending)

---

## 🚀 How to Start/Stop System

### Start Everything
```bash
bash start_decepticloud.sh
```

This script:
1. Starts Wazuh Docker stack (indexer → manager → dashboard)
2. Waits for Wazuh to be healthy
3. Applies custom DeceptiCloud rules/decoders
4. Starts DeceptiCloud platform (all services)
5. Starts Wazuh log ingestion bridge

### Stop Everything
```bash
bash stop_decepticloud.sh
```

This script:
1. Stops all DeceptiCloud processes
2. Stops Wazuh Docker containers
3. Cleans up PID files

---

## 📊 Current System Metrics

### Attacker Profiles
- **Total Profiles**: 13
- **Behavioral Clusters**: 5 (via DBSCAN)
- **High Risk Profiles**: Varies by threat score

### ML Models
| Model | Status | Accuracy |
|-------|--------|----------|
| Web Attack Detector V2 | ✅ Trained | 93.97% |
| DDoS Detector V1 | ✅ Trained | 95.88% |
| XSS Detector | ⏳ Pending | - |
| Brute Force Detector | ⏳ Pending | - |
| Port Scan Detector | ⏳ Pending | - |
| Credential Stuffing Detector | ⏳ Pending | - |
| Anomaly Detector | ⏳ Pending | - |

### Phase 2 Features
- **LLM Responses**: 248 requests, 242 successful (97.6%)
- **GAN Synthetic Data**: 35 users (100% synthetic)
- **Behavioral Fingerprints**: 13 profiles, 5 clusters

---

## 🔧 Wazuh Configuration

### Custom Rules & Decoders
- **Location**: `wazuh/custom_rules.xml`, `wazuh/custom_decoders.xml`
- **Status**: ✅ Applied to manager
- **Rules**: 20+ custom detection rules for DeceptiCloud attacks
- **Decoders**: 10+ custom decoders for attack parsing

### Fixed Issues
1. ✅ Regex syntax errors in decoders (removed problematic characters)
2. ✅ Frequency rule errors (added proper if_matched_sid structure)
3. ✅ Dashboard SSL disabled for local HTTP access

---

## 📁 Project Structure

```
DeceptiCloud/
├── dashboard/              # Flask dashboard (port 9000)
│   ├── app.py             # Main dashboard backend
│   ├── static/            # CSS, JS, images
│   └── templates/         # HTML templates
├── ml_pipeline/           # ML models and training
│   ├── model_api.py       # ML API server (port 5000)
│   └── models/            # Trained model files
├── proxy/                 # Routing proxy (port 8080)
│   └── routing_proxy.py   # Traffic classifier & router
├── websites/              # 14 websites (7 real + 7 honeypot)
│   └── run_all.py         # Website launcher
├── database/              # SQLite database
│   ├── db_service.py      # Database service layer
│   └── decepticloud.db    # Main database
├── wazuh/                 # Wazuh integration
│   ├── custom_rules.xml   # Custom detection rules
│   ├── custom_decoders.xml # Custom log decoders
│   └── log_ingestion_service.py # Wazuh → DB bridge
├── wazuh-docker/          # Wazuh Docker stack
│   └── single-node/       # Single-node deployment
├── start_decepticloud.sh  # ✨ Unified start script
├── stop_decepticloud.sh   # ✨ Unified stop script
└── launch_decepticloud_v2.py # DeceptiCloud launcher
```

---

## 🧪 Testing

### Run Attack Simulations
```bash
# Web attacks (SQLi, XSS, etc.)
bash attacks/web_attacks.sh

# DDoS simulation
bash attacks/ddos_attack.sh
```

### Check System Health
```bash
# DeceptiCloud health
curl http://localhost:9000/api/system-health

# ML API health
curl http://localhost:5000/api/health

# Wazuh API health
curl -sk -u "wazuh-wui:MyS3cr37P450r.*-" -X POST \
  https://localhost:55000/security/user/authenticate
```

---

## 📝 Logs

### DeceptiCloud Logs
```bash
# Dashboard
tail -f logs/dashboard.log

# ML API
tail -f logs/ml_api.log

# Proxy
tail -f logs/proxy.log

# Launch logs
tail -f logs/launch/decepticloud.log
```

### Wazuh Logs
```bash
# Manager logs
sg docker -c "docker logs single-node-wazuh.manager"

# Dashboard logs
sg docker -c "docker logs single-node-wazuh.dashboard"

# Indexer logs
sg docker -c "docker logs single-node-wazuh.indexer"
```

---

## 🎯 Key Features Working

### ✅ Attack Detection & Routing
- ML-based classification (Web Attack + DDoS)
- Rule-based detection (SQLi, XSS, Traversal, CMDi)
- Scanner detection (sqlmap, nikto, nmap, etc.)
- Automatic routing to honeypots

### ✅ Attacker Profiling
- Behavioral fingerprinting
- DBSCAN clustering (5 clusters from 13 profiles)
- Threat scoring
- Session tracking

### ✅ Deception Layer
- 7 honeypot clones (identical to real sites)
- GAN-generated synthetic data
- LLM-powered adaptive responses
- Canary tokens

### ✅ Monitoring & Analytics
- Real-time dashboard
- Attack timeline visualization
- Infrastructure health monitoring
- Blockchain attack ledger

### ✅ SIEM Integration
- Wazuh manager + indexer + dashboard
- Custom rules for DeceptiCloud attacks
- Log ingestion bridge (DeceptiCloud → Wazuh)
- Alert correlation

---

## 🔍 Known Limitations

1. **5 ML Models Pending Training**: XSS, Brute Force, Port Scan, Credential Stuffing, Anomaly detectors not yet trained
2. **Wazuh Agents Not Deployed**: No agents on honeypot/real site containers yet
3. **SSL Disabled on Wazuh Dashboard**: For local dev convenience (should enable for production)

---

## 📚 Documentation

- **Full System Docs**: `README_COMPLETE_SYSTEM.md`
- **Quick Start**: `QUICKSTART.md`
- **Issues Analysis**: `ISSUES_ANALYSIS_AND_FIXES.md`
- **Fixes Applied**: `FIXES_APPLIED.md`
- **Build Plan**: `DECEPTICLOUD_BUILD_PLAN.md`

---

**Last Updated**: 2026-04-18  
**System Version**: v2.0  
**Status**: ✅ Fully Operational
