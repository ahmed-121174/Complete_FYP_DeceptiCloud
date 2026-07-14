"""
Web Attack Model - Ensemble Voting Classifier
Combines ANN + Random Forest + XGBoost for improved performance
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import VotingClassifier, RandomForestClassifier, GradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (balanced_accuracy_score, matthews_corrcoef,
                             classification_report, confusion_matrix)
from scipy.sparse import hstack
import joblib
from xgboost import XGBClassifier

sys.path.append(str(Path(__file__).parent))
from feature_engineering import WebAttackFeatureExtractor

def load_and_prepare_data():
    """Load data and prepare features"""
    print("STEP 1: DATA LOADING & PREPARATION")
    
    base_path = Path(__file__).parent.parent / "Datasets" / "SQLI-nosqli-XSS"
    all_csv_files = list(base_path.rglob("*.csv"))
    
    all_df = []
    for csv_file in all_csv_files:
        try:
            df = pd.read_csv(csv_file, low_memory=False)
            df = df.drop_duplicates().dropna(how='all').dropna(axis=1, how='all')
            all_df.append(df)
        except:
            continue
    
    combined_df = pd.concat(all_df, ignore_index=True).drop_duplicates()
    print(f" Loaded {len(combined_df):,} samples from {len(all_csv_files)} files")
    
    # Get text and labels

    label_col = [col for col in combined_df.columns if 'label' in col.lower()][0]
    text_col = [col for col in ['Sentence', 'Query'] if col in combined_df.columns][0]
    
    unique_labels = combined_df[label_col].unique()
    label_set = set([str(v).strip() for v in unique_labels if pd.notna(v)])
    
    if label_set <= {'0', '1'}:
        y = combined_df[label_col].fillna('1').astype(str).str.strip().astype(int)
    else:
        y = (combined_df[label_col] != unique_labels[0]).astype(int)
    
    text_data = combined_df[text_col].fillna('').astype(str)
    
    return text_data, y

def extract_all_features(text_train, text_test):
    """Extract TF-IDF + engineered features"""
    print("STEP 2: FEATURE EXTRACTION (TF-IDF + ENGINEERED)")
    
    # TF-IDF

    print("\n Extracting TF-IDF features...")
    tfidf = TfidfVectorizer(max_features=3000, ngram_range=(1, 3), min_df=2, max_df=0.8, analyzer='char_wb')
    X_tfidf_train = tfidf.fit_transform(text_train)
    X_tfidf_test = tfidf.transform(text_test)
    print(f"    TF-IDF: {X_tfidf_train.shape[1]:,} features")
    
    # Engineered features

    print("\n Extracting engineered features...")
    extractor = WebAttackFeatureExtractor()
    
    X_eng_train = extractor.extract_features_batch(text_train.reset_index(drop=True))
    X_eng_test = extractor.extract_features_batch(text_test.reset_index(drop=True))
    print(f"    Engineered: {X_eng_train.shape[1]} features")
    
    # Combine

    X_train = hstack([X_tfidf_train, X_eng_train.values]).toarray()  # Convert to dense for XGBoost
    X_test = hstack([X_tfidf_test, X_eng_test.values]).toarray()
    
    print(f"\n Total features: {X_train.shape[1]:,}")
    
    return X_train, X_test, tfidf, extractor

def main():
    print("WEB ATTACK MODEL - ENSEMBLE VOTING CLASSIFIER")
    
    np.random.seed(42)
    
    # Load data

    text_data, y = load_and_prepare_data()
    
    # Split

    text_train, text_test, y_train, y_test = train_test_split(
        text_data, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\n Train: {len(y_train):,} | Test: {len(y_test):,}")
    
    # Extract features

    X_train, X_test, tfidf, extractor = extract_all_features(text_train, text_test)
    
    # Create individual classifiers

    print("STEP 3: CREATING ENSEMBLE CLASSIFIERS")
    
    print("\n 1. Random Forest (500 trees)")
    rf = RandomForestClassifier(
        n_estimators=500,
        max_depth=30,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    
    print(" 2. XGBoost (200 estimators)")
    xgb = XGBClassifier(
        n_estimators=200,
        max_depth=15,
        learning_rate=0.1,
        scale_pos_weight=(y_train == 0).sum() / (y_train == 1).sum(),
        random_state=42,
        n_jobs=-1,
        eval_metric='logloss'
    )
    
    print(" 3. Gradient Boosting (150 estimators)")
    gb = GradientBoostingClassifier(
        n_estimators=150,
        max_depth=10,
        learning_rate=0.1,
        random_state=42
    )
    
    # Create voting classifier with HARD voting (majority vote)

    print("\n  Creating Voting Classifier (HARD voting - majority rule)")
    print("   Rule: Prediction = 'benign' only if 2/3 models agree")
    
    ensemble = VotingClassifier(
        estimators=[
            ('rf', rf),
            ('xgb', xgb),
            ('gb', gb)
        ],
        voting='hard',  # Majority vote
        n_jobs=-1
    )
    
    # Train ensemble

    print("STEP 4: TRAINING ENSEMBLE")
    
    print("\n Training all 3 models...")
    ensemble.fit(X_train, y_train)
    print(" Ensemble training complete!")
    
    # Evaluate

    print("STEP 5: EVALUATION")
    
    y_pred = ensemble.predict(X_test)
    
    acc = np.mean(y_pred == y_test)
    bal_acc = balanced_accuracy_score(y_test, y_pred)
    mcc = matthews_corrcoef(y_test, y_pred)
    
    print(f"\n Ensemble Test Results:")
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
    
    # Individual model performance

    print("INDIVIDUAL MODEL PERFORMANCE")
    
    for name, clf in ensemble.named_estimators_.items():
        y_pred_ind = clf.predict(X_test)
        acc_ind = balanced_accuracy_score(y_test, y_pred_ind)
        cm_ind = confusion_matrix(y_test, y_pred_ind)
        bp = cm_ind[0,0] / (cm_ind[0,0] + cm_ind[1,0]) if (cm_ind[0,0] + cm_ind[1,0]) > 0 else 0
        print(f"\n{name.upper()}:")
        print(f"   Balanced Accuracy: {acc_ind*100:.2f}%")
        print(f"   Benign Precision: {bp*100:.2f}%")
    
    # Success criteria

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
        print("    ALL CRITERIA MET!   ")
    
    # Save

    Path('models').mkdir(exist_ok=True)
    joblib.dump(ensemble, 'models/web_attack_ensemble.pkl')
    print("\n Ensemble model saved: models/web_attack_ensemble.pkl")

if __name__ == "__main__":
    main()
