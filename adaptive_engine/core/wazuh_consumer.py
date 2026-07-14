#!/usr/bin/env python3
"""
Wazuh Log Consumer
Polls Wazuh API for new alerts, extracts ML features, and stores
them in the training_data table for continuous learning.
"""

import json
import time
import logging
import requests
import urllib3
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from database.db_service import get_db_service

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger('wazuh_consumer')

WAZUH_API   = 'https://localhost:55000'
WAZUH_USER  = 'wazuh-wui'
WAZUH_PASS  = 'MyS3cr37P450r.*-'
POLL_SEC    = 10          # poll every 10 s
BATCH       = 200         # alerts per request

# Rule-level → severity mapping
LEVEL_MAP = {range(0,4):'info', range(4,7):'low', range(7,10):'medium',
             range(10,13):'high', range(13,16):'critical'}

# Rule IDs that map to specific attack types
RULE_ATTACK_MAP = {
    # DeceptiCloud custom rules (100001-100099)
    100001: 'SQLi', 100002: 'SQLi', 100010: 'XSS', 100011: 'XSS',
    100020: 'Path Traversal', 100030: 'Command Injection',
    100040: 'DDoS', 100041: 'DDoS',
    100050: 'Brute Force', 100051: 'Brute Force',
    100060: 'Port Scan', 100070: 'Credential Stuffing',
    100080: 'Honeypot Access', 100090: 'Canary Token',
    # Wazuh built-in rules
    31100: 'Web Attack', 31101: 'SQLi', 31103: 'XSS',
    5710: 'SSH Brute Force', 5712: 'SSH Brute Force',
    40101: 'Port Scan', 40111: 'Port Scan',
}


