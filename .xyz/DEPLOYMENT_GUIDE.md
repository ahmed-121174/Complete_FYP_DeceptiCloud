# 🚀 COMPLETE SYSTEM DEPLOYMENT - USAGE GUIDE

## ✅ What Just Happened

I've created a **master deployment script** that runs your ENTIRE project with ONE command!

## 📝 The Master Script: `deploy_complete_system.sh`

### What It Does (Automatically):

1. **Environment Setup** ✅
   - Creates virtual environment
   - Installs all dependencies
   - Creates necessary directories

2. **Dataset Analysis** ✅
   - Analyzes all 21 CSV files
   - Generates report

3. **ML Model Training** 🔄 (30-60 minutes)
   - Trains Web Attack Detector
   - Trains DDoS Detector
   - Saves models to `models/` directory
   - Generates training plots

4. **ML API Launch** ✅
   - Starts Flask API on port 5000
   - Loads both trained models
   - Ready for real-time detection

5. **Honeypot Deployment** ✅
   - Starts 5 **deceptive** honeypots (ports 8080-8084)
   - Starts 5 **legitimate** honeypots (ports 8085-8089)
   - All connected to ML API

---

## 🎮 How to USE

### Option 1: Run Complete System (Recommended)

```bash
cd "/home/irtaza-butt/Desktop/Ahmed Fype-II"
./deploy_complete_system.sh
```

**This runs EVERYTHING!** ⏱️ First run takes ~30-60 minutes (model training).  
Subsequent runs are fast (~2 minutes) because models are already trained.

### Option 2: Check Current Status

```bash
./check_status.sh
```

Shows:
- Which services are running
- Port availability
- Latest logs
- Health status

### Option 3: Manual Control

```bash
# Train models only
./train_all.sh

# Start ML API only
cd ml_pipeline && source ../venv/bin/activate && python model_api.py

# Start one honeypot
cd honeypot && source ../venv/bin/activate
export HONEYPOT_TYPE=deceptive
export HONEYPOT_SERVICE=ecommerce  
export ML_API_URL=http://localhost:5000
export PORT=8080
python app.py
```

---

## 🌐 System Access Points

### ML Detection API
```
http://localhost:5000
http://localhost:5000/api/health
```

### Deceptive Honeypots (Trap Attackers)
```
http://localhost:8080  - E-commerce
http://localhost:8081  - Banking
http://localhost:8082  - Admin
http://localhost:8083  - API
http://localhost:8084  - Corporate
```

### Legitimate Honeypots (Serve Users)
```
http://localhost:8085  - E-commerce
http://localhost:8086  - Banking
http://localhost:8087  - Admin
http://localhost:8088  - API
http://localhost:8089  - Corporate
```

---

## 🧪 Testing the System

### Test 1: Check ML API Health
```bash
curl http://localhost:5000/api/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "models": {
    "web_attack": "loaded",
    "ddos": "loaded"
  }
}
```

### Test 2: Visit a Honeypot
```bash
# In browser
open http://localhost:8080

# Or with curl
curl http://localhost:8080
```

### Test 3: Simulate SQL Injection Attack
```bash
curl "http://localhost:8080/search?q='+UNION+SELECT+*+FROM+users--"
```

**What Happens:**
1. Honeypot receives request
2. Logs the suspicious pattern
3. Sends features to ML API
4. ML API detects attack
5. Returns prediction
6. Honeypot logs the attack

### Test 4: Check Attack Logs
```bash
cat logs/honeypot_deceptive_ecommerce.log | grep -i "attack"
```

---

## 📊 Monitoring

### View Real-time Logs

```bash
# Deployment progress
tail -f logs/deployment_*.log

# ML API activity
tail -f logs/ml_api.log

# Honeypot activity
tail -f logs/honeypot_deceptive_ecommerce.log

# All logs
tail -f logs/*.log
```

### Check What's Running

```bash
# Using status script
./check_status.sh

# Manual check
ps aux | grep -E "(model_api|honeypot/app)"

# Check ports
netstat -tuln | grep -E "(5000|808[0-9])"
```

---

## 🛑 Stopping the System

### Option 1: Ctrl+C
If you ran `./deploy_complete_system.sh` in foreground, just press **Ctrl+C**.  
It will automatically stop all services.

### Option 2: Find and Kill Processes
```bash
# Find process IDs
ps aux | grep model_api
ps aux | grep honeypot/app

# Kill them
kill <PID>

# Or kill all Python processes (be careful!)
pkill -f model_api
pkill -f "honeypot/app"
```

