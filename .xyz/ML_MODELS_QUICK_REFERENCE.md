# ML Models Quick Reference Guide

Quick reference for using all 7 ML detection models in DeceptiCloud.

---

## 🚀 Quick Start

### Start ML API
```bash
./venv/bin/python3 ml_pipeline/model_api.py
```

### Check Health
```bash
curl http://localhost:5000/api/health
```

### Get Model Info
```bash
curl http://localhost:5000/api/model-info
```

---

## 📋 MODEL REFERENCE

### 1. Web Attack Detector (Existing)
**Detects**: SQLi, NoSQLi, XSS, Path Traversal, Command Injection  
**Endpoint**: `POST /api/detect/web-attack`  
**Input**: Feature vector (23 features)  
**Accuracy**: 93.97%

```bash
curl -X POST http://localhost:5000/api/detect/web-attack \
  -H "Content-Type: application/json" \
  -d '{"features": [100, 50, 20, 0, 1, 0, 10, 0, 0, 0, 5, 3, 1, 50, 10, 2, 1, 1, 0, 1, 100, 0, 0]}'
```

### 2. DDoS Detector (Existing)
**Detects**: DDoS attacks  
**Endpoint**: `POST /api/detect/ddos`  
**Input**: Feature dict or vector (30 features)  
**Accuracy**: 95.88%

```bash
curl -X POST http://localhost:5000/api/detect/ddos \
  -H "Content-Type: application/json" \
  -d '{"features": {...}}'
```

### 3. XSS Detector (NEW)
**Detects**: Cross-Site Scripting attacks  
**Endpoint**: `POST /api/detect/xss`  
**Input**: Text string  
**Accuracy**: 100%

```bash
# Malicious
curl -X POST http://localhost:5000/api/detect/xss \
  -H "Content-Type: application/json" \
  -d '{"text": "<script>alert(1)</script>"}'

# Benign
curl -X POST http://localhost:5000/api/detect/xss \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}'
```

### 4. Brute Force Detector (NEW)
**Detects**: Brute force login attacks  
**Endpoint**: `POST /api/detect/brute-force`  
**Input**: Feature vector (10 features)  
**Accuracy**: 100%

**Features**:
1. num_attempts
2. avg_time_between_attempts
3. min_time_between_attempts
4. max_time_between_attempts
5. unique_usernames
6. success_rate
7. avg_response_time
8. has_brute_force_ua (0 or 1)
9. attempts_per_minute
10. password_length_variance

```bash
# Attack pattern
curl -X POST http://localhost:5000/api/detect/brute-force \
  -H "Content-Type: application/json" \
  -d '{"features": [50, 0.5, 0.1, 2.0, 45, 0.02, 0.1, 1, 60.0, 5.0]}'

# Normal pattern
curl -X POST http://localhost:5000/api/detect/brute-force \
  -H "Content-Type: application/json" \
  -d '{"features": [3, 30.0, 15.0, 60.0, 1, 0.67, 0.3, 0, 2.0, 2.0]}'
```

### 5. Port Scan Detector (NEW)
**Detects**: Port scanning attacks  
**Endpoint**: `POST /api/detect/port-scan`  
**Input**: Feature vector (12 features)  
**Accuracy**: 100%

**Features**:
1. num_ports_accessed
2. unique_ports
3. avg_time_between_accesses
4. min_time_between_accesses
5. max_time_between_accesses
6. avg_port_diff
7. sequential_pattern (0 or 1)
8. ports_per_second
9. has_scan_ua (0 or 1)
10. avg_response_time
11. common_ports_ratio
12. high_port_ratio

```bash
# Scan pattern
curl -X POST http://localhost:5000/api/detect/port-scan \
  -H "Content-Type: application/json" \
  -d '{"features": [50, 50, 0.05, 0.01, 0.1, 1.0, 1, 10.0, 1, 0.02, 0.2, 0.8]}'

# Normal pattern
curl -X POST http://localhost:5000/api/detect/port-scan \
  -H "Content-Type: application/json" \
  -d '{"features": [3, 3, 10.0, 5.0, 20.0, 100.0, 0, 0.1, 0, 0.2, 1.0, 0.0]}'
```

