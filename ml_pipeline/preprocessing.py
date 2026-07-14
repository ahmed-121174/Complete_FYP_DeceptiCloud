"""
Updated Data Preprocessing Module with Class Imbalance Handling
Fixes label encoding bug and adds SMOTE oversampling
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.feature_selection import SelectKBest, f_classif
from imblearn.over_sampling import SMOTE
import joblib

class DataPreprocessor:
    """Enhanced preprocessor with SMOTE and proper label handling"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_selector = None
        self.label_column = None
    
    def identify_label_column(self, df):
        """Identify the label column"""
        label_candidates = ['label', 'class', 'target', 'y']
        for col in df.columns:
            if any(candidate in col.lower() for candidate in label_candidates):
                return col
        return df.columns[-1]
    
    def remove_duplicates(self, df):
        """Remove duplicate rows"""
        before = len(df)
        df = df.drop_duplicates()
        after = len(df)
        if before > after:
            print(f"   Removed {before - after:,} duplicates ({(before - after) / before * 100:.2f}%)")
        else:
            print(f"   No duplicates found")
        return df
    
    def handle_null_values(self, df, label_col=None):
        """Handle null values - NEVER drop label column"""
        null_counts = df.isnull().sum()
        null_cols = null_counts[null_counts > 0]
        
        if len(null_cols) > 0:
            print(f"   Found null values in {len(null_cols)} columns:")
            for col, count in null_cols.items():
                pct = (count / len(df)) * 100
                if pct > 50 and col != label_col:
                    print(f"    - Dropping '{col}' (>{pct:.1f}% null)")
                    df = df.drop(columns=[col])
                else:
                    if df[col].dtype in ['float64', 'int64']:
                        median_val = df[col].median()
                        df[col].fillna(median_val, inplace=True)
                        print(f"    - Filled '{col}' with median ({median_val:.2f})")
                    else:
                        mode_val = df[col].mode()[0] if len(df[col].mode()) > 0 else 'unknown'
                        df[col].fillna(mode_val, inplace=True)
                        print(f"    - Filled '{col}' with mode ('{mode_val}')")
        else:
            print(f"   No null values found")
        
        return df
    
    def normalize_label(self, df, label_col):
        """
        FIXED: Normalize label column to binary 0/1
        Handles both numeric labels ('0', '1', 0, 1) and text labels ('BENIGN', 'ATTACK')
        """
        unique_values = df[label_col].unique()
        
        print(f"  Label column '{label_col}' has values: {unique_values}")
        
        # Check if labels are already numeric 0/1

        unique_set = set([str(v).strip() for v in unique_values if pd.notna(v)])
        
        if unique_set <= {'0', '1'}:
            # Already binary - just convert to int

            df[label_col] = df[label_col].fillna('1').astype(str).str.strip().astype(int)
            
            benign_count = (df[label_col] == 0).sum()
            attack_count = (df[label_col] == 1).sum()
            
            print(f"   Labels already binary (0=Benign, 1=Attack):")
            print(f"     - 0 (Benign): {benign_count:,} samples ({benign_count/len(df)*100:.1f}%)")
            print(f"     - 1 (Attack): {attack_count:,} samples ({attack_count/len(df)*100:.1f}%)")
            
            return df
        
        # Otherwise, find benign value by searching for "BENIGN" keyword (case-insensitive)

        benign_values = [v for v in unique_values if 'benign' in str(v).lower()]
        
        if len(benign_values) == 0:
            print(f"    WARNING: No 'BENIGN' label or '0' found. Assuming first unique value is benign.")
            benign_label = unique_values[0]
        else:
            benign_label = benign_values[0]
        
        # Map benign to 0, all others to 1

        df[label_col] = (df[label_col] != benign_label).astype(int)
        
        attack_count = (df[label_col] == 1).sum()
        benign_count = (df[label_col] == 0).sum()
        
        print(f"   Binary mapping:")
        print(f"     - '{benign_label}' → 0 (Benign): {benign_count:,} samples ({benign_count/len(df)*100:.1f}%)")
        print(f"     - All other labels → 1 (Attack): {attack_count:,} samples ({attack_count/len(df)*100:.1f}%)")
        
        return df

    def apply_smote(self, X, y):
        """Apply SMOTE to balance classes"""
        unique, counts = np.unique(y, return_counts=True)
        class_dist = dict(zip(unique, counts))
        
        print(f"\n   Class distribution BEFORE SMOTE:")
        for cls, count in class_dist.items():
            label = "Benign" if cls == 0 else "Attack"
            print(f"     - {label} ({cls}): {count:,} samples ({count/len(y)*100:.1f}%)")
        
        # Apply SMOTE only if minority class has enough samples

        min_samples = min(counts)
        if min_samples < 6:
            print(f"    Skipping SMOTE (minority class has only {min_samples} samples, need >= 6)")
            return X, y
        
        try:
            smote = SMOTE(random_state=42, k_neighbors=min(5, min_samples-1))
            X_resampled, y_resampled = smote.fit_resample(X, y)
            
            unique_after, counts_after = np.unique(y_resampled, return_counts=True)
            class_dist_after = dict(zip(unique_after, counts_after))
            
            print(f"\n   Class distribution AFTER SMOTE:")
            for cls, count in class_dist_after.items():
                label = "Benign" if cls == 0 else "Attack"
                print(f"     - {label} ({cls}): {count:,} samples ({count/len(y_resampled)*100:.1f}%)")
            
            return X_resampled, y_resampled
            
        except Exception as e:
            print(f"    SMOTE failed: {e}. Continuing without oversampling.")
            return X, y
    
    def calculate_class_weights(self, y):
        """Calculate class weights for imbalanced data"""
        from sklearn.utils.class_weight import compute_class_weight
        
        classes = np.unique(y)
        weights = compute_class_weight('balanced', classes=classes, y=y)
        class_weight_dict = dict(zip(classes, weights))
        
        print(f"\n    Calculated class weights:")
        for cls, weight in class_weight_dict.items():
            label = "Benign" if cls == 0 else "Attack"
            print(f"     - {label} ({cls}): {weight:.2f}")
        
        return class_weight_dict
    
    def preprocess_dataset(self, df, label_col=None, test_size=0.2, val_size=0.1, 
                          select_features=None, use_smote=True):
        """
        Complete preprocessing pipeline with SMOTE and class weights
        
        Args:
            df: Input dataframe
            label_col: Name of label column
            test_size: Test set fraction
            val_size: Validation set fraction
            select_features: Number of top features to select
            use_smote: Whether to apply SMOTE oversampling
        """
        print("ENHANCED DATA PREPROCESSING PIPELINE (with SMOTE & Class Weights)")
        
        print(f"\nInitial dataset: {df.shape[0]:,} rows × {df.shape[1]} columns")
        
        # Identify label column

        if label_col is None:
            label_col = self.identify_label_column(df)
        self.label_column = label_col
        print(f"\n1. Label column: '{label_col}'")
        
        # Remove duplicates

        print(f"\n2. Removing duplicates...")
        df = self.remove_duplicates(df)
        
        # Handle nulls

        print(f"\n3. Handling null values...")
        df = self.handle_null_values(df, label_col)
        
        # Remove constant columns

        print(f"\n4. Removing constant columns...")
        constant_cols = [c for c in df.columns if c != label_col and df[c].nunique() <= 1]
        if constant_cols:
            print(f"   Removing {len(constant_cols)} constant columns")
            df = df.drop(columns=constant_cols)
        
        # Handle infinite values

        print(f"\n5. Handling infinite values...")
        for col in df.select_dtypes(include=[np.number]).columns:
            if col != label_col:
                df = df[~df[col].isin([np.inf, -np.inf])]
        
        # FIXED: Normalize labels with proper benign detection

        print(f"\n6. Normalizing labels (FIXED VERSION)...")
        df = self.normalize_label(df, label_col)
        
        # Encode categorical

        print(f"\n7. Encoding categorical features...")
        cat_cols = [c for c in df.select_dtypes(include=['object']).columns if c != label_col]
        if cat_cols:
            print(f"   Encoding {len(cat_cols)} categorical columns")
            for col in cat_cols:
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col].astype(str))
                self.label_encoders[col] = le
        
        # Separate features and target

        print(f"\n8. Separating features and target...")
        X = df.drop(columns=[label_col])
        y = df[label_col]
        print(f"  Features: {X.shape[1]}, Target: {label_col}")
        print(f"  Class distribution: {dict(zip(*np.unique(y, return_counts=True)))}")
        
        # Split data

        print(f"\n9. Splitting data (train: {int((1-test_size-val_size)*100)}%, val: {int(val_size*100)}%, test: {int(test_size*100)}%)...")
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        val_size_adjusted = val_size / (1 - test_size)
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=val_size_adjusted, random_state=42, stratify=y_temp
        )
        
        print(f"  Train: {len(y_train):,} samples")
        print(f"  Val:   {len(y_val):,} samples")
        print(f"  Test:  {len(y_test):,} samples")
        
        # Apply SMOTE to training data only (if enabled)

        if use_smote:
            print(f"\n10. Applying SMOTE to training data...")
            X_train, y_train = self.apply_smote(X_train.values, y_train.values)
            X_train = pd.DataFrame(X_train, columns=X.columns)
            y_train = pd.Series(y_train)
        
        # Feature selection

        if select_features and select_features < X_train.shape[1]:
            print(f"\n11. Selecting top {select_features} features...")
            self.feature_selector = SelectKBest(f_classif, k=select_features)
            X_train = self.feature_selector.fit_transform(X_train, y_train)
            X_val = self.feature_selector.transform(X_val)
            X_test = self.feature_selector.transform(X_test)
            print(f"   Selected {select_features} features")
        
        # Scaling

        print(f"\n12. Scaling features...")
        X_train = self.scaler.fit_transform(X_train)
        X_val = self.scaler.transform(X_val)
        X_test = self.scaler.transform(X_test)
        print(f"   Applied StandardScaler")
        
        # Calculate class weights

        class_weights = self.calculate_class_weights(y_train)
        
        print(" PREPROCESSING COMPLETE")
        print(f"Final feature count: {X_train.shape[1]}")
        print(f"Final dataset sizes:")
        print(f"  - Train: {len(y_train):,} samples")
        print(f"  - Val:   {len(y_val):,} samples")
        print(f"  - Test:  {len(y_test):,} samples")
        
        return {
            'X_train': X_train,
            'y_train': y_train,
            'X_val': X_val,
            'y_val': y_val,
            'X_test': X_test,
            'y_test': y_test,
            'class_weights': class_weights
        }
    
    def save_preprocessor(self, filepath):
        """Save preprocessor to file"""
        joblib.dump({
            'scaler': self.scaler,
            'label_encoders': self.label_encoders,
            'feature_selector': self.feature_selector,
            'label_column': self.label_column
        }, filepath)
        print(f"\n Preprocessor saved to {filepath.split('/')[-1]}")

def load_and_combine_datasets(file_paths, dataset_name="Combined Dataset"):
    """Load and combine multiple CSV files"""
    print(f"LOADING {dataset_name.upper()}")
    
    dataframes = []
    for file_path in file_paths:
        if file_path.exists():
            print(f"\nLoading: {file_path.name}")
            df = pd.read_csv(file_path)
            print(f"  Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
            dataframes.append(df)
    
    print(f"\nCombining {len(dataframes)} datasets...")
    combined = pd.concat(dataframes, ignore_index=True)
    
    print(f" COMBINED {dataset_name.upper()}")
    print(f"Total: {len(combined):,} rows × {len(combined.columns)} columns")
    print(f"Memory: {combined.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    
    return combined
