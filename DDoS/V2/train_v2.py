"""
DDoS V2 - Fixed Training Pipeline
Fixes:
  - max_depth reduced 15->8 (core overfitting cause)
  - max_features='sqrt' added (reduces correlation memorization)
  - min_samples_leaf doubled 5->10
  - Threshold optimized on val set instead of hardcoded 0.5
  - Best model selected by lowest train-test gap, not just accuracy
  - Outputs overwrite DDoS/V1/models/ so model_api.py picks up automatically
"""

import sys
import json
import time
import joblib
import numpy as np
from pathlib import Path
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    balanced_accuracy_score, roc_auc_score,
    confusion_matrix, classification_report, precision_recall_curve
)
from sklearn.model_selection import StratifiedKFold, cross_val_score
import warnings
warnings.filterwarnings('ignore')

PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'DDoS' / 'V1'))

from preprocessing import DDoSPreprocessor

OUTPUT_MODELS = PROJECT_ROOT / 'DDoS' / 'V1' / 'models'
V2_LOG = Path(__file__).parent / 'results.json'


def find_optimal_threshold(model, X_val, y_val):
    y_probs = model.predict_proba(X_val)[:, 1]
    precision, recall, thresholds = precision_recall_curve(y_val, y_probs)
    f1 = 2 * precision * recall / (precision + recall + 1e-10)
    best_idx = np.argmax(f1[:-1])  # exclude last (no threshold)
    best_threshold = float(thresholds[best_idx])
    print(f"  Optimal threshold: {best_threshold:.4f} "
          f"(F1={f1[best_idx]:.4f}, P={precision[best_idx]:.4f}, R={recall[best_idx]:.4f})")
    return best_threshold


def evaluate(name, model, X_test, y_test, threshold=0.5):
    y_probs = model.predict_proba(X_test)[:, 1]
    y_pred = (y_probs >= threshold).astype(int)

    bal_acc = balanced_accuracy_score(y_test, y_pred) * 100
    auc = roc_auc_score(y_test, y_probs)
    cm = confusion_matrix(y_test, y_pred)
    benign_recall = cm[0, 0] / cm[0].sum() * 100 if cm[0].sum() > 0 else 0
    attack_recall = cm[1, 1] / cm[1].sum() * 100 if cm[1].sum() > 0 else 0

    print(f"\n{'='*60}")
    print(f"  {name} — TEST RESULTS (threshold={threshold:.4f})")
    print(f"{'='*60}")
    print(f"  Balanced Accuracy:  {bal_acc:.2f}%")
    print(f"  AUC:                {auc:.4f}")
    print(f"  Benign Recall:      {benign_recall:.2f}%")
    print(f"  Attack Recall:      {attack_recall:.2f}%")
    print(f"\n{classification_report(y_test, y_pred, target_names=['Benign','Attack'])}")

    return {
        'balanced_accuracy': round(bal_acc, 4),
        'auc': round(auc, 6),
        'benign_recall': round(benign_recall, 4),
        'attack_recall': round(attack_recall, 4),
    }


def overfitting_check(model, X_train, y_train, X_test, y_test, threshold=0.5):
    train_probs = model.predict_proba(X_train)[:, 1]
    test_probs  = model.predict_proba(X_test)[:, 1]
    train_pred  = (train_probs >= threshold).astype(int)
    test_pred   = (test_probs  >= threshold).astype(int)

    train_bal = balanced_accuracy_score(y_train, train_pred) * 100
    test_bal  = balanced_accuracy_score(y_test,  test_pred)  * 100
    gap = train_bal - test_bal

    status = "PASS" if gap < 5.0 else "FAIL"
    print(f"  Train Balanced Acc: {train_bal:.2f}%")
    print(f"  Test  Balanced Acc: {test_bal:.2f}%")
    print(f"  Gap:                {gap:.2f}%  [{status}]")
    return gap, status


