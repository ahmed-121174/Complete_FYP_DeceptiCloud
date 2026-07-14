

import json
import time
import hashlib
import random
import string
from pathlib import Path
from datetime import datetime
from flask import Blueprint, request, jsonify, Response
import logging

logger = logging.getLogger('canary_tokens')

# CONFIGURATION

CANARY_LOG_FILE = Path(__file__).parent.parent / 'logs' / 'canary_alerts.jsonl'
CANARY_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# In-memory alert counter

canary_stats = {
    'total_triggers': 0,
    'by_type': {},
    'recent_alerts': [],
}

# (#14) Reconstruct stats from log file on startup

def _reconstruct_stats():
    """Load historical canary stats from the JSONL log file."""
    if not CANARY_LOG_FILE.exists():
        return
    try:
        with open(CANARY_LOG_FILE, 'r') as f:
            for line in f:
                try:
                    alert = json.loads(line)
                    token_type = alert.get('token_type', 'unknown')
                    canary_stats['total_triggers'] += 1
                    canary_stats['by_type'][token_type] = canary_stats['by_type'].get(token_type, 0) + 1
                    canary_stats['recent_alerts'].append(alert)
                except (json.JSONDecodeError, KeyError):
                    pass
        # Keep only last 100 in memory

        canary_stats['recent_alerts'] = canary_stats['recent_alerts'][-100:]
        if canary_stats['total_triggers'] > 0:
            logger.info(f" Reconstructed {canary_stats['total_triggers']} canary alerts from log")
    except Exception as e:
        logger.warning(f"Could not reconstruct canary stats: {e}")

_reconstruct_stats()

# CANARY ALERT LOGGING

def log_canary_alert(token_type, details, req):
    """Log a canary token trigger event."""
    alert = {
        'timestamp': datetime.now().isoformat(),
        'token_type': token_type,
        'attacker_ip': req.remote_addr,
        'user_agent': req.headers.get('User-Agent', ''),
        'method': req.method,
        'path': req.path,
        'query': req.query_string.decode('utf-8', errors='replace'),
        'referer': req.headers.get('Referer', ''),
        'details': details,
    }
    
    # Write to file

    with open(CANARY_LOG_FILE, 'a') as f:
        f.write(json.dumps(alert) + '\n')
    
    # Update in-memory stats

    canary_stats['total_triggers'] += 1
    canary_stats['by_type'][token_type] = canary_stats['by_type'].get(token_type, 0) + 1
    canary_stats['recent_alerts'].append(alert)
    # Keep last 100 alerts in memory

    if len(canary_stats['recent_alerts']) > 100:
        canary_stats['recent_alerts'] = canary_stats['recent_alerts'][-100:]
    
    logger.warning(f" CANARY TRIGGERED: {token_type} by {req.remote_addr} at {req.path}")
    return alert

# FAKE DATA GENERATORS

def generate_fake_aws_key():
    """Generate a realistic-looking (but fake) AWS access key."""
    key_id = 'AKIA' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
    secret = ''.join(random.choices(string.ascii_letters + string.digits + '+/', k=40))
    return key_id, secret

