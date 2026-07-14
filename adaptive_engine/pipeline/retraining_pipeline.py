#!/usr/bin/env python3
"""
Continuous Retraining Pipeline
Pulls new training data from DB, retrains the appropriate model,
evaluates it, and hot-swaps it into the ML API if it improves.
"""

import json
import json
import logging
import numpy as np
import joblib
import shutil
import requests
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from database.db_service import get_db_service

logger = logging.getLogger('retraining')

BASE_DIR    = Path(__file__).parent.parent.parent
MODELS_DIR  = BASE_DIR / 'ml_pipeline' / 'models'
ARCHIVE_DIR = BASE_DIR / 'ml_pipeline' / 'model_archive'
ML_API_URL  = 'http://localhost:5000'

ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

# Minimum improvement required to swap model (avoid noise-driven swaps)
MIN_IMPROVEMENT = 0.005   # 0.5 percentage points

# Model configs — all 7 attack detection models
MODEL_CONFIGS = {
    'XSS': {
        'model_file':    'xss_detector.pkl',
        'vectorizer':    'xss_vectorizer.pkl',
        'metadata':      'xss_metadata.json',
        'mode':          'text',
        'feature_names': None,
    },
    'Brute Force': {
        'model_file':  'brute_force_detector.pkl',
        'scaler':      'brute_force_scaler.pkl',
        'metadata':    'brute_force_metadata.json',
        'mode':        'tabular',
        'feature_names': [
            'num_attempts','avg_time_between_attempts','min_time_between_attempts',
            'max_time_between_attempts','unique_usernames','success_rate',
            'avg_response_time','has_brute_force_ua','attempts_per_minute',
            'password_length_variance'
        ],
    },
    'Port Scan': {
        'model_file':  'port_scan_detector.pkl',
        'scaler':      'port_scan_scaler.pkl',
        'metadata':    'port_scan_metadata.json',
        'mode':        'tabular',
        'feature_names': [
            'num_ports_accessed','unique_ports','avg_time_between_accesses',
            'min_time_between_accesses','max_time_between_accesses','avg_port_diff',
            'sequential_pattern','ports_per_second','has_scan_ua',
            'avg_response_time','common_ports_ratio','high_port_ratio'
        ],
    },
    'Credential Stuffing': {
        'model_file':  'credential_stuffing_detector.pkl',
        'scaler':      'credential_stuffing_scaler.pkl',
        'metadata':    'credential_stuffing_metadata.json',
        'mode':        'tabular',
        'feature_names': [
            'num_attempts','avg_time_between_attempts','min_time_between_attempts',
            'attempts_per_minute','unique_ips','unique_user_agents','unique_usernames',
            'ip_rotation_rate','ua_rotation_rate','username_rotation_rate',
            'success_rate','avg_response_time'
        ],
    },
    'SQL Injection': {
        'model_file':  'web_attack_best_model.keras',
        'scaler':      'web_attack_preprocessor_fixed.pkl',
        'metadata':    'web_attack_preprocessor_metadata.json',
        'mode':        'tabular',
        'feature_names': WEB_ATTACK_FEATURES,
    },
    'DDoS': {
        'model_file':  'ddos_best_model.keras',
        'scaler':      'ddos_preprocessor.pkl',
        'metadata':    'ddos_preprocessor_metadata.json',
        'mode':        'tabular',
        'feature_names': [
            'packets_per_sec','bytes_per_sec','src_ip_entropy','dst_port_entropy',
            'avg_packet_size','tcp_syn_ratio','icmp_ratio','udp_ratio',
            'connection_count','unique_src_ips'
        ],
    },
    'Anomaly Detection': {
        'model_file':  'anomaly_detector.pkl',
        'scaler':      'anomaly_scaler.pkl',
        'metadata':    'anomaly_metadata.json',
        'mode':        'tabular',
        'feature_names': WEB_ATTACK_FEATURES,
    },
}

# Generic web-attack features (used for SQLi, Anomaly Detection, etc.)
WEB_ATTACK_FEATURES = [
    'url_length','path_length','query_length','body_length',
    'method_is_post','method_is_put','num_headers','has_auth_header',
    'content_type_json','content_type_form','num_params','num_path_segments',
    'has_encoded_chars','num_special_chars','max_param_length',
    'sqli_pattern_count','nosqli_pattern_count','xss_pattern_count',
    'traversal_pattern_count','has_suspicious_ua','ua_length',
    'has_referer','has_cookie'
]


