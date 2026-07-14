import json
import hashlib
import math
import statistics
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from flask import Blueprint, request, jsonify
import logging
import socket
import struct

# Try to import geoip2 for geolocation
try:
    import geoip2.database
    import geoip2.errors
    GEOIP_AVAILABLE = True
except ImportError:
    GEOIP_AVAILABLE = False

logger = logging.getLogger('fingerprint')

# CONFIGURATION

FINGERPRINT_LOG = Path(__file__).parent.parent / 'logs' / 'fingerprints.jsonl'
FINGERPRINT_LOG.parent.mkdir(parents=True, exist_ok=True)

# GeoIP Database Path (optional - download from MaxMind)
GEOIP_DB_PATH = Path(__file__).parent.parent / 'data' / 'GeoLite2-City.mmdb'

# In-memory fingerprint database

fingerprint_db = defaultdict(lambda: {
    'profiles': [],
    'first_seen': None,
    'last_seen': None,
    'ips_used': [],  # (#9) list instead of set for JSON serialization
    'cluster_id': None,
    'ja3_hashes': [],  # JA3 TLS fingerprints
    'geolocations': [],  # Geographic locations
})

# Cluster assignments

clusters = {}
next_cluster_id = 0

# JA3 FINGERPRINTING

def compute_ja3_hash(tls_data):
    """
    Compute JA3 TLS fingerprint from TLS ClientHello data.
    JA3 = MD5(SSLVersion,Ciphers,Extensions,EllipticCurves,EllipticCurvePointFormats)
    """
    if not tls_data:
        return None
    
    try:
        ssl_version = str(tls_data.get('ssl_version', ''))
        ciphers = ','.join(map(str, tls_data.get('ciphers', [])))
        extensions = ','.join(map(str, tls_data.get('extensions', [])))
        elliptic_curves = ','.join(map(str, tls_data.get('elliptic_curves', [])))
        ec_point_formats = ','.join(map(str, tls_data.get('ec_point_formats', [])))
        
        ja3_string = f"{ssl_version},{ciphers},{extensions},{elliptic_curves},{ec_point_formats}"
        return hashlib.md5(ja3_string.encode()).hexdigest()
    except Exception as e:
        logger.warning(f"JA3 computation failed: {e}")
        return None

def extract_ja3_from_request(request_obj):
    """
    Extract JA3 fingerprint from Flask request headers.
    Note: This is a simplified version. Full JA3 requires TLS layer access.
    """
    # In production, you'd need to capture TLS ClientHello at the network layer
    # For now, we'll create a pseudo-JA3 from available headers
    try:
        user_agent = request_obj.headers.get('User-Agent', '')
        accept = request_obj.headers.get('Accept', '')
        accept_encoding = request_obj.headers.get('Accept-Encoding', '')
        accept_language = request_obj.headers.get('Accept-Language', '')
        
        # Create a pseudo-JA3 hash from HTTP headers
        header_string = f"{user_agent}|{accept}|{accept_encoding}|{accept_language}"
        return hashlib.md5(header_string.encode()).hexdigest()[:16]
    except Exception as e:
        logger.warning(f"JA3 extraction failed: {e}")
        return None

# GEOLOCATION

def get_geolocation(ip_address):
    """
    Get geographic location from IP address using GeoIP2 database.
    Returns dict with country, city, lat, lon, or None if unavailable.
    """
    if not GEOIP_AVAILABLE or not GEOIP_DB_PATH.exists():
        return None
    
    try:
        with geoip2.database.Reader(str(GEOIP_DB_PATH)) as reader:
            response = reader.city(ip_address)
            return {
                'country': response.country.name or 'Unknown',
                'country_code': response.country.iso_code or 'XX',
                'city': response.city.name or 'Unknown',
                'latitude': response.location.latitude,
                'longitude': response.location.longitude,
                'timezone': response.location.time_zone or 'Unknown',
            }
    except (geoip2.errors.AddressNotFoundError, Exception) as e:
        logger.debug(f"Geolocation lookup failed for {ip_address}: {e}")
        return None

# FINGERPRINT PROCESSING

