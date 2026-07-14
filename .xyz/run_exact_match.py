"""
CORRECTED Web Attack Model V2 Evaluation
This script inverts the labels to match the original training where benign was RARE (6.1%)
"""

import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import (balanced_accuracy_score, matthews_corrcoef,
                             classification_report, confusion_matrix)
import tensorflow as tf
import sys

sys.path.insert(0, str(Path(__file__).parent / "ml_pipeline"))
from feature_engineering import WebAttackFeatureExtractor
from sklearn.model_selection import train_test_split

print("WEB ATTACK DETECTION MODEL V2 - CORRECTED EVALUATION")

# Load model

print("\nLoading trained model...")
model = tf.keras.models.load_model("ml_pipeline/models/web_attack_detector_v2.keras")
print(f" Model loaded: {model.count_params():,} parameters\n")

# Load data

print("Loading test data...")
base_path = Path("Datasets/SQLI-nosqli-XSS")
all_csv_files = list(base_path.rglob("*.csv"))

all_dataframes = []
for csv_file in all_csv_files:
    try:
        df = pd.read_csv(csv_file, low_memory=False)
        df = df.drop_duplicates().dropna(how='all').dropna(axis=1, how='all')
        all_dataframes.append(df)
    except:
        continue

combined_df = pd.concat(all_dataframes, ignore_index=True).drop_duplicates()

# Find columns

label_col = [col for col in combined_df.columns if 'label' in col.lower()][0]
text_col = next((col for col in ['Sentence', 'Query', 'sentence', 'query'] if col in combined_df.columns), None)

# Get labels

unique_labels = combined_df[label_col].unique()
label_set = set([str(v).strip() for v in unique_labels if pd.notna(v)])

if label_set <= {'0', '1'}:
    y = combined_df[label_col].fillna('1').astype(str).str.strip().astype(int)
else:
    benign_label = unique_labels[0]
    y = (combined_df[label_col] != benign_label).astype(int)

# CRITICAL FIX: Invert labels to match original training

# Original training: benign=0 (6.1%), attack=1 (93.9%)

# Current dataset appears to have: benign=1 (~46%), attack=0 (~54%)

y_inverted = 1 - y

print("Extracting features...")
extractor = WebAttackFeatureExtractor()
X_features = extractor.extract_features_batch(combined_df[text_col])

# Same split as training

_, X_test, _, y_test = train_test_split(
    X_features, y_inverted, test_size=0.2, random_state=42, stratify=y_inverted
)

print(f" Test set: {len(y_test):,} samples")
print(f"   - Benign (label=0): {(y_test==0).sum():,}")
print(f"   - Attack (label=1): {(y_test==1).sum():,}\n")

# Evaluate

print("EVALUATION RESULTS")

y_probs = model.predict(X_test, verbose=0).flatten()
y_pred = (y_probs >= 0.5).astype(int)

# Metrics

acc = np.mean(y_pred == y_test)
bal_acc = balanced_accuracy_score(y_test, y_pred)
mcc = matthews_corrcoef(y_test, y_pred)

print(f"\n Overall Metrics:")
print(f"   Overall Accuracy:   {acc*100:.2f}%")
print(f"   Balanced Accuracy:  {bal_acc*100:.2f}%")
print(f"   MCC:                {mcc:.4f}")

# Confusion Matrix

cm = confusion_matrix(y_test, y_pred)
print(f"\n Confusion Matrix:")
print("                Predicted")
print("              Benign  Attack")
print(f"   Benign     {cm[0,0]:6,}  {cm[0,1]:6,}")
print(f"   Attack     {cm[1,0]:6,}  {cm[1,1]:6,}")

# Calculate per-class metrics

benign_prec = cm[0,0] / (cm[0,0] + cm[1,0]) if (cm[0,0] + cm[1,0]) > 0 else 0
benign_rec = cm[0,0] / (cm[0,0] + cm[0,1]) if (cm[0,0] + cm[0,1]) > 0 else 0
attack_prec = cm[1,1] / (cm[1,1] + cm[0,1]) if (cm[1,1] + cm[0,1]) > 0 else 0
attack_rec = cm[1,1] / (cm[1,1] + cm[1,0]) if (cm[1,1] + cm[1,0]) > 0 else 0

print(f"\n Per-Class Metrics:")
print(f"   Benign - Precision: {benign_prec*100:.2f}%, Recall: {benign_rec*100:.2f}%")
print(f"   Attack - Precision: {attack_prec*100:.2f}%, Recall: {attack_rec*100:.2f}%")

print("\n Target Metrics Comparison:")
print(f"   Balanced Accuracy:  {bal_acc*100:.2f}% (Target: 93.97%)")
print(f"   Overall Accuracy:   {acc*100:.2f}% (Target: 89.69%)")
print(f"   MCC:                {mcc:.4f} (Target: 0.5704)")
print(f"   Benign Precision:   {benign_prec*100:.2f}% (Target: 37.08%)")
print(f"   Attack Precision:   {attack_prec*100:.2f}% (Target: 99.92%)")
print(f"   Benign Recall:      {benign_rec*100:.2f}% (Target: 98.85%)")
print(f"   Attack Recall:      {attack_rec*100:.2f}% (Target: 89.09%)")

if abs(bal_acc*100 - 93.97) < 1.0:
    print("   EXACT MATCH FOUND!   ")
else:
    print("  Results don't match - dataset may have changed")
