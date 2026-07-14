"""
Behavioral Monitor - Real-time Attacker Detection on Real Sites

Continuously monitors user behavior on REAL sites and compares it with
known attacker fingerprints from honeypot interactions. If a user's behavior
matches known attackers with ≥75% similarity, their session is terminated.

This protects real sites from attackers who may have bypassed initial detection.
"""

import logging
import hashlib
import json
from datetime import datetime
from typing import Dict, Optional, Tuple

logger = logging.getLogger('behavioral_monitor')

# Import fingerprint database from behavioral_fingerprint module
try:
    from honeypot.behavioral_fingerprint import (
        fingerprint_db,
        compute_behavioral_hash,
        _profile_to_vector,
        _euclidean_distance,
        extract_ja3_from_request,
        get_geolocation,
    )
    FINGERPRINT_MODULE_AVAILABLE = True
except ImportError:
    FINGERPRINT_MODULE_AVAILABLE = False
    logger.warning("⚠️  Fingerprint module not available - behavioral monitoring disabled")

# Similarity threshold for session termination
TERMINATION_THRESHOLD = 0.50  # 50% similarity

# Track monitored sessions on real sites
monitored_sessions = {}  # {session_id: {ip, behavioral_hash, similarity_score, first_seen, last_check}}

def compute_realtime_behavioral_hash(request_data: dict) -> str:
    """
    Compute behavioral hash from real-time request data.
    Uses same algorithm as honeypot fingerprinting for consistency.
    """
    if not FINGERPRINT_MODULE_AVAILABLE:
        return None
    
    # Extract behavioral features from request
    stable_features = {
        'user_agent': request_data.get('user_agent', ''),
        'accept': request_data.get('accept', ''),
        'accept_encoding': request_data.get('accept_encoding', ''),
        'accept_language': request_data.get('accept_language', ''),
        'referer': request_data.get('referer', ''),
    }
    
    hash_input = json.dumps(stable_features, sort_keys=True)
    return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

def calculate_behavioral_similarity(
    request_data: dict,
    request_obj=None
) -> Tuple[bool, float, Optional[str]]:
    """
    Calculate similarity between current request and known attacker fingerprints.
    
    Args:
        request_data: Dict with user_agent, headers, etc.
        request_obj: Flask request object for JA3 extraction
    
    Returns:
        Tuple of (is_attacker, similarity_score, matched_fingerprint_hash)
    """
    if not FINGERPRINT_MODULE_AVAILABLE or not fingerprint_db:
        return False, 0.0, None
    
    # Extract current behavioral features
    current_hash = compute_realtime_behavioral_hash(request_data)
    if not current_hash:
        return False, 0.0, None
    
    # Extract JA3 if available
    current_ja3 = None
    if request_obj:
        try:
            current_ja3 = extract_ja3_from_request(request_obj)
        except Exception as e:
            logger.debug(f"JA3 extraction failed: {e}")
    
    # Get geolocation
    current_geo = None
    ip = request_data.get('ip')
    if ip:
        try:
            current_geo = get_geolocation(ip)
        except Exception as e:
            logger.debug(f"Geolocation lookup failed: {e}")
    
    # Compare with all known attacker fingerprints
    max_similarity = 0.0
    matched_hash = None
    
    for attacker_hash, attacker_data in fingerprint_db.items():
        # Get most recent profile for this attacker
        profiles = attacker_data.get('profiles', [])
        if not profiles:
            continue
        
        recent_profile = profiles[-1]  # Most recent
        
        # Calculate multi-factor similarity
        similarity_score = _calculate_similarity_score(
            current_hash=current_hash,
            current_ja3=current_ja3,
            current_geo=current_geo,
            attacker_hash=attacker_hash,
            attacker_profile=recent_profile,
            attacker_data=attacker_data
        )
        
        if similarity_score > max_similarity:
            max_similarity = similarity_score
            matched_hash = attacker_hash
    
    # Determine if this is an attacker
    is_attacker = max_similarity >= TERMINATION_THRESHOLD
    
    if is_attacker:
        logger.warning(
            f"🚨 ATTACKER DETECTED on real site! "
            f"IP: {ip} | "
            f"Similarity: {max_similarity:.2%} | "
            f"Matched: {matched_hash}"
        )
    
    return is_attacker, max_similarity, matched_hash

