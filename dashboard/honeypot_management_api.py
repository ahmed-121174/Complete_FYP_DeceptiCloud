#!/usr/bin/env python3
"""
Honeypot Management API Endpoints
Provides honeypot control, routing rules, session tracking, and canary token management
"""

import sys
import json
import requests
from pathlib import Path
from datetime import datetime
from flask import Blueprint, request, jsonify

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_service import get_db_service
from config import PROXY_URL, HONEYPOT_PORTS

# Create blueprint
honeypot_mgmt_bp = Blueprint('honeypot_management', __name__)
db = get_db_service()

# Honeypot configuration
HONEYPOTS = [
    {'id': 'banking', 'name': 'SecureBank', 'type': 'banking', 'real_port': 3001, 'hp_port': 4001},
    {'id': 'ecommerce', 'name': 'MegaStore', 'type': 'ecommerce', 'real_port': 3002, 'hp_port': 4002},
    {'id': 'healthcare', 'name': 'MedClinic', 'type': 'healthcare', 'real_port': 3003, 'hp_port': 4003},
    {'id': 'blog', 'name': 'TechBlog', 'type': 'blog', 'real_port': 3004, 'hp_port': 4004},
    {'id': 'api_service', 'name': 'DataAPI', 'type': 'api_service', 'real_port': 3005, 'hp_port': 4005},
    {'id': 'corporate', 'name': 'NexaGen', 'type': 'corporate', 'real_port': 3006, 'hp_port': 4006},
    {'id': 'admin_panel', 'name': 'SysNet', 'type': 'admin_panel', 'real_port': 3007, 'hp_port': 4007},
    {'id': 'ssh', 'name': 'SSH Honeypot', 'type': 'ssh', 'real_port': 22, 'hp_port': 2222},
]


def check_port_status(port):
    """Check if a port is responding"""
    try:
        response = requests.get(f'http://localhost:{port}/', timeout=1)
        return True
    except:
        return False


