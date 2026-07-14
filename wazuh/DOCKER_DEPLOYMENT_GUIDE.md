# Wazuh Docker Deployment Guide for DeceptiCloud

## 📋 Overview

This guide covers the complete Docker-based Wazuh deployment for DeceptiCloud, including:
- Wazuh Manager (SIEM core)
- Wazuh Indexer (OpenSearch for log storage)
- Wazuh Dashboard (Web UI)
- 8 Wazuh Agents (1 proxy + 7 honeypots)

## 🚀 Quick Start

### Step 1: Install Docker and Wazuh
```bash
cd wazuh
sudo bash install_docker_and_wazuh.sh
```

This script will:
1. Install Docker and Docker Compose
2. Configure system for Wazuh (vm.max_map_count, swap)
3. Start Wazuh stack with all agents
4. Display access information

**Installation Time**: 5-10 minutes

### Step 2: Verify Installation
```bash
# Check service status
./manage_wazuh.sh status

# View logs
./manage_wazuh.sh logs

# List agents
./manage_wazuh.sh agents
```

### Step 3: Access Wazuh Dashboard
```
URL: http://localhost:5601
Username: admin
Password: SecretPassword
```

### Step 4: Start Log Ingestion
```bash
cd ..
python3 wazuh/log_ingestion_service.py &
```

---

## 📦 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network                           │
│                  (172.25.0.0/16)                           │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Wazuh      │  │   Wazuh      │  │   Wazuh      │    │
│  │   Manager    │  │   Indexer    │  │  Dashboard   │    │
│  │  :55000      │  │   :9200      │  │   :5601      │    │
│  │  :1514       │  │              │  │              │    │
│  └──────┬───────┘  └──────────────┘  └──────────────┘    │
│         │                                                  │
│         ├──────────────┬──────────────┬──────────────┐   │
│         │              │              │              │   │
│  ┌──────▼───┐   ┌──────▼───┐   ┌──────▼───┐   ┌──────▼───┐
│  │ Agent    │   │ Agent    │   │ Agent    │   │ Agent    │
│  │ Proxy    │   │ Banking  │   │ Ecommerce│   │ ...      │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Configuration

### Docker Compose Services

| Service | Port | Purpose |
|---------|------|---------|
| wazuh-manager | 1514, 1515, 55000 | SIEM core, agent communication, API |
| wazuh-indexer | 9200 | Log storage (OpenSearch) |
| wazuh-dashboard | 5601 | Web interface |
| wazuh-agent-proxy | - | Monitors DeceptiCloud proxy |
| wazuh-agent-*-honeypot | - | Monitors honeypots (7 agents) |

### Volume Mounts

**Wazuh Manager**:
- `wazuh-manager-data`: `/var/ossec/data` (persistent data)
- `wazuh-manager-logs`: `/var/ossec/logs` (logs)
- `wazuh-manager-etc`: `/var/ossec/etc` (configuration)
- `./wazuh-config/ossec.conf`: `/var/ossec/etc/ossec.conf` (main config)
- `./wazuh-config/local_rules.xml`: Custom rules
- `./wazuh-config/local_decoder.xml`: Custom decoders

**Wazuh Agents**:
- `../proxy/logs`: Proxy attack logs
- `../logs`: System logs

### Environment Variables

**Wazuh Manager**:
```yaml
INDEXER_URL: https://wazuh-indexer:9200
API_USERNAME: wazuh-api
API_PASSWORD: DeceptiCloudWazuh2026
```

**Wazuh Agents**:
```yaml
WAZUH_MANAGER: wazuh-manager
WAZUH_AGENT_NAME: <agent-name>
WAZUH_AGENT_GROUP: honeypots|decepticloud
```

---

## 🛠️ Management Commands

### Using manage_wazuh.sh

```bash
# Start Wazuh stack
./manage_wazuh.sh start

# Stop Wazuh stack
./manage_wazuh.sh stop

# Restart services
./manage_wazuh.sh restart

# Check status
./manage_wazuh.sh status

# View logs (follow mode)
./manage_wazuh.sh logs -f

# List connected agents
./manage_wazuh.sh agents

# Backup configuration
./manage_wazuh.sh backup

# Restore from backup
./manage_wazuh.sh restore backups/wazuh_backup_20260418_120000
```

### Direct Docker Commands

