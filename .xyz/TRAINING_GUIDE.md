# TRAINING COMMANDS - Step-by-Step Guide

## 📊 Data Split Strategy

### Automatic Data Cleaning & Splitting

Both models use identical preprocessing with **70/10/20 split**:

```
Combined Dataset (All CSV files)
        ↓
[PREPROCESSING - Automatic Data Cleaning]
├─ Remove duplicate rows
├─ Handle null values (median/mode imputation)
├─ Remove constant columns (no variance)
├─ Handle infinite values
├─ Encode categorical features
├─ Normalize labels to Binary (0/1)
├─ Feature scaling (StandardScaler)
└─ Feature selection (Top K features)
        ↓
[DATA SPLIT - Stratified]
├─ 70% Training Set    (for model learning)
├─ 10% Validation Set  (for hyperparameter tuning)
└─ 20% Test Set        (for final evaluation)
```

**Key Points:**
- ✅ **NO manual data cleaning required** - fully automated
- ✅ **Stratified split** - maintains class balance
- ✅ **Original files untouched** - cleaning happens in memory
- ✅ **Random seed = 42** - reproducible results

---

## 🚀 Complete Training Commands (In Sequence)

### Step 1: Setup Environment
```bash
cd "/home/irtaza-butt/Desktop/Ahmed Fype-II"

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install pandas numpy scikit-learn tensorflow matplotlib seaborn flask flask-cors pyyaml requests joblib
```

### Step 2: Analyze Datasets (Optional but Recommended)
```bash
# This shows what data we have
python analyze_datasets.py
```

**Expected Output:**
- Analysis of all 21 CSV files
- Summary report saved to `dataset_analysis_report.json`

### Step 3: Create Models Directory
```bash
mkdir -p models plots logs
```

### Step 4: Train Web Attack Detection Model
```bash
cd ml_pipeline
python train_web_attack.py
```

**What This Does:**
1. Loads 9 CSV files:
   - `SQLiV3.csv`
   - `sqli.csv`
   - `sqliv2.csv`
   - `Modified_SQL_Dataset.csv`
   - `sql_queries.csv`
   - `sqli-extended.csv`
   - `nosql_injection_dataset_labeled.csv`
   - `nosql_payloads.csv`
   - `nosqli-datasetcsv.csv`

2. Combines all datasets into one DataFrame

3. **Automatic Preprocessing:**
   - Removes duplicates
   - Handles null/missing values
   - Removes constant columns
   - Handles infinite values
   - Encodes categorical features
   - Normalizes labels to 0 (Benign) / 1 (Attack)
   - Scales features with StandardScaler
   - Selects **top 100 features**

4. **Splits data (70/10/20):**
   - 70% → Training
   - 10% → Validation
   - 20% → Test

5. **Trains model:**
   - 100 epochs (may stop early with Early Stopping)
   - Batch size: 64
   - Adam optimizer
   - Monitors validation loss

6. **Evaluates on test set:**
   - Accuracy, Precision, Recall, F1-Score, AUC
   - Confusion Matrix
   - Classification Report

7. **Tests on unseen data** (if available):
   - `sqli_test_1000 (1).csv`
   - `nosqli_test_1000 (1).csv`

8. **Saves:**
   - Model: `models/web_attack_detector.keras`
   - Preprocessor: `models/web_attack_preprocessor_scaler.pkl`
   - Metadata: `models/web_attack_preprocessor_metadata.json`
   - Training plot: `plots/web_attack_training_history.png`

**Expected Duration:** 15-30 minutes

**Expected Output:**
```
✅ WEB ATTACK DETECTION MODEL TRAINING COMPLETE!
Final Test Accuracy: 92.34%
Model saved to: models/web_attack_detector.keras
```

### Step 5: Train DDoS Detection Model
```bash
# Still in ml_pipeline directory
python train_ddos.py
```

**What This Does:**
1. Loads 10 CSV files:
   - `DrDoS_DNS_data_1_per.csv`
   - `DrDoS_LDAP_data_2_0_per.csv`
   - `DrDoS_MSSQL_data_1_3_per.csv`
   - `DrDoS_NTP_data_data_5_per.csv`
   - `DrDoS_NetBIOS_data_1_3_per.csv`
   - `DrDoS_SNMP_data_1_3_per.csv`
   - `DrDoS_SSDP_data_2_per.csv`
   - `DrDoS_UDP_data_2_per.csv`
   - `UDPLag_data_2_0_per.csv`
   - `syn_data.csv`

2. Combines all DDoS datasets

3. **Automatic Preprocessing:** (same as Web Attack)
   - Selects **top 80 features** (network traffic optimized)

4. **Splits data (70/10/20)**

5. **Trains model:**
   - 100 epochs
   - Batch size: 128 (larger for network traffic)

6. **Evaluates and saves**

**Expected Duration:** 15-30 minutes

**Expected Output:**
```
✅ DDOS DETECTION MODEL TRAINING COMPLETE!
Final Test Accuracy: 94.12%
Model saved to: models/ddos_detector.keras
```

### Step 6: Verify Models Are Trained
```bash
# Go back to project root
cd ..

# Check if models exist
ls -lh models/
```

**Expected Files:**
```
web_attack_detector.keras        (trained model)
web_attack_detector.json          (model metadata)
web_attack_preprocessor_scaler.pkl
web_attack_preprocessor_metadata.json

ddos_detector.keras               (trained model)
ddos_detector.json                (model metadata)
ddos_preprocessor_scaler.pkl
ddos_preprocessor_metadata.json
```

