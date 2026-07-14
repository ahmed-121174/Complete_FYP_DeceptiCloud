"""
DDoS V1 - Model Training Pipeline
Trains Random Forest + Gradient Boosting + MLP ensemble.
Includes overfitting checks at every stage.
"""

import sys
import time
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.metrics import (
    balanced_accuracy_score, accuracy_score, classification_report,
    confusion_matrix, roc_auc_score, matthews_corrcoef, f1_score
)
from sklearn.model_selection import StratifiedKFold, cross_val_score
import warnings
warnings.filterwarnings('ignore')

# Add parent for preprocessing

sys.path.insert(0, str(Path(__file__).parent))
from preprocessing import DDoSPreprocessor

OUTPUT_DIR = Path(__file__).parent
MODELS_DIR = OUTPUT_DIR / "models"
LOGS_DIR = OUTPUT_DIR / "logs"

def overfitting_check(model_name, y_train, y_train_pred, y_test, y_test_pred):
    """
    Checks if model is overfitting by comparing train vs test metrics.
    Returns True if model PASSES (no overfitting), False if FAILS.
    """
    train_bal = balanced_accuracy_score(y_train, y_train_pred) * 100
    test_bal = balanced_accuracy_score(y_test, y_test_pred) * 100
    gap = train_bal - test_bal

    train_auc = roc_auc_score(y_train, y_train_pred)
    test_auc = roc_auc_score(y_test, y_test_pred)

    benign_recall_test = 0
    cm = confusion_matrix(y_test, y_test_pred)
    if cm.shape[0] > 1 and cm[0].sum() > 0:
        benign_recall_test = cm[0, 0] / cm[0].sum() * 100

    attack_recall_test = 0
    if cm.shape[0] > 1 and cm[1].sum() > 0:
        attack_recall_test = cm[1, 1] / cm[1].sum() * 100

    print(f"\n   OVERFITTING CHECK: {model_name}")
    print(f"  {''*55}")
    print(f"  {'Metric':<30} {'Train':>10} {'Test':>10} {'Status':>8}")
    print(f"  {''*55}")
    print(f"  {'Balanced Accuracy':<30} {train_bal:>9.2f}% {test_bal:>9.2f}% ", end="")

    passed = True
    issues = []

    # Check 1: Train-test gap < 5%

    if gap > 5:
        print(f"{' GAP':>8}")
        issues.append(f"Train-test gap: {gap:.2f}% (max 5%)")
        passed = False
    else:
        print(f"{'':>8}")

    print(f"  {'AUC':<30} {train_auc:>10.4f} {test_auc:>10.4f} ", end="")
    # Check 2: AUC > 0.85

    if test_auc < 0.85:
        print(f"{' LOW':>8}")
        issues.append(f"Test AUC: {test_auc:.4f} (min 0.85)")
        passed = False
    else:
        print(f"{'':>8}")

    print(f"  {'Benign Recall':<30} {'--':>10} {benign_recall_test:>9.2f}% ", end="")
    # Check 3: Benign recall > 0% (not memorizing)

    if benign_recall_test < 10:
        print(f"{' MEMO':>8}")
        issues.append(f"Benign recall: {benign_recall_test:.2f}% (model memorizing!)")
        passed = False
    else:
        print(f"{'':>8}")

    print(f"  {'Attack Recall':<30} {'--':>10} {attack_recall_test:>9.2f}% ", end="")
    if attack_recall_test < 50:
        print(f"{' LOW':>8}")
        issues.append(f"Attack recall too low: {attack_recall_test:.2f}%")
    else:
        print(f"{'':>8}")

    print(f"  {''*55}")

    if passed:
        print(f"   {model_name}: PASSED - No overfitting detected!")
    else:
        print(f"   {model_name}: ISSUES DETECTED:")
        for issue in issues:
            print(f"     - {issue}")

    return passed, {
        'train_balanced_acc': train_bal,
        'test_balanced_acc': test_bal,
        'gap': gap,
        'train_auc': train_auc,
        'test_auc': test_auc,
        'benign_recall': benign_recall_test,
        'attack_recall': attack_recall_test,
        'passed': passed
    }

