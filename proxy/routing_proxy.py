"""
Routing Proxy — AI-Driven Traffic Classification & Routing

This reverse proxy intercepts all incoming HTTP requests, extracts features
from URL/headers/body, sends them to the ML API for attack detection,
and routes:
  - Benign traffic → Real website
  - Malicious traffic → Honeypot clone

Also implements dynamic honeypot features:
  - Service rotation (every 60s, configurable)
  - Fake response headers
  - Request logging for analysis
"""

from flask import Flask, request, Response, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
import requests
import re
import json
import time
import threading
import random
import logging
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote

# Central config

_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
from config import (
    ML_API_URL as _ML_API_URL, PROXY_PORT, PROXY_API_KEY,
    RULE_SCORE_HIGH_THRESHOLD, RULE_SCORE_LOW_THRESHOLD,
    ML_CONFIDENCE_THRESHOLD, FEATURE_ORDER, RATE_LIMIT_DEFAULT,
)

# Database Integration
try:
    from proxy.db_integration import log_attack_to_db
    _DB_ENABLED = True
except ImportError:
    try:
        from db_integration import log_attack_to_db
        _DB_ENABLED = True
    except ImportError:
        _DB_ENABLED = False
        def log_attack_to_db(x): return None

# Phase 1: Blockchain Attack Ledger

try:
    from honeypot.blockchain_ledger import log_to_blockchain
    _BLOCKCHAIN_ENABLED = True
    logger_init = logging.getLogger('proxy')
    logger_init.info('\u26d3\ufe0f  Blockchain Attack Ledger enabled')
except ImportError:
    _BLOCKCHAIN_ENABLED = False
    log_to_blockchain = lambda x: None

# L7 HTTP DDoS Detector (rate-based, works natively with HTTP proxy)
try:
    from DDoS.L7.l7_detector import is_ddos as _l7_is_ddos
    _L7_DDOS_ENABLED = True
except ImportError:
    _l7_is_ddos = None
    _L7_DDOS_ENABLED = False

# Phase 2: LLM Adaptive Response Engine — lazy-loaded so it works even if

# Ollama starts AFTER the proxy (common in demo setups)

try:
    from honeypot.llm_response_engine import generate_response, check_ollama_status
    _llm_import_ok = True
except ImportError:
    _llm_import_ok = False
    generate_response = lambda x, y, z: None
    def check_ollama_status(): return False

# Phase 3: Behavioral Monitor — Real-time attacker detection on real sites

try:
    from honeypot.behavioral_monitor import check_real_site_user, get_monitoring_stats
    _BEHAVIORAL_MONITOR_ENABLED = True
    logger_init = logging.getLogger('proxy')
    logger_init.info('🔍 Behavioral Monitor enabled - protecting real sites')
except ImportError:
    _BEHAVIORAL_MONITOR_ENABLED = False
    check_real_site_user = lambda *args, **kwargs: (False, 0.0, None)
    get_monitoring_stats = lambda: {'enabled': False}

# Lazy cached LLM status — re-checks every 60s

_llm_status_cache: dict = {'enabled': False, 'last_check': 0.0}
_llm_status_lock = threading.Lock()

def _llm_is_enabled() -> bool:
    """Returns True if Ollama is reachable. Re-checks every 60s so proxy
    auto-enables LLM even if Ollama starts after the proxy."""
    if not _llm_import_ok:
        return False
    now = time.time()
    with _llm_status_lock:
        if now - _llm_status_cache['last_check'] < 15:
            return _llm_status_cache['enabled']
    # Outside lock: do the actual network check

    enabled = check_ollama_status()
    with _llm_status_lock:
        _llm_status_cache['enabled'] = enabled
        _llm_status_cache['last_check'] = now
    if enabled:
        logger.info('\U0001f9e0 LLM Adaptive Response Engine enabled (Ollama)')
    return enabled

app = Flask(__name__)
CORS(app)
limiter = Limiter(get_remote_address, app=app, default_limits=[RATE_LIMIT_DEFAULT])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('proxy')

# Thread-safety locks (#6, #8)

_ip_lock = threading.Lock()
_log_lock = threading.Lock()
_llm_stats_lock = threading.Lock()

# CONFIGURATION

ML_API_URL = _ML_API_URL

# Site routing map: host/path prefix → (real_port, honeypot_port)

SITE_MAP = {
    'banking':     {'real': 3001, 'honeypot': 4001},
    'ecommerce':   {'real': 3002, 'honeypot': 4002},
    'healthcare':  {'real': 3003, 'honeypot': 4003},
    'blog':        {'real': 3004, 'honeypot': 4004},
    'api_service': {'real': 3005, 'honeypot': 4005},
    'corporate':   {'real': 3006, 'honeypot': 4006},
    'admin_panel': {'real': 3007, 'honeypot': 4007},
}

# Default site to proxy (can be changed via config or environment)

DEFAULT_SITE = 'banking'

# Rotation config

from config import ROTATION_INTERVAL as _ROTATION_INTERVAL_DEFAULT
ROTATION_INTERVAL = _ROTATION_INTERVAL_DEFAULT
current_rotation = {
    'site': DEFAULT_SITE,
    'last_rotated': time.time()
}
malicious_ips = {}  # {ip: {count: N, first_seen: ..., last_seen: ...}} — guarded by _ip_lock
rotation_lock = threading.Lock()

# LLM Stats — persisted to disk so they survive proxy restarts

LLM_STATS_FILE = Path(__file__).parent / 'logs' / 'llm_stats.json'
LLM_STATS_FILE.parent.mkdir(parents=True, exist_ok=True)

def _load_llm_stats():
    """Load LLM stats from disk (survives proxy restarts for demo)."""
    try:
        if LLM_STATS_FILE.exists():
            with open(LLM_STATS_FILE) as f:
                d = json.load(f)
                return {
                    'total_requests': d.get('total_requests', 0),
                    'successful_responses': d.get('successful_responses', 0),
                    'fallbacks': d.get('fallbacks', 0),
                    'last_generated': d.get('last_generated', None)
                }
    except Exception:
        pass
    return {'total_requests': 0, 'successful_responses': 0, 'fallbacks': 0, 'last_generated': None}

