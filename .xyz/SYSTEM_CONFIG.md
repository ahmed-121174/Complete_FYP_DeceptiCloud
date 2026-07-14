# DECEPTICLOUD — SYSTEM CONFIGURATION

## 🔧 SERVICE PORTS

| Service | Port | Type | Status |
|---------|------|------|--------|
| ML API | 5000 | Core | ✅ Working |
| Routing Proxy | 8080 | Core | ✅ Working |
| Dashboard | 9000 | Core | ✅ Working |
| Banking (Real) | 3001 | Real Site | ✅ Working |
| E-commerce (Real) | 3002 | Real Site | ✅ Working |
| Healthcare (Real) | 3003 | Real Site | ✅ Working |
| Blog (Real) | 3004 | Real Site | ✅ Working |
| API Service (Real) | 3005 | Real Site | ✅ Working |
| Corporate (Real) | 3006 | Real Site | ✅ Working |
| Admin Panel (Real) | 3007 | Real Site | ✅ Working |
| Banking (Honeypot) | 4001 | Honeypot | ✅ Working |
| E-commerce (Honeypot) | 4002 | Honeypot | ✅ Working |
| Healthcare (Honeypot) | 4003 | Honeypot | ✅ Working |
| Blog (Honeypot) | 4004 | Honeypot | ✅ Working |
| API Service (Honeypot) | 4005 | Honeypot | ✅ Working |
| Corporate (Honeypot) | 4006 | Honeypot | ✅ Working |
| Admin Panel (Honeypot) | 4007 | Honeypot | ✅ Working |
| Wazuh Manager | 1514 | SIEM | ⚠️ Optional |
| Wazuh API | 55000 | SIEM | ⚠️ Optional |

## 📁 FILE PATHS

### Configuration
- Main config: `config.py`
- Database: `database/decepticloud.db`
- Database schema: `database/schema.sql`

### Logs
- Attack log (JSONL): `proxy/logs/proxy_attacks.jsonl`
- LLM stats: `proxy/logs/llm_stats.json`
- Blockchain: `logs/attack_chain.json`
- Canary triggers: `logs/canary_triggers.jsonl`
- Honeypot events: `logs/honeypot_events.jsonl`

### ML Models
- Web Attack V2: `ml_pipeline/models/web_attack_detector_v2.keras`
- Web Attack Scaler: `ml_pipeline/models/web_attack_preprocessor_scaler.pkl`
- DDoS V1: `DDoS/V1/models/best_model.pkl`
- DDoS Scaler: `DDoS/V1/models/scaler.pkl`
- DDoS Features: `DDoS/V1/models/selected_features.pkl`

### Wazuh
- Custom rules: `wazuh/custom_rules.xml` → `/var/ossec/etc/rules/local_rules.xml`
- Custom decoders: `wazuh/custom_decoders.xml` → `/var/ossec/etc/decoders/local_decoder.xml`
- Wazuh config: `/var/ossec/etc/ossec.conf`

## 🔐 CREDENTIALS

### Dashboard
- Username: `admin`
- Password: `DeceptiCloud`
- Session key: `decepticloud-session-key-change-in-prod`

### Proxy API
- API Key: `decepti-internal-api-key`

### Wazuh (if installed)
- Username: `wazuh`
- Password: `wazuh` (change after installation)

## 🎯 API ENDPOINTS

### ML API (Port 5000)
- `GET /api/health` - Health check
- `POST /api/detect/web` - Web attack detection
- `POST /api/detect/ddos` - DDoS detection
- `GET /api/model-info` - Model metadata

### Routing Proxy (Port 8080)
- `GET /<site>/<path>` - Main routing endpoint
- `GET /proxy/status` - Proxy status and stats
- `GET /proxy/attacks` - Recent attacks
- `GET /proxy/missed-attacks` - Benign requests log
- `GET /proxy/classify` - Debug classification endpoint
- `POST /proxy/config` - Update proxy configuration

### Dashboard (Port 9000)
- `POST /api/login` - User login
- `POST /api/logout` - User logout
- `GET /api/me` - Current user info
- `GET /api/stats` - Attack statistics
- `GET /api/attacks` - Recent attacks
- `GET /api/system-health` - System health check
- `GET /api/infrastructure` - Infrastructure status
- `GET /api/phase2-stats` - LLM, GAN, fingerprint stats
- `GET /api/blockchain` - Blockchain ledger
- `GET /api/canary` - Canary token stats
- `GET /api/fingerprints` - Attacker fingerprints
- `GET /api/model-info` - ML model information
- `GET /api/settings` - Dashboard settings
- `POST /api/settings` - Update settings

### Wazuh API (Port 55000, if installed)
- `GET /security/user/authenticate` - Get JWT token
- `GET /alerts` - Get alerts
- `GET /agents` - Get agent list

## 🗄️ DATABASE SCHEMA

### Tables
1. **attacks** - All detected attacks
2. **attacker_profiles** - Fingerprints and behavioral profiles
3. **sessions** - Individual attacker sessions
4. **events** - System events and logs
5. **ml_models** - ML model versions and performance
6. **training_data** - Data for adaptive learning
7. **wazuh_alerts** - Alerts from Wazuh SIEM
8. **honeypot_events** - Detailed honeypot interactions
9. **canary_tokens** - Canary token definitions
10. **canary_triggers** - Canary token triggers
11. **routing_rules** - Dynamic routing configuration
12. **system_health** - Component health over time