def compute_behavioral_hash(fingerprint_data):
    """
    Compute a stable behavioral hash from fingerprint data.
    Unlike IP addresses, this hash remains similar even across VPN/Tor changes.
    """
    stable_features = {
        'screen_resolution': fingerprint_data.get('screen', {}).get('resolution', ''),
        'timezone_offset': fingerprint_data.get('timezone_offset', 0),
        'language': fingerprint_data.get('language', ''),
        'platform': fingerprint_data.get('platform', ''),
        'color_depth': fingerprint_data.get('screen', {}).get('colorDepth', 0),
        'touch_support': fingerprint_data.get('touch_support', False),
        'canvas_hash': fingerprint_data.get('canvas_hash', ''),
        'webgl_hash': fingerprint_data.get('webgl_hash', ''),
        'fonts_hash': fingerprint_data.get('fonts_hash', ''),
    }
    
    hash_input = json.dumps(stable_features, sort_keys=True)
    return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

def extract_typing_features(keystroke_intervals):
    """Extract statistical features from keystroke timing data."""
    if not keystroke_intervals or len(keystroke_intervals) < 2:
        return {
            'typing_speed_mean': 0,
            'typing_speed_std': 0,
            'typing_speed_median': 0,
            'typing_rhythm_score': 0,
        }
    
    intervals = [max(0, min(i, 5000)) for i in keystroke_intervals]  # clamp
    
    return {
        'typing_speed_mean': statistics.mean(intervals),
        'typing_speed_std': statistics.stdev(intervals) if len(intervals) > 1 else 0,
        'typing_speed_median': statistics.median(intervals),
        'typing_rhythm_score': _rhythm_score(intervals),
    }

def _rhythm_score(intervals):
    """Calculate how rhythmic/regular the typing pattern is (0-1)."""
    if len(intervals) < 2:
        return 0
    mean = statistics.mean(intervals)
    if mean == 0:
        return 0
    cv = statistics.stdev(intervals) / mean  # coefficient of variation
    return max(0, 1 - cv)  # Higher = more regular typing

def extract_mouse_features(mouse_data):
    """Extract features from mouse movement data."""
    if not mouse_data or len(mouse_data) < 2:
        return {
            'mouse_velocity_mean': 0,
            'mouse_velocity_std': 0,
            'mouse_acceleration_mean': 0,
            'mouse_linearity': 0,
            'mouse_sample_count': 0,
        }
    
    velocities = []
    accelerations = []
    total_distance = 0
    
    for i in range(1, len(mouse_data)):
        p1 = mouse_data[i - 1]
        p2 = mouse_data[i]
        
        dx = p2.get('x', 0) - p1.get('x', 0)
        dy = p2.get('y', 0) - p1.get('y', 0)
        dt = max(p2.get('t', 0) - p1.get('t', 0), 1)  # avoid div by 0
        
        distance = math.sqrt(dx * dx + dy * dy)
        velocity = distance / dt * 1000  # pixels per second
        total_distance += distance
        velocities.append(velocity)
    
    for i in range(1, len(velocities)):
        accelerations.append(abs(velocities[i] - velocities[i - 1]))
    
    # Linearity: straight-line distance vs total path distance

    if len(mouse_data) >= 2 and total_distance > 0:
        start = mouse_data[0]
        end = mouse_data[-1]
        straight_dist = math.sqrt(
            (end.get('x', 0) - start.get('x', 0)) ** 2 +
            (end.get('y', 0) - start.get('y', 0)) ** 2
        )
        linearity = straight_dist / total_distance
    else:
        linearity = 0
    
    return {
        'mouse_velocity_mean': statistics.mean(velocities) if velocities else 0,
        'mouse_velocity_std': statistics.stdev(velocities) if len(velocities) > 1 else 0,
        'mouse_acceleration_mean': statistics.mean(accelerations) if accelerations else 0,
        'mouse_linearity': linearity,
        'mouse_sample_count': len(mouse_data),
    }