def generate_fake_db_dump():
    """Generate a realistic-looking SQL dump with watermarked fake data."""
    watermark = hashlib.md5(f"CANARY-{time.time()}".encode()).hexdigest()[:8]
    names = [
        ('John', 'Smith', f'john.smith{watermark[:4]}@example.com'),
        ('Alice', 'Johnson', f'alice.j{watermark[4:]}@corporate.net'),
        ('Robert', 'Williams', f'r.williams@enterprise-{watermark}.com'),
        ('Sarah', 'Brown', f'sarah.b{watermark[:3]}@finance.org'),
        ('Michael', 'Davis', f'mdavis.{watermark}@admin.local'),
    ]
    
    dump = f"""-- MySQL dump 10.13  Distrib 8.0.32, for Linux (x86_64)
-- Host: db-prod-master-01.internal    Database: users_production
-- Server version   8.0.32-0ubuntu0.22.04.1
-- Watermark: {watermark}

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(64) NOT NULL,
  `email` varchar(128) NOT NULL,
  `password_hash` varchar(256) NOT NULL,
  `role` enum('user','admin','superadmin') DEFAULT 'user',
  `api_key` varchar(64) DEFAULT NULL,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `users`
--

INSERT INTO `users` VALUES
"""
    for i, (first, last, email) in enumerate(names, 1):
        fake_hash = hashlib.sha256(f"canary_{first}_{watermark}".encode()).hexdigest()
        fake_api = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        role = 'superadmin' if i == 1 else ('admin' if i == 2 else 'user')
        dump += f"({i},'{first.lower()}.{last.lower()}','{email}','{fake_hash}','{role}','sk_{fake_api}','2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}'),\n"
    
    dump += """
-- Table structure for table `api_tokens`
--

DROP TABLE IF EXISTS `api_tokens`;
CREATE TABLE `api_tokens` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `token` varchar(128) NOT NULL,
  `permissions` json DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `api_tokens` VALUES
"""
    for i in range(1, 6):
        fake_token = ''.join(random.choices(string.ascii_letters + string.digits, k=48))
        dump += f"({i},{i},'tok_{fake_token}','{{\"read\": true, \"write\": true, \"admin\": true}}'),\n"
    
    dump += "\n-- Dump completed\n"
    return dump

def generate_fake_env():
    """Generate a realistic .env file with fake credentials."""
    aws_key, aws_secret = generate_fake_aws_key()
    db_pass = ''.join(random.choices(string.ascii_letters + string.digits, k=24))
    jwt_secret = ''.join(random.choices(string.ascii_letters + string.digits, k=48))
    stripe_key = 'sk_live_' + ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    
    return f"""# Production Environment Configuration
# WARNING: Do not commit this file!


NODE_ENV=production
PORT=3000

# Database

DB_HOST=db-prod-master-01.internal
DB_PORT=3306
DB_NAME=users_production
DB_USER=app_service
DB_PASSWORD={db_pass}
DB_SSL=true

# AWS Credentials

AWS_ACCESS_KEY_ID={aws_key}
AWS_SECRET_ACCESS_KEY={aws_secret}
AWS_REGION=us-east-1
AWS_S3_BUCKET=prod-user-uploads

# JWT Authentication

JWT_SECRET={jwt_secret}
JWT_EXPIRY=24h

# Stripe Payment

STRIPE_SECRET_KEY={stripe_key}
STRIPE_WEBHOOK_SECRET=whsec_{''.join(random.choices(string.ascii_letters + string.digits, k=32))}

# Redis Cache

REDIS_URL=redis://cache-prod-01.internal:6379/0
REDIS_PASSWORD={''.join(random.choices(string.ascii_letters + string.digits, k=16))}

# SMTP Email

SMTP_HOST=smtp.sendgrid.net
SMTP_USER=apikey
SMTP_PASSWORD=SG.{''.join(random.choices(string.ascii_letters + string.digits, k=40))}

# Internal API Keys

INTERNAL_API_KEY=ikey_{''.join(random.choices(string.ascii_letters + string.digits, k=32))}
ADMIN_SECRET={''.join(random.choices(string.ascii_letters + string.digits, k=24))}
"""

# FLASK BLUEPRINT — Canary Token Routes

canary_bp = Blueprint('canary_tokens', __name__)

@canary_bp.route('/robots.txt')
def robots_txt():
    """Serve a robots.txt that reveals 'hidden' sensitive paths."""
    log_canary_alert('robots_txt', {
        'description': 'Attacker accessed robots.txt to discover hidden paths'
    }, request)
    
    content = """# Robots.txt — Please do not crawl these sensitive directories
User-agent: *
Disallow: /admin/
Disallow: /backup/
Disallow: /api/v2/internal/
Disallow: /uploads/private/
Disallow: /config/
Disallow: /.env
Disallow: /database/
Disallow: /wp-admin/
Disallow: /phpmyadmin/
Disallow: /server-status
Disallow: /debug/
Disallow: /api/v2/config
"""
    return Response(content, mimetype='text/plain')