### Step 7: Check Training Plots
```bash
ls -lh plots/
```

**Expected Files:**
```
web_attack_training_history.png   (accuracy, loss, precision, recall plots)
ddos_training_history.png
```

### Step 8: Start ML API (Optional - for testing)
```bash
cd ml_pipeline
python model_api.py
```

**Access at:** http://localhost:5000

### Step 9: Test ML API (Optional)
```bash
# In a new terminal
# Health check
curl http://localhost:5000/api/health

# Test Web Attack detection (example - you need actual features)
curl -X POST http://localhost:5000/api/detect/web-attack \
  -H "Content-Type: application/json" \
  -d '{"features": [0.1, 0.2, 0.3]}'
```

---

## 📊 Detailed Train/Test Split Explanation

### Web Attack Model

**Input Files (9):**
- 6 SQL Injection datasets
- 3 NoSQL Injection datasets

**Combined Size:** Varies (depends on available data)

**Preprocessing:**
```python
test_size=0.2      # 20% for testing
val_size=0.1       # 10% for validation
# Remaining = 70% for training
```

**Example with 10,000 samples:**
```
Total Combined: 10,000 samples
    ↓
After Cleaning: ~9,500 samples (duplicates removed)
    ↓
Split:
├─ Training:   6,650 samples (70%)
├─ Validation:   950 samples (10%)
└─ Test:       1,900 samples (20%)
```

**Feature Selection:**
- Selects **top 100 features** from all available features
- Uses ANOVA F-value for selection

### DDoS Model

**Input Files (10):**
- All DDoS attack type datasets

**Combined Size:** ~212,000 samples

**Same split (70/10/20):**
```
Total: ~212,000 samples
    ↓
After Cleaning: ~200,000 samples
    ↓
Split:
├─ Training:   140,000 samples (70%)
├─ Validation:  20,000 samples (10%)
└─ Test:        40,000 samples (20%)
```

**Feature Selection:**
- Selects **top 80 features** (optimized for network traffic)

---

## 🎯 Expected Accuracy

Based on the architecture and datasets:

### Web Attack Model
- **Training Accuracy:** 95-98%
- **Validation Accuracy:** 92-95%
- **Test Accuracy:** 90-94%
- **Unseen Data Accuracy:** 88-92%

### DDoS Model
- **Training Accuracy:** 96-99%
- **Validation Accuracy:** 94-97%
- **Test Accuracy:** 92-96%

---

## ⚡ Quick Commands (All in One)

```bash
#!/bin/bash
# Run this to train everything

cd "/home/irtaza-butt/Desktop/Ahmed Fype-II"

# Setup
source venv/bin/activate || (python3 -m venv venv && source venv/bin/activate)
pip install -q pandas numpy scikit-learn tensorflow matplotlib seaborn flask flask-cors pyyaml requests joblib

# Create directories
mkdir -p models plots logs

# Train models
cd ml_pipeline
echo "Training Web Attack Model..."
python train_web_attack.py

echo "Training DDoS Model..."
python train_ddos.py

echo "✅ All models trained!"
ls -lh ../models/
```

**Save this as:** `train_all.sh` and run with `bash train_all.sh`

---

## 🔍 Monitoring Training Progress

During training, you'll see:

```
Epoch 1/100
████████████████████ 100/100 [00:05<00:00] - loss: 0.234 - accuracy: 0.912 - val_loss: 0.189 - val_accuracy: 0.935

Epoch 2/100
████████████████████ 100/100 [00:05<00:00] - loss: 0.156 - accuracy: 0.947 - val_loss: 0.142 - val_accuracy: 0.956
...

Epoch 00024: early stopping

✅ Training complete!

📊 Test Results:
   Loss:      0.1234
   Accuracy:  92.45%
   Precision: 93.12%
   Recall:    91.87%
   F1-Score:  92.49%
   AUC:       0.9678
```

---

## 📝 Training Logs

All training output is displayed in the terminal. To save logs:

```bash
# Web Attack with logging
python train_web_attack.py 2>&1 | tee ../logs/web_attack_training.log

# DDoS with logging
python train_ddos.py 2>&1 | tee ../logs/ddos_training.log
```

---

## ✅ Verification Checklist

After training, verify:

- [ ] `models/web_attack_detector.keras` exists
- [ ] `models/ddos_detector.keras` exists
- [ ] `plots/web_attack_training_history.png` exists
- [ ] `plots/ddos_training_history.png` exists
- [ ] Test accuracy > 90% for both models
- [ ] No errors in terminal output

---

## 🐛 Troubleshooting

**"No module named tensorflow"**
```bash
pip install tensorflow
```

**"Memory error during training"**
```bash
# Reduce batch size in training scripts
# Edit train_web_attack.py: batch_size=32 (instead of 64)
# Edit train_ddos.py: batch_size=64 (instead of 128)
```

**"File not found error"**
```bash
# Make sure you're in the right directory
pwd  # Should show: /home/irtaza-butt/Desktop/Ahmed Fype-II/ml_pipeline
```

**Training too slow?**
- Expected: 15-30 minutes per model on CPU
- Use GPU if available (TensorFlow will auto-detect)
- Reduce epochs: Change `epochs=100` to `epochs=50`

---

Ready to train! Start with Step 1 above. 🚀
