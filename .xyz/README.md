# AI-Driven Cyber Deception System with Dynamic Honeypots

## 🎯 Project Overview

An advanced cybersecurity system that combines Deep Learning-based attack detection with dynamic honeypots featuring adaptive strategies. This final-year project deploys AI models to detect Web Attacks (SQLi, NoSQLi, XSS) and DDoS attacks in real-time, while using deceptive honeypots with IP/port rotation to confuse attackers.

### Key Features

- **🤖 Deep Learning Detection Models**
  - Web Attack Detector (SQLi, NoSQLi, XSS)
  - DDoS Attack Detector
  - ANN/MLP architecture with 2 hidden layers
  - Binary classification output (Attack/Benign)
  - 90%+ accuracy on test data

- **🍯 Dynamic Honeypots**
  -10 honeypot instances (5 legitimate + 5 deceptive)
  - Identical UI for deception
  - Automatic IP/port rotation
  - Configurable rotation intervals
  - Comprehensive logging

- **📊 Adaptive Learning**
  - Wazuh integration for log collection
  - Continuous model retraining
  - Model versioning and rollback
  - Feedback loop for improvement

- **☁️ Cloud Deployment**
  - Docker containerization
  - Kubernetes orchestration
  - Load balancing
  - Auto-scaling
  - Health monitoring

## 📁 Project Structure

```
Ahmed Fype-II/
├── Datasets/                      # Training datasets
│   ├── DDoS/                     # DDoS attack datasets (10 files)
│   └── SQLI-nosqli-XSS/          # Web attack datasets (11 files)
├── ml_pipeline/                   # Machine Learning Pipeline
│   ├── preprocessing.py          # Data preprocessing module
│   ├── web_attack_model.py       # Web Attack ANN model
│   ├── ddos_model.py             # DDoS ANN model
│   ├── train_web_attack.py       # Training script for Web Attack
│   ├── train_ddos.py             # Training script for DDoS
│   └── model_api.py              # Flask REST API for inference
├── honeypot/                      # Honeypot System
│   ├── app.py                    # Flask honeypot application
│   ├── logger.py                 # Comprehensive logging
│   ├── rotation_manager.py       # IP/Port rotation manager
│   └── templates/                # HTML templates
├── docker/                        # Docker configurations
│   ├── ml-api.Dockerfile         # ML API Docker image
│   ├── honeypot.Dockerfile       # Honeypot Docker image
│   └── docker-compose.yml        # Local development setup
├── kubernetes/                    # Kubernetes manifests
│   ├── ml-api-deployment.yaml    # ML API deployment
│   ├── honeypot-deployment.yaml  # Honeypot deployment
│   └── ingress.yaml              # Ingress configuration
├── adaptive_learning/             # Adaptive Learning Module
│   ├── log_processor.py          # Wazuh log processing
│   ├── retrain_pipeline.py       # Automated retraining
│   └── continuous_learning.py    # Continuous learning orchestrator
├── dashboard/                     # Monitoring Dashboard
│   ├── app.py                    # Dashboard Flask app
│   └── templates/                # Dashboard UI
├── wazuh/                         # Wazuh Configuration
│   └── ossec.conf                # Wazuh config file
├── config/                        # Configuration files
│   └── config.yaml               # Central configuration
└── scripts/                       # Utility scripts
    ├── setup.sh                  # Initial setup
    └── deploy.sh                 # Deployment script
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- Kubernetes cluster (minikube for local, GKE/EKS/AKS for production)
- kubectl installed and configured

### 1. Clone and Setup

```bash
cd "Ahmed Fype-II"

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Train ML Models

```bash
# Train Web Attack Detection Model
cd ml_pipeline
python train_web_attack.py

# Train DDoS Detection Model
python train_ddos.py
```

Expected output:
- Models saved to `models/` directory
- Training plots in `plots/` directory
- Accuracy > 90% on test data

### 3. Start ML API

```bash
# From ml_pipeline directory
python model_api.py
```

API will be available at `http://localhost:5000`

### 4. Test ML API

```bash
curl -X POST http://localhost:5000/api/detect/web-attack \
  -H "Content-Type: application/json" \
  -d '{"features": [...]}'
```

### 5. Run Honeypot (Local)

```bash
# From honeypot directory
export HONEYPOT_TYPE=deceptive
export HONEYPOT_SERVICE=ecommerce
export ML_API_URL=http://localhost:5000

python app.py
```

Honeypot will be available at `http://localhost:8080`

### 6. Deploy with Docker Compose

```bash
# Build and run all services
docker-compose -f docker/docker-compose.yml up --build
```

Services:
- ML API: http://localhost:5000
- Honeypot instances: http://localhost:8080-8089
- Wazuh: http://localhost:55000

### 7. Deploy to Kubernetes

```bash
# Apply Kubernetes manifests
kubectl apply -f kubernetes/

# Check deployment status
kubectl get pods
kubectl get services
```

## 📊 ML Models

### Architecture

Both models use identical ANN/MLP architecture:

```
Input Layer (n features)
      ↓
Hidden Layer 1 (128 neurons, ReLU)
      ↓
Dropout (0.3)
      ↓
Batch Normalization
      ↓
Hidden Layer 2 (64 neurons, ReLU)
      ↓
Dropout (0.3)
      ↓
Batch Normalization
      ↓
Output Layer (1 neuron, Sigmoid)
      ↓
Binary Output: 0 (Benign) / 1 (Attack)
```