def process_fingerprint(raw_data, ip_address, user_agent, request_obj=None):
    """
    Process a raw fingerprint submission and create a behavioral profile.
    
    Args:
        raw_data: dict from the client-side JS collector
        ip_address: attacker's IP
        user_agent: attacker's user-agent string
        request_obj: Flask request object for JA3 extraction
    
    Returns:
        dict: processed fingerprint profile
    """
    behavioral_hash = compute_behavioral_hash(raw_data)
    
    typing_features = extract_typing_features(
        raw_data.get('keystroke_intervals', [])
    )
    
    mouse_features = extract_mouse_features(
        raw_data.get('mouse_movements', [])
    )
    
    # Extract JA3 fingerprint
    ja3_hash = None
    if request_obj:
        ja3_hash = extract_ja3_from_request(request_obj)
    
    # Get geolocation
    geolocation = get_geolocation(ip_address)
    
    profile = {
        'timestamp': datetime.now().isoformat(),
        'behavioral_hash': behavioral_hash,
        'ip_address': ip_address,
        'user_agent': user_agent,
        
        # JA3 TLS Fingerprint
        'ja3_hash': ja3_hash,
        
        # Geolocation
        'geolocation': geolocation,
        
        # Browser fingerprint

        'browser': {
            'canvas_hash': raw_data.get('canvas_hash', ''),
            'webgl_hash': raw_data.get('webgl_hash', ''),
            'fonts_hash': raw_data.get('fonts_hash', ''),
            'screen_resolution': raw_data.get('screen', {}).get('resolution', ''),
            'color_depth': raw_data.get('screen', {}).get('colorDepth', 0),
            'timezone_offset': raw_data.get('timezone_offset', 0),
            'language': raw_data.get('language', ''),
            'platform': raw_data.get('platform', ''),
            'touch_support': raw_data.get('touch_support', False),
            'do_not_track': raw_data.get('do_not_track', None),
            'plugins_count': raw_data.get('plugins_count', 0),
        },
        
        # Behavioral features

        'typing': typing_features,
        'mouse': mouse_features,
        
        # Request metadata

        'request_intervals': raw_data.get('request_intervals', []),
        'pages_visited': raw_data.get('pages_visited', []),
        'time_on_page': raw_data.get('time_on_page', 0),
        'scroll_depth': raw_data.get('scroll_depth', 0),
        'form_interactions': raw_data.get('form_interactions', 0),
    }
    
    # Store in memory and on disk

    _store_profile(behavioral_hash, profile)
    
    # Run advanced clustering

    cluster_id = _assign_cluster(behavioral_hash, profile)
    profile['cluster_id'] = cluster_id
    
    return profile

def _store_profile(behavioral_hash, profile):
    """Store a fingerprint profile in the database."""
    entry = fingerprint_db[behavioral_hash]
    
    if entry['first_seen'] is None:
        entry['first_seen'] = profile['timestamp']
    entry['last_seen'] = profile['timestamp']
    if profile['ip_address'] not in entry['ips_used']:  # (#9) dedup list
        entry['ips_used'].append(profile['ip_address'])
    
    # Store JA3 hashes
    if profile.get('ja3_hash') and profile['ja3_hash'] not in entry['ja3_hashes']:
        entry['ja3_hashes'].append(profile['ja3_hash'])
    
    # Store geolocations
    if profile.get('geolocation'):
        geo_key = f"{profile['geolocation'].get('country_code', 'XX')}:{profile['geolocation'].get('city', 'Unknown')}"
        if geo_key not in [f"{g.get('country_code', 'XX')}:{g.get('city', 'Unknown')}" for g in entry['geolocations']]:
            entry['geolocations'].append(profile['geolocation'])
    
    entry['profiles'].append(profile)
    
    # Keep only last 50 profiles per hash

    if len(entry['profiles']) > 50:
        entry['profiles'] = entry['profiles'][-50:]
    
    # Persist to disk

    with open(FINGERPRINT_LOG, 'a') as f:
        disk_profile = {**profile}
        f.write(json.dumps(disk_profile) + '\n')
    
    logger.info(
        f"🔍 Fingerprint [{behavioral_hash}] from {profile['ip_address']} | "
        f"IPs used: {len(entry['ips_used'])} | "
        f"Profiles: {len(entry['profiles'])} | "
        f"JA3: {profile.get('ja3_hash', 'N/A')[:8] if profile.get('ja3_hash') else 'N/A'}... | "
        f"Location: {(profile.get('geolocation') or {}).get('city', 'Unknown')}, {(profile.get('geolocation') or {}).get('country', 'Unknown')}"
    )

