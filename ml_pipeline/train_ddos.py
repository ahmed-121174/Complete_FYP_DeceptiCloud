"""
Training Script for DDoS Detection Model
Loads all DDoS datasets, preprocesses them, and trains the ANN model
"""

import sys
from pathlib import Path

# Add parent directory to path

sys.path.append(str(Path(__file__).parent))

from preprocessing import DataPreprocessor, load_and_combine_datasets
from ddos_model import DDoSDetector
import tensorflow as tf

def main():
    print("DDOS DETECTION MODEL - TRAINING PIPELINE")
    
    # Set random seeds for reproducibility

    tf.random.set_seed(42)
    
    # Dataset base path

    base_path = Path(__file__).parent.parent / "Datasets" / "DDoS"
    
    # Define all DDoS dataset files

    dataset_files = [
        base_path / "DrDoS_DNS_data_1_per.csv",
        base_path / "DrDoS_LDAP_data_2_0_per.csv",
        base_path / "DrDoS_MSSQL_data_1_3_per.csv",
        base_path / "DrDoS_NTP_data_data_5_per.csv",
        base_path / "DrDoS_NetBIOS_data_1_3_per.csv",
        base_path / "DrDoS_SNMP_data_1_3_per.csv",
        base_path / "DrDoS_SSDP_data_2_per.csv",
        base_path / "DrDoS_UDP_data_2_per.csv",
        base_path / "UDPLag_data_2_0_per.csv",
        base_path / "syn_data.csv",
    ]
    
    # Filter to only existing files

    dataset_files = [f for f in dataset_files if f.exists()]
    
    print(f"\nFound {len(dataset_files)} dataset files to process")
    print("  Using 5% sample from each file for training")
    
    # Load and Sample 10% from Each Dataset

    print("LOADING AND SAMPLING DDOS DATASETS (5% of each file)")
    
    import pandas as pd
    sampled_dataframes = []
    
    for file_path in dataset_files:
        print(f"\nLoading: {file_path.name}")
        df = pd.read_csv(file_path)
        original_size = len(df)
        
        # Sample 5% of the data

        sample_df = df.sample(frac=0.05, random_state=42)
        sampled_size = len(sample_df)
        
        print(f"  Original: {original_size:,} rows → Sampled: {sampled_size:,} rows (5%)")
        sampled_dataframes.append(sample_df)
    
    # Combine all sampled datasets

    print(f"\nCombining {len(sampled_dataframes)} sampled datasets...")
    combined_df = pd.concat(sampled_dataframes, ignore_index=True)
    
    print(" COMBINED SAMPLED DATASET")
    print(f"Total: {len(combined_df):,} rows × {len(combined_df.columns)} columns")
    print(f"Memory: {combined_df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    
    # COMPREHENSIVE DATA CLEANING

    print("DATA CLEANING PHASE")
    
    initial_rows = len(combined_df)
    initial_cols = len(combined_df.columns)
    
    # 1. Remove duplicates

    print("\n1. Removing duplicate rows...")
    before_dup = len(combined_df)
    combined_df = combined_df.drop_duplicates()
    after_dup = len(combined_df)
    print(f"    Removed {before_dup - after_dup:,} duplicates ({((before_dup - after_dup) / before_dup * 100):.2f}%)")
    
    # 2. Handle null values

    print("\n2. Handling null/missing values...")
    null_counts = combined_df.isnull().sum()
    null_cols = null_counts[null_counts > 0]
    if len(null_cols) > 0:
        print(f"   Found {len(null_cols)} columns with nulls:")
        for col, count in null_cols.items():
            pct = (count / len(combined_df)) * 100
            print(f"     - {col}: {count:,} nulls ({pct:.2f}%)")
            if pct > 50:
                print(f"       → Dropping column '{col}' (>50% null)")
                combined_df = combined_df.drop(columns=[col])
            else:
                # Fill with median for numeric, mode for categorical

                if combined_df[col].dtype in ['float64', 'int64']:
                    fill_value = combined_df[col].median()
                    combined_df[col] = combined_df[col].fillna(fill_value)
                    print(f"       → Filled with median ({fill_value})")
                else:
                    fill_value = combined_df[col].mode()[0] if len(combined_df[col].mode()) > 0 else 'UNKNOWN'
                    combined_df[col] = combined_df[col].fillna(fill_value)
                    print(f"       → Filled with mode ('{fill_value}')")
    else:
        print("    No null values found!")
    
    # 3. Remove inf values

    print("\n3. Handling infinite values...")
    inf_count = 0
    for col in combined_df.select_dtypes(include=['float64', 'int64']).columns:
        inf_mask = combined_df[col].isin([float('inf'), float('-inf')])
        if inf_mask.any():
            inf_count += inf_mask.sum()
            combined_df = combined_df[~inf_mask]
    if inf_count > 0:
        print(f"    Removed {inf_count:,} rows with infinite values")
    else:
        print("    No infinite values found!")
    
    # 4. Remove constant columns (no variance)

    print("\n4. Removing constant columns...")
    constant_cols = [col for col in combined_df.columns if combined_df[col].nunique() <= 1]
    if constant_cols:
        print(f"    Removing {len(constant_cols)} constant columns: {constant_cols}")
        combined_df = combined_df.drop(columns=constant_cols)
    else:
        print("    No constant columns found!")
    
    print(" CLEANING COMPLETE")
    print(f"Rows: {initial_rows:,} → {len(combined_df):,} ({len(combined_df)/initial_rows*100:.1f}% remaining)")
    print(f"Columns: {initial_cols} → {len(combined_df.columns)} ({len(combined_df.columns)/initial_cols*100:.1f}% remaining)")
    
    # Initialize preprocessor

    preprocessor = DataPreprocessor()
    
    # Preprocess data

    data = preprocessor.preprocess_dataset(
        df=combined_df,
        label_col=None,  # Auto-detect
        test_size=0.2,
        val_size=0.1,
        select_features=80  # Select top 80 features for network traffic
    )
    
    # Save preprocessor

    preprocessor.save_preprocessor('models/ddos_preprocessor.pkl')
    
    # Get data splits

    X_train = data['X_train']
    y_train = data['y_train']
    X_val = data['X_val']
    y_val = data['y_val']
    X_test = data['X_test']
    y_test = data['y_test']
    
    # Build model

    input_dim = X_train.shape[1]
    detector = DDoSDetector(input_dim=input_dim)
    detector.build_model()
    
    # Train model

    history = detector.train(
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        epochs=100,
        batch_size=128  # Larger batch size for network traffic
    )
    
    # Evaluate model

    metrics = detector.evaluate(X_test, y_test)
    
    # Plot training history

    detector.plot_training_history('plots/ddos_training_history.png')
    
    # Save model

    detector.save_model('models/ddos_detector.keras')
    
    print(" DDOS DETECTION MODEL TRAINING COMPLETE!")
    print(f"\nFinal Test Accuracy: {metrics['accuracy']*100:.2f}%")
    print(f"Model saved to: models/ddos_detector.keras")
    print(f"Preprocessor saved to: models/ddos_preprocessor.pkl")
    
if __name__ == "__main__":
    main()
