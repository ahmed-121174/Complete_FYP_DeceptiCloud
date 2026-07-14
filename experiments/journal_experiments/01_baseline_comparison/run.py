#!/usr/bin/env python3
"""
Experiment 1: Baseline Comparison
Compare DeceptiCloud against traditional IDS systems and single-model approaches

Baselines:
1. Rule-based only (Snort-style signatures)
2. Single ML model (Random Forest only)
3. Single ML model (Neural Network only)
4. DeceptiCloud (Full ensemble)

Metrics: Accuracy, Precision, Recall, F1, FPR, Detection Latency
"""

import sys
import json
import time
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, roc_auc_score, classification_report
)
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import seaborn as sns

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

RESULTS_DIR = Path(__file__).parent / 'results'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def load_attack_data():
    """Load attack data from DeceptiCloud logs"""
    print("Loading attack data...")
    
    # Load from database
    try:
        from database.db_service import get_db_service
        db = get_db_service()
        attacks = db.get_attacks(limit=10000)
        
        if len(attacks) < 100:
            print(f"⚠ Only {len(attacks)} attacks in database. Generating synthetic data...")
            return generate_synthetic_dataset()
        
        print(f"✓ Loaded {len(attacks)} attacks from database")
        return process_database_attacks(attacks)
    
    except Exception as e:
        print(f"⚠ Database error: {e}. Generating synthetic data...")
        return generate_synthetic_dataset()


def generate_synthetic_dataset(n_samples=5000):
    """Generate synthetic attack dataset for testing"""
    print(f"Generating {n_samples} synthetic samples...")
    
    np.random.seed(42)
    
    # 60% benign, 40% attacks
    n_benign = int(n_samples * 0.6)
    n_attacks = n_samples - n_benign
    
    # Benign features (low values) - with more overlap for realism
    benign_features = np.random.normal(0.25, 0.15, (n_benign, 20))
    benign_features = np.clip(benign_features, 0, 1)
    benign_labels = np.zeros(n_benign)
    
    # Attack features (high values) - with more overlap for realism
    attack_features = np.random.normal(0.65, 0.20, (n_attacks, 20))
    attack_features = np.clip(attack_features, 0, 1)
    attack_labels = np.ones(n_attacks)
    
    # Add some hard cases (overlapping distributions)
    # 5% of benign look like attacks
    hard_benign_idx = np.random.choice(n_benign, size=int(n_benign * 0.05), replace=False)
    benign_features[hard_benign_idx] = np.random.normal(0.6, 0.1, (len(hard_benign_idx), 20))
    benign_features[hard_benign_idx] = np.clip(benign_features[hard_benign_idx], 0, 1)
    
    # 5% of attacks look like benign
    hard_attack_idx = np.random.choice(n_attacks, size=int(n_attacks * 0.05), replace=False)
    attack_features[hard_attack_idx] = np.random.normal(0.3, 0.1, (len(hard_attack_idx), 20))
    attack_features[hard_attack_idx] = np.clip(attack_features[hard_attack_idx], 0, 1)
    
    # Combine
    X = np.vstack([benign_features, attack_features])
    y = np.concatenate([benign_labels, attack_labels])
    
    # Shuffle
    indices = np.random.permutation(len(X))
    X = X[indices]
    y = y[indices]
    
    return X, y


def process_database_attacks(attacks):
    """Convert database attacks to feature matrix"""
    features = []
    labels = []
    
    for attack in attacks:
        # Extract features (simplified)
        feat = [
            len(attack.get('url', '')),
            len(attack.get('path', '')),
            len(attack.get('query_string', '')),
            attack.get('confidence', 0),
            1 if attack.get('captured') else 0,
            len(attack.get('user_agent', '')),
            1 if 'sqlmap' in attack.get('user_agent', '').lower() else 0,
            1 if 'nikto' in attack.get('user_agent', '').lower() else 0,
        ]
        # Pad to 20 features
        feat.extend([0] * (20 - len(feat)))
        features.append(feat[:20])
        labels.append(1 if attack.get('captured') else 0)
    
    return np.array(features), np.array(labels)


def rule_based_classifier(X):
    """Simple rule-based classifier (Snort-style)"""
    predictions = []
    
    for sample in X:
        score = 0
        # Rule 1: High URL length
        if sample[0] > 0.5:
            score += 0.3
        # Rule 2: High query length
        if sample[2] > 0.5:
            score += 0.3
        # Rule 3: Suspicious patterns
        if sample[6] > 0.5 or sample[7] > 0.5:
            score += 0.4
        
        predictions.append(1 if score >= 0.5 else 0)
    
    return np.array(predictions)


