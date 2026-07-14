# DeceptiCloud v2.0 — Complete Project Architecture
> **AI-Driven Cyber Deception System for Cloud Infrastructures**  
> FYP-II | Department of Computer Science

---

## 🗺️ System Overview

DeceptiCloud is a **honeypot-based intrusion deception system** that:
1. Intercepts ALL incoming HTTP traffic via a **Routing Proxy**
2. Uses an **ML pipeline** to classify each request as benign or malicious
3. Routes malicious traffic to **honeypot clones** of real web services
4. The attacker sees a realistic fake site full of **GAN-generated fake data**
5. An **LLM** further personalises the response to the attacker's payload
6. Every attack is written to an immutable **blockchain ledger**
7. The **dashboard** gives the defender a real-time command centre view

```
INTERNET ─► ROUTING PROXY :8080 ─► ML classify ─► REAL site :3001-3007
                                                └──► HONEYPOT :4001-4007
                                                        └──► LLM response or GAN data
```

---

## 📁 Root Directory Layout

```
/Ahmed Fype-II/
├── config.py                   ← Single source of truth for all constants
├── launch_decepticloud.py      ← Master launcher (starts all 16 services)
├── requirements.txt            ← Python dependencies
│
├── proxy/                      ← Phase 1: Traffic interception + ML routing
│   ├── routing_proxy.py        ← Main proxy server (Flask, port 8080)
│   └── logs/
│       ├── proxy_attacks.jsonl ← Attack log (every captured attack)
│       └── benign_requests.jsonl ← Benign request log (missed attacks)
│
├── ml_pipeline/                ← Phase 1: ML attack detection
│   ├── model_api.py            ← REST API wrapper for both models (port 5000)
│   ├── models/
│   │   ├── web_attack_detector_v2.keras      ← ANN model weights
│   │   └── web_attack_preprocessor_scaler.pkl← Feature scaler
│   ├── train_model.py          ← Training script for web attack model
│   ├── retrain_honest.py       ← Retraining with calibration
│   └── predict.py              ← Direct inference helper
│
├── DDoS/V1/                    ← Phase 1: DDoS detection
│   └── models/
│       ├── best_model.pkl      ← Random Forest model
│       ├── scaler.pkl          ← Feature scaler
│       └── selected_features.pkl ← 30 CIC-DDoS2019 features
│
├── honeypot/                   ← Phase 2: Deception layer
│   ├── blockchain_ledger.py    ← SHA-256 linked attack evidence chain
│   └── llm_response_engine.py ← Ollama LLM adaptive response engine
│
├── websites/                   ← 7 real + 7 honeypot web apps
│   ├── banking/                ← Real banking site (Flask, port 3001)
│   ├── ecommerce/              ← Real e-commerce site (port 3002)
│   ├── healthcare/             ← Real healthcare site (port 3003)
│   ├── blog/                   ← Real blog site (port 3004)
│   ├── api_service/            ← Real API service (port 3005)
│   ├── corporate/              ← Real corporate site (port 3006)
│   ├── admin_panel/            ← Real admin panel (port 3007)
│   ├── banking_honeypot/       ← Fake banking site (port 4001) ← attackers land here
│   ├── ecommerce_honeypot/     ← Fake e-commerce (port 4002)
│   ├── healthcare_honeypot/    ← Fake healthcare (port 4003)
│   ├── blog_honeypot/          ← Fake blog (port 4004)
│   ├── api_service_honeypot/   ← Fake API service (port 4005)
│   ├── corporate_honeypot/     ← Fake corporate (port 4006)
│   ├── admin_panel_honeypot/   ← Fake admin panel (port 4007)
│   └── databases/
│       ├── banking_honeypot.db         ← GAN-generated fake users
│       ├── ecommerce_honeypot.db
│       ├── healthcare_honeypot.db
│       ├── blog_honeypot.db
│       ├── api_service_honeypot.db
│       ├── corporate_honeypot.db
│       └── admin_panel_honeypot.db
│
├── dashboard/                  ← Defender command centre (port 9000)
│   ├── app.py                  ← Flask backend for dashboard
│   ├── templates/
│   │   └── dashboard.html      ← Single-page app shell
│   └── static/
│       ├── dashboard.js        ← Frontend logic (fetch + render)
│       └── dashboard.css       ← Dark-mode styling
│
├── attacks/                    ← Attack simulation scripts
│   ├── web_attacks.sh          ← 16 web attack types via curl
│   └── ddos_attack.sh          ← DDoS flood simulation
│
└── JURY_PRESENTATION/
    ├── 1_START_SYSTEM.sh       ← Launch all 16 services
    ├── 2_WEB_ATTACKS.sh        ← All web attack demos
    ├── 3_DDOS_ATTACK.sh        ← DDoS + crash + K8s restart
    ├── 4_NARRATED_DEMO.sh      ← Full 7-phase narrated demo
    ├── STOP_ALL.sh             ← Kill everything
    └── JURY_GUIDE.md           ← Step-by-step jury procedure
```

