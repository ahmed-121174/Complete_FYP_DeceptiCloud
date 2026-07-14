"""
Web Attack Model - Training with Feature Engineering
Implements comprehensive feature extraction from SQL/NoSQL injection text
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import (balanced_accuracy_score, matthews_corrcoef,
                             classification_report, confusion_matrix,
                             precision_recall_curve, roc_curve, auc)
from imblearn.over_sampling import SMOTE
import tensorflow as tf
import matplotlib.pyplot as plt

sys.path.append(str(Path(__file__).parent))
from feature_engineering import WebAttackFeatureExtractor
from web_attack_model import WebAttackDetector

def load_and_clean_datasets():
    """Load and clean all CSV files"""
    print("STEP 1: LOADING ALL WEB ATTACK DATASETS")
    
    base_path = Path(__file__).parent.parent / "Datasets" / "SQLI-nosqli-XSS"
    all_csv_files = list(base_path.rglob("*.csv"))
    
    print(f"\n Found {len(all_csv_files)} CSV files")
    
    all_dataframes = []
    for csv_file in all_csv_files:
        try:
            df = pd.read_csv(csv_file, low_memory=False)
            df = df.drop_duplicates().dropna(how='all').dropna(axis=1, how='all')
            print(f"    {csv_file.name}: {len(df):,} rows")
            all_dataframes.append(df)
        except:
            continue
    
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    combined_df = combined_df.drop_duplicates()
    
    print(f"\n Combined: {len(combined_df):,} rows")
    return combined_df

def prepare_data_with_features(df):
    """Prepare data with feature engineering"""
    print("STEP 2: FEATURE ENGINEERING & DATA PREPARATION")
    
    # Detect label column

    label_col = None
    for col in df.columns:
        if 'label' in col.lower():
            label_col = col
            break
    
    if label_col is None:
        print(" No label column found!")
        return None
    
    # Get text column (Sentence or Query)

    text_col = None
    for col in ['Sentence', 'Query', 'sentence', 'query']:
        if col in df.columns:
            text_col = col
            break
    
    if text_col is None:
        print(" No text column found!")
        return None
    
    print(f"\n Text column: '{text_col}'")
    print(f"  Label column: '{label_col}'")
    
    # Extract labels

    print(f"\n1. Extracting labels...")
    unique_labels = df[label_col].unique()
    print(f"   Unique labels: {unique_labels[:10]}")
    
    # Normalize labels to 0/1

    label_set = set([str(v).strip() for v in unique_labels if pd.notna(v)])
    if label_set <= {'0', '1'}:
        y = df[label_col].fillna('1').astype(str).str.strip().astype(int)
    else:
        # Assume first value is benign

        benign_label = unique_labels[0]
        y = (df[label_col] != benign_label).astype(int)
    
    benign_count = (y == 0).sum()
    attack_count = (y == 1).sum()
    print(f"   Benign (0): {benign_count:,} ({benign_count/len(y)*100:.1f}%)")
    print(f"   Attack (1): {attack_count:,} ({attack_count/len(y)*100:.1f}%)")
    
    # Extract features

    print(f"\n2. Extracting features from text...")
    extractor = WebAttackFeatureExtractor()
    X_features = extractor.extract_features_batch(df[text_col])
    
    print(f"\n Feature extraction complete!")
    print(f"   Total features: {X_features.shape[1]}")
    print(f"   Total samples: {X_features.shape[0]:,}")
    
    return X_features, y

def find_optimal_threshold(model, X_val, y_val):
    """Find optimal classification threshold"""
    print("THRESHOLD OPTIMIZATION")
    
    y_probs = model.model.predict(X_val, verbose=0).flatten()
    
    # Compute precision-recall curve

    precision, recall, thresholds = precision_recall_curve(y_val, y_probs)
    
    # Find threshold that maximizes F1 score

    f1_scores = 2 * (precision * recall) / (precision + recall + 1e-10)
    optimal_idx = np.argmax(f1_scores)
    optimal_threshold = thresholds[optimal_idx] if optimal_idx < len(thresholds) else 0.5
    
    print(f"\n Threshold Analysis:")
    print(f"   Default threshold (0.5):")
    y_pred_default = (y_probs >= 0.5).astype(int)
    bal_acc_default = balanced_accuracy_score(y_val, y_pred_default)
    print(f"      Balanced Accuracy: {bal_acc_default*100:.2f}%")
    
    print(f"\n   Optimal threshold ({optimal_threshold:.4f}):")
    y_pred_optimal = (y_probs >= optimal_threshold).astype(int)
    bal_acc_optimal = balanced_accuracy_score(y_val, y_pred_optimal)
    print(f"      Balanced Accuracy: {bal_acc_optimal*100:.2f}%")
    print(f"      Precision: {precision[optimal_idx]*100:.2f}%")
    print(f"      Recall: {recall[optimal_idx]*100:.2f}%")
    print(f"      F1-Score: {f1_scores[optimal_idx]*100:.2f}%")
    
    return optimal_threshold

def main():
    print("WEB ATTACK MODEL - FEATURE ENGINEERING SOLUTION")
    
    tf.random.set_seed(42)
    np.random.seed(42)
    
    # Load data

    df = load_and_clean_datasets()
    
    # Extract features

    X, y = prepare_data_with_features(df)
    
    # Split data (stratified)

    print("STEP 3: SPLITTING DATA (STRATIFIED)")
    
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=0.125, random_state=42, stratify=y_temp  # 0.125 of 80% = 10% overall
    )
    
    print(f"\n Data split:")
    print(f"   Train: {len(y_train):,} samples")
    print(f"   Val:   {len(y_val):,} samples")
    print(f"   Test:  {len(y_test):,} samples")
    
    # Apply SMOTE to training data

    print("STEP 4: APPLYING SMOTE")
    
    print(f"\n Before SMOTE:")
    unique, counts = np.unique(y_train, return_counts=True)
    for u, c in zip(unique, counts):
        print(f"   Class {u}: {c:,} ({c/len(y_train)*100:.1f}%)")
    
    smote = SMOTE(random_state=42)
    X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)
    
    print(f"\n After SMOTE:")
    unique, counts = np.unique(y_train_balanced, return_counts=True)
    for u, c in zip(unique, counts):
        print(f"   Class {u}: {c:,} ({c/len(y_train_balanced)*100:.1f}%)")
    
    # Calculate class weights

    class_weights = compute_class_weight(
        'balanced', classes=np.unique(y_train_balanced), y=y_train_balanced
    )
    class_weight_dict = {i: class_weights[i] for i in range(len(class_weights))}
    print(f"\n  Class weights: {class_weight_dict}")
    
    # Build and train model

    print("STEP 5: TRAINING MODEL")
    
    detector = WebAttackDetector(input_dim=X_train_balanced.shape[1])
    detector.build_model()
    
    history = detector.train(
        X_train=X_train_balanced,
        y_train=y_train_balanced,
        X_val=X_val,
        y_val=y_val,
        epochs=100,
        batch_size=64,
        class_weight=class_weight_dict
    )
    
    # Find optimal threshold

    optimal_threshold = find_optimal_threshold(detector, X_val, y_val)
    
    # Evaluate on test set

    print("STEP 6: FINAL EVALUATION ON TEST SET")
    
    y_probs = detector.model.predict(X_test, verbose=0).flatten()
    y_pred = (y_probs >= optimal_threshold).astype(int)
    
    acc = np.mean(y_pred == y_test)
    bal_acc = balanced_accuracy_score(y_test, y_pred)
    mcc = matthews_corrcoef(y_test, y_pred)
    
    print(f"\n Test Results (threshold={optimal_threshold:.4f}):")
    print(f"   Accuracy:          {acc*100:.2f}%")
    print(f"   Balanced Accuracy: {bal_acc*100:.2f}%")
    print(f"   MCC:               {mcc:.4f}")
    
    cm = confusion_matrix(y_test, y_pred)
    print(f"\n Confusion Matrix:")
    print("                Predicted")
    print("              Benign  Attack")
    print(f"   Benign     {cm[0,0]:6d}  {cm[0,1]:6d}")
    print(f"   Attack     {cm[1,0]:6d}  {cm[1,1]:6d}")
    
    print(f"\n Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Benign', 'Attack']))
    
    # Success criteria

    print("SUCCESS CRITERIA CHECK")
    
    benign_precision = cm[0,0] / (cm[0,0] + cm[1,0]) if (cm[0,0] + cm[1,0]) > 0 else 0
    benign_recall = cm[0,0] / (cm[0,0] + cm[0,1]) if (cm[0,0] + cm[0,1]) > 0 else 0
    attack_precision = cm[1,1] / (cm[1,1] + cm[0,1]) if (cm[1,1] + cm[0,1]) > 0 else 0
    attack_recall = cm[1,1] / (cm[1,1] + cm[1,0]) if (cm[1,1] + cm[1,0]) > 0 else 0
    
    criteria = {
        "Overall Accuracy (80-95%)": (80 <= acc*100 <= 95, acc*100),
        "Benign Precision (>70%)": (benign_precision*100 > 70, benign_precision*100),
        "Benign Recall (>70%)": (benign_recall*100 > 70, benign_recall*100),
        "Attack Precision (>85%)": (attack_precision*100 > 85, attack_precision*100),
        "Attack Recall (>85%)": (attack_recall*100 > 85, attack_recall*100),
        "Balanced Accuracy (>80%)": (bal_acc*100 > 80, bal_acc*100),
    }
    
    all_passed = True
    for criterion, (passed, value) in criteria.items():
        status = " PASS" if passed else " FAIL"
        print(f"{criterion:35s}: {value:6.2f}%  {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n ALL CRITERIA MET - MODEL READY!")
    else:
        print("\n  SOME CRITERIA NOT MET")
    
    # Save model

    detector.save_model('models/web_attack_detector_v2.keras')
    
    # Save threshold

    with open('models/web_attack_threshold.txt', 'w') as f:
        f.write(str(optimal_threshold))
    
    print(f"\n Model saved: models/web_attack_detector_v2.keras")
    print(f" Threshold saved: models/web_attack_threshold.txt")

if __name__ == "__main__":
    main()