def _save_llm_stats():
    """Persist LLM stats to disk (called after each update)."""
    try:
        with open(LLM_STATS_FILE, 'w') as f:
            json.dump(llm_stats, f)
    except Exception:
        pass

llm_stats = _load_llm_stats()

# Attack log

ATTACK_LOG_FILE = Path(__file__).parent / 'logs' / 'proxy_attacks.jsonl'
ATTACK_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Known malicious IPs (start empty, populated by detections)

malicious_ips = {}  # {ip: {'count': N, 'first_seen': ts, 'last_seen': ts}} — guarded by _ip_lock

# ── IP Blocklist (persisted + in-memory) ───────────────────────────────
BLOCKED_IPS_FILE = Path(__file__).parent / 'logs' / 'blocked_ips.json'
BLOCKED_IPS: set = set()
_blocked_lock = threading.Lock()

def _load_blocked_ips():
    """Load persisted blocked IPs on startup."""
    global BLOCKED_IPS
    try:
        if BLOCKED_IPS_FILE.exists():
            data = json.loads(BLOCKED_IPS_FILE.read_text())
            BLOCKED_IPS = set(data.get('blocked_ips', []))
            logger.info(f'Loaded {len(BLOCKED_IPS)} blocked IPs from disk')
    except Exception as e:
        logger.warning(f'Could not load blocked_ips.json: {e}')

def _save_blocked_ips():
    """Persist blocked IPs to disk."""
    try:
        BLOCKED_IPS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(BLOCKED_IPS_FILE, 'w') as f:
            json.dump({'blocked_ips': list(BLOCKED_IPS), 'updated': datetime.now().isoformat()}, f)
    except Exception as e:
        logger.warning(f'Could not save blocked_ips.json: {e}')

_load_blocked_ips()

# FEATURE EXTRACTION (for web attack detection)

# Common attack patterns

SQLI_PATTERNS = [
    r"(?i)(union\s+select|select\s+.*\s+from|insert\s+into|delete\s+from|drop\s+table)",
    r"(?i)(or\s+1\s*=\s*1|and\s+1\s*=\s*1|'\s*or\s*'|'\s*and\s*')",
    r"(?i)(--|;|/\*|\*/|@@|char\(|concat\(|ascii\(|substring\()",
    r"(?i)(exec\s*\(|execute|xp_cmdshell|sp_executesql)",
    r"(?i)(benchmark\s*\(|sleep\s*\(|waitfor\s+delay)",
    r"(?i)(information_schema|sys\.tables|mysql\.user)",
]

NOSQLI_PATTERNS = [
    r'(\$gt|\$lt|\$ne|\$eq|\$regex|\$where|\$or|\$and)',
    r"(?i)(db\.\w+\.find|db\.\w+\.insert|db\.\w+\.drop)",
    r'\{[^}]*"\$',
    r'(?i)(mapreduce|aggregate|eval\s*\()',
]

XSS_PATTERNS = [
    r'<\s*script[^>]*>',
    r'(?i)(on\w+\s*=\s*["\'])',
    r'(?i)(javascript\s*:)',
    r'(?i)(document\.(cookie|write|location)|window\.(location|open))',
    r'(<\s*img[^>]+onerror|<\s*svg[^>]+onload)',
    r'(?i)(alert\s*\(|confirm\s*\(|prompt\s*\()',
    r'<\s*(iframe|embed|object|applet)',
]

TRAVERSAL_PATTERNS = [
    r'(\.\./|\.\.\\|%2e%2e|%252e)',
    r'(?i)(/etc/passwd|/etc/shadow|/proc/self)',
    r'(?i)(cmd\.exe|powershell|/bin/(ba)?sh)',
]

def count_pattern_matches(text, patterns):
    """Count how many patterns match in the text."""
    count = 0
    for pattern in patterns:
        if re.search(pattern, text):
            count += 1
    return count

def extract_features(req):
    """
    Extract security-relevant features from an HTTP request.
    Returns a feature dict for classification.
    """
    url = req.url
    path = req.path
    query_string = req.query_string.decode('utf-8', errors='replace')
    headers = dict(req.headers)
    body = req.get_data(as_text=True)
    method = req.method
    user_agent = headers.get('User-Agent', '')

    # Combine all input text for pattern matching

    all_input = f"{url} {query_string} {body} {' '.join(headers.values())}"
    decoded_input = unquote(all_input)

    features = {
        # Request metadata

        'url_length': len(url),
        'path_length': len(path),
        'query_length': len(query_string),
        'body_length': len(body),
        'method_is_post': 1 if method == 'POST' else 0,
        'method_is_put': 1 if method == 'PUT' else 0,
        'num_headers': len(headers),
        'has_auth_header': 1 if 'Authorization' in headers else 0,
        'content_type_json': 1 if 'json' in headers.get('Content-Type', '').lower() else 0,
        'content_type_form': 1 if 'form' in headers.get('Content-Type', '').lower() else 0,

        # URL features

        'num_params': len(parse_qs(query_string)),
        'num_path_segments': len([s for s in path.split('/') if s]),
        'has_encoded_chars': 1 if '%' in url else 0,
        'num_special_chars': sum(1 for c in all_input if c in "'\";<>(){}[]|&`!"),
        'max_param_length': max([len(v[0]) for v in parse_qs(query_string).values()] or [0]),

        # Attack pattern counts

        'sqli_pattern_count': count_pattern_matches(decoded_input, SQLI_PATTERNS),
        'nosqli_pattern_count': count_pattern_matches(decoded_input, NOSQLI_PATTERNS),
        'xss_pattern_count': count_pattern_matches(decoded_input, XSS_PATTERNS),
        'traversal_pattern_count': count_pattern_matches(decoded_input, TRAVERSAL_PATTERNS),

        # Behavioral

        'has_suspicious_ua': 1 if any(t in user_agent.lower() for t in
            ['sqlmap', 'nikto', 'nmap', 'dirb', 'burp', 'curl', 'wget', 'python-requests']) else 0,
        'ua_length': len(user_agent),
        'has_referer': 1 if 'Referer' in headers else 0,
        'has_cookie': 1 if 'Cookie' in headers else 0,
    }

    return features