### 6. Credential Stuffing Detector (NEW)
**Detects**: Credential stuffing attacks  
**Endpoint**: `POST /api/detect/credential-stuffing`  
**Input**: Feature vector (12 features)  
**Accuracy**: 100%

**Features**:
1. num_attempts
2. avg_time_between_attempts
3. min_time_between_attempts
4. attempts_per_minute
5. unique_ips
6. unique_user_agents
7. unique_usernames
8. ip_rotation_rate
9. ua_rotation_rate
10. username_rotation_rate
11. success_rate
12. avg_response_time

```bash
# Attack pattern
curl -X POST http://localhost:5000/api/detect/credential-stuffing \
  -H "Content-Type: application/json" \
  -d '{"features": [100, 0.5, 0.1, 120.0, 10, 5, 80, 0.1, 0.05, 0.8, 0.05, 0.1]}'

# Normal pattern
curl -X POST http://localhost:5000/api/detect/credential-stuffing \
  -H "Content-Type: application/json" \
  -d '{"features": [5, 30.0, 10.0, 2.0, 1, 1, 1, 0.2, 0.2, 0.2, 0.6, 0.3]}'
```

### 7. Anomaly Detector (NEW)
**Detects**: Anomalous/unusual requests  
**Endpoint**: `POST /api/detect/anomaly`  
**Input**: Feature vector (21 features)  
**Accuracy**: 87%

**Features**:
1. method_is_get (0 or 1)
2. method_is_post (0 or 1)
3. method_is_unusual (0 or 1)
4. query_length
5. body_length
6. num_headers
7. has_auth (0 or 1)
8. response_code
9. response_time
10. num_params
11. special_chars_count
12. path_depth
13. path_length
14. has_suspicious_ua (0 or 1)
15. ua_length
16. has_suspicious_path (0 or 1)
17. has_traversal (0 or 1)
18. response_is_error (0 or 1)
19. response_is_redirect (0 or 1)
20. fast_response (0 or 1)
21. slow_response (0 or 1)

```bash
# Anomalous request
curl -X POST http://localhost:5000/api/detect/anomaly \
  -H "Content-Type: application/json" \
  -d '{"features": [0, 0, 1, 5000, 50000, 30, 0, 404, 0.01, 50, 200, 10, 200, 1, 50, 1, 1, 1, 0, 1, 0]}'

# Normal request
curl -X POST http://localhost:5000/api/detect/anomaly \
  -H "Content-Type: application/json" \
  -d '{"features": [1, 0, 0, 20, 100, 10, 1, 200, 0.2, 2, 5, 2, 30, 0, 100, 0, 0, 0, 0, 0, 0]}'
```

---

## 🧪 TESTING

### Run All Tests
```bash
./venv/bin/python3 test_new_ml_models.py
```

### Test Individual Model
```python
import requests

# Test XSS
response = requests.post(
    "http://localhost:5000/api/detect/xss",
    json={"text": "<script>alert(1)</script>"}
)
print(response.json())
```

---

## 🔄 RETRAINING MODELS

### Regenerate Dataset
```bash
./venv/bin/python3 ml_pipeline/data_generation/generate_xss_data.py
./venv/bin/python3 ml_pipeline/data_generation/generate_brute_force_data.py
./venv/bin/python3 ml_pipeline/data_generation/generate_port_scan_data.py
./venv/bin/python3 ml_pipeline/data_generation/generate_credential_stuffing_data.py
./venv/bin/python3 ml_pipeline/data_generation/generate_anomaly_data.py
```

### Retrain Model
```bash
./venv/bin/python3 ml_pipeline/training/train_xss.py
./venv/bin/python3 ml_pipeline/training/train_brute_force.py
./venv/bin/python3 ml_pipeline/training/train_port_scan.py
./venv/bin/python3 ml_pipeline/training/train_credential_stuffing.py
./venv/bin/python3 ml_pipeline/training/train_anomaly.py
```

### Restart ML API
```bash
pkill -f model_api.py
./venv/bin/python3 ml_pipeline/model_api.py
```

---

