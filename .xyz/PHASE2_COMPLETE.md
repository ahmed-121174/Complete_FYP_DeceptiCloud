# Phase 2 — Adaptive Learning Engine ✅

**Date**: April 18, 2026 | **Tests**: 24/24 PASSED

---

## What Was Built

### 1. Wazuh Log Consumer (`adaptive_engine/core/wazuh_consumer.py`)
- Polls Wazuh OpenSearch indexer every 15s for new alerts
- Extracts 26 ML features from each alert (URL patterns, attack signatures, behavioral signals)
- Maps Wazuh rule IDs → attack types (SQLi, XSS, Brute Force, Port Scan, etc.)
- Stores raw alerts in `wazuh_alerts` table
- Stores extracted features in `training_data` table for retraining
- Cursor-based pagination — never re-processes the same alert

### 2. Drift Detector (`adaptive_engine/core/drift_detector.py`)
- Monitors live prediction confidence over a 6-hour sliding window
- Triggers retraining when:
  - Average confidence drops >10% below baseline
  - >25% of predictions fall in the uncertainty zone (0.40–0.60)
  - 200+ new training samples accumulate
- Generates full drift reports per model type

### 3. Continuous Retraining Pipeline (`adaptive_engine/pipeline/retraining_pipeline.py`)
- Pulls unused training data from DB per attack type
- Retrains with regularization (prevents overfitting)
- Compares new model vs current — only deploys if improved
- Archives previous model before deploying new one
- Calls `/api/reload-models` to hot-swap models in ML API (zero downtime)
- Full rollback support — restore any previous version

### 4. Behavioral Profiler (`adaptive_engine/behavioral/profiler.py`)
- Builds rich attacker profiles from attacks, Wazuh alerts, canary triggers
- Detects tools (sqlmap, nikto, hydra, masscan, etc.)
- Classifies timing patterns: burst / persistent / scheduled / sporadic
- Computes threat score (0–1) from 7 weighted behavioral signals
- K-means clustering across all profiles (5 clusters identified)
- Behavioral comparison: detects same attacker across different IPs (VPN/Tor pivoting)

### 5. Engine Orchestrator (`adaptive_engine/engine.py`)
- 4 background worker threads running concurrently:
  - Wazuh consumer (every 15s)
  - Drift detector (every 5 min)
  - Retraining pipeline (every 10 min)
  - Profile updater (every 2 min)
- Manual override: force retrain / rollback any model
- State persistence to `engine_state.json`

### 6. Dashboard API (`adaptive_engine/api/adaptive_api.py`)
7 new REST endpoints:
- `GET /api/adaptive/status` — engine status, counters
- `GET /api/adaptive/drift` — drift report per model
- `POST /api/adaptive/retrain` — manual retrain trigger
- `POST /api/adaptive/rollback` — model rollback
- `POST /api/adaptive/compare` — behavioral attacker comparison
- `GET /api/adaptive/clusters` — cluster summary
- `GET /api/adaptive/training-stats` — training data pipeline stats
- `GET /api/adaptive/wazuh-alerts` — live Wazuh alerts feed
- `GET /api/adaptive/model-history` — model version history
- `GET /api/adaptive/profiles` — enhanced attacker profiles

### 7. Dashboard UI (Adaptive Engine page)
Full page added to DeceptiCloud dashboard:
- Engine status cards (alerts ingested, retraining runs, profiles, drift events)
- Drift detection panel per model with confidence trends
- Training data pipeline stats by attack type
- Manual retrain/rollback controls for each model
- Model version history table
- Live Wazuh alerts feed with level filter
- Behavioral attacker comparison tool
- Attacker cluster visualization

---

## Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| DeceptiCloud Dashboard | http://localhost:9000 | admin / DeceptiCloud |
| → Adaptive Engine page | http://localhost:9000 → "🧠 Adaptive Engine" | — |
| Wazuh Dashboard | https://localhost:5601 | admin / SecretPassword1! |
| Wazuh Manager API | https://localhost:55000 | wazuh-wui / MyS3cr37P450r.*- |
| ML API | http://localhost:5000 | — |

---

## How Continuous Learning Works

```
Wazuh Alerts (every 15s)
    ↓
Feature Extraction (26 features per alert)
    ↓
training_data table (labeled by rule level + attack type)
    ↓
Drift Detector (every 5 min)
    ↓ if drift detected or 200+ new samples
Retraining Pipeline
    ↓ if new model improves accuracy
Archive old model → Deploy new model
    ↓
ML API hot-reload (zero downtime)
    ↓
Better detection on next attack
```

---

## Test Results: 24/24 PASSED

All Wazuh stack, ML API, Adaptive Engine, and Dashboard API tests passed.
