# DECEPTICLOUD — MASTER INDEX

**AI-Driven Cyber Deception Platform**  
**Version**: 2.0  
**Status**: ✅ Operational  
**Last Updated**: April 18, 2026

---

## 📚 DOCUMENTATION GUIDE

### 🚀 Getting Started
Start here if you're new to the system:

1. **[QUICKSTART.md](QUICKSTART.md)** ⭐ START HERE
   - 5-minute setup guide
   - Launch instructions
   - Basic testing
   - Dashboard tour

2. **[README_COMPLETE_SYSTEM.md](README_COMPLETE_SYSTEM.md)**
   - Complete system overview
   - Architecture diagrams
   - Component descriptions
   - Configuration guide

---

### 📋 Planning & Status

3. **[DECEPTICLOUD_BUILD_PLAN.md](DECEPTICLOUD_BUILD_PLAN.md)**
   - System audit results
   - Phase-by-phase plan
   - Implementation strategy
   - Timeline estimates

4. **[BUILD_STATUS.md](BUILD_STATUS.md)**
   - Current progress (53% complete)
   - Completed phases
   - Pending tasks
   - Next steps

5. **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)**
   - What was built
   - Technical details
   - Achievements
   - Lessons learned

---

### 🔧 Configuration & Reference

6. **[SYSTEM_CONFIG.md](SYSTEM_CONFIG.md)**
   - All service ports
   - File paths
   - Credentials
   - API endpoints
   - Database schema
   - ML model specs
   - Configuration parameters

---

### 🛡️ Component-Specific Guides

7. **[wazuh/README.md](wazuh/README.md)**
   - Wazuh installation
   - Custom rules reference
   - Agent deployment
   - Log ingestion
   - Troubleshooting

---

## 🗂️ FILE STRUCTURE

### Core System Files
```
/Ahmed Fype-II/
├── config.py                          # Central configuration
├── launch_decepticloud.py             # Original launcher
├── launch_decepticloud_v2.py          # Enhanced launcher ⭐ USE THIS
│
├── database/                          # Database layer (NEW)
│   ├── __init__.py
│   ├── schema.sql                     # Database schema
│   ├── db_service.py                  # Database service
│   ├── migrate_existing_data.py       # Data migration
│   └── decepticloud.db                # SQLite database
│
├── proxy/                             # Routing proxy
│   ├── routing_proxy.py               # Main proxy
│   ├── db_integration.py              # Database integration (NEW)
│   └── logs/
│       ├── proxy_attacks.jsonl        # Attack log
│       └── llm_stats.json             # LLM statistics
│
├── ml_pipeline/                       # ML detection
│   ├── model_api.py                   # ML API server
│   ├── models/                        # Trained models
│   └── *.py                           # Training scripts
│
├── dashboard/                         # Web dashboard
│   ├── app.py                         # Flask backend
│   ├── templates/                     # HTML templates
│   └── static/                        # CSS/JS
│
├── websites/                          # 14 websites
│   ├── banking/                       # Real banking (3001)
│   ├── ecommerce/                     # Real e-commerce (3002)
│   ├── ... (5 more real sites)
│   ├── banking_honeypot/              # Fake banking (4001)
│   ├── ecommerce_honeypot/            # Fake e-commerce (4002)
│   └── ... (5 more honeypots)
│
├── honeypot/                          # Deception layer
│   ├── blockchain_ledger.py           # Blockchain
│   ├── llm_response_engine.py         # LLM engine
│   ├── gan_data_generator.py          # GAN data
│   └── *.py                           # Other modules
│
├── wazuh/                             # SIEM integration (NEW)
│   ├── install_wazuh.sh               # Installation script
│   ├── deploy_agents.sh               # Agent deployment
│   ├── log_ingestion_service.py       # Log ingestion
│   ├── custom_rules.xml               # Custom rules
│   ├── custom_decoders.xml            # Custom decoders
│   └── README.md                      # Wazuh guide
│
├── attacks/                           # Attack simulation
│   ├── web_attacks.sh                 # Web attacks
│   └── ddos_attack.sh                 # DDoS attack
│
└── logs/                              # System logs
    ├── attack_chain.json              # Blockchain
    ├── canary_triggers.jsonl          # Canary tokens
    └── *.log                          # Various logs
```

---

## 🎯 QUICK REFERENCE

### Launch Commands
```bash
# Start the system
python3 launch_decepticloud_v2.py

# Run attack simulation
bash attacks/web_attacks.sh

# Install Wazuh (optional)
sudo bash wazuh/install_wazuh.sh
```

### Access Points
- **Dashboard**: http://localhost:9000 (admin / DeceptiCloud)
- **ML API**: http://localhost:5000
- **Proxy**: http://localhost:8080
- **Real Sites**: http://localhost:3001-3007
- **Honeypots**: http://localhost:4001-4007

### Key Files
- **Database**: `database/decepticloud.db`
- **Config**: `config.py`
- **Attack Log**: `proxy/logs/proxy_attacks.jsonl`
- **Blockchain**: `logs/attack_chain.json`

---

## 📊 SYSTEM STATUS

### Operational Components ✅
- [x] Database Layer (394 attacks stored)
- [x] ML Detection API (2 models loaded)
- [x] Routing Proxy (routing working)
- [x] Dashboard (all pages working)
- [x] Honeypots (7 running)
- [x] Real Sites (7 running)
- [x] Blockchain Ledger (operational)
- [x] LLM Engine (operational)
- [x] GAN Data (operational)

