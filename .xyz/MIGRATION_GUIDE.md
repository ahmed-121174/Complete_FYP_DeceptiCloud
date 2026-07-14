# Project Migration Guide

This guide details how to transfer the **AI-Driven Cyber Deception System** to a new machine.

## 📦 1. Prerequisite Checklist (New Machine)

Ensure the new laptop has the following installed:
- **Python 3.10+**
- **Docker & Docker Compose** (optional, for containerized run)
- **Git** (if cloning)

---

## 💾 2. Transferring Files

### Option A: Zip Transfer (Simplest)
1. On the **OLD** machine, run this command to zip the project (excluding bulky venv/cache):
   ```bash
   # Make sure you are in the project folder
   zip -r project_transfer.zip . -x "venv/*" -x "__pycache__/*" -x ".git/*" -x "Dataset/*"
   ```
   *Note: If your datasets are large, copy them separately.*

2. Transfer `project_transfer.zip` to the new machine.
3. Unzip:
   ```bash
   unzip project_transfer.zip -d cyber-deception-system
   cd cyber-deception-system
   ```

### Option B: Git
If this repo is on GitHub/GitLab:
```bash
git clone <your-repo-url>
cd <repo-name>
# You may need to copy the 'models/' folder manually if it was ignored
```

---

## ⚙️ 3. Setup on New Machine

### Local Python Setup (Recommended for Development)

1. **Create Virtual Environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies:**
   I have consolidated all dependencies into `requirements.txt`. Run:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Verify Setup:**
   Run the setup script to check everything:
   ```bash
   chmod +x scripts/setup.sh
   ./scripts/setup.sh
   ```

### Docker Setup (Recommended for Production)

1. **Build and Run:**
   ```bash
   docker-compose -f docker/docker-compose.yml up --build
   ```

---

## 🧪 4. Verify Project State

After setup, run these quick checks to ensure the transfer worked:

### Check Models
Verify that your trained models are present and loadable:
```bash
ls -lh ml_pipeline/models/
# Should see: web_attack_detector_v2.keras, ddos_detector.keras, etc.
```

### Test API
Start the ML API and check its health:
```bash
# Terminal 1
cd ml_pipeline
python model_api.py

# Terminal 2 (Test)
curl http://localhost:5000/api/health
# Expected: {"status": "healthy", ...}
```

---

## ⚠️ Troubleshooting

**Missing 'xgboost' or 'imbalanced-learn'?**
- I have updated `requirements.txt` to include these. Re-run `pip install -r requirements.txt`.

**TensorFlow Version Errors?**
- The project is now locked to **TensorFlow 2.15/2.20**. Ensure you don't define conflicting versions.

**Permission Denied on Scripts?**
- Run `chmod +x scripts/*.sh` to make them executable.
