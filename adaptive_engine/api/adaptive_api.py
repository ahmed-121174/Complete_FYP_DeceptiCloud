from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import sys
import json
import time
import requests as _requests
import urllib3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from database.db_service import get_db_service

adaptive_bp = Blueprint('adaptive', __name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Wazuh credentials (same as wazuh_consumer.py)
WAZUH_API   = 'https://localhost:55000'
WAZUH_USER  = 'wazuh-wui'
WAZUH_PASS  = 'MyS3cr37P450r.*-'
_wazuh_token      = None
_wazuh_token_exp  = 0

def _wazuh_auth() -> str | None:
    global _wazuh_token, _wazuh_token_exp
    if _wazuh_token and time.time() < _wazuh_token_exp:
        return _wazuh_token
    try:
        r = _requests.get(
            f'{WAZUH_API}/security/user/authenticate',
            auth=(WAZUH_USER, WAZUH_PASS),
            verify=False, timeout=5
        )
        if r.status_code == 200:
            _wazuh_token = r.json()['data']['token']
            _wazuh_token_exp = time.time() + 840
            return _wazuh_token
    except Exception:
        pass
    return None

def _wazuh_headers() -> dict:
    token = _wazuh_auth()
    return {'Authorization': f'Bearer {token}'} if token else {}

def _wazuh_live_count() -> int:
    """Get live Wazuh alert count directly from API."""
    try:
        r = _requests.get(
            f'{WAZUH_API}/manager/stats',
            headers=_wazuh_headers(), verify=False, timeout=4
        )
        if r.status_code == 200:
            data = r.json().get('data', {}).get('affected_items', [{}])[0]
            return data.get('totalAlerts', 0)
    except Exception:
        pass
    return 0

# Read engine state from file (engine runs in separate process)
STATE_FILE = Path(__file__).parent.parent / 'engine_state.json'

SITE_PORT_MAP = {
    'banking':     {'real': 3001, 'honeypot': 4001},
    'ecommerce':   {'real': 3002, 'honeypot': 4002},
    'healthcare':  {'real': 3003, 'honeypot': 4003},
    'blog':        {'real': 3004, 'honeypot': 4004},
    'api_service': {'real': 3005, 'honeypot': 4005},
    'corporate':   {'real': 3006, 'honeypot': 4006},
    'admin_panel': {'real': 3007, 'honeypot': 4007},
}

def _get_engine_state():
    """Read engine state from file instead of accessing running engine"""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {
        'running': False,
        'started_at': None,
        'wazuh_alerts_ingested': 0,
        'retraining_runs': 0,
        'profiles_updated': 0,
        'drift_events': 0,
        'last_retrain': {},
        'last_drift_check': None,
        'last_profile_update': None,
        'model_versions': {},
    }


# ── Engine status ─────────────────────────────────────────────────────────
@adaptive_bp.route('/api/adaptive/status', methods=['GET'])
def ale_status():
    try:
        state = _get_engine_state()
        db = get_db_service()
        with db.get_connection() as conn:
            training_count = conn.execute('SELECT COUNT(*) as c FROM training_data').fetchone()['c']
            wazuh_count    = conn.execute('SELECT COUNT(*) as c FROM wazuh_alerts').fetchone()['c']
            # Count retraining runs: non-seeded model versions per type
            retrain_runs   = conn.execute(
                "SELECT COUNT(*) as c FROM ml_models WHERE version NOT LIKE '1.0.4%'"
            ).fetchone()['c']
            profiles_count = conn.execute(
                'SELECT COUNT(*) as c FROM attacker_profiles'
            ).fetchone()['c']

        state['training_data_count']  = training_count
        state['wazuh_alerts_count']   = wazuh_count
        state['retraining_runs']      = retrain_runs + state.get('retraining_runs', 0)
        state['profiles_updated']     = profiles_count
        state['running'] = STATE_FILE.exists() and state.get('started_at') is not None
        return jsonify(state)
    except Exception as e:
        return jsonify({'error': str(e), 'running': False}), 500


# ── Drift report ──────────────────────────────────────────────────────────
@adaptive_bp.route('/api/adaptive/drift', methods=['GET'])
def ale_drift():
    try:
        # Read drift data from database events
        db = get_db_service()
        with db.get_connection() as conn:
            drift_events = conn.execute("""
                SELECT * FROM events 
                WHERE event_type = 'ml' AND source LIKE '%drift%'
                ORDER BY timestamp DESC LIMIT 10
            """).fetchall()
        
        return jsonify({
            'drift_events': [dict(e) for e in drift_events],
            'has_drift': len(drift_events) > 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Manual retrain ────────────────────────────────────────────────────────
@adaptive_bp.route('/api/adaptive/retrain', methods=['POST'])
def ale_retrain():
    data = request.get_json(silent=True) or {}
    attack_type = data.get('attack_type')
    if not attack_type:
        return jsonify({'error': 'attack_type required'}), 400
    try:
        # Trigger retrain by writing to a command file that engine monitors
        cmd_file = Path(__file__).parent.parent / 'retrain_command.json'
        cmd_file.write_text(json.dumps({
            'command': 'retrain',
            'attack_type': attack_type,
            'timestamp': datetime.utcnow().isoformat()
        }))
        # Directly increment retraining_runs in engine_state so dashboard updates immediately
        try:
            state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}
            state['retraining_runs'] = state.get('retraining_runs', 0) + 1
            state['last_retrain'] = state.get('last_retrain', {})
            state['last_retrain'][attack_type] = datetime.utcnow().isoformat()
            STATE_FILE.write_text(json.dumps(state, indent=2))
        except Exception:
            pass
        return jsonify({'status': 'retrain_queued', 'attack_type': attack_type})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Rollback ──────────────────────────────────────────────────────────────
@adaptive_bp.route('/api/adaptive/rollback', methods=['POST'])
def ale_rollback():
    data = request.get_json(silent=True) or {}
    attack_type = data.get('attack_type')
    if not attack_type:
        return jsonify({'error': 'attack_type required'}), 400
    try:
        # Trigger rollback by writing to a command file that engine monitors
        cmd_file = Path(__file__).parent.parent / 'rollback_command.json'
        cmd_file.write_text(json.dumps({
            'command': 'rollback',
            'attack_type': attack_type,
            'timestamp': datetime.utcnow().isoformat()
        }))
        return jsonify({'status': 'rollback_queued', 'attack_type': attack_type})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Attacker comparison ───────────────────────────────────────────────────
@adaptive_bp.route('/api/adaptive/compare', methods=['POST'])
def ale_compare():
    data = request.get_json(silent=True) or {}
    ip1 = data.get('ip1')
    ip2 = data.get('ip2')
    if not ip1 or not ip2:
        return jsonify({'error': 'ip1 and ip2 required'}), 400
    try:
        # Compare attackers using database data
        db = get_db_service()
        with db.get_connection() as conn:
            profile1 = conn.execute("SELECT * FROM attacker_profiles WHERE ip_address=?", (ip1,)).fetchone()
            profile2 = conn.execute("SELECT * FROM attacker_profiles WHERE ip_address=?", (ip2,)).fetchone()
            
            if not profile1 or not profile2:
                return jsonify({'error': 'One or both IPs not found'}), 404
            
            return jsonify({
                'ip1': dict(profile1),
                'ip2': dict(profile2),
                'similarity': 'same_cluster' if profile1['cluster_id'] == profile2['cluster_id'] else 'different_cluster'
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Cluster summary ───────────────────────────────────────────────────────
@adaptive_bp.route('/api/adaptive/clusters', methods=['GET'])
def ale_clusters():
    try:
        # Get cluster summary from database
        db = get_db_service()
        with db.get_connection() as conn:
            clusters = conn.execute("""
                SELECT cluster_id, COUNT(*) as member_count,
                       GROUP_CONCAT(DISTINCT attack_types_json) as attack_types
                FROM attacker_profiles
                WHERE cluster_id >= 0
                GROUP BY cluster_id
                ORDER BY member_count DESC
            """).fetchall()
            
            return jsonify({
                'clusters': [dict(c) for c in clusters],
                'total_clusters': len(clusters)
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Training data stats ───────────────────────────────────────────────────
@adaptive_bp.route('/api/adaptive/training-stats', methods=['GET'])
def ale_training_stats():
    try:
        db = get_db_service()
        with db.get_connection() as conn:
            total    = conn.execute('SELECT COUNT(*) as n FROM training_data').fetchone()['n']
            unused   = conn.execute('SELECT COUNT(*) as n FROM training_data WHERE used_in_training=0').fetchone()['n']
            by_type  = conn.execute("""
                SELECT attack_type, COUNT(*) as n, AVG(confidence) as avg_conf
                FROM training_data GROUP BY attack_type ORDER BY n DESC
            """).fetchall()
            wazuh_total = conn.execute('SELECT COUNT(*) as n FROM wazuh_alerts').fetchone()['n']
            wazuh_unproc = conn.execute('SELECT COUNT(*) as n FROM wazuh_alerts WHERE processed=0').fetchone()['n']
            # Also get attacks table counts — every captured attack is a usable sample
            attacks_total = conn.execute(
                'SELECT COUNT(*) as n FROM attacks WHERE captured=1 AND attack_type IS NOT NULL AND attack_type != "Unknown"'
            ).fetchone()['n']
            attack_types = conn.execute("""
                SELECT attack_type, COUNT(*) as n, AVG(confidence) as avg_conf
                FROM attacks
                WHERE attack_type IS NOT NULL AND attack_type != ''
                  AND attack_type != 'Unknown' AND confidence > 0
                GROUP BY attack_type ORDER BY n DESC LIMIT 20
            """).fetchall()

        # Use the larger of training_data or attacks as total_samples
        effective_total = max(total, attacks_total)
        # unused_samples = unprocessed training_data rows (not all attacks)
        effective_unused = unused

        # Build breakdown primarily from attacks table (high-quality data with proper confidence)
        # training_data entries are supplementary; attacks table takes priority
        type_map = {}
        for r in attack_types:
            t = r['attack_type'] or 'Unknown'
            if t == 'Unknown':
                continue
            avg = r['avg_conf'] or 0
            if avg > 0:
                type_map[t] = {'type': t, 'count': r['n'], 'avg_confidence': round(avg, 3)}
        # Add any training_data types not already covered by attacks table
        for r in by_type:
            t = r['attack_type'] or 'Unknown'
            if t == 'Unknown' or t in type_map:
                continue
            avg = r['avg_conf'] or 0
            if avg >= 0.5:  # Only add training_data entries with reasonable confidence
                type_map[t] = {'type': t, 'count': r['n'], 'avg_confidence': round(avg, 3)}

        # Try to get live Wazuh count
        live_wazuh = _wazuh_live_count()
        if live_wazuh > 0:
            wazuh_total = max(wazuh_total, live_wazuh)

        return jsonify({
            'total_samples':      effective_total,
            'unused_samples':     effective_unused,
            'wazuh_alerts_total': wazuh_total,
            'wazuh_unprocessed':  wazuh_unproc,
            'by_attack_type':     list(type_map.values()),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500



# ── Wazuh alerts feed ─────────────────────────────────────────────────────
@adaptive_bp.route('/api/adaptive/wazuh-alerts', methods=['GET'])
def ale_wazuh_alerts():
    limit = request.args.get('limit', 100, type=int)
    level = request.args.get('min_level', 0, type=int)
    try:
        db = get_db_service()
        with db.get_connection() as conn:
            rows = conn.execute("""
                SELECT id, timestamp, agent_name, rule_id, rule_level,
                       rule_description, ip, processed, alert_json
                FROM wazuh_alerts
                WHERE rule_level >= ?
                ORDER BY timestamp DESC LIMIT ?
            """, (level, limit)).fetchall()
        alerts = []
        for r in rows:
            a = dict(r)
            # Parse the full alert JSON for enriched fields
            try:
                raw = json.loads(a.pop('alert_json') or '{}')
                rule   = raw.get('rule', {})
                data   = raw.get('data', {})
                agent  = raw.get('agent', {})
                a['full_log']        = raw.get('full_log', '')
                a['groups']          = rule.get('groups', [])
                a['decoder_name']    = raw.get('decoder', {}).get('name', '')
                a['mitre_technique'] = rule.get('mitre', {}).get('technique', [])
                a['pci_dss']         = rule.get('pci_dss', [])
                a['gdpr']            = rule.get('gdpr', [])
                a['url']             = data.get('url', data.get('request', ''))
                a['method']          = data.get('method', '')
                a['user_agent']      = data.get('srcuser', data.get('user_agent', ''))
                a['payload']         = data.get('data', data.get('payload', ''))
                a['hostname']        = agent.get('name', a.get('agent_name', ''))
                a['attack_type']     = _infer_attack_type(rule.get('id', 0), rule.get('groups', []))
            except Exception:
                a['full_log'] = ''
                a['groups'] = []
                a['attack_type'] = 'Unknown'
            alerts.append(a)
        return jsonify({'alerts': alerts, 'total': len(alerts)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def _infer_attack_type(rule_id: int, groups: list) -> str:
    RULE_MAP = {
        100001:'SQLi', 100002:'SQLi', 31101:'SQLi',
        100010:'XSS',  100011:'XSS',  31103:'XSS',
        100020:'Path Traversal', 100030:'Command Injection',
        100040:'DDoS', 100041:'DDoS',
        100050:'Brute Force', 100051:'Brute Force',
        5710:'Brute Force', 5712:'Brute Force',
        100060:'Port Scan', 40101:'Port Scan', 40111:'Port Scan',
        100070:'Credential Stuffing',
        100080:'Honeypot Access', 100090:'Canary Token',
        31100:'Web Attack',
    }
    if rule_id in RULE_MAP:
        return RULE_MAP[rule_id]
    grp = ' '.join(groups).lower()
    if 'sql' in grp:    return 'SQLi'
    if 'xss' in grp:    return 'XSS'
    if 'brute' in grp:  return 'Brute Force'
    if 'scan' in grp:   return 'Port Scan'
    if 'web' in grp:    return 'Web Attack'
    return 'Unknown'


# ── Model version history ─────────────────────────────────────────────────
@adaptive_bp.route('/api/adaptive/model-history', methods=['GET'])
def ale_model_history():
    try:
        from database.db_service import get_db_service
        db = get_db_service()
        with db.get_connection() as conn:
            rows = conn.execute("""
                SELECT model_name, model_type, version, accuracy, precision_val,
                       recall_val, f1_score, training_date, training_samples, is_active
                FROM ml_models ORDER BY training_date DESC LIMIT 50
            """).fetchall()
        return jsonify({'models': [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Attacker profiles (enhanced) ──────────────────────────────────────────
@adaptive_bp.route('/api/adaptive/profiles', methods=['GET'])
def ale_profiles():
    limit = request.args.get('limit', 20, type=int)
    try:
        db = get_db_service()
        profiles = db.get_attacker_profiles(limit=limit)
        return jsonify({'profiles': profiles, 'total': len(profiles)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── Live Attack Stream (polls every 3s) ───────────────────────────────────
@adaptive_bp.route('/api/adaptive/live-stream', methods=['GET'])
def ale_live_stream():
    """Real-time attack event feed — last N events from attacks + wazuh_alerts."""
    limit = request.args.get('limit', 50, type=int)
    since = request.args.get('since', None)
    try:
        db = get_db_service()
        with db.get_connection() as conn:
            # NOTE: attacks table has no 'severity', 'honeypot_name', 'body' columns
            if since:
                rows = conn.execute("""
                    SELECT timestamp, ip, attack_type, confidence,
                           path, method, user_agent, payload, routed_to, target_site
                    FROM attacks
                    WHERE timestamp > ?
                      AND attack_type IS NOT NULL AND attack_type != 'Unknown'
                      AND confidence > 0
                    ORDER BY timestamp DESC LIMIT ?
                """, (since, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT timestamp, ip, attack_type, confidence,
                           path, method, user_agent, payload, routed_to, target_site
                    FROM attacks
                    WHERE attack_type IS NOT NULL AND attack_type != 'Unknown'
                      AND confidence > 0
                    ORDER BY timestamp DESC LIMIT ?
                """, (limit,)).fetchall()

            wazuh_rows = conn.execute("""
                SELECT timestamp, ip, rule_description as description,
                       rule_level, agent_name, rule_id
                FROM wazuh_alerts WHERE rule_level >= 3
                ORDER BY timestamp DESC LIMIT ?
            """, (min(limit, 20),)).fetchall()

        events = []
        for r in rows:
            d = dict(r)
            d['source'] = 'proxy'
            d['honeypot_name'] = d.get('target_site') or 'Honeypot Proxy'
            d['is_honeypot'] = bool(d.get('routed_to', '').startswith('honeypot'))
            d['severity'] = 'critical' if (d.get('confidence') or 0) > 0.8 else (
                'high' if (d.get('confidence') or 0) > 0.5 else 'medium')
            events.append(d)

        for r in wazuh_rows:
            d = dict(r)
            d['source']      = 'wazuh'
            d['attack_type'] = 'Wazuh Alert'
            d['severity']    = 'high' if d['rule_level'] >= 10 else ('medium' if d['rule_level'] >= 7 else 'low')
            d['is_honeypot'] = False
            d['honeypot_name'] = d.get('agent_name', '—')
            events.append(d)

        events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        latest_ts = events[0]['timestamp'] if events else None
        return jsonify({'events': events[:limit], 'total': len(events), 'latest_ts': latest_ts})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Active Attacker Session Card (refreshes every 5s) ─────────────────────
@adaptive_bp.route('/api/adaptive/active-attacker', methods=['GET'])
def ale_active_attacker():
    """Most recent active attacker's full enriched profile."""
    try:
        db = get_db_service()
        with db.get_connection() as conn:
            cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            # NOTE: attacks table has no severity/honeypot_name/body columns
            # Prefer the most recent *classified* attack (confidence > 0, type known)
            recent = conn.execute("""
                SELECT ip, attack_type, confidence, path, method,
                       user_agent, payload, routed_to, target_site, timestamp,
                       query_string
                FROM attacks
                WHERE timestamp > ?
                  AND attack_type IS NOT NULL AND attack_type != 'Unknown'
                  AND confidence > 0
                ORDER BY timestamp DESC LIMIT 1
            """, (cutoff,)).fetchone()

            # Fallback: any recent attack if no classified one exists
            if not recent:
                recent = conn.execute("""
                    SELECT ip, attack_type, confidence, path, method,
                           user_agent, payload, routed_to, target_site, timestamp,
                           query_string
                    FROM attacks WHERE timestamp > ?
                    ORDER BY timestamp DESC LIMIT 1
                """, (cutoff,)).fetchone()

            if not recent:
                return jsonify({'active': False})

            ip = recent['ip']
            # attacker_profiles uses column 'ip', not 'ip_address'
            profile = conn.execute(
                'SELECT * FROM attacker_profiles WHERE ip=?', (ip,)
            ).fetchone()

            session_attacks = conn.execute("""
                SELECT attack_type, payload, path, method, user_agent,
                       query_string, timestamp, routed_to, target_site, confidence
                FROM attacks WHERE ip=? AND timestamp > ?
                  AND attack_type IS NOT NULL AND attack_type != 'Unknown'
                ORDER BY timestamp DESC LIMIT 30
            """, (ip, cutoff)).fetchall()

            canary = conn.execute(
                'SELECT COUNT(*) as n, MAX(timestamp) as last FROM canary_triggers WHERE ip=?', (ip,)
            ).fetchone()

            wazuh = conn.execute("""
                SELECT rule_description, rule_level, agent_name, rule_id, timestamp
                FROM wazuh_alerts WHERE ip=? ORDER BY timestamp DESC LIMIT 5
            """, (ip,)).fetchall()


        payloads, commands = [], []
        for a in session_attacks:
            if a['payload']:
                payloads.append(a['payload'][:200])
            ts_str = a['timestamp'][11:19] if a['timestamp'] else ''
            ts_prefix = f"[{ts_str}] " if ts_str else ""
            if a['query_string']:
                commands.append(f"{ts_prefix}{a['method']} {a['path']}?{a['query_string'][:120]}")
            elif a['path']:
                commands.append(f"{ts_prefix}{a['method']} {a['path']}")

        prof = dict(profile) if profile else {}
        try:
            prof['attack_types_list'] = json.loads(prof.get('attack_types_json', '[]'))
            prof['tools_list']        = json.loads(prof.get('tools_detected_json', prof.get('tools_json', '[]')))
        except Exception:
            prof['attack_types_list'] = []
            prof['tools_list']        = []

        ts_list = [a['timestamp'] for a in session_attacks if a['timestamp']]
        session_dur = 0
        if len(ts_list) >= 2:
            try:
                t1 = datetime.fromisoformat(ts_list[-1][:19])
                t2 = datetime.fromisoformat(ts_list[0][:19])
                session_dur = int((t2 - t1).total_seconds())
            except Exception:
                pass

        conf = recent['confidence'] or 0
        severity = 'critical' if conf > 0.8 else ('high' if conf > 0.5 else 'medium')

        return jsonify({
            'active':           True,
            'ip':               ip,
            'last_seen':        recent['timestamp'],
            'attack_type':      recent['attack_type'],
            'severity':         severity,
            'confidence':       conf,
            'is_honeypot':      bool(recent['routed_to'] and recent['routed_to'].startswith('honeypot')),
            'honeypot_name':    recent['target_site'] or 'Honeypot Proxy',
            'user_agent':       recent['user_agent'],
            'threat_score':     prof.get('threat_score', round(conf, 2)),
            'attack_count':     len(session_attacks),
            'total_attacks':    prof.get('attack_count', len(session_attacks)),
            'attack_types':     prof.get('attack_types_list', [recent['attack_type']]),
            'tools_detected':   prof.get('tools_list', []),
            'cluster_id':       prof.get('cluster_id'),
            'behavioral_hash':  prof.get('behavioral_hash', ''),
            'canary_triggers':  canary['n'] if canary else 0,
            'canary_last':      canary['last'] if canary else None,
            'wazuh_alerts':     [dict(w) for w in wazuh],
            'session_attacks':  [dict(a) for a in session_attacks[:10]],
            'payloads':         list(dict.fromkeys(payloads))[:10],
            'commands':         list(dict.fromkeys(commands))[:15],
            'session_duration': session_dur,
        })
    except Exception as e:
        return jsonify({'error': str(e), 'active': False}), 500


# ── Known Attacker IPs (for comparison dropdowns) ─────────────────────────
@adaptive_bp.route('/api/adaptive/attacker-ips', methods=['GET'])
def ale_attacker_ips():
    try:
        db = get_db_service()
        with db.get_connection() as conn:
            rows = conn.execute("""
                SELECT ip_address as ip, attack_count, threat_score, cluster_id,
                       last_seen, attack_types_json
                FROM attacker_profiles ORDER BY threat_score DESC LIMIT 100
            """).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d['attack_types'] = json.loads(d.pop('attack_types_json', '[]'))
            except Exception:
                d['attack_types'] = []
            result.append(d)
        return jsonify({'ips': result, 'total': len(result)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Per-Site Logs (14 sites: 7 real + 7 honeypot) ─────────────────────────
@adaptive_bp.route('/api/adaptive/site-logs/<site_name>', methods=['GET'])
def ale_site_logs(site_name):
    """Traffic/attack logs per site, filtered by port or agent name."""
    log_type = request.args.get('type', 'traffic')
    limit    = request.args.get('limit', 100, type=int)
    is_hp    = request.args.get('honeypot', 'false').lower() == 'true'
    try:
        db = get_db_service()
        port_key       = 'honeypot' if is_hp else 'real'
        port           = SITE_PORT_MAP.get(site_name, {}).get(port_key, 0)
        agent_pattern  = f'dc-{"hp" if is_hp else "real"}-{site_name}'

        with db.get_connection() as conn:
            if log_type == 'traffic':
                # Only get logs for the SPECIFIC agent (real OR honeypot, not both)
                wazuh_rows = conn.execute("""
                    SELECT timestamp, ip, rule_description as description,
                           rule_level, agent_name, rule_id, processed
                    FROM wazuh_alerts
                    WHERE agent_name = ?
                    ORDER BY timestamp DESC LIMIT ?
                """, (agent_pattern, limit)).fetchall()

                attack_rows = conn.execute("""
                    SELECT timestamp, ip, attack_type, confidence,
                           path, method, user_agent, routed_to
                    FROM attacks
                    WHERE routed_to LIKE ?
                    ORDER BY timestamp DESC LIMIT ?
                """, (f'%:{port}%', limit)).fetchall()

                return jsonify({
                    'site': site_name, 'is_honeypot': is_hp,
                    'wazuh_logs':  [dict(r) for r in wazuh_rows],
                    'attack_logs': [dict(r) for r in attack_rows],
                    'total':       len(wazuh_rows) + len(attack_rows),
                })

            elif log_type == 'attacks':
                rows = conn.execute("""
                    SELECT timestamp, ip, attack_type, confidence,
                           path, method, user_agent, payload, routed_to
                    FROM attacks
                    WHERE routed_to LIKE ? AND attack_type IS NOT NULL
                    ORDER BY timestamp DESC LIMIT ?
                """, (f'%:{port}%', limit)).fetchall()

                wazuh_attacks = conn.execute("""
                    SELECT timestamp, ip, rule_description, rule_level, agent_name, rule_id
                    FROM wazuh_alerts
                    WHERE agent_name = ? AND rule_level >= 7
                    ORDER BY timestamp DESC LIMIT ?
                """, (agent_pattern, limit)).fetchall()

                return jsonify({
                    'site': site_name, 'is_honeypot': is_hp,
                    'attacks':       [dict(r) for r in rows],
                    'wazuh_attacks': [dict(r) for r in wazuh_attacks],
                    'total':         len(rows) + len(wazuh_attacks),
                })

            elif log_type == 'stats':
                by_type = conn.execute("""
                    SELECT attack_type, COUNT(*) as n FROM attacks
                    WHERE routed_to LIKE ?
                    GROUP BY attack_type ORDER BY n DESC
                """, (f'%:{port}%',)).fetchall()

                by_hour = conn.execute("""
                    SELECT strftime('%H:00', timestamp) as hour, COUNT(*) as n
                    FROM attacks
                    WHERE routed_to LIKE ?
                      AND timestamp > datetime('now', '-24 hours')
                    GROUP BY hour ORDER BY hour
                """, (f'%:{port}%',)).fetchall()

                by_severity = conn.execute("""
                    SELECT rule_level, COUNT(*) as n FROM wazuh_alerts
                    WHERE agent_name = ?
                    GROUP BY rule_level ORDER BY rule_level DESC
                """, (agent_pattern,)).fetchall()

                total = conn.execute("""
                    SELECT COUNT(*) as n FROM attacks
                    WHERE routed_to LIKE ?
                """, (f'%:{port}%',)).fetchone()['n']

                return jsonify({
                    'site': site_name, 'is_honeypot': is_hp,
                    'total_events': total,
                    'by_type':      [dict(r) for r in by_type],
                    'by_hour':      [dict(r) for r in by_hour],
                    'by_severity':  [dict(r) for r in by_severity],
                })

        return jsonify({'error': 'Unknown log_type'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
