"""
Run Web Attack Model V2 - Corrected Evaluation
This script produces the EXACT results matching the documentation:
- Balanced Accuracy: 93.97%
- Overall Accuracy: 89.69%
- MCC: 0.5704
"""

import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import (balanced_accuracy_score, matthews_corrcoef,
                             classification_report, confusion_matrix)
import tensorflow as tf
import sys

# Add ml_pipeline to path for imports

sys.path.insert(0, str(Path(__file__).parent / "ml_pipeline"))
from feature_engineering import WebAttackFeatureExtractor
from sklearn.model_selection import train_test_split

print("WEB ATTACK DETECTION MODEL V2 - EVALUATION")

# Load the trained model

print("\nLoading trained model...")
model_path = "ml_pipeline/models/web_attack_detector_v2.keras"
model = tf.keras.models.load_model(model_path)
print(f" Model loaded: {model.count_params():,} parameters\n")

# Load and prepare test data

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

combined_df = pd.concat(all_dataframes, ignore_index=True)
combined_df = combined_df.drop_duplicates()

# Find columns

label_col = [col for col in combined_df.columns if 'label' in col.lower()][0]
text_col = None
for col in ['Sentence', 'Query', 'sentence', 'query']:
    if col in combined_df.columns:
        text_col = col
        break

# Normalize labels - CRITICAL: Ensure benign=0, attack=1

unique_labels = combined_df[label_col].unique()
label_set = set([str(v).strip() for v in unique_labels if pd.notna(v)])

if label_set <= {'0', '1'}:
    y = combined_df[label_col].fillna('1').astype(str).str.strip().astype(int)
else:
    # Find which label is benign (usually the first one or has 'benign' in name)

    benign_label = unique_labels[0]
    y = (combined_df[label_col] != benign_label).astype(int)

# Extract features

print("Extracting features from samples...")
extractor = WebAttackFeatureExtractor()
X_features = extractor.extract_features_batch(combined_df[text_col])

# Split to get same test set (random_state=42 ensures reproducibility)

_, X_test, _, y_test = train_test_split(
    X_features, y, test_size=0.2, random_state=42, stratify=y
)

print(f" Test set: {len(y_test):,} samples")
print(f"   - Benign (label=0): {(y_test==0).sum():,}")
print(f"   - Attack (label=1): {(y_test==1).sum():,}\n")

# Evaluate with threshold=0.5

print("EVALUATION RESULTS")

y_probs = model.predict(X_test, verbose=0).flatten()
y_pred = (y_probs >= 0.5).astype(int)

# Calculate metrics

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

# Detailed metrics

benign_prec = cm[0,0] / (cm[0,0] + cm[1,0]) if (cm[0,0] + cm[1,0]) > 0 else 0
benign_rec = cm[0,0] / (cm[0,0] + cm[0,1]) if (cm[0,0] + cm[0,1]) > 0 else 0
benign_f1 = 2 * (benign_prec * benign_rec) / (benign_prec + benign_rec) if (benign_prec + benign_rec) > 0 else 0

attack_prec = cm[1,1] / (cm[1,1] + cm[0,1]) if (cm[1,1] + cm[0,1]) > 0 else 0
attack_rec = cm[1,1] / (cm[1,1] + cm[1,0]) if (cm[1,1] + cm[1,0]) > 0 else 0
attack_f1 = 2 * (attack_prec * attack_rec) / (attack_prec + attack_rec) if (attack_prec + attack_rec) > 0 else 0

print(f"\n Per-Class Metrics:")
print(f"   Benign Class:")
print(f"      Precision: {benign_prec*100:.2f}%")
print(f"      Recall:    {benign_rec*100:.2f}%")
print(f"      F1-Score:  {benign_f1:.2f}")

print(f"\n   Attack Class:")
print(f"      Precision: {attack_prec*100:.2f}%")
print(f"      Recall:    {attack_rec*100:.2f}%")
print(f"      F1-Score:  {attack_f1:.2f}")

# False alarm rate

false_alarms = cm[0,1]
total_samples = len(y_test)
false_alarm_rate = (false_alarms / total_samples) * 100

print(f"\n Key Achievements:")
print(f"    Balanced Accuracy: {bal_acc*100:.2f}% {'' if bal_acc*100 > 93 else ''}")
print(f"    Attack Detection:  {attack_rec*100:.2f}% ({cm[1,1]:,}/{(y_test==1).sum():,} caught)")
print(f"    Benign Detection:  {benign_rec*100:.2f}% ({cm[0,0]:,}/{(y_test==0).sum():,} caught)")
print(f"    False Alarm Rate:  {false_alarm_rate:.2f}% ({false_alarms:,}/{total_samples:,})")
print(f"    Attack Precision:  {attack_prec*100:.2f}%")

print(" EVALUATION COMPLETE")
