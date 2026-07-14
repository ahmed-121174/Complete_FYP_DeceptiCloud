#!/usr/bin/env python3
"""
Direct evaluation with TensorFlow 2.20.0 - should work now!
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.metrics import balanced_accuracy_score, matthews_corrcoef, confusion_matrix
import tensorflow as tf

print(f"TensorFlow version: {tf.__version__}")

# Add code directory to path

sys.path.insert(0, str(Path(__file__).parent / "V2-SQLI-XSS-NoSQLi/code"))
from feature_engineering import WebAttackFeatureExtractor
from sklearn.model_selection import train_test_split

print("V2 MODEL EVALUATION WITH TENSORFLOW 2.20.0")

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

print(f"\n Extracting 52 features...")
extractor = WebAttackFeatureExtractor()
X_features = extractor.extract_features_batch(combined_df[text_col])

# Split (random_state=42 to match training)

_, X_test, _, y_test = train_test_split(
    X_features, y, test_size=0.2, random_state=42, stratify=y
)

print(f" Test set: {len(y_test):,} samples")
print(f"   - Benign (0): {(y_test==0).sum():,}")
print(f"   - Attack (1): {(y_test==1).sum():,}\n")

# Try to load the V2 model

model_path = "V2-SQLI-XSS-NoSQLi/models/web_attack_detector_v2.keras"
print(f" Loading model: {model_path}")

try:
    model = tf.keras.models.load_model(model_path)
    print(f" Model loaded successfully!")
    print(f"   Parameters: {model.count_params():,}")
    
    # Predict

    print("\n Running predictions...")
    y_probs = model.predict(X_test, verbose=0).flatten()
    y_pred = (y_probs >= 0.5).astype(int)
    
    # Metrics

    acc = np.mean(y_pred == y_test) * 100
    bal_acc = balanced_accuracy_score(y_test, y_pred) * 100
    mcc = matthews_corrcoef(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred)
    
    print("RESULTS")
    
    print(f"\n Overall Metrics:")
    print(f"   Overall Accuracy:   {acc:.2f}%")
    print(f"   Balanced Accuracy:  {bal_acc:.2f}%")
    print(f"   MCC:                {mcc:.4f}")
    
    print(f"\n Confusion Matrix:")
    print("                Predicted")
    print("              Benign  Attack")
    print(f"   Benign     {cm[0,0]:6,}  {cm[0,1]:6,}")
    print(f"   Attack     {cm[1,0]:6,}  {cm[1,1]:6,}")
    
    # Per-class metrics

    benign_prec = cm[0,0] / (cm[0,0] + cm[1,0]) * 100 if (cm[0,0] + cm[1,0]) > 0 else 0
    benign_rec = cm[0,0] / (cm[0,0] + cm[0,1]) * 100 if (cm[0,0] + cm[0,1]) > 0 else 0
    attack_prec = cm[1,1] / (cm[1,1] + cm[0,1]) * 100 if (cm[1,1] + cm[0,1]) > 0 else 0
    attack_rec = cm[1,1] / (cm[1,1] + cm[1,0]) * 100 if (cm[1,1] + cm[1,0]) > 0 else 0
    
    print(f"\n Per-Class Metrics:")
    print(f"   Benign - Precision: {benign_prec:.2f}%, Recall: {benign_rec:.2f}%")
    print(f"   Attack - Precision: {attack_prec:.2f}%, Recall: {attack_rec:.2f}%")
    
    # Compare to targets

    print("COMPARISON TO TARGET (93.97% balanced accuracy)")
    
    target_bal = 93.97
    target_acc = 89.69
    diff_bal = abs(bal_acc - target_bal)
    diff_acc = abs(acc - target_acc)
    
    print(f"   Balanced Accuracy: {bal_acc:.2f}% vs {target_bal}% (diff: {diff_bal:.2f}%)")
    print(f"   Overall Accuracy:  {acc:.2f}% vs {target_acc}% (diff: {diff_acc:.2f}%)")
    
    if diff_bal < 1.0 and diff_acc < 1.0:
        print("\n  EXACT MATCH FOUND!")
    elif diff_bal < 5.0:
        print("\n CLOSE MATCH (within 5%)")
    else:
        print("\n Results differ - likely different dataset")
    
except Exception as e:
    print(f" Error loading model: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()

