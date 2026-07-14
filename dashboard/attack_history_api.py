#!/usr/bin/env python3
"""
Attack History API Endpoints
Provides comprehensive attack history with filtering and export
"""

import sys
import json
import csv
import io
from pathlib import Path
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, Response

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_service import get_db_service

# Create blueprint
attack_history_bp = Blueprint('attack_history', __name__)
db = get_db_service()


@attack_history_bp.route('/api/attack-history/list', methods=['GET'])
@attack_history_bp.route('/api/attack-history', methods=['GET'])
def get_attack_history():
    """
    Get attack history with filtering and pagination
    
    Query parameters:
        - page: Page number (default: 1)
        - limit: Items per page (default: 50)
        - attack_type: Filter by attack type
        - ip: Filter by IP address
        - start_date: Filter by start date (ISO format)
        - end_date: Filter by end date (ISO format)
        - min_confidence: Minimum confidence score
        - sort: Sort field (default: timestamp)
        - order: Sort order (asc/desc, default: desc)
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)
        attack_type = request.args.get('attack_type')
        ip = request.args.get('ip')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        min_confidence = request.args.get('min_confidence', type=float)
        sort_field = request.args.get('sort', 'timestamp')
        sort_order = request.args.get('order', 'desc')
        
        # Build filters
        filters = {}
        if attack_type:
            filters['attack_type'] = attack_type
        if ip:
            filters['ip'] = ip
        if start_date:
            filters['start_date'] = start_date
        if end_date:
            filters['end_date'] = end_date
        
        # Calculate offset
        offset = (page - 1) * limit
        
        # Get attacks
        attacks = db.get_attacks(limit=limit, offset=offset, filters=filters)
        
        # Filter by confidence if specified
        if min_confidence is not None:
            attacks = [a for a in attacks if a.get('confidence', 0) >= min_confidence]
        
        # Get total count
        total = db.get_attack_count(filters=filters)
        
        # Parse JSON fields
        for attack in attacks:
            if attack.get('attack_types_json'):
                attack['attack_types'] = json.loads(attack['attack_types_json'])
            if attack.get('headers_json'):
                attack['headers'] = json.loads(attack['headers_json'])
            if attack.get('classification_json'):
                attack['classification'] = json.loads(attack['classification_json'])
        
        return jsonify({
            'attacks': attacks,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            },
            'filters': filters
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@attack_history_bp.route('/api/attack-history/export', methods=['GET'])
def export_attack_history():
    """
    Export attack history as CSV or JSON
    
    Query parameters:
        - format: Export format (csv/json, default: csv)
        - attack_type: Filter by attack type
        - ip: Filter by IP address
        - start_date: Filter by start date
        - end_date: Filter by end date
    """
    try:
        # Get query parameters
        export_format = request.args.get('format', 'csv')
        attack_type = request.args.get('attack_type')
        ip = request.args.get('ip')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build filters
        filters = {}
        if attack_type:
            filters['attack_type'] = attack_type
        if ip:
            filters['ip'] = ip
        if start_date:
            filters['start_date'] = start_date
        if end_date:
            filters['end_date'] = end_date
        
        # Get all attacks matching filters
        attacks = db.get_attacks(limit=10000, filters=filters)
        
        # Parse JSON fields
        for attack in attacks:
            if attack.get('attack_types_json'):
                attack['attack_types'] = json.loads(attack['attack_types_json'])
        
        if export_format == 'json':
            # Export as JSON
            output = json.dumps(attacks, indent=2)
            return Response(
                output,
                mimetype='application/json',
                headers={
                    'Content-Disposition': f'attachment; filename=attack_history_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                }
            )
        
        else:
            # Export as CSV
            output = io.StringIO()
            if attacks:
                fieldnames = ['id', 'timestamp', 'ip', 'attack_type', 'confidence',
                            'detection_method', 'routed_to', 'target_site', 'url']
                writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(attacks)
            
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename=attack_history_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
                }
            )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@attack_history_bp.route('/api/attack-history/stats', methods=['GET'])
def get_attack_history_stats():
    """Get attack history statistics"""
    try:
        stats = db.get_attack_stats()
        
        # Add time-based stats
        with db.get_connection() as conn:
            # Attacks by day (last 30 days)
            cursor = conn.execute("""
                SELECT DATE(timestamp) as date, COUNT(*) as count
                FROM attacks
                WHERE timestamp >= datetime('now', '-30 days')
                GROUP BY DATE(timestamp)
                ORDER BY date
            """)
            stats['by_day'] = {row['date']: row['count'] for row in cursor.fetchall()}
            
            # Attacks by detection method
            cursor = conn.execute("""
                SELECT detection_method, COUNT(*) as count
                FROM attacks
                GROUP BY detection_method
            """)
            stats['by_detection_method'] = {row['detection_method']: row['count'] 
                                           for row in cursor.fetchall()}
            
            # Attacks by target site
            cursor = conn.execute("""
                SELECT target_site, COUNT(*) as count
                FROM attacks
                WHERE target_site IS NOT NULL
                GROUP BY target_site
                ORDER BY count DESC
                LIMIT 10
            """)
            stats['by_target'] = {row['target_site']: row['count'] 
                                 for row in cursor.fetchall()}
        
        return jsonify(stats)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@attack_history_bp.route('/api/attack-history/<int:attack_id>', methods=['GET'])
def get_attack_detail(attack_id: int):
    """Get detailed information about a specific attack"""
    try:
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM attacks WHERE id = ?", (attack_id,))
            attack = cursor.fetchone()
            
            if not attack:
                return jsonify({'error': 'Attack not found'}), 404
            
            attack_dict = dict(attack)
            
            # Parse JSON fields
            if attack_dict.get('attack_types_json'):
                attack_dict['attack_types'] = json.loads(attack_dict['attack_types_json'])
            if attack_dict.get('headers_json'):
                attack_dict['headers'] = json.loads(attack_dict['headers_json'])
            if attack_dict.get('classification_json'):
                attack_dict['classification'] = json.loads(attack_dict['classification_json'])
            
            # Get related attacker profile
            if attack_dict.get('ip'):
                profile = db.get_attacker_profile_by_ip(attack_dict['ip'])
                if profile:
                    attack_dict['attacker_profile'] = profile
            
            # Get related honeypot events
            cursor = conn.execute("""
                SELECT * FROM honeypot_events
                WHERE ip = ? AND timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp
                LIMIT 50
            """, (
                attack_dict['ip'],
                attack_dict['timestamp'],
                (datetime.fromisoformat(attack_dict['timestamp']) + timedelta(hours=1)).isoformat()
            ))
            attack_dict['related_events'] = [dict(row) for row in cursor.fetchall()]
            
            return jsonify(attack_dict)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@attack_history_bp.route('/api/attack-history/timeline', methods=['GET'])
def get_attack_timeline():
    """
    Get attack timeline for visualization
    
    Query parameters:
        - days: Number of days to include (default: 7)
        - granularity: hour/day (default: hour)
    """
    try:
        days = request.args.get('days', 7, type=int)
        granularity = request.args.get('granularity', 'hour')
        
        with db.get_connection() as conn:
            if granularity == 'hour':
                cursor = conn.execute("""
                    SELECT 
                        strftime('%Y-%m-%d %H:00:00', timestamp) as time_bucket,
                        COUNT(*) as count,
                        attack_type
                    FROM attacks
                    WHERE timestamp >= datetime('now', ? || ' days')
                    GROUP BY time_bucket, attack_type
                    ORDER BY time_bucket
                """, (f'-{days}',))
            else:
                cursor = conn.execute("""
                    SELECT 
                        DATE(timestamp) as time_bucket,
                        COUNT(*) as count,
                        attack_type
                    FROM attacks
                    WHERE timestamp >= datetime('now', ? || ' days')
                    GROUP BY time_bucket, attack_type
                    ORDER BY time_bucket
                """, (f'-{days}',))
            
            timeline = {}
            for row in cursor.fetchall():
                time_bucket = row['time_bucket']
                attack_type = row['attack_type']
                count = row['count']
                
                if time_bucket not in timeline:
                    timeline[time_bucket] = {}
                timeline[time_bucket][attack_type] = count
            
            return jsonify({
                'timeline': timeline,
                'granularity': granularity,
                'days': days
            })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
