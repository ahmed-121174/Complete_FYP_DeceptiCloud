#!/usr/bin/env python3
"""
Database Integration Module for Routing Proxy
Handles logging attacks and events to the centralized database
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import hashlib

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_service import get_db_service

# Initialize database service
db = get_db_service()


def log_attack_to_db(attack_data: Dict) -> Optional[int]:
    """
    Log an attack to the database
    
    Args:
        attack_data: Dictionary containing attack information
        
    Returns:
        Attack ID if successful, None otherwise
    """
    try:
        # Prepare attack data for database
        db_attack = {
            'timestamp': attack_data.get('timestamp', datetime.now().isoformat()),
            'ip': attack_data.get('ip', ''),
            'user_agent': attack_data.get('user_agent', ''),
            'method': attack_data.get('method', 'GET'),
            'url': attack_data.get('url', ''),
            'path': attack_data.get('path', ''),
            'query_string': attack_data.get('query_string', ''),
            'attack_type': attack_data.get('attack_type', 'Unknown'),
            'attack_types': attack_data.get('attack_types', []),
            'confidence': attack_data.get('confidence', 0.0),
            'detection_method': attack_data.get('detection_method', 'unknown'),
            'routed_to': attack_data.get('routed_to', 'honeypot'),
            'honeypot_port': attack_data.get('honeypot_port'),
            'target_site': attack_data.get('target', ''),
            'payload': attack_data.get('payload', ''),
            'headers': attack_data.get('headers', {}),
            'classification': attack_data.get('classification', {}),
            'captured': attack_data.get('captured', True),
            'session_id': attack_data.get('session_id')
        }

        # Skip entries that have no classification (direct honeypot hits with no ML processing)
        # These are noise — Unknown attack type with zero confidence
        if db_attack['attack_type'] in ('Unknown', '') and db_attack['confidence'] == 0.0:
            return None

        # Insert into database
        attack_id = db.insert_attack(db_attack)
        
        # Update attacker profile
        if db_attack['ip']:
            update_attacker_profile(
                ip=db_attack['ip'],
                attack_types=db_attack['attack_types'],
                user_agent=db_attack['user_agent'],
                confidence=db_attack['confidence']
            )
        
        # Create system event for high-severity attacks
        if db_attack['confidence'] >= 0.85:
            create_system_event(
                event_type='attack',
                severity='high' if db_attack['confidence'] >= 0.95 else 'medium',
                source='routing_proxy',
                message=f"{db_attack['attack_type']} attack from {db_attack['ip']}",
                details={
                    'attack_id': attack_id,
                    'attack_type': db_attack['attack_type'],
                    'confidence': db_attack['confidence'],
                    'target': db_attack['target_site']
                },
                ip=db_attack['ip'],
                related_attack_id=attack_id
            )
        
        return attack_id
    
    except Exception as e:
        print(f"Error logging attack to database: {e}")
        return None


def update_attacker_profile(ip: str, attack_types: list, user_agent: str = None, 
                            confidence: float = 0.0):
    """
    Update or create attacker profile
    
    Args:
        ip: Attacker IP address
        attack_types: List of attack types
        user_agent: User agent string
        confidence: Attack confidence score
    """
    try:
        # Get existing profile or create new
        existing = db.get_attacker_profile_by_ip(ip)
        
        if existing:
            # Merge attack types
            existing_types = set(json.loads(existing.get('attack_types_json', '[]')))
            existing_types.update(attack_types)
            
            # Merge user agents
            existing_uas = set(json.loads(existing.get('user_agents_json', '[]')))
            if user_agent:
                existing_uas.add(user_agent)
            
            # Update threat score (weighted average)
            current_score = existing.get('threat_score', 0.0)
            attack_count = existing.get('attack_count', 0)
            new_score = (current_score * attack_count + confidence) / (attack_count + 1)
            
            profile_data = {
                'ip': ip,
                'last_seen': datetime.now().isoformat(),
                'attack_types': list(existing_types),
                'user_agents': list(existing_uas),
                'threat_score': new_score,
                'behavioral_hash': generate_behavioral_hash(ip, list(existing_types), list(existing_uas))
            }
        else:
            # Create new profile
            profile_data = {
                'ip': ip,
                'first_seen': datetime.now().isoformat(),
                'last_seen': datetime.now().isoformat(),
                'attack_types': attack_types,
                'user_agents': [user_agent] if user_agent else [],
                'threat_score': confidence,
                'behavioral_hash': generate_behavioral_hash(ip, attack_types, [user_agent] if user_agent else [])
            }
        
        db.upsert_attacker_profile(profile_data)
    
    except Exception as e:
        print(f"Error updating attacker profile: {e}")


def generate_behavioral_hash(ip: str, attack_types: list, user_agents: list) -> str:
    """
    Generate a behavioral fingerprint hash
    
    Args:
        ip: IP address
        attack_types: List of attack types
        user_agents: List of user agents
        
    Returns:
        SHA256 hash of behavioral patterns
    """
    # Create a string representation of behavior
    behavior_str = f"{ip}|{sorted(attack_types)}|{sorted(user_agents)}"
    return hashlib.sha256(behavior_str.encode()).hexdigest()[:16]


def create_system_event(event_type: str, severity: str, source: str, 
                       message: str, details: Dict = None, ip: str = None,
                       related_attack_id: int = None):
    """
    Create a system event
    
    Args:
        event_type: Type of event ('attack', 'system', 'honeypot', 'ml', 'wazuh')
        severity: Severity level ('low', 'medium', 'high', 'critical')
        source: Source component
        message: Event message
        details: Additional details dictionary
        ip: Related IP address
        related_attack_id: Related attack ID
    """
    try:
        event_data = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'severity': severity,
            'source': source,
            'message': message,
            'details': details or {},
            'ip': ip,
            'related_attack_id': related_attack_id
        }
        
        db.insert_event(event_data)
    
    except Exception as e:
        print(f"Error creating system event: {e}")


def log_honeypot_event(honeypot_name: str, honeypot_port: int, event_type: str,
                       ip: str, details: Dict = None, session_id: str = None,
                       attack_id: int = None):
    """
    Log a honeypot interaction event
    
    Args:
        honeypot_name: Name of the honeypot
        honeypot_port: Port number
        event_type: Type of event
        ip: Attacker IP
        details: Event details
        session_id: Session ID
        attack_id: Related attack ID
    """
    try:
        with db.get_connection() as conn:
            conn.execute("""
                INSERT INTO honeypot_events (
                    timestamp, honeypot_name, honeypot_port, event_type,
                    ip, session_id, details_json, attack_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                honeypot_name,
                honeypot_port,
                event_type,
                ip,
                session_id,
                json.dumps(details or {}),
                attack_id
            ))
            conn.commit()
    
    except Exception as e:
        print(f"Error logging honeypot event: {e}")


