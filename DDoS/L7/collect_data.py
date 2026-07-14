"""
DDoS/L7/collect_data.py

Runs inside the proxy process (or standalone) to log HTTP-level
behavioral features per IP into a CSV that can be used for training.

Usage:
  - Import and call log_request() from routing_proxy.py on every request.
  - To generate labeled data, run the system in two modes:
      1. Normal traffic  → label = 0 (benign)
      2. Attack traffic  → label = 1 (ddos)
  - The CSV is written to DDoS/L7/data/http_features.csv
"""

import csv
import time
import math
import threading
from collections import defaultdict, deque
from pathlib import Path

# ─── State (per-IP sliding window of 10s) ────────────────────────────────────

WINDOW_SECS   = 10       # sliding window size
BURST_WINDOW  = 1        # burst detection sub-window (seconds)

_lock         = threading.Lock()
_ip_windows   = defaultdict(lambda: deque())   # ip -> deque of (timestamp, path, status, ua)
_data_log: list[dict] = []

# Output paths
_HERE         = Path(__file__).parent
DATA_DIR      = _HERE / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)
CSV_PATH      = DATA_DIR / 'http_features.csv'

FEATURE_NAMES = [
    'req_per_10s',          # request rate over 10s window
    'req_per_1s',           # burst rate over last 1s
    'unique_paths_ratio',   # distinct URIs / total requests (low = flood to same endpoint)
    'error_rate',           # fraction of 4xx/5xx responses
    'ua_entropy',           # Shannon entropy of User-Agent strings (low = same bot UA)
    'avg_path_depth',       # average slash-depth of requested paths
    'is_root_flood',        # fraction of requests to '/' exactly
    'ip_is_spoofed',        # 1 if X-Forwarded-For rotates faster than 2/s
]

_CSV_HEADER_WRITTEN = CSV_PATH.exists()  # don't rewrite header if file exists


def _entropy(strings: list[str]) -> float:
    if not strings:
        return 0.0
    freq = defaultdict(int)
    for s in strings:
        freq[s] += 1
    n = len(strings)
    return -sum((c / n) * math.log2(c / n) for c in freq.values() if c > 0)


def extract_features(ip: str, path: str, status: int, ua: str,
                     x_forwarded_for: str | None = None) -> dict:
    """
    Update the per-IP sliding window and return the current feature vector.
    This is called on every request by the proxy.
    """
    now = time.time()

    with _lock:
        w = _ip_windows[ip]
        w.append((now, path, status, ua, x_forwarded_for or ip))

        # Evict entries older than WINDOW_SECS
        cutoff = now - WINDOW_SECS
        while w and w[0][0] < cutoff:
            w.popleft()

        entries       = list(w)
        burst_cutoff  = now - BURST_WINDOW
        burst_entries = [e for e in entries if e[0] >= burst_cutoff]

        req_per_10s   = len(entries)
        req_per_1s    = len(burst_entries)

        paths         = [e[1] for e in entries]
        unique_paths  = len(set(paths))
        unique_ratio  = unique_paths / max(req_per_10s, 1)

        statuses      = [e[2] for e in entries]
        error_rate    = sum(1 for s in statuses if s >= 400) / max(req_per_10s, 1)

        uas           = [e[3] for e in entries]
        ua_entropy    = _entropy(uas)

        depths        = [p.count('/') for p in paths]
        avg_depth     = sum(depths) / max(len(depths), 1)

        root_flood    = sum(1 for p in paths if p.rstrip('?').rstrip('/') in ('', '/')) / max(req_per_10s, 1)

        xff_vals      = [e[4] for e in burst_entries]
        unique_ips_1s = len(set(xff_vals))
        is_spoofed    = 1.0 if unique_ips_1s >= 2 and req_per_1s >= 2 else 0.0

    return {
        'req_per_10s':       req_per_10s,
        'req_per_1s':        req_per_1s,
        'unique_paths_ratio': round(unique_ratio, 4),
        'error_rate':        round(error_rate, 4),
        'ua_entropy':        round(ua_entropy, 4),
        'avg_path_depth':    round(avg_depth, 4),
        'is_root_flood':     round(root_flood, 4),
        'ip_is_spoofed':     is_spoofed,
    }


def log_request(ip: str, path: str, status: int, ua: str,
                xff: str | None = None, label: int | None = None) -> dict:
    """
    Call this from the proxy on every request.
    If label is provided (0=benign, 1=ddos), appends to CSV for training.
    Returns the feature dict for immediate inference.
    """
    features = extract_features(ip, path, status, ua, xff)

    if label is not None:
        row = dict(features)
        row['label'] = label
        _append_csv(row)

    return features


def _append_csv(row: dict):
    global _CSV_HEADER_WRITTEN
    with open(CSV_PATH, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FEATURE_NAMES + ['label'])
        if not _CSV_HEADER_WRITTEN:
            writer.writeheader()
            _CSV_HEADER_WRITTEN = True
        writer.writerow(row)


def clear_ip(ip: str):
    """Call this after an IP is blocked to reset its window."""
    with _lock:
        _ip_windows.pop(ip, None)
