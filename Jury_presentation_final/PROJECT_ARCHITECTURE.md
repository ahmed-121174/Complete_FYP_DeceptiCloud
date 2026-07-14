# DeceptiCloud — Full System Architecture
## AI-Driven Cyber Deception System using Dynamic Honeypots in Cloud Environment

---

## System Overview

DeceptiCloud is a **cyber deception platform** that uses Artificial Intelligence to detect, deceive, and document cyber-attacks in real time. It deploys a network of dynamic honeypots — fake-but-convincing web applications — that intercept attackers, serve AI-generated deception content, and log all activity to a tamper-proof blockchain ledger.

```
ATTACKER
    │
    ▼
[Port 8080] ─── Routing Proxy (AI Gateway)
    │                     │
    │           ML Classification Engine
    │           ┌──────────────────────┐
    │           │ • Web Attack Model   │  ← Is this a SQLi? XSS? Scanner?
    │           │ • Rule-Based Engine  │  ← Payload pattern matching
    │           │ • Confidence Score   │  ← 0.0 – 1.0
    │           └──────────────────────┘
    │                     │
    ├── Benign? ──────────► Real Sites   (ports 3001–3007) → Normal response
    │
    └── Malicious? ────────► Honeypots  (ports 4001–4007) → AI Deception
                                  │
                            LLM Response Engine (Ollama)
                            Generates convincing fake error pages
                                  │
                            Blockchain Ledger  ← Tamper-proof attack log
                                  │
                            Dashboard  (port 9000) ← Real-time SOC view
```

---

## Module-by-Module Breakdown

### 1. ML API — `model_api.py` (Port 5000)
**Purpose:** Hosts two trained machine learning models as REST API endpoints.

**Models:**
| Model | Algorithm | Dataset | Accuracy |
|-------|-----------|---------|----------|
| DDoS Detection | Random Forest / Neural Net | CIC-DDoS2019 | 95.9% |
| Web Attack Detection | Gradient Boosting + Rules | Custom dataset | 93.97% BA |

**How it works:**
- `POST /api/predict/ddos` — receives traffic features, returns `{prediction, confidence, attack_type}`
- `POST /api/predict/web_attack` — receives HTTP features, returns attack classification
- `GET /api/health` — returns model load status and version info
- Both models are loaded into memory at startup from `ml_models/` directory

**In the demo:** The DDoS script sends live traffic metrics to this model. The routing proxy sends HTTP feature vectors for every incoming request.

---

### 2. Routing Proxy — `proxy/routing_proxy.py` (Port 8080)
**Purpose:** The **central AI gateway**. Every attacker request passes through here. This is the brain of DeceptiCloud.

**Processing pipeline for every request:**
```
Incoming HTTP Request
    │
    ├─ Feature Extraction (URL, method, headers, payload, user-agent)
    │
    ├─ Rule-Based Scoring (regex patterns for SQLi, XSS, traversal, CMDi)
    │
    ├─ ML Model Inference → Web Attack model scores the request
    │
    ├─ Confidence Score computed: is_malicious = score ≥ threshold
    │
    ├─ MALICIOUS? → Route to Honeypot (port 4001–4007)
    │                   │
    │                   ├─ Call LLM to generate deception HTML
    │                   ├─ Log to proxy_attacks.jsonl
    │                   └─ Log to blockchain
    │
    └─ BENIGN? → Route to Real Site (port 3001–3007)
                    Normal response served
```

**Key components:**
- `SITE_MAP` — maps URL prefix to (real_port, honeypot_port)
- `_classify_request()` — combined rule + ML scoring
- `generate_response()` — calls LLM for deception content
- `llm_stats` — persisted to `logs/llm_stats.json` (survives restarts)
- `ATTACK_LOG_FILE` — all attacks written to `proxy/logs/proxy_attacks.jsonl`

---

### 3. LLM Response Engine — `honeypot/llm_response_engine.py`
**Purpose:** Uses a local Large Language Model (Ollama) to generate **convincing, unique deception HTML pages** for each attacker.

**How it works:**
- When an attacker sends a SQLi payload → proxy asks LLM to generate a "fake SQL error page" with believable fake leaked data
- When attacker sends XSS → LLM generates a page that appears to reflect the XSS (fooling the attacker into thinking it worked)
- When attacker sends path traversal → LLM generates fake `/etc/passwd` content
- Responses are **cached** (same attack type → same cached response for speed)
- Falls back to static templates if Ollama is unavailable