@canary_bp.route('/.env')
@canary_bp.route('/env')
@canary_bp.route('/.env.production')
@canary_bp.route('/.env.local')
def fake_env():
    """Serve a fake .env file with decoy credentials."""
    log_canary_alert('env_file', {
        'description': 'Attacker accessed environment file with fake credentials',
        'severity': 'CRITICAL',
    }, request)
    return Response(generate_fake_env(), mimetype='text/plain')

@canary_bp.route('/backup.sql')
@canary_bp.route('/backup.sql.gz')
@canary_bp.route('/database/backup.sql')
@canary_bp.route('/db_backup.sql')
@canary_bp.route('/dump.sql')
def fake_backup():
    """Serve a fake database dump with watermarked canary data."""
    log_canary_alert('database_backup', {
        'description': 'Attacker downloaded fake database backup',
        'severity': 'CRITICAL',
    }, request)
    return Response(generate_fake_db_dump(), mimetype='application/sql',
                    headers={'Content-Disposition': 'attachment; filename=backup.sql'})

@canary_bp.route('/wp-admin')
@canary_bp.route('/wp-admin/')
@canary_bp.route('/wp-login.php')
@canary_bp.route('/administrator/')
@canary_bp.route('/admin.php')
def fake_wp_admin():
    """Fake WordPress admin panel — pure canary."""
    log_canary_alert('admin_panel_scan', {
        'description': 'Attacker probing for CMS admin panels',
        'probe_path': request.path,
    }, request)
    return Response("""<!DOCTYPE html>
<html><head><title>WordPress &rsaquo; Log In</title></head>
<body style="background:#f1f1f1;font-family:sans-serif;text-align:center;padding:8% 0">
<h1 style="font-size:20px"><a href="#">Powered by WordPress</a></h1>
<form style="background:#fff;padding:26px 24px;max-width:320px;margin:auto;box-shadow:0 1px 3px rgba(0,0,0,.13);border:1px solid #c3c4c7">
<p><label>Username or Email Address<br><input type="text" name="log" size="20" style="width:100%;padding:4px;font-size:24px;margin:2px 6px 16px 0"></label></p>
<p><label>Password<br><input type="password" name="pwd" size="20" style="width:100%;padding:4px;font-size:24px;margin:2px 6px 16px 0"></label></p>
<p><input type="submit" value="Log In" style="background:#2271b1;color:#fff;border:none;padding:6px 20px;cursor:pointer;font-size:13px"></p>
</form></body></html>""", mimetype='text/html')

@canary_bp.route('/phpmyadmin/')
@canary_bp.route('/phpmyadmin')
@canary_bp.route('/pma/')
@canary_bp.route('/myadmin/')
def fake_phpmyadmin():
    """Fake phpMyAdmin page."""
    log_canary_alert('phpmyadmin_scan', {
        'description': 'Attacker scanning for phpMyAdmin',
        'probe_path': request.path,
    }, request)
    return Response("""<!DOCTYPE html>
<html><head><title>phpMyAdmin</title></head>
<body style="background:#e7e7e7;font-family:sans-serif;text-align:center;padding:5% 0">
<h1>phpMyAdmin 5.2.1</h1>
<form style="background:#fff;padding:20px;max-width:400px;margin:auto;border:1px solid #ccc">
<p>Username: <input type="text" name="pma_username" style="width:100%;padding:5px;margin:5px 0"></p>
<p>Password: <input type="password" name="pma_password" style="width:100%;padding:5px;margin:5px 0"></p>
<select style="width:100%;padding:5px;margin:5px 0"><option>MySQL</option></select>
<p><input type="submit" value="Go" style="background:#4c9900;color:#fff;padding:5px 20px;border:none;cursor:pointer"></p>
</form></body></html>""", mimetype='text/html')

