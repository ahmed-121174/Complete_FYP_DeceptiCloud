#!/usr/bin/env python3
"""
Behavioral Comparison & Attacker Profiling Engine
Builds rich attacker profiles from:
  - Attack patterns (type, frequency, timing)
  - Tool signatures (user-agent, payload style)
  - Wazuh alerts (system-level events)
  - Behavioral fingerprints (keystroke, mouse, browser)
  - Cluster membership (DBSCAN across all features)
"""

import json
import hashlib
import logging
import numpy as np
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from database.db_service import get_db_service

logger = logging.getLogger('profiler')

# Threat score weights
W = {
    'attack_count':       0.20,
    'attack_diversity':   0.15,
    'tool_sophistication':0.20,
    'persistence':        0.15,
    'honeypot_depth':     0.10,
    'wazuh_severity':     0.10,
    'canary_triggered':   0.10,
}

TOOL_SCORES = {
    'sqlmap': 0.9, 'nikto': 0.8, 'nmap': 0.7, 'masscan': 0.8,
    'hydra': 0.85, 'medusa': 0.85, 'burp': 0.75, 'zap': 0.7,
    'metasploit': 0.95, 'msfconsole': 0.95, 'curl': 0.3,
    'python-requests': 0.4, 'wget': 0.3, 'go-http': 0.4,
}