```bash
# View all containers
docker-compose ps

# View logs for specific service
docker-compose logs wazuh-manager
docker-compose logs wazuh-agent-proxy

# Execute command in manager
docker exec -it wazuh-manager /bin/bash

# Restart specific service
docker-compose restart wazuh-manager

# View resource usage
docker stats
```

---

## 📊 Custom Rules & Decoders

### Custom Rules (local_rules.xml)

DeceptiCloud includes 20+ custom rules:

| Rule ID | Level | Description |
|---------|-------|-------------|
| 100001-100002 | 10-12 | SQL Injection |
| 100010-100011 | 10-12 | XSS |
| 100020 | 10 | Path Traversal |
| 100030 | 12 | Command Injection |
| 100040 | 10 | NoSQL Injection |
| 100050-100051 | 8-10 | Scanner Detection |
| 100060-100061 | 8-10 | Brute Force |
| 100070 | 8 | Port Scan |
| 100080-100081 | 10-12 | DDoS |
| 100090 | 8 | Honeypot Access |
| 100100 | 10 | Credential Stuffing |
| 100110 | 12 | MITM |
| 100120 | 6 | Suspicious User-Agent |

### Custom Decoders (local_decoder.xml)

- `decepticloud-proxy`: Proxy log decoder
- `decepticloud-honeypot`: Honeypot event decoder
- `web-attack-*`: Web attack pattern decoders
- `scanner-useragent-tools`: Scanner tool detection

---

## 🔍 Monitoring & Alerts

### Wazuh Dashboard

Access at `http://localhost:5601`

**Key Sections**:
1. **Security Events**: Real-time attack detection
2. **Agents**: Agent status and health
3. **Integrity Monitoring**: File changes
4. **Vulnerability Detection**: System vulnerabilities
5. **Compliance**: PCI DSS, GDPR, HIPAA

### Alert Levels

- **1-5**: Informational
- **6-8**: Low severity (monitoring, recon)
- **9-11**: Medium severity (attack attempts)
- **12-15**: High/Critical (confirmed attacks)

### Active Response

Wazuh can automatically respond to attacks:

**Configured Responses**:
- **firewall-drop**: Block IP for 10 minutes (rules 100002, 100011, 100030, 100081)
- **host-deny**: Block IP for 1 hour (rules 100061, 100100)

---

## 🔐 Security

### Credentials

**Wazuh API**:
- Username: `wazuh-api`
- Password: `DeceptiCloudWazuh2026`

**Wazuh Dashboard**:
- Username: `admin`
- Password: `SecretPassword`

**⚠️ Change these in production!**

### Changing Credentials

**API Password**:
```bash
docker exec -it wazuh-manager /var/ossec/bin/wazuh-api-user -u wazuh-api -p NewPassword
```

**Dashboard Password**:
```bash
docker exec -it wazuh-dashboard /usr/share/wazuh-dashboard/bin/wazuh-dashboard-users useradd admin -p NewPassword
```

### Network Security

- All services run in isolated Docker network (172.25.0.0/16)
- Only necessary ports exposed to host
- Agents communicate securely with manager

---

## 📈 Performance Tuning

### Resource Allocation

**Minimum Requirements**:
- CPU: 4 cores
- RAM: 8 GB
- Disk: 50 GB

**Recommended**:
- CPU: 8 cores
- RAM: 16 GB
- Disk: 100 GB

### Optimization

**Increase Indexer Memory**:
Edit `docker-compose.yml`:
```yaml
environment:
  - "OPENSEARCH_JAVA_OPTS=-Xms1g -Xmx1g"  # Change to -Xms2g -Xmx2g
```

**Adjust Log Retention**:
Edit `wazuh-config/ossec.conf`:
```xml
<global>
  <logall>no</logall>  <!-- Disable if disk space is limited -->
</global>
```

---

## 🐛 Troubleshooting

### Services Won't Start

**Check Docker**:
```bash
sudo systemctl status docker
sudo systemctl start docker
```

**Check vm.max_map_count**:
```bash
sysctl vm.max_map_count
# Should be 262144 or higher
sudo sysctl -w vm.max_map_count=262144
```

**Check disk space**:
```bash
df -h
```

### Agents Not Connecting

**Check manager status**:
```bash
docker exec wazuh-manager /var/ossec/bin/wazuh-control status
```

