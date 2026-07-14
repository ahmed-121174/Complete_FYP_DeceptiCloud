"""
DDoS V1 - Data Preprocessing Pipeline
Loads DDoS datasets, cleans data, selects features, balances classes via SMOTE.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler
from sklearn.ensemble import RandomForestClassifier
from imblearn.over_sampling import SMOTE
import joblib
import warnings
warnings.filterwarnings('ignore')

class DDoSPreprocessor:
    """End-to-end preprocessing for DDoS detection dataset."""

    def __init__(self, output_dir="DDoS/V1"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.scaler = RobustScaler()
        self.selected_features = None
        self.label_col = " Label"

        # Columns to drop (identifiers and leaking features)

        self.drop_cols = [
            'Unnamed: 0', 'Flow ID', ' Source IP', ' Source Port',
            ' Destination IP', ' Destination Port', ' Timestamp',
            'SimillarHTTP',
            ' Inbound',  # LEAKS LABEL - achieves 99.87% accuracy alone!
        ]

    def load_data(self, data_dir="Datasets/DDoS_sampled"):
        """Load and combine all CSV files."""
        # Resolve relative to project root (two levels up from DDoS/V1/)

        data_path = Path(data_dir)
        if not data_path.exists():
            project_root = Path(__file__).parent.parent.parent
            data_path = project_root / data_dir
        if not data_path.exists():
            # Try absolute path

            data_path = Path("/media/amei-302/New Volume/SEMESTER VIII/Ahmed Fype-II") / data_dir
        csv_files = sorted(data_path.glob("*.csv"))

        print(f"\n{'='*80}")
        print(f"LOADING DATASET FROM {data_path}")
        print(f"{'='*80}")

        dfs = []
        for f in csv_files:
            print(f"  Loading {f.name}...", end=" ")
            df = pd.read_csv(f, low_memory=False)
            print(f"{len(df):,} rows")
            dfs.append(df)

        combined = pd.concat(dfs, ignore_index=True)
        print(f"\n Combined: {len(combined):,} rows × {len(combined.columns)} columns")
        return combined

    def clean_data(self, df):
        """Remove duplicates, nulls, infs, constant columns, and identifier columns."""
        print(f"\n{'='*80}")
        print("DATA CLEANING")
        print(f"{'='*80}")
        initial = len(df)

        # 1. Drop identifier columns

        cols_to_drop = [c for c in self.drop_cols if c in df.columns]
        df = df.drop(columns=cols_to_drop)
        print(f"  1. Dropped {len(cols_to_drop)} identifier columns")

        # 2. Normalize labels to binary

        print(f"  2. Normalizing labels...")
        unique_labels = df[self.label_col].unique()
        print(f"     Found labels: {unique_labels}")
        label_map = {}
        for label in unique_labels:
            label_str = str(label).strip().upper()
            label_map[label] = 0 if label_str == "BENIGN" else 1
        df[self.label_col] = df[self.label_col].map(label_map)
        benign_count = (df[self.label_col] == 0).sum()
        attack_count = (df[self.label_col] == 1).sum()
        print(f"     Benign: {benign_count:,} ({benign_count/len(df)*100:.1f}%)")
        print(f"     Attack: {attack_count:,} ({attack_count/len(df)*100:.1f}%)")

        # 3. Remove duplicates

        before = len(df)
        df = df.drop_duplicates()
        print(f"  3. Removed {before - len(df):,} duplicates")

        # 4. Convert all feature columns to numeric

        feature_cols = [c for c in df.columns if c != self.label_col]
        for col in feature_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # 5. Replace inf with NaN, then fill NaN with median

        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        null_count = df.isnull().sum().sum()
        if null_count > 0:
            print(f"  4. Filling {null_count:,} null/inf values with median")
            for col in feature_cols:
                if df[col].isnull().any():
                    df[col] = df[col].fillna(df[col].median())

        # 6. Remove constant columns (zero variance)

        constant_cols = [col for col in feature_cols if df[col].nunique() <= 1]
        if constant_cols:
            print(f"  5. Removing {len(constant_cols)} constant columns: {constant_cols[:5]}...")
            df = df.drop(columns=constant_cols)

        # Final null check - drop any remaining rows with NaN

        df = df.dropna()

        print(f"\n   Cleaned: {len(df):,} rows × {len(df.columns)} columns "
              f"(kept {len(df)/initial*100:.1f}%)")
        return df

    def remove_correlated_features(self, df, threshold=0.95):
        """Remove highly correlated features to reduce redundancy."""
        print(f"\n{'='*80}")
        print(f"CORRELATION ANALYSIS (threshold={threshold})")
        print(f"{'='*80}")

        feature_cols = [c for c in df.columns if c != self.label_col]
        corr_matrix = df[feature_cols].corr().abs()

        # Upper triangle

        upper = corr_matrix.where(
            np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        )

        # Find columns with correlation > threshold

        to_drop = [col for col in upper.columns if any(upper[col] > threshold)]
        print(f"  Found {len(to_drop)} highly correlated features to remove")
        if to_drop:
            print(f"  Removing: {to_drop[:10]}{'...' if len(to_drop) > 10 else ''}")
            df = df.drop(columns=to_drop)

        remaining = len([c for c in df.columns if c != self.label_col])
        print(f"   Remaining features: {remaining}")
        return df

    def select_features(self, X_train, y_train, n_features=30):
        """Select top N features using Random Forest importance."""
        print(f"\n{'='*80}")
        print(f"FEATURE SELECTION (top {n_features} via Random Forest)")
        print(f"{'='*80}")

        # Quick RF for feature importance

        rf = RandomForestClassifier(
            n_estimators=50, max_depth=10, random_state=42,
            n_jobs=-1, class_weight='balanced'
        )
        rf.fit(X_train, y_train)

        importances = pd.Series(rf.feature_importances_, index=X_train.columns)
        importances = importances.sort_values(ascending=False)

        # Select top N

        self.selected_features = importances.head(n_features).index.tolist()

        print(f"\n  Top {n_features} features:")
        for i, (feat, imp) in enumerate(importances.head(n_features).items()):
            print(f"    {i+1:2d}. {feat.strip():40s} importance: {imp:.4f}")

        return self.selected_features

    def preprocess(self, data_dir="Datasets/DDoS_sampled", n_features=30):
        """Full preprocessing pipeline. Returns train/val/test splits."""

        # Step 1: Load data

        df = self.load_data(data_dir)

        # Step 2: Clean data

        df = self.clean_data(df)

        # Step 3: Remove correlated features

        df = self.remove_correlated_features(df, threshold=0.95)

        # Step 4: Split features and labels

        feature_cols = [c for c in df.columns if c != self.label_col]
        X = df[feature_cols]
        y = df[self.label_col]

        # Step 5: Stratified train/val/test split (70/15/15)

        print(f"\n{'='*80}")
        print("SPLITTING DATA (70% train, 15% val, 15% test)")
        print(f"{'='*80}")

        X_train_full, X_test, y_train_full, y_test = train_test_split(
            X, y, test_size=0.15, random_state=42, stratify=y
        )
        X_train, X_val, y_train, y_val = train_test_split(
            X_train_full, y_train_full, test_size=0.1765,  # 0.15/0.85 ≈ 0.1765
            random_state=42, stratify=y_train_full
        )

        print(f"  Train: {len(y_train):,} (Benign: {(y_train==0).sum():,}, "
              f"Attack: {(y_train==1).sum():,})")
        print(f"  Val:   {len(y_val):,} (Benign: {(y_val==0).sum():,}, "
              f"Attack: {(y_val==1).sum():,})")
        print(f"  Test:  {len(y_test):,} (Benign: {(y_test==0).sum():,}, "
              f"Attack: {(y_test==1).sum():,})")

        # Step 6: Feature selection (on train only)

        selected = self.select_features(X_train, y_train, n_features)
        X_train = X_train[selected]
        X_val = X_val[selected]
        X_test = X_test[selected]

        # Step 7: SMOTE on training data only

        print(f"\n{'='*80}")
        print("APPLYING SMOTE TO BALANCE TRAINING DATA")
        print(f"{'='*80}")
        print(f"  Before SMOTE: Benign={int((y_train==0).sum()):,}, "
              f"Attack={int((y_train==1).sum()):,}")

        smote = SMOTE(random_state=42, k_neighbors=5)
        X_train_sm, y_train_sm = smote.fit_resample(X_train, y_train)

        print(f"  After SMOTE:  Benign={int((y_train_sm==0).sum()):,}, "
              f"Attack={int((y_train_sm==1).sum()):,}")
        print(f"   Classes balanced: {(y_train_sm==0).sum()/len(y_train_sm)*100:.1f}% / "
              f"{(y_train_sm==1).sum()/len(y_train_sm)*100:.1f}%")

        # Step 8: Scale features (fit on SMOTE'd training data)

        print(f"\n{'='*80}")
        print("SCALING FEATURES (RobustScaler)")
        print(f"{'='*80}")

        X_train_scaled = pd.DataFrame(
            self.scaler.fit_transform(X_train_sm),
            columns=selected
        )
        X_val_scaled = pd.DataFrame(
            self.scaler.transform(X_val),
            columns=selected
        )
        X_test_scaled = pd.DataFrame(
            self.scaler.transform(X_test),
            columns=selected
        )
        print(f"   Scaling complete")

        # Step 9: Save artifacts

        print(f"\n{'='*80}")
        print("SAVING ARTIFACTS")
        print(f"{'='*80}")

        models_dir = self.output_dir / "models"
        models_dir.mkdir(exist_ok=True)

        joblib.dump(self.scaler, models_dir / "scaler.pkl")
        joblib.dump(self.selected_features, models_dir / "selected_features.pkl")
        print(f"   Saved scaler and feature list")

        data = {
            'X_train': X_train_scaled, 'y_train': y_train_sm,
            'X_val': X_val_scaled, 'y_val': y_val,
            'X_test': X_test_scaled, 'y_test': y_test,
            'feature_names': selected
        }

        print(f"\n{'='*80}")
        print(" PREPROCESSING COMPLETE")
        print(f"{'='*80}")
        print(f"  Training:   {len(y_train_sm):,} samples ({len(selected)} features)")
        print(f"  Validation: {len(y_val):,} samples")
        print(f"  Testing:    {len(y_test):,} samples")

        return data

if __name__ == "__main__":
    preprocessor = DDoSPreprocessor()
    data = preprocessor.preprocess()
