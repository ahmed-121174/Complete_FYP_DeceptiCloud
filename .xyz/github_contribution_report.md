# DeceptiCloud — GitHub Repository Branch & Contribution Report

**Project:** DeceptiCloud — AI-Driven Cyber Deception System using Dynamic Honeypots in Cloud Environment
**Team:** Ahmed Ali · Shoaib · Waleed

---

## Branch Overview

| Branch | Purpose |
|--------|---------|
| `main` | Final integrated, production-ready version |
| `Ahmed` | Files primarily implemented by Ahmed Ali |
| `Shoaib` | Files primarily implemented by Shoaib |
| `Waleed` | Files primarily implemented by Waleed |
| `challenges` | Experimental/non-integrated work (subdivided by member) |

---

## Branch: `main`

Contains the fully integrated system — all files merged and tested together.

> All files listed under the individual branches (`Ahmed`, `Shoaib`, `Waleed`) are present here in their final, integrated state.

---

## Branch: `Ahmed`

Ahmed led the core AI gateway, ML inference pipeline, blockchain ledger, and system orchestration.

### Routing Proxy (AI Gateway)
| File | Role |
|------|------|
| [proxy/routing_proxy.py](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/proxy/routing_proxy.py) | Central AI traffic classification and routing engine |

### ML Pipeline — Inference API & Web Attack Training
| File | Role |
|------|------|
| [ml_pipeline/model_api.py](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/ml_pipeline/model_api.py) | REST API serving both ML models (web attack + DDoS) |
| [ml_pipeline/train_web_attack_v2.py](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/ml_pipeline/train_web_attack_v2.py) | Web Attack Detector V2 training script (active model) |
| [ml_pipeline/web_attack_model.py](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/ml_pipeline/web_attack_model.py) | Web attack model class and inference wrapper |
| [ml_pipeline/feature_engineering.py](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/ml_pipeline/feature_engineering.py) | Feature engineering utilities for both models |
| [ml_pipeline/preprocessing.py](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/ml_pipeline/preprocessing.py) | Input preprocessing and normalization pipeline |
| [ml_pipeline/models/web_attack_detector_v2.keras](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/ml_pipeline/models/web_attack_detector_v2.keras) | Trained Web Attack Detector V2 (ANN) |
| [ml_pipeline/models/web_attack_detector_v2.json](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/ml_pipeline/models/web_attack_detector_v2.json) | Web Attack model metadata |
| [ml_pipeline/models/web_attack_preprocessor_scaler.pkl](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/ml_pipeline/models/web_attack_preprocessor_scaler.pkl) | Web attack feature scaler |
| [ml_pipeline/models/web_attack_threshold.txt](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/ml_pipeline/models/web_attack_threshold.txt) | Classification threshold for web attack model |

### Blockchain Ledger
| File | Role |
|------|------|
| [honeypot/blockchain_ledger.py](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/honeypot/blockchain_ledger.py) | Custom SHA-256 blockchain for tamper-proof attack logging |

### System Configuration & Orchestration
| File | Role |
|------|------|
| [config.py](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/config.py) | Central system configuration (ports, thresholds, feature order, GAN params) |
| [launch_decepticloud.py](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/launch_decepticloud.py) | Single-script system launcher |
| [config/rotation_config.json](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/config/rotation_config.json) | Runtime honeypot rotation configuration |

### Jury Presentation Scripts
| File | Role |
|------|------|
| [Jury_presentation_final/scripts/1_START_SYSTEM.sh](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/Jury_presentation_final/scripts/1_START_SYSTEM.sh) | Full system startup script |
| [Jury_presentation_final/scripts/STOP_ALL.sh](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/Jury_presentation_final/scripts/STOP_ALL.sh) | System shutdown script |
| [Jury_presentation_final/PROJECT_ARCHITECTURE.md](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/Jury_presentation_final/PROJECT_ARCHITECTURE.md) | System architecture documentation |
| [Jury_presentation_final/JURY_GUIDE.md](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/Jury_presentation_final/JURY_GUIDE.md) | Jury walkthrough guide |
| [Jury_presentation_final/README.md](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/Jury_presentation_final/README.md) | Repository README |