def classify_request(features):
    """
    Classify request using ensemble of rule-based + ML detection. (#19, #20)
    Always consults ML model when available and combines both signals.
    Thresholds are sourced from config.py for calibration control.
    """
    # Rule-based score

    score = 0
    score += features['sqli_pattern_count'] * 0.25
    score += features['nosqli_pattern_count'] * 0.25
    score += features['xss_pattern_count'] * 0.25
    score += features['traversal_pattern_count'] * 0.3
    score += features['has_suspicious_ua'] * 0.15
    score += min(features['num_special_chars'] / 20, 0.3)

    attack_types = _get_attack_types(features)

    # (#13) Build feature vector in canonical order for ML model

    feature_vec = [features.get(k, 0) for k in FEATURE_ORDER]

    # (#20) Always try ML API — ensemble both signals

    ml_result = None
    try:
        resp = requests.post(
            f'{ML_API_URL}/api/detect/web-attack',
            json={'features': feature_vec},
            timeout=1.0
        )
        if resp.status_code == 200:
            ml_result = resp.json()
    except Exception as e:
        logger.debug(f"ML API unavailable: {e}")  # (#10) no bare except

    # Ensemble decision: either signal triggers detection

    if ml_result:
        ml_malicious = ml_result.get('is_malicious', False)
        ml_conf = ml_result.get('confidence', 0)
        is_malicious = (
            score >= RULE_SCORE_HIGH_THRESHOLD
            or (ml_malicious and ml_conf >= ML_CONFIDENCE_THRESHOLD)
            or (score >= RULE_SCORE_LOW_THRESHOLD and ml_malicious)
        )
        confidence = max(score, ml_conf) if is_malicious else min(score, ml_conf)
        method = 'ensemble'
    else:
        # ML unavailable — rule-only fallback

        is_malicious = score >= RULE_SCORE_LOW_THRESHOLD
        confidence = score
        method = 'rule_based_fallback'

    return {
        'is_malicious': is_malicious,
        'confidence': min(confidence, 1.0),
        'method': method,
        'attack_types': attack_types if is_malicious else [],
    }

def _get_attack_types(features):
    """Determine which attack types are suspected."""
    types = []
    if features['sqli_pattern_count'] > 0:
        types.append('SQLi')
    if features['nosqli_pattern_count'] > 0:
        types.append('NoSQLi')
    if features['xss_pattern_count'] > 0:
        types.append('XSS')
    if features['traversal_pattern_count'] > 0:
        types.append('Path Traversal')
    if features['has_suspicious_ua']:
        types.append('Suspicious Tool')
    return types

# ROTATION MANAGER

def rotate_services():
    """Periodically rotate which honeypot services are active."""
    while True:
        time.sleep(ROTATION_INTERVAL)
        with rotation_lock:
            sites = list(SITE_MAP.keys())
            new_site = random.choice(sites)
            current_rotation['site'] = new_site
            current_rotation['last_rotated'] = time.time()
            logger.info(f" Service rotated to: {new_site}")

# Request logging


# Map site names to honeypot port names for human-readable logging

_PORT_TO_SITE = {
    4001: 'Banking Honeypot (SecureBank)',
    4002: 'E-commerce Honeypot (MegaStore)',
    4003: 'Healthcare Honeypot (MedClinic)',
    4004: 'Blog Honeypot (TechBlog)',
    4005: 'API Service Honeypot (DataAPI)',
    4006: 'Corporate Honeypot (NexaGen Corp)',
    4007: 'Admin Honeypot (SysNet Admin)',
    3001: 'Banking Real Site',
    3002: 'E-commerce Real Site',
    3003: 'Healthcare Real Site',
    3004: 'Blog Real Site',
    3005: 'API Real Site',
    3006: 'Corporate Real Site',
    3007: 'Admin Real Site',
}

_BENIGN_LOG_FILE = Path(__file__).parent / 'logs' / 'benign_requests.jsonl'

def _fetch_fake_users(honeypot_port):
    """Fetch first 3 GAN-generated users from a honeypot for logging evidence."""
    try:
        import requests as _req
        r = _req.get(f'http://localhost:{honeypot_port}/api/users', timeout=1)
        if r.status_code == 200:
            users = r.json()[:3]
            return [{'id': u.get('id'), 'username': u.get('username'), 'email': u.get('email'), 'role': u.get('role')} for u in users]
    except Exception:
        pass
    return []