---

## 🔧 Module-by-Module Reference

---

### 1. `config.py` — Central Configuration
**Path:** `config.py`  
**Purpose:** Single source of truth for all ports, credentials, thresholds, and constants.

| Constant | Value | Purpose |
|----------|-------|---------|
| `SITE_MAP` | dict | Maps site names to real:honeypot port pairs |
| `ML_CONFIDENCE_THRESHOLD` | 0.5 | Score above which a request is flagged malicious |
| `GAN_WATERMARK_DECIMAL` | 7 | Last digit watermark in balance to prove GAN origin |
| `ML_API_URL` | http://localhost:5000 | ML API endpoint |
| `DASHBOARD_SECRET_KEY` | – | JWT/session secret |
| `RATE_LIMIT_DEFAULT` | "200/minute" | Flask-Limiter default |

**Integrates with:** every module (imported everywhere)

---

### 2. `launch_decepticloud.py` — Master Launcher
**Path:** `launch_decepticloud.py`  
**Purpose:** Starts all 16 services in correct order using subprocess, writes PIDs to `/tmp/`.

**Startup order:**
1. ML API (`model_api.py`, port 5000)
2. All 7 real websites (ports 3001–3007)
3. All 7 honeypot websites (ports 4001–4007)
4. Routing Proxy (`routing_proxy.py`, port 8080)
5. Dashboard (`dashboard/app.py`, port 9000)

**Integrates with:** all modules (orchestrator)

---

### 3. `proxy/routing_proxy.py` — Traffic Routing Engine
**Path:** `proxy/routing_proxy.py`  
**Port:** 8080  
**Purpose:** Every HTTP request from the internet enters here first.

**Flow for each request:**
```
Request → extract_features() → classify_request() via ML API
       → is_malicious?
           YES → route_to_honeypot(:4001-4007) + log_attack() + LLM response
           NO  → route_to_real_site(:3001-3007) + log_benign_with_reason()
```

**Key functions:**

| Function | Purpose |
|----------|---------|
| `extract_features(req)` | Builds 22-feature vector from HTTP request |
| `classify_request(features)` | Calls ML API → returns `{is_malicious, confidence, attack_types, routed_to}` |
| `proxy_to_site(site_name, path)` | Main routing handler — decision + forward |
| `log_attack(req, classification, target)` | Logs to JSONL, increments counters, calls blockchain |
| `log_benign_with_reason(req, cls, target, reason)` | Logs why a request was NOT flagged |
| `_llm_is_enabled()` | Lazy-checks Ollama every 60s — auto-enables if Ollama starts late |

**Key endpoints:**

| Endpoint | Purpose |
|----------|---------|
| `GET /<site>/<path>` | Main proxy — routes all traffic |
| `GET /proxy/status` | Health + LLM stats + rotation state |
| `GET /proxy/attacks` | Recent attack log entries |
| `GET /proxy/missed-attacks` | Benign requests log (missed attacks) |
| `GET /proxy/classify` | Debug endpoint — classify a single request |

**Integrates with:** ML API (classify), LLM engine (generate_response), blockchain (log_to_blockchain), honeypot sites (forward traffic)

---

### 4. `ml_pipeline/model_api.py` — ML Inference API
**Path:** `ml_pipeline/model_api.py`  
**Port:** 5000  
**Purpose:** REST wrapper around the two ML models — accepts feature vectors, returns classification.

**Endpoints:**

| Endpoint | Input | Output |
|----------|-------|--------|
| `GET /api/health` | – | `{status, models:{web_attack, ddos}}` |
| `POST /api/detect/web` | 22 features JSON | `{is_malicious, confidence, attack_type, attack_types[]}` |
| `POST /api/detect/ddos` | 30 flow features | `{is_ddos, confidence, attack_type}` |

**Models loaded:**

| Model | File | Architecture | Training Data |
|-------|------|-------------|---------------|
| Web Attack V2 | `models/web_attack_detector_v2.keras` | ANN: 22→128→64→1 sigmoid | CIC-IDS2017 + custom SQLi/XSS/NoSQLi |
| DDoS V1 | `DDoS/V1/models/best_model.pkl` | Random Forest 100 trees | CIC-DDoS2019 |