class WazuhConsumer:
    def __init__(self):
        self.db   = get_db_service()
        self.token = None
        self.token_expiry = 0
        self._last_alert_ts = self._load_cursor()

    # ── Auth ──────────────────────────────────────────────────────────────
    def _auth(self) -> bool:
        try:
            r = requests.post(
                f'{WAZUH_API}/security/user/authenticate',
                auth=(WAZUH_USER, WAZUH_PASS),
                verify=False, timeout=8
            )
            if r.status_code == 200:
                self.token = r.json()['data']['token']
                self.token_expiry = time.time() + 850   # ~14 min
                return True
        except Exception as e:
            logger.warning(f'Wazuh auth failed: {e}')
        return False

    def _headers(self):
        if time.time() > self.token_expiry:
            self._auth()
        return {'Authorization': f'Bearer {self.token}'}

    # ── Cursor persistence ────────────────────────────────────────────────
    def _cursor_path(self):
        return Path(__file__).parent.parent / '.wazuh_cursor'

    def _load_cursor(self) -> str:
        p = self._cursor_path()
        if p.exists():
            return p.read_text().strip()
        # Default: last 24 h
        return (datetime.utcnow() - timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%SZ')

    def _save_cursor(self, ts: str):
        self._cursor_path().write_text(ts)
        self._last_alert_ts = ts

    # ── Fetch alerts ──────────────────────────────────────────────────────
    def fetch_new_alerts(self) -> list:
        """Fetch alerts from Wazuh OpenSearch indexer (wazuh-alerts-* index)."""
        try:
            query = {
                "query": {
                    "range": {
                        "timestamp": {"gt": self._last_alert_ts}
                    }
                },
                "sort": [{"timestamp": {"order": "asc"}}],
                "size": BATCH
            }
            r = requests.post(
                'https://localhost:9200/wazuh-alerts-*/_search',
                auth=('admin', 'SecretPassword1!'),
                json=query,
                verify=False, timeout=10
            )
            if r.status_code == 200:
                hits = r.json().get('hits', {}).get('hits', [])
                return [h['_source'] for h in hits]
        except Exception as e:
            logger.warning(f'Fetch alerts from indexer error: {e}')
        return []

    # ── Feature extraction ────────────────────────────────────────────────
    def extract_features(self, alert: dict) -> dict | None:
        """
        Convert a Wazuh alert into an ML feature vector.
        Returns None if the alert cannot be mapped to a useful feature set.
        """
        rule    = alert.get('rule', {})
        rule_id = int(rule.get('id', 0))
        level   = int(rule.get('level', 0))
        data    = alert.get('data', {})
        agent   = alert.get('agent', {})

        # --- HTTP / web-attack features ---
        url     = data.get('url', data.get('request', ''))
        method  = data.get('method', 'GET').upper()
        ua      = data.get('srcuser', data.get('user_agent', ''))
        src_ip  = data.get('srcip', alert.get('agent', {}).get('ip', ''))
        payload = data.get('data', data.get('payload', ''))
        full    = f'{url} {payload} {ua}'

        import re
        SQLI_RE = re.compile(r"(?i)(union.{0,20}select|'\s*or\s*'|or\s+1=1|--|;select|xp_|exec\(|benchmark\(|sleep\()", re.I)
        XSS_RE  = re.compile(r"(?i)(<script|javascript:|onerror=|onload=|alert\(|document\.cookie)", re.I)
        TRAV_RE = re.compile(r"(\.\./|\.\.\\|%2e%2e|/etc/passwd|/windows/system32)", re.I)

        features = {
            # Request metadata
            'url_length':        len(url),
            'path_length':       len(url.split('?')[0]),
            'query_length':      len(url.split('?')[1]) if '?' in url else 0,
            'body_length':       len(payload),
            'method_is_post':    1 if method == 'POST' else 0,
            'method_is_put':     1 if method == 'PUT' else 0,
            'num_headers':       level,          # proxy for complexity
            'has_auth_header':   0,
            'content_type_json': 0,
            'content_type_form': 0,
            # URL features
            'num_params':        url.count('&') + (1 if '?' in url else 0),
            'num_path_segments': len([s for s in url.split('?')[0].split('/') if s]),
            'has_encoded_chars': 1 if '%' in url else 0,
            'num_special_chars': sum(1 for c in full if c in "'\";<>(){}[]|&`!"),
            'max_param_length':  max((len(v) for v in url.split('&')), default=0),
            # Attack pattern counts
            'sqli_pattern_count':     len(SQLI_RE.findall(full)),
            'nosqli_pattern_count':   1 if any(k in full for k in ['$gt','$lt','$ne','$where']) else 0,
            'xss_pattern_count':      len(XSS_RE.findall(full)),
            'traversal_pattern_count':len(TRAV_RE.findall(full)),
            # Behavioral
            'has_suspicious_ua': 1 if any(t in ua.lower() for t in
                ['sqlmap','nikto','nmap','dirb','burp','curl','wget','python-requests','hydra','masscan']) else 0,
            'ua_length':         len(ua),
            'has_referer':       0,
            'has_cookie':        0,
            # Wazuh-specific
            'rule_level':        level,
            'rule_id':           rule_id,
            'agent_name':        agent.get('name', ''),
            'src_ip':            src_ip,
        }
        return features

    def _severity(self, level: int) -> str:
        for r, s in LEVEL_MAP.items():
            if level in r:
                return s
        return 'info'

    def _attack_type(self, rule_id: int, features: dict) -> str:
        if rule_id in RULE_ATTACK_MAP:
            return RULE_ATTACK_MAP[rule_id]
        # Infer from features
        if features.get('sqli_pattern_count', 0) > 0:   return 'SQLi'
        if features.get('xss_pattern_count', 0) > 0:    return 'XSS'
        if features.get('traversal_pattern_count', 0) > 0: return 'Path Traversal'
        if features.get('has_suspicious_ua'):            return 'Scanner'
        return 'Unknown'

    # ── Ingest pipeline ───────────────────────────────────────────────────
    def ingest_alert(self, alert: dict):
        rule    = alert.get('rule', {})
        rule_id = int(rule.get('id', 0))
        level   = int(rule.get('level', 0))
        ts      = alert.get('timestamp', datetime.utcnow().isoformat())
        data    = alert.get('data', {})
        src_ip  = data.get('srcip', '')

        features = self.extract_features(alert)
        if features is None:
            return

        attack_type = self._attack_type(rule_id, features)
        is_attack   = 1 if level >= 7 or attack_type not in ('Unknown',) else 0
        severity    = self._severity(level)

        # 1. Store raw alert
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO wazuh_alerts
                (timestamp, agent_id, agent_name, rule_id, rule_level,
                 rule_description, alert_json, ip, processed)
                VALUES (?,?,?,?,?,?,?,?,0)
            """, (
                ts,
                alert.get('agent', {}).get('id'),
                alert.get('agent', {}).get('name'),
                rule_id, level,
                rule.get('description', ''),
                json.dumps(alert),
                src_ip
            ))
            conn.commit()

        # 2. Store as training data (only if level >= 5 — meaningful signal)
        if level >= 5:
            with self.db.get_connection() as conn:
                conn.execute("""
                    INSERT INTO training_data
                    (features_json, label, attack_type, confidence, verified, used_in_training)
                    VALUES (?,?,?,?,0,0)
                """, (
                    json.dumps(features),
                    is_attack,
                    attack_type,
                    min(level / 15.0, 1.0)   # normalise level to 0-1 confidence
                ))
                conn.commit()

        # 3. Store system event
        self.db.insert_event({
            'timestamp': ts,
            'event_type': 'wazuh',
            'severity': severity,
            'source': f"wazuh/{alert.get('agent',{}).get('name','manager')}",
            'message': rule.get('description', f'Rule {rule_id}'),
            'details': {
                'rule_id': rule_id, 'rule_level': level,
                'attack_type': attack_type, 'features_extracted': True
            },
            'ip': src_ip
        })

    def run_once(self) -> int:
        """Fetch and ingest one batch. Returns number of alerts processed."""
        alerts = self.fetch_new_alerts()
        if not alerts:
            return 0
        for a in alerts:
            self.ingest_alert(a)
        # Advance cursor to latest timestamp
        latest = max(a.get('timestamp', '') for a in alerts)
        if latest:
            self._save_cursor(latest)
        logger.info(f'Ingested {len(alerts)} Wazuh alerts → training_data')
        return len(alerts)

    def run_forever(self):
        logger.info('Wazuh consumer started')
        while True:
            try:
                n = self.run_once()
                if n:
                    logger.info(f'Processed {n} alerts')
            except Exception as e:
                logger.error(f'Consumer error: {e}')
            time.sleep(POLL_SEC)