### Docker — Core Services
| File | Role |
|------|------|
| [docker/docker-compose.yml](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/docker/docker-compose.yml) | Full 17-service orchestration definition |
| [docker/proxy.Dockerfile](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/docker/proxy.Dockerfile) | Routing proxy container build |
| [docker/ml-api.Dockerfile](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/docker/ml-api.Dockerfile) | ML API container build |

### Kubernetes Manifests
| File | Role |
|------|------|
| [kubernetes/namespace.yaml](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/kubernetes/namespace.yaml) | DeceptiCloud namespace definition |
| [kubernetes/cyber-deception.yaml](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/kubernetes/cyber-deception.yaml) | Full system Kubernetes deployment manifest |
| [kubernetes/ml-api-deployment.yaml](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/kubernetes/ml-api-deployment.yaml) | ML API pod deployment and service |
| [kubernetes/honeypot-deployment.yaml](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/kubernetes/honeypot-deployment.yaml) | Honeypot pods deployment and service |

### Setup & Environment Scripts
| File | Role |
|------|------|
| [scripts/setup.sh](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/scripts/setup.sh) | Full environment setup and dependency installation |
| [scripts/presample_ddos_data.sh](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/scripts/presample_ddos_data.sh) | DDoS dataset pre-sampling utility script |

### Unit Tests — Core Modules
| File | Role |
|------|------|
| [tests/conftest.py](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/tests/conftest.py) | Shared pytest fixtures and test configuration |
| [tests/test_config.py](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/tests/test_config.py) | Unit tests for [config.py](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/config.py) values and environment overrides |
| [tests/test_proxy.py](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/tests/test_proxy.py) | Unit tests for proxy feature extraction and classification logic |
| [tests/test_ml_api.py](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/tests/test_ml_api.py) | Unit tests for ML API prediction endpoints |

---

## Branch: `Shoaib`

Shoaib led the LLM deception engine, canary token system, website honeypot applications, and attack simulation scripts.

### LLM Adaptive Response Engine
| File | Role |
|------|------|
| [honeypot/llm_response_engine.py](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/honeypot/llm_response_engine.py) | Ollama-based LLM integration for generating deceptive HTML responses |

