#!/usr/bin/env python3
"""
Test all available model files to find the correct one
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.metrics import balanced_accuracy_score, matthews_corrcoef, confusion_matrix
import tensorflow as tf

# Add code directory to path

sys.path.insert(0, str(Path(__file__).parent / "V2-SQLI-XSS-NoSQLi/code"))
from feature_engineering import WebAttackFeatureExtractor
from sklearn.model_selection import train_test_split

print("TESTING ALL MODEL FILES")

# List of all model files to test

model_files = [
    "V2-SQLI-XSS-NoSQLi/models/web_attack_detector_v2.keras",
    "V2-SQLI-XSS-NoSQLi/models/web_attack_best_model.keras",
    "ml_pipeline/models/web_attack_detector_v2.keras",
    "ml_pipeline/models/web_attack_detector_fixed.keras",
    "ml_pipeline/models/web_attack_detector.keras",
    "ml_pipeline/models/web_attack_best_model.keras",
]

# Load original dataset

print("\n Loading original dataset...")
original_dataset_path = Path("Orignal_dataset")
csv_files = list(original_dataset_path.rglob("*.csv"))

dataframes = []
for csv_file in csv_files:
    for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
        try:
            df = pd.read_csv(csv_file, encoding=encoding, low_memory=False)
            dataframes.append(df)
            break
        except:
            continue

combined_df = pd.concat(dataframes, ignore_index=True).drop_duplicates()
print(f" Loaded {len(combined_df):,} samples")

# Find columns

text_col = next((col for col in ['Sentence', 'Query', 'sentence', 'query'] if col in combined_df.columns), None)
label_col = [col for col in combined_df.columns if 'label' in col.lower()][0]

# Normalize labels

unique_labels = combined_df[label_col].unique()
label_set = set([str(v).strip() for v in unique_labels if pd.notna(v)])

if label_set <= {'0', '1'}:
    y = combined_df[label_col].fillna('1').astype(str).str.strip().astype(int)
else:
    benign_label = unique_labels[0]
    y = (combined_df[label_col] != benign_label).astype(int)

# Extract features

print(f" Extracting 52 features...")
extractor = WebAttackFeatureExtractor()
X_features = extractor.extract_features_batch(combined_df[text_col])
print(f" Features extracted: {X_features.shape}")

# Split (random_state=42 to match training)

_, X_test, _, y_test = train_test_split(
    X_features, y, test_size=0.2, random_state=42, stratify=y
)

print(f" Test set: {len(y_test):,} samples")
print(f"   - Benign: {(y_test==0).sum():,}")
print(f"   - Attack: {(y_test==1).sum():,}\n")

# Test each model

print("TESTING MODELS")

results = []

for model_path in model_files:
    model_file = Path(model_path)
    
    if not model_file.exists():
        print(f"\n {model_path} - NOT FOUND")
        continue
    
    print(f"\n Testing: {model_path}")
    
    try:
        model = tf.keras.models.load_model(model_path)
        print(f"   Parameters: {model.count_params():,}")
        
        # Predict

        y_probs = model.predict(X_test, verbose=0).flatten()
        y_pred = (y_probs >= 0.5).astype(int)
        
        # Metrics

        acc = np.mean(y_pred == y_test) * 100
        bal_acc = balanced_accuracy_score(y_test, y_pred) * 100
        mcc = matthews_corrcoef(y_test, y_pred)
        cm = confusion_matrix(y_test, y_pred)
        
        # Per-class metrics

        benign_prec = cm[0,0] / (cm[0,0] + cm[1,0]) * 100 if (cm[0,0] + cm[1,0]) > 0 else 0
        benign_rec = cm[0,0] / (cm[0,0] + cm[0,1]) * 100 if (cm[0,0] + cm[0,1]) > 0 else 0
        attack_prec = cm[1,1] / (cm[1,1] + cm[0,1]) * 100 if (cm[1,1] + cm[0,1]) > 0 else 0
        attack_rec = cm[1,1] / (cm[1,1] + cm[1,0]) * 100 if (cm[1,1] + cm[1,0]) > 0 else 0
        
        print(f"   Overall Acc: {acc:.2f}%")
        print(f"   Balanced Acc: {bal_acc:.2f}%")
        print(f"   MCC: {mcc:.4f}")
        print(f"   Confusion Matrix:")
        print(f"      Benign: {cm[0,0]:6,}  {cm[0,1]:6,}")
        print(f"      Attack: {cm[1,0]:6,}  {cm[1,1]:6,}")
        
        # Check if close to target

        target_bal_acc = 93.97
        target_acc = 89.69
        
        diff_bal = abs(bal_acc - target_bal_acc)
        diff_acc = abs(acc - target_acc)
        
        if diff_bal < 5.0 and diff_acc < 5.0:
            status = " CLOSE MATCH!"
        elif diff_bal < 10.0:
            status = "  Partial match"
        else:
            status = " No match"
        
        print(f"   Status: {status} (diff: {diff_bal:.2f}% bal_acc, {diff_acc:.2f}% acc)")
        
        results.append({
            'model': model_path,
            'acc': acc,
            'bal_acc': bal_acc,
            'mcc': mcc,
            'cm': cm,
            'status': status,
            'diff_bal': diff_bal,
            'diff_acc': diff_acc
        })
        
    except Exception as e:
        print(f"    Error: {str(e)[:100]}")

# Summary

print("SUMMARY")

if results:
    # Sort by closest to target balanced accuracy

    results_sorted = sorted(results, key=lambda x: x['diff_bal'])
    
    print(f"\nBest Match:")
    best = results_sorted[0]
    print(f"   Model: {best['model']}")
    print(f"   Balanced Accuracy: {best['bal_acc']:.2f}% (target: 93.97%)")
    print(f"   Overall Accuracy: {best['acc']:.2f}% (target: 89.69%)")
    print(f"   MCC: {best['mcc']:.4f} (target: 0.5704)")
    print(f"   {best['status']}")
else:
    print("\n No models tested successfully")

