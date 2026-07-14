# DeceptiCloud - Wazuh Integration

## Overview

Wazuh provides centralized log collection, analysis, and alerting for the DeceptiCloud system. It acts as a SIEM (Security Information and Event Management) layer that aggregates logs from all 14 nodes (7 real sites + 7 honeypots).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Wazuh Manager                           │
│                   (Port 1514, 55000)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Log Analysis │  │ Rule Engine  │  │  Wazuh API   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   ┌────▼────┐         ┌────▼────┐        ┌────▼────┐
   │ Agent 1 │         │ Agent 2 │  ...   │ Agent 14│
   │Honeypot │         │  Real   │        │  Real   │
   │ Banking │         │ Banking │        │  Admin  │
   └─────────┘         └─────────┘        └─────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                ┌───────────▼───────────┐
                │ Log Ingestion Service │
                │   (Python Service)    │
                └───────────┬───────────┘
                            │
                    ┌───────▼────────┐
                    │   PostgreSQL   │
                    │    Database    │
                    └────────────────┘
```

## Installation

### Step 1: Install Wazuh Manager

```bash
sudo bash wazuh/install_wazuh.sh
```

This will:
- Install Wazuh Manager 4.x
- Install Wazuh API
- Start all services
- Configure ports (1514 for agents, 55000 for API)

### Step 2: Configure Custom Rules

```bash
sudo cp wazuh/custom_rules.xml /var/ossec/etc/rules/local_rules.xml
sudo cp wazuh/custom_decoders.xml /var/ossec/etc/decoders/local_decoder.xml
sudo systemctl restart wazuh-manager
```

### Step 3: Deploy Agents

```bash
sudo bash wazuh/deploy_agents.sh
```

This registers 14 agents:
- 7 honeypot agents (honeypot-banking-01, etc.)
- 7 real site agents (real-banking-01, etc.)

### Step 4: Start Log Ingestion Service

```bash
python3 wazuh/log_ingestion_service.py
```

This service:
- Polls Wazuh API every 5 seconds
- Ingests alerts into the database
- Creates system events for high-severity alerts
- Runs continuously in the background

## Custom Rules

The following custom rules are included:

| Rule ID | Level | Description |
|---------|-------|-------------|
| 100001 | 10 | SQL Injection attempt |
| 100002 | 12 | High confidence SQL Injection |
| 100010 | 10 | XSS attempt |
| 100011 | 12 | High confidence XSS |
| 100020 | 10 | Path Traversal attempt |
| 100030 | 12 | Command Injection attempt |
| 100040 | 10 | NoSQL Injection attempt |
| 100050 | 8 | Security scanner detected |
| 100060 | 8 | Multiple failed logins |
| 100061 | 10 | Brute force attack (5+ in 60s) |
| 100070 | 8 | Port scan (10+ in 10s) |
| 100080 | 10 | Possible DDoS (100+ in 10s) |
| 100081 | 12 | DDoS confirmed (500+ in 60s) |
| 100090 | 8 | Honeypot access |
| 100100 | 10 | Credential stuffing (20+ in 60s) |
| 100110 | 12 | MITM indicator |
| 100120 | 6 | Suspicious User-Agent |

## Alert Levels

- **1-5**: Informational
- **6-8**: Low severity (monitoring, reconnaissance)
- **9-11**: Medium severity (attack attempts)
- **12-15**: High/Critical severity (confirmed attacks)

## Configuration

### Wazuh API Credentials

Default credentials (change after installation):
- Username: `wazuh`
- Password: `wazuh`

Update in `wazuh/log_ingestion_service.py`:
```python
WAZUH_API_USER = 'your_username'
WAZUH_API_PASSWORD = 'your_password'
```

### Polling Interval

Adjust in `wazuh/log_ingestion_service.py`:
```python
POLL_INTERVAL = 5  # seconds
```

## Verification

### Check Wazuh Manager Status
```bash
sudo systemctl status wazuh-manager
```

### Check Wazuh API Status
```bash
sudo systemctl status wazuh-api
```

### List Registered Agents
```bash
sudo /var/ossec/bin/agent_control -l
```

### View Recent Alerts
```bash
sudo tail -f /var/ossec/logs/alerts/alerts.log
```

### Test API Connection
```bash
curl -k -u wazuh:wazuh https://localhost:55000/security/user/authenticate
```

## Integration with DeceptiCloud

### Proxy Integration

The routing proxy can be configured to send logs to Wazuh agents:

```python
# In proxy/routing_proxy.py
import syslog

def log_to_wazuh(attack_data):
    syslog.syslog(syslog.LOG_WARNING, 
        f"decepticloud-proxy: {attack_data['ip']} - {attack_data['attack_type']} - {attack_data['confidence']} - {attack_data['url']}")
```

### Dashboard Integration

The dashboard reads Wazuh alerts from the database:

```python
# Query recent Wazuh alerts
alerts = db.execute_query("""
    SELECT * FROM wazuh_alerts 
    WHERE rule_level >= 10 
    ORDER BY timestamp DESC 
    LIMIT 50
""")
```

## Troubleshooting

### Wazuh Manager won't start
```bash
sudo /var/ossec/bin/wazuh-control start
sudo tail -f /var/ossec/logs/ossec.log
```

### Agents not connecting
```bash
# Check firewall
sudo ufw allow 1514/tcp
sudo ufw allow 55000/tcp

# Check agent status
sudo /var/ossec/bin/agent_control -l
```

### API authentication fails
```bash
# Reset API credentials
sudo /var/ossec/bin/wazuh-api-user -u wazuh -p newpassword
```

### No alerts appearing
```bash
# Check rule syntax
sudo /var/ossec/bin/wazuh-logtest

# Restart manager
sudo systemctl restart wazuh-manager
```

## Production Deployment

For production:

1. **Separate Wazuh Manager**: Deploy on dedicated server
2. **Install agents on actual nodes**: Each honeypot/real site gets its own agent
3. **Configure TLS**: Enable TLS for agent-manager communication
4. **Set up Elasticsearch**: For advanced analytics and visualization
5. **Configure email alerts**: For high-severity events
6. **Implement log rotation**: Prevent disk space issues
7. **Regular backups**: Backup Wazuh configuration and rules

## Resources

- [Wazuh Documentation](https://documentation.wazuh.com/)
- [Wazuh API Reference](https://documentation.wazuh.com/current/user-manual/api/reference.html)
- [Custom Rules Guide](https://documentation.wazuh.com/current/user-manual/ruleset/custom.html)