def _assign_cluster(behavioral_hash, profile):
    """
    Advanced clustering using DBSCAN-inspired approach with multiple features.
    Groups attackers with similar browser + behavioral + network fingerprints.
    Considers JA3, geolocation, and behavioral patterns.
    """
    global next_cluster_id
    
    # Feature vector for comparison (enhanced with JA3 and geo)

    features = _profile_to_vector(profile)
    
    # Check existing clusters for a match

    best_cluster = None
    best_distance = float('inf')
    best_similarity_score = 0
    
    for cluster_id, cluster_data in clusters.items():
        centroid = cluster_data['centroid']
        distance = _euclidean_distance(features, centroid)
        
        # Calculate additional similarity metrics
        ja3_match = _ja3_similarity(profile, cluster_data)
        geo_match = _geo_similarity(profile, cluster_data)
        
        # Combined similarity score (weighted)
        similarity_score = (
            (1.0 - min(distance, 1.0)) * 0.5 +  # Behavioral similarity (50%)
            ja3_match * 0.3 +                     # JA3 similarity (30%)
            geo_match * 0.2                       # Geographic similarity (20%)
        )
        
        if similarity_score > best_similarity_score:
            best_similarity_score = similarity_score
            best_distance = distance
            best_cluster = cluster_id
    
    # Threshold for "same attacker" — tuned for multi-factor similarity
    # Higher threshold = stricter clustering (fewer, more precise clusters)
    SIMILARITY_THRESHOLD = 0.65  # 65% overall similarity required
    
    if best_cluster is not None and best_similarity_score >= SIMILARITY_THRESHOLD:
        # Update cluster centroid (running average)

        cluster = clusters[best_cluster]
        n = cluster['member_count']
        cluster['centroid'] = [
            (c * n + f) / (n + 1)
            for c, f in zip(cluster['centroid'], features)
        ]
        cluster['member_count'] += 1
        if behavioral_hash not in cluster['members']:  # (#9) dedup list
            cluster['members'].append(behavioral_hash)
        cluster['last_seen'] = profile['timestamp']
        
        # Update cluster metadata
        if profile.get('ja3_hash') and profile['ja3_hash'] not in cluster.get('ja3_hashes', []):
            cluster.setdefault('ja3_hashes', []).append(profile['ja3_hash'])
        if profile.get('geolocation'):
            cluster.setdefault('geolocations', []).append(profile['geolocation'])
        
        fingerprint_db[behavioral_hash]['cluster_id'] = best_cluster
        return best_cluster
    else:
        # Create new cluster

        cluster_id = next_cluster_id
        next_cluster_id += 1
        
        clusters[cluster_id] = {
            'centroid': features,
            'member_count': 1,
            'members': [behavioral_hash],  # (#9) list instead of set
            'first_seen': profile['timestamp'],
            'last_seen': profile['timestamp'],
            'ja3_hashes': [profile.get('ja3_hash')] if profile.get('ja3_hash') else [],
            'geolocations': [profile.get('geolocation')] if profile.get('geolocation') else [],
        }
        
        fingerprint_db[behavioral_hash]['cluster_id'] = cluster_id
        return cluster_id

def _ja3_similarity(profile, cluster_data):
    """
    Calculate JA3 fingerprint similarity between profile and cluster.
    Returns 1.0 if JA3 matches, 0.0 if no match or unavailable.
    """
    profile_ja3 = profile.get('ja3_hash')
    cluster_ja3s = cluster_data.get('ja3_hashes', [])
    
    if not profile_ja3 or not cluster_ja3s:
        return 0.5  # Neutral score if JA3 unavailable
    
    return 1.0 if profile_ja3 in cluster_ja3s else 0.0

def _geo_similarity(profile, cluster_data):
    """
    Calculate geographic similarity between profile and cluster.
    Returns 1.0 for same country, 0.5 for same region, 0.0 for different.
    """
    profile_geo = profile.get('geolocation')
    cluster_geos = cluster_data.get('geolocations', [])
    
    if not profile_geo or not cluster_geos:
        return 0.5  # Neutral score if geolocation unavailable
    
    profile_country = profile_geo.get('country_code', 'XX')
    
    # Check if same country exists in cluster
    for geo in cluster_geos:
        if geo.get('country_code') == profile_country:
            # Same city = perfect match
            if geo.get('city') == profile_geo.get('city'):
                return 1.0
            # Same country = partial match
            return 0.7
    
    return 0.0  # Different country