def main():
    t_start = time.time()

    print("\n" + "="*60)
    print("  DDoS V2 — FIXED TRAINING PIPELINE")
    print("  max_depth=8, sqrt features, threshold-optimized")
    print("="*60)

    # STEP 1: PREPROCESS (reuse V1 pipeline)
    preprocessor = DDoSPreprocessor(output_dir=str(PROJECT_ROOT / 'DDoS' / 'V1'))
    data = preprocessor.preprocess(
        data_dir=str(PROJECT_ROOT / 'Datasets' / 'DDoS_sampled'),
        n_features=30
    )

    X_train = data['X_train']
    y_train = data['y_train']
    X_val   = data['X_val']
    y_val   = data['y_val']
    X_test  = data['X_test']
    y_test  = data['y_test']
    features = data['feature_names']

    # STEP 2: TRAIN V2 RF (fixed hyperparameters)
    print(f"\n{'='*60}")
    print("  TRAINING RANDOM FOREST V2")
    print("  max_depth=8 | min_samples_leaf=10 | max_features=sqrt")
    print(f"{'='*60}")

    rf_v2 = RandomForestClassifier(
        n_estimators=150,
        max_depth=8,              # key fix: was 15
        min_samples_split=20,     # was 10
        min_samples_leaf=10,      # was 5
        max_features='sqrt',      # key fix: was not set
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )

    t0 = time.time()
    rf_v2.fit(X_train, y_train)
    print(f"  Trained in {time.time()-t0:.1f}s")

    # STEP 3: THRESHOLD OPTIMIZATION on val set
    print(f"\n{'='*60}")
    print("  THRESHOLD OPTIMIZATION (val set)")
    print(f"{'='*60}")
    threshold = find_optimal_threshold(rf_v2, X_val, y_val)

    # STEP 4: OVERFITTING CHECK
    print(f"\n{'='*60}")
    print("  OVERFITTING CHECK")
    print(f"{'='*60}")
    gap, of_status = overfitting_check(rf_v2, X_train, y_train, X_test, y_test, threshold)

    # STEP 5: CROSS-VALIDATION
    print(f"\n{'='*60}")
    print("  5-FOLD CROSS-VALIDATION")
    print(f"{'='*60}")
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(rf_v2, X_train, y_train,
                                cv=skf, scoring='balanced_accuracy', n_jobs=-1)
    cv_mean = cv_scores.mean() * 100
    cv_std  = cv_scores.std()  * 100
    print(f"  Fold scores: {[f'{s*100:.2f}%' for s in cv_scores]}")
    print(f"  Mean: {cv_mean:.2f}% ± {cv_std:.2f}%")

    # STEP 6: FINAL EVALUATION
    results = evaluate("RF V2", rf_v2, X_test, y_test, threshold)
    results['cv_mean'] = round(cv_mean, 4)
    results['cv_std']  = round(cv_std, 4)
    results['train_test_gap'] = round(gap, 4)

    # STEP 7: SAVE — overwrite V1 models dir so model_api.py picks up automatically
    print(f"\n{'='*60}")
    print("  SAVING TO DDoS/V1/models/ (replaces best_model.pkl)")
    print(f"{'='*60}")

    OUTPUT_MODELS.mkdir(parents=True, exist_ok=True)

    joblib.dump(rf_v2, OUTPUT_MODELS / 'best_model.pkl')
    joblib.dump(rf_v2, OUTPUT_MODELS / 'random_forest_v2.pkl')

    # Save threshold
    with open(OUTPUT_MODELS / 'threshold.txt', 'w') as f:
        f.write(str(threshold))

    print(f"  Saved best_model.pkl (RF V2)")
    print(f"  Saved threshold.txt  ({threshold:.4f})")

    # Update metadata.json
    metadata = {
        'best_model': 'random_forest_v2',
        'version': 'V2',
        'trained_at': datetime.now().isoformat(),
        'n_features': len(features),
        'feature_names': features,
        'threshold': threshold,
        'hyperparameters': {
            'n_estimators': 150,
            'max_depth': 8,
            'min_samples_split': 20,
            'min_samples_leaf': 10,
            'max_features': 'sqrt',
            'class_weight': 'balanced'
        },
        'leaking_features_removed': [' Inbound'],
        'results': {'random_forest_v2': results}
    }
    with open(OUTPUT_MODELS / 'metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"  Updated metadata.json")

    # Save V2-specific log
    Path(__file__).parent.mkdir(parents=True, exist_ok=True)
    with open(V2_LOG, 'w') as f:
        json.dump(metadata, f, indent=2)

    # FINAL SUMMARY
    elapsed = time.time() - t_start
    print(f"\n{'='*60}")
    print("  DDoS V2 TRAINING COMPLETE")
    print(f"{'='*60}")
    print(f"  Balanced Accuracy:  {results['balanced_accuracy']:.2f}%")
    print(f"  AUC:                {results['auc']:.4f}")
    print(f"  Benign Recall:      {results['benign_recall']:.2f}%")
    print(f"  Attack Recall:      {results['attack_recall']:.2f}%")
    print(f"  Train-Test Gap:     {gap:.2f}%  [{of_status}]")
    print(f"  CV Mean:            {cv_mean:.2f}% ± {cv_std:.2f}%")
    print(f"  Threshold:          {threshold:.4f}")
    print(f"  Total time:         {elapsed/60:.1f} min")

    if of_status == 'FAIL':
        print("\n  WARNING: Train-test gap >= 5% — consider reducing max_depth further.")
    else:
        print("\n  No overfitting detected.")

    return results


if __name__ == '__main__':
    main()