## 📊 RESPONSE FORMAT

All detection endpoints return:

```json
{
  "prediction": 0 or 1,
  "confidence": 0.0 to 1.0,
  "attack_type": "Attack Type" or "Benign/Normal",
  "is_malicious": true or false,
  "timestamp": "ISO 8601 timestamp"
}
```

Anomaly detector also includes:
```json
{
  "anomaly_score": -1.0 to 0.0
}
```

---

## 🐛 TROUBLESHOOTING

### Model Not Loaded
**Symptom**: `"error": "XSS Detector not loaded"`  
**Solution**: Check if model files exist in `ml_pipeline/models/`

### Feature Count Mismatch
**Symptom**: `"error": "Expected X features, got Y"`  
**Solution**: Verify feature vector length matches model requirements

### Low Confidence
**Symptom**: Predictions with confidence < 0.5  
**Solution**: Check if input features are scaled correctly or retrain model

### API Not Responding
**Symptom**: Connection refused  
**Solution**: Ensure ML API is running on port 5000

---

## 📚 FEATURE EXTRACTION EXAMPLES

### Brute Force Features (Python)
```python
def extract_brute_force_features(login_attempts):
    timestamps = [a['timestamp'] for a in login_attempts]
    time_diffs = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
    
    return [
        len(login_attempts),  # num_attempts
        sum(time_diffs) / len(time_diffs),  # avg_time_between_attempts
        min(time_diffs),  # min_time_between_attempts
        max(time_diffs),  # max_time_between_attempts
        len(set(a['username'] for a in login_attempts)),  # unique_usernames
        sum(1 for a in login_attempts if a['success']) / len(login_attempts),  # success_rate
        sum(a['response_time'] for a in login_attempts) / len(login_attempts),  # avg_response_time
        1 if 'hydra' in login_attempts[0]['user_agent'].lower() else 0,  # has_brute_force_ua
        len(login_attempts) / ((timestamps[-1] - timestamps[0]) / 60),  # attempts_per_minute
        sum((a['password_length'] - 8) ** 2 for a in login_attempts) / len(login_attempts)  # password_length_variance
    ]
```

### Port Scan Features (Python)
```python
def extract_port_scan_features(port_accesses):
    timestamps = [a['timestamp'] for a in port_accesses]
    ports = [a['port'] for a in port_accesses]
    time_diffs = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
    port_diffs = [abs(ports[i+1] - ports[i]) for i in range(len(ports)-1)]
    
    common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 3306, 3389, 5432, 8080, 8443]
    
    return [
        len(ports),  # num_ports_accessed
        len(set(ports)),  # unique_ports
        sum(time_diffs) / len(time_diffs),  # avg_time_between_accesses
        min(time_diffs),  # min_time_between_accesses
        max(time_diffs),  # max_time_between_accesses
        sum(port_diffs) / len(port_diffs),  # avg_port_diff
        1 if sum(1 for d in port_diffs if d == 1) / len(port_diffs) > 0.5 else 0,  # sequential_pattern
        len(ports) / (timestamps[-1] - timestamps[0]),  # ports_per_second
        1 if 'nmap' in port_accesses[0]['user_agent'].lower() else 0,  # has_scan_ua
        sum(a['response_time'] for a in port_accesses) / len(port_accesses),  # avg_response_time
        sum(1 for p in ports if p in common_ports) / len(ports),  # common_ports_ratio
        sum(1 for p in ports if p > 1024) / len(ports)  # high_port_ratio
    ]
```

---

## 🎯 USE CASES

### XSS Detector
- Input validation for forms
- URL parameter sanitization
- Comment/review filtering

### Brute Force Detector
- Login endpoint protection
- API authentication monitoring
- Account lockout decisions

### Port Scan Detector
- Network intrusion detection
- Firewall rule generation
- Attacker profiling

### Credential Stuffing Detector
- Account takeover prevention
- Bot detection
- Rate limiting decisions

### Anomaly Detector
- Zero-day attack detection
- Baseline deviation alerts
- Unknown threat identification

---

**Last Updated**: April 18, 2026  
**ML API Version**: 3.0.0  
**Total Models**: 7
