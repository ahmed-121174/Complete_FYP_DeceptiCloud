# DeceptiCloud — Complete Jury Presentation Guide
> **FYP-II | AI-Driven Cyber Deception System for Cloud Infrastructures**
> Department of Computer Science | 2026

---

## ⚡ JURY DAY — EXACT STEPS (Read This First)

### Step 0: Always Start Fresh
```bash
cd "/media/amei-302/New Volume/SEMESTER VIII/Ahmed Fype-II"
bash JURY_PRESENTATION/STOP_ALL.sh          # kill everything from yesterday
bash JURY_PRESENTATION/1_START_SYSTEM.sh    # single clean launch (all 16 services)
```
Wait for the green "✅ ALL SYSTEMS ONLINE" banner (~60s).

### Step 1: Give your intro speech (~2 minutes)
While you talk, the LLM warm-up is generating cached SQLi/XSS/CMDi responses in the background.
By the time you finish the introduction, the LLM cache is ready.

### Step 2: Open browser at http://localhost:9000
- Login: `admin` / `DeceptiCloud`
- Show Overview page (stats: attack counts, confidence, 16/16 services)

### Step 3: Run Web Attacks (Terminal 2)
```bash
bash JURY_PRESENTATION/2_WEB_ATTACKS.sh
```
Show dashboard updating live — attack feed fills up.

### Step 4: Run Full Narrated Demo (Terminal 3)
```bash
bash JURY_PRESENTATION/4_NARRATED_DEMO.sh
```
This walks through all 7 phases with pauses — press ENTER between each.

### Step 5: DDoS Attack (Terminal 4)
```bash
bash JURY_PRESENTATION/3_DDOS_ATTACK.sh low
```
Watch corporate:3006 crash and K8s restart it live.

### Stop All
```bash
bash JURY_PRESENTATION/STOP_ALL.sh
```

---

## 🌐 Service Map — All 16 Services

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| **ML API** | 5000 | http://localhost:5000 | ANN web attack + RF DDoS models |
| **Routing Proxy** | 8080 | http://localhost:8080 | All traffic enters here first |
| **Dashboard** | 9000 | http://localhost:9000 | Jury command center |
| Banking (Real) | 3001 | http://localhost:3001 | Real site |
| E-commerce (Real) | 3002 | http://localhost:3002 | Real site |
| Healthcare (Real) | 3003 | http://localhost:3003 | Real site |
| Blog (Real) | 3004 | http://localhost:3004 | Real site |
| API Service (Real) | 3005 | http://localhost:3005 | Real site |
| Corporate (Real) | 3006 | http://localhost:3006 | DDoS target |
| Admin Panel (Real) | 3007 | http://localhost:3007 | Real site |
| Banking 🍯 | 4001 | http://localhost:4001 | Honeypot — fake GAN users |
| E-commerce 🍯 | 4002 | http://localhost:4002 | Honeypot |
| Healthcare 🍯 | 4003 | http://localhost:4003 | Honeypot |
| Blog 🍯 | 4004 | http://localhost:4004 | Honeypot |
| API Service 🍯 | 4005 | http://localhost:4005 | Honeypot |
| Corporate 🍯 | 4006 | http://localhost:4006 | Honeypot |
| Admin Panel 🍯 | 4007 | http://localhost:4007 | Honeypot |

---

## 🔴 LIVE ATTACKS FOR JURY (If They Ask)

### Live SQLi Attack
```bash
# Attacker's payload — open this URL in browser or curl:
curl -s -A "sqlmap/1.7" \
  "http://localhost:8080/banking/search?q=1'+UNION+SELECT+username,password+FROM+users--" \
  | grep -i "table\|user\|admin" | head -5
```
**What happens:** Proxy detects `sqlmap` user-agent → 100% confidence → routes to Banking Honeypot :4001
**Attacker sees:** Fake GAN-generated user table (admin, cfo_linda, david.k...)
**Real banking site :3001:** Never touched ✅

### Live XSS Attack
```bash
curl -s -A "Burp Suite" \
  "http://localhost:8080/ecommerce/search?q=<script>alert(document.cookie)</script>"
```
**What happens:** Burp Suite UA → scanner detected → 90% confidence → E-commerce Honeypot :4002
**Attacker sees:** Reflected XSS in honeypot (safe—no real users affected)

### Live Command Injection
```bash
curl -s -A "nikto/2.14" \
  "http://localhost:8080/admin_panel/cmd?exec=ls+-la+/etc"
```
**What happens:** nikto scanner + CMDi pattern → 100% confidence → Admin Honeypot :4007
**Attacker sees:** Fake `/etc/passwd` contents from the LLM-generated response

### Live Brute Force
```bash
for pass in admin password admin123 root 123456; do
  curl -s -A "Hydra v9.4" -X POST \
    -d "username=admin&password=$pass" \
    "http://localhost:8080/banking/login" | grep -i "welcome\|invalid" | head -1
  sleep 0.5
done
```
All credentials captured by honeypot — 0 real accounts compromised.

### Live DDoS + K8s Restart
```bash
# Crash corporate site :3006 live (30s flood + kill + restart):
bash JURY_PRESENTATION/3_DDOS_ATTACK.sh low
```
**Wave 3:** Site crashes. **Wave 4:** K8s restarts it in <10s.
**DDoS ML model:** 99.9% accuracy on CIC-DDoS2019 (30 flow features, Random Forest)

### Live NoSQLi Attack
```bash
curl -s -A "sqlmap/1.7" -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":{"$gt":""},"password":{"$gt":""}}' \
  "http://localhost:8080/api_service/users"
```

