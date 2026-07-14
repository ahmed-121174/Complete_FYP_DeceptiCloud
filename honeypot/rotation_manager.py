import os
import time
import random
import logging
import subprocess
import json
from datetime import datetime, timedelta
from pathlib import Path

class RotationManager:
    """
    Manages IP and Port rotation for honeypot instances
    """
    
    def __init__(self, config_file='config/rotation_config.json'):
        self.config_file = Path(config_file)
        self.config = self.load_config()
        self.logger = logging.getLogger('rotation_manager')
        self.logger.setLevel(logging.INFO)
        
        # Rotation state

        self.current_ip = None
        self.current_port = None
        self.last_rotation = None
        self.rotation_count = 0
        
    def load_config(self):
        """Load rotation configuration"""
        default_config = {
            'rotation_interval_seconds': 300,  # 5 minutes
            'ip_pool': [
                '10.0.1.10', '10.0.1.11', '10.0.1.12', '10.0.1.13', '10.0.1.14',
                '10.0.1.15', '10.0.1.16', '10.0.1.17', '10.0.1.18', '10.0.1.19'
            ],
            'port_pool': [8080, 8081, 8082, 8083, 8084, 8085, 8086, 8087, 8088, 8089],
            'kubernetes_enabled': True,
            'kubernetes_namespace': 'honeypot',
            'service_name': 'honeypot-service'
        }
        
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                loaded_config = json.load(f)
                default_config.update(loaded_config)
        else:
            # Create default config

            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
        
        return default_config
    
    def get_next_ip_port(self):
        """Get next IP and port combination"""
        # Exclude current values to ensure rotation

        available_ips = [ip for ip in self.config['ip_pool'] if ip != self.current_ip]
        available_ports = [port for port in self.config['port_pool'] if port != self.current_port]
        
        new_ip = random.choice(available_ips if available_ips else self.config['ip_pool'])
        new_port = random.choice(available_ports if available_ports else self.config['port_pool'])
        
        return new_ip, new_port
    
    def rotate(self):
        """Perform IP/Port rotation"""
        self.logger.info("Starting rotation...")
        
        # Get new IP and port

        new_ip, new_port = self.get_next_ip_port()
        
        self.logger.info(f"Rotating from {self.current_ip}:{self.current_port} to {new_ip}:{new_port}")
        
        # Update Kubernetes service if enabled

        if self.config['kubernetes_enabled']:
            success = self.update_kubernetes_service(new_ip, new_port)
            if not success:
                self.logger.error("Failed to update Kubernetes service")
                return False
        
        # Update state

        self.current_ip = new_ip
        self.current_port = new_port
        self.last_rotation = datetime.now()
        self.rotation_count += 1
        
        self.logger.info(f" Rotation #{self.rotation_count} complete: {new_ip}:{new_port}")
        
        # Save state

        self.save_state()
        
        return True
    
    def update_kubernetes_service(self, new_ip, new_port):
        """
        Update Kubernetes service with new IP/port
        """
        try:
            namespace = self.config['kubernetes_namespace']
            service_name = self.config['service_name']
            
            # Patch service with new external IP

            patch = {
                'spec': {
                    'externalIPs': [new_ip],
                    'ports': [{
                        'port': new_port,
                        'targetPort': 8080,
                        'protocol': 'TCP'
                    }]
                }
            }
            
            patch_json = json.dumps(patch)
            
            cmd = [
                'kubectl', 'patch', 'service', service_name,
                '-n', namespace,
                '--type', 'merge',
                '-p', patch_json
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f" Kubernetes service updated")
                return True
            else:
                self.logger.error(f" Kubectl error: {result.stderr}")
                return False
        
        except Exception as e:
            self.logger.error(f"Error updating Kubernetes: {e}")
            return False
    
    def should_rotate(self):
        """Check if rotation is needed"""
        if self.last_rotation is None:
            return True
        
        elapsed = (datetime.now() - self.last_rotation).total_seconds()
        return elapsed >= self.config['rotation_interval_seconds']
    
    def run_rotation_loop(self):
        """
        Main rotation loop - runs continuously
        """
        self.logger.info("Starting rotation loop...")
        
        # Initial rotation

        self.rotate()
        
        while True:
            if self.should_rotate():
                self.rotate()
            
            # Sleep for a short interval before checking again

            time.sleep(min(60, self.config['rotation_interval_seconds'] // 5))
    
    def save_state(self):
        """Save current state to file"""
        state_file = Path('logs/rotation_state.json')
        state_file.parent.mkdir(parents=True, exist_ok=True)
        
        state = {
            'current_ip': self.current_ip,
            'current_port': self.current_port,
            'last_rotation': self.last_rotation.isoformat() if self.last_rotation else None,
            'rotation_count': self.rotation_count
        }
        
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_state(self):
        """Load previous state"""
        state_file = Path('logs/rotation_state.json')
        
        if state_file.exists():
            with open(state_file, 'r') as f:
                state = json.load(f)
            
            self.current_ip = state.get('current_ip')
            self.current_port = state.get('current_port')
            if state.get('last_rotation'):
                self.last_rotation = datetime.fromisoformat(state['last_rotation'])
            self.rotation_count = state.get('rotation_count', 0)
            
            self.logger.info(f"Loaded state: {self.current_ip}:{self.current_port}")
    
    def get_status(self):
        """Get current rotation status"""
        return {
            'current_ip': self.current_ip,
            'current_port': self.current_port,
            'last_rotation': self.last_rotation.isoformat() if self.last_rotation else None,
            'rotation_count': self.rotation_count,
            'next_rotation_in': self.config['rotation_interval_seconds'] - 
                               (datetime.now() - self.last_rotation).total_seconds() 
                               if self.last_rotation else 0
        }

if __name__ == "__main__":
    # Setup logging

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create rotation manager

    manager = RotationManager()
    
    # Load previous state if exists

    manager.load_state()
    
    # Run rotation loop

    try:
        manager.run_rotation_loop()
    except KeyboardInterrupt:
        print("\n Rotation manager stopped")
        manager.save_state()
