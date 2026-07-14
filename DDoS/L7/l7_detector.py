"""
DDoS/L7/l7_detector.py

Drop-in inference module for routing_proxy.py.
Loads the trained L7 DDoS model once at startup and exposes
a single function: is_ddos(ip, path, status, ua, xff) -> (bool, float)

Usage in routing_proxy.py:
    from DDoS.L7.l7_detector import is_ddos, record_request
    ...
    attack, confidence = is_ddos(ip, path, status_code, user_agent, xff)
    if attack:
        # route to honeypot
"""

import logging
import warnings
import joblib
from pathlib import Path

# Suppress sklearn UserWarning when feature names are validated
warnings.filterwarnings('ignore', message='X does not have valid feature names')

logger = logging.getLogger('proxy.l7_ddos')

_HERE     = Path(__file__).parent
_MODELS   = _HERE / 'models'

# Globals loaded once at import time
_model     = None
_scaler    = None
_threshold = 0.5
_loaded    = False

# Import the feature extractor
try:
    from DDoS.L7.collect_data import extract_features, clear_ip
except ImportError:
    try:
        import sys
        sys.path.insert(0, str(_HERE.parent.parent))
        from DDoS.L7.collect_data import extract_features, clear_ip
    except ImportError:
        extract_features = None
        clear_ip = None


def _load():
    global _model, _scaler, _threshold, _loaded
    if _loaded:
        return True
    try:
        _model     = joblib.load(_MODELS / 'l7_ddos_model.pkl')
        _scaler    = joblib.load(_MODELS / 'l7_scaler.pkl')
        tpath      = _MODELS / 'l7_threshold.txt'
        _threshold = float(tpath.read_text().strip()) if tpath.exists() else 0.5
        _loaded    = True
        logger.info(f"L7 DDoS detector loaded (threshold={_threshold:.4f})")
        return True
    except Exception as e:
        logger.warning(f"L7 DDoS model not loaded: {e} — run DDoS/L7/train_l7.py first")
        return False


def record_request(ip: str, path: str, status: int, ua: str,
                   xff: str | None = None) -> dict | None:
    """
    Record a request in the sliding window.
    Returns the feature dict, or None if feature extractor not available.
    """
    if extract_features is None:
        return None
    return extract_features(ip, path, status, ua, xff)


def is_ddos(ip: str, path: str, status: int, ua: str,
            xff: str | None = None) -> tuple[bool, float]:
    """
    Main inference function called by routing_proxy.py.

    Returns:
        (is_attack: bool, confidence: float)
    """
    if not _load():
        return False, 0.0

    if extract_features is None:
        return False, 0.0

    try:
        import pandas as _pd
        features = extract_features(ip, path, status, ua, xff)
        _FNAMES = [
            'req_per_10s', 'req_per_1s', 'unique_paths_ratio',
            'error_rate', 'ua_entropy', 'avg_path_depth',
            'is_root_flood', 'ip_is_spoofed',
        ]
        feat_df     = _pd.DataFrame([[
            features['req_per_10s'],
            features['req_per_1s'],
            features['unique_paths_ratio'],
            features['error_rate'],
            features['ua_entropy'],
            features['avg_path_depth'],
            features['is_root_flood'],
            features['ip_is_spoofed'],
        ]], columns=_FNAMES)

        feat_scaled = _scaler.transform(feat_df)
        prob        = float(_model.predict_proba(feat_scaled)[0][1])
        attack      = prob >= _threshold

        if attack:
            logger.warning(
                f"L7 DDoS detected: IP={ip} req/s={features['req_per_1s']} "
                f"ua_entropy={features['ua_entropy']:.2f} conf={prob:.4f}"
            )

        return attack, prob

    except Exception as e:
        logger.error(f"L7 DDoS inference error: {e}")
        return False, 0.0


def reset_ip(ip: str):
    """Reset the sliding window for an IP after it is blocked."""
    if clear_ip:
        clear_ip(ip)


# Pre-load on import (non-blocking — warnings only if model not trained yet)
_load()
