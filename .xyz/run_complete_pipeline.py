#!/usr/bin/env python3
"""
Complete Pipeline: Preprocess Original Dataset and Evaluate V2 Model
Uses the original dataset to reproduce exact metrics (93.97% balanced accuracy)
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add code directory to path

sys.path.insert(0, str(Path(__file__).parent / "V2-SQLI-XSS-NoSQLi/code"))

from preprocessing import DataPreprocessor, load_and_combine_datasets
from feature_engineering import WebAttackFeatureExtractor
from sklearn.metrics import balanced_accuracy_score, matthews_corrcoef, confusion_matrix
import tensorflow as tf

print("REPRODUCING EXACT WEB ATTACK V2 RESULTS")
print("Using original dataset to get 93.97% balanced accuracy\n")

# Step 1: Load original dataset files

print("STEP 1: LOADING ORIGINAL DATASET")

original_dataset_path = Path("Orignal_dataset")
csv_files = list(original_dataset_path.rglob("*.csv"))

print(f"\nFound {len(csv_files)} CSV files:")
for csv_file in csv_files:
    print(f"  - {csv_file.relative_to(original_dataset_path)}")

# Load and combine all datasets (with encoding error handling)

dataframes = []
for csv_file in csv_files:
    print(f"\nLoading: {csv_file.relative_to(original_dataset_path)}")
    
    # Try different encodings

    for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
        try:
            df = pd.read_csv(csv_file, encoding=encoding, low_memory=False)
            print(f"  Shape: {df.shape[0]:,} rows × {df.shape[1]} columns (encoding: {encoding})")
            dataframes.append(df)
            break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"   Error with {encoding}: {str(e)[:50]}")
            continue
    else:
        print(f"   Failed to load {csv_file.name} - skipping")

print(f"\nCombining {len(dataframes)} datasets...")
combined_df = pd.concat(dataframes, ignore_index=True)

print(f"\n Combined dataset: {len(combined_df):,} rows × {len(combined_df.columns)} columns")

# Step 2: Run preprocessing

print("STEP 2: PREPROCESSING DATA")

preprocessor = DataPreprocessor()
preprocessed_data = preprocessor.preprocess_dataset(
    combined_df,
    label_col=None,  # Auto-detect
    test_size=0.2,
    val_size=0.1,
    use_smote=True
)

# Extract data splits

X_train = preprocessed_data['X_train']
y_train = preprocessed_data['y_train']
X_test = preprocessed_data['X_test']
y_test = preprocessed_data['y_test']

print(f"\n Preprocessing complete!")
print(f"   Test set: {len(y_test):,} samples")
print(f"     - Benign (0): {(y_test==0).sum():,}")
print(f"     - Attack (1): {(y_test==1).sum():,}")

# Step 3: Extract features for V2 model

print("STEP 3: EXTRACTING V2 FEATURES")

# Note: The V2 model uses feature engineering, not the preprocessing pipeline

# We need to reload the data and use WebAttackFeatureExtractor


# Find text column

text_col = None
for col in ['Sentence', 'Query', 'sentence', 'query']:
    if col in combined_df.columns:
        text_col = col
        break

if text_col is None:
    print("ERROR: Could not find text column!")
    sys.exit(1)

print(f"\nUsing column: '{text_col}'")

# Find label column

label_col = [col for col in combined_df.columns if 'label' in col.lower()][0]

# Normalize labels

unique_labels = combined_df[label_col].unique()
label_set = set([str(v).strip() for v in unique_labels if pd.notna(v)])

if label_set <= {'0', '1'}:
    y = combined_df[label_col].fillna('1').astype(str).str.strip().astype(int)
else:
    benign_label = unique_labels[0]
    y = (combined_df[label_col] != benign_label).astype(int)

print(f"\nExtracting features from {len(combined_df):,} samples...")
extractor = WebAttackFeatureExtractor()
X_features = extractor.extract_features_batch(combined_df[text_col])

# Split to match original (random_state=42)

from sklearn.model_selection import train_test_split
_, X_test_features, _, y_test_v2 = train_test_split(
    X_features, y, test_size=0.2, random_state=42, stratify=y
)

print(f" Extracted {X_features.shape[1]} features")
print(f"   Test set: {len(y_test_v2):,} samples")
print(f"     - Benign (0): {(y_test_v2==0).sum():,}")
print(f"     - Attack (1): {(y_test_v2==1).sum():,}")

# Step 4: Load V2 model and evaluate

print("STEP 4: EVALUATING V2 MODEL")

model_path = "ml_pipeline/models/web_attack_detector_v2.keras"
print(f"\nLoading model: {model_path}")
model = tf.keras.models.load_model(model_path)
print(f" Model loaded: {model.count_params():,} parameters")

# Predict

print("\nRunning predictions...")
y_probs = model.predict(X_test_features, verbose=0).flatten()
y_pred = (y_probs >= 0.5).astype(int)

# Calculate metrics

acc = np.mean(y_pred == y_test_v2)
bal_acc = balanced_accuracy_score(y_test_v2, y_pred)
mcc = matthews_corrcoef(y_test_v2, y_pred)
cm = confusion_matrix(y_test_v2, y_pred)

# Display results

print("FINAL RESULTS")

print(f"\n Overall Metrics:")
print(f"   Overall Accuracy:   {acc*100:.2f}%")
print(f"   Balanced Accuracy:  {bal_acc*100:.2f}%")
print(f"   MCC:                {mcc:.4f}")

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

# Compare to targets

print("COMPARISON TO TARGET METRICS")

targets = {
    "Balanced Accuracy": (bal_acc*100, 93.97),
    "Overall Accuracy": (acc*100, 89.69),
    "MCC": (mcc, 0.5704),
    "Benign Precision": (benign_prec*100, 37.08),
    "Benign Recall": (benign_rec*100, 98.85),
    "Attack Precision": (attack_prec*100, 99.92),
    "Attack Recall": (attack_rec*100, 89.09),
}

all_match = True
for metric, (actual, target) in targets.items():
    diff = abs(actual - target)
    match = "" if diff < 1.0 else ""
    if diff >= 1.0:
        all_match = False
    print(f"{match} {metric:20s}: {actual:6.2f}% (target: {target:.2f}%, diff: {diff:+.2f})")

if all_match:
    print("  EXACT MATCH ACHIEVED! All metrics within 1% of target!")
else:
    print("  Results differ from target - dataset may still be different")