class RetrainingPipeline:
    def __init__(self):
        self.db = get_db_service()

    # ── Data loading ──────────────────────────────────────────────────────
    def load_training_data(self, attack_type: str | None = None,
                           min_samples: int = 100) -> tuple[list, list]:
        """Load unused training data from DB. Returns (X, y)."""
        with self.db.get_connection() as conn:
            if attack_type:
                rows = conn.execute(
                    "SELECT features_json, label FROM training_data "
                    "WHERE used_in_training=0 AND attack_type=? LIMIT 5000",
                    (attack_type,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT features_json, label FROM training_data "
                    "WHERE used_in_training=0 LIMIT 10000"
                ).fetchall()

        if len(rows) < min_samples:
            logger.info(f'Not enough data for {attack_type}: {len(rows)} < {min_samples}')
            return [], []

        X, y = [], []
        for row in rows:
            try:
                feats = json.loads(row['features_json'])
                X.append(feats)
                y.append(int(row['label']))
            except Exception:
                continue
        return X, y

    def mark_used(self, attack_type: str | None = None):
        """Mark training data as used after retraining."""
        with self.db.get_connection() as conn:
            if attack_type:
                conn.execute(
                    "UPDATE training_data SET used_in_training=1 WHERE attack_type=?",
                    (attack_type,)
                )
            else:
                conn.execute("UPDATE training_data SET used_in_training=1")
            conn.commit()

    # ── Tabular model retraining ──────────────────────────────────────────
    def _retrain_tabular(self, attack_type: str, cfg: dict,
                         X_raw: list, y: list) -> dict | None:
        from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
        from sklearn.preprocessing import StandardScaler
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

        feature_names = cfg['feature_names']

        # Build feature matrix
        X = []
        for feat_dict in X_raw:
            row = [feat_dict.get(f, 0) for f in feature_names]
            X.append(row)
        X = np.array(X, dtype=float)
        y = np.array(y)

        if len(np.unique(y)) < 2:
            logger.warning(f'{attack_type}: only one class in data, skipping')
            return None

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42, stratify=y
        )

        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s  = scaler.transform(X_test)

        # Choose estimator
        if attack_type == 'Credential Stuffing':
            model = GradientBoostingClassifier(
                n_estimators=40, max_depth=3, learning_rate=0.05,
                subsample=0.8, random_state=42
            )
        else:
            model = RandomForestClassifier(
                n_estimators=30, max_depth=6, min_samples_split=12,
                min_samples_leaf=6, max_features='sqrt', random_state=42
            )

        model.fit(X_train_s, y_train)
        y_pred = model.predict(X_test_s)

        metrics = {
            'accuracy':  float(accuracy_score(y_test, y_pred)),
            'precision': float(precision_score(y_test, y_pred, zero_division=0)),
            'recall':    float(recall_score(y_test, y_pred, zero_division=0)),
            'f1_score':  float(f1_score(y_test, y_pred, zero_division=0)),
        }

        return {'model': model, 'scaler': scaler, 'metrics': metrics}

    # ── Text model retraining (XSS) ───────────────────────────────────────
    def _retrain_text(self, attack_type: str, cfg: dict,
                      X_raw: list, y: list) -> dict | None:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

        texts = [d.get('url', '') + ' ' + d.get('payload', '') for d in X_raw]
        y = np.array(y)

        if len(np.unique(y)) < 2:
            return None

        X_train, X_test, y_train, y_test = train_test_split(
            texts, y, test_size=0.25, random_state=42, stratify=y
        )

        vec = TfidfVectorizer(max_features=200, ngram_range=(1,2),
                              analyzer='char', min_df=3, max_df=0.9)
        X_train_v = vec.fit_transform(X_train)
        X_test_v  = vec.transform(X_test)

        model = RandomForestClassifier(
            n_estimators=25, max_depth=5, min_samples_split=15,
            min_samples_leaf=8, max_features='sqrt', random_state=42
        )
        model.fit(X_train_v, y_train)
        y_pred = model.predict(X_test_v)

        metrics = {
            'accuracy':  float(accuracy_score(y_test, y_pred)),
            'precision': float(precision_score(y_test, y_pred, zero_division=0)),
            'recall':    float(recall_score(y_test, y_pred, zero_division=0)),
            'f1_score':  float(f1_score(y_test, y_pred, zero_division=0)),
        }
        return {'model': model, 'vectorizer': vec, 'metrics': metrics}

    # ── Save & hot-swap ───────────────────────────────────────────────────
    def _archive_current(self, cfg: dict):
        ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        for key in ('model_file', 'scaler', 'vectorizer', 'metadata'):
            fname = cfg.get(key)
            if fname:
                src = MODELS_DIR / fname
                if src.exists():
                    shutil.copy2(src, ARCHIVE_DIR / f'{ts}_{fname}')

    def _save_new_model(self, cfg: dict, result: dict, attack_type: str,
                        version: str, n_samples: int):
        # Save model
        joblib.dump(result['model'], MODELS_DIR / cfg['model_file'])

        # Save scaler or vectorizer
        if 'scaler' in result:
            joblib.dump(result['scaler'], MODELS_DIR / cfg['scaler'])
        if 'vectorizer' in result:
            joblib.dump(result['vectorizer'], MODELS_DIR / cfg['vectorizer'])

        # Save metadata
        meta = {
            'model_type':    'Random Forest (Adaptive)',
            'attack_type':   attack_type,
            'version':       version,
            'trained_at':    datetime.utcnow().isoformat(),
            'training_samples': n_samples,
            **result['metrics']
        }
        with open(MODELS_DIR / cfg['metadata'], 'w') as f:
            json.dump(meta, f, indent=2)

        # Record in ml_models table
        with self.db.get_connection() as conn:
            conn.execute("UPDATE ml_models SET is_active=0 WHERE model_type=?", (attack_type,))
            conn.execute("""
                INSERT OR REPLACE INTO ml_models
                (model_name, model_type, version, file_path, accuracy, precision_val,
                 recall_val, f1_score, training_date, training_samples, is_active)
                VALUES (?,?,?,?,?,?,?,?,?,?,1)
            """, (
                f'{attack_type} Detector',
                attack_type,
                version,
                str(MODELS_DIR / cfg['model_file']),
                result['metrics']['accuracy'],
                result['metrics']['precision'],
                result['metrics']['recall'],
                result['metrics']['f1_score'],
                datetime.utcnow().isoformat(),
                n_samples
            ))
            conn.commit()

    def _reload_ml_api(self):
        """Signal ML API to reload models."""
        try:
            r = requests.post(f'{ML_API_URL}/api/reload-models', timeout=5)
            if r.status_code == 200:
                logger.info('ML API reloaded models successfully')
            else:
                logger.warning(f'ML API reload returned {r.status_code}')
        except Exception as e:
            logger.warning(f'Could not reload ML API: {e}')

    # ── Current model accuracy ────────────────────────────────────────────
    def _current_accuracy(self, attack_type: str) -> float:
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT accuracy FROM ml_models WHERE model_type=? AND is_active=1",
                (attack_type,)
            ).fetchone()
        return float(row['accuracy']) if row else 0.80

    # ── Public API ────────────────────────────────────────────────────────
    def retrain(self, attack_type: str) -> dict:
        """
        Full retraining cycle for one attack type.
        Returns a result dict with status and metrics.
        """
        logger.info(f'Starting retraining for {attack_type}')
        cfg = MODEL_CONFIGS.get(attack_type)
        if not cfg:
            return {'status': 'skipped', 'reason': f'No config for {attack_type}'}

        X, y = self.load_training_data(attack_type, min_samples=80)
        if not X:
            return {'status': 'skipped', 'reason': 'Insufficient training data'}

        # Train
        try:
            if cfg['mode'] == 'text':
                result = self._retrain_text(attack_type, cfg, X, y)
            else:
                result = self._retrain_tabular(attack_type, cfg, X, y)
        except Exception as e:
            logger.error(f'Training error for {attack_type}: {e}')
            return {'status': 'error', 'reason': str(e)}

        if result is None:
            return {'status': 'skipped', 'reason': 'Training returned no result'}

        new_acc  = result['metrics']['accuracy']
        curr_acc = self._current_accuracy(attack_type)

        if new_acc < curr_acc - MIN_IMPROVEMENT:
            logger.info(f'{attack_type}: new model ({new_acc:.3f}) worse than current ({curr_acc:.3f}), keeping current')
            return {
                'status': 'rejected',
                'reason': f'New accuracy {new_acc:.3f} < current {curr_acc:.3f}',
                'metrics': result['metrics']
            }

        # Archive current, save new
        self._archive_current(cfg)
        version = datetime.utcnow().strftime('v%Y%m%d_%H%M%S')
        self._save_new_model(cfg, result, attack_type, version, len(X))
        self.mark_used(attack_type)
        self._reload_ml_api()

        logger.info(f'{attack_type} retrained: {curr_acc:.3f} → {new_acc:.3f}')
        return {
            'status':  'deployed',
            'version': version,
            'prev_accuracy': curr_acc,
            'metrics': result['metrics'],
            'samples': len(X)
        }

    def profile_comparison_retrain(self) -> dict:
        """
        Compare honeypot attacker profiles against real-site visitors.
        If behavioral similarity > 50% => flag as attacker, block at proxy,
        and trigger retraining on the matched attack type.
        """
        results = []
        try:
            with self.db.get_connection() as conn:
                attacker_profiles = conn.execute("""
                    SELECT ip_address, attack_count, threat_score,
                           attack_types_json, tools_json, path_patterns_json, cluster_id
                    FROM attacker_profiles WHERE threat_score > 0.3
                    ORDER BY threat_score DESC LIMIT 50
                """).fetchall()

                if not attacker_profiles:
                    return {'matched': 0, 'results': []}

                real_visitors = conn.execute("""
                    SELECT ip, user_agent, path, method,
                           GROUP_CONCAT(attack_type) as suspected_types,
                           COUNT(*) as request_count
                    FROM attacks
                    WHERE routed_to NOT LIKE 'honeypot%' AND ip IS NOT NULL
                      AND timestamp > datetime('now', '-2 hours')
                    GROUP BY ip LIMIT 200
                """).fetchall()

            for visitor in real_visitors:
                visitor_ip   = visitor['ip']
                visitor_ua   = (visitor['user_agent'] or '').lower()
                visitor_paths = set((visitor['path'] or '').split('/'))
                best_score, best_match = 0.0, None

                for attacker in attacker_profiles:
                    score = 0.0
                    if attacker['ip_address'] == visitor_ip:
                        score = 1.0
                    else:
                        try:
                            tools = json.loads(attacker['tools_json'] or '[]')
                            if any(t.lower() in visitor_ua for t in tools if t):
                                score += 0.35
                        except Exception:
                            pass
                        try:
                            att_paths = set(json.loads(attacker['path_patterns_json'] or '[]'))
                            if att_paths and visitor_paths:
                                overlap = len(att_paths & visitor_paths) / max(len(att_paths | visitor_paths), 1)
                                score += overlap * 0.40
                        except Exception:
                            pass
                        try:
                            cid = attacker['cluster_id']
                            if cid is not None:
                                with self.db.get_connection() as c2:
                                    if c2.execute(
                                        'SELECT 1 FROM attacker_profiles WHERE ip_address=? AND cluster_id=?',
                                        (visitor_ip, cid)
                                    ).fetchone():
                                        score += 0.25
                        except Exception:
                            pass

                    if score > best_score:
                        best_score, best_match = score, attacker

                if best_score > 0.50 and best_match:
                    try:
                        attack_types = json.loads(best_match['attack_types_json'] or '[]')
                    except Exception:
                        attack_types = []

                    logger.warning(
                        f'Profile match {best_score:.1%} -- visitor {visitor_ip} '
                        f'matches attacker {best_match["ip_address"]} (types: {attack_types})'
                    )

                    with self.db.get_connection() as conn:
                        try:
                            conn.execute("""
                                UPDATE attacker_profiles
                                SET threat_score=?, flagged_on_real_site=1, last_seen=datetime('now')
                                WHERE ip_address=?
                            """, (min(best_score, 1.0), visitor_ip))
                            conn.commit()
                        except Exception:
                            pass

                    self._block_ip_at_proxy(visitor_ip)

                    primary = attack_types[0] if attack_types else 'Anomaly Detection'
                    try:
                        self.retrain(primary)
                    except Exception as re:
                        logger.error(f'Auto-retrain failed: {re}')

                    results.append({
                        'visitor_ip':   visitor_ip,
                        'matched_to':   best_match['ip_address'],
                        'similarity':   round(best_score, 3),
                        'attack_types': attack_types,
                        'action':       'blocked_and_retrained',
                    })

        except Exception as e:
            logger.error(f'Profile comparison error: {e}')

        return {'matched': len(results), 'results': results}

    def _block_ip_at_proxy(self, ip: str) -> bool:
        """POST to proxy internal block endpoint."""
        try:
            resp = requests.post(
                'http://localhost:8080/proxy/block-ip',
                json={'ip': ip, 'reason': 'behavioral_profile_match'},
                timeout=3
            )
            if resp.status_code == 200:
                logger.info(f'IP {ip} blocked at proxy')
                return True
        except Exception as e:
            logger.debug(f'Proxy block-ip unreachable: {e}')
        return False