### Optional Components ⚠️
- [ ] Wazuh Manager (not installed)
- [ ] Wazuh Agents (not deployed)
- [ ] Log Ingestion (not running)

### Pending Enhancements 🔄
- [ ] Attack History Page
- [ ] Attacker Profiles Page
- [ ] Honeypot Management Page
- [ ] Additional ML Models (5 models)
- [ ] Adaptive Learning Engine
- [ ] Enhanced Fingerprinting
- [ ] SSH Honeypot

---

## 🔍 FIND WHAT YOU NEED

### I want to...

**...get started quickly**
→ Read [QUICKSTART.md](QUICKSTART.md)

**...understand the architecture**
→ Read [README_COMPLETE_SYSTEM.md](README_COMPLETE_SYSTEM.md)

**...see what's been built**
→ Read [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

**...check current status**
→ Read [BUILD_STATUS.md](BUILD_STATUS.md)

**...configure the system**
→ Read [SYSTEM_CONFIG.md](SYSTEM_CONFIG.md)

**...install Wazuh**
→ Read [wazuh/README.md](wazuh/README.md)

**...understand the build plan**
→ Read [DECEPTICLOUD_BUILD_PLAN.md](DECEPTICLOUD_BUILD_PLAN.md)

**...troubleshoot issues**
→ Check logs in `logs/` directory
→ Review troubleshooting sections in READMEs

**...run tests**
→ `bash attacks/web_attacks.sh`
→ `bash attacks/ddos_attack.sh`

**...view attack data**
→ Dashboard: http://localhost:9000
→ Database: `python3 -c "from database.db_service import get_db_service; print(get_db_service().get_attack_stats())"`

**...add new features**
→ Review [DECEPTICLOUD_BUILD_PLAN.md](DECEPTICLOUD_BUILD_PLAN.md) Phase 2-9

---

## 📈 PROGRESS TRACKER

| Phase | Status | Progress |
|-------|--------|----------|
| Phase 0: Database | ✅ Complete | 100% |
| Phase 1: Wazuh | ⚠️ Ready | 90% |
| Phase 2: Honeypots | 🔄 Pending | 30% |
| Phase 3: Proxy | 🔄 Pending | 40% |
| Phase 4: ML Pipeline | 🔄 Pending | 50% |
| Phase 5: Adaptive Learning | ⏸️ Not Started | 0% |
| Phase 6: Fingerprinting | 🔄 Pending | 40% |
| Phase 7: Dashboard | 🔄 Pending | 60% |
| Phase 8: Testing | 🔄 Pending | 50% |
| Phase 9: Persistence | 🔄 Pending | 70% |

**Overall**: 53% Complete

---

## 🎓 LEARNING PATH

### For New Users
1. Read QUICKSTART.md
2. Launch the system
3. Run attack simulation
4. Explore dashboard
5. Read README_COMPLETE_SYSTEM.md

### For Developers
1. Read DECEPTICLOUD_BUILD_PLAN.md
2. Review SYSTEM_CONFIG.md
3. Study database schema
4. Review proxy code
5. Read BUILD_STATUS.md for next tasks

### For Security Analysts
1. Read README_COMPLETE_SYSTEM.md
2. Review attack detection methods
3. Explore dashboard pages
4. Study Wazuh integration
5. Review blockchain ledger

---

## 🆘 SUPPORT

### Common Issues

**System won't start**
→ Check logs in `logs/` directory
→ Verify ports are available
→ Kill stuck processes: `pkill -f "python3.*decepticloud"`

**Dashboard not loading**
→ Check if running: `curl http://localhost:9000/api/stats`
→ Clear browser cache
→ Check browser console for errors

**No attacks showing**
→ Check database: `python3 -c "from database.db_service import get_db_service; print(get_db_service().get_attack_stats())"`
→ Check proxy logs: `tail -f proxy/logs/proxy_attacks.jsonl`

**ML API timeout**
→ Increase timeout in proxy code
→ Check ML API: `curl http://localhost:5000/api/health`

### Get Help
1. Check relevant README
2. Review logs
3. Check BUILD_STATUS.md for known issues
4. Review troubleshooting sections

---

## 📝 CHANGELOG

### v2.0 (April 18, 2026)
- ✅ Added centralized database layer
- ✅ Migrated 394 attacks from JSONL
- ✅ Added Wazuh integration (ready to deploy)
- ✅ Created enhanced launch script
- ✅ Added comprehensive documentation
- ✅ Added database integration to proxy
- ✅ Preserved all existing functionality

### v1.0 (Previous)
- ✅ Core deception system
- ✅ ML detection (2 models)
- ✅ 14 websites (7 real + 7 honeypot)
- ✅ Dashboard
- ✅ Blockchain ledger
- ✅ LLM engine
- ✅ GAN data

---

## 🏆 PROJECT INFO

**Name**: DeceptiCloud  
**Type**: Final Year Project (FYP-II)  
**Department**: Computer Science  
**Year**: 2026  
**Status**: ✅ Operational  
**Version**: 2.0  

---

**Last Updated**: April 18, 2026  
**Maintained By**: FYP-II Team  
**License**: Academic Project