def evaluate_model(name, model, X_test, y_test):
    """Full evaluation with all metrics."""
    y_pred = model.predict(X_test)
    y_prob = None
    try:
        y_prob = model.predict_proba(X_test)[:, 1]
    except:
        pass

    acc = accuracy_score(y_test, y_pred) * 100
    bal_acc = balanced_accuracy_score(y_test, y_pred) * 100
    mcc = matthews_corrcoef(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='macro') * 100
    auc = roc_auc_score(y_test, y_prob if y_prob is not None else y_pred)
    cm = confusion_matrix(y_test, y_pred)

    print(f"\n{'='*65}")
    print(f"   {name} - TEST SET RESULTS")
    print(f"{'='*65}")
    print(f"  Overall Accuracy:   {acc:.2f}%")
    print(f"  Balanced Accuracy:  {bal_acc:.2f}%")
    print(f"  F1 Score (macro):   {f1:.2f}%")
    print(f"  MCC:                {mcc:.4f}")
    print(f"  AUC:                {auc:.4f}")
    print(f"\n  Confusion Matrix:")
    print(f"                  Predicted")
    print(f"                Benign   Attack")
    print(f"    Benign    {cm[0,0]:>8,}  {cm[0,1]:>8,}")
    print(f"    Attack    {cm[1,0]:>8,}  {cm[1,1]:>8,}")
    print(f"\n  {classification_report(y_test, y_pred, target_names=['Benign','Attack'])}")

    return {
        'accuracy': acc, 'balanced_accuracy': bal_acc, 'mcc': mcc,
        'f1_macro': f1, 'auc': auc,
        'confusion_matrix': cm.tolist(),
        'benign_recall': cm[0,0] / cm[0].sum() * 100 if cm[0].sum() > 0 else 0,
        'attack_recall': cm[1,1] / cm[1].sum() * 100 if cm[1].sum() > 0 else 0,
        'benign_precision': cm[0,0] / (cm[0,0]+cm[1,0]) * 100 if (cm[0,0]+cm[1,0]) > 0 else 0,
        'attack_precision': cm[1,1] / (cm[1,1]+cm[0,1]) * 100 if (cm[1,1]+cm[0,1]) > 0 else 0,
    }

def cross_validate(name, model, X, y, n_folds=5):
    """Stratified K-Fold cross-validation for generalization check."""
    print(f"\n   {n_folds}-Fold Cross-Validation for {name}...")
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)
    scores = cross_val_score(model, X, y, cv=skf, scoring='balanced_accuracy', n_jobs=-1)
    print(f"     Fold scores: {[f'{s*100:.2f}%' for s in scores]}")
    print(f"     Mean: {scores.mean()*100:.2f}% ± {scores.std()*100:.2f}%")
    return scores.mean(), scores.std()

