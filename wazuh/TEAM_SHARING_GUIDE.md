# Wazuh Configuration Sharing Guide

## 📦 For Team Members

This directory contains a complete, ready-to-deploy Wazuh SIEM setup for DeceptiCloud.

### 🚀 Quick Setup (5 minutes)

1. **Copy this directory** to your machine
2. **Run installation**:
   ```bash
   cd wazuh
   sudo bash install_docker_and_wazuh.sh
   ```
3. **Access Wazuh Dashboard**: http://localhost:5601
   - Username: `admin`
   - Password: `SecretPassword`

That's it! Everything is pre-configured.

---

## 📁 What's Included

```
wazuh/
├── docker-compose.yml              # Complete stack definition
├── wazuh-config/                   # Pre-configured settings
│   ├── ossec.conf                  # Manager configuration
│   ├── local_rules.xml             # 20+ custom rules
│   └── local_decoder.xml           # Custom decoders
├── install_docker_and_wazuh.sh     # One-command installation
├── manage_wazuh.sh                 # Management commands
├── log_ingestion_service.py        # DeceptiCloud integration
├── DOCKER_DEPLOYMENT_GUIDE.md      # Complete documentation
└── TEAM_SHARING_GUIDE.md           # This file
```

---

## 🎯 What You Get

### Services
- ✅ Wazuh Manager (SIEM core)
- ✅ Wazuh Indexer (log storage)
- ✅ Wazuh Dashboard (web UI)
- ✅ 8 Pre-configured agents

### Features
- ✅ 20+ custom detection rules
- ✅ Automatic attack detection
- ✅ Real-time alerting
- ✅ Log aggregation
- ✅ Compliance monitoring
- ✅ File integrity monitoring

### Integration
- ✅ DeceptiCloud proxy monitoring
- ✅ Honeypot event tracking
- ✅ Attack correlation
- ✅ Database integration

---

## 🔧 Management

### Start/Stop
```bash
./manage_wazuh.sh start    # Start all services
./manage_wazuh.sh stop     # Stop all services
./manage_wazuh.sh restart  # Restart services
```

### Monitor
```bash
./manage_wazuh.sh status   # Check service status
./manage_wazuh.sh logs     # View logs
./manage_wazuh.sh agents   # List agents
```

### Backup/Restore
```bash
./manage_wazuh.sh backup   # Create backup
./manage_wazuh.sh restore backups/wazuh_backup_YYYYMMDD_HHMMSS
```

---

## 🔐 Credentials

**Wazuh API**:
- Username: `wazuh-api`
- Password: `DeceptiCloudWazuh2026`

**Wazuh Dashboard**:
- Username: `admin`
- Password: `SecretPassword`

**Change these in production!**

---

## 📊 Custom Rules

Pre-configured detection for:
- SQL Injection
- XSS
- Path Traversal
- Command Injection
- NoSQL Injection
- Scanner Detection
- Brute Force
- Port Scanning
- DDoS
- Credential Stuffing
- MITM attacks

All rules are in `wazuh-config/local_rules.xml`

---

## 🐛 Troubleshooting

### Installation Issues

**Docker not starting**:
```bash
sudo systemctl start docker
sudo systemctl enable docker
```

**Permission denied**:
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

**Port conflicts**:
```bash
# Check if ports are in use
sudo netstat -tulpn | grep -E '(1514|5601|9200|55000)'
```

### Service Issues

**Services won't start**:
```bash
# Check system requirements
sysctl vm.max_map_count  # Should be >= 262144
sudo sysctl -w vm.max_map_count=262144

# Check disk space
df -h
```

**Agents not connecting**:
```bash
# Check manager status
docker exec wazuh-manager /var/ossec/bin/wazuh-control status

# Restart agent
docker-compose restart wazuh-agent-proxy
```

---

## 📚 Documentation

- **Complete Guide**: `DOCKER_DEPLOYMENT_GUIDE.md`
- **Wazuh Docs**: https://documentation.wazuh.com/
- **Docker Docs**: https://docs.docker.com/

---

## 🤝 Sharing with Others

### Method 1: Direct Copy
```bash
# Zip the directory
tar -czf wazuh-config.tar.gz wazuh/

# Share the archive
# Recipients extract and run install script
```

### Method 2: Git Repository
```bash
# Add to git
git add wazuh/
git commit -m "Add Wazuh configuration"
git push

# Team members clone and run
git clone <repo>
cd wazuh
sudo bash install_docker_and_wazuh.sh
```

### Method 3: Docker Registry (Advanced)
```bash
# Save images
docker save wazuh/wazuh-manager:4.7.0 | gzip > wazuh-manager.tar.gz

# Load on another machine
docker load < wazuh-manager.tar.gz
```

---

## ✅ Verification Checklist

After installation, verify:

- [ ] Docker is running: `docker ps`
- [ ] All services are up: `./manage_wazuh.sh status`
- [ ] Dashboard accessible: http://localhost:5601
- [ ] API accessible: `curl http://localhost:55000`
- [ ] Agents connected: `./manage_wazuh.sh agents`
- [ ] Logs flowing: `./manage_wazuh.sh logs`

---

## 🎓 Learning Resources

### Wazuh Basics
1. Access dashboard: http://localhost:5601
2. Navigate to "Security Events"
3. Review detected attacks
4. Check agent status
5. Explore compliance reports

### Custom Rules
1. Edit `wazuh-config/local_rules.xml`
2. Add your rule
3. Restart manager: `docker-compose restart wazuh-manager`
4. Test: `docker exec wazuh-manager /var/ossec/bin/wazuh-logtest`

### Integration
1. Start log ingestion: `python3 log_ingestion_service.py`
2. Check DeceptiCloud dashboard
3. Verify Wazuh alerts appear
4. Review correlation

---

## 💡 Tips

1. **Resource Usage**: Monitor with `docker stats`
2. **Log Rotation**: Configured automatically
3. **Backups**: Run weekly backups
4. **Updates**: Pull latest images monthly
5. **Security**: Change default passwords
6. **Performance**: Adjust memory in docker-compose.yml
7. **Customization**: Add rules in local_rules.xml
8. **Monitoring**: Check dashboard daily

---

## 🆘 Getting Help

### Check Logs
```bash
# All services
docker-compose logs

# Specific service
docker logs wazuh-manager
docker logs wazuh-agent-proxy
```

### Common Issues

**High CPU usage**:
- Reduce indexer memory in docker-compose.yml
- Disable unnecessary features in ossec.conf

**Disk space full**:
- Clean old logs: `docker system prune`
- Adjust retention in ossec.conf

**Agents disconnected**:
- Check network: `docker network inspect wazuh_decepticloud-network`
- Restart agents: `docker-compose restart`

---

## 🎉 Success!

You now have a production-ready Wazuh SIEM integrated with DeceptiCloud!

**What's Next**:
1. Explore the dashboard
2. Review detected attacks
3. Customize rules for your needs
4. Set up email alerts
5. Configure compliance monitoring

**Questions?** Check `DOCKER_DEPLOYMENT_GUIDE.md` for detailed documentation.

---

**Version**: 1.0  
**Maintained By**: DeceptiCloud Team  
**Last Updated**: April 18, 2026