**22 Web Attack Features:**
- URL component lengths (path, query, domain)
- Special character counts (apostrophe, angle brackets, semicolons...)
- HTTP method encoding
- User-agent scanner flags (sqlmap, Burp, Hydra, nikto, ZAP)
- Pattern booleans (SQLi keywords, script tags, traversal `../`)

**Integrates with:** Routing Proxy (called on every request), Dashboard (health check)

---

### 5. `honeypot/llm_response_engine.py` — LLM Adaptive Response
**Path:** `honeypot/llm_response_engine.py`  
**Purpose:** Uses Ollama (gemma3:1b, 777MB) to generate unique, context-aware HTML responses tailored to each attacker's specific payload.

**How it works (no hardcoding):**
```
Attack arrives at proxy → generate_response(attack_type, payload, site)
    ├─ Cache HIT?  → return cached HTML instantly ✅ (SUCCESS++)
    └─ Cache MISS? → queue background thread generation
                     return None (proxy falls through to dynamic honeypot)
                     [60-90s later on CPU]
                     cache populated with LLM-generated HTML
                     NEXT attack of same type → cache HIT → SUCCESS++
```

**Warm-up:** At startup (once only via `_warmup_done` flag), pre-generates responses for:
- SQLi `q=1' UNION SELECT username,password FROM users--` → banking
- XSS `q=<script>alert(document.cookie)</script>` → ecommerce  
- CMDi `exec=ls -la /etc; cat /etc/passwd` → admin_panel

**Payloads match exact proxy format** (includes `q=` prefix from `unquote(query_string)`)

**Key config:**
```python
MODEL_NAME  = "gemma3:1b"   # CPU-friendly
TIMEOUT     = 90.0          # 90s — generous for CPU inference
NUM_PREDICT = 300           # tokens — fast but rich HTML
```

**Integrates with:** Routing Proxy (generate_response called per attack), Dashboard (LLM stats via /proxy/status)

---

### 6. `honeypot/blockchain_ledger.py` — Attack Evidence Chain
**Path:** `honeypot/blockchain_ledger.py`  
**Purpose:** Every captured attack gets a blockchain block — SHA-256 linked, tamper-evident.

**Block structure:**
```json
{
  "index": 184,
  "timestamp": "2026-02-26T00:32:15",
  "data": { "ip":"127.0.0.1", "attack_type":"SQLi", "target":"banking_honeypot" },
  "previous_hash": "00aaa4e731c344...",
  "nonce": 194,
  "hash": "0023c5e9af56ec..."
}
```

**Proof of Work:** Hash must start with `00` (two leading zeros) — demonstrates mining concept.

**Integrates with:** Routing Proxy (log_to_blockchain on every attack), Dashboard (Blockchain Ledger page)

---

### 7. `websites/<name>_honeypot/` — Honeypot Web Apps (×7)
**Paths:** `websites/banking_honeypot/`, `ecommerce_honeypot/`, etc.  
**Ports:** 4001–4007  
**Purpose:** Convincing fake replicas of real sites, pre-loaded with GAN-generated fake users.

**What makes them dynamic:**
- Full Flask web apps with routes, templates, login forms
- SQLite DBs seeded with 5 GAN-generated fake users per site
- Fake accounts have GAN watermark: `CAST(balance*100 AS INT) % 10 = 7`
- Banking honeypot exposes `/api/users` — returns fake user JSON
- Every interaction (login attempt, search, form submit) is logged

**GAN watermark example:**
```sql
admin   balance=250000.07  → int(25000007) % 10 = 7 ✅ SYNTHETIC
cfo_linda balance=180000.07 → int(18000007) % 10 = 7 ✅ SYNTHETIC
```

**Integrates with:** Routing Proxy (attackers forwarded here), Dashboard (honeypot status), LLM Engine (fallback target when LLM cache not ready)

---

### 8. `dashboard/app.py` — Defender Dashboard Backend
**Path:** `dashboard/app.py`  
**Port:** 9000  
**Purpose:** Flask backend that aggregates data from all services and serves the React-style dashboard.

**Key API endpoints:**

| Endpoint | Returns |
|----------|---------|
| `POST /api/login` | Session token (admin/DeceptiCloud) |
| `GET /api/stats` | Overview: total attacks, confidence, rotation site |
| `GET /api/attacks` | Recent 50 attacks from proxy log |
| `GET /api/phase2-stats` | LLM stats + GAN synthetic % + fingerprint clusters |
| `GET /api/system-health` | Status of all 16 services |
| `GET /api/blockchain` | All blockchain blocks + chain validity |
| `GET /api/ml-models` | Both model info + accuracy metrics |
| `GET /api/canary-tokens` | Triggered canary token list |
| `GET /api/fingerprints` | DBSCAN attacker clusters |

