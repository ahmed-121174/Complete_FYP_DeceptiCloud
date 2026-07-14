#!/usr/bin/env python3
"""
DeceptiCloud - Wazuh Log Ingestion Service
Polls Wazuh API for alerts and ingests them into the database
"""

import requests
import json
import time
import sys
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import base64

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_service import get_db_service
from config import DASHBOARD_PORT

# Wazuh API Configuration
WAZUH_API_HOST = 'localhost'
WAZUH_API_PORT = 55000
WAZUH_API_USER = 'wazuh-wui'
WAZUH_API_PASSWORD = 'MyS3cr37P450r.*-'
WAZUH_API_URL = f'https://{WAZUH_API_HOST}:{WAZUH_API_PORT}'

# Polling configuration
POLL_INTERVAL = 5  # seconds
ALERT_BATCH_SIZE = 100

# WebSocket for real-time dashboard updates (optional)
WEBSOCKET_ENABLED = False


class WazuhAPIClient:
    """Client for Wazuh API"""
    
    def __init__(self, host: str, port: int, user: str, password: str):
        self.base_url = f'https://{host}:{port}'
        self.user = user
        self.password = password
        self.token = None
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification for local setup
        
        # Suppress SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def authenticate(self) -> bool:
        """Authenticate with Wazuh API and get JWT token"""
        try:
            auth_str = f'{self.user}:{self.password}'
            auth_bytes = auth_str.encode('utf-8')
            auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
            
            headers = {
                'Authorization': f'Basic {auth_b64}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.get(
                f'{self.base_url}/security/user/authenticate',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('data', {}).get('token')
                return True
            else:
                print(f"Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"Authentication error: {e}")
            return False
    
    def get_alerts(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get recent alerts from Wazuh"""
        if not self.token:
            if not self.authenticate():
                return []
        
        try:
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            
            params = {
                'limit': limit,
                'offset': offset,
                'sort': '-timestamp'
            }
            
            response = self.session.get(
                f'{self.base_url}/alerts',
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', {}).get('affected_items', [])
            elif response.status_code == 401:
                # Token expired, re-authenticate
                if self.authenticate():
                    return self.get_alerts(limit, offset)
            
            return []
        except Exception as e:
            print(f"Error fetching alerts: {e}")
            return []
    
    def get_agents(self) -> List[Dict]:
        """Get list of connected agents"""
        if not self.token:
            if not self.authenticate():
                return []
        
        try:
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.get(
                f'{self.base_url}/agents',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', {}).get('affected_items', [])
            
            return []
        except Exception as e:
            print(f"Error fetching agents: {e}")
            return []


class LogIngestionService:
    """Service that polls Wazuh and ingests alerts into database"""
    
    def __init__(self):
        self.db = get_db_service()
        self.wazuh_client = None
        self.running = False
        self.last_alert_id = None
        self.stats = {
            'total_alerts': 0,
            'alerts_ingested': 0,
            'errors': 0,
            'last_poll': None
        }
    
    def connect_wazuh(self) -> bool:
        """Connect to Wazuh API"""
        try:
            self.wazuh_client = WazuhAPIClient(
                WAZUH_API_HOST,
                WAZUH_API_PORT,
                WAZUH_API_USER,
                WAZUH_API_PASSWORD
            )
            
            if self.wazuh_client.authenticate():
                print(f"✓ Connected to Wazuh API at {WAZUH_API_URL}")
                return True
            else:
                print(f"✗ Failed to authenticate with Wazuh API")
                return False
        except Exception as e:
            print(f"✗ Error connecting to Wazuh: {e}")
            return False
    
    def process_alert(self, alert: Dict):
        """Process a single Wazuh alert and store in database"""
        try:
            # Extract alert data
            timestamp = alert.get('timestamp', datetime.now().isoformat())
            agent_id = alert.get('agent', {}).get('id')
            agent_name = alert.get('agent', {}).get('name')
            rule = alert.get('rule', {})
            rule_id = rule.get('id')
            rule_level = rule.get('level', 0)
            rule_description = rule.get('description', '')
            
            # Extract IP if available
            ip = None
            if 'data' in alert:
                data = alert.get('data', {})
                ip = data.get('srcip') or data.get('src_ip') or data.get('ip')
            
            # Store in wazuh_alerts table
            with self.db.get_connection() as conn:
                conn.execute("""
                    INSERT INTO wazuh_alerts (
                        timestamp, agent_id, agent_name, rule_id, rule_level,
                        rule_description, alert_json, ip, processed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp,
                    agent_id,
                    agent_name,
                    rule_id,
                    rule_level,
                    rule_description,
                    json.dumps(alert),
                    ip,
                    False
                ))
                conn.commit()
            
            # Create system event
            severity = 'low'
            if rule_level >= 12:
                severity = 'critical'
            elif rule_level >= 10:
                severity = 'high'
            elif rule_level >= 7:
                severity = 'medium'
            
            event_data = {
                'timestamp': timestamp,
                'event_type': 'wazuh',
                'severity': severity,
                'source': f'wazuh-agent-{agent_name or agent_id}',
                'message': rule_description,
                'details': {
                    'rule_id': rule_id,
                    'rule_level': rule_level,
                    'agent': agent_name or agent_id
                },
                'ip': ip
            }
            self.db.insert_event(event_data)
            
            self.stats['alerts_ingested'] += 1
            
        except Exception as e:
            print(f"Error processing alert: {e}")
            self.stats['errors'] += 1
    
    def poll_alerts(self):
        """Poll Wazuh for new alerts"""
        if not self.wazuh_client:
            return
        
        try:
            alerts = self.wazuh_client.get_alerts(limit=ALERT_BATCH_SIZE)
            self.stats['total_alerts'] += len(alerts)
            self.stats['last_poll'] = datetime.now().isoformat()
            
            for alert in alerts:
                self.process_alert(alert)
            
            if alerts:
                print(f"Processed {len(alerts)} alerts (Total: {self.stats['alerts_ingested']})")
        
        except Exception as e:
            print(f"Error polling alerts: {e}")
            self.stats['errors'] += 1
    
    def run(self):
        """Main service loop"""
        print("=" * 60)
        print("DeceptiCloud - Wazuh Log Ingestion Service")
        print("=" * 60)
        
        # Try to connect to Wazuh
        if not self.connect_wazuh():
            print("\n⚠ Wazuh not available - running in standalone mode")
            print("  Install Wazuh using: sudo bash wazuh/install_wazuh.sh")
            print("  Service will continue checking for Wazuh availability...")
        
        self.running = True
        retry_count = 0
        
        print(f"\nPolling interval: {POLL_INTERVAL}s")
        print("Press Ctrl+C to stop\n")
        
        while self.running:
            try:
                if self.wazuh_client:
                    self.poll_alerts()
                    retry_count = 0
                else:
                    # Try to reconnect every 30 seconds
                    if retry_count % 6 == 0:
                        print("Attempting to connect to Wazuh...")
                        self.connect_wazuh()
                    retry_count += 1
                
                time.sleep(POLL_INTERVAL)
            
            except KeyboardInterrupt:
                print("\n\nShutting down...")
                self.running = False
                break
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(POLL_INTERVAL)
        
        print("\n" + "=" * 60)
        print("Service Statistics:")
        print(f"  Total alerts received: {self.stats['total_alerts']}")
        print(f"  Alerts ingested: {self.stats['alerts_ingested']}")
        print(f"  Errors: {self.stats['errors']}")
        print("=" * 60)


def main():
    service = LogIngestionService()
    service.run()


if __name__ == '__main__':
    main()