def main():
    start_time = time.time()

    print("\n" + ""*30)
    print("  DDoS V1 - ENSEMBLE MODEL TRAINING PIPELINE")
    print("  Strategy: Random Forest + Gradient Boosting")
    print("  Anti-Overfitting: SMOTE + Feature Selection + Cross-Validation")
    print(""*30)

    # STEP 1: PREPROCESSING

    preprocessor = DDoSPreprocessor(output_dir=str(OUTPUT_DIR))
    data = preprocessor.preprocess(data_dir="Datasets/DDoS_sampled", n_features=30)

    X_train = data['X_train']
    y_train = data['y_train']
    X_val = data['X_val']
    y_val = data['y_val']
    X_test = data['X_test']
    y_test = data['y_test']
    feature_names = data['feature_names']

    all_results = {}

    # STEP 2: TRAIN RANDOM FOREST

    print(f"\n{'='*80}")
    print("TRAINING MODEL 1: RANDOM FOREST")
    print(f"{'='*80}")
    print("  Config: n_estimators=200, max_depth=15, class_weight='balanced'")

    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_split=10,
        min_samples_leaf=5,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1,
        verbose=0
    )

    t0 = time.time()
    rf.fit(X_train, y_train)
    rf_train_time = time.time() - t0
    print(f"   Trained in {rf_train_time:.1f}s")

    # Overfitting check

    rf_train_pred = rf.predict(X_train)
    rf_test_pred = rf.predict(X_test)
    rf_passed, rf_check = overfitting_check("Random Forest", y_train, rf_train_pred, y_test, rf_test_pred)
    all_results['random_forest'] = evaluate_model("Random Forest", rf, X_test, y_test)
    all_results['random_forest']['train_time'] = rf_train_time

    # Cross-validation

    cv_mean, cv_std = cross_validate("Random Forest", rf, X_train, y_train)
    all_results['random_forest']['cv_mean'] = cv_mean * 100
    all_results['random_forest']['cv_std'] = cv_std * 100

    # STEP 3: TRAIN GRADIENT BOOSTING

    print(f"\n{'='*80}")
    print("TRAINING MODEL 2: GRADIENT BOOSTING")
    print(f"{'='*80}")
    print("  Config: n_estimators=100, max_depth=5, learning_rate=0.1")

    gb = GradientBoostingClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        subsample=0.8,
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=42,
        verbose=0
    )

    t0 = time.time()
    gb.fit(X_train, y_train)
    gb_train_time = time.time() - t0
    print(f"   Trained in {gb_train_time:.1f}s")

    # Overfitting check

    gb_train_pred = gb.predict(X_train)
    gb_test_pred = gb.predict(X_test)
    gb_passed, gb_check = overfitting_check("Gradient Boosting", y_train, gb_train_pred, y_test, gb_test_pred)
    all_results['gradient_boosting'] = evaluate_model("Gradient Boosting", gb, X_test, y_test)
    all_results['gradient_boosting']['train_time'] = gb_train_time

    # Cross-validation

    cv_mean, cv_std = cross_validate("Gradient Boosting", gb, X_train, y_train)
    all_results['gradient_boosting']['cv_mean'] = cv_mean * 100
    all_results['gradient_boosting']['cv_std'] = cv_std * 100

    # STEP 4: ENSEMBLE (Soft Voting)

    print(f"\n{'='*80}")
    print("CREATING ENSEMBLE (Soft Voting)")
    print(f"{'='*80}")

    ensemble = VotingClassifier(
        estimators=[('rf', rf), ('gb', gb)],
        voting='soft',
        n_jobs=-1
    )

    t0 = time.time()
    ensemble.fit(X_train, y_train)
    ens_train_time = time.time() - t0
    print(f"   Ensemble ready in {ens_train_time:.1f}s")

    # Overfitting check

    ens_train_pred = ensemble.predict(X_train)
    ens_test_pred = ensemble.predict(X_test)
    ens_passed, ens_check = overfitting_check("Ensemble", y_train, ens_train_pred, y_test, ens_test_pred)
    all_results['ensemble'] = evaluate_model("Ensemble (RF + GB)", ensemble, X_test, y_test)
    all_results['ensemble']['train_time'] = ens_train_time

    # STEP 5: SELECT BEST MODEL

    print(f"\n{'='*80}")
    print("MODEL COMPARISON")
    print(f"{'='*80}")

    print(f"\n  {'Model':<25} {'Bal. Acc':>10} {'AUC':>8} {'F1':>8} "
          f"{'Benign R':>10} {'Attack R':>10} {'Overfit':>10}")
    print(f"  {''*85}")

    best_model_name = None
    best_bal_acc = 0

    for name, metrics in all_results.items():
        label = name.replace('_', ' ').title()
        overfit = " PASS" if metrics.get('auc', 0) > 0.85 and metrics.get('benign_recall', 0) > 10 else " FAIL"
        print(f"  {label:<25} {metrics['balanced_accuracy']:>9.2f}% {metrics['auc']:>7.4f} "
              f"{metrics['f1_macro']:>7.2f}% {metrics['benign_recall']:>9.2f}% "
              f"{metrics['attack_recall']:>9.2f}% {overfit:>10}")

        if metrics['balanced_accuracy'] > best_bal_acc and metrics.get('benign_recall', 0) > 10:
            best_bal_acc = metrics['balanced_accuracy']
            best_model_name = name

    # STEP 6: SAVE BEST MODEL

    print(f"\n{'='*80}")
    print("SAVING MODELS")
    print(f"{'='*80}")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # Save all models

    joblib.dump(rf, MODELS_DIR / "random_forest.pkl")
    joblib.dump(gb, MODELS_DIR / "gradient_boosting.pkl")
    joblib.dump(ensemble, MODELS_DIR / "ensemble.pkl")
    print(f"   Saved all 3 models to {MODELS_DIR}/")

    # Determine best

    best_model = ensemble  # Default to ensemble
    if best_model_name == 'random_forest':
        best_model = rf
    elif best_model_name == 'gradient_boosting':
        best_model = gb

    joblib.dump(best_model, MODELS_DIR / "best_model.pkl")
    print(f"   Best model: {best_model_name} (saved as best_model.pkl)")

    # Save metadata

    metadata = {
        'best_model': best_model_name,
        'trained_at': datetime.now().isoformat(),
        'n_features': len(feature_names),
        'feature_names': feature_names,
        'results': {}
    }
    for name, metrics in all_results.items():
        # Convert numpy types

        clean = {}
        for k, v in metrics.items():
            if isinstance(v, (np.floating, np.integer)):
                clean[k] = float(v)
            elif isinstance(v, np.ndarray):
                clean[k] = v.tolist()
            else:
                clean[k] = v
        metadata['results'][name] = clean

    with open(MODELS_DIR / "metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)

    # FINAL SUMMARY

    total_time = time.time() - start_time

    print(f"\n{'='*80}")
    print(" DDoS V1 - TRAINING COMPLETE")
    print(f"{'='*80}")
    print(f"\n   Best Model: {best_model_name}")
    print(f"   Balanced Accuracy: {all_results[best_model_name]['balanced_accuracy']:.2f}%")
    print(f"   AUC: {all_results[best_model_name]['auc']:.4f}")
    print(f"   Benign Recall: {all_results[best_model_name]['benign_recall']:.2f}%")
    print(f"   Attack Recall: {all_results[best_model_name]['attack_recall']:.2f}%")
    print(f"    Total time: {total_time/60:.1f} minutes")
    print(f"\n  Files saved to: {MODELS_DIR}/")
    print(f"    - random_forest.pkl")
    print(f"    - gradient_boosting.pkl")
    print(f"    - ensemble.pkl")
    print(f"    - best_model.pkl")
    print(f"    - metadata.json")
    print(f"    - scaler.pkl")
    print(f"    - selected_features.pkl")

if __name__ == "__main__":
    main()