@honeypot_mgmt_bp.route('/api/honeypots/list', methods=['GET'])
def list_honeypots():
    """Get list of all honeypots with their status"""
    try:
        honeypots_status = []
        
        for hp in HONEYPOTS:
            # Check real and honeypot status
            real_status = check_port_status(hp['real_port']) if hp['id'] != 'ssh' else True
            hp_status = check_port_status(hp['hp_port'])
            
            # Get stats from database
            with db.get_connection() as conn:
                # Count attacks routed to this honeypot
                cursor = conn.execute("""
                    SELECT COUNT(*) as count
                    FROM attacks
                    WHERE target_site = ? AND routed_to = 'honeypot'
                """, (hp['type'],))
                attack_count = cursor.fetchone()['count']
                
                # Count active sessions
                cursor = conn.execute("""
                    SELECT COUNT(*) as count
                    FROM sessions
                    WHERE is_active = 1
                """)
                active_sessions = cursor.fetchone()['count']
            
            honeypots_status.append({
                'id': hp['id'],
                'name': hp['name'],
                'type': hp['type'],
                'real_port': hp['real_port'],
                'hp_port': hp['hp_port'],
                'real_status': 'online' if real_status else 'offline',
                'hp_status': 'online' if hp_status else 'offline',
                'attack_count': attack_count,
                'active_sessions': active_sessions,
                'enabled': hp_status  # Honeypot is enabled if it's online
            })
        
        # Get total attacks captured (aligned with overview stats)
        with db.get_connection() as conn:
            total_captured = conn.execute(
                "SELECT COUNT(*) as c FROM attacks WHERE captured = 1"
            ).fetchone()['c']
        
        return jsonify({
            'honeypots': honeypots_status,
            'total': len(honeypots_status),
            'online': sum(1 for h in honeypots_status if h['hp_status'] == 'online'),
            'total_attacks_captured': total_captured
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@honeypot_mgmt_bp.route('/api/honeypots/<honeypot_id>/status', methods=['GET'])
def get_honeypot_status(honeypot_id: str):
    """Get detailed status for a specific honeypot"""
    try:
        # Find honeypot config
        hp = next((h for h in HONEYPOTS if h['id'] == honeypot_id), None)
        if not hp:
            return jsonify({'error': 'Honeypot not found'}), 404
        
        # Check status
        real_status = check_port_status(hp['real_port']) if hp['id'] != 'ssh' else True
        hp_status = check_port_status(hp['hp_port'])
        
        # Get detailed stats
        with db.get_connection() as conn:
            # Recent attacks
            cursor = conn.execute("""
                SELECT * FROM attacks
                WHERE target_site = ? AND routed_to = 'honeypot'
                ORDER BY timestamp DESC
                LIMIT 50
            """, (hp['type'],))
            recent_attacks = [dict(row) for row in cursor.fetchall()]
            
            # Active sessions
            cursor = conn.execute("""
                SELECT * FROM sessions
                WHERE is_active = 1
                ORDER BY start_time DESC
            """)
            active_sessions = [dict(row) for row in cursor.fetchall()]
            
            # Canary triggers
            cursor = conn.execute("""
                SELECT * FROM honeypot_events
                WHERE event_type = 'canary_trigger'
                ORDER BY timestamp DESC
                LIMIT 20
            """)
            canary_triggers = [dict(row) for row in cursor.fetchall()]
        
        return jsonify({
            'id': hp['id'],
            'name': hp['name'],
            'type': hp['type'],
            'real_port': hp['real_port'],
            'hp_port': hp['hp_port'],
            'real_status': 'online' if real_status else 'offline',
            'hp_status': 'online' if hp_status else 'offline',
            'enabled': hp_status,
            'recent_attacks': recent_attacks,
            'active_sessions': active_sessions,
            'canary_triggers': canary_triggers,
            'stats': {
                'total_attacks': len(recent_attacks),
                'active_sessions': len(active_sessions),
                'canary_triggers': len(canary_triggers)
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@honeypot_mgmt_bp.route('/api/honeypots/<honeypot_id>/toggle', methods=['POST'])
def toggle_honeypot(honeypot_id: str):
    """Enable or disable a honeypot (note: actual control requires process management)"""
    try:
        data = request.get_json() or {}
        enabled = data.get('enabled', True)
        
        # Find honeypot
        hp = next((h for h in HONEYPOTS if h['id'] == honeypot_id), None)
        if not hp:
            return jsonify({'error': 'Honeypot not found'}), 404
        
        # Log the action
        with db.get_connection() as conn:
            conn.execute("""
                INSERT INTO events (timestamp, event_type, severity, description, metadata_json)
                VALUES (?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                'honeypot_toggle',
                'info',
                f"Honeypot {hp['name']} {'enabled' if enabled else 'disabled'}",
                json.dumps({'honeypot_id': honeypot_id, 'enabled': enabled})
            ))
            conn.commit()
        
        # Note: Actual process control would require systemd/supervisor integration
        # For now, we just log the action
        
        return jsonify({
            'status': 'success',
            'honeypot_id': honeypot_id,
            'enabled': enabled,
            'message': f"Honeypot {hp['name']} {'enabled' if enabled else 'disabled'}",
            'note': 'Process control requires manual restart of honeypot services'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@honeypot_mgmt_bp.route('/api/routing-rules/list', methods=['GET'])
def list_routing_rules():
    """Get all routing rules"""
    try:
        with db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    id,
                    rule_name as name,
                    priority,
                    condition_json,
                    action,
                    target_honeypot,
                    is_active as enabled,
                    created_at,
                    updated_at
                FROM routing_rules
                ORDER BY priority DESC, created_at DESC
            """)
            rules = [dict(row) for row in cursor.fetchall()]
            
            # Parse JSON fields and format for frontend
            for rule in rules:
                # Parse condition JSON
                if rule.get('condition_json'):
                    try:
                        condition_data = json.loads(rule['condition_json'])
                        rule['condition'] = condition_data.get('description', 'Custom condition')
                        rule['conditions'] = condition_data
                    except:
                        rule['condition'] = 'Parse error'
                        rule['conditions'] = {}
                else:
                    rule['condition'] = 'None'
                    rule['conditions'] = {}
                
                # Format action
                if rule.get('action'):
                    if rule['action'] == 'route_to_honeypot':
                        target = rule.get('target_honeypot', 'auto')
                        rule['action_display'] = f"Route to {target} honeypot"
                    else:
                        rule['action_display'] = rule['action'].replace('_', ' ').title()
                else:
                    rule['action_display'] = 'None'
                
                # Format status
                rule['status'] = 'Enabled' if rule.get('enabled') else 'Disabled'
        
        return jsonify({
            'rules': rules,
            'total': len(rules)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@honeypot_mgmt_bp.route('/api/routing-rules/create', methods=['POST'])
def create_routing_rule():
    """Create a new routing rule"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Rule name is required'}), 400
        
        with db.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO routing_rules (
                    name, description, priority, enabled,
                    conditions_json, actions_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['name'],
                data.get('description', ''),
                data.get('priority', 50),
                data.get('enabled', True),
                json.dumps(data.get('conditions', {})),
                json.dumps(data.get('actions', {})),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            conn.commit()
            rule_id = cursor.lastrowid
        
        return jsonify({
            'status': 'success',
            'rule_id': rule_id,
            'message': 'Routing rule created successfully'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@honeypot_mgmt_bp.route('/api/routing-rules/<int:rule_id>/update', methods=['PUT'])
def update_routing_rule(rule_id: int):
    """Update an existing routing rule"""
    try:
        data = request.get_json()
        
        with db.get_connection() as conn:
            # Check if rule exists
            cursor = conn.execute("SELECT id FROM routing_rules WHERE id = ?", (rule_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Rule not found'}), 404
            
            # Update rule
            conn.execute("""
                UPDATE routing_rules
                SET name = ?, description = ?, priority = ?, enabled = ?,
                    conditions_json = ?, actions_json = ?, updated_at = ?
                WHERE id = ?
            """, (
                data.get('name'),
                data.get('description', ''),
                data.get('priority', 50),
                data.get('enabled', True),
                json.dumps(data.get('conditions', {})),
                json.dumps(data.get('actions', {})),
                datetime.now().isoformat(),
                rule_id
            ))
            conn.commit()
        
        return jsonify({
            'status': 'success',
            'rule_id': rule_id,
            'message': 'Routing rule updated successfully'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@honeypot_mgmt_bp.route('/api/routing-rules/<int:rule_id>/delete', methods=['DELETE'])
def delete_routing_rule(rule_id: int):
    """Delete a routing rule"""
    try:
        with db.get_connection() as conn:
            # Check if rule exists
            cursor = conn.execute("SELECT id FROM routing_rules WHERE id = ?", (rule_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Rule not found'}), 404
            
            # Delete rule
            conn.execute("DELETE FROM routing_rules WHERE id = ?", (rule_id,))
            conn.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Routing rule deleted successfully'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@honeypot_mgmt_bp.route('/api/sessions/active', methods=['GET'])
def get_active_sessions():
    """Get all active sessions"""
    try:
        with db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT s.*, ap.threat_score, ap.attack_types_json
                FROM sessions s
                LEFT JOIN attacker_profiles ap ON s.ip = ap.ip
                WHERE s.is_active = 1
                ORDER BY s.start_time DESC
            """)
            sessions = [dict(row) for row in cursor.fetchall()]
            
            # Parse JSON fields
            for session in sessions:
                if session.get('honeypots_visited_json'):
                    session['honeypots_visited'] = json.loads(session['honeypots_visited_json'])
                if session.get('actions_json'):
                    session['actions'] = json.loads(session['actions_json'])
                if session.get('attack_types_json'):
                    session['attack_types'] = json.loads(session['attack_types_json'])
                
                # Calculate duration
                start = datetime.fromisoformat(session['start_time'])
                duration = (datetime.now() - start).total_seconds()
                session['duration_seconds'] = int(duration)
        
        return jsonify({
            'sessions': sessions,
            'total': len(sessions)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@honeypot_mgmt_bp.route('/api/sessions/<int:session_id>/terminate', methods=['POST'])
def terminate_session(session_id: int):
    """Terminate an active session"""
    try:
        with db.get_connection() as conn:
            # Check if session exists
            cursor = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            session = cursor.fetchone()
            
            if not session:
                return jsonify({'error': 'Session not found'}), 404
            
            # Update session
            end_time = datetime.now().isoformat()
            start_time = datetime.fromisoformat(session['start_time'])
            duration = int((datetime.now() - start_time).total_seconds())
            
            conn.execute("""
                UPDATE sessions
                SET is_active = 0, end_time = ?, duration_seconds = ?
                WHERE id = ?
            """, (end_time, duration, session_id))
            conn.commit()
        
        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'message': 'Session terminated successfully'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@honeypot_mgmt_bp.route('/api/canary-tokens/list', methods=['GET'])
def list_canary_tokens():
    """Get all canary tokens and their trigger counts"""
    try:
        # Get canary token stats from honeypot events
        with db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    event_type,
                    COUNT(*) as trigger_count,
                    MAX(timestamp) as last_triggered
                FROM honeypot_events
                WHERE event_type LIKE 'canary_%'
                GROUP BY event_type
            """)
            token_stats = [dict(row) for row in cursor.fetchall()]
            
            # Get recent triggers
            cursor = conn.execute("""
                SELECT * FROM honeypot_events
                WHERE event_type LIKE 'canary_%'
                ORDER BY timestamp DESC
                LIMIT 50
            """)
            recent_triggers = [dict(row) for row in cursor.fetchall()]
        
        # Define available canary token types
        token_types = [
            {'type': 'env_file', 'name': '.env File', 'path': '/.env', 'description': 'Fake environment variables'},
            {'type': 'backup_sql', 'name': 'backup.sql', 'path': '/backup.sql', 'description': 'Decoy database dump'},
            {'type': 'wp_admin', 'name': 'wp-admin', 'path': '/wp-admin', 'description': 'Fake WordPress panel'},
            {'type': 'phpmyadmin', 'name': 'phpMyAdmin', 'path': '/phpmyadmin', 'description': 'Decoy DB manager'},
            {'type': 'api_config', 'name': 'API Config', 'path': '/config/api.json', 'description': 'Fake API credentials'},
            {'type': 'git_config', 'name': '.git/config', 'path': '/.git/config', 'description': 'Repository exposure'},
            {'type': 'server_status', 'name': 'server-status', 'path': '/server-status', 'description': 'Apache status'},
            {'type': 'debug', 'name': 'Debug Endpoint', 'path': '/debug', 'description': 'Fake debug info'},
        ]
        
        # Merge stats with token types
        for token in token_types:
            stats = next((s for s in token_stats if s['event_type'] == f"canary_{token['type']}"), None)
            if stats:
                token['trigger_count'] = stats['trigger_count']
                token['last_triggered'] = stats['last_triggered']
            else:
                token['trigger_count'] = 0
                token['last_triggered'] = None
        
        return jsonify({
            'tokens': token_types,
            'total': len(token_types),
            'recent_triggers': recent_triggers,
            'total_triggers': sum(t['trigger_count'] for t in token_types)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@honeypot_mgmt_bp.route('/api/canary-tokens/create', methods=['POST'])
def create_canary_token():
    """Create a new canary token (logs the creation)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('type') or not data.get('path'):
            return jsonify({'error': 'Token type and path are required'}), 400
        
        # Log the token creation
        with db.get_connection() as conn:
            conn.execute("""
                INSERT INTO events (timestamp, event_type, severity, description, metadata_json)
                VALUES (?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                'canary_token_created',
                'info',
                f"Canary token created: {data['type']} at {data['path']}",
                json.dumps(data)
            ))
            conn.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Canary token created successfully',
            'note': 'Token will be active on next honeypot restart'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@honeypot_mgmt_bp.route('/api/proxy/config', methods=['GET', 'POST'])
def proxy_config():
    """Get or update proxy configuration"""
    try:
        if request.method == 'GET':
            # Get current config from proxy
            try:
                response = requests.get(f'{PROXY_URL}/proxy/status', timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    return jsonify({
                        'rotation_interval': data.get('rotation_interval', 60),
                        'current_site': data.get('current_site', 'banking'),
                        'known_attackers': data.get('known_attackers', 0)
                    })
            except:
                pass
            
            return jsonify({
                'rotation_interval': 60,
                'current_site': 'banking',
                'known_attackers': 0
            })
        
        else:  # POST
            data = request.get_json()
            
            # Update proxy config
            try:
                response = requests.post(
                    f'{PROXY_URL}/proxy/config',
                    json=data,
                    timeout=2
                )
                if response.status_code == 200:
                    return jsonify({
                        'status': 'success',
                        'message': 'Proxy configuration updated'
                    })
            except:
                pass
            
            return jsonify({
                'status': 'error',
                'message': 'Failed to update proxy configuration'
            }), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