**Integrates with:** Proxy (reads JSONL logs + /proxy/status), ML API (health), Blockchain, all honeypot DBs (GAN %), all websites (health)

---

### 9. `dashboard/static/dashboard.js` — Dashboard Frontend
**Path:** `dashboard/static/dashboard.js`  
**Purpose:** Single-page app — polls backend every 5 seconds, renders all panels.

**Pages rendered:**
- **Overview:** Attack count, confidence sparkline, 16 service tiles, top threat actors
- **Attack Analysis:** Paginated attack log with colour-coded attack type badges
- **Honeypot Mgmt:** 7 real↔honeypot port pairs, rotation timer
- **ML Models:** Both models with accuracy gauges
- **Blockchain:** Block list with hashes, chain verification status
- **Phase 2 (AI Analytics):** LLM Engine box (requests/success/fallback), GAN %, Fingerprint clusters
- **Canary Tokens:** API key exposure detection
- **Fingerprints:** DBSCAN attacker behavioral clusters

**Integrates with:** Dashboard backend (all `/api/*` endpoints via fetch)

---

## 🔗 Integration Map

```
config.py ──────────────────────────────────────► ALL modules

launch_decepticloud.py ──► starts ──► ml_pipeline/model_api.py      :5000
                                   ├─► websites/<real>/              :3001-3007
                                   ├─► websites/<name>_honeypot/     :4001-4007
                                   ├─► proxy/routing_proxy.py        :8080
                                   └─► dashboard/app.py              :9000

proxy/routing_proxy.py
  ├─► ml_pipeline/model_api.py        (POST /api/detect/web — classify every request)
  ├─► honeypot/blockchain_ledger.py   (log_to_blockchain — every captured attack)
  ├─► honeypot/llm_response_engine.py (generate_response — dynamic HTML for attacker)
  ├─► websites/<real>/                (forward benign traffic here)
  └─► websites/<name>_honeypot/       (forward malicious traffic here)

dashboard/app.py
  ├─► proxy/routing_proxy.py          (GET /proxy/status, /proxy/attacks)
  ├─► ml_pipeline/model_api.py        (GET /api/health)
  ├─► honeypot/blockchain_ledger.py   (read chain)
  ├─► websites/databases/*_honeypot.db (GAN user count + watermark check)
  ├─► websites/<all_16>/              (health polls)
  └─► dashboard/static/dashboard.js  (serves the frontend)
```

---

## 🤔 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Proxy-first architecture** | All traffic enters through ONE point → zero false negatives on routing |
| **Honeypot instead of blocking** | Deception: attacker believes they succeeded → wastes their time + reveals TTPs |
| **GAN for fake users** | Static fake data is detectable; GAN data has realistic distributions |
| **LLM for dynamic responses** | Every unique payload gets a unique "leaked data" response — attacker can't fingerprint |
| **Async LLM** | LLM inference on CPU takes 60-90s; async prevents blocking Flask request threads |
| **Blockchain** | Immutable tamper-evident log — evidence admissible in legal/compliance scenarios |
| **DBSCAN fingerprinting** | Unsupervised clustering of attacker behaviour — detects coordinated campaigns |

---

## 📊 Performance Summary

| Component | Metric | Value |
|-----------|--------|-------|
| Web Attack Model | Accuracy | 94.0% |
| Web Attack Model | Precision | 92.0% |
| Web Attack Model | Recall | 95.0% |
| DDoS Model | Accuracy | 99.9% |
| DDoS Model | Precision | 99.8% |
| DDoS Model | F1 Score | 100.0% |
| System Throughput | Requests/sec | ~50 (single-core) |
| LLM Response Time | First response | 60–90s (CPU) |
| LLM Cache Hit | Subsequent responses | <10ms |
| Honeypots Active | Count | 7 |
| GAN Users | Total | 35 (100% synthetic) |
| Blockchain Blocks | As of demo | 187+ |

---

## 🚨 What Attackers See vs What's Real

| Attacker Action | What Attacker Sees | What's Actually Happening |
|----------------|-------------------|--------------------------|
| Browse banking site | Convincing SecureBank with real UI | Honeypot at :4001 |
| SQLi dump | "Leaked" users: admin, cfo_linda, david.k | GAN fake users, watermarked |
| SQLi (2nd+ attempt) | Unique HTML table from AI | gemma3:1b generated on-device |
| Login with stolen creds | "Welcome, admin" | Honeypot captured credential |
| XSS reflected | Script tag reflected in search results | Honeypot — no real users at risk |
| DDoS flood | Site goes down briefly | K8s auto-restarts in <10s |
| Recon of `/etc/passwd` | Realistic fake passwd entries | LLM-generated CMDi response |
