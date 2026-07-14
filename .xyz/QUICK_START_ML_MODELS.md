# Quick Start - ML Models

Fast guide to get started with all 7 ML detection models.

---

## 🚀 Start ML API

```bash
# Start the ML API (loads all 7 models)
./venv/bin/python3 ml_pipeline/model_api.py
```

Wait ~5 seconds for models to load, then verify:

```bash
# Check health (should show 7/7 models loaded)
curl http://localhost:5000/api/health
```

---

## 🧪 Quick Tests

### Test XSS Detection
```bash
# Malicious XSS
curl -X POST http://localhost:5000/api/detect/xss \
  -H "Content-Type: application/json" \
  -d '{"text": "<script>alert(1)</script>"}'

# Expected: {"prediction": 1, "confidence": 1.0, "attack_type": "XSS"}
```

### Test Brute Force Detection
```bash
# Attack pattern (50 attempts in 1 minute)
curl -X POST http://localhost:5000/api/detect/brute-force \
  -H "Content-Type: application/json" \
  -d '{"features": [50, 0.5, 0.1, 2.0, 45, 0.02, 0.1, 1, 60.0, 5.0]}'

# Expected: {"prediction": 1, "attack_type": "Brute Force"}
```

### Run All Tests
```bash
./venv/bin/python3 test_new_ml_models.py
```

Expected output: `ALL TESTS COMPLETED: 10/10 PASSED`

---

## 📋 Available Models

| Model | Endpoint | Accuracy |
|-------|----------|----------|
| Web Attack | `/api/detect/web-attack` | 93.97% |
| DDoS | `/api/detect/ddos` | 95.88% |
| **XSS** | `/api/detect/xss` | **100%** |
| **Brute Force** | `/api/detect/brute-force` | **100%** |
| **Port Scan** | `/api/detect/port-scan` | **100%** |
| **Credential Stuffing** | `/api/detect/credential-stuffing` | **100%** |
| **Anomaly** | `/api/detect/anomaly` | **87%** |

---

## 📖 Documentation

- **Complete Guide**: `NEW_ML_MODELS_COMPLETION_REPORT.md`
- **API Reference**: `ML_MODELS_QUICK_REFERENCE.md`
- **Session Summary**: `SESSION_FINAL_SUMMARY.md`

---

## 🔄 Retrain Models (Optional)

```bash
# Regenerate datasets
./venv/bin/python3 ml_pipeline/data_generation/generate_xss_data.py
./venv/bin/python3 ml_pipeline/data_generation/generate_brute_force_data.py
./venv/bin/python3 ml_pipeline/data_generation/generate_port_scan_data.py
./venv/bin/python3 ml_pipeline/data_generation/generate_credential_stuffing_data.py
./venv/bin/python3 ml_pipeline/data_generation/generate_anomaly_data.py

# Retrain models
./venv/bin/python3 ml_pipeline/training/train_xss.py
./venv/bin/python3 ml_pipeline/training/train_brute_force.py
./venv/bin/python3 ml_pipeline/training/train_port_scan.py
./venv/bin/python3 ml_pipeline/training/train_credential_stuffing.py
./venv/bin/python3 ml_pipeline/training/train_anomaly.py

# Restart ML API
pkill -f model_api.py
./venv/bin/python3 ml_pipeline/model_api.py
```

---

## ✅ Verification Checklist

- [ ] ML API running on port 5000
- [ ] Health check shows 7/7 models loaded
- [ ] XSS test detects malicious payload
- [ ] Brute force test detects attack pattern
- [ ] All 10 tests pass in test suite

---

**Status**: ✅ All 7 models operational  
**Version**: ML API 3.0.0  
**Last Updated**: April 18, 2026