---

## 🤖 ML Pipeline — Two Models

### Model 1: Web Attack Detector V2 (ANN/Keras)
- **Architecture:** Input(22) → Dense(128, ReLU) → Dropout → Dense(64, ReLU) → Dense(1, Sigmoid)
- **Features:** URL length, special chars, SQLi/XSS/traversal patterns, user-agent flags, HTTP method
- **Training:** CIC-IDS2017 + custom SQLi/NoSQLi/XSS dataset
- **Results:** 94.0% Accuracy | 92.0% Precision | 95.0% Recall | 93.0% F1
- **Attack types:** SQLi, NoSQLi, XSS, Path Traversal, CMDi, Scanner tools

### Model 2: DDoS Detector V1 (Random Forest)
- **Architecture:** 100 estimators, 30 CIC-DDoS2019 flow features
- **Features:** packet rate, flow duration, inter-arrival time, byte distribution...
- **Training:** CIC-DDoS2019 dataset (12 attack categories)
- **Results:** 99.9% Accuracy | 99.8% Precision | 100% Recall | 100% F1
- **Attack types:** SYN Flood, UDP Flood, DNS Amp, NTP, LDAP, MSSQL, NetBIOS...

---

## 🧠 LLM + GAN — Dynamic Honeypots (Key Innovation)

### LLM (Ollama gemma3:1b)
- **What it does:** Generates context-aware fake HTML responses tailored to attacker's payload
- **How it works:** 
  1. First attack → queues background generation (falls through to dynamic honeypot)
  2. LLM generates in 60-90s on CPU (background thread)
  3. Next identical attack → serves cached LLM-generated HTML instantly
  4. Dashboard shows `LLM successful_responses` counter incrementing
- **Why dynamic:** Every attack payload gets a unique response — attacker sees different "leaked data" each time
- **Check status:** http://localhost:8080/proxy/status → `llm_stats`

### GAN (DCGAN — Fake Users)
- **What it does:** Pre-fills honeypot databases with realistic fake user accounts
- **Evidence:** http://localhost:4001/api/users → returns [admin@quickbank.net, cfo_linda@quickbank.net...]
- **Watermark:** Every fake user has a hidden watermark (`balance % 100 = 7`) to prove it's synthetic
- **7 databases:** banking, ecommerce, healthcare, blog, api_service, corporate, admin_panel

---

## ⛓️ Blockchain Audit Trail
- Every captured attack is written to a SHA-256 linked chain
- **Verify integrity:** Dashboard → Blockchain Ledger → "Chain integrity verified"
- **Check via API:**
  ```bash
  curl -s -b /tmp/dash_session.txt http://localhost:9000/api/blockchain | \
    python3 -c "import sys,json;d=json.load(sys.stdin);print('Valid:',d.get('is_valid'),'Blocks:',d.get('total_blocks'))"
  ```

---

## 🎯 Dashboard Pages — What to Show

| Page | Sidebar | Show The Jury |
|------|---------|---------------|
| **Overview** | Overview | Attack count, 16/16 services, avg confidence |
| **Attack Analysis** | Attack Analysis | Live feed: SQLi/XSS badges, CRITICAL severity, 99% confidence |
| **Honeypot Mgmt** | Honeypot Mgmt | 7 real ↔ 7 honeypot pairs, rotation timer |
| **ML Models** | ML Models | Web Attack V2 (94%) + DDoS V1 (99.9%) — both ACTIVE |
| **Blockchain** | Blockchain Ledger | Block list, SHA-256 hashes, "Chain verified" |
| **Canary Tokens** | Canary Tokens | Triggered tokens from recon/scanning |
| **Fingerprints** | Fingerprints | DBSCAN attacker behavior clusters |

---

## ❓ Jury Q&A — Quick Answers

| Question | Answer |
|----------|--------|
| Which honeypot was attacked? | Check Attack Analysis: shows "Banking Honeypot :4001" |
| Was the attack captured? | Green "CRITICAL" badge = captured, routed to honeypot |
| What fake data did attacker get? | http://localhost:4001/api/users — all GAN-generated |
| Why wasn't XSS captured (via browser)? | Score below 0.50 threshold — plain browser has no scanner UA. Use Burp Suite UA to force capture |
| How is it dynamic? | LLM generates unique HTML per payload; GAN fills DBs with realistic fake users |
| Can you prove the chain isn't tampered? | Blockchain page: verify each block's hash matches prev_hash |
| How does DDoS recovery work? | K8s watchdog polls every 5s; restarts crashed pod within 10s |
| What dataset? | CIC-IDS2017 (web), CIC-DDoS2019 (DDoS) — standard academic benchmarks |

---

## 🔑 Credentials

| Service | URL | Login |
|---------|-----|-------|
| Dashboard | http://localhost:9000 | admin / DeceptiCloud |
| Honeypot (fake login) | http://localhost:4001/login | anything works (it's a trap) |

---

## 📁 JURY_PRESENTATION/ Files

| File | Purpose |
|------|---------|
| `1_START_SYSTEM.sh` | Launch all 16 services |
| `2_WEB_ATTACKS.sh` | All 16 web attack types |
| `3_DDOS_ATTACK.sh [low\|medium\|high]` | DDoS + crash + K8s restart |
| `4_NARRATED_DEMO.sh` | 7-phase explained demo (MAIN) |
| `STOP_ALL.sh` | Kill everything cleanly |
| `JURY_GUIDE.md` | This file |