class AttackerProfiler:
    def __init__(self):
        self.db = get_db_service()

    # ── Tool detection ────────────────────────────────────────────────────
    def _detect_tools(self, user_agents: list, payloads: list) -> list:
        tools = set()
        combined = ' '.join(user_agents + payloads).lower()
        for tool, _ in TOOL_SCORES.items():
            if tool in combined:
                tools.add(tool)
        return sorted(tools)

    def _tool_sophistication(self, tools: list) -> float:
        if not tools:
            return 0.1
        return min(max(TOOL_SCORES.get(t, 0.3) for t in tools), 1.0)

    # ── Behavioral hash ───────────────────────────────────────────────────
    def _behavioral_hash(self, ip: str, attack_types: list,
                         tools: list, ua_list: list) -> str:
        sig = f"{sorted(attack_types)}|{sorted(tools)}|{sorted(set(ua_list))}"
        return hashlib.sha256(sig.encode()).hexdigest()[:16]

    # ── Threat score ──────────────────────────────────────────────────────
    def _threat_score(self, profile: dict) -> float:
        attacks = profile.get('attack_count', 0)
        types   = len(profile.get('attack_types', []))
        tools   = profile.get('tools_detected', [])
        days    = profile.get('active_days', 1)
        canary  = profile.get('canary_triggered', False)
        wazuh_lvl = profile.get('max_wazuh_level', 0)

        score = 0.0
        # Attack volume (log scale)
        score += W['attack_count'] * min(np.log1p(attacks) / np.log1p(500), 1.0)
        # Diversity
        score += W['attack_diversity'] * min(types / 6.0, 1.0)
        # Tool sophistication
        score += W['tool_sophistication'] * self._tool_sophistication(tools)
        # Persistence (active over multiple days)
        score += W['persistence'] * min(days / 7.0, 1.0)
        # Honeypot depth
        hp_depth = profile.get('honeypot_depth', 0)
        score += W['honeypot_depth'] * min(hp_depth / 10.0, 1.0)
        # Wazuh severity
        score += W['wazuh_severity'] * min(wazuh_lvl / 15.0, 1.0)
        # Canary
        score += W['canary_triggered'] * (1.0 if canary else 0.0)

        return round(min(score, 1.0), 4)

    # ── Cluster assignment ────────────────────────────────────────────────
    def _assign_cluster(self, profiles: list) -> dict:
        """
        Simple k-means-style clustering on threat_score + attack_diversity.
        Returns {ip: cluster_id}.
        """
        if len(profiles) < 3:
            return {p['ip']: 0 for p in profiles}

        try:
            from sklearn.cluster import KMeans
            from sklearn.preprocessing import StandardScaler

            features = []
            ips = []
            for p in profiles:
                features.append([
                    p.get('threat_score', 0),
                    len(p.get('attack_types', [])),
                    p.get('attack_count', 0),
                    len(p.get('tools_detected', [])),
                ])
                ips.append(p['ip'])

            X = StandardScaler().fit_transform(features)
            k = min(5, len(profiles))
            labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(X)
            return dict(zip(ips, [int(l) for l in labels]))
        except Exception as e:
            logger.warning(f'Clustering failed: {e}')
            return {p['ip']: 0 for p in profiles}

    # ── Build / update profile ────────────────────────────────────────────
    def build_profile(self, ip: str) -> dict:
        """Build a complete profile for one IP from all available data."""
        # Attacks
        attacks = self.db.get_attacks(limit=1000, filters={'ip': ip})
        if not attacks:
            return {}

        attack_types = list({a.get('attack_type', 'Unknown') for a in attacks})
        user_agents  = [a.get('user_agent', '') for a in attacks if a.get('user_agent')]
        payloads     = [a.get('payload', '') or a.get('query_string', '') for a in attacks]
        timestamps   = sorted(a.get('timestamp', '') for a in attacks)

        # Time analysis
        first_seen = timestamps[0] if timestamps else datetime.utcnow().isoformat()
        last_seen  = timestamps[-1] if timestamps else datetime.utcnow().isoformat()
        try:
            d1 = datetime.fromisoformat(first_seen[:19])
            d2 = datetime.fromisoformat(last_seen[:19])
            active_days = max((d2 - d1).days, 1)
        except Exception:
            active_days = 1

        # Request rate (requests per hour)
        try:
            total_hours = max(active_days * 24, 1)
            req_rate = len(attacks) / total_hours
        except Exception:
            req_rate = 0

        # Tools
        tools = self._detect_tools(user_agents, payloads)

        # Honeypot depth (how many honeypot pages visited)
        hp_events = [a for a in attacks if a.get('routed_to', '').startswith('honeypot')]
        hp_depth  = len(hp_events)

        # Wazuh alerts for this IP
        max_wazuh_level = 0
        try:
            with self.db.get_connection() as conn:
                row = conn.execute(
                    "SELECT MAX(rule_level) as ml FROM wazuh_alerts WHERE ip=?", (ip,)
                ).fetchone()
                if row and row['ml']:
                    max_wazuh_level = int(row['ml'])
        except Exception:
            pass

        # Canary triggered
        canary = False
        try:
            with self.db.get_connection() as conn:
                row = conn.execute(
                    "SELECT COUNT(*) as n FROM canary_triggers WHERE ip=?", (ip,)
                ).fetchone()
                canary = bool(row and row['n'] > 0)
        except Exception:
            pass

        # Attack timing pattern
        timing_pattern = self._timing_pattern(timestamps)

        profile = {
            'ip':              ip,
            'first_seen':      first_seen,
            'last_seen':       last_seen,
            'attack_count':    len(attacks),
            'attack_types':    attack_types,
            'user_agents':     list(set(user_agents))[:10],
            'tools_detected':  tools,
            'active_days':     active_days,
            'req_rate_per_hr': round(req_rate, 2),
            'honeypot_depth':  hp_depth,
            'max_wazuh_level': max_wazuh_level,
            'canary_triggered':canary,
            'timing_pattern':  timing_pattern,
            'behavioral_hash': self._behavioral_hash(ip, attack_types, tools, user_agents),
        }
        profile['threat_score'] = self._threat_score(profile)
        return profile

    def _timing_pattern(self, timestamps: list) -> str:
        """Classify attack timing: burst, persistent, scheduled, sporadic."""
        if len(timestamps) < 3:
            return 'sporadic'
        try:
            dts = [datetime.fromisoformat(t[:19]) for t in timestamps]
            diffs = [(dts[i+1]-dts[i]).total_seconds() for i in range(len(dts)-1)]
            avg_gap = np.mean(diffs)
            std_gap = np.std(diffs)
            cv = std_gap / avg_gap if avg_gap > 0 else 0

            if avg_gap < 2:       return 'burst'
            if cv < 0.3:          return 'scheduled'
            if avg_gap < 300:     return 'persistent'
            return 'sporadic'
        except Exception:
            return 'unknown'

    # ── Comparison ────────────────────────────────────────────────────────
    def compare_profiles(self, ip1: str, ip2: str) -> dict:
        """
        Compare two attacker profiles to determine if they are likely
        the same attacker using different IPs (VPN/Tor pivoting).
        """
        p1 = self.build_profile(ip1)
        p2 = self.build_profile(ip2)
        if not p1 or not p2:
            return {'similar': False, 'score': 0.0}

        scores = []

        # Same behavioral hash → very likely same attacker
        if p1['behavioral_hash'] == p2['behavioral_hash']:
            return {'similar': True, 'score': 1.0, 'reason': 'identical behavioral hash'}

        # Attack type overlap
        t1, t2 = set(p1['attack_types']), set(p2['attack_types'])
        if t1 and t2:
            overlap = len(t1 & t2) / len(t1 | t2)
            scores.append(('attack_type_overlap', overlap))

        # Tool overlap
        tl1, tl2 = set(p1['tools_detected']), set(p2['tools_detected'])
        if tl1 and tl2:
            tool_overlap = len(tl1 & tl2) / len(tl1 | tl2)
            scores.append(('tool_overlap', tool_overlap))

        # UA overlap
        ua1 = set(p1['user_agents'])
        ua2 = set(p2['user_agents'])
        if ua1 and ua2:
            ua_overlap = len(ua1 & ua2) / len(ua1 | ua2)
            scores.append(('ua_overlap', ua_overlap))

        # Timing pattern
        if p1['timing_pattern'] == p2['timing_pattern']:
            scores.append(('timing_match', 0.7))

        # Threat score proximity
        ts_diff = abs(p1['threat_score'] - p2['threat_score'])
        scores.append(('threat_score_proximity', max(0, 1 - ts_diff * 3)))

        if not scores:
            return {'similar': False, 'score': 0.0}

        avg_score = float(np.mean([s for _, s in scores]))
        similar   = avg_score >= 0.65

        return {
            'similar':    similar,
            'score':      round(avg_score, 3),
            'components': dict(scores),
            'reason':     'behavioral similarity' if similar else 'distinct profiles'
        }

    # ── Bulk update ───────────────────────────────────────────────────────
    def update_all_profiles(self) -> int:
        """Rebuild profiles for all known IPs and update DB. Returns count."""
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT DISTINCT ip FROM attacks ORDER BY ip"
            ).fetchall()
        ips = [r['ip'] for r in rows]

        profiles = []
        for ip in ips:
            try:
                p = self.build_profile(ip)
                if p:
                    profiles.append(p)
            except Exception as e:
                logger.warning(f'Profile build failed for {ip}: {e}')

        # Cluster assignment
        cluster_map = self._assign_cluster(profiles)

        # Upsert into DB + explicitly write cluster_id
        updated = 0
        for p in profiles:
            cluster_id = cluster_map.get(p['ip'], 0)
            try:
                self.db.upsert_attacker_profile({
                    'ip':              p['ip'],
                    'first_seen':      p['first_seen'],
                    'last_seen':       p['last_seen'],
                    'attack_count':    p['attack_count'],
                    'attack_types':    p['attack_types'],
                    'user_agents':     p['user_agents'],
                    'behavioral_hash': p['behavioral_hash'],
                    'tools_detected':  p['tools_detected'],
                    'threat_score':    p['threat_score'],
                    'cluster_id':      cluster_id,
                })
                # Explicit cluster_id write-back (fallback in case upsert ignores it)
                with self.db.get_connection() as conn:
                    conn.execute(
                        'UPDATE attacker_profiles SET cluster_id=? WHERE ip_address=?',
                        (cluster_id, p['ip'])
                    )
                    conn.commit()
                updated += 1
            except Exception as e:
                logger.warning(f'Profile upsert failed for {p["ip"]}: {e}')

        logger.info(f'Updated {updated} profiles, {len(set(cluster_map.values()))} clusters')
        return updated

    def get_cluster_summary(self) -> list:
        """Return enriched cluster summaries for dashboard cluster cards."""
        with self.db.get_connection() as conn:
            clusters = conn.execute("""
                SELECT cluster_id,
                       COUNT(*) as member_count,
                       AVG(threat_score) as avg_threat,
                       MAX(threat_score) as max_threat,
                       MAX(last_seen) as last_active,
                       MIN(first_seen) as first_seen,
                       GROUP_CONCAT(ip_address, ',') as members_csv,
                       GROUP_CONCAT(attack_types_json, '|') as all_types_json
                FROM attacker_profiles
                WHERE cluster_id IS NOT NULL
                GROUP BY cluster_id
                ORDER BY avg_threat DESC
            """).fetchall()

        result = []
        for r in clusters:
            d = dict(r)
            # Parse members list
            members = [m.strip() for m in (d.pop('members_csv', '') or '').split(',') if m.strip()]
            d['members'] = members[:10]  # first 10 IPs
            # Parse and merge all attack types
            all_types = set()
            for tj in (d.pop('all_types_json', '') or '').split('|'):
                try:
                    all_types.update(json.loads(tj))
                except Exception:
                    pass
            d['attack_types'] = sorted(all_types)
            result.append(d)
        return result
