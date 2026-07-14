#!/usr/bin/env python3
"""
Canary Token Manager
Creates and manages canary tokens for honeypots
"""

import sys
import json
import secrets
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import hashlib

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_service import get_db_service

db = get_db_service()


class CanaryTokenManager:
    """Manages canary tokens across all honeypots"""
    
    def __init__(self):
        self.tokens = {}
        self._load_tokens()
    
    def create_token(self, token_type: str, honeypot_name: str,
                    description: str = None) -> str:
        """
        Create a new canary token
        
        Args:
            token_type: Type of token (url, email, api_key, document, dns)
            honeypot_name: Name of the honeypot
            description: Optional description
            
        Returns:
            Token ID
        """
        token_id = secrets.token_urlsafe(16)
        
        # Generate token value based on type
        if token_type == 'url':
            token_value = f"https://canary.decepticloud.local/{token_id}"
        elif token_type == 'email':
            token_value = f"alert-{token_id}@canary.decepticloud.local"
        elif token_type == 'api_key':
            token_value = f"sk_live_{secrets.token_urlsafe(32)}"
        elif token_type == 'document':
            token_value = f"document_{token_id}.pdf"
        elif token_type == 'dns':
            token_value = f"{token_id}.canary.decepticloud.local"
        else:
            token_value = secrets.token_urlsafe(32)
        
        # Store in database
        try:
            with db.get_connection() as conn:
                conn.execute("""
                    INSERT INTO canary_tokens (
                        token_id, token_type, token_value, honeypot_name
                    ) VALUES (?, ?, ?, ?)
                """, (token_id, token_type, token_value, honeypot_name))
                conn.commit()
            
            self.tokens[token_id] = {
                'type': token_type,
                'value': token_value,
                'honeypot': honeypot_name,
                'description': description,
                'created': datetime.now().isoformat(),
                'triggers': 0
            }
            
            return token_id
        
        except Exception as e:
            print(f"Error creating canary token: {e}")
            return None
    
    def trigger_token(self, token_id: str, ip: str, user_agent: str = None,
                     details: Dict = None):
        """
        Record a canary token trigger
        
        Args:
            token_id: Token ID that was triggered
            ip: IP address that triggered the token
            user_agent: User agent string
            details: Additional details
        """
        if token_id not in self.tokens:
            # Try to load from database
            self._load_token(token_id)
        
        if token_id not in self.tokens:
            print(f"Unknown token: {token_id}")
            return
        
        try:
            with db.get_connection() as conn:
                conn.execute("""
                    INSERT INTO canary_triggers (
                        token_id, timestamp, ip, user_agent, details_json
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    token_id,
                    datetime.now().isoformat(),
                    ip,
                    user_agent,
                    json.dumps(details or {})
                ))
                conn.commit()
            
            self.tokens[token_id]['triggers'] += 1
            
            # Create high-severity event
            from database.db_service import get_db_service
            db = get_db_service()
            db.insert_event({
                'timestamp': datetime.now().isoformat(),
                'event_type': 'canary',
                'severity': 'high',
                'source': f"canary-{self.tokens[token_id]['type']}",
                'message': f"Canary token triggered: {self.tokens[token_id]['type']}",
                'details': {
                    'token_id': token_id,
                    'token_type': self.tokens[token_id]['type'],
                    'honeypot': self.tokens[token_id]['honeypot'],
                    'ip': ip,
                    'user_agent': user_agent
                },
                'ip': ip
            })
            
            print(f"🚨 CANARY TOKEN TRIGGERED: {token_id} from {ip}")
        
        except Exception as e:
            print(f"Error triggering canary token: {e}")
    
    def get_token(self, token_id: str) -> Optional[Dict]:
        """Get token information"""
        if token_id not in self.tokens:
            self._load_token(token_id)
        return self.tokens.get(token_id)
    
    def get_all_tokens(self, honeypot_name: str = None) -> List[Dict]:
        """Get all tokens, optionally filtered by honeypot"""
        if honeypot_name:
            return [t for t in self.tokens.values() 
                   if t['honeypot'] == honeypot_name]
        return list(self.tokens.values())
    
    def get_triggers(self, token_id: str = None, limit: int = 100) -> List[Dict]:
        """Get token triggers"""
        try:
            with db.get_connection() as conn:
                if token_id:
                    cursor = conn.execute("""
                        SELECT * FROM canary_triggers
                        WHERE token_id = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (token_id, limit))
                else:
                    cursor = conn.execute("""
                        SELECT * FROM canary_triggers
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (limit,))
                
                return [dict(row) for row in cursor.fetchall()]
        
        except Exception as e:
            print(f"Error getting triggers: {e}")
            return []
    
    def delete_token(self, token_id: str) -> bool:
        """Delete a canary token"""
        try:
            with db.get_connection() as conn:
                conn.execute("DELETE FROM canary_tokens WHERE token_id = ?", (token_id,))
                conn.commit()
            
            if token_id in self.tokens:
                del self.tokens[token_id]
            
            return True
        
        except Exception as e:
            print(f"Error deleting token: {e}")
            return False
    
    def _load_tokens(self):
        """Load all tokens from database"""
        try:
            with db.get_connection() as conn:
                cursor = conn.execute("SELECT * FROM canary_tokens")
                for row in cursor.fetchall():
                    token_id = row['token_id']
                    self.tokens[token_id] = {
                        'type': row['token_type'],
                        'value': row['token_value'],
                        'honeypot': row['honeypot_name'],
                        'created': row['created_at'],
                        'triggers': 0
                    }
                
                # Count triggers
                cursor = conn.execute("""
                    SELECT token_id, COUNT(*) as count
                    FROM canary_triggers
                    GROUP BY token_id
                """)
                for row in cursor.fetchall():
                    token_id = row['token_id']
                    if token_id in self.tokens:
                        self.tokens[token_id]['triggers'] = row['count']
        
        except Exception as e:
            print(f"Error loading tokens: {e}")
    
    def _load_token(self, token_id: str):
        """Load a single token from database"""
        try:
            with db.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM canary_tokens WHERE token_id = ?",
                    (token_id,)
                )
                row = cursor.fetchone()
                if row:
                    self.tokens[token_id] = {
                        'type': row['token_type'],
                        'value': row['token_value'],
                        'honeypot': row['honeypot_name'],
                        'created': row['created_at'],
                        'triggers': 0
                    }
        
        except Exception as e:
            print(f"Error loading token: {e}")
    
    def embed_in_html(self, token_id: str, html_content: str) -> str:
        """
        Embed a canary token in HTML content
        
        Args:
            token_id: Token ID to embed
            html_content: HTML content to modify
            
        Returns:
            Modified HTML with embedded token
        """
        token = self.get_token(token_id)
        if not token:
            return html_content
        
        if token['type'] == 'url':
            # Add hidden link
            canary_html = f'<a href="{token["value"]}" style="display:none;">.</a>'
            # Insert before closing body tag
            if '</body>' in html_content:
                html_content = html_content.replace('</body>', f'{canary_html}</body>')
            else:
                html_content += canary_html
        
        elif token['type'] == 'email':
            # Add hidden mailto link
            canary_html = f'<a href="mailto:{token["value"]}" style="display:none;">.</a>'
            if '</body>' in html_content:
                html_content = html_content.replace('</body>', f'{canary_html}</body>')
            else:
                html_content += canary_html
        
        return html_content


# Singleton instance
_manager = None

def get_canary_manager() -> CanaryTokenManager:
    """Get the singleton canary token manager"""
    global _manager
    if _manager is None:
        _manager = CanaryTokenManager()
    return _manager


if __name__ == '__main__':
    # Test the canary manager
    manager = get_canary_manager()
    
    # Create test tokens
    url_token = manager.create_token('url', 'banking', 'Hidden link in banking page')
    email_token = manager.create_token('email', 'ecommerce', 'Fake support email')
    api_token = manager.create_token('api_key', 'api_service', 'Fake API key')
    
    print(f"Created tokens:")
    print(f"  URL: {url_token}")
    print(f"  Email: {email_token}")
    print(f"  API Key: {api_token}")
    
    # Test trigger
    manager.trigger_token(url_token, '192.168.1.100', 'Mozilla/5.0')
    
    # Get all tokens
    tokens = manager.get_all_tokens()
    print(f"\nTotal tokens: {len(tokens)}")
    
    # Get triggers
    triggers = manager.get_triggers()
    print(f"Total triggers: {len(triggers)}")
