# 🛡️ DeceptiCloud — AI-Powered Cyber Deception & Intrusion Detection System

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/TensorFlow-2.x-orange?logo=tensorflow&logoColor=white" />
  <img src="https://img.shields.io/badge/Wazuh-SIEM-red?logo=wazuh&logoColor=white" />
  <img src="https://img.shields.io/badge/License-Academic-green" />
  <img src="https://img.shields.io/badge/Status-Complete-brightgreen" />
</p>

---

## 📄 FYP Report

> **Click below to read the full Final Year Project report:**

### 👉 [FYP-Report_DeceptiCloud_Final.pdf](./FYP-Report_DeceptiCloud_Final.pdf)

---

## 📌 Project Overview

**DeceptiCloud** is an AI-powered cybersecurity system that combines:
- 🍯 **Honeypot deception technology** — lures and traps attackers
- 🤖 **Machine Learning detection** — real-time DDoS, web attack & intrusion classification
- 🔍 **Wazuh SIEM integration** — centralized log monitoring and alerting
- 📊 **Live dashboard** — real-time threat visualization

---

## 🧠 Key Features

| Feature | Description |
|---|---|
| **DDoS Detection** | ML model trained on 10+ DDoS attack types (DrDoS, UDP, SNMP, DNS...) |
| **Web Attack Detection** | XSS, SQLi, NoSQLi, Brute Force detection via ensemble models |
| **Honeypot Websites** | 7 fake websites (banking, healthcare, e-commerce, etc.) to trap attackers |
| **Adaptive Engine** | Dynamically adjusts honeypot responses based on attack patterns |
| **Wazuh Integration** | Real-time SIEM alerts with custom decoders and rules |
| **Proxy Routing** | Smart proxy routes real vs malicious traffic to real vs honeypot sites |

---

## 🗂️ Project Structure

```
DeceptiCloud/
├── ml_pipeline/          # ML models, training scripts, preprocessing
│   ├── models/           # Trained .pkl, .keras, .json model files
│   └── training/         # Individual attack-type training scripts
├── proxy/                # Routing proxy (real ↔ honeypot traffic)
├── websites/             # 7 honeypot + real website pairs
├── wazuh/                # SIEM config, custom rules, decoders
├── scripts/              # Utility and automation scripts
├── tests/                # Unit, integration & system tests
├── logs/                 # System logs
└── Datasets/             # ⚠️ Excluded (too large — see below)
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.11
- Docker (for Wazuh)
- Linux (Ubuntu recommended)

### Install dependencies
```bash
pip install -r requirements.txt
```

### Start DeceptiCloud
```bash
bash start_decepticloud.sh
```

### Start with Wazuh SIEM
```bash
bash start_decepti_wazuh.sh
```

---

## 📦 Full Project ZIP (with venv)

The complete project archive (including Python virtual environment) is available as split parts due to GitHub's 2 GB file limit:

| File | Size |
|------|------|
| `Ahmed Fype-II.zip.partaa` | ~1.4 GB |
| `Ahmed Fype-II.zip.partab` | ~1.4 GB |

**To restore:**
```bash
cat Ahmed\ Fype-II.zip.parta* > Ahmed\ Fype-II.zip
unzip Ahmed\ Fype-II.zip
```

> See [README_FULL_ZIP.md](./README_FULL_ZIP.md) for detailed instructions.

---

## 📊 Datasets

Datasets are **not included** in this repo due to GitHub's 2 GB per-file limit. The datasets used are:

| Dataset | Source |
|---|---|
| CIC-DDoS2019 | [UNB CIC](https://www.unb.ca/cic/datasets/ddos-2019.html) |
| CSIC-2010 (Web Attacks) | [CSIC](http://www.isi.csic.es/dataset/) |
| Custom XSS / SQLi datasets | Curated & labeled manually |

---

## 👨‍💻 Authors

**Ahmed** — Final Year Project, Semester VIII

---

## 📜 License

This project is submitted as an academic Final Year Project. All rights reserved.