@canary_bp.route('/api/v2/config')
@canary_bp.route('/api/v2/internal/config')
@canary_bp.route('/api/config')
@canary_bp.route('/config.json')
def fake_api_config():
    """Serve fake API configuration with decoy keys."""
    aws_key, aws_secret = generate_fake_aws_key()
    log_canary_alert('api_config', {
        'description': 'Attacker accessed fake API configuration endpoint',
        'severity': 'HIGH',
    }, request)
    return jsonify({
        'version': '2.1.0',
        'environment': 'production',
        'debug': True,
        'database': {
            'host': 'db-prod-master-01.internal',
            'port': 3306,
            'name': 'users_production',
            'username': 'app_service',
            'password': ''.join(random.choices(string.ascii_letters + string.digits, k=20)),
        },
        'aws': {
            'access_key_id': aws_key,
            'secret_access_key': aws_secret,
            'region': 'us-east-1',
        },
        'jwt_secret': ''.join(random.choices(string.ascii_letters + string.digits, k=48)),
        'api_keys': {
            'internal': 'ikey_' + ''.join(random.choices(string.ascii_letters + string.digits, k=32)),
            'stripe': 'sk_live_' + ''.join(random.choices(string.ascii_letters + string.digits, k=32)),
        },
        'endpoints': {
            'users_service': 'http://users-svc.internal:8081',
            'payment_service': 'http://payments-svc.internal:8082',
            'notification_service': 'http://notify-svc.internal:8083',
        }
    })

@canary_bp.route('/server-status')
@canary_bp.route('/server-info')
def fake_server_status():
    """Fake Apache server-status page."""
    log_canary_alert('server_status', {
        'description': 'Attacker accessed server status page',
    }, request)
    return Response(f"""<!DOCTYPE html>
<html><head><title>Apache Status</title></head>
<body><h1>Apache Server Status for localhost (via ::1)</h1>
<p>Server Version: Apache/2.4.41 (Ubuntu) OpenSSL/1.1.1f</p>
<p>Current Time: {datetime.now().strftime('%A, %d-%b-%Y %H:%M:%S UTC')}</p>
<p>Server uptime: 47 days 3 hours 22 minutes</p>
<p>Total accesses: 1482930 - Total Traffic: 2.8 GB</p>
<p>CPU Usage: u3.72 s1.21 cu0 cs0 - .00112% CPU load</p>
<p>3.41 requests/sec - 1842 B/second - 540 B/request</p>
<p>14 requests currently being processed, 11 idle workers</p>
</body></html>""", mimetype='text/html')

@canary_bp.route('/debug/')
@canary_bp.route('/debug/vars')
@canary_bp.route('/debug/pprof/')
def fake_debug():
    """Fake debug endpoint."""
    log_canary_alert('debug_endpoint', {
        'description': 'Attacker probing debug endpoints',
    }, request)
    return jsonify({
        'runtime': {'goroutines': 42, 'threads': 8},
        'memstats': {'alloc': '48.2 MB', 'sys': '128.4 MB'},
        'build': {'version': 'go1.21.4', 'commit': 'a1b2c3d4'},
        'config_path': '/etc/app/production.yaml',
    })

# ACTIVE DEFENSE: EICAR SCARE TACTIC

@canary_bp.route('/download/confidential_keys.txt')
@canary_bp.route('/keys.txt')
def fake_eicar_scare():
    """Serve the EICAR test string to trigger attacker's antivirus."""
    log_canary_alert('eicar_scare', {
        'description': 'Attacker downloaded fake keys containing EICAR test string',
        'severity': 'CRITICAL',
    }, request)
    
    # Standard EICAR string (harmless but flagged by AVs)
    eicar = r"X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    return Response(eicar, mimetype='text/plain', 
                    headers={'Content-Disposition': 'attachment; filename="confidential_keys.txt"'})

# ACTIVE DEFENSE: ZIP BOMB (Decompression Bomb)