## 🚀 STARTUP SEQUENCE

### Automatic (Recommended)
```bash
python3 launch_decepticloud.py
```

### Manual
```bash
# 1. Start ML API
python3 ml_pipeline/model_api.py &

# 2. Start all websites (14 processes)
python3 websites/run_all.py &

# 3. Start routing proxy
python3 proxy/routing_proxy.py &

# 4. Start dashboard
python3 dashboard/app.py &

# 5. (Optional) Start Wazuh log ingestion
python3 wazuh/log_ingestion_service.py &
```

## 🔍 DETECTION THRESHOLDS

### Rule-Based Scoring
- High threshold: `0.5`
- Low threshold: `0.3`

### ML Confidence
- Threshold: `0.7` (70%)
- High confidence: `≥ 0.85` (85%)
- Critical confidence: `≥ 0.95` (95%)

### Rate Limiting
- Default: `200/minute`
- Login endpoints: `5/minute`
- ML API: `100/minute`

## 📊 ML MODEL SPECIFICATIONS

### Web Attack Detector V2
- **Architecture**: ANN/MLP (128 → 64 → 1)
- **Input features**: 23
- **Output**: Binary (Attack/Benign)
- **Attack types**: SQLi, NoSQLi, XSS, Path Traversal, CMDi
- **Accuracy**: 93.97%
- **Precision**: 92%
- **Recall**: 95%
- **F1 Score**: 93%

### DDoS Detector V1
- **Architecture**: Random Forest (100 trees)
- **Input features**: 30 (CIC-DDoS2019)
- **Output**: Binary (Attack/Benign)
- **Attack types**: SYN Flood, DNS Amp, UDP Flood, NTP Amp, LDAP Amp, MSSQL Amp, NetBIOS Amp, SNMP Amp, SSDP Amp, UDP Lag
- **Accuracy**: 95.88%
- **Precision**: 94.81%
- **Recall**: 96.90%
- **F1 Score**: 95.99%

## 🎨 FEATURE ENGINEERING

### Web Attack Features (23)
1. url_length
2. path_length
3. query_length
4. fragment_length
5. num_params
6. param_value_length
7. has_ip_address
8. num_special_chars
9. has_encoded_chars
10. num_path_segments
11. has_file_extension
12. content_length
13. num_headers
14. has_cookie
15. has_auth_header
16. has_user_agent
17. is_post
18. is_put
19. is_delete
20. sqli_score
21. xss_score
22. traversal_score
23. (scanner detection)

## 🔄 HONEYPOT ROTATION

- **Interval**: 60 seconds (configurable)
- **Default site**: banking
- **Rotation enabled**: Yes
- **Sites in rotation**: All 7 honeypots

## 🧠 LLM CONFIGURATION

- **Model**: gemma3:1b (777MB)
- **Timeout**: 90 seconds
- **Max tokens**: 300
- **Cache enabled**: Yes
- **Fallback**: Dynamic honeypot pages

## 🔗 GAN CONFIGURATION

- **Watermark decimal**: 7 (last digit of balance)
- **Watermark ratio**: 30%
- **Default epochs**: 2000
- **Mode collapse check**: Every 200 epochs
- **Mode collapse threshold**: 0.01 std

## 📈 SYSTEM REQUIREMENTS

### Minimum
- CPU: 4 cores
- RAM: 8 GB
- Disk: 20 GB
- OS: Ubuntu 20.04+ / Debian 11+

### Recommended
- CPU: 8 cores
- RAM: 16 GB
- Disk: 50 GB
- OS: Ubuntu 22.04 LTS

## 🛠️ DEPENDENCIES

See `xyz/requirements.txt` for Python packages:
- tensorflow==2.20.0
- pandas==3.0.0
- numpy==2.4.2
- scikit-learn==1.8.0
- Flask==3.1.2
- flask-cors==6.0.2
- requests==2.32.5

## 🔧 ENVIRONMENT VARIABLES

All configurable via environment variables (see `config.py`):
- `ML_API_PORT` (default: 5000)
- `PROXY_PORT` (default: 8080)
- `DASHBOARD_PORT` (default: 9000)
- `REAL_SITE_BASE_PORT` (default: 3001)
- `HONEYPOT_SITE_BASE_PORT` (default: 4001)
- `ML_CONFIDENCE` (default: 0.7)
- `ROTATION_INTERVAL` (default: 60)

## 📝 LOGGING LEVELS

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages (potential issues)
- **ERROR**: Error messages (failures)
- **CRITICAL**: Critical errors (system failures)

## 🔐 SECURITY NOTES

1. **Change default credentials** in production
2. **Enable HTTPS** for all services
3. **Configure firewall** rules
4. **Regular backups** of database
5. **Monitor disk space** for logs
6. **Update dependencies** regularly
7. **Review Wazuh alerts** daily

## 📞 SUPPORT

For issues or questions:
1. Check logs in `logs/` directory
2. Review `DECEPTICLOUD_BUILD_PLAN.md`
3. Check component-specific READMEs
4. Review system health in dashboard