def get_attack_stats() -> Dict:
    """Get attack statistics from database"""
    try:
        return db.get_attack_stats()
    except Exception as e:
        print(f"Error getting attack stats: {e}")
        return {
            'total': 0,
            'by_type': {},
            'by_hour': {},
            'top_ips': [],
            'avg_confidence': 0.0
        }


def get_recent_attacks(limit: int = 50) -> list:
    """Get recent attacks from database"""
    try:
        return db.get_attacks(limit=limit)
    except Exception as e:
        print(f"Error getting recent attacks: {e}")
        return []


def get_attacker_profiles(limit: int = 100) -> list:
    """Get attacker profiles from database"""
    try:
        return db.get_attacker_profiles(limit=limit)
    except Exception as e:
        print(f"Error getting attacker profiles: {e}")
        return []


def get_cluster_stats() -> Dict:
    """Get clustering statistics"""
    try:
        return db.get_cluster_stats()
    except Exception as e:
        print(f"Error getting cluster stats: {e}")
        return {
            'total_profiles': 0,
            'cluster_count': 0,
            'clusters': []
        }


# Export functions
__all__ = [
    'log_attack_to_db',
    'update_attacker_profile',
    'create_system_event',
    'log_honeypot_event',
    'get_attack_stats',
    'get_recent_attacks',
    'get_attacker_profiles',
    'get_cluster_stats'
]
