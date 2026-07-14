"""
DDoS V1 - HONEST RETRAIN (without leaking Inbound feature)
This script removes the Inbound feature which was leaking the label.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from imblearn.over_sampling import SMOTE
from sklearn.metrics import (balanced_accuracy_score, accuracy_score, confusion_matrix,
    classification_report, roc_auc_score, f1_score)
from sklearn.model_selection import cross_val_score, StratifiedKFold
import joblib, json, warnings, time
from datetime import datetime
warnings.filterwarnings('ignore')

def main():
    start = time.time()
    sep = '=' * 80
    print(sep)
    print('DDoS V1 - RETRAIN WITHOUT LEAKING FEATURES')
    print(sep)

    # LOAD

    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / 'Datasets' / 'DDoS_sampled'
    if not data_dir.exists():
        data_dir = Path('/media/amei-302/New Volume/SEMESTER VIII/Ahmed Fype-II/Datasets/DDoS_sampled')

    dfs = []
    for f in sorted(data_dir.glob('*.csv')):
        df = pd.read_csv(f, low_memory=False)
        print(f'  {f.name}: {len(df):,} rows')
        dfs.append(df)
    combined = pd.concat(dfs, ignore_index=True)
    print(f'Combined: {len(combined):,} rows')

    label_col = ' Label'
    # CRITICAL: Drop ALL leaking/identifier columns INCLUDING Inbound

    leaking = [
        'Unnamed: 0', 'Flow ID', ' Source IP', ' Source Port',
        ' Destination IP', ' Destination Port', ' Timestamp',
        'SimillarHTTP', ' Inbound'  # <-- LEAKS LABEL!
    ]
    combined = combined.drop(columns=[c for c in leaking if c in combined.columns])
    print(f'Dropped leaking columns (including Inbound)')

    combined['label'] = combined[label_col].apply(
        lambda x: 0 if str(x).strip().upper() == 'BENIGN' else 1
    )
    combined = combined.drop(columns=[label_col])
    benign_n = int((combined['label'] == 0).sum())
    attack_n = int((combined['label'] == 1).sum())
    print(f'Benign: {benign_n:,}, Attack: {attack_n:,}')

    before = len(combined)
    combined = combined.drop_duplicates()
    print(f'Removed {before - len(combined):,} duplicates -> {len(combined):,} rows')

    feature_cols = [c for c in combined.columns if c != 'label']
    for col in feature_cols:
        combined[col] = pd.to_numeric(combined[col], errors='coerce')
    combined.replace([np.inf, -np.inf], np.nan, inplace=True)
    for col in feature_cols:
        if combined[col].isnull().any():
            combined[col] = combined[col].fillna(combined[col].median())

    constant = [c for c in feature_cols if combined[c].nunique() <= 1]
    combined = combined.drop(columns=constant)
    combined = combined.dropna()
    print(f'Removed {len(constant)} constant cols')

    feature_cols = [c for c in combined.columns if c != 'label']
    corr = combined[feature_cols].corr().abs()
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
    to_drop_corr = [col for col in upper.columns if any(upper[col] > 0.95)]
    combined = combined.drop(columns=to_drop_corr)
    print(f'Removed {len(to_drop_corr)} correlated features')
    feature_cols = [c for c in combined.columns if c != 'label']
    print(f'Remaining features: {len(feature_cols)}')

    # SPLIT

    X = combined[feature_cols]
    y = combined['label']
    X_tr, X_test, y_tr, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_tr, y_tr, test_size=0.1765, random_state=42, stratify=y_tr
    )
    print(f'Train: {len(y_train):,} | Val: {len(y_val):,} | Test: {len(y_test):,}')

    # Feature selection

    print('\nSelecting top 30 features...')
    rf_fs = RandomForestClassifier(
        n_estimators=50, max_depth=10, random_state=42,
        n_jobs=-1, class_weight='balanced'
    )
    rf_fs.fit(X_train, y_train)
    importances = pd.Series(
        rf_fs.feature_importances_, index=X_train.columns
    ).sort_values(ascending=False)
    selected = importances.head(30).index.tolist()

    print('\nTop 10 features (HONEST - no Inbound):')
    for i, feat in enumerate(selected[:10]):
        print(f'  {i+1:2d}. {feat.strip():40s} {importances[feat]:.4f}')

    X_train = X_train[selected]
    X_val = X_val[selected]
    X_test = X_test[selected]

    # SMOTE

    b_count = int((y_train == 0).sum())
    a_count = int((y_train == 1).sum())
    print(f'\nBefore SMOTE: Benign={b_count:,}, Attack={a_count:,}')
    smote = SMOTE(random_state=42, k_neighbors=5)
    X_train_sm, y_train_sm = smote.fit_resample(X_train, y_train)
    b2 = int((y_train_sm == 0).sum())
    a2 = int((y_train_sm == 1).sum())
    print(f'After SMOTE:  Benign={b2:,}, Attack={a2:,}')

    # Scale

    scaler = RobustScaler()
    X_train_s = pd.DataFrame(scaler.fit_transform(X_train_sm), columns=selected)
    X_val_s = pd.DataFrame(scaler.transform(X_val), columns=selected)
    X_test_s = pd.DataFrame(scaler.transform(X_test), columns=selected)

    # RANDOM FOREST

    print(f'\n{sep}')
    print('TRAINING RANDOM FOREST (HONEST - no Inbound)')
    print(sep)
    rf = RandomForestClassifier(
        n_estimators=200, max_depth=15, min_samples_split=10,
        min_samples_leaf=5, class_weight='balanced', random_state=42, n_jobs=-1
    )
    t0 = time.time()
    rf.fit(X_train_s, y_train_sm)
    print(f'Trained in {time.time() - t0:.1f}s')

    rf_train_pred = rf.predict(X_train_s)
    rf_test_pred = rf.predict(X_test_s)
    rf_test_prob = rf.predict_proba(X_test_s)[:, 1]
    train_ba = balanced_accuracy_score(y_train_sm, rf_train_pred) * 100
    test_ba = balanced_accuracy_score(y_test, rf_test_pred) * 100
    test_auc = roc_auc_score(y_test, rf_test_prob)
    cm = confusion_matrix(y_test, rf_test_pred)

    print(f'\nRF RESULTS:')
    print(f'  Train Balanced Accuracy: {train_ba:.2f}%')
    print(f'  Test Balanced Accuracy:  {test_ba:.2f}%')
    print(f'  Gap:                     {train_ba - test_ba:.2f}%')
    print(f'  AUC:                     {test_auc:.4f}')
    b_recall = cm[0, 0] / cm[0].sum() * 100
    a_recall = cm[1, 1] / cm[1].sum() * 100
    print(f'  Benign Recall:           {b_recall:.2f}% ({cm[0,0]}/{cm[0].sum()})')
    print(f'  Attack Recall:           {a_recall:.2f}% ({cm[1,1]}/{cm[1].sum()})')
    print(f'\n  Confusion Matrix:')
    print(f'                Benign   Attack')
    print(f'  Benign      {cm[0,0]:>7,}  {cm[0,1]:>7,}')
    print(f'  Attack      {cm[1,0]:>7,}  {cm[1,1]:>7,}')
    print(classification_report(y_test, rf_test_pred, target_names=['Benign', 'Attack']))

    # CV

    print('5-Fold Cross-Validation...')
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv = cross_val_score(
        rf, X_train_s, y_train_sm, cv=skf,
        scoring='balanced_accuracy', n_jobs=-1
    )
    cv_strs = [f'{s*100:.2f}%' for s in cv]
    print(f'  Fold scores: {cv_strs}')
    print(f'  Mean: {cv.mean()*100:.2f}% +/- {cv.std()*100:.2f}%')

    # GRADIENT BOOSTING

    print(f'\n{sep}')
    print('TRAINING GRADIENT BOOSTING (HONEST - no Inbound)')
    print(sep)
    gb = GradientBoostingClassifier(
        n_estimators=100, max_depth=5, learning_rate=0.1,
        subsample=0.8, min_samples_split=10, min_samples_leaf=5, random_state=42
    )
    t0 = time.time()
    gb.fit(X_train_s, y_train_sm)
    print(f'Trained in {time.time() - t0:.1f}s')

    gb_train_pred = gb.predict(X_train_s)
    gb_test_pred = gb.predict(X_test_s)
    gb_test_prob = gb.predict_proba(X_test_s)[:, 1]
    gb_train_ba = balanced_accuracy_score(y_train_sm, gb_train_pred) * 100
    gb_test_ba = balanced_accuracy_score(y_test, gb_test_pred) * 100
    gb_auc = roc_auc_score(y_test, gb_test_prob)
    gb_cm = confusion_matrix(y_test, gb_test_pred)

    gb_b_recall = gb_cm[0, 0] / gb_cm[0].sum() * 100
    gb_a_recall = gb_cm[1, 1] / gb_cm[1].sum() * 100

    print(f'\nGB RESULTS:')
    print(f'  Train Balanced Accuracy: {gb_train_ba:.2f}%')
    print(f'  Test Balanced Accuracy:  {gb_test_ba:.2f}%')
    print(f'  Gap:                     {gb_train_ba - gb_test_ba:.2f}%')
    print(f'  AUC:                     {gb_auc:.4f}')
    print(f'  Benign Recall:           {gb_b_recall:.2f}% ({gb_cm[0,0]}/{gb_cm[0].sum()})')
    print(f'  Attack Recall:           {gb_a_recall:.2f}% ({gb_cm[1,1]}/{gb_cm[1].sum()})')
    print(f'\n  Confusion Matrix:')
    print(f'                Benign   Attack')
    print(f'  Benign      {gb_cm[0,0]:>7,}  {gb_cm[0,1]:>7,}')
    print(f'  Attack      {gb_cm[1,0]:>7,}  {gb_cm[1,1]:>7,}')
    print(classification_report(y_test, gb_test_pred, target_names=['Benign', 'Attack']))

    # SAVE

    print(f'\n{sep}')
    print('SAVING HONEST MODELS')
    print(sep)
    models_dir = Path(__file__).parent / 'models'
    models_dir.mkdir(parents=True, exist_ok=True)

    if test_ba >= gb_test_ba:
        best_name, best_model = 'random_forest', rf
        best_ba_val, best_auc_val, best_cm = test_ba, test_auc, cm
    else:
        best_name, best_model = 'gradient_boosting', gb
        best_ba_val, best_auc_val, best_cm = gb_test_ba, gb_auc, gb_cm

    joblib.dump(rf, models_dir / 'random_forest.pkl')
    joblib.dump(gb, models_dir / 'gradient_boosting.pkl')
    joblib.dump(best_model, models_dir / 'best_model.pkl')
    joblib.dump(scaler, models_dir / 'scaler.pkl')
    joblib.dump(selected, models_dir / 'selected_features.pkl')

    metadata = {
        'best_model': best_name,
        'trained_at': datetime.now().isoformat(),
        'n_features': len(selected),
        'feature_names': selected,
        'leaking_features_removed': [' Inbound'],
        'results': {
            'random_forest': {
                'balanced_accuracy': float(test_ba),
                'auc': float(test_auc),
                'benign_recall': float(b_recall),
                'attack_recall': float(a_recall),
                'train_test_gap': float(train_ba - test_ba),
                'cv_mean': float(cv.mean() * 100),
                'cv_std': float(cv.std() * 100)
            },
            'gradient_boosting': {
                'balanced_accuracy': float(gb_test_ba),
                'auc': float(gb_auc),
                'benign_recall': float(gb_b_recall),
                'attack_recall': float(gb_a_recall),
                'train_test_gap': float(gb_train_ba - gb_test_ba)
            }
        }
    }
    with open(models_dir / 'metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

    total = time.time() - start
    print(f'\nAll models saved!')
    print(f'\n{sep}')
    print(f'FINAL HONEST RESULTS')
    print(sep)
    best_b = best_cm[0, 0] / best_cm[0].sum() * 100
    best_a = best_cm[1, 1] / best_cm[1].sum() * 100
    print(f'  Best Model:       {best_name}')
    print(f'  Balanced Accuracy: {best_ba_val:.2f}%')
    print(f'  AUC:              {best_auc_val:.4f}')
    print(f'  Benign Recall:    {best_b:.2f}%')
    print(f'  Attack Recall:    {best_a:.2f}%')
    print(f'  Total time:       {total / 60:.1f} min')

if __name__ == '__main__':
    main()