### Option 3: Kill by Port
```bash
# Kill process on port 5000 (ML API)
kill $(lsof -t -i:5000)

# Kill all honeypots
for port in {8080..8089}; do
    kill $(lsof -t -i:$port) 2>/dev/null
done
```

---

## 📁 Important Files & Directories

```
Ahmed Fype-II/
├── deploy_complete_system.sh    ⭐ MASTER SCRIPT - Run this!
├── check_status.sh               📊 Check system status
├── train_all.sh                  🧠 Train models only
├── models/                       💾 Trained ML models
│   ├── web_attack_detector.keras
│   ├── ddos_detector.keras
│   └── *.pkl (preprocessors)
├── logs/                         📝 All system logs
│   ├── deployment_*.log          (main deployment log)
│   ├── ml_api.log                (ML API logs)
│   ├── honeypot_*.log            (honeypot logs)
│   └── *_training.log            (training logs)
├── plots/                        📈 Training visualizations
│   ├── web_attack_training_history.png
│   └── ddos_training_history.png
└── ...
```

---

## ⏱️ Timeline Expectations

### First Run (Fresh Start)
```
00:00 - Start deployment
00:01 - Environment setup complete
00:02 - Dependencies installed
00:05 - Dataset analysis complete
00:10 - Web Attack model training starts
15:00 - Web Attack model complete
15:05 - DDoS model training starts
30:00 - DDoS model complete
30:01 - ML API starts
30:02 - Honeypots launch
30:05 - System fully operational ✅
```

### Subsequent Runs (Models Already Trained)
```
00:00 - Start deployment
00:30 - Environment check
01:00 - Models detected (skip training)
01:30 - ML API starts
02:00 - Honeypots launch
02:30 - System fully operational ✅
```

---

## 🎯 Production Tips

### 1. Background Execution
```bash
# Run in background with nohup
nohup ./deploy_complete_system.sh > deployment.out 2>&1 &

# View output
tail -f deployment.out
```

### 2. Auto-Restart on Failure
```bash
# Create a systemd service (advanced)
# Or use simple loop:
while true; do
    ./deploy_complete_system.sh
    echo "System stopped. Restarting in 10 seconds..."
    sleep 10
done
```

### 3. Docker Alternative
```bash
# For cleaner deployment
docker-compose -f docker/docker-compose.yml up --build
```

---

## 🐛 Troubleshooting

### Issue: "Models not found"
**Solution:** Models need to be trained first. Run the script and wait for training to complete.

### Issue: "Port already in use"
**Solution:**
```bash
# Find what's using the port
lsof -i:5000
lsof -i:8080

# Kill it
kill $(lsof -t -i:5000)
```

### Issue: "TensorFlow not found"
**Solution:**
```bash
source venv/bin/activate
pip install tensorflow
```

### Issue: "Script hangs during training"
**This is normal!** Training takes 30-60 minutes. Check logs:
```bash
tail -f logs/deployment_*.log
```

---

## 📞 Quick Reference Commands

```bash
# Deploy entire system
./deploy_complete_system.sh

# Check status
./check_status.sh

# Test ML API
curl http://localhost:5000/api/health

# Test honeypot
curl http://localhost:8080

# View logs
tail -f logs/deployment_*.log

# Stop everything
pkill -f model_api && pkill -f "honeypot/app"
```

---

## 🎓 For Your Presentation/Demo

### Demo Flow:

1. **Show the master script**
   ```bash
   cat deploy_complete_system.sh
   ```

2. **Run it**
   ```bash
   ./deploy_complete_system.sh
   ```

3. **While it runs, explain:**
   - Environment setup
   - Model training process
   - Architecture diagram

4. **When complete, demo:**
   - Visit honeypots in browser
   - Simulate attacks
   - Show ML detection
   - Display logs
   - Show training plots

5. **Show monitoring**
   ```bash
   ./check_status.sh
   ```

---

## ✅ Success Indicators

You know the system is working when:

- ✅ `./check_status.sh` shows all services running
- ✅ `curl http://localhost:5000/api/health` returns JSON
- ✅ Browser opens http://localhost:8080 successfully
- ✅ `models/` directory contains `.keras` files
- ✅ `logs/` directory has recent activity
- ✅ No error messages in terminal

---

**Ready to deploy! Just run: `./deploy_complete_system.sh`** 🚀
