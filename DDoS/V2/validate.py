"""
DDoS V2 - Standalone Validation Script
Loads the saved best_model.pkl and validates it against a fresh test split.
Fails with exit code 1 if success criteria not met.
"""

import sys
import json
import joblib
import numpy as np
from pathlib import Path
from sklearn.metrics import balanced_accuracy_score, roc_auc_score, confusion_matrix

PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT / 'DDoS' / 'V1'))

from preprocessing import DDoSPreprocessor

MODELS_DIR = PROJECT_ROOT / 'DDoS' / 'V1' / 'models'

SUCCESS_CRITERIA = {
    'balanced_accuracy': 90.0,
    'benign_recall': 85.0,
    'attack_recall': 90.0,
    'train_test_gap': 5.0,   # max allowed
}


def main():
    print("\n" + "="*60)
    print("  DDoS V2 — VALIDATION")
    print("="*60)

    # Load artifacts
    model     = joblib.load(MODELS_DIR / 'best_model.pkl')
    scaler    = joblib.load(MODELS_DIR / 'scaler.pkl')
    features  = joblib.load(MODELS_DIR / 'selected_features.pkl')

    threshold_path = MODELS_DIR / 'threshold.txt'
    threshold = float(threshold_path.read_text().strip()) if threshold_path.exists() else 0.5
    print(f"  Threshold: {threshold:.4f}")
    print(f"  Features:  {len(features)}")

    # Fresh preprocessing (new random_state=99 for independence)
    preprocessor = DDoSPreprocessor(output_dir=str(PROJECT_ROOT / 'DDoS' / 'V1'))
    preprocessor.scaler = scaler
    preprocessor.selected_features = features

    # Load data with alternate seed
    df = preprocessor.load_data(str(PROJECT_ROOT / 'Datasets' / 'DDoS_sampled'))
    df = preprocessor.clean_data(df)

    fc = [c for c in df.columns if c != preprocessor.label_col]
    X  = df[fc][features]   # only selected features
    y  = df[preprocessor.label_col]

    from sklearn.model_selection import train_test_split
    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.15, random_state=99, stratify=y   # different seed
    )

    X_test_scaled = scaler.transform(X_test)

    # Predict
    y_probs = model.predict_proba(X_test_scaled)[:, 1]
    y_pred  = (y_probs >= threshold).astype(int)

    bal_acc       = balanced_accuracy_score(y_test, y_pred) * 100
    auc           = roc_auc_score(y_test, y_probs)
    cm            = confusion_matrix(y_test, y_pred)
    benign_recall = cm[0, 0] / cm[0].sum() * 100 if cm[0].sum() > 0 else 0
    attack_recall = cm[1, 1] / cm[1].sum() * 100 if cm[1].sum() > 0 else 0

    # Train set check for gap
    _, X_train, _, y_train = train_test_split(
        X, y, test_size=0.85, random_state=99, stratify=y
    )
    X_train_scaled = scaler.transform(X_train)
    train_pred     = (model.predict_proba(X_train_scaled)[:, 1] >= threshold).astype(int)
    train_bal      = balanced_accuracy_score(y_train, train_pred) * 100
    gap            = train_bal - bal_acc

    print(f"\n  Results on held-out test (seed=99):")
    print(f"  Balanced Accuracy : {bal_acc:.2f}%   (min {SUCCESS_CRITERIA['balanced_accuracy']}%)")
    print(f"  AUC               : {auc:.4f}")
    print(f"  Benign Recall     : {benign_recall:.2f}%   (min {SUCCESS_CRITERIA['benign_recall']}%)")
    print(f"  Attack Recall     : {attack_recall:.2f}%   (min {SUCCESS_CRITERIA['attack_recall']}%)")
    print(f"  Train-Test Gap    : {gap:.2f}%   (max {SUCCESS_CRITERIA['train_test_gap']}%)")

    passed = all([
        bal_acc       >= SUCCESS_CRITERIA['balanced_accuracy'],
        benign_recall >= SUCCESS_CRITERIA['benign_recall'],
        attack_recall >= SUCCESS_CRITERIA['attack_recall'],
        gap           <= SUCCESS_CRITERIA['train_test_gap'],
    ])

    print(f"\n{'='*60}")
    if passed:
        print("  VALIDATION PASSED — model is production ready")
    else:
        print("  VALIDATION FAILED — criteria not met:")
        if bal_acc       < SUCCESS_CRITERIA['balanced_accuracy']:
            print(f"    - Balanced accuracy {bal_acc:.2f}% < {SUCCESS_CRITERIA['balanced_accuracy']}%")
        if benign_recall < SUCCESS_CRITERIA['benign_recall']:
            print(f"    - Benign recall {benign_recall:.2f}% < {SUCCESS_CRITERIA['benign_recall']}%")
        if attack_recall < SUCCESS_CRITERIA['attack_recall']:
            print(f"    - Attack recall {attack_recall:.2f}% < {SUCCESS_CRITERIA['attack_recall']}%")
        if gap > SUCCESS_CRITERIA['train_test_gap']:
            print(f"    - Gap {gap:.2f}% > {SUCCESS_CRITERIA['train_test_gap']}%")
    print(f"{'='*60}")

    sys.exit(0 if passed else 1)


if __name__ == '__main__':
    main()
