# DeceptiCloud v2.0 — README
> AI-Driven Cyber Deception System | Final Year Project

## What This System Does
DeceptiCloud is a **honeypot-based intrusion deception platform**. Every HTTP request goes through a routing proxy that uses an ANN model to detect attacks. Malicious traffic is silently routed to honeypot clones of real websites — filled with GAN-generated fake data. An on-device LLM (Ollama gemma3:1b) generates unique deceptive responses per attacker payload. Every attack is logged to a blockchain ledger.

---

## ⚡ How to Run (No Errors)

### First Time Only — Install Dependencies
```bash
cd "/media/amei-302/New Volume1/SEMESTER VIII/Ahmed Fype-II"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Every Time — Start the System
```bash
cd "/media/amei-302/New Volume1/SEMESTER VIII/Ahmed Fype-II"

# One command — stops old + starts fresh automatically:
bash Jury_presentation_final/scripts/1_START_SYSTEM.sh
```

Wait for the green `✅ ALL SYSTEMS ONLINE` banner (takes ~35 seconds).

### Open Dashboard
- URL: http://localhost:9000
- Login: `admin` / `DeceptiCloud`

---

## Service Map

| Service | Port | Purpose |
|---------|------|---------|
| Dashboard | 9000 | Defender command center |
| Routing Proxy | 8080 | All traffic goes through here |
| ML API | 5000 | ANN web attack + Random Forest DDoS models |
| Banking (Real) | 3001 | Legitimate site (benign users go here) |
| Banking (Honeypot) | 4001 | Trap for attackers |
| E-commerce (Real) | 3002 | Legitimate site |
| E-commerce (Honeypot) | 4002 | Trap |
| Healthcare (Real) | 3003 | Legitimate site |
| Healthcare (Honeypot) | 4003 | Trap |
| Blog (Real) | 3004 | Legitimate site |
| Blog (Honeypot) | 4004 | Trap |
| API Service (Real) | 3005 | Legitimate site |
| API Service (Honeypot) | 4005 | Trap |
| Corporate (Real) | 3006 | Legitimate site |
| Corporate (Honeypot) | 4006 | Trap |
| Admin Panel (Real) | 3007 | Legitimate site |
| Admin Panel (Honeypot) | 4007 | Trap |

---

## Demo Commands

### Send Web Attacks
```bash
bash Jury_presentation_final/scripts/2_WEB_ATTACKS.sh
```

### DDoS Demo
```bash
bash Jury_presentation_final/scripts/3_DDOS_ATTACK.sh low
```

### Narrated Demo (7 phases with explanations)
```bash
bash Jury_presentation_final/scripts/4_NARRATED_DEMO.sh
```

### Stop Everything
```bash
bash Jury_presentation_final/scripts/STOP_ALL.sh
```

---

## Quick Manual Attack Test
```bash
# SQLi attack through proxy (attacker view)
curl -A "sqlmap/1.7" "http://localhost:8080/banking/search?q=1'+UNION+SELECT+username,password+FROM+users--"

# See what attacker gets (GAN fake users)
curl http://localhost:4001/api/users

# Check dashboard stats
curl http://localhost:8080/proxy/status
```

---

## Common Issues & Fixes

| Problem | Fix |
|---------|-----|
| Port already in use | `bash Jury_presentation_final/scripts/STOP_ALL.sh` then restart |
| ModuleNotFoundError | Scripts use explicit venv python — fixed in 1_START_SYSTEM.sh |
| LLM fallbacks only | Fixed — LLM now generates synchronously (80 tokens, ~10s) on first request |
| GAN shows 0% synthetic | Fixed — watermark embedded at seed time in db_seeder.py |
| Fingerprints 0/0 | Fixed — computed from attack log directly, no honeypot API dependency |

---

## Project Structure
```
├── config.py                  # All global constants
├── launch_decepticloud.py     # Master launcher
├── requirements.txt           # Python deps
├── proxy/routing_proxy.py     # Traffic interception + ML routing
├── ml_pipeline/model_api.py   # ML REST API (port 5000)
├── honeypot/
│   ├── llm_response_engine.py # Ollama LLM adaptive responses
│   └── blockchain_ledger.py   # SHA-256 attack evidence chain  
├── websites/                  # 7 real + 7 honeypot Flask apps
│   ├── shared/db_seeder.py    # DB seeder with GAN watermark
│   └── databases/             # SQLite DBs (35 GAN fake users)
├── dashboard/app.py           # Defender dashboard backend
├── attacks/                   # Attack simulation scripts
└── Jury_presentation_final/   # ← This folder
```