**Check agent logs**:
```bash
docker logs wazuh-agent-proxy
```

**Restart agent**:
```bash
docker-compose restart wazuh-agent-proxy
```

### Dashboard Not Accessible

**Check service status**:
```bash
docker-compose ps wazuh-dashboard
```

**Check logs**:
```bash
docker-compose logs wazuh-dashboard
```

**Restart dashboard**:
```bash
docker-compose restart wazuh-dashboard
```

### High Resource Usage

**Check resource usage**:
```bash
docker stats
```

**Reduce indexer memory**:
Edit `docker-compose.yml` and reduce `OPENSEARCH_JAVA_OPTS`

**Disable unnecessary features**:
Edit `wazuh-config/ossec.conf`:
```xml
<rootcheck>
  <disabled>yes</disabled>
</rootcheck>
```

---

## 💾 Backup & Restore

### Backup

```bash
# Create backup
./manage_wazuh.sh backup

# Backup location
ls -lh backups/
```

**Backup includes**:
- Configuration files
- Custom rules and decoders
- Manager data
- Docker volumes

### Restore

```bash
# List backups
ls -lh backups/

# Restore from backup
./manage_wazuh.sh restore backups/wazuh_backup_20260418_120000
```

### Manual Backup

```bash
# Backup volumes
docker run --rm \
  -v wazuh_wazuh-manager-data:/data \
  -v $(pwd)/backup:/backup \
  alpine tar czf /backup/manager-data.tar.gz -C /data .

# Backup configuration
cp -r wazuh-config backup/
```

---

## 🔄 Updates

### Update Wazuh

```bash
# Stop services
./manage_wazuh.sh stop

# Pull latest images
docker-compose pull

# Start services
./manage_wazuh.sh start
```

### Update Configuration

```bash
# Edit configuration
nano wazuh-config/ossec.conf
nano wazuh-config/local_rules.xml

# Restart manager
docker-compose restart wazuh-manager
```

---

## 📚 Integration with DeceptiCloud

### Log Ingestion Service

The log ingestion service connects Wazuh to DeceptiCloud database:

```bash
# Start service
python3 wazuh/log_ingestion_service.py &

# Check status
ps aux | grep log_ingestion
```

**What it does**:
1. Polls Wazuh API every 5 seconds
2. Retrieves new alerts
3. Stores in DeceptiCloud database
4. Creates system events for high-severity alerts

### Dashboard Integration

DeceptiCloud dashboard shows Wazuh data:
- Wazuh alerts in event feed
- Agent status in infrastructure health
- Alert statistics in overview

---

## 🎓 Best Practices

1. **Regular Backups**: Backup configuration weekly
2. **Monitor Resources**: Check `docker stats` regularly
3. **Review Alerts**: Check Wazuh dashboard daily
4. **Update Rules**: Add custom rules as needed
5. **Rotate Logs**: Configure log rotation
6. **Secure Credentials**: Change default passwords
7. **Network Isolation**: Keep Wazuh in isolated network
8. **Documentation**: Document custom rules and changes

---

## 📞 Support

### Logs Location

- **Manager logs**: `docker logs wazuh-manager`
- **Agent logs**: `docker logs wazuh-agent-<name>`
- **Dashboard logs**: `docker logs wazuh-dashboard`
- **Indexer logs**: `docker logs wazuh-indexer`

### Useful Commands

```bash
# Check all logs
docker-compose logs

# Follow specific service
docker-compose logs -f wazuh-manager

# Execute command in manager
docker exec -it wazuh-manager /bin/bash

# Check agent status
docker exec wazuh-manager /var/ossec/bin/agent_control -l

# Test rules
docker exec wazuh-manager /var/ossec/bin/wazuh-logtest
```

---

## 🎉 Conclusion

You now have a fully containerized Wazuh deployment integrated with DeceptiCloud!

**Next Steps**:
1. Access Wazuh Dashboard
2. Review agent status
3. Start log ingestion service
4. Monitor alerts
5. Customize rules as needed

**For sharing with team members**:
- Share the entire `wazuh/` directory
- They can run `sudo bash install_docker_and_wazuh.sh`
- All configurations are preserved in `wazuh-config/`
- Backups can be shared via `backups/` directory

---

**Version**: 1.0  
**Last Updated**: April 18, 2026  
**Status**: Production Ready
