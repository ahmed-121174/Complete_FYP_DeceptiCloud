#!/usr/bin/env python3
"""
Adaptive Learning Engine — Main Orchestrator
Runs as a background service. Coordinates:
  1. Wazuh log consumption
  2. Drift detection
  3. Automatic retraining
  4. Attacker profile updates
  5. Behavioral comparison
"""

import time
import logging
import threading
import json
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from adaptive_engine.core.wazuh_consumer    import WazuhConsumer
from adaptive_engine.core.drift_detector    import DriftDetector
from adaptive_engine.pipeline.retraining_pipeline import RetrainingPipeline
from adaptive_engine.behavioral.profiler    import AttackerProfiler
from database.db_service import get_db_service

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('adaptive_engine')

# Intervals (seconds)
WAZUH_POLL_INTERVAL    = 15
DRIFT_CHECK_INTERVAL   = 300   # 5 min
PROFILE_UPDATE_INTERVAL= 120   # 2 min
RETRAIN_CHECK_INTERVAL = 600   # 10 min

# State file for dashboard
STATE_FILE = Path(__file__).parent / 'engine_state.json'


class AdaptiveLearningEngine:
    def __init__(self):
        self.db         = get_db_service()
        self.consumer   = WazuhConsumer()
        self.detector   = DriftDetector()
        self.pipeline   = RetrainingPipeline()
        self.profiler   = AttackerProfiler()
        self._running   = False
        self._threads   = []
        self._state     = {
            'started_at':        None,
            'wazuh_alerts_ingested': 0,
            'retraining_runs':   0,
            'profiles_updated':  0,
            'drift_events':      0,
            'last_retrain':      {},
            'last_drift_check':  None,
            'last_profile_update': None,
            'model_versions':    {},
        }

    # ── State persistence ─────────────────────────────────────────────────
    def _save_state(self):
        try:
            STATE_FILE.write_text(json.dumps(self._state, indent=2))
        except Exception:
            pass

    def load_state(self) -> dict:
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text())
            except Exception:
                pass
        return {}

    # ── Worker threads ────────────────────────────────────────────────────
    def _wazuh_worker(self):
        """Continuously poll Wazuh and ingest alerts."""
        logger.info('Wazuh consumer thread started')
        while self._running:
            try:
                n = self.consumer.run_once()
                if n:
                    self._state['wazuh_alerts_ingested'] += n
                    self._save_state()
            except Exception as e:
                logger.error(f'Wazuh worker error: {e}')
            time.sleep(WAZUH_POLL_INTERVAL)

    def _drift_worker(self):
        """Periodically check for model drift."""
        logger.info('Drift detection thread started')
        while self._running:
            try:
                self.detector.load_baselines_from_db()
                report = self.detector.full_report()
                drift_count = sum(
                    1 for m in report.get('models', {}).values()
                    if m.get('drift_detected')
                )
                if drift_count:
                    self._state['drift_events'] += drift_count
                    logger.warning(f'Drift detected in {drift_count} model(s)')
                    # Log to DB
                    self.db.insert_event({
                        'timestamp': datetime.utcnow().isoformat(),
                        'event_type': 'ml',
                        'severity': 'medium',
                        'source': 'adaptive_engine/drift_detector',
                        'message': f'Model drift detected in {drift_count} model(s)',
                        'details': {'report': report}
                    })
                self._state['last_drift_check'] = datetime.utcnow().isoformat()
                self._save_state()
            except Exception as e:
                logger.error(f'Drift worker error: {e}')
            time.sleep(DRIFT_CHECK_INTERVAL)

    def _retrain_worker(self):
        """Check if retraining is needed and trigger it."""
        logger.info('Retraining worker thread started')
        # Stagger start to avoid all workers firing at once
        time.sleep(60)
        while self._running:
            try:
                attack_types = ['XSS', 'Brute Force', 'Port Scan', 'Credential Stuffing']
                for atype in attack_types:
                    if not self._running:
                        break
                    should, reason = self.detector.should_retrain(atype)
                    if should:
                        logger.info(f'Retraining {atype}: {reason}')
                        result = self.pipeline.retrain(atype)
                        self._state['retraining_runs'] += 1
                        self._state['last_retrain'][atype] = {
                            'at':     datetime.utcnow().isoformat(),
                            'reason': reason,
                            'result': result
                        }
                        # Log to DB
                        self.db.insert_event({
                            'timestamp': datetime.utcnow().isoformat(),
                            'event_type': 'ml',
                            'severity': 'low',
                            'source': 'adaptive_engine/retraining',
                            'message': f'{atype} model retrained: {result.get("status")}',
                            'details': result
                        })
                        self._save_state()
                        time.sleep(5)   # brief pause between models
            except Exception as e:
                logger.error(f'Retrain worker error: {e}')
            time.sleep(RETRAIN_CHECK_INTERVAL)

    def _profile_worker(self):
        """Periodically rebuild attacker profiles."""
        logger.info('Profile update thread started')
        time.sleep(30)   # let system settle first
        while self._running:
            try:
                n = self.profiler.update_all_profiles()
                self._state['profiles_updated'] = n
                self._state['last_profile_update'] = datetime.utcnow().isoformat()
                self._save_state()
                logger.info(f'Updated {n} attacker profiles')
            except Exception as e:
                logger.error(f'Profile worker error: {e}')
            time.sleep(PROFILE_UPDATE_INTERVAL)

    # ── Public API ────────────────────────────────────────────────────────
    def start(self):
        self._running = True
        self._state['started_at'] = datetime.utcnow().isoformat()

        workers = [
            ('wazuh',   self._wazuh_worker),
            ('drift',   self._drift_worker),
            ('retrain', self._retrain_worker),
            ('profile', self._profile_worker),
        ]
        for name, fn in workers:
            t = threading.Thread(target=fn, name=name, daemon=True)
            t.start()
            self._threads.append(t)

        logger.info('Adaptive Learning Engine started — all workers running')
        self._save_state()

    def stop(self):
        self._running = False
        logger.info('Adaptive Learning Engine stopping...')

    def status(self) -> dict:
        return {
            **self._state,
            'running': self._running,
            'threads': [t.name for t in self._threads if t.is_alive()],
        }

    def force_retrain(self, attack_type: str) -> dict:
        """Manually trigger retraining for one model."""
        logger.info(f'Manual retrain triggered for {attack_type}')
        result = self.pipeline.retrain(attack_type)
        self._state['retraining_runs'] += 1
        self._state['last_retrain'][attack_type] = {
            'at': datetime.utcnow().isoformat(),
            'reason': 'manual',
            'result': result
        }
        self._save_state()
        return result

    def force_rollback(self, attack_type: str) -> dict:
        """Manually rollback a model to its previous version."""
        return self.pipeline.rollback(attack_type)

    def drift_report(self) -> dict:
        self.detector.load_baselines_from_db()
        return self.detector.full_report()

    def compare_attackers(self, ip1: str, ip2: str) -> dict:
        return self.profiler.compare_profiles(ip1, ip2)

    def cluster_summary(self) -> list:
        return self.profiler.get_cluster_summary()


# Singleton
_engine: AdaptiveLearningEngine | None = None

def get_engine() -> AdaptiveLearningEngine:
    global _engine
    if _engine is None:
        _engine = AdaptiveLearningEngine()
    return _engine


if __name__ == '__main__':
    import signal
    engine = get_engine()
    engine.start()

    def _shutdown(sig, frame):
        engine.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    print('Adaptive Learning Engine running. Ctrl+C to stop.')
    while True:
        time.sleep(60)
        s = engine.status()
        print(f"[{datetime.now():%H:%M:%S}] Alerts: {s['wazuh_alerts_ingested']} | "
              f"Retrains: {s['retraining_runs']} | Profiles: {s['profiles_updated']}")