@canary_bp.route('/backup/database_full_2026.zip')
@canary_bp.route('/db.zip')
@canary_bp.route('/backup.zip')
@canary_bp.route('/backup/full_backup.zip')
@canary_bp.route('/data/export.zip')
@canary_bp.route('/credentials.zip')
@canary_bp.route('/users_dump.zip')
@canary_bp.route('/user_data.zip')
@canary_bp.route('/database_backup.zip')
@canary_bp.route('/private/data.zip')
def fake_zip_bomb():
    """Serve a Zip Bomb (2.9 KB → 10 TB) to crash automated scanners.
    
    Uses non-recursive overlapping data technique (David Fifield, 2019).
    10 entries × 1 TB each = 10 TB advertised. File is only ~3 KB.
    """
    log_canary_alert('zip_bomb_download', {
        'description': 'Attacker downloaded ZIP Bomb decompression trap',
        'severity': 'CRITICAL',
        'file_served': 'database_full_2026.zip',
        'actual_size_kb': 2.9,
        'claimed_size_tb': 10,
        'technique': 'Non-recursive overlapping entries (Fifield 2019)',
        'effect': 'Extraction attempt will consume 10TB of disk space',
    }, request)

    bomb_path = Path(__file__).parent.parent / 'assets' / '10TB_bomb.zip'
    if bomb_path.exists():
        with open(bomb_path, 'rb') as f:
            data = f.read()
        logger.warning(
            f"[ZIP BOMB] Delivered to {request.remote_addr} | "
            f"File: {len(data)/1024:.1f}KB → 10TB on extraction"
        )
        return Response(
            data,
            mimetype='application/zip',
            headers={
                'Content-Disposition': 'attachment; filename="database_full_2026.zip"',
                'Content-Length': str(len(data)),
                'X-Archive-Type': 'database-backup',   # deceptive header
            }
        )
    else:
        # Fallback: return a minimal valid zip with a misleading message
        logger.error(f"[ZIP BOMB] Asset missing! Run: python3 assets/create_zipbomb.py")
        return Response("Archive corrupted — contact admin", status=500)


# Tracking pixel (1x1 transparent PNG)

TRACKING_PIXEL = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
    b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
    b'\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
    b'\r\n\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
)

@canary_bp.route('/pixel.png')
@canary_bp.route('/analytics.png')
@canary_bp.route('/t.gif')
def tracking_pixel():
    """Serve a 1x1 tracking pixel that logs access."""
    log_canary_alert('tracking_pixel', {
        'description': 'Tracking pixel accessed (possibly from a cached/stolen page)',
    }, request)
    return Response(TRACKING_PIXEL, mimetype='image/png',
                    headers={'Cache-Control': 'no-store, no-cache'})

@canary_bp.route('/.git/config')
@canary_bp.route('/.git/HEAD')
@canary_bp.route('/.gitignore')
def fake_git():
    """Fake git config exposure."""
    log_canary_alert('git_exposure', {
        'description': 'Attacker scanning for exposed git repositories',
        'severity': 'HIGH',
    }, request)
    if 'config' in request.path:
        return Response("""[core]
    repositoryformatversion = 0
    filemode = true
    bare = false
    logallrefupdates = true
[remote "origin"]
    url = git@github.com:internal-corp/production-app.git
    fetch = +refs/heads/*:refs/remotes/origin/*
[branch "main"]
    remote = origin
    merge = refs/heads/main
""", mimetype='text/plain')
    elif 'HEAD' in request.path:
        return Response("ref: refs/heads/main\n", mimetype='text/plain')
    else:
        return Response("""# .gitignore
.env
.env.local
.env.production
*.key
*.pem
backup.sql
config/secrets.yml
node_modules/
""", mimetype='text/plain')

# CANARY STATS API (for Dashboard integration)

@canary_bp.route('/api/canary-stats')
def get_canary_stats():
    """Return canary token trigger statistics."""
    return jsonify({
        'total_triggers': canary_stats['total_triggers'],
        'by_type': canary_stats['by_type'],
        'recent_alerts': canary_stats['recent_alerts'][-20:],
        'timestamp': datetime.now().isoformat(),
    })
