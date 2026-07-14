#!/usr/bin/env python3
"""
Enhanced Honeypot Logger
Comprehensive logging for all honeypot interactions
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import hashlib

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_service import get_db_service

db = get_db_service()


class HoneypotLogger:
    """Enhanced logger for honeypot events"""
    
    def __init__(self, honeypot_name: str, honeypot_port: int):
        self.honeypot_name = honeypot_name
        self.honeypot_port = honeypot_port
        self.session_cache = {}
    
    def log_interaction(self, event_type: str, ip: str, details: Dict,
                       user_agent: str = None, session_id: str = None):
        """
        Log a honeypot interaction
        
        Args:
            event_type: Type of interaction (login_attempt, form_submit, api_call, etc.)
            ip: Attacker IP address
            details: Event details dictionary
            user_agent: User agent string
            session_id: Session identifier
        """
        try:
            # Generate session ID if not provided
            if not session_id:
                session_id = self._generate_session_id(ip, user_agent)
            
            # Log to database
            with db.get_connection() as conn:
                conn.execute("""
                    INSERT INTO honeypot_events (
                        timestamp, honeypot_name, honeypot_port, event_type,
                        ip, session_id, details_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    self.honeypot_name,
                    self.honeypot_port,
                    event_type,
                    ip,
                    session_id,
                    json.dumps(details)
                ))
                conn.commit()
            
            # Update session cache
            if session_id not in self.session_cache:
                self.session_cache[session_id] = {
                    'ip': ip,
                    'first_seen': datetime.now().isoformat(),
                    'event_count': 0
                }
            self.session_cache[session_id]['event_count'] += 1
            self.session_cache[session_id]['last_seen'] = datetime.now().isoformat()
            
        except Exception as e:
            print(f"Error logging honeypot interaction: {e}")
    
    def log_login_attempt(self, ip: str, username: str, password: str,
                         success: bool, user_agent: str = None):
        """Log a login attempt"""
        details = {
            'username': username,
            'password_hash': hashlib.sha256(password.encode()).hexdigest()[:16],
            'success': success,
            'user_agent': user_agent
        }
        self.log_interaction('login_attempt', ip, details, user_agent)
    
    def log_form_submit(self, ip: str, form_data: Dict, user_agent: str = None):
        """Log a form submission"""
        # Sanitize sensitive data
        sanitized = {k: '***' if 'password' in k.lower() else v 
                    for k, v in form_data.items()}
        details = {
            'form_data': sanitized,
            'user_agent': user_agent
        }
        self.log_interaction('form_submit', ip, details, user_agent)
    
    def log_api_call(self, ip: str, endpoint: str, method: str, 
                    params: Dict = None, user_agent: str = None):
        """Log an API call"""
        details = {
            'endpoint': endpoint,
            'method': method,
            'params': params or {},
            'user_agent': user_agent
        }
        self.log_interaction('api_call', ip, details, user_agent)
    
    def log_file_access(self, ip: str, file_path: str, user_agent: str = None):
        """Log a file access attempt"""
        details = {
            'file_path': file_path,
            'user_agent': user_agent
        }
        self.log_interaction('file_access', ip, details, user_agent)
    
    def log_search_query(self, ip: str, query: str, user_agent: str = None):
        """Log a search query"""
        details = {
            'query': query,
            'user_agent': user_agent
        }
        self.log_interaction('search_query', ip, details, user_agent)
    
    def log_page_view(self, ip: str, page: str, referrer: str = None,
                     user_agent: str = None):
        """Log a page view"""
        details = {
            'page': page,
            'referrer': referrer,
            'user_agent': user_agent
        }
        self.log_interaction('page_view', ip, details, user_agent)
    
    def log_download_attempt(self, ip: str, file_name: str, user_agent: str = None):
        """Log a file download attempt"""
        details = {
            'file_name': file_name,
            'user_agent': user_agent
        }
        self.log_interaction('download_attempt', ip, details, user_agent)
    
    def log_command_execution(self, ip: str, command: str, user_agent: str = None):
        """Log a command execution attempt"""
        details = {
            'command': command,
            'user_agent': user_agent
        }
        self.log_interaction('command_execution', ip, details, user_agent)
    
    def get_session_stats(self, session_id: str) -> Optional[Dict]:
        """Get statistics for a session"""
        return self.session_cache.get(session_id)
    
    def get_active_sessions(self) -> Dict:
        """Get all active sessions"""
        return self.session_cache
    
    def _generate_session_id(self, ip: str, user_agent: str = None) -> str:
        """Generate a session ID based on IP and user agent"""
        data = f"{ip}:{user_agent or 'unknown'}:{datetime.now().date()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


# Singleton instances for each honeypot
_loggers = {}

def get_honeypot_logger(honeypot_name: str, honeypot_port: int) -> HoneypotLogger:
    """Get or create a honeypot logger instance"""
    key = f"{honeypot_name}:{honeypot_port}"
    if key not in _loggers:
        _loggers[key] = HoneypotLogger(honeypot_name, honeypot_port)
    return _loggers[key]


if __name__ == '__main__':
    # Test the logger
    logger = get_honeypot_logger('banking', 4001)
    
    # Test login attempt
    logger.log_login_attempt(
        ip='192.168.1.100',
        username='admin',
        password='password123',
        success=False,
        user_agent='Mozilla/5.0'
    )
    
    # Test API call
    logger.log_api_call(
        ip='192.168.1.100',
        endpoint='/api/users',
        method='GET',
        user_agent='sqlmap/1.0'
    )
    
    print("✓ Honeypot logger test successful")