### Canary Token System
| File | Role |
|------|------|
| [honeypot/canary_tokens.py](file:///media/amei-302/New%20Volume/SEMESTER%20VIII/Ahmed%20Fype-II/honeypot/canary_tokens.py) | Flask Blueprint serving trap routes (`.env`, `.git`, `backup.sql`, `wp-admin`, etc.) |

### Honeypot Web Applications — Sites
| File | Role |
|------|------|
| `websites/banking/` | SecureBank honeypot and real site (templates + static assets) |
| `websites/ecommerce/` | MegaStore honeypot and real site |
| `websites/corporate/` | NexaGen Corp honeypot and real site |
| `websites/run_all.py` | Script to launch all 14 website Flask processes |

### Attack Simulation Scripts
| File | Role |
|------|------|
| `attacks/web_attacks.sh` | 16-attack red-team simulation (SQLi, XSS, Path Traversal, CMDi) |
| `Jury_presentation_final/scripts/2_WEB_ATTACKS.sh` | Jury-ready web attack demo script |

### Docker — Website Services
| File | Role |
|------|------|
| `docker/website.Dockerfile` | Shared Dockerfile for all 14 real/honeypot websites |
| `docker/honeypot.Dockerfile` | Honeypot-specific container configuration |

### ML Pipeline — DDoS Training
| File | Role |
|------|------|
| `ml_pipeline/ddos_model.py` | DDoS model wrapper and inference logic |
| `ml_pipeline/train_ddos.py` | DDoS model training script |
| `ml_pipeline/models/ddos_preprocessor_scaler.pkl` | DDoS feature scaler |

### Unit Tests — Deception Modules
| File | Role |
|------|------|
| `tests/test_honeypot_modules.py` | Unit tests for blockchain, canary tokens, fingerprint modules |
| `tests/integration/test_proxy_honeypot_routing.py` | Integration tests for proxy-to-honeypot routing decisions |

---

## Branch: `Waleed`

Waleed led the behavioral fingerprinting engine, GAN synthetic data generator, SOC dashboard, and DDoS infrastructure.

### Behavioral Fingerprinting
| File | Role |
|------|------|
| `honeypot/behavioral_fingerprint.py` | Browser/behavioral profiling and distance-based attacker clustering |

### GAN Synthetic Data Generator
| File | Role |
|------|------|
| `honeypot/gan_data_generator.py` | WGAN-GP model for generating realistic synthetic user profiles |
| `honeypot/train_gan.py` | GAN training entry point |
| `honeypot/rotation_manager.py` | Honeypot rotation management logic |

### SOC Dashboard
| File | Role |
|------|------|
| `dashboard/app.py` | Dashboard Flask backend — all API endpoints and aggregation logic |
| `dashboard/templates/dashboard.html` | Full dashboard frontend HTML (9 monitoring panels) |
| `dashboard/static/dashboard.js` | Dashboard JavaScript — live polling, charts, infrastructure health panel |

### Honeypot Web Applications — Sites
| File | Role |
|------|------|
| `websites/healthcare/` | MedCore honeypot and real site |
| `websites/blog/` | TechBlog honeypot and real site |
| `websites/api_service/` | DataAPI honeypot and real site |
| `websites/admin_panel/` | SysNet Admin honeypot and real site |

### DDoS Detection & Infrastructure
| File | Role |
|------|------|
| `DDoS/V1/train_model.py` | DDoS Random Forest model training script |
| `DDoS/V1/preprocessing.py` | DDoS-specific data preprocessing |
| `DDoS/V1/predict.py` | DDoS prediction utility |
| `DDoS/V1/models/best_model.pkl` | Trained DDoS Random Forest model |
| `DDoS/V1/models/scaler.pkl` | DDoS feature scaler |
| `DDoS/V1/models/selected_features.pkl` | Selected DDoS feature list |
| `attacks/ddos_attack.sh` | DDoS red-team simulation + K8s watchdog recovery |
| `Jury_presentation_final/scripts/3_DDOS_ATTACK.sh` | Jury-ready DDoS demo script |
| `Jury_presentation_final/scripts/4_NARRATED_DEMO.sh` | Full narrated jury demo script |

### Docker — Dashboard
| File | Role |
|------|------|
| `docker/dashboard.Dockerfile` | Dashboard container build |

### Website Shared Infrastructure & Databases
| File | Role |
|------|------|
| `websites/shared/site_factory.py` | Factory that builds Flask app instances for any site type/variant |
| `websites/shared/db_seeder.py` | Seeds all 14 SQLite databases (real + honeypot) with GAN-generated users |
| `websites/databases/banking_honeypot.db` | Banking honeypot SQLite database (GAN-populated) |
| `websites/databases/banking_real.db` | Banking real site SQLite database |
| `websites/databases/ecommerce_honeypot.db` | E-commerce honeypot database |
| `websites/databases/ecommerce_real.db` | E-commerce real site database |
| `websites/databases/healthcare_honeypot.db` | Healthcare honeypot database |
| `websites/databases/healthcare_real.db` | Healthcare real site database |
| `websites/databases/blog_honeypot.db` | Blog honeypot database |
| `websites/databases/blog_real.db` | Blog real site database |
| `websites/databases/api_service_honeypot.db` | API service honeypot database |
| `websites/databases/api_service_real.db` | API service real site database |
| `websites/databases/corporate_honeypot.db` | Corporate honeypot database |
| `websites/databases/corporate_real.db` | Corporate real site database |
| `websites/databases/admin_panel_honeypot.db` | Admin panel honeypot database |
| `websites/databases/admin_panel_real.db` | Admin panel real site database |

### Unit & System Tests — Dashboard & End-to-End
| File | Role |
|------|------|
| `tests/test_dashboard.py` | Unit tests for dashboard API endpoints |
| `tests/test_gan_generator.py` | Unit tests for GAN generation, watermarking, and validation |
| `tests/test_launch_script.py` | Tests for system launch script behaviour |
| `tests/integration/test_dashboard_api.py` | Integration tests for dashboard data aggregation endpoints |
| `tests/integration/test_proxy_ml_integration.py` | Integration tests for proxy ↔ ML API classification flow |
| `tests/system/test_full_attack_flow.py` | End-to-end system test: attack → detection → honeypot → blockchain → dashboard |

---

## Branch: `challenges`

Experimental and non-integrated work that was explored but excluded from the final implementation due to technical limitations such as overfitting, training instability, or architectural mismatches.

---

### Ahmed — Challenges

These files represent Ahmed's exploration of alternative DDoS detection approaches and early ML API designs.

| File | Reason for Exclusion |
|------|---------------------|
| `ml_pipeline/train_web_attack_ensemble.py` | Ensemble (stacking) experiment — high complexity, marginal accuracy gain |
| `ml_pipeline/train_web_attack_fixed.py` | Bugfix training attempt — superseded by V2 architecture |
| `ml_pipeline/evaluate_web_attack_v2.py` | Standalone evaluation script — superseded by model metadata JSON |
| `ml_pipeline/investigate_misclassified.py` | Misclassification analysis utility — research use only |
| `ml_pipeline/models/web_attack_detector.keras` | V1 web attack model — lower balanced accuracy |
| `ml_pipeline/models/web_attack_detector.json` | V1 model metadata |
| `ml_pipeline/models/web_attack_detector_fixed.keras` | Fixed V1 model — still underperformed V2 |
| `ml_pipeline/models/web_attack_detector_fixed.json` | Fixed V1 metadata |
| `ml_pipeline/models/web_attack_best_model.keras` | Best of V1 family — still replaced by V2 |
| `ml_pipeline/data_quality/` | Data quality investigation scripts — exploratory, not production |
| `ml_pipeline/DATA_QUALITY_INVESTIGATION.md` | Data quality analysis notes |

---

### Shoaib — Challenges

These files represent Shoaib's exploration of alternative web attack detection strategies and ensemble approaches.

| File | Reason for Exclusion |
|------|---------------------|
| `ml_pipeline/train_ddos_sampled.py` | Sampled DDoS training experiment — produced lower balanced accuracy than V1 |
| `ml_pipeline/models/ddos_detector.keras` | Early Keras-based DDoS model — inferior to Random Forest V1 |
| `ml_pipeline/models/ddos_best_model.keras` | Alternate Keras DDoS attempt |
| `ml_pipeline/models/ddos_detector.json` | Metadata for the excluded Keras DDoS model |
| `ml_pipeline/models/ddos_preprocessor.pkl` | Large preprocessor for the excluded Keras DDoS model |
| `ml_pipeline/models/ddos_preprocessor_metadata.json` | Metadata for excluded DDoS preprocessor |
| `DDoS/V1/retrain_honest.py` | Retraining attempt targeting specific metrics — unstable convergence |
| `ml_pipeline/models/web_attack_tfidf.pkl` | TF-IDF vectorizer from ensemble experiment |
| `ml_pipeline/models/web_attack_feature_extractor.pkl` | Custom feature extractor — not compatible with V2 pipeline |
| `ml_pipeline/models/web_attack_preprocessor_fixed.pkl` | Large preprocessor from fixed-V1 training |
| `ml_pipeline/models/web_attack_preprocessor_metadata.json` | Metadata for excluded preprocessor |

---

### Waleed — Challenges

These files represent Waleed's exploration of alternative model architectures, character-level detection, and honeypot prototypes.

| File | Reason for Exclusion |
|------|---------------------|
| `ml_pipeline/train_web_attack_v3_rf.py` | Random Forest V3 web attack experiment — overfitting on benign class |
| `ml_pipeline/models/web_attack_rf_model.pkl` | Trained RF model from V3 — high benign precision, poor attack recall |
| `ml_pipeline/models/char_lstm_best.keras` | Character-level LSTM for URL classification — very slow inference, not real-time suitable |
| `ml_pipeline/models/char_tokenizer.pkl` | Tokenizer for the LSTM model |
| `ml_pipeline/preprocessing_old.py` | Legacy preprocessing pipeline — refactored into active `preprocessing.py` |
| `honeypot/app.py` | Early generic honeypot Flask prototype — replaced by per-site `websites/` architecture |
| `honeypot/logger.py` | Logger utility tied only to legacy `honeypot/app.py` — not used in production |
| `V2-SQLI-XSS-NoSQLi/` | Second-generation dataset collection attempt — data quality issues identified, not used for final training |

---

*Report generated for DeceptiCloud — FYP-II.*
