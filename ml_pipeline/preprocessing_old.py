"""
Data Preprocessing Module
Handles data cleaning, preprocessing, and feature engineering for both DDoS and Web Attack datasets
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.feature_selection import SelectKBest, f_classif
import joblib
import json
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class DataPreprocessor:
    """
    Unified data preprocessing class for cybersecurity datasets
    """
    
    def __init__(self, config=None):
        self.config = config or {}
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_names = []
        self.label_column = None
        
    def identify_label_column(self, df):
        """Automatically identify the label/target column"""
        possible_labels = ['label', 'Label', 'target', 'class', 'attack', 'malicious', 'is_attack']
        
        for col in possible_labels:
            if col in df.columns:
                return col
        
        # If not found, assume last column is label

        return df.columns[-1]
    
    def remove_duplicates(self, df):
        """Remove duplicate rows"""
        initial_count = len(df)
        df = df.drop_duplicates()
        removed = initial_count - len(df)
        
        if removed > 0:
            print(f"   Removed {removed:,} duplicate rows ({removed/initial_count*100:.2f}%)")
        else:
            print(f"   No duplicates found")
        
        return df
    
    def handle_null_values(self, df, label_col=None):
        """Handle missing values intelligently"""
        null_counts = df.isnull().sum()
        null_cols = null_counts[null_counts > 0]
        
        if len(null_cols) == 0:
            print(f"   No null values found")
            return df
        
        print(f"   Found null values in {len(null_cols)} columns:")
        
        for col in null_cols.index:
            null_count = null_counts[col]
            null_pct = (null_count / len(df)) * 100
            
            # NEVER drop the label column, even if it has many nulls

            if col == label_col:
                # For label column, drop rows with null labels instead

                if null_pct > 0:
                    print(f"    - Dropping {null_count} rows with null labels")
                    df = df.dropna(subset=[col])
                continue
            
            # If more than 50% null, drop the column

            if null_pct > 50:
                print(f"    - Dropping '{col}' ({null_pct:.1f}% null)")
                df = df.drop(columns=[col])
                continue
            
            # Handle based on data type

            if df[col].dtype in ['int64', 'float64']:
                # Fill with median for numeric

                median_val = df[col].median()
                df[col].fillna(median_val, inplace=True)
                print(f"    - Filled '{col}' with median ({median_val:.2f})")
            else:
                # Fill with mode for categorical

                mode_val = df[col].mode()[0] if len(df[col].mode()) > 0 else 'unknown'
                df[col].fillna(mode_val, inplace=True)
                print(f"    - Filled '{col}' with mode ('{mode_val}')")
        
        return df
    
    def remove_constant_columns(self, df, label_col=None):
        """Remove columns with constant values (no variance)"""
        constant_cols = [col for col in df.columns if df[col].nunique() <= 1]
        
        # NEVER remove the label column, even if it's constant

        if label_col and label_col in constant_cols:
            constant_cols.remove(label_col)
            print(f"   Label column '{label_col}' is constant, but keeping it")
        
        if constant_cols:
            print(f"   Removing {len(constant_cols)} constant columns")
            df = df.drop(columns=constant_cols)
        
        return df
    
    def handle_infinite_values(self, df):
        """Replace infinite values with NaN and then handle"""
        # Replace inf with NaN

        df = df.replace([np.inf, -np.inf], np.nan)
        
        # Handle the new NaN values

        for col in df.select_dtypes(include=[np.number]).columns:
            if df[col].isnull().any():
                df[col].fillna(df[col].median(), inplace=True)
        
        return df
    
    def encode_categorical_features(self, df, label_col):
        """Encode categorical features using Label Encoding"""
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        # Remove label column from categorical if present

        if label_col in categorical_cols:
            categorical_cols.remove(label_col)
        
        if categorical_cols:
            print(f"   Encoding {len(categorical_cols)} categorical columns")
        
            for col in categorical_cols:
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col].astype(str))
                self.label_encoders[col] = le
        
        return df
    
    def normalize_label(self, df, label_col):
        """Normalize label column to binary 0/1"""
        unique_values = df[label_col].unique()
        
        print(f"  Label column '{label_col}' has values: {unique_values}")
        
        # Map to binary

        if len(unique_values) == 2:
            # Already binary, ensure it's 0 and 1

            value_map = {unique_values[0]: 0, unique_values[1]: 1}
            df[label_col] = df[label_col].map(value_map)
            print(f"   Mapped labels: {value_map}")
        else:
            # Multi-class: assume first value is benign (0), rest are attacks (1)

            is_attack = ~(df[label_col] == unique_values[0])
            df[label_col] = is_attack.astype(int)
            print(f"   Binary mapping: '{unique_values[0]}' → 0 (benign), others → 1 (attack)")
        
        return df
    
    def scale_features(self, X_train, X_test=None):
        """Standardize features using StandardScaler"""
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        if X_test is not None:
            X_test_scaled = self.scaler.transform(X_test)
            return X_train_scaled, X_test_scaled
        
        return X_train_scaled
    
    def feature_selection(self, X, y, k=50):
        """Select top K features based on ANOVA F-value"""
        if X.shape[1] <= k:
            print(f"   Keeping all {X.shape[1]} features (less than {k})")
            return X
        
        selector = SelectKBest(f_classif, k=k)
        X_selected = selector.fit_transform(X, y)
        
        selected_indices = selector.get_support(indices=True)
        self.feature_names = [self.feature_names[i] for i in selected_indices]
        
        print(f"   Selected top {k} features from {X.shape[1]}")
        
        return X_selected
    
    def preprocess_dataset(self, df, label_col=None, test_size=0.2, val_size=0.1, 
                          select_features=None):
        """
        Complete preprocessing pipeline
        
        Args:
            df: Input dataframe
            label_col: Name of label column (auto-detected if None)
            test_size: Proportion for test set
            val_size: Proportion for validation set
            select_features: Number of top features to select (None = keep all)
        
        Returns:
            Dictionary with train/val/test splits
        """
        print("DATA PREPROCESSING PIPELINE")
        
        print(f"\nInitial dataset: {df.shape[0]:,} rows × {df.shape[1]} columns")
        
        # Step 1: Identify label column

        if label_col is None:
            label_col = self.identify_label_column(df)
        self.label_column = label_col
        print(f"\n1. Label column: '{label_col}'")
        
        # Step 2: Remove duplicates

        print(f"\n2. Removing duplicates...")
        df = self.remove_duplicates(df)
        
        # Step 3: Handle null values

        print(f"\n3. Handling null values...")
        df = self.handle_null_values(df, label_col)
        
        # Step 4: Remove constant columns

        print(f"\n4. Removing constant columns...")
        df = self.remove_constant_columns(df, label_col)
        
        # Step 5: Handle infinite values

        print(f"\n5. Handling infinite values...")
        df = self.handle_infinite_values(df)
        
        # Step 6: Normalize label

        print(f"\n6. Normalizing labels...")
        df = self.normalize_label(df, label_col)
        
        # Step 7: Encode categorical features

        print(f"\n7. Encoding categorical features...")
        df = self.encode_categorical_features(df, label_col)
        
        # Step 8: Separate features and target

        print(f"\n8. Separating features and target...")
        X = df.drop(columns=[label_col])
        y = df[label_col]
        self.feature_names = X.columns.tolist()
        
        print(f"  Features: {X.shape[1]}, Target: {y.name}")
        print(f"  Class distribution: {dict(y.value_counts())}")
        
        # Step 9: Train-test-val split

        print(f"\n9. Splitting data (train: {1-test_size-val_size:.0%}, val: {val_size:.0%}, test: {test_size:.0%})...")
        
        # First split: train+val vs test

        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Second split: train vs val

        val_ratio = val_size / (1 - test_size)
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=val_ratio, random_state=42, stratify=y_temp
        )
        
        print(f"  Train: {X_train.shape[0]:,} samples")
        print(f"  Val:   {X_val.shape[0]:,} samples")
        print(f"  Test:  {X_test.shape[0]:,} samples")
        
        # Step 10: Feature selection (optional)

        if select_features and select_features < X_train.shape[1]:
            print(f"\n10. Feature selection (top {select_features})...")
            X_train = self.feature_selection(X_train, y_train, k=select_features)
            # Apply same feature selection to val and test

            X_val = X_val[self.feature_names]
            X_test = X_test[self.feature_names]
        
        # Step 11: Scale features

        print(f"\n11. Scaling features...")
        X_train_scaled, X_val_scaled = self.scale_features(X_train, X_val)
        X_test_scaled = self.scaler.transform(X_test)
        print(f"   Applied StandardScaler")
        
        print(f"\n{'='*80}")
        print(f" PREPROCESSING COMPLETE")
        print(f"{'='*80}")
        print(f"Final feature count: {X_train_scaled.shape[1]}")
        print(f"Final dataset sizes:")
        print(f"  - Train: {X_train_scaled.shape[0]:,} samples")
        print(f"  - Val:   {X_val_scaled.shape[0]:,} samples")
        print(f"  - Test:  {X_test_scaled.shape[0]:,} samples")
        
        return {
            'X_train': X_train_scaled,
            'X_val': X_val_scaled,
            'X_test': X_test_scaled,
            'y_train': y_train.values,
            'y_val': y_val.values,
            'y_test': y_test.values,
            'feature_names': self.feature_names
        }
    
    def save_preprocessor(self, filepath):
        """Save preprocessor state"""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Save scaler

        joblib.dump(self.scaler, filepath.parent / f"{filepath.stem}_scaler.pkl")
        
        # Save metadata

        metadata = {
            'feature_names': self.feature_names,
            'label_column': self.label_column,
            'config': self.config
        }
        
        with open(filepath.parent / f"{filepath.stem}_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n Preprocessor saved to {filepath.parent}")
    
    def load_preprocessor(self, filepath):
        """Load preprocessor state"""
        filepath = Path(filepath)
        
        # Load scaler

        self.scaler = joblib.load(filepath.parent / f"{filepath.stem}_scaler.pkl")
        
        # Load metadata

        with open(filepath.parent / f"{filepath.stem}_metadata.json", 'r') as f:
            metadata = json.load(f)
        
        self.feature_names = metadata['feature_names']
        self.label_column = metadata['label_column']
        self.config = metadata['config']
        
        print(f" Preprocessor loaded from {filepath.parent}")

def load_and_combine_datasets(file_patterns, dataset_name="Dataset"):
    """
    Load multiple CSV files and combine them into a single dataset
    
    Args:
        file_patterns: List of file paths or glob patterns
        dataset_name: Name for the combined dataset
    
    Returns:
        Combined pandas DataFrame
    """
    from glob import glob
    
    print(f"\n{'='*80}")
    print(f"LOADING {dataset_name.upper()}")
    print(f"{'='*80}")
    
    all_dfs = []
    
    for pattern in file_patterns:
        files = glob(str(pattern)) if '*' in str(pattern) else [pattern]
        
        for filepath in files:
            print(f"\nLoading: {Path(filepath).name}")
            try:
                df = pd.read_csv(filepath, low_memory=False)
                print(f"  Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
                all_dfs.append(df)
            except Exception as e:
                print(f"  ERROR: {str(e)}")
    
    if not all_dfs:
        raise ValueError(f"No datasets loaded for {dataset_name}")
    
    # Combine all dataframes

    print(f"\nCombining {len(all_dfs)} datasets...")
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    print(f"\n{'='*80}")
    print(f" COMBINED {dataset_name.upper()}")
    print(f"{'='*80}")
    print(f"Total: {combined_df.shape[0]:,} rows × {combined_df.shape[1]} columns")
    print(f"Memory: {combined_df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    
    return combined_df

if __name__ == "__main__":
    # Example usage

    print("Data Preprocessing Module")
    print("This module provides utilities for preprocessing cybersecurity datasets")
