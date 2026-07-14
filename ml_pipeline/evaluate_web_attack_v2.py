"""
Evaluate Web Attack Model V2 with Default Threshold
Quick script to evaluate the trained model with threshold=0.5
"""

import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import (balanced_accuracy_score, matthews_corrcoef,
                             classification_report, confusion_matrix)
import tensorflow as tf
import sys

sys.path.append(str(Path(__file__).parent))
from feature_engineering import WebAttackFeatureExtractor
from sklearn.model_selection import train_test_split

# Load the trained model

print("Loading trained model...")
model = tf.keras.models.load_model('models/web_attack_detector_v2.keras')
print(f" Model loaded: {model.count_params():,} parameters\n")

# Load and prepare test data

print("Loading test data...")
base_path = Path(__file__).parent.parent / "Datasets" / "SQLI-nosqli-XSS"
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

label_col = text_col = None
for col in combined_df.columns:
    if 'label' in col.lower():
        label_col = col
for col in ['Sentence', 'Query', 'sentence', 'query']:
    if col in combined_df.columns:
        text_col = col
        break

# Normalize labels

unique_labels = combined_df[label_col].unique()
label_set = set([str(v).strip() for v in unique_labels if pd.notna(v)])
if label_set <= {'0', '1'}:
    y = combined_df[label_col].fillna('1').astype(str).str.strip().astype(int)
else:
    benign_label = unique_labels[0]
    y = (combined_df[label_col] != benign_label).astype(int)

# Extract features

print("Extracting features...")
extractor = WebAttackFeatureExtractor()
X_features = extractor.extract_features_batch(combined_df[text_col])

# Split to get same test set

_, X_test, _, y_test = train_test_split(
    X_features, y, test_size=0.2, random_state=42, stratify=y
)

print(f" Test set: {len(y_test):,} samples\n")

# Evaluate with default threshold (0.5)

print("EVALUATION WITH DEFAULT THRESHOLD (0.5)")

y_probs = model.predict(X_test, verbose=0).flatten()
y_pred = (y_probs >= 0.5).astype(int)

acc = np.mean(y_pred == y_test)
bal_acc = balanced_accuracy_score(y_test, y_pred)
mcc = matthews_corrcoef(y_test, y_pred)

print(f"\n Test Results:")
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

# Calculate metrics for criteria

benign_precision = cm[0,0] / (cm[0,0] + cm[1,0]) if (cm[0,0] + cm[1,0]) > 0 else 0
benign_recall = cm[0,0] / (cm[0,0] + cm[0,1]) if (cm[0,0] + cm[0,1]) > 0 else 0
attack_precision = cm[1,1] / (cm[1,1] + cm[0,1]) if (cm[1,1] + cm[0,1]) > 0 else 0
attack_recall = cm[1,1] / (cm[1,1] + cm[1,0]) if (cm[1,1] + cm[1,0]) > 0 else 0

print("SUCCESS CRITERIA CHECK")

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
    print("    ALL CRITERIA MET - MODEL READY FOR DEPLOYMENT!   ")
else:
    print("\n  SOME CRITERIA NOT MET")

# Save threshold

with open('models/web_attack_threshold_corrected.txt', 'w') as f:
    f.write("0.5")
print("\n Corrected threshold (0.5) saved to: models/web_attack_threshold_corrected.txt")
