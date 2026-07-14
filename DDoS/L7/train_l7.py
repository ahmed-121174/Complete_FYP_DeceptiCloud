"""
DDoS/L7/train_l7.py

Trains a lightweight Decision Tree on the HTTP-level features logged
by collect_data.py. Outputs:
  - DDoS/L7/models/l7_ddos_model.pkl
  - DDoS/L7/models/l7_threshold.txt
  - DDoS/L7/models/l7_metadata.json

Usage:
  1. Collect data:  run system normally, then run attack script
  2. python DDoS/L7/train_l7.py

For demo: a synthetic dataset is generated automatically if no CSV exists.
"""

import sys
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import (
    balanced_accuracy_score, classification_report,
    confusion_matrix, roc_auc_score, precision_recall_curve
)
from sklearn.preprocessing import StandardScaler

HERE       = Path(__file__).parent
DATA_PATH  = HERE / 'data' / 'http_features.csv'
MODELS_DIR = HERE / 'models'
MODELS_DIR.mkdir(parents=True, exist_ok=True)

FEATURE_NAMES = [
    'req_per_10s', 'req_per_1s', 'unique_paths_ratio',
    'error_rate', 'ua_entropy', 'avg_path_depth',
    'is_root_flood', 'ip_is_spoofed',
]


def generate_synthetic_data(n_benign=3000, n_attack=3000, seed=42):
    """
    Generate realistic synthetic training data that mirrors what
    ddos_attack.sh (30-60 curl workers, DDoS-Bot/N UA, random X-Forward-For)
    produces vs normal browsing traffic.
    """
    rng = np.random.default_rng(seed)

    # Benign: low rate, varied paths, low error, varied UA
    benign = {
        'req_per_10s':        rng.integers(1, 15, n_benign),
        'req_per_1s':         rng.integers(0, 3,  n_benign),
        'unique_paths_ratio': rng.uniform(0.5, 1.0, n_benign),
        'error_rate':         rng.uniform(0.0, 0.15, n_benign),
        'ua_entropy':         rng.uniform(2.0, 5.0, n_benign),
        'avg_path_depth':     rng.uniform(1.0, 4.0, n_benign),
        'is_root_flood':      rng.uniform(0.0, 0.3, n_benign),
        'ip_is_spoofed':      rng.integers(0, 2, n_benign) * 0.0,  # rarely spoofed
        'label':              np.zeros(n_benign, dtype=int),
    }

    # Attack: high rate, same endpoint, same UA pattern, spoofed IPs
    attack = {
        'req_per_10s':        rng.integers(40, 200, n_attack),
        'req_per_1s':         rng.integers(8,  50,  n_attack),
        'unique_paths_ratio': rng.uniform(0.01, 0.2, n_attack),
        'error_rate':         rng.uniform(0.3,  1.0, n_attack),
        'ua_entropy':         rng.uniform(0.0,  1.5, n_attack),   # DDoS-Bot/1..N has low entropy
        'avg_path_depth':     rng.uniform(0.0,  1.5, n_attack),   # hits '/' repeatedly
        'is_root_flood':      rng.uniform(0.6,  1.0, n_attack),
        'ip_is_spoofed':      np.ones(n_attack, dtype=float),     # X-Forward-For rotates
        'label':              np.ones(n_attack, dtype=int),
    }

    df_b = pd.DataFrame(benign)
    df_a = pd.DataFrame(attack)
    df   = pd.concat([df_b, df_a], ignore_index=True).sample(frac=1, random_state=seed)
    return df


def load_or_generate_data():
    if DATA_PATH.exists():
        df = pd.read_csv(DATA_PATH)
        print(f"  Loaded real data: {len(df):,} rows from {DATA_PATH}")
        if len(df) < 200:
            print("  Too few samples — augmenting with synthetic data")
            df = pd.concat([df, generate_synthetic_data(1500, 1500)], ignore_index=True)
    else:
        print("  No real data CSV found — generating synthetic training data")
        print("  (Run the attack script while the proxy logs, then retrain for real data)")
        df = generate_synthetic_data()
    return df


def find_threshold(model, X_val, y_val, scaler=None):
    Xv = scaler.transform(X_val) if scaler else X_val
    probs = model.predict_proba(Xv)[:, 1]
    precision, recall, thresholds = precision_recall_curve(y_val, probs)
    f1 = 2 * precision * recall / (precision + recall + 1e-10)
    idx = np.argmax(f1[:-1])
    return float(thresholds[idx])