def log_attack(req, classification, target):
    """Log attack details for analysis — enhanced with honeypot name and fake data preview."""
    # Parse honeypot port from target string like 'honeypot:4001'

    honeypot_port = None
    honeypot_name = 'Unknown'
    is_honeypot = target.startswith('honeypot:')
    if is_honeypot:
        try:
            honeypot_port = int(target.split(':')[1])
            honeypot_name = _PORT_TO_SITE.get(honeypot_port, f'Honeypot:{honeypot_port}')
        except (IndexError, ValueError):
            pass

    # Fetch a preview of the fake GAN data served to the attacker

    fake_data_preview = []
    if is_honeypot and honeypot_port:
        fake_data_preview = _fetch_fake_users(honeypot_port)

    attack_types = classification.get('attack_types', [])
    entry = {
        'timestamp': datetime.now().isoformat(),
        'ip': req.remote_addr,
        'method': req.method,
        'url': req.url,
        'path': req.path,
        'query': req.query_string.decode('utf-8', errors='replace'),
        'user_agent': req.headers.get('User-Agent', ''),
        'classification': classification,
        'routed_to': target,
        'honeypot_name': honeypot_name if is_honeypot else 'N/A (real site)',
        'honeypot_port': honeypot_port,
        'captured': is_honeypot,
        'attack_type_primary': attack_types[0] if attack_types else 'Unknown',
        'fake_data_served': fake_data_preview,
        'body_preview': req.get_data(as_text=True)[:500],
    }

    # (#8) Thread-safe file write

    with _log_lock:
        with open(ATTACK_LOG_FILE, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    # Phase 1: Also log to Blockchain Ledger (tamper-proof)

    if _BLOCKCHAIN_ENABLED:
        try:
            log_to_blockchain(entry)
        except Exception as e:
            logger.debug(f"Blockchain log error (non-fatal): {e}")  # (#10)

    # Phase 4: Log to Central Database for Dashboard
    if _DB_ENABLED:
        try:
            log_attack_to_db(entry)
        except Exception as e:
            logger.debug(f"Database log error: {e}")

    # (#6, #22) Thread-safe IP tracking; use list for JSON-serializable attack_types

    ip = req.remote_addr
    with _ip_lock:
        if ip not in malicious_ips:
            malicious_ips[ip] = {
                'count': 0,
                'first_seen': datetime.now().isoformat(),
                'attack_types': []
            }
        malicious_ips[ip]['count'] += 1
        malicious_ips[ip]['last_seen'] = datetime.now().isoformat()
        for at in classification.get('attack_types', []):
            if at not in malicious_ips[ip]['attack_types']:
                malicious_ips[ip]['attack_types'].append(at)

def log_benign_with_reason(req, classification, target_port, missed_reason):
    """Log benign/missed requests so can see why they weren't flagged."""
    entry = {
        'timestamp': datetime.now().isoformat(),
        'ip': req.remote_addr,
        'method': req.method,
        'path': req.path,
        'query': req.query_string.decode('utf-8', errors='replace')[:200],
        'user_agent': req.headers.get('User-Agent', ''),
        'confidence': classification.get('confidence', 0),
        'attack_types_suspected': classification.get('attack_types', []),
        'routed_to': f'real_site:{target_port}',
        'site_name': _PORT_TO_SITE.get(target_port, f'Real:{target_port}'),
        'captured': False,
        'missed_reason': missed_reason,
    }
    with _log_lock:
        _BENIGN_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_BENIGN_LOG_FILE, 'a') as f:
            f.write(json.dumps(entry) + '\n')

# PROXY ROUTES