### Training Details

- **Optimizer**: Adam (lr=0.001)
- **Loss**: Binary Cross-Entropy
- **Metrics**: Accuracy, Precision, Recall, AUC, F1-Score
- **Callbacks**: Early Stopping, Learning Rate Reduction, Model Checkpointing
- **Data Split**: 70% Train, 10% Validation, 20% Test

### Model Performance

| Model | Accuracy | Precision | Recall | F1-Score |
|-------|----------|-----------|--------|----------|
| Web Attack Detector | >90% | >90% | >90% | >90% |
| DDoS Detector | >90% | >90% | >90% | >90% |

## 🍯 Honeypot System

### Honeypot Types

1. **Legitimate Websites** (5 instances)
   - Serve real users
   - Normal functionality
   - Response to legitimate requests

2. **Deceptive Honeypots** (5 instances)
   - Identical UI to legitimate sites
   - Log all interactions
   - Detect and analyze attacks
   - Always fail authentication

### Services Mimicked

- E-commerce platform
- Banking portal
- Admin dashboard
- API server
- Corporate website

### IP/Port Rotation

- **Rotation Interval**: Configurable (default: 5 minutes)
- **IP Pool**: 10.0.1.10 - 10.0.1.19
- **Port Pool**: 8080 - 8089
- **Coordination**: Prevents multiple attackers from detecting pattern
- **Implementation**: Kubernetes service updates

## 📈 Adaptive Learning

### Workflow

1. **Log Collection**
   - Wazuh collects logs from all honeypots
   - Centralized log storage
   - Real-time monitoring

2. **Feature Extraction**
   - Parse Wazuh logs
   - Extract attack features
   - Generate labels from alerts

3. **Model Retraining**
   - Scheduled retraining (daily/weekly)
   - Incremental learning
   - Performance comparison

4. **Deployment**
   - Deploy improved model
   - A/B testing
   - Rollback if performance degrades

## 🔧 Configuration

### ML API Configuration

```yaml
# config/config.yaml
ml_api:
  host: 0.0.0.0
  port: 5000
  models:
    web_attack:
      path: models/web_attack_detector.keras
      preprocessor: models/web_attack_preprocessor.pkl
    ddos:
      path: models/ddos_detector.keras
      preprocessor: models/ddos_preprocessor.pkl
```

### Honeypot Configuration

```yaml
honeypot:
  instances: 10
  rotation_interval: 300  # seconds
  services:
    - ecommerce
    - banking
    - admin
    - api
    - corporate
```

### Rotation Configuration

```json
{
  "rotation_interval_seconds": 300,
  "ip_pool": ["10.0.1.10", "10.0.1.11", ...],
  "port_pool": [8080, 8081, 8082, ...],
  "kubernetes_enabled": true,
  "kubernetes_namespace": "honeypot"
}
```

## 📚 API Documentation

### Web Attack Detection

```http
POST /api/detect/web-attack
Content-Type: application/json

{
  "features": [feature1, feature2, ..., featureN]
}
```

**Response:**
```json
{
  "prediction": 1,
  "confidence": 0.95,
  "attack_type": "Web Attack (SQLi/NoSQLi/XSS)",
  "is_malicious": true,
  "timestamp": "2026-02-08T00:45:00"
}
```

### DDoS Detection

```http
POST /api/detect/ddos
Content-Type: application/json

{
  "features": [feature1, feature2, ..., featureN]
}
```

### Health Check

```http
GET /api/health
```

## 🧪 Testing

### Unit Tests

```bash
pytest ml_pipeline/tests/test_preprocessing.py
pytest ml_pipeline/tests/test_models.py
pytest honeypot/tests/test_rotation.py
```

### Integration Tests

```bash
pytest tests/integration/test_e2e_detection.py
pytest tests/integration/test_adaptive_learning.py
```

### Manual Testing

1. Send legitimate request → Expect 0/False
2. Send SQLi payload → Expect 1/True  
3. Send DDoS traffic → Expect 1/True
4. Verify IP/port rotation occurs
5. Check Wazuh logs

## 📊 Monitoring

### Dashboard

Access the monitoring dashboard at `http://localhost:3000`

Features:
- Real-time attack visualization
- Detection statistics
- Honeypot health status
- Model performance metrics
- Wazuh alert feed

### Metrics

- Total requests handled
- Attacks detected
- False positive rate
- Model accuracy over time
- Rotation status

## 🔐 Security Considerations

- All honeypots run in isolated network segments
- ML models trained on sanitized data
- Logs encrypted at rest
- API authentication required in production
- Regular security audits

## 🤝 Contributing

This is a final-year project. For improvements or suggestions:

1. Fork the repository
2. Create feature branch
3. Make changes
4. Submit pull request

## 📝 License

Educational/Academic Use Only

## 👥 Authors

Final Year Project - Cybersecurity & AI

## 🙏 Acknowledgments

- Dataset providers
- Wazuh community
- TensorFlow/Keras team
- Kubernetes community

## 📞 Support

For issues or questions, please create an issue in the repository.

---

**Note**: This system is designed for educational and research purposes. Deploy responsibly and in compliance with applicable laws and regulations.