def main():
    print("\n" + "="*60)
    print("  DDoS L7 HTTP DETECTOR — TRAINING")
    print("  Features: req_rate, burst, path_diversity, error_rate,")
    print("            ua_entropy, path_depth, root_flood, ip_spoof")
    print("="*60)

    df = load_or_generate_data()
    print(f"\n  Class balance:")
    print(f"    Benign: {(df['label']==0).sum():,}  Attack: {(df['label']==1).sum():,}")

    X = df[FEATURE_NAMES].astype(float)
    y = df['label'].astype(int)

    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=0.15 / 0.85, random_state=42, stratify=y_temp
    )

    # Scale — pass DataFrames so sklearn keeps feature names (no warnings)
    scaler = StandardScaler()
    X_train_s = pd.DataFrame(scaler.fit_transform(X_train), columns=FEATURE_NAMES)
    X_val_s   = pd.DataFrame(scaler.transform(X_val),       columns=FEATURE_NAMES)
    X_test_s  = pd.DataFrame(scaler.transform(X_test),      columns=FEATURE_NAMES)

    # Train Decision Tree (primary — fast, interpretable, deployable)
    print(f"\n{'='*60}")
    print("  TRAINING DECISION TREE (primary)")
    print(f"{'='*60}")
    dt = DecisionTreeClassifier(
        max_depth=6,
        min_samples_leaf=10,
        class_weight='balanced',
        random_state=42
    )
    dt.fit(X_train_s, y_train)

    # Threshold on val — if PR-curve returns 1.0 (perfectly separable synthetic data)
    # fall back to a practical rate-based threshold of 0.5
    threshold = find_threshold(dt, X_val, y_val, scaler)
    if threshold >= 0.999:
        threshold = 0.5
        print("  Note: PR-curve threshold=1.0 (perfectly separable data); overriding to 0.5")

    # Evaluate
    y_probs = dt.predict_proba(X_test_s)[:, 1]
    y_pred  = (y_probs >= threshold).astype(int)
    bal_acc = balanced_accuracy_score(y_test, y_pred) * 100
    auc     = roc_auc_score(y_test, y_probs)
    cm      = confusion_matrix(y_test, y_pred)
    benign_recall = cm[0, 0] / cm[0].sum() * 100 if cm[0].sum() > 0 else 0
    attack_recall = cm[1, 1] / cm[1].sum() * 100 if cm[1].sum() > 0 else 0

    # Gap check
    train_pred  = (dt.predict_proba(X_train_s)[:, 1] >= threshold).astype(int)
    train_bal   = balanced_accuracy_score(y_train, train_pred) * 100
    gap = train_bal - bal_acc

    print(f"\n  Balanced Accuracy:  {bal_acc:.2f}%")
    print(f"  AUC:                {auc:.4f}")
    print(f"  Benign Recall:      {benign_recall:.2f}%")
    print(f"  Attack Recall:      {attack_recall:.2f}%")
    print(f"  Train-Test Gap:     {gap:.2f}%  [{'PASS' if gap < 5 else 'FAIL'}]")
    print(f"  Threshold:          {threshold:.4f}")
    print(f"\n{classification_report(y_test, y_pred, target_names=['Benign','DDoS'])}")

    # Cross-validation
    skf    = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(dt, X_train_s, y_train,
                                cv=skf, scoring='balanced_accuracy')
    print(f"  CV (5-fold): {cv_scores.mean()*100:.2f}% ± {cv_scores.std()*100:.2f}%")

    # Feature importances
    print(f"\n  Feature Importances:")
    for feat, imp in sorted(zip(FEATURE_NAMES, dt.feature_importances_),
                            key=lambda x: -x[1]):
        print(f"    {feat:25s}  {imp:.4f}  {'█' * int(imp * 40)}")

    # Save
    joblib.dump(dt, MODELS_DIR / 'l7_ddos_model.pkl')
    joblib.dump(scaler, MODELS_DIR / 'l7_scaler.pkl')
    with open(MODELS_DIR / 'l7_threshold.txt', 'w') as f:
        f.write(str(threshold))

    metadata = {
        'model': 'DecisionTree',
        'version': 'L7-v1',
        'trained_at': datetime.now().isoformat(),
        'feature_names': FEATURE_NAMES,
        'threshold': threshold,
        'results': {
            'balanced_accuracy': round(bal_acc, 4),
            'auc': round(auc, 6),
            'benign_recall': round(benign_recall, 4),
            'attack_recall': round(attack_recall, 4),
            'train_test_gap': round(gap, 4),
            'cv_mean': round(cv_scores.mean() * 100, 4),
            'cv_std': round(cv_scores.std() * 100, 4),
        },
        'data_source': str(DATA_PATH) if DATA_PATH.exists() else 'synthetic'
    }
    with open(MODELS_DIR / 'l7_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\n  Saved → DDoS/L7/models/")
    print(f"    l7_ddos_model.pkl | l7_scaler.pkl | l7_threshold.txt | l7_metadata.json")
    print(f"\n  Training complete.")


if __name__ == '__main__':
    main()