def _calculate_similarity_score(
    current_hash: str,
    current_ja3: Optional[str],
    current_geo: Optional[dict],
    attacker_hash: str,
    attacker_profile: dict,
    attacker_data: dict
) -> float:
    """
    Calculate multi-factor similarity score between current user and known attacker.
    Uses same algorithm as clustering for consistency.
    
    Factors:
    - Behavioral hash match (40%)
    - JA3 TLS fingerprint match (30%)
    - Geographic similarity (20%)
    - IP overlap (10%)
    """
    score = 0.0
    
    # 1. Behavioral Hash Similarity (40%)
    if current_hash == attacker_hash:
        score += 0.40  # Exact match
    else:
        # Partial match based on hash similarity (Hamming distance)
        hash_similarity = _hash_similarity(current_hash, attacker_hash)
        score += 0.40 * hash_similarity
    
    # 2. JA3 TLS Fingerprint Match (30%)
    attacker_ja3s = attacker_data.get('ja3_hashes', [])
    if current_ja3 and attacker_ja3s:
        if current_ja3 in attacker_ja3s:
            score += 0.30  # Exact JA3 match
    elif not current_ja3 and not attacker_ja3s:
        score += 0.15  # Neutral (both unavailable)
    
    # 3. Geographic Similarity (20%)
    attacker_geos = attacker_data.get('geolocations', [])
    if current_geo and attacker_geos:
        geo_score = _geo_similarity_score(current_geo, attacker_geos)
        score += 0.20 * geo_score
    elif not current_geo and not attacker_geos:
        score += 0.10  # Neutral (both unavailable)
    
    # 4. IP Overlap (10%)
    current_ip = attacker_profile.get('ip_address')
    attacker_ips = attacker_data.get('ips_used', [])
    if current_ip in attacker_ips:
        score += 0.10  # Same IP used before
    
    return min(score, 1.0)

def _hash_similarity(hash1: str, hash2: str) -> float:
    """Calculate similarity between two hashes (0.0 to 1.0)."""
    if len(hash1) != len(hash2):
        return 0.0
    
    # Hamming distance
    matches = sum(c1 == c2 for c1, c2 in zip(hash1, hash2))
    return matches / len(hash1)

def _geo_similarity_score(current_geo: dict, attacker_geos: list) -> float:
    """Calculate geographic similarity score (0.0 to 1.0)."""
    current_country = current_geo.get('country_code', 'XX')
    current_city = current_geo.get('city', 'Unknown')
    
    for geo in attacker_geos:
        attacker_country = geo.get('country_code', 'XX')
        attacker_city = geo.get('city', 'Unknown')
        
        if current_city == attacker_city and current_country == attacker_country:
            return 1.0  # Same city
        elif current_country == attacker_country:
            return 0.7  # Same country
    
    return 0.0  # Different location

def check_real_site_user(
    ip: str,
    user_agent: str,
    headers: dict,
    request_obj=None
) -> Tuple[bool, float, Optional[str]]:
    """
    Check if a user on a real site matches known attacker behavior.
    
    Args:
        ip: User's IP address
        user_agent: User-Agent header
        headers: Request headers dict
        request_obj: Flask request object (optional, for JA3)
    
    Returns:
        Tuple of (should_terminate, similarity_score, reason)
    """
    if not FINGERPRINT_MODULE_AVAILABLE:
        return False, 0.0, None
    
    # Build request data
    request_data = {
        'ip': ip,
        'user_agent': user_agent,
        'accept': headers.get('Accept', ''),
        'accept_encoding': headers.get('Accept-Encoding', ''),
        'accept_language': headers.get('Accept-Language', ''),
        'referer': headers.get('Referer', ''),
    }
    
    # Calculate similarity with known attackers
    is_attacker, similarity, matched_hash = calculate_behavioral_similarity(
        request_data, request_obj
    )
    
    if is_attacker:
        reason = (
            f"Behavioral match with known attacker {matched_hash} "
            f"(similarity: {similarity:.2%})"
        )
        
        # Log the detection
        logger.warning(
            f"🚨 SESSION TERMINATION: {ip} | "
            f"Similarity: {similarity:.2%} | "
            f"Matched: {matched_hash} | "
            f"UA: {user_agent[:50]}..."
        )
        
        return True, similarity, reason
    
    return False, similarity, None

def get_monitoring_stats() -> dict:
    """Get statistics about behavioral monitoring."""
    if not FINGERPRINT_MODULE_AVAILABLE:
        return {
            'enabled': False,
            'reason': 'Fingerprint module not available'
        }
    
    return {
        'enabled': True,
        'termination_threshold': TERMINATION_THRESHOLD,
        'known_attackers': len(fingerprint_db),
        'monitored_sessions': len(monitored_sessions),
        'timestamp': datetime.now().isoformat(),
    }

# API endpoint for dashboard
def get_terminated_sessions() -> list:
    """Get list of terminated sessions for dashboard display."""
    terminated = []
    for session_id, data in monitored_sessions.items():
        if data.get('terminated', False):
            terminated.append({
                'session_id': session_id,
                'ip': data.get('ip'),
                'similarity_score': data.get('similarity_score'),
                'matched_fingerprint': data.get('matched_fingerprint'),
                'terminated_at': data.get('terminated_at'),
                'reason': data.get('reason'),
            })
    return terminated
