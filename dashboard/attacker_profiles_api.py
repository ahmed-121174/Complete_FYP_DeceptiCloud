#!/usr/bin/env python3
"""
Attacker Profiles API Endpoints
Provides attacker profiling and clustering functionality
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from flask import Blueprint, request, jsonify
import numpy as np
from sklearn.cluster import DBSCAN
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_service import get_db_service

# Create blueprint
attacker_profiles_bp = Blueprint('attacker_profiles', __name__)
db = get_db_service()


@attacker_profiles_bp.route('/api/attacker-profiles/list', methods=['GET'])
@attacker_profiles_bp.route('/api/attacker-profiles', methods=['GET'])
def get_attacker_profiles():
    """
    Get all attacker profiles with optional filtering
    
    Query parameters:
        - limit: Number of profiles to return (default: 100)
        - min_attacks: Minimum attack count
        - cluster_id: Filter by cluster ID
        - sort: Sort field (default: last_seen)
        - order: Sort order (asc/desc, default: desc)
    """
    try:
        limit = request.args.get('limit', 100, type=int)
        min_attacks = request.args.get('min_attacks', type=int)
        cluster_id = request.args.get('cluster_id', type=int)
        
        profiles = db.get_attacker_profiles(limit=limit)
        
        # Parse JSON fields
        for profile in profiles:
            if profile.get('attack_types_json'):
                profile['attack_types'] = json.loads(profile['attack_types_json'])
            if profile.get('user_agents_json'):
                profile['user_agents'] = json.loads(profile['user_agents_json'])
            if profile.get('tools_detected_json'):
                profile['tools_detected'] = json.loads(profile['tools_detected_json'])
            if profile.get('geolocation_json'):
                profile['geolocation'] = json.loads(profile['geolocation_json'])
        
        # Apply filters
        if min_attacks:
            profiles = [p for p in profiles if p.get('attack_count', 0) >= min_attacks]
        
        if cluster_id is not None:
            profiles = [p for p in profiles if p.get('cluster_id') == cluster_id]
        
        # Get cluster count
        with db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT cluster_id) as count
                FROM attacker_profiles
                WHERE cluster_id IS NOT NULL AND cluster_id >= 0
            """)
            cluster_count = cursor.fetchone()['count']
            
            # Get cluster distribution
            cursor = conn.execute("""
                SELECT cluster_id, COUNT(*) as count
                FROM attacker_profiles
                WHERE cluster_id IS NOT NULL AND cluster_id >= 0
                GROUP BY cluster_id
            """)
            clusters = {str(row['cluster_id']): row['count'] for row in cursor.fetchall()}
        
        return jsonify({
            'profiles': profiles,
            'total': len(profiles),
            'cluster_count': cluster_count,
            'clusters': clusters
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@attacker_profiles_bp.route('/api/attacker-profiles/<ip>', methods=['GET'])
def get_attacker_profile(ip: str):
    """Get detailed profile for a specific attacker"""
    try:
        profile = db.get_attacker_profile_by_ip(ip)
        
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404
        
        # Parse JSON fields
        if profile.get('attack_types_json'):
            profile['attack_types'] = json.loads(profile['attack_types_json'])
        if profile.get('user_agents_json'):
            profile['user_agents'] = json.loads(profile['user_agents_json'])
        if profile.get('tools_detected_json'):
            profile['tools_detected'] = json.loads(profile['tools_detected_json'])
        if profile.get('geolocation_json'):
            profile['geolocation'] = json.loads(profile['geolocation_json'])
        
        # Get attack history for this IP
        attacks = db.get_attacks(limit=1000, filters={'ip': ip})
        profile['attack_history'] = attacks
        
        # Get sessions
        with db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM sessions
                WHERE ip = ?
                ORDER BY start_time DESC
                LIMIT 50
            """, (ip,))
            profile['sessions'] = [dict(row) for row in cursor.fetchall()]
            
            # Get honeypot events
            cursor = conn.execute("""
                SELECT * FROM honeypot_events
                WHERE ip = ?
                ORDER BY timestamp DESC
                LIMIT 100
            """, (ip,))
            profile['honeypot_events'] = [dict(row) for row in cursor.fetchall()]
        
        # Get related attackers (same cluster)
        if profile.get('cluster_id') is not None:
            with db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT ip, attack_count, threat_score, last_seen
                    FROM attacker_profiles
                    WHERE cluster_id = ? AND ip != ?
                    ORDER BY attack_count DESC
                    LIMIT 10
                """, (profile['cluster_id'], ip))
                profile['related_attackers'] = [dict(row) for row in cursor.fetchall()]
        
        return jsonify(profile)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@attacker_profiles_bp.route('/api/attacker-profiles/clustering', methods=['POST'])
def perform_clustering():
    """
    Perform DBSCAN clustering on attacker profiles
    
    Request body:
        - eps: DBSCAN epsilon parameter (default: 0.5)
        - min_samples: Minimum samples per cluster (default: 2)
        - features: Features to use for clustering (default: all)
    """
    try:
        data = request.get_json() or {}
        eps = data.get('eps', 0.5)
        min_samples = data.get('min_samples', 2)
        
        # Get all profiles
        profiles = db.get_attacker_profiles(limit=1000)
        
        if len(profiles) < min_samples:
            return jsonify({
                'error': 'Not enough profiles for clustering',
                'profiles_count': len(profiles)
            }), 400
        
        # Extract features for clustering
        feature_vectors = []
        profile_ips = []
        
        for profile in profiles:
            # Parse JSON fields
            attack_types = json.loads(profile.get('attack_types_json', '[]'))
            user_agents = json.loads(profile.get('user_agents_json', '[]'))
            
            # Create feature vector
            features = [
                profile.get('attack_count', 0),
                profile.get('threat_score', 0),
                len(attack_types),
                len(user_agents),
                # Add more features as needed
            ]
            
            feature_vectors.append(features)
            profile_ips.append(profile['ip'])
        
        # Normalize features
        feature_vectors = np.array(feature_vectors)
        feature_vectors = (feature_vectors - feature_vectors.mean(axis=0)) / (feature_vectors.std(axis=0) + 1e-10)
        
        # Perform DBSCAN clustering
        clustering = DBSCAN(eps=eps, min_samples=min_samples)
        cluster_labels = clustering.fit_predict(feature_vectors)
        
        # Update database with cluster assignments
        cluster_stats = defaultdict(int)
        for ip, cluster_id in zip(profile_ips, cluster_labels):
            cluster_id = int(cluster_id)
            cluster_stats[cluster_id] += 1
            
            with db.get_connection() as conn:
                conn.execute("""
                    UPDATE attacker_profiles
                    SET cluster_id = ?, updated_at = ?
                    WHERE ip = ?
                """, (cluster_id if cluster_id >= 0 else None, datetime.now().isoformat(), ip))
                conn.commit()
        
        # Prepare response
        clusters = []
        for cluster_id, count in cluster_stats.items():
            if cluster_id >= 0:  # Exclude noise points (-1)
                clusters.append({
                    'cluster_id': cluster_id,
                    'size': count
                })
        
        return jsonify({
            'clusters': sorted(clusters, key=lambda x: x['size'], reverse=True),
            'total_clusters': len([c for c in clusters if c['cluster_id'] >= 0]),
            'noise_points': cluster_stats.get(-1, 0),
            'total_profiles': len(profiles),
            'parameters': {
                'eps': eps,
                'min_samples': min_samples
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@attacker_profiles_bp.route('/api/attacker-profiles/clusters', methods=['GET'])
def get_clusters():
    """Get cluster statistics"""
    try:
        stats = db.get_cluster_stats()
        
        # Get detailed cluster information
        clusters = []
        for cluster_info in stats.get('clusters', []):
            cluster_id = cluster_info['id']
            
            with db.get_connection() as conn:
                # Get cluster members
                cursor = conn.execute("""
                    SELECT ip, attack_count, threat_score, last_seen
                    FROM attacker_profiles
                    WHERE cluster_id = ?
                    ORDER BY attack_count DESC
                """, (cluster_id,))
                members = [dict(row) for row in cursor.fetchall()]
                
                # Get common attack types
                cursor = conn.execute("""
                    SELECT attack_types_json
                    FROM attacker_profiles
                    WHERE cluster_id = ?
                """, (cluster_id,))
                
                all_attack_types = []
                for row in cursor.fetchall():
                    types = json.loads(row['attack_types_json'] or '[]')
                    all_attack_types.extend(types)
                
                # Count attack type frequency
                attack_type_counts = defaultdict(int)
                for attack_type in all_attack_types:
                    attack_type_counts[attack_type] += 1
                
                common_attack_types = sorted(
                    attack_type_counts.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
                
                clusters.append({
                    'cluster_id': cluster_id,
                    'size': len(members),
                    'members': members[:10],  # Top 10 members
                    'common_attack_types': [{'type': t, 'count': c} for t, c in common_attack_types],
                    'avg_threat_score': sum(m['threat_score'] for m in members) / len(members) if members else 0
                })
        
        return jsonify({
            'clusters': clusters,
            'total_clusters': len(clusters),
            'total_profiles': stats['total_profiles']
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@attacker_profiles_bp.route('/api/attacker-profiles/stats', methods=['GET'])
def get_profile_stats():
    """Get attacker profile statistics"""
    try:
        with db.get_connection() as conn:
            # Total profiles
            cursor = conn.execute("SELECT COUNT(*) as count FROM attacker_profiles")
            total = cursor.fetchone()['count']
            
            # Profiles by threat score range
            cursor = conn.execute("""
                SELECT 
                    CASE 
                        WHEN threat_score >= 0.9 THEN 'critical'
                        WHEN threat_score >= 0.7 THEN 'high'
                        WHEN threat_score >= 0.5 THEN 'medium'
                        ELSE 'low'
                    END as threat_level,
                    COUNT(*) as count
                FROM attacker_profiles
                GROUP BY threat_level
            """)
            by_threat_level = {row['threat_level']: row['count'] for row in cursor.fetchall()}
            
            # Top attackers
            cursor = conn.execute("""
                SELECT ip, attack_count, threat_score, last_seen
                FROM attacker_profiles
                ORDER BY attack_count DESC
                LIMIT 10
            """)
            top_attackers = [dict(row) for row in cursor.fetchall()]
            
            # Recent profiles
            cursor = conn.execute("""
                SELECT ip, attack_count, threat_score, first_seen
                FROM attacker_profiles
                ORDER BY first_seen DESC
                LIMIT 10
            """)
            recent_profiles = [dict(row) for row in cursor.fetchall()]
        
        return jsonify({
            'total': total,
            'by_threat_level': by_threat_level,
            'top_attackers': top_attackers,
            'recent_profiles': recent_profiles
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@attacker_profiles_bp.route('/api/attacker-profiles/export', methods=['GET'])
def export_attacker_profiles():
    """
    Export attacker profiles as CSV or JSON
    
    Query parameters:
        - format: Export format (csv/json, default: csv)
        - min_attacks: Minimum attack count filter
        - cluster_id: Filter by cluster ID
    """
    import csv
    import io
    from flask import Response
    
    try:
        # Get query parameters
        export_format = request.args.get('format', 'csv')
        min_attacks = request.args.get('min_attacks', type=int)
        cluster_id = request.args.get('cluster_id', type=int)
        
        # Get all profiles
        profiles = db.get_attacker_profiles(limit=10000)
        
        # Parse JSON fields
        for profile in profiles:
            if profile.get('attack_types_json'):
                profile['attack_types'] = json.loads(profile['attack_types_json'])
            if profile.get('user_agents_json'):
                profile['user_agents'] = json.loads(profile['user_agents_json'])
            if profile.get('tools_detected_json'):
                profile['tools_detected'] = json.loads(profile['tools_detected_json'])
        
        # Apply filters
        if min_attacks:
            profiles = [p for p in profiles if p.get('attack_count', 0) >= min_attacks]
        
        if cluster_id is not None:
            profiles = [p for p in profiles if p.get('cluster_id') == cluster_id]
        
        if export_format == 'json':
            # Export as JSON
            output = json.dumps(profiles, indent=2)
            return Response(
                output,
                mimetype='application/json',
                headers={
                    'Content-Disposition': f'attachment; filename=attacker_profiles_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                }
            )
        
        else:
            # Export as CSV
            output = io.StringIO()
            if profiles:
                fieldnames = ['ip', 'first_seen', 'last_seen', 'attack_count', 
                            'threat_score', 'cluster_id', 'behavioral_hash']
                writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                
                # Flatten attack_types for CSV
                for profile in profiles:
                    profile_copy = profile.copy()
                    if isinstance(profile_copy.get('attack_types'), list):
                        profile_copy['attack_types'] = ', '.join(profile_copy['attack_types'])
                    writer.writerow(profile_copy)
            
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename=attacker_profiles_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
                }
            )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