@app.route('/proxy/status', methods=['GET'])
def proxy_status():
    """Return proxy status and stats."""
    with _ip_lock:
        snapshot = {ip: dict(data) for ip, data in list(malicious_ips.items())[:20]}
    with _llm_stats_lock:
        llm_snap = dict(llm_stats)
    behavioral_stats = get_monitoring_stats() if _BEHAVIORAL_MONITOR_ENABLED else {'enabled': False}
    with _blocked_lock:
        blocked_count = len(BLOCKED_IPS)
    return jsonify({
        'status': 'healthy',
        'current_site': current_rotation['site'],
        'rotation_interval': ROTATION_INTERVAL,
        'known_attackers': len(malicious_ips),
        'blocked_ips': blocked_count,
        'attacker_summary': snapshot,
        'llm_stats': llm_snap,
        'behavioral_monitor': behavioral_stats,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/proxy/block-ip', methods=['POST'])
def block_ip():
    """Internal endpoint: add IP to blocklist (called by profiler/retraining pipeline)."""
    data = request.get_json(silent=True) or {}
    ip   = data.get('ip', '').strip()
    reason = data.get('reason', 'manual')
    if not ip:
        return jsonify({'error': 'ip required'}), 400
    with _blocked_lock:
        BLOCKED_IPS.add(ip)
        _save_blocked_ips()
    logger.warning(f'BLOCKED IP: {ip} (reason: {reason})')
    return jsonify({'status': 'blocked', 'ip': ip, 'reason': reason})

@app.route('/proxy/unblock-ip', methods=['POST'])
def unblock_ip():
    """Internal endpoint: remove IP from blocklist."""
    data = request.get_json(silent=True) or {}
    ip   = data.get('ip', '').strip()
    if not ip:
        return jsonify({'error': 'ip required'}), 400
    with _blocked_lock:
        BLOCKED_IPS.discard(ip)
        _save_blocked_ips()
    return jsonify({'status': 'unblocked', 'ip': ip})

@app.route('/proxy/blocked-ips', methods=['GET'])
def list_blocked_ips():
    """List all currently blocked IPs."""
    with _blocked_lock:
        return jsonify({'blocked_ips': sorted(BLOCKED_IPS), 'total': len(BLOCKED_IPS)})

@app.route('/proxy/attacks', methods=['GET'])
def get_attacks():
    """Return recent attack logs."""
    limit = request.args.get('limit', 50, type=int)
    attacks = []
    if ATTACK_LOG_FILE.exists():
        with open(ATTACK_LOG_FILE) as f:
            lines = f.readlines()
            for line in lines[-limit:]:
                try:
                    attacks.append(json.loads(line))
                except Exception as e:  # (#10)
                    logger.debug(f"Malformed log line: {e}")
    return jsonify({'attacks': attacks, 'total': len(attacks)})

@app.route('/proxy/missed-attacks', methods=['GET'])
def get_missed_attacks():
    """Return benign/missed requests with the reason they were not flagged."""
    limit = request.args.get('limit', 50, type=int)
    missed = []
    if _BENIGN_LOG_FILE.exists():
        with open(_BENIGN_LOG_FILE) as f:
            lines = f.readlines()
            for line in lines[-limit:]:
                try:
                    missed.append(json.loads(line))
                except Exception as e:
                    logger.debug(f"Malformed benign log line: {e}")
    return jsonify({'missed_attacks': missed, 'total': len(missed)})

@app.route('/proxy/classify', methods=['POST'])
def classify_payload():
    """
    Live classification endpoint — for demo/testing purposes.
    POST JSON: {"url": "/search?q=1' OR '1'='1", "user_agent": "sqlmap/1.7", "method": "GET"}
    Returns: rule score, ML confidence, verdict
    """
    data = request.get_json(silent=True) or {}
    url = data.get('url', '/test')
    user_agent = data.get('user_agent', 'Mozilla/5.0')
    method = data.get('method', 'GET')

    # Build a fake request-like object for scoring

    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(url)
    query = parsed.query or ''

    # Rule-based scoring (same as proxy uses internally)

    rule_score = 0.0
    sqli_score = 0.0
    xss_score = 0.0
    traversal_score = 0.0

    sqli_patterns = [
        r"(?i)(union\s+select|' or '|or 1=1|drop table|insert into|--|;select|'='|1'|xp_|exec\(|benchmark\()",
        r"(?i)(sleep\(\d+\)|waitfor\s+delay)",
        r"(?i)(select.*from|where.*=|having.*=)",
    ]
    xss_patterns = [r"(?i)(<script|javascript:|onerror=|onload=|alert\(|document\.cookie)", r"(?i)(eval\(|src=data:)"]
    trav_patterns = [r"(\.\./|\.\.\\|%2e%2e|%252e|/etc/|/windows/system32)", r"(?i)(passwd|shadow|boot\.ini|win\.ini)"]

    import re
    target = url + user_agent
    for p in sqli_patterns:
        if re.search(p, target): sqli_score += 0.33
    for p in xss_patterns:
        if re.search(p, target): xss_score += 0.5
    for p in trav_patterns:
        if re.search(p, target): traversal_score += 0.5

    sqli_score = min(sqli_score, 1.0)
    xss_score = min(xss_score, 1.0)
    traversal_score = min(traversal_score, 1.0)

    # High-confidence scanner/tool detection

    scanner_agents = ['sqlmap', 'nikto', 'nmap', 'masscan', 'dirbuster', 'hydra', 'burp', 'zap']
    is_scanner = any(s in user_agent.lower() for s in scanner_agents)
    if is_scanner:
        rule_score = max(rule_score + 0.7, 0.7)

    rule_score = max(rule_score, sqli_score * 0.8, xss_score * 0.8, traversal_score * 0.7)
    rule_score = min(rule_score, 1.0)

    # Determine dominant attack type

    scores = {'SQLi': sqli_score, 'XSS': xss_score, 'Path Traversal': traversal_score}
    if is_scanner: scores['Scanner'] = 0.9
    attack_type = max(scores, key=scores.get) if any(v > 0 for v in scores.values()) else 'Unknown'
    top_score = max(scores.values()) if scores else 0.0

    is_malicious = rule_score >= RULE_SCORE_HIGH_THRESHOLD or top_score > 0.5
    verdict = 'MALICIOUS → HONEYPOT' if is_malicious else 'BENIGN → REAL SITE'

    # Log malicious classification attempts to DB
    if is_malicious and _DB_ENABLED:
        try:
            log_attack_to_db({
                'timestamp': datetime.now().isoformat(),
                'ip': request.remote_addr,
                'method': method,
                'url': url,
                'path': urlparse(url).path,
                'query_string': urlparse(url).query,
                'attack_type': attack_type,
                'attack_types': [attack_type],
                'confidence': round(max(rule_score, top_score), 3),
                'detection_method': 'classification_api',
                'routed_to': 'honeypot',
                'captured': True,
                'user_agent': user_agent
            })
        except Exception:
            pass

    return jsonify({
        'url': url,
        'is_malicious': is_malicious,
        'verdict': verdict,
        'rule_score': round(rule_score, 3),
        'confidence': round(max(rule_score, top_score), 3),
        'attack_type': attack_type,
        'scores': {k: round(v, 3) for k, v in scores.items()},
        'scanner_detected': is_scanner,
        'routed_to': 'honeypot' if is_malicious else 'real_site',
    })

# (#1) API key required for config mutation

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == 'POST':
            key = request.headers.get('X-API-Key', '')
            if key != PROXY_API_KEY:
                return jsonify({'error': 'Forbidden — X-API-Key header required'}), 403
        return f(*args, **kwargs)
    return decorated

@app.route('/proxy/config', methods=['GET', 'POST'])
@require_api_key
def proxy_config():
    """Get or update proxy configuration (POST requires X-API-Key header)."""
    global ROTATION_INTERVAL, DEFAULT_SITE

    if request.method == 'POST':
        data = request.get_json()
        if 'rotation_interval' in data:
            ROTATION_INTERVAL = data['rotation_interval']
        if 'default_site' in data and data['default_site'] in SITE_MAP:
            DEFAULT_SITE = data['default_site']
        return jsonify({'status': 'updated', 'config': {
            'rotation_interval': ROTATION_INTERVAL,
            'default_site': DEFAULT_SITE,
        }})

    return jsonify({
        'rotation_interval': ROTATION_INTERVAL,
        'default_site': DEFAULT_SITE,
        'available_sites': list(SITE_MAP.keys()),
        'ml_api_url': ML_API_URL,
    })

# ── Demo Control APIs (used by Laptop B attack scripts) ────────────────

@app.route('/proxy/demo/crash-honeypot', methods=['POST'])
def demo_crash_honeypot():
    """Demo: crash corporate honeypot on port 4006 and restart it after 4 seconds.
    Called by Laptop B's DDoS script during Wave 3 to simulate pod crash."""
    import subprocess
    import threading

    DEMO_PORT = 4006
    PROJECT_DIR = Path(__file__).parent.parent

    def restart_honeypot():
        time.sleep(4)
        try:
            env = {'PATH': '/usr/bin:/bin:/usr/local/bin'}
            venv_python = PROJECT_DIR / 'venv' / 'bin' / 'python3'
            python_bin = str(venv_python) if venv_python.exists() else 'python3'
            code = f"""
import sys, os
sys.path.insert(0, '.')
sys.path.insert(0, 'websites')
from pathlib import Path
from shared.site_factory import create_app
config = {{
    'name': 'NexaGen Corp Honeypot', 'type': 'corporate', 'is_honeypot': True,
    'db_path': str(Path('websites/databases/corporate_honeypot.db')),
    'port': {DEMO_PORT}, 'theme_color': '#e74c3c',
    'tagline': 'Innovation Through Technology',
    'icon': '\\U0001f36f', 'items_label': 'Services'
}}
app = create_app(config)
app.run(host='0.0.0.0', port={DEMO_PORT}, debug=False, use_reloader=False)
"""
            subprocess.Popen(
                [python_bin, '-c', code],
                cwd=str(PROJECT_DIR),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            logger.info(f"[DEMO] Honeypot port {DEMO_PORT} restarted successfully")
        except Exception as e:
            logger.error(f"[DEMO] Honeypot restart failed: {e}")

    # Kill the process on port 4006
    try:
        result = subprocess.run(['lsof', '-ti', f':{DEMO_PORT}', '-sTCP:LISTEN'], capture_output=True, text=True)
        pids = [p.strip() for p in result.stdout.strip().split() if p.strip()]
        killed = 0
        for pid in pids:
            subprocess.run(['kill', '-9', pid], capture_output=True)
            killed += 1
        threading.Thread(target=restart_honeypot, daemon=True).start()
        logger.warning(f"[DEMO] 💥 Crashed honeypot :{DEMO_PORT} (killed {killed} PIDs) — restarting in 4s")
        return jsonify({'status': 'crashed', 'port': DEMO_PORT, 'killed_pids': killed, 'restarting_in': '4s'})
    except Exception as e:
        logger.error(f"[DEMO] Crash failed: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/proxy/demo/log-ddos', methods=['POST'])
def demo_log_ddos():
    """Log a DDoS attack event from Laptop B into the attack DB.
    Called once per DDoS wave so the dashboard shows real DDoS entries."""
    try:
        data = request.get_json() or {}
        attacker_ip = data.get('attacker_ip', request.remote_addr)
        wave = data.get('wave', 1)
        req_count = data.get('request_count', 0)
        classification = {
            'is_malicious': True,
            'confidence': 0.97,
            'attack_types': ['DDoS'],
            'method': 'l7_ddos_detector',
            'rule_score': 0.95,
        }
        # Write to attack log file directly
        entry = {
            'timestamp': datetime.now().isoformat(),
            'ip': attacker_ip,
            'method': 'GET',
            'url': f'/corporate/flood-wave-{wave}',
            'path': f'/corporate/flood-wave-{wave}',
            'attack_type': 'DDoS',
            'attack_types': ['DDoS'],
            'confidence': 0.97,
            'routed_to': f'honeypot:4006',
            'user_agent': f'DDoS-Flood/Wave{wave}',
            'captured': True,
            'wave': wave,
            'request_count': req_count,
        }
        with open(ATTACK_LOG_FILE, 'a') as f:
            f.write(json.dumps(entry) + '\n')
        # Also log to DB
        try:
            log_attack_to_db(
                ip=attacker_ip,
                user_agent=f'DDoS-Flood/Wave{wave}',
                method='GET',
                url=f'/corporate/flood-wave-{wave}',
                attack_type='DDoS',
                attack_types_json=json.dumps(['DDoS']),
                confidence=0.97,
                detection_method='l7_ddos_detector',
                routed_to='honeypot',
                honeypot_port=4006,
                target_site='corporate',
                payload=f'DDoS wave {wave}: {req_count} requests',
                headers_json='{}',
                classification_json=json.dumps(classification),
                captured=True,
            )
        except Exception:
            pass
        logger.warning(f"[DEMO] DDoS wave {wave} logged: {req_count} reqs from {attacker_ip}")
        return jsonify({'status': 'logged', 'wave': wave})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Canary token paths served directly from proxy ────────────────────
# These must bypass the LLM and ML classifier — serve the zip bomb / fake
# credentials directly so the attacker gets the real canary file, not an
# LLM-generated SQL page.

_CANARY_ZIP_PATHS = {
    '/backup/database_full_2026.zip', '/db.zip', '/backup.zip',
    '/backup/full_backup.zip', '/data/export.zip', '/credentials.zip',
    '/users_dump.zip', '/user_data.zip', '/database_backup.zip',
    '/private/data.zip',
}
_CANARY_OTHER_PATHS = {
    '/robots.txt', '/.env', '/env', '/.env.production', '/.env.local',
    '/backup.sql', '/backup.sql.gz', '/database/backup.sql',
    '/db_backup.sql', '/dump.sql',
    '/wp-admin', '/wp-admin/', '/wp-login.php', '/administrator/', '/admin.php',
    '/phpmyadmin/', '/phpmyadmin', '/pma/', '/myadmin/',
    '/api/v2/config', '/api/v2/internal/config', '/api/config', '/config.json',
    '/server-status', '/server-info',
    '/debug/', '/debug/vars', '/debug/pprof/',
    '/download/confidential_keys.txt', '/keys.txt',
    '/.git/config', '/.git/HEAD', '/.gitignore',
    '/pixel.png', '/analytics.png', '/t.gif',
}

def _forward_to_canary(canary_path):
    """Forward request directly to a honeypot canary endpoint (port 4001)."""
    honeypot_port = 4001   # any honeypot — they all have canary_bp registered
    url = f'http://127.0.0.1:{honeypot_port}{canary_path}'
    try:
        resp = requests.get(
            url,
            headers={'X-Real-IP': request.remote_addr,
                     'User-Agent': request.headers.get('User-Agent', '')},
            timeout=10,
            stream=True,
        )
        # Stream back the response (important for binary zip content)
        headers = {k: v for k, v in resp.headers.items()
                   if k.lower() not in ('transfer-encoding', 'connection')}
        return Response(
            resp.content,
            status=resp.status_code,
            headers=headers,
            mimetype=resp.headers.get('Content-Type', 'application/octet-stream'),
        )
    except Exception as e:
        logger.error(f'Canary forward failed for {canary_path}: {e}')
        return Response('Not found', status=404)

@app.route('/robots.txt')
@app.route('/.env')
@app.route('/env')
@app.route('/.env.production')
@app.route('/.env.local')
@app.route('/backup.sql')
@app.route('/db.zip')
@app.route('/backup.zip')
@app.route('/credentials.zip')
@app.route('/users_dump.zip')
@app.route('/user_data.zip')
@app.route('/database_backup.zip')
@app.route('/download/confidential_keys.txt')
@app.route('/keys.txt')
@app.route('/.git/config')
@app.route('/.git/HEAD')
@app.route('/.gitignore')
@app.route('/wp-admin')
@app.route('/wp-admin/')
@app.route('/wp-login.php')
@app.route('/administrator/')
@app.route('/admin.php')
@app.route('/phpmyadmin/')
@app.route('/phpmyadmin')
@app.route('/server-status')
@app.route('/config.json')
def proxy_canary_root():
    """Top-level canary paths — forward to honeypot canary blueprint."""
    return _forward_to_canary(request.path)

@app.route('/backup/<path:subpath>')
@app.route('/data/<path:subpath>')
@app.route('/private/<path:subpath>')
@app.route('/debug/<path:subpath>')
@app.route('/database/<path:subpath>')
def proxy_canary_subpath(subpath):
    """Canary sub-paths (e.g. /backup/database_full_2026.zip)."""
    return _forward_to_canary(request.path)

# Determine site from path prefix: /banking/... → banking site

@app.route('/<site_name>/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@app.route('/<site_name>/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy_to_site(site_name, path):
    """
    Main proxy endpoint.
    Receives requests, classifies them, and routes to real or honeypot.
    """
    if site_name in ('proxy', 'static', 'favicon.ico'):
        return jsonify({'error': 'Not a proxied route'}), 404

    # Determine which site

    if site_name in SITE_MAP:
        target_site = site_name
    else:
        target_site = current_rotation['site']
        path = f'{site_name}/{path}' if path else site_name

    # ── Blocked IP check (session termination) ───────────────────────────
    ip = request.remote_addr
    with _blocked_lock:
        if ip in BLOCKED_IPS:
            logger.warning(f'BLOCKED IP {ip} attempted access — returning 403')
            return jsonify({
                'error': 'Access denied',
                'reason': 'Your IP has been blocked due to suspicious behavioral patterns.',
                'code': 403
            }), 403

    # Extract features and classify

    features = extract_features(request)
    classification = classify_request(features)

    # Check if IP is known attacker (auto-route to honeypot)

    ip = request.remote_addr
    if ip in malicious_ips and malicious_ips[ip]['count'] >= 3:
        classification['is_malicious'] = True
        classification['method'] = 'known_attacker'
        classification['confidence'] = 0.99

    # L7 DDoS Detection — rate-based, HTTP-native (overrides web-attack classify)
    if _L7_DDOS_ENABLED and _l7_is_ddos is not None:
        _ua  = request.headers.get('User-Agent', '')
        _xff = request.headers.get('X-Forwarded-For', None)
        _ddos_attack, _ddos_conf = _l7_is_ddos(
            ip=ip,
            path=request.path,
            status=200,   # pre-routing — use 200 as placeholder
            ua=_ua,
            xff=_xff
        )
        if _ddos_attack and not classification['is_malicious']:
            classification['is_malicious'] = True
            classification['method'] = 'l7_ddos_detector'
            classification['confidence'] = _ddos_conf
            classification['attack_types'] = ['DDoS']
            logger.warning(f"L7 DDoS detected: {ip} conf={_ddos_conf:.4f}")

    # Route decision

    if classification['is_malicious']:
        target_port = SITE_MAP[target_site]['honeypot']
        target_label = 'HONEYPOT'
        log_attack(request, classification, f'honeypot:{target_port}')

        # Phase 2: LLM Adaptive Response (for high-confidence attacks)

        # Intercept specific attack types and generate dynamic HTML via LLM

        # If LLM fails → returns None → falls through to the DYNAMIC honeypot

        if _llm_is_enabled() and classification['confidence'] >= 0.3:
            attack_types = classification.get('attack_types', [])
            primary_attack = attack_types[0] if attack_types else 'Generic'
            
            # LLM fires for ALL attack types — maps everything to a prompt category

            _llm_type_map = {
                'SQLi': 'SQLi', 'NoSQLi': 'SQLi', 'XSS': 'XSS',
                'Command Injection': 'Command Injection',
                'Path Traversal': 'Path Traversal',
                'Suspicious Tool': 'SQLi',
            }
            llm_attack_type = _llm_type_map.get(primary_attack, 'SQLi')
            try:
                with _llm_stats_lock:  # (#6) thread-safe — count every attempt
                    llm_stats['total_requests'] += 1
                llm_html = generate_response(
                    attack_type=llm_attack_type,
                    payload=unquote(request.query_string.decode('utf-8', errors='replace')),
                    site_name=target_site
                )
                if llm_html is not None:
                    with _llm_stats_lock:
                        llm_stats['successful_responses'] += 1
                        llm_stats['last_generated'] = datetime.now().isoformat()
                        _save_llm_stats()
                    _save_llm_stats()
                    logger.info(f" Served LLM response for {primary_attack} → {llm_attack_type}")
                    return Response(llm_html, status=200, mimetype='text/html')
                else:
                    with _llm_stats_lock:
                        llm_stats['fallbacks'] += 1
                    _save_llm_stats()
                    logger.info(f" LLM cache miss — routing to dynamic honeypot")
            except Exception as e:
                with _llm_stats_lock:
                    llm_stats['fallbacks'] += 1
                _save_llm_stats()
                logger.error(f"LLM generation failed: {e}")
            # Fall through to the DYNAMIC honeypot (Flask app on port {target_port})


    else:
        target_port = SITE_MAP[target_site]['real']
        target_label = 'REAL'
        
        # Phase 3: Behavioral Monitor - Check if user matches known attackers
        # If similarity > 50%, terminate session and route to honeypot instead
        if _BEHAVIORAL_MONITOR_ENABLED:
            should_terminate, similarity, reason = check_real_site_user(
                ip=ip,
                user_agent=request.headers.get('User-Agent', ''),
                headers=dict(request.headers),
                request_obj=request
            )
            
            if should_terminate:
                # Override routing decision - send to honeypot
                target_port = SITE_MAP[target_site]['honeypot']
                target_label = 'HONEYPOT (BEHAVIORAL MATCH)'
                
                # Log as attack with special classification
                classification['is_malicious'] = True
                classification['method'] = 'behavioral_monitor'
                classification['confidence'] = similarity
                classification['attack_types'] = ['Behavioral Match']
                classification['termination_reason'] = reason
                
                log_attack(request, classification, f'honeypot:{target_port}')
                
                logger.warning(
                    f"🚨 SESSION TERMINATED: {ip} → HONEYPOT | "
                    f"Similarity: {similarity:.2%} | "
                    f"Reason: {reason}"
                )
                
                # Continue to honeypot routing (skip benign logging)
            else:
                # Normal benign request - log it
                # Compute why it wasn't flagged (for audit/ visibility)
                conf = classification.get('confidence', 0)
                types = classification.get('attack_types', [])
                if conf == 0 and not types:
                    missed_reason = 'No attack patterns detected (benign request)'
                elif conf > 0 and conf < RULE_SCORE_HIGH_THRESHOLD:
                    missed_reason = f'Score {conf:.2f} below threshold {RULE_SCORE_HIGH_THRESHOLD} — weak signal'
                elif types and conf < ML_CONFIDENCE_THRESHOLD:
                    missed_reason = f'Suspected {types} but ML confidence {conf:.2f} < {ML_CONFIDENCE_THRESHOLD} threshold'
                else:
                    missed_reason = f'Classified as benign by ensemble (behavioral similarity: {similarity:.2%})'
                log_benign_with_reason(request, classification, target_port, missed_reason)
        else:
            # Behavioral monitor disabled - normal benign logging
            conf = classification.get('confidence', 0)
            types = classification.get('attack_types', [])
            if conf == 0 and not types:
                missed_reason = 'No attack patterns detected (benign request)'
            elif conf > 0 and conf < RULE_SCORE_HIGH_THRESHOLD:
                missed_reason = f'Score {conf:.2f} below threshold {RULE_SCORE_HIGH_THRESHOLD} — weak signal'
            elif types and conf < ML_CONFIDENCE_THRESHOLD:
                missed_reason = f'Suspected {types} but ML confidence {conf:.2f} < {ML_CONFIDENCE_THRESHOLD} threshold'
            else:
                missed_reason = 'Classified as benign by ensemble'
            log_benign_with_reason(request, classification, target_port, missed_reason)

    # Forward request

    target_url = f'http://localhost:{target_port}/{path}'
    if request.query_string:
        target_url += f'?{request.query_string.decode("utf-8", errors="replace")}'

    try:
        # Forward with original method, headers, body

        resp = requests.request(
            method=request.method,
            url=target_url,
            headers={k: v for k, v in request.headers if k.lower() != 'host'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            timeout=10
        )

        # Build response

        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(k, v) for k, v in resp.raw.headers.items()
                    if k.lower() not in excluded_headers]

        # Add deceptive headers for honeypot responses

        if classification['is_malicious']:
            headers.append(('X-Powered-By', random.choice([
                'PHP/7.4.3', 'ASP.NET', 'Express', 'Apache/2.4.41'
            ])))
            headers.append(('Server', random.choice([
                'Apache/2.4.41 (Ubuntu)', 'nginx/1.18.0', 'Microsoft-IIS/10.0'
            ])))

        # Log routing decision

        logger.info(
            f"{'' if classification['is_malicious'] else ''} "
            f"{ip} → {target_label} :{target_port} | "
            f"{request.method} /{path} | "
            f"conf={classification['confidence']:.2f} "
            f"method={classification['method']} "
            f"types={classification.get('attack_types', [])}"
        )

        return Response(resp.content, resp.status_code, headers)

    except requests.exceptions.ConnectionError:
        return jsonify({
            'error': f'Target site {target_site} not reachable on port {target_port}',
            'hint': 'Run websites/run_all.py first'
        }), 502
    except Exception as e:
        logger.exception("Proxy forwarding error")  # (#5) log real error
        return jsonify({'error': 'Internal proxy error'}), 500  # (#5) sanitized

@app.route('/')
def index():
    """Proxy landing page / API info."""
    return jsonify({
        'name': 'AI-Driven Cyber Defense Routing Proxy',
        'version': '1.0.0',
        'description': 'Classifies incoming traffic and routes malicious requests to honeypots',
        'routes': {
            '/<site>/...': 'Proxy to site (banking, ecommerce, healthcare, blog, api_service, corporate, admin_panel)',
            '/proxy/status': 'Proxy status and attacker stats',
            '/proxy/attacks': 'Recent attack logs',
            '/proxy/config': 'Proxy configuration',
        },
        'current_rotation': current_rotation['site'],
        'available_sites': list(SITE_MAP.keys()),
        'status': 'active',
        'timestamp': datetime.now().isoformat()
    })

# STARTUP

if __name__ == '__main__':
    print("  AI-DRIVEN ROUTING PROXY")
    print(f"  ML API:    {ML_API_URL}")
    print(f"  Rotation:  every {ROTATION_INTERVAL}s")
    print(f"  Sites:     {', '.join(SITE_MAP.keys())}")
    print(f"  Proxy:     http://localhost:{PROXY_PORT}")
    print()
    print("  Usage:")
    print("    Benign:  curl http://localhost:8080/banking/")
    print("    SQLi:    curl 'http://localhost:8080/banking/search?q=1+OR+1%3D1--'")
    print("    XSS:     curl 'http://localhost:8080/ecommerce/search?q=<script>alert(1)</script>'")
    print()

    # Start rotation thread

    rotation_thread = threading.Thread(target=rotate_services, daemon=True)
    rotation_thread.start()

    # Run with threading enabled to handle concurrent requests

    # Critical: LLM requests take time (30s+), so we must not block benign traffic

    app.run(host='0.0.0.0', port=PROXY_PORT, debug=False, threaded=True)
