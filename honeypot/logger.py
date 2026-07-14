import json
import logging
from pathlib import Path
from datetime import datetime
import hashlib
import sys

# Add project root to sys.path for database access
_project_root = str(Path(__file__).parent.parent.resolve())
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Debug path
with open('logs/path_debug.log', 'a') as f:
    f.write(f"[{datetime.now()}] __file__: {__file__}\n")
    f.write(f"[{datetime.now()}] parent: {Path(__file__).parent}\n")
    f.write(f"[{datetime.now()}] project_root: {_project_root}\n")
    f.write(f"[{datetime.now()}] sys.path[0]: {sys.path[0]}\n")

try:
    from database.db_service import get_db_service
    _DB_ENABLED = True
except ImportError:
    _DB_ENABLED = False

class HoneypotLogger:
    """
    Centralized logging for honeypot activities
    """
    
    def __init__(self, honeypot_type='deceptive', service='ecommerce', log_dir='logs'):
        self.honeypot_type = honeypot_type
        self.service = service
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Database service
        self.db = get_db_service() if _DB_ENABLED else None
        
        # Site map for port resolution (if not provided)
        self.site_ports = {
            'banking': 4001, 'ecommerce': 4002, 'healthcare': 4003,
            'blog': 4004, 'api_service': 4005, 'corporate': 4006, 'admin_panel': 4007
        }
        
        # Configure separate log files

        self.request_log = self.log_dir / f'{honeypot_type}_{service}_requests.log'
        self.attack_log = self.log_dir / f'{honeypot_type}_{service}_attacks.log'
        self.interaction_log = self.log_dir / f'{honeypot_type}_{service}_interactions.log'
        
        # Wazuh log format (JSON)

        self.wazuh_log = self.log_dir / f'{honeypot_type}_{service}_wazuh.json'
        
        # Setup loggers

        self._setup_loggers()
    
    def _setup_loggers(self):
        """Setup logging handlers"""
        # Request logger

        self.request_logger = logging.getLogger(f'honeypot.{self.service}.requests')
        self.request_logger.setLevel(logging.INFO)
        request_handler = logging.FileHandler(self.request_log)
        request_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.request_logger.addHandler(request_handler)
        
        # Attack logger

        self.attack_logger = logging.getLogger(f'honeypot.{self.service}.attacks')
        self.attack_logger.setLevel(logging.WARNING)
        attack_handler = logging.FileHandler(self.attack_log)
        attack_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.attack_logger.addHandler(attack_handler)
        
        # Interaction logger

        self.interaction_logger = logging.getLogger(f'honeypot.{self.service}.interactions')
        self.interaction_logger.setLevel(logging.INFO)
        interaction_handler = logging.FileHandler(self.interaction_log)
        interaction_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.interaction_logger.addHandler(interaction_handler)
    
    def log_request(self, request_data):
        """Log incoming HTTP request"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'honeypot_type': self.honeypot_type,
            'service': self.service,
            'type': 'request',
            **request_data
        }
        
        # Log to request file

        self.request_logger.info(json.dumps(log_entry))
        
        # Also log to Wazuh format

        self._log_to_wazuh(log_entry)
    
    def log_attack(self, attack_data):
        """Log detected attack"""
        attack_id = hashlib.md5(
            f"{datetime.now().isoformat()}{attack_data}".encode()
        ).hexdigest()
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'honeypot_type': self.honeypot_type,
            'service': self.service,
            'type': 'attack',
            'attack_id': attack_id,
            'severity': 'high',
            **attack_data
        }
        
        # Log to attack file

        self.attack_logger.warning(json.dumps(log_entry))
        
        # Log to Wazuh with alert
        self._log_to_wazuh(log_entry, alert=True)

        # Log to Database
        if self.db:
            try:
                self.db.insert_attack({
                    'timestamp': log_entry['timestamp'],
                    'ip': attack_data.get('remote_addr') or attack_data.get('ip', '0.0.0.0'),
                    'attack_type': attack_data.get('pattern_detected', 'Honeypot Interaction'),
                    'attack_types': [attack_data.get('pattern_detected', 'Honeypot Interaction')],
                    'confidence': 1.0,
                    'detection_method': 'honeypot_internal',
                    'target_site': self.service,
                    'honeypot_port': self.site_ports.get(self.service),
                    'captured': True
                })
            except Exception:
                pass

        return attack_id
    
    def log_interaction(self, interaction_data):
        """Log user interaction"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'honeypot_type': self.honeypot_type,
            'service': self.service,
            'type': 'interaction',
            **interaction_data
        }
        
        # Log to interaction file

        self.interaction_logger.info(json.dumps(log_entry))
        
        # Log to Wazuh
        self._log_to_wazuh(log_entry)

        # Log to Database (as honeypot event)
        if self.db:
            try:
                self.db.insert_honeypot_event({
                    'timestamp': log_entry['timestamp'],
                    'honeypot_name': self.service,
                    'honeypot_port': self.site_ports.get(self.service),
                    'event_type': interaction_data.get('action', 'interaction'),
                    'ip': interaction_data.get('ip') or interaction_data.get('remote_addr', '0.0.0.0'),
                    'details': interaction_data
                })
            except Exception:
                pass
    
    def _log_to_wazuh(self, log_data, alert=False):
        """
        Log in Wazuh-compatible JSON format
        """
        wazuh_entry = {
            'timestamp': log_data.get('timestamp', datetime.now().isoformat()),
            'agent': {
                'name': f'honeypot-{self.service}',
                'type': self.honeypot_type
            },
            'data': log_data,
            'rule': {
                'level': 10 if alert else 3,
                'description': f'Honeypot {log_data.get("type", "activity")}'
            }
        }
        
        # Append to Wazuh log file

        with open(self.wazuh_log, 'a') as f:
            f.write(json.dumps(wazuh_entry) + '\n')
    
    def get_statistics(self):
        """Get honeypot statistics"""
        stats = {
            'total_requests': 0,
            'total_attacks': 0,
            'total_interactions': 0
        }
        
        # Count lines in log files

        if self.request_log.exists():
            with open(self.request_log, 'r') as f:
                stats['total_requests'] = sum(1 for _ in f)
        
        if self.attack_log.exists():
            with open(self.attack_log, 'r') as f:
                stats['total_attacks'] = sum(1 for _ in f)
        
        if self.interaction_log.exists():
            with open(self.interaction_log, 'r') as f:
                stats['total_interactions'] = sum(1 for _ in f)
        
        return stats

if __name__ == "__main__":
    # Test logger

    logger = HoneypotLogger('deceptive', 'ecommerce')
    
    # Test request log

    logger.log_request({
        'method': 'GET',
        'path': '/products',
        'remote_addr': '192.168.1.100'
    })
    
    # Test attack log

    logger.log_attack({
        'pattern_detected': 'union select',
        'query': "' UNION SELECT * FROM users--"
    })
    
    # Test interaction log

    logger.log_interaction({
        'action': 'login_attempt',
        'username': 'admin'
    })
    
    # Get stats

    print(json.dumps(logger.get_statistics(), indent=2))
