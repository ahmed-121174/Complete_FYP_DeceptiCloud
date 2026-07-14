# Additional ML Models - Build Plan

**Date**: April 18, 2026  
**Models to Build**: 5 (Brute Force, Port Scan, XSS, Credential Stuffing, Anomaly Detection)  
**Estimated Time**: 6-8 hours  
**Status**: In Progress

---

## 📊 DATASET STRATEGY

### Available Data
- ✅ **394 attacks** in database (SQLi, XSS, NoSQLi, Path Traversal, Command Injection)
- ✅ **User agents** (sqlmap, nikto, burp, ZAP, curl)
- ✅ **IP patterns** (127.0.0.1 with 260 attempts - brute force pattern)
- ✅ **Request patterns** (method, path, query_string, headers)
- ✅ **Timing data** (timestamps for rate analysis)

### Data Sources by Model

#### 1. Brute Force Detector
**Data Sources**:
- Existing attack logs (repeated IPs)
- SSH honeypot logs (if available)
- Generate synthetic login attempts
- Public SSH brute force datasets

**Features**:
- Request rate (requests per minute)
- Failed login attempts
- Time between requests
- User agent patterns
- IP reputation
- Geographic location changes
- Password patterns (common passwords)

#### 2. Port Scan Detector
**Data Sources**:
- Generate synthetic port scan patterns
- Use network flow data if available
- Public CICIDS2017 dataset (port scan subset)

**Features**:
- Ports accessed per IP
- Time between port accesses
- Sequential vs random port access
- SYN/ACK patterns
- Packet size distribution
- Connection duration

#### 3. XSS Detector (Separate from Web Attack)
**Data Sources**:
- Extract XSS from existing database (24 samples)
- XSS payload databases (OWASP, PayloadsAllTheThings)
- Generate variations using mutation

**Features**:
- Script tag presence
- Event handler patterns (onclick, onerror, onload)
- JavaScript keywords
- Encoding patterns (URL, HTML, Unicode)
- Tag nesting depth
- Special characters count

#### 4. Credential Stuffing Detector
**Data Sources**:
- Generate from common username/password patterns
- Analyze existing login attempts
- Public breach databases (Have I Been Pwned patterns)

**Features**:
- Login velocity (attempts per second)
- Username/password patterns
- Success rate
- User agent rotation
- IP rotation patterns
- Time-of-day patterns
- Geographic distribution

#### 5. Anomaly Detector (Unsupervised)
**Data Sources**:
- All existing traffic (normal + attack)
- Baseline from benign requests
- Statistical analysis of patterns

**Features**:
- Request frequency
- Path access patterns
- Parameter count
- Payload size
- Header count
- Time-of-day patterns
- Deviation from baseline

---

## 🏗️ BUILD APPROACH

### Phase 1: Data Collection & Preparation (2 hours)
1. Extract existing data from database
2. Generate synthetic data for each model
3. Create feature extraction pipelines
4. Split into train/validation/test sets

### Phase 2: Model Development (3 hours)
1. Build and train each model
2. Hyperparameter tuning
3. Cross-validation
4. Performance evaluation

### Phase 3: Integration (1 hour)
1. Add models to ML API
2. Create detection endpoints
3. Update routing proxy
4. Test end-to-end

### Phase 4: Testing & Validation (1 hour)
1. Unit tests for each model
2. Integration tests
3. Attack simulation tests
4. Performance benchmarks

---

## 🎯 MODEL SPECIFICATIONS

### 1. Brute Force Detector
**Type**: Time-series + Classification  
**Algorithm**: Random Forest + Rate Analysis  
**Input**: Request sequence (last N requests from IP)  
**Output**: Binary (Brute Force / Normal)  
**Threshold**: 5+ failed attempts in 60 seconds  

**Architecture**:
```
Input Features (10) → Random Forest (100 trees) → Binary Output
+ Rate-based rules for real-time detection
```

### 2. Port Scan Detector
**Type**: Sequence Analysis  
**Algorithm**: LSTM + Rule-based  
**Input**: Port access sequence  
**Output**: Binary (Port Scan / Normal)  
**Threshold**: 10+ ports in 30 seconds  

**Architecture**:
```
Port Sequence (20) → LSTM (64 units) → Dense (32) → Binary Output
+ Sequential pattern rules
```

### 3. XSS Detector
**Type**: Text Classification  
**Algorithm**: CNN + Feature Engineering  
**Input**: Request payload (text)  
**Output**: Binary (XSS / Normal)  
**Features**: 25 engineered features  

**Architecture**:
```
Text Input → Tokenization → CNN (128 filters) → Dense (64) → Binary Output
+ Pattern matching rules
```

### 4. Credential Stuffing Detector
**Type**: Behavioral Analysis  
**Algorithm**: Gradient Boosting + Velocity Analysis  
**Input**: Login attempt sequence  
**Output**: Binary (Credential Stuffing / Normal)  
**Threshold**: 20+ attempts in 60 seconds  

**Architecture**:
```
Behavioral Features (15) → XGBoost → Binary Output
+ Velocity-based rules
```

### 5. Anomaly Detector
**Type**: Unsupervised Learning  
**Algorithm**: Isolation Forest + Autoencoder  
**Input**: Request features (30)  
**Output**: Anomaly score (0-1)  
**Threshold**: Score > 0.7 = Anomaly  

