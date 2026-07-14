# DECEPTICLOUD — FULL SYSTEM BUILD PLAN

## 📋 SYSTEM AUDIT RESULTS

### ✅ EXISTING COMPONENTS (WORKING)
1. **ML Models** (DO NOT OVERWRITE)
   - Web Attack Detector V2: `ml_pipeline/models/web_attack_detector_v2.keras`
   - DDoS Detector V1: `DDoS/V1/models/best_model.pkl`
   - SQL Injection models in `V2-SQLI-XSS-NoSQLi/models/`
   
2. **Frontend Dashboard** (EXTEND, DON'T REBUILD)
   - Flask backend: `dashboard/app.py` (port 9000)
   - Frontend: `dashboard/static/dashboard.js`, `dashboard.css`
   - Templates: `dashboard/templates/dashboard.html`
   
3. **Routing Proxy** (EXTEND)
   - `proxy/routing_proxy.py` (port 8080)
   - Already has ML integration and routing logic
   
4. **Honeypot Infrastructure** (EXTEND)
   - 7 honeypot sites: `websites/*_honeypot/` (ports 4001-4007)
   - 7 real sites: `websites/*/` (ports 3001-3007)
   - GAN data generator: `honeypot/gan_data_generator.py`
   - LLM engine: `honeypot/llm_response_engine.py`
   - Blockchain: `honeypot/blockchain_ledger.py`
   
5. **ML API** (WORKING)
   - `ml_pipeline/model_api.py` (port 5000)
   
6. **Launch System**
   - `launch_decepticloud.py` - orchestrates all services

### ❌ MISSING COMPONENTS (TO BUILD)

1. **Wazuh Integration** (PHASE 1)
   - No Wazuh manager installed
   - No Wazuh agents configured
   - No custom rules/decoders
   - No log ingestion service from Wazuh to backend
   
2. **Database Layer** (ALL PHASES)
   - No PostgreSQL/MongoDB for persistent storage
   - Currently using JSONL files and SQLite
   - Need centralized DB for: attacks, profiles, fingerprints, events
   
3. **Additional ML Models** (PHASE 4)
   - Brute Force Detector
   - Port Scan Detector
   - XSS Detector (separate from web attack)
   - Credential Stuffing Detector
   - Behavioral Anomaly Detector
   
4. **Adaptive Learning Engine** (PHASE 5)
   - Continuous learning pipeline
   - Behavioral comparison system
   - Model retraining automation
   
5. **Enhanced Fingerprinting** (PHASE 6)
   - JA3/JA3S TLS fingerprinting
   - Canvas fingerprinting
   - Advanced clustering (DBSCAN/K-Means)
   - Attacker profile pages
   
6. **Dashboard Pages** (PHASE 7)
   - Attack History Page (new)
   - Attacker Profiles Page (new)
   - Enhanced Fingerprints Page
   - Enhanced Honeypot Management Page
   - Remove Canary Token Page

## 🎯 BUILD STRATEGY

### APPROACH
- **Incremental Enhancement**: Build on existing infrastructure
- **Database-First**: Establish PostgreSQL as central data store
- **Wazuh Integration**: Add Wazuh as log aggregation layer
- **ML Pipeline Extension**: Add new detection models
- **Dashboard Enhancement**: Add missing pages and features

### TECHNOLOGY STACK
- **Database**: PostgreSQL (primary), SQLite (honeypot local)
- **Backend**: Python/Flask
- **ML**: TensorFlow, scikit-learn, XGBoost
- **SIEM**: Wazuh (to be installed)
- **Containerization**: Docker (existing Dockerfiles)
- **Orchestration**: Kubernetes-style watchdog (existing)

## 📐 IMPLEMENTATION PHASES

### PHASE 0: DATABASE SETUP (NEW)
**Priority**: CRITICAL - Foundation for all other phases

1. Install PostgreSQL
2. Create database schema:
   - `attacks` table (all attack events)
   - `attacker_profiles` table (fingerprints, clusters)
   - `sessions` table (attacker sessions)
   - `events` table (system events)
   - `models` table (ML model versions)
   - `training_data` table (for adaptive learning)
3. Create database service layer: `database/db_service.py`
4. Migrate existing JSONL data to PostgreSQL
5. Update proxy to write to PostgreSQL
6. Update dashboard to read from PostgreSQL

### PHASE 1: WAZUH INSTALLATION & CONFIGURATION
**Dependencies**: Phase 0 complete

1.1 **Install Wazuh Manager**
   - Install Wazuh 4.x on system
   - Configure `ossec.conf`
   - Enable Wazuh API (port 55000)
   - Start services

1.2 **Deploy Wazuh Agents**
   - Install agents on 14 nodes (or simulate)
   - Enroll with manager
   - Configure log forwarding

1.3 **Custom Rules & Decoders**
   - Create rules for: SQLi, XSS, DDoS, brute force, port scan
   - Set alert levels
   - Configure webhooks

1.4 **Log Ingestion Service**
   - Build `wazuh/log_ingestion_service.py`
   - Poll Wazuh API for alerts
   - Parse and normalize
   - Store in PostgreSQL
   - Emit WebSocket events to dashboard

### PHASE 2: HONEYPOT INFRASTRUCTURE ENHANCEMENT
**Dependencies**: Phase 0 complete

2.1 **Enhance Existing Honeypots**
   - Add comprehensive logging
   - Integrate with Wazuh agents
   - Add canary token embedding

2.2 **SSH Honeypot**
   - Deploy Cowrie SSH honeypot
   - Configure logging
   - Integrate with Wazuh

2.3 **Canary Token System**
   - Enhance existing `honeypot/canary_tokens.py`
   - Integrate alerts into main feed (not separate page)

### PHASE 3: INTELLIGENT ROUTING PROXY ENHANCEMENT
**Dependencies**: Phase 0, Phase 1 complete

3.1 **Enhanced Proxy**
   - Add JA3 TLS fingerprinting
   - Add geolocation lookup
   - Improve routing decision logic
   - Add routing rules editor API

3.2 **Honeypot Management API**
   - Add endpoints for honeypot control
   - Add routing rules management
   - Add live session tracking

3.3 **Dashboard Honeypot Management Page**
   - Build new page in dashboard
   - Show all honeypots with status
   - Show routing rules
   - Show active sessions

### PHASE 4: ML DETECTION PIPELINE EXPANSION
**Dependencies**: Phase 0 complete

4.1 **Integrate Existing Models**
   - Wire SQL Injection model into proxy
   - Wire DDoS model into proxy
   - Add model versioning

4.2 **Build Additional Models**
   - Brute Force Detector (rate + ML)
   - Port Scan Detector (sequence analysis)
   - XSS Detector (pattern + ML)
   - Credential Stuffing Detector
   - Behavioral Anomaly Detector

4.3 **Unified ML API**
   - Extend `ml_pipeline/model_api.py`
   - Add endpoints for all models
   - Add async processing
   - Add fallback logic

### PHASE 5: ADAPTIVE LEARNING ENGINE
**Dependencies**: Phase 0, Phase 4 complete

5.1 **Continuous Learning Pipeline**
   - Build `adaptive_learning/learning_engine.py`
   - Implement incremental learning
   - Add model retraining automation
   - Add model versioning and rollback

5.2 **Behavioral Comparison System**
   - Extract behavioral features in real-time
   - Compare against attacker profiles
   - Implement similarity scoring
   - Add auto-flagging logic

5.3 **Adaptive Engine Status API**
   - Add endpoints for engine status
   - Integrate with dashboard

### PHASE 6: ATTACKER FINGERPRINTING & PROFILING
**Dependencies**: Phase 0 complete

6.1 **Enhanced Fingerprint Collection**
   - Add JA3/JA3S TLS fingerprinting
   - Add HTTP header fingerprinting
   - Add canvas fingerprinting (if JS executes)
   - Add behavioral fingerprinting
   - Add tool detection

6.2 **Attacker Clustering**
   - Implement DBSCAN clustering
   - Implement K-Means clustering
   - Dynamic cluster computation
   - Unified data source for all views

6.3 **Attacker Profile System**
   - Build profile database schema
   - Build profile API endpoints
   - Build profile pages in dashboard

### PHASE 7: DASHBOARD & FRONTEND ENHANCEMENT
**Dependencies**: All previous phases

7.1 **Fix Existing Pages**
   - Fix cluster count consistency (Overview vs Fingerprints)
   - Remove hardcoded data
   - Use real database queries

7.2 **New Pages**
   - Attack History Page (table with filters, export)
   - Attacker Profiles Page (list + detail view)
   - Enhanced Fingerprints Page (fix cluster count)
   - Honeypot Management Page (from Phase 3)

7.3 **Remove Canary Token Page**
   - Remove from navigation
   - Remove routes
   - Integrate alerts into main feed

7.4 **Pipeline Monitor Enhancement**
   - Add real health checks
   - Remove timer-based counters
   - Add component status indicators

### PHASE 8: ATTACK SIMULATION & TESTING
**Dependencies**: All phases complete

8.1 **Comprehensive Attack Suite**
   - SQL Injection (SQLmap)
   - DDoS (hping3/slowloris)
   - Brute Force (Hydra)
   - Port Scan (Nmap)
   - XSS (manual payloads)
   - Credential Stuffing (Burp/custom)
   - MITM simulation

8.2 **End-to-End Validation**
   - Validate each attack type
   - Verify routing decisions
   - Verify logging
   - Verify dashboard updates
   - Verify adaptive learning

### PHASE 9: DATA PERSISTENCE & RECOVERY
**Dependencies**: Phase 0 complete

9.1 **Data Retention**
   - Implement data retention policies
   - Add data export functionality
   - Add backup automation

9.2 **System Recovery**
   - Ensure state restoration on restart
   - Verify no hardcoded state
   - Test full system restart

## 🚀 EXECUTION ORDER

1. **Phase 0**: Database Setup (CRITICAL PATH)
2. **Phase 1**: Wazuh Installation
3. **Phase 4**: ML Pipeline (can run parallel with Phase 1)
4. **Phase 6**: Fingerprinting (can run parallel with Phase 1)
5. **Phase 2**: Honeypot Enhancement
6. **Phase 3**: Proxy Enhancement
7. **Phase 5**: Adaptive Learning
8. **Phase 7**: Dashboard Enhancement
9. **Phase 8**: Testing
10. **Phase 9**: Data Persistence

## 📊 ESTIMATED TIMELINE

- Phase 0: 2-3 hours
- Phase 1: 4-6 hours
- Phase 2: 2-3 hours
- Phase 3: 3-4 hours
- Phase 4: 6-8 hours
- Phase 5: 4-6 hours
- Phase 6: 4-5 hours
- Phase 7: 4-6 hours
- Phase 8: 2-3 hours
- Phase 9: 2-3 hours

**Total**: 33-47 hours

## 🔧 CONFIGURATION TRACKING

All configurations will be documented in: `SYSTEM_CONFIG.md`

Including:
- Service ports
- API endpoints
- Database schemas
- File paths
- Credentials
- Model versions
