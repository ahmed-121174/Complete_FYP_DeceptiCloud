"""
Web Attack Model - Complete Fix and Re-training Script
Implements all proposed fixes for class imbalance
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import (balanced_accuracy_score, matthews_corrcoef,
                             classification_report, confusion_matrix)
from imblearn.over_sampling import SMOTE
import tensorflow as tf
from collections import Counter

sys.path.append(str(Path(__file__).parent))
from preprocessing import DataPreprocessor
from web_attack_model import WebAttackDetector

def clean_and_load_all_datasets():
    """Load and clean all CSV files from Web Attack dataset"""
    print("STEP 1: LOADING AND CLEANING ALL WEB ATTACK DATASETS")
    
    base_path = Path(__file__).parent.parent / "Datasets" / "SQLI-nosqli-XSS"
    
    # Find ALL CSV files recursively

    all_csv_files = list(base_path.rglob("*.csv"))
    print(f"\n Found {len(all_csv_files)} CSV files:")
    for f in all_csv_files:
        size_mb = f.stat().st_size / (1024*1024)
        print(f"   - {f.relative_to(base_path)}: {size_mb:.2f} MB")
    
    all_dataframes = []
    
    for csv_file in all_csv_files:
        print(f"\n Processing: {csv_file.name}")
        try:
            df = pd.read_csv(csv_file, low_memory=False)
            original_rows = len(df)
            
            # Clean duplicate rows

            df = df.drop_duplicates()
            duplicates_removed = original_rows - len(df)
            
            # Remove rows with all nulls

            df = df.dropna(how='all')
            
            # Remove completely empty columns

            df = df.dropna(axis=1, how='all')
            
            print(f"   Original: {original_rows:,} rows")
            print(f"   After cleaning: {len(df):,} rows ({duplicates_removed:,} duplicates removed)")
            print(f"   Columns: {len(df.columns)}")
            
            all_dataframes.append(df)
            
        except Exception as e:
            print(f"    Error loading {csv_file.name}: {e}")
            continue
    
    print(f"\n Successfully loaded {len(all_dataframes)} datasets")
    print("COMBINING ALL DATASETS")
    
    # Combine all datasets

    combined_df = pd.concat(all_dataframes, ignore_index=True)
    
    print(f"\n Combined dataset: {len(combined_df):,} rows × {len(combined_df.columns)} columns")
    
    # Final duplicate removal across all combined data

    before_dedup = len(combined_df)
    combined_df = combined_df.drop_duplicates()
    after_dedup = len(combined_df)
    print(f" Cross-dataset deduplication: Removed {before_dedup - after_dedup:,} duplicates")
    
    return combined_df

def prepare_balanced_data(X, y):
    """Apply SMOTE to balance classes"""
    print("STEP 3: APPLYING SMOTE FOR CLASS BALANCING")
    
    print(f"\n Before SMOTE:")
    unique, counts = np.unique(y, return_counts=True)
    for u, c in zip(unique, counts):
        print(f"   Class {u}: {c:,} samples ({c/len(y)*100:.2f}%)")
    
    # Apply SMOTE

    smote = SMOTE(random_state=42, k_neighbors=5)
    X_balanced, y_balanced = smote.fit_resample(X, y)
    
    print(f"\n After SMOTE:")
    unique, counts = np.unique(y_balanced, return_counts=True)
    for u, c in zip(unique, counts):
        print(f"   Class {u}: {c:,} samples ({c/len(y_balanced)*100:.2f}%)")
    
    return X_balanced, y_balanced

def calculate_class_weights(y_train):
    """Calculate class weights for training"""
    class_weights = compute_class_weight(
        'balanced',
        classes=np.unique(y_train),
        y=y_train
    )
    class_weight_dict = {i: class_weights[i] for i in range(len(class_weights))}
    
    print(f"\n Class Weights: {class_weight_dict}")
    return class_weight_dict

def cross_validate_model(X, y, n_folds=5):
    """Perform stratified 5-fold cross-validation"""
    print(f"STEP 5: {n_folds}-FOLD STRATIFIED CROSS-VALIDATION")
    
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)
    
    cv_accuracies = []
    cv_balanced_accs = []
    cv_mccs = []
    
    for fold, (train_idx, val_idx) in enumerate(skf.split(X, y), 1):
        print(f"\n Fold {fold}/{n_folds}")
        
        X_train_cv = X[train_idx]
        y_train_cv = y[train_idx]
        X_val_cv = X[val_idx]
        y_val_cv = y[val_idx]
        
        # Calculate class weights

        class_weights = calculate_class_weights(y_train_cv)
        
        # Build and train model

        detector = WebAttackDetector(input_dim=X_train_cv.shape[1])
        detector.build_model()
        
        # Train with class weights

        detector.model.fit(
            X_train_cv, y_train_cv,
            validation_data=(X_val_cv, y_val_cv),
            epochs=30,
            batch_size=64,
            class_weight=class_weights,
            verbose=0
        )
        
        # Evaluate

        y_pred = (detector.model.predict(X_val_cv, verbose=0) > 0.5).astype(int).flatten()
        
        acc = np.mean(y_pred == y_val_cv)
        bal_acc = balanced_accuracy_score(y_val_cv, y_pred)
        mcc = matthews_corrcoef(y_val_cv, y_pred)
        
        cv_accuracies.append(acc)
        cv_balanced_accs.append(bal_acc)
        cv_mccs.append(mcc)
        
        print(f"   Accuracy: {acc*100:.2f}%")
        print(f"   Balanced Accuracy: {bal_acc*100:.2f}%")
        print(f"   MCC: {mcc:.4f}")
    
    print(f"\n" + "="*80)
    print("CROSS-VALIDATION SUMMARY")
    print(f"Accuracy:          {np.mean(cv_accuracies)*100:.2f}% ± {np.std(cv_accuracies)*100:.2f}%")
    print(f"Balanced Accuracy: {np.mean(cv_balanced_accs)*100:.2f}% ± {np.std(cv_balanced_accs)*100:.2f}%")
    print(f"MCC:               {np.mean(cv_mccs):.4f} ± {np.std(cv_mccs):.4f}")
    
    return np.mean(cv_balanced_accs)

def main():
    print("WEB ATTACK MODEL - COMPLETE FIX AND RE-TRAINING")
    print("\nImplementing ALL proposed fixes:")
    print("  1.  Thorough data cleaning")
    print("  2.  Class weights in training")
    print("  3.  SMOTE for benign samples")
    print("  4.  5-fold cross-validation")
    print("  5.  Balanced accuracy monitoring")
    print("  6.  Per-class metrics reporting\n")
    
    tf.random.set_seed(42)
    np.random.seed(42)
    
    # Step 1: Load and clean all data

    combined_df = clean_and_load_all_datasets()
    
    # Step 2: Preprocess with stratified split

    print("STEP 2: PREPROCESSING WITH STRATIFIED SPLIT")
    
    preprocessor = DataPreprocessor()
    data = preprocessor.preprocess_dataset(
        df=combined_df,
        label_col=None,
        test_size=0.2,
        val_size=0.1,
        select_features=100
    )
    
    X_train = data['X_train']
    y_train = data['y_train']
    X_val = data['X_val']
    y_val = data['y_val']
    X_test = data['X_test']
    y_test = data['y_test']
    
    print(f"\n Data Splits (Stratified):")
    print(f"   Training:   {len(y_train):,} samples")
    print(f"   Validation: {len(y_val):,} samples")
    print(f"   Test:       {len(y_test):,} samples")
    
    # Step 3: Apply SMOTE to training data

    X_train_balanced, y_train_balanced = prepare_balanced_data(X_train, y_train)
    
    # Step 4: Calculate class weights

    class_weights = calculate_class_weights(y_train_balanced)
    
    # Step 5: Cross-validation

    cv_balanced_acc = cross_validate_model(X_train_balanced, y_train_balanced, n_folds=5)
    
    # Step 6: Final model training with ALL fixes

    print("STEP 6: FINAL MODEL TRAINING WITH CLASS WEIGHTS")
    
    detector = WebAttackDetector(input_dim=X_train_balanced.shape[1])
    detector.build_model()
    
    print(f"\nTraining with:")
    print(f"  - SMOTE-balanced data: {len(y_train_balanced):,} samples")
    print(f"  - Class weights: {class_weights}")
    print(f"  - Epochs: 100, Batch size: 64")
    
    history = detector.train(
        X_train=X_train_balanced,
        y_train=y_train_balanced,
        X_val=X_val,
        y_val=y_val,
        epochs=100,
        batch_size=64,
        class_weight=class_weights
    )
    
    # Step 7: Comprehensive Evaluation

    print("STEP 7: COMPREHENSIVE MODEL EVALUATION")
    
    y_pred = (detector.model.predict(X_test, verbose=0) > 0.5).astype(int).flatten()
    
    # Calculate all metrics

    acc = np.mean(y_pred == y_test)
    bal_acc = balanced_accuracy_score(y_test, y_pred)
    mcc = matthews_corrcoef(y_test, y_pred)
    
    print(f"\n Test Set Results:")
    print(f"   Accuracy:          {acc*100:.2f}%")
    print(f"   Balanced Accuracy: {bal_acc*100:.2f}%")
    print(f"   MCC:               {mcc:.4f}")
    
    print(f"\n Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print("                Predicted")
    print("              Benign  Attack")
    print(f"   Benign     {cm[0,0]:6d}  {cm[0,1]:6d}")
    print(f"   Attack     {cm[1,0]:6d}  {cm[1,1]:6d}")
    
    print(f"\n Per-Class Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Benign', 'Attack']))
    
    # Success criteria check

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
        print("\n ALL CRITERIA MET - MODEL READY FOR DEPLOYMENT!")
    else:
        print("\n  SOME CRITERIA NOT MET - REVIEW REQUIRED")
    
    # Save model

    detector.save_model('models/web_attack_detector_fixed.keras')
    preprocessor.save_preprocessor('models/web_attack_preprocessor_fixed.pkl')
    
    print(" TRAINING COMPLETE")
    print(f"\nModel saved to: models/web_attack_detector_fixed.keras")
    print(f"Preprocessor saved to: models/web_attack_preprocessor_fixed.pkl")
    
    # Document dataset usage

    print("DATASET USAGE SUMMARY")
    print("\nCSV Files Used:")
    base_path = Path(__file__).parent.parent / "Datasets" / "SQLI-nosqli-XSS"
    for csv_file in base_path.rglob("*.csv"):
        print(f"  - {csv_file.relative_to(base_path)}")
    
    print(f"\nTrain/Val/Test Split:")
    print(f"  - Training:   70% ({len(y_train):,} samples original, {len(y_train_balanced):,} after SMOTE)")
    print(f"  - Validation: 10% ({len(y_val):,} samples)")
    print(f"  - Test:       20% ({len(y_test):,} samples)")
    print(f"\nSplit Method: Stratified (preserves class distribution)")

if __name__ == "__main__":
    main()