**Architecture**:
```
Features (30) → Isolation Forest → Anomaly Score
+ Autoencoder for reconstruction error
```

---

## 📁 FILE STRUCTURE

```
ml_pipeline/
├── models/
│   ├── brute_force_detector.pkl
│   ├── brute_force_metadata.json
│   ├── port_scan_detector.h5
│   ├── port_scan_metadata.json
│   ├── xss_detector.pkl
│   ├── xss_metadata.json
│   ├── credential_stuffing_detector.pkl
│   ├── credential_stuffing_metadata.json
│   ├── anomaly_detector.pkl
│   └── anomaly_metadata.json
├── training/
│   ├── train_brute_force.py
│   ├── train_port_scan.py
│   ├── train_xss.py
│   ├── train_credential_stuffing.py
│   └── train_anomaly.py
├── data_generation/
│   ├── generate_brute_force_data.py
│   ├── generate_port_scan_data.py
│   ├── generate_xss_data.py
│   ├── generate_credential_stuffing_data.py
│   └── generate_anomaly_data.py
└── detectors/
    ├── brute_force_detector.py
    ├── port_scan_detector.py
    ├── xss_detector.py
    ├── credential_stuffing_detector.py
    └── anomaly_detector.py
```

---

## 🎓 TRAINING STRATEGY

### Data Augmentation Techniques

**1. For Text-based (XSS)**:
- Character substitution (< → &lt;)
- Case variation (Script → SCRIPT → sCrIpT)
- Encoding variation (URL, HTML, Unicode)
- Whitespace injection
- Comment injection

**2. For Sequence-based (Port Scan, Brute Force)**:
- Time jittering (add random delays)
- Sequence shuffling
- Partial sequence extraction
- Rate variation

**3. For Behavioral (Credential Stuffing)**:
- IP rotation simulation
- User agent rotation
- Success rate variation
- Time-of-day variation

### Synthetic Data Generation

**Brute Force** (10,000 samples):
- 5,000 normal login patterns
- 5,000 brute force patterns
- Vary: rate, user agents, IPs, timing

**Port Scan** (10,000 samples):
- 5,000 normal port access
- 5,000 scan patterns (sequential, random, SYN)
- Vary: speed, port ranges, protocols

**XSS** (5,000 samples):
- 2,500 benign inputs
- 2,500 XSS payloads (from OWASP + mutations)
- Vary: encoding, obfuscation, context

**Credential Stuffing** (10,000 samples):
- 5,000 normal logins
- 5,000 stuffing patterns
- Vary: velocity, success rate, rotation

**Anomaly** (20,000 samples):
- 18,000 normal requests (baseline)
- 2,000 anomalous requests
- Vary: all features

---

## 📊 EXPECTED PERFORMANCE

### Target Metrics

| Model | Accuracy | Precision | Recall | F1-Score |
|-------|----------|-----------|--------|----------|
| Brute Force | >95% | >90% | >95% | >92% |
| Port Scan | >90% | >85% | >90% | >87% |
| XSS | >94% | >92% | >94% | >93% |
| Credential Stuffing | >93% | >90% | >93% | >91% |
| Anomaly | >85% | >80% | >85% | >82% |

### Why These Targets?

- **Brute Force**: Clear patterns, easy to detect
- **Port Scan**: Sequential patterns, moderate difficulty
- **XSS**: Similar to existing web attack model (93.97%)
- **Credential Stuffing**: Behavioral patterns, moderate difficulty
- **Anomaly**: Unsupervised, lower accuracy expected

---

## 🔄 INTEGRATION PLAN

### 1. Update ML API (`ml_pipeline/model_api.py`)

Add endpoints:
```python
POST /api/classify-brute-force
POST /api/classify-port-scan
POST /api/classify-xss
POST /api/classify-credential-stuffing
POST /api/classify-anomaly
POST /api/classify-all  # Run all models
```

### 2. Update Routing Proxy

Add detection calls:
```python
# In routing_proxy.py
results = {
    'web_attack': classify_web_attack(request),
    'brute_force': classify_brute_force(request),
    'port_scan': classify_port_scan(request),
    'xss': classify_xss(request),
    'credential_stuffing': classify_credential_stuffing(request),
    'anomaly': classify_anomaly(request)
}
```

### 3. Update Dashboard

Add model cards for each new model in ML Models page

---

## ⏱️ TIMELINE

### Hour 1-2: Data Generation
- ✅ Analyze existing data
- ⏳ Generate synthetic datasets
- ⏳ Create feature extractors

### Hour 3-4: Model Training (Part 1)
- ⏳ Train Brute Force detector
- ⏳ Train Port Scan detector

### Hour 5-6: Model Training (Part 2)
- ⏳ Train XSS detector
- ⏳ Train Credential Stuffing detector
- ⏳ Train Anomaly detector

### Hour 7: Integration
- ⏳ Update ML API
- ⏳ Update Routing Proxy
- ⏳ Update Dashboard

### Hour 8: Testing
- ⏳ Unit tests
- ⏳ Integration tests
- ⏳ Attack simulations

---

## 🚀 NEXT STEPS

1. **Start with data generation** (easiest to hardest)
2. **Build models incrementally** (test each before moving on)
3. **Integrate one at a time** (avoid breaking existing system)
4. **Test thoroughly** (ensure accuracy meets targets)

---

**Status**: Ready to begin  
**First Task**: Generate synthetic data for all 5 models  
**Estimated Completion**: 6-8 hours from now
