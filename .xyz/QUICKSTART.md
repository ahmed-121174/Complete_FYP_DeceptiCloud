# DeceptiCloud — Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Launch the System
```bash
cd "/media/amei-302/New Volume/SEMESTER VIII/Ahmed Fype-II"
python3 launch_decepticloud_v2.py
```

Wait for all services to start (20-30 seconds).

### Step 2: Access the Dashboard
Open your browser and go to:
```
http://localhost:9000
```

Login with:
- **Username**: `admin`
- **Password**: `DeceptiCloud`

### Step 3: Run Attack Simulation
Open a new terminal and run:
```bash
cd "/media/amei-302/New Volume/SEMESTER VIII/Ahmed Fype-II"
bash attacks/web_attacks.sh
```

### Step 4: Watch the Dashboard
Go back to the dashboard and watch:
- Attack count increasing in real-time
- New attacks appearing in the feed
- Attacker profiles being created
- Blockchain blocks being added

### Step 5: Explore the System

**View Attack Details**:
- Click on any attack in the feed
- See full classification details
- View attacker profile

**Check System Health**:
- Go to "Infrastructure Health" page
- See all 17 services status
- Watch real-time health checks

**View ML Models**:
- Go to "ML Models" page
- See model performance metrics
- View model architecture

**Explore Blockchain**:
- Go to "Blockchain Ledger" page
- See tamper-proof attack log
- Verify chain integrity

---

## 🎯 What's Happening Behind the Scenes?

### When You Launch
1. Database initializes (SQLite)
2. Existing attack data migrates (if first run)
3. ML models load (TensorFlow + scikit-learn)
4. 14 websites start (7 real + 7 honeypots)
5. Routing proxy starts (port 8080)
6. Dashboard starts (port 9000)

### When You Run Attacks
1. Attack hits proxy (port 8080)
2. Proxy extracts 23 features
3. ML model classifies (attack/benign)
4. Attacker routed to honeypot (ports 4001-4007)
5. Attack logged to database
6. Attacker profile created/updated
7. Blockchain block added
8. Dashboard updates in real-time

### What Attackers See
- Convincing fake website (identical to real)
- GAN-generated fake data
- LLM-powered adaptive responses
- They think they succeeded!

### What You See
- Real-time attack detection
- Complete attacker profile
- Behavioral fingerprints
- Attack patterns and trends
- Tamper-proof evidence

---

## 📊 Key Metrics to Watch

### Overview Page
- **Total Attacks**: Should increase as you run simulations
- **Detection Rate**: Should be 100%
- **Avg Confidence**: Should be 90%+
- **Active Attackers**: Number of unique IPs

### Attack Analysis Page
- **Recent Attacks**: Last 50 attacks
- **Attack Types**: SQLi, XSS, Scanner, etc.
- **Confidence Scores**: 0.0 - 1.0

### Infrastructure Health Page
- **All Services**: Should show "UP" (green)
- **Response Time**: Should be < 100ms
- **Status**: Real-time updates every 3s

---

## 🧪 Testing Scenarios

### Scenario 1: SQL Injection
```bash
curl "http://localhost:8080/banking/search?q=1'+OR+1=1--"
```
**Expected**: Routed to honeypot, logged as SQLi attack

### Scenario 2: XSS Attack
```bash
curl "http://localhost:8080/ecommerce/search?q=<script>alert(1)</script>"
```
**Expected**: Routed to honeypot, logged as XSS attack

### Scenario 3: Scanner Detection
```bash
curl -A "sqlmap/1.0" "http://localhost:8080/banking/"
```
**Expected**: Routed to honeypot, logged as Scanner

### Scenario 4: Benign Request
```bash
curl "http://localhost:8080/banking/"
```
**Expected**: Routed to real site (port 3001)

---

## 🔍 Troubleshooting

### Dashboard Won't Load
```bash
# Check if dashboard is running
curl http://localhost:9000/api/stats

# If not, check logs
tail -f logs/dashboard.log
```

### No Attacks Showing
```bash
# Check database
python3 -c "from database.db_service import get_db_service; print(get_db_service().get_attack_stats())"

# Check proxy logs
tail -f proxy/logs/proxy_attacks.jsonl
```

### ML API Not Responding
```bash
# Check ML API
curl http://localhost:5000/api/health

# If not, restart
pkill -f "model_api.py"
python3 ml_pipeline/model_api.py &
```

### Services Not Starting
```bash
# Check port availability
netstat -tulpn | grep -E '(5000|8080|9000)'

# Kill stuck processes
pkill -f "python3.*decepticloud"

# Restart
python3 launch_decepticloud_v2.py
```

---

## 📚 Next Steps

### 1. Install Wazuh (Optional)
```bash
sudo bash wazuh/install_wazuh.sh
sudo bash wazuh/deploy_agents.sh
python3 wazuh/log_ingestion_service.py &
```

### 2. Run Comprehensive Tests
```bash
bash attacks/web_attacks.sh
bash attacks/ddos_attack.sh
```

### 3. Explore Advanced Features
- Attacker profiling and clustering
- Behavioral fingerprinting
- Adaptive learning engine
- Blockchain ledger verification

### 4. Customize Configuration
Edit `config.py` to change:
- Detection thresholds
- Rate limits
- Rotation intervals
- Service ports

---

## 🎓 Learn More

- **Full Documentation**: `README_COMPLETE_SYSTEM.md`
- **Build Plan**: `DECEPTICLOUD_BUILD_PLAN.md`
- **System Config**: `SYSTEM_CONFIG.md`
- **Build Status**: `BUILD_STATUS.md`
- **Wazuh Guide**: `wazuh/README.md`

---

## 🆘 Need Help?

1. Check logs in `logs/` directory
2. Review `BUILD_STATUS.md` for known issues
3. Check system health in dashboard
4. Review database for data consistency

---

**Status**: ✅ System Operational  
**Version**: v2.0  
**Last Updated**: 2026-04-18
