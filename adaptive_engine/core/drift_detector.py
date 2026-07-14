#!/usr/bin/env python3
"""
Model Drift Detector
Monitors live prediction confidence and detects when a model is degrading.
Triggers retraining when drift is confirmed.
"""

import json
import logging
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from database.db_service import get_db_service

logger = logging.getLogger('drift_detector')

# Thresholds
DRIFT_WINDOW_HOURS   = 6      # look at last N hours of predictions
MIN_SAMPLES          = 50     # need at least this many samples to evaluate
CONFIDENCE_DROP_THR  = 0.10   # if avg confidence drops by >10% → drift
UNCERTAINTY_ZONE     = (0.40, 0.60)  # predictions in this range = uncertain
UNCERTAINTY_RATIO_THR = 0.25  # if >25% of predictions are uncertain → drift
FP_RATE_THR          = 0.15   # if false-positive rate > 15% → drift


class DriftDetector:
    def __init__(self):
        self.db = get_db_service()
        self._baseline: dict[str, float] = {}   # model_type → baseline avg confidence

    # ── Baseline ──────────────────────────────────────────────────────────
    def set_baseline(self, model_type: str, avg_confidence: float):
        self._baseline[model_type] = avg_confidence
        logger.info(f'Baseline set for {model_type}: {avg_confidence:.3f}')

    def load_baselines_from_db(self):
        """Load baselines from the ml_models table (active models)."""
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT model_type, accuracy, precision_val, recall_val, f1_score, "
                "training_samples, training_date, version FROM ml_models WHERE is_active=1"
            ).fetchall()
        self._model_meta = {}
        for row in rows:
            mtype = row['model_type']
            acc = float(row['accuracy'] or 0.85)
            self._baseline[mtype] = acc
            self._model_meta[mtype] = {
                'accuracy':   acc,
                'precision':  float(row['precision_val'] or 0),
                'recall':     float(row['recall_val'] or 0),
                'f1_score':   float(row['f1_score'] or 0),
                'training_samples': row['training_samples'] or 0,
                'training_date':    row['training_date'] or '',
                'version':          row['version'] or '',
            }
        logger.info(f'Loaded {len(self._baseline)} baselines from DB')

    # ── Recent predictions ────────────────────────────────────────────────
    def _recent_attacks(self, hours: int = DRIFT_WINDOW_HOURS) -> list:
        since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        return self.db.get_attacks(
            limit=2000,
            filters={'start_date': since}
        )

    # ── Drift metrics ─────────────────────────────────────────────────────
    def compute_metrics(self, model_type: str | None = None) -> dict:
        """
        Compute drift metrics for one or all models.
        Returns dict: {model_type: {avg_conf, uncertainty_ratio, drift_detected, reason}}
        """
        attacks = self._recent_attacks()
        if len(attacks) < MIN_SAMPLES:
            return {}

        # Group by attack_type
        by_type: dict[str, list] = {}
        for a in attacks:
            t = a.get('attack_type', 'Unknown')
            by_type.setdefault(t, []).append(float(a.get('confidence', 0.5)))

        results = {}
        for atype, confs in by_type.items():
            if model_type and atype != model_type:
                continue
            if len(confs) < 10:
                continue

            arr = np.array(confs)
            avg_conf = float(arr.mean())
            uncertain = float(np.mean((arr >= UNCERTAINTY_ZONE[0]) & (arr <= UNCERTAINTY_ZONE[1])))
            baseline  = self._baseline.get(atype, 0.85)

            drift = False
            reasons = []

            if avg_conf < baseline - CONFIDENCE_DROP_THR:
                drift = True
                reasons.append(f'confidence dropped {baseline - avg_conf:.2%} below baseline')

            if uncertain > UNCERTAINTY_RATIO_THR:
                drift = True
                reasons.append(f'{uncertain:.1%} predictions in uncertainty zone')

            results[atype] = {
                'avg_confidence':    avg_conf,
                'baseline':          baseline,
                'uncertainty_ratio': uncertain,
                'sample_count':      len(confs),
                'drift_detected':    drift,
                'reasons':           reasons,
                'checked_at':        datetime.utcnow().isoformat()
            }

        return results

    # ── Training data quality ─────────────────────────────────────────────
    def new_training_samples(self, model_type: str | None = None) -> int:
        """Count unverified training samples not yet used in training."""
        with self.db.get_connection() as conn:
            if model_type:
                row = conn.execute(
                    "SELECT COUNT(*) as n FROM training_data WHERE used_in_training=0 AND attack_type=?",
                    (model_type,)
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT COUNT(*) as n FROM training_data WHERE used_in_training=0"
                ).fetchone()
        return int(row['n']) if row else 0

    # ── Decision ──────────────────────────────────────────────────────────
    def should_retrain(self, model_type: str) -> tuple[bool, str]:
        """
        Returns (should_retrain: bool, reason: str).
        Triggers retraining if:
          1. Drift detected in live predictions, OR
          2. Enough new training samples accumulated (>= 200)
        """
        new_samples = self.new_training_samples(model_type)
        if new_samples >= 200:
            return True, f'{new_samples} new training samples accumulated'

        metrics = self.compute_metrics(model_type)
        if model_type in metrics and metrics[model_type]['drift_detected']:
            reasons = '; '.join(metrics[model_type]['reasons'])
            return True, f'Drift detected: {reasons}'

        return False, 'No drift detected'

    def full_report(self) -> dict:
        """Full drift report for all 7 models — always returns data seeded from ml_models table."""
        self.load_baselines_from_db()
        live_metrics = self.compute_metrics()
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'window_hours': DRIFT_WINDOW_HOURS,
            'models': {}
        }
        # Always include ALL models from DB, even with no live prediction data
        for mtype, meta in self._model_meta.items():
            live = live_metrics.get(mtype, {})
            baseline = self._baseline.get(mtype, meta['accuracy'])
            # Use live avg_confidence if available, otherwise use model accuracy as proxy
            avg_conf = live.get('avg_confidence', meta['accuracy'])
            uncertainty = live.get('uncertainty_ratio', round(1.0 - meta['accuracy'], 4))
            drift = live.get('drift_detected', False)
            reasons = live.get('reasons', [])
            sample_count = live.get('sample_count', 0)
            new_samples = self.new_training_samples(mtype)
            should, reason = self.should_retrain(mtype)
            report['models'][mtype] = {
                'avg_confidence':      avg_conf,
                'baseline':            baseline,
                'uncertainty_ratio':   uncertainty,
                'sample_count':        sample_count,
                'drift_detected':      drift,
                'reasons':             reasons,
                'checked_at':          datetime.utcnow().isoformat(),
                'new_training_samples': new_samples,
                'retrain_recommended': should,
                'retrain_reason':      reason,
                # Extra metadata from ml_models
                'precision':           meta['precision'],
                'recall':              meta['recall'],
                'f1_score':            meta['f1_score'],
                'training_samples':    meta['training_samples'],
                'version':             meta['version'],
                'training_date':       meta['training_date'],
            }
        return report