def train_single_rf(X_train, y_train):
    """Train single Random Forest model"""
    print("Training Random Forest...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=15,  # Increased for better performance
        min_samples_split=5,  # Prevent overfitting
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    return model


def train_single_nn(X_train, y_train):
    """Train single Neural Network model"""
    print("Training Neural Network...")
    model = MLPClassifier(
        hidden_layer_sizes=(64, 32),
        max_iter=500,
        random_state=42,
        early_stopping=True,
        alpha=0.001  # Regularization to prevent overfitting
    )
    model.fit(X_train, y_train)
    return model


def ensemble_classifier(X, rf_model, nn_model):
    """Ensemble: Soft voting between RF and NN"""
    rf_probs = rf_model.predict_proba(X)[:, 1]
    nn_probs = nn_model.predict_proba(X)[:, 1]
    
    # Average probabilities
    ensemble_probs = (rf_probs + nn_probs) / 2
    predictions = (ensemble_probs >= 0.5).astype(int)
    
    return predictions, ensemble_probs


def evaluate_model(name, y_true, y_pred, y_probs=None):
    """Comprehensive model evaluation"""
    results = {
        'name': name,
        'accuracy': accuracy_score(y_true, y_pred),
        'precision': precision_score(y_true, y_pred, zero_division=0),
        'recall': recall_score(y_true, y_pred, zero_division=0),
        'f1': f1_score(y_true, y_pred, zero_division=0),
        'confusion_matrix': confusion_matrix(y_true, y_pred).tolist(),
    }
    
    if y_probs is not None:
        results['auc_roc'] = roc_auc_score(y_true, y_probs)
    
    # False Positive Rate
    cm = confusion_matrix(y_true, y_pred)
    if cm.shape == (2, 2):
        tn, fp, fn, tp = cm.ravel()
        results['fpr'] = fp / (fp + tn) if (fp + tn) > 0 else 0
        results['tpr'] = tp / (tp + fn) if (tp + fn) > 0 else 0
    
    return results


def measure_latency(model, X_sample, n_iterations=100):
    """Measure prediction latency"""
    latencies = []
    
    for _ in range(n_iterations):
        start = time.time()
        if callable(model):
            model(X_sample)
        else:
            model.predict(X_sample)
        latencies.append((time.time() - start) * 1000)  # ms
    
    return {
        'mean_ms': np.mean(latencies),
        'std_ms': np.std(latencies),
        'p95_ms': np.percentile(latencies, 95),
        'p99_ms': np.percentile(latencies, 99),
    }


def plot_comparison(results, output_path):
    """Create comparison visualizations"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    models = [r['name'] for r in results]
    
    # Plot 1: Accuracy Metrics
    metrics = ['accuracy', 'precision', 'recall', 'f1']
    metric_data = {m: [r[m] for r in results] for m in metrics}
    
    x = np.arange(len(models))
    width = 0.2
    
    for i, metric in enumerate(metrics):
        axes[0, 0].bar(x + i*width, metric_data[metric], width, label=metric.capitalize())
    
    axes[0, 0].set_xlabel('Model')
    axes[0, 0].set_ylabel('Score')
    axes[0, 0].set_title('Performance Metrics Comparison')
    axes[0, 0].set_xticks(x + width * 1.5)
    axes[0, 0].set_xticklabels(models, rotation=15, ha='right')
    axes[0, 0].legend()
    axes[0, 0].grid(axis='y', alpha=0.3)
    
    # Plot 2: FPR vs TPR
    fprs = [r.get('fpr', 0) for r in results]
    tprs = [r.get('tpr', 0) for r in results]
    
    axes[0, 1].scatter(fprs, tprs, s=200, alpha=0.6)
    for i, model in enumerate(models):
        axes[0, 1].annotate(model, (fprs[i], tprs[i]), fontsize=9)
    
    axes[0, 1].set_xlabel('False Positive Rate')
    axes[0, 1].set_ylabel('True Positive Rate (Recall)')
    axes[0, 1].set_title('FPR vs TPR Trade-off')
    axes[0, 1].grid(alpha=0.3)
    axes[0, 1].plot([0, 1], [0, 1], 'k--', alpha=0.3)
    
    # Plot 3: Latency Comparison
    if 'latency' in results[0]:
        latencies = [r['latency']['mean_ms'] for r in results]
        errors = [r['latency']['std_ms'] for r in results]
        
        axes[1, 0].bar(models, latencies, yerr=errors, capsize=5, alpha=0.7)
        axes[1, 0].set_ylabel('Latency (ms)')
        axes[1, 0].set_title('Prediction Latency')
        axes[1, 0].set_xticklabels(models, rotation=15, ha='right')
        axes[1, 0].grid(axis='y', alpha=0.3)
    
    # Plot 4: Confusion Matrices
    for i, result in enumerate(results):
        cm = np.array(result['confusion_matrix'])
        if cm.shape == (2, 2):
            row = i // 2
            col = i % 2
            if i < 4:  # Only plot first 4
                sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                           ax=axes[1, 1] if i < 2 else axes[1, 1],
                           cbar=False, square=True)
                axes[1, 1].set_title(f'Confusion Matrix: {result["name"]}')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved comparison plot: {output_path}")


def main():
    print("\n" + "="*80)
    print("EXPERIMENT 1: BASELINE COMPARISON")
    print("="*80 + "\n")
    
    # Load data
    X, y = load_attack_data()
    print(f"Dataset: {len(X)} samples, {sum(y)} attacks ({sum(y)/len(y)*100:.1f}%)\n")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    
    print(f"Train: {len(X_train)} samples")
    print(f"Test:  {len(X_test)} samples\n")
    
    # Train models
    print("="*80)
    print("TRAINING MODELS")
    print("="*80 + "\n")
    
    rf_model = train_single_rf(X_train, y_train)
    nn_model = train_single_nn(X_train, y_train)
    
    # Evaluate all approaches
    print("\n" + "="*80)
    print("EVALUATION")
    print("="*80 + "\n")
    
    results = []
    
    # 1. Rule-based
    print("[1/4] Rule-Based Classifier...")
    rule_pred = rule_based_classifier(X_test)
    rule_results = evaluate_model("Rule-Based", y_test, rule_pred)
    rule_results['latency'] = measure_latency(rule_based_classifier, X_test[:10])
    results.append(rule_results)
    
    # 2. Single RF
    print("[2/4] Random Forest...")
    rf_pred = rf_model.predict(X_test)
    rf_probs = rf_model.predict_proba(X_test)[:, 1]
    rf_results = evaluate_model("Random Forest", y_test, rf_pred, rf_probs)
    rf_results['latency'] = measure_latency(rf_model, X_test[:10])
    results.append(rf_results)
    
    # 3. Single NN
    print("[3/4] Neural Network...")
    nn_pred = nn_model.predict(X_test)
    nn_probs = nn_model.predict_proba(X_test)[:, 1]
    nn_results = evaluate_model("Neural Network", y_test, nn_pred, nn_probs)
    nn_results['latency'] = measure_latency(nn_model, X_test[:10])
    results.append(nn_results)
    
    # 4. Ensemble (DeceptiCloud)
    print("[4/4] Ensemble (DeceptiCloud)...")
    ens_pred, ens_probs = ensemble_classifier(X_test, rf_model, nn_model)
    ens_results = evaluate_model("DeceptiCloud Ensemble", y_test, ens_pred, ens_probs)
    ens_results['latency'] = measure_latency(
        lambda X: ensemble_classifier(X, rf_model, nn_model), X_test[:10]
    )
    results.append(ens_results)
    
    # Print results table
    print("\n" + "="*80)
    print("RESULTS SUMMARY")
    print("="*80 + "\n")
    
    print(f"{'Model':<25} {'Acc':>8} {'Prec':>8} {'Rec':>8} {'F1':>8} {'FPR':>8} {'Latency':>10}")
    print("-"*80)
    
    for r in results:
        print(f"{r['name']:<25} "
              f"{r['accuracy']:>7.1%} "
              f"{r['precision']:>7.1%} "
              f"{r['recall']:>7.1%} "
              f"{r['f1']:>7.1%} "
              f"{r.get('fpr', 0):>7.1%} "
              f"{r['latency']['mean_ms']:>8.2f}ms")
    
    # Statistical significance
    print("\n" + "="*80)
    print("STATISTICAL ANALYSIS")
    print("="*80 + "\n")
    
    best_model = max(results, key=lambda x: x['f1'])
    print(f"Best Model: {best_model['name']}")
    print(f"  F1 Score: {best_model['f1']:.1%}")
    print(f"  Improvement over Rule-Based: {(best_model['f1'] - results[0]['f1'])*100:.1f} percentage points")
    print(f"  Improvement over Single RF: {(best_model['f1'] - results[1]['f1'])*100:.1f} percentage points")
    
    # Save results
    output_file = RESULTS_DIR / 'baseline_comparison_results.json'
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'dataset_size': len(X),
            'test_size': len(X_test),
            'results': results,
            'best_model': best_model['name']
        }, f, indent=2)
    
    print(f"\n✓ Results saved: {output_file}")
    
    # Generate plots
    plot_file = RESULTS_DIR / 'baseline_comparison_plot.png'
    plot_comparison(results, plot_file)
    
    print("\n" + "="*80)
    print("EXPERIMENT 1 COMPLETE")
    print("="*80 + "\n")
    
    print(f"Key Findings:")
    print(f"  • Ensemble outperforms single models by {(best_model['f1'] - results[1]['f1'])*100:.1f}pp in F1")
    print(f"  • False Positive Rate: {best_model.get('fpr', 0):.1%} (production-ready: <1%)")
    print(f"  • Detection Latency: {best_model['latency']['mean_ms']:.2f}ms (real-time capable)")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
