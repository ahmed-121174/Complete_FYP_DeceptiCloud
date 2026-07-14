# DeceptiCloud - Quick Start Guide (Post-Fix)

## ✓ System is Now Fixed and Running!

All issues have been resolved. The system now works correctly regardless of which drive you're on.

## Current Status

```
✓ Wazuh Manager:    Running (172.25.0.3)
✓ Wazuh Indexer:    Running (port 9200)
✓ Wazuh Dashboard:  Running (port 5601)
✓ 23 Agent Containers: Running
✓ ML API:           Running (port 5000)
✓ Dashboard:        Running (port 8080)
✓ Routing Proxy:    Running (port 9000)
✓ Adaptive Engine:  Running
✓ Log Ingestion:    Running
```

## Quick Commands

### Start Everything
```bash
./start_stop/decepticloud_control.sh start
```

### Stop Everything
```bash
./start_stop/decepticloud_control.sh stop
```

### Check Status
```bash
./start_stop/decepticloud_control.sh status
```

### Restart
```bash
./start_stop/decepticloud_control.sh restart
```

## Access URLs

| Service | URL | Notes |
|---------|-----|-------|
| Wazuh Dashboard | http://localhost:5601 | Security monitoring |
| DeceptiCloud Dashboard | http://localhost:8080 | Main control panel |
| ML API | http://localhost:5000 | Machine learning service |
| Routing Proxy | http://localhost:9000 | Traffic routing |

## What Was Fixed

1. **Hardcoded paths** → Now auto-detects location
2. **Wrong docker-compose file** → Using working version
3. **Old containers** → Recreated with correct paths
4. **Docker Compose v2** → Now using native command

## For Jury Presentation

Everything is ready! You can now:

1. **Start the system** (if not already running):
   ```bash
   ./start_stop/decepticloud_control.sh start
   ```

2. **Run demonstrations**:
   ```bash
   # Web attacks
   ./.JURY_PRESENTATION/2_WEB_ATTACKS.sh
   
   # DDoS attacks
   ./.JURY_PRESENTATION/3_DDOS_ATTACK.sh
   ```

3. **Show dashboards**:
   - Open http://localhost:8080 for DeceptiCloud
   - Open http://localhost:5601 for Wazuh

## Troubleshooting

### Dashboard not loading?
Wait 1-2 minutes after startup for all services to initialize.

### Check logs:
```bash
tail -f logs/launch_v2.log
```

### View Docker logs:
```bash
docker logs wazuh-manager
docker logs wazuh-dashboard
```

### Complete reset:
```bash
./start_stop/decepticloud_control.sh stop
docker rm -f $(docker ps -aq | grep -E "wazuh|dc-agent")
./start_stop/decepticloud_control.sh start
```

## System Will Now Survive

✓ Laptop restarts
✓ Drive changes
✓ Path changes
✓ System updates

No more manual path fixes needed!

## Files to Reference

- `SYSTEM_STARTUP_FIXED.md` - Detailed fix documentation
- `STARTUP_FIX_APPLIED.md` - Technical details of changes
- `start_stop/decepticloud_control.sh` - Main control script

---

**Status**: System operational and ready for demonstration! 🚀
