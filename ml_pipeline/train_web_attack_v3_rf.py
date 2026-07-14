"""
Web Attack Model V3 - TF-IDF + Random Forest
Combines TF-IDF text features with engineered features for optimal performance
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (balanced_accuracy_score, matthews_corrcoef,
                             classification_report, confusion_matrix)
from scipy.sparse import hstack
import joblib

sys.path.append(str(Path(__file__).parent))
from feature_engineering import WebAttackFeatureExtractor

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

def prepare_data(df):
    """Prepare data with labels and text"""
    print("STEP 2: DATA PREPARATION")
    
    # Detect label column

    label_col = None
    for col in df.columns:
        if 'label' in col.lower():
            label_col = col
            break
    
    # Get text column

    text_col = None
    for col in ['Sentence', 'Query', 'sentence', 'query']:
        if col in df.columns:
            text_col = col
            break
    
    print(f"\n Text column: '{text_col}'")
    print(f"  Label column: '{label_col}'")
    
    # Normalize labels

    unique_labels = df[label_col].unique()
    label_set = set([str(v).strip() for v in unique_labels if pd.notna(v)])
    
    if label_set <= {'0', '1'}:
        y = df[label_col].fillna('1').astype(str).str.strip().astype(int)
    else:
        benign_label = unique_labels[0]
        y = (df[label_col] != benign_label).astype(int)
    
    benign_count = (y == 0).sum()
    attack_count = (y == 1).sum()
    print(f"\n   Benign (0): {benign_count:,} ({benign_count/len(y)*100:.1f}%)")
    print(f"   Attack (1): {attack_count:,} ({attack_count/len(y)*100:.1f}%)")
    
    # Get text data

    text_data = df[text_col].fillna('').astype(str)
    
    return text_data, y

def main():
    print("WEB ATTACK MODEL V3 - TF-IDF + RANDOM FOREST")
    
    np.random.seed(42)
    
    # Load data

    df = load_and_clean_datasets()
    text_data, y = prepare_data(df)
    
    # Split data (stratified)

    print("STEP 3: SPLITTING DATA (STRATIFIED)")
    
    X_text_train, X_text_test, y_train, y_test = train_test_split(
        text_data, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\n Data split:")
    print(f"   Train: {len(y_train):,} samples")
    print(f"   Test:  {len(y_test):,} samples")
    
    # Extract TF-IDF features

    print("STEP 4: TF-IDF VECTORIZATION")
    
    print("\n Creating TF-IDF vectorizer...")
    print("   Parameters:")
    print("     - max_features: 3000")
    print("     - ngram_range: (1, 3) (unigrams, bigrams, trigrams)")
    print("     - min_df: 2 (ignore terms appearing in <2 docs)")
    print("     - max_df: 0.8 (ignore terms appearing in >80% docs)")
    
    tfidf = TfidfVectorizer(
        max_features=3000,
        ngram_range=(1, 3),
        min_df=2,
        max_df=0.8,
        analyzer='char_wb',  # Character n-grams within word boundaries
        lowercase=True
    )
    
    X_tfidf_train = tfidf.fit_transform(X_text_train)
    X_tfidf_test = tfidf.transform(X_text_test)
    
    print(f"\n TF-IDF features extracted:")
    print(f"   Vocabulary size: {len(tfidf.vocabulary_):,}")
    print(f"   Feature matrix shape (train): {X_tfidf_train.shape}")
    print(f"   Feature matrix shape (test): {X_tfidf_test.shape}")
    
    # Extract engineered features

    print("STEP 5: FEATURE ENGINEERING")
    
    extractor = WebAttackFeatureExtractor()
    
    print("\n Extracting engineered features (train)...")
    X_eng_train = extractor.extract_features_batch(X_text_train.reset_index(drop=True))
    
    print("\n Extracting engineered features (test)...")
    X_eng_test = extractor.extract_features_batch(X_text_test.reset_index(drop=True))
    
    # Combine TF-IDF and engineered features

    print("STEP 6: COMBINING FEATURES")
    
    print("\n Combining TF-IDF and engineered features...")
    X_train_combined = hstack([X_tfidf_train, X_eng_train.values])
    X_test_combined = hstack([X_tfidf_test, X_eng_test.values])
    
    print(f"\n Combined features:")
    print(f"   TF-IDF features: {X_tfidf_train.shape[1]:,}")
    print(f"   Engineered features: {X_eng_train.shape[1]}")
    print(f"   Total features: {X_train_combined.shape[1]:,}")
    print(f"   Train samples: {X_train_combined.shape[0]:,}")
    print(f"   Test samples: {X_test_combined.shape[0]:,}")
    
    # Train Random Forest

    print("STEP 7: TRAINING RANDOM FOREST")
    
    print("\n Random Forest parameters:")
    print("   - n_estimators: 500")
    print("   - max_depth: 30")
    print("   - min_samples_split: 5")
    print("   - min_samples_leaf: 2")
    print("   - class_weight: 'balanced'")
    print("   - n_jobs: -1 (all CPUs)")
    
    rf_model = RandomForestClassifier(
        n_estimators=500,
        max_depth=30,
        min_samples_split=5,
        min_samples_leaf=2,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1,
        verbose=1
    )
    
    print("\n Training Random Forest...")
    rf_model.fit(X_train_combined, y_train)
    
    print("\n Training complete!")
    
    # Evaluate on test set

    print("STEP 8: EVALUATION ON TEST SET")
    
    y_pred = rf_model.predict(X_test_combined)
    y_proba = rf_model.predict_proba(X_test_combined)[:, 1]
    
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
    
    # Feature importance

    print("FEATURE IMPORTANCE (Top 20)")
    
    # Get feature names

    tfidf_features = [f"tfidf_{i}" for i in range(X_tfidf_train.shape[1])]
    eng_features = list(X_eng_train.columns)
    all_features = tfidf_features + eng_features
    
    feature_importance = pd.DataFrame({
        'feature': all_features,
        'importance': rf_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\n   Top 20 Most Important Features:")
    for idx, row in feature_importance.head(20).iterrows():
        print(f"   {row['feature']:40s}: {row['importance']:.6f}")
    
    # Success criteria

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
        print("\n  SOME CRITERIA NOT MET - REVIEW REQUIRED")
    
    # Save model and vectorizer

    print("SAVING MODEL AND COMPONENTS")
    
    Path('models').mkdir(exist_ok=True)
    
    joblib.dump(rf_model, 'models/web_attack_rf_model.pkl')
    joblib.dump(tfidf, 'models/web_attack_tfidf.pkl')
    joblib.dump(extractor, 'models/web_attack_feature_extractor.pkl')
    
    print("\n Saved:")
    print("   - models/web_attack_rf_model.pkl")
    print("   - models/web_attack_tfidf.pkl")
    print("   - models/web_attack_feature_extractor.pkl")
    
    print(" TRAINING COMPLETE")

if __name__ == "__main__":
    main()