def _profile_to_vector(profile):
    """Convert a profile to a normalized feature vector for clustering."""
    return [
        profile['browser'].get('timezone_offset', 0) / 720.0,  # normalize to [-1, 1]
        profile['browser'].get('color_depth', 24) / 32.0,
        1.0 if profile['browser'].get('touch_support', False) else 0.0,
        profile['typing'].get('typing_speed_mean', 0) / 500.0,  # normalize
        profile['typing'].get('typing_rhythm_score', 0),
        profile['mouse'].get('mouse_velocity_mean', 0) / 2000.0,  # normalize
        profile['mouse'].get('mouse_linearity', 0),
        min(profile.get('time_on_page', 0) / 300.0, 1.0),  # cap at 5 min
    ]

def _euclidean_distance(v1, v2):
    """Compute Euclidean distance between two vectors."""
    if len(v1) != len(v2):
        return float('inf')
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))

# FLASK BLUEPRINT — Fingerprinting API

fingerprint_bp = Blueprint('fingerprint', __name__)

@fingerprint_bp.route('/api/fingerprint', methods=['POST'])
def receive_fingerprint():
    """Receive fingerprint telemetry from the client-side JS collector."""
    try:
        raw_data = request.get_json(silent=True)
        if not raw_data:
            return jsonify({'status': 'error', 'message': 'No data'}), 400
        
        profile = process_fingerprint(
            raw_data=raw_data,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            request_obj=request,  # Pass request for JA3 extraction
        )
        
        return jsonify({
            'status': 'ok',
            'behavioral_hash': profile['behavioral_hash'],
            'cluster_id': profile['cluster_id'],
            'ja3_hash': profile.get('ja3_hash'),
            'geolocation': profile.get('geolocation'),
        })
    except Exception as e:
        logger.error(f"Fingerprint processing error: {e}")
        return jsonify({'status': 'error'}), 500

@fingerprint_bp.route('/api/fingerprint-stats')
def fingerprint_stats():
    """Return fingerprint statistics for the dashboard."""
    profiles = []
    for bhash, data in fingerprint_db.items():
        # Get most recent geolocation
        recent_geo = None
        if data['profiles']:
            for profile in reversed(data['profiles']):
                if profile.get('geolocation'):
                    recent_geo = profile['geolocation']
                    break
        
        profiles.append({
            'behavioral_hash': bhash,
            'first_seen': data['first_seen'],
            'last_seen': data['last_seen'],
            'ips_used': data['ips_used'],  # (#9) already a list now
            'ip_count': len(data['ips_used']),
            'profile_count': len(data['profiles']),
            'cluster_id': data['cluster_id'],
            'ja3_hashes': data.get('ja3_hashes', []),
            'ja3_count': len(data.get('ja3_hashes', [])),
            'geolocation': recent_geo,
            'geo_countries': list(set(g.get('country', 'Unknown') for g in data.get('geolocations', []) if g)),
        })
    
    cluster_info = []
    for cid, cdata in clusters.items():
        # Aggregate cluster geolocation data
        cluster_countries = list(set(g.get('country', 'Unknown') for g in cdata.get('geolocations', []) if g))
        cluster_cities = list(set(f"{g.get('city', 'Unknown')}, {g.get('country_code', 'XX')}" for g in cdata.get('geolocations', []) if g))
        
        cluster_info.append({
            'cluster_id': cid,
            'member_count': cdata['member_count'],
            'unique_fingerprints': len(cdata['members']),
            'first_seen': cdata['first_seen'],
            'last_seen': cdata['last_seen'],
            'ja3_hashes': cdata.get('ja3_hashes', []),
            'ja3_diversity': len(set(cdata.get('ja3_hashes', []))),
            'countries': cluster_countries,
            'cities': cluster_cities[:5],  # Top 5 cities
        })
    
    return jsonify({
        'total_fingerprints': len(fingerprint_db),
        'total_clusters': len(clusters),
        'profiles': profiles,
        'clusters': cluster_info,
        'timestamp': datetime.now().isoformat(),
        'geoip_available': GEOIP_AVAILABLE and GEOIP_DB_PATH.exists(),
    })