**Jury-visible result:** The attacker gets back a completely convincing fake response. They think they've compromised the system.

---

### 4. Dynamic Honeypots — `websites/` (Ports 4001–4007)
**Purpose:** Seven full Flask web applications that look identical to the real sites but are instrumented traps.

**Seven honeypots:**
| Port | Name | Theme |
|------|------|-------|
| 4001 | SecureBank Honeypot | Banking/Finance |
| 4002 | ShopEase Honeypot | E-commerce |
| 4003 | MedCore Honeypot | Healthcare |
| 4004 | TechBlog Honeypot | Blog/CMS |
| 4005 | DataAPI Honeypot | REST API |
| 4006 | NexaGen Corp Honeypot | Corporate Site |
| 4007 | AdminPanel Honeypot | Admin Interface |

**What makes them "dynamic":**
- GAN-generated synthetic user profiles in each SQLite database (`*_honeypot.db`)
- Canary tokens embedded in responses (URLs, emails, tokens — triggers when clicked)
- Behavioral fingerprinting — tracks attacker patterns across requests
- All activity logged to blockchain

**GAN Synthetic Data:** `gan_data_generator.py` uses CTGAN to generate 35 realistic but fake user profiles per honeypot. These appear as real data to attackers but cannot harm real users.

---

### 5. Real Sites — `websites/` (Ports 3001–3007)
**Purpose:** Identical-looking Flask applications serving legitimate users.

**Key difference from honeypots:**
- No canary tokens
- Real (or empty) SQLite databases  
- Not instrumented for attack logging
- **Protected by the proxy** — attackers never reach these

During DDoS demo: The **real site (:3006) stays UP** while the honeypot (:4006) crashes. Real users are unaffected.

---

### 6. Blockchain Ledger — `honeypot/blockchain_ledger.py`
**Purpose:** Provides **tamper-proof, immutable logging** of every attack event.

**How it works:**
- Each attack logged as a `Block` with SHA-256 hash of `(index, timestamp, attack_data, previous_hash)`
- Chain stored as JSON list in `honeypot/attack_chain.json`
- Genesis block created at system startup
- `verify_chain()` walks the chain and validates every hash link
- Any tampering with a block invalidates all subsequent blocks

**Jury verification:** Dashboard shows "Chain integrity verified — no tampering detected" by running `verify_chain()` on every API call.

---

### 7. GAN Data Generator — `gan_data_generator.py`
**Purpose:** Generates synthetic but realistic user profiles for honeypot databases using a Generative Adversarial Network.

**Model:** CTGAN (Conditional Tabular GAN) trained on schema patterns
**Output:** 35 users per honeypot with realistic names, account numbers, balances, emails
**Watermark:** Every GAN-generated record has `balance` field with 7 as last decimal digit (detectable, not visible to attackers)

---

### 8. Dashboard — `dashboard/app.py` (Port 9000)
**Purpose:** Real-time Security Operations Center (SOC) web interface for monitoring all system activity.

**Panels and data sources:**

| Panel | API Endpoint | Data Source |
|-------|-------------|-------------|
| Overview Stats | `/api/stats` | `proxy_attacks.jsonl` + proxy memory |
| Attack Analysis | `/api/attacks` | `proxy_attacks.jsonl` |
| Infrastructure Health | `/api/infrastructure` | Live port polls (all 17 services) |
| LLM Response Engine | `/api/phase2-stats` | `logs/llm_stats.json` |
| GAN Synthetic Identities | `/api/phase2-stats` | SQLite `*_honeypot.db` |
| Behavioral Fingerprints | `/api/fingerprints` | `proxy_attacks.jsonl` by IP |
| Blockchain Ledger | `/api/blockchain` | `honeypot/attack_chain.json` |
| Canary Tokens | `/api/canary` | `logs/canary_triggers.jsonl` |
| Honeypot Manager | `/api/honeypots` | Live honeypot API polls |

**Infrastructure Health Panel** (new): Polls all 17 service ports every 3 seconds and shows UP/DOWN status with response time. During DDoS demo, the Corporate Honeypot (:4006) shows as **DOWN** in red, then switches to **UP** (green) when K8s watchdog restarts it.

---

### 9. K8s Auto-Recovery Watchdog — `attacks/ddos_attack.sh`
**Purpose:** Simulates a **Kubernetes ReplicaSet controller** that monitors honeypot health and auto-restarts failed pods.

**How it works:**
1. DDoS attack script starts a watchdog background loop
2. Watchdog polls the honeypot port every 2 seconds
3. If port goes DOWN → watchdog spawns a new Flask process for that site
4. Watchdog confirms recovery by re-polling the port
5. Dashboard infrastructure panel shows the DOWN → UP transition in real time

**What this demonstrates to the jury:** Cloud-native resilience (Kubernetes-style auto-healing), ensuring the deception layer stays operational even under sustained DDoS attack.

---

### 10. Attack Scripts — `attacks/`
**Purpose:** Red-team simulation tools that demonstrate the system working against real attack patterns.

| Script | Location | What it does |
|--------|----------|-------------|
| `web_attacks.sh` | `attacks/` | Fires 16 HTTP attacks (SQLi, XSS, Path Traversal, CMD Injection) through proxy; 100% detected |
| `ddos_attack.sh` | `attacks/` | 4-wave DDoS flood targeting corporate honeypot (:4006); site crashes, K8s restarts it |

**Note:** The attack scripts = simulated red team (attacker). The detection, routing, logging, deception = real blue team (defender). This is standard security research practice.

---

## Data Flow Diagram

```
Attack Flow:
  curl -A "sqlmap/1.7" http://localhost:8080/banking/search?q=UNION+SELECT...
           │
           ▼
    [Routing Proxy :8080]
    1. Extract features (UA, URL, payload, method)
    2. Rule score: SQLI_PATTERNS match → score += 0.5
    3. Scanner UA "sqlmap" → score += 0.7 → total = 1.0 → MALICIOUS
    4. Route to Banking Honeypot :4001
    5. Call LLM → generate fake "SQL error" page
    6. Return fake page to attacker ← attacker thinks they won
    7. Log to proxy_attacks.jsonl
    8. Log to blockchain (SHA-256 hash chain)
    9. Dashboard updates in 3s

Benign Flow:
  curl http://localhost:8080/banking/account
           │
           ▼
    [Routing Proxy :8080]
    1. Extract features
    2. Rule score: no patterns → score = 0.0 → BENIGN
    3. Route to Real Banking Site :3001
    4. Normal response served
    (Not logged as attack)
```

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| ML Models | scikit-learn, pandas, numpy |
| LLM | Ollama (local, no cloud dependency) |
| GAN | CTGAN (tabular synthetic data) |
| Web Framework | Flask (Python) |
| Proxy | Flask + threading + concurrent.futures |
| Blockchain | Python (custom SHA-256 chain) |
| Databases | SQLite (per honeypot) |
| Dashboard Frontend | HTML/CSS/JavaScript |
| Containerization | Docker (Dockerfiles in `docker/`) |
| Orchestration | Kubernetes-style watchdog (bash + Python) |
| Attack Simulation | bash + curl |

---

## Execution Order for Jury

```bash
cd "/media/amei-302/New Volume1/SEMESTER VIII/Ahmed Fype-II"

# [Terminal 1] Start all 17 services
bash Jury_presentation_final/scripts/1_START_SYSTEM.sh
# → Opens dashboard at http://localhost:9000 automatically

# [Terminal 2] Web attack demo
bash Jury_presentation_final/scripts/2_WEB_ATTACKS.sh
# → Shows 100% detection rate, 16/16 attacks caught

# [Terminal 3] DDoS + K8s recovery demo
bash Jury_presentation_final/scripts/3_DDOS_ATTACK.sh low
# → Corporate Honeypot :4006 crashes → K8s restarts it
# → Dashboard Infrastructure panel shows the transition

# [Stop all]
bash Jury_presentation_final/scripts/STOP_ALL.sh
```

---

## Key Metrics (Jury Day)

| Metric | Value |
|--------|-------|
| Attacks Detected | 200+ |
| Honeypot Events | = Attacks Detected |
| Avg Detection Confidence | 93-94% |
| Detection Rate | 100% |
| Blockchain Blocks | 380+ (tamper-proof) |
| System Health | 16/16 services UP |
| GAN Users per Honeypot | 35 synthetic profiles |
| LLM Success Rate | 99%+ |
