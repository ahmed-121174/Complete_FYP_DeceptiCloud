"""
Training Script for DDoS Detection Model - Using Pre-Sampled Data
Loads pre-sampled DDoS datasets from Datasets/DDoS_sampled/
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from preprocessing import DataPreprocessor, load_and_combine_datasets
from ddos_model import DDoSDetector
import tensorflow as tf

def main():
    print("DDOS DETECTION MODEL - TRAINING WITH PRE-SAMPLED DATA")
    
    tf.random.set_seed(42)
    
    # Use PRE-SAMPLED data directory

    base_path = Path(__file__).parent.parent / "Datasets" / "DDoS_sampled"
    
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
    
    dataset_files = [f for f in dataset_files if f.exists()]
    
    print(f"\n Found {len(dataset_files)} pre-sampled files in {base_path.name}/")
    print("   (Data already sampled to 5% - no further sampling needed)\n")
    
    # Load pre-sampled data

    combined_df = load_and_combine_datasets(dataset_files, "DDoS Dataset (Pre-Sampled)")
    
    # Preprocessing

    preprocessor = DataPreprocessor()
    
    data = preprocessor.preprocess_dataset(
        df=combined_df,
        label_col=None,
        test_size=0.2,
        val_size=0.1,
        select_features=80
    )
    
    preprocessor.save_preprocessor('models/ddos_preprocessor.pkl')
    
    X_train, y_train = data['X_train'], data['y_train']
    X_val, y_val = data['X_val'], data['y_val']
    X_test, y_test = data['X_test'], data['y_test']
    
    print(f"\n Data Splits:")
    print(f"   Training:   {len(y_train):,} samples")
    print(f"   Validation: {len(y_val):,} samples")
    print(f"   Testing:    {len(y_test):,} samples")
    
    # Build and train model

    print("BUILDING DDOS DETECTION MODEL")
    
    detector = DDoSDetector(input_dim=X_train.shape[1])
    detector.build_model()
    
    print("TRAINING DDOS DETECTION MODEL")
    print(f"\nTraining set: {len(y_train):,} samples")
    print(f"Validation set: {len(y_val):,} samples")
    print("Epochs: 100, Batch size: 128\n")
    
    history = detector.train(
        X_train, y_train,
        X_val, y_val,
        epochs=100,
        batch_size=128
    )
    
    print("\n Training complete!\n")
    
    # Evaluate

    print("EVALUATING DDOS DETECTION MODEL")
    print(f"\nTest set: {len(y_test):,} samples\n")
    
    metrics = detector.evaluate(X_test, y_test)
    
    print(f" Test Results:")
    print(f"   Loss:      {metrics['loss']:.4f}")
    print(f"   Accuracy:  {metrics['accuracy']*100:.2f}%")
    print(f"   Precision: {metrics['precision']*100:.2f}%")
    print(f"   Recall:    {metrics['recall']*100:.2f}%")
    print(f"   F1-Score:  {metrics['f1_score']*100:.2f}%")
    print(f"   AUC:       {metrics['auc']:.4f}")
    
    # Save model

    detector.save_model('models/ddos_detector.keras')
    
    print(" DDOS DETECTION MODEL TRAINING COMPLETE - NO ERRORS!")
    print(f"\nFinal Test Accuracy: {metrics['accuracy']*100:.2f}%")
    print(f"Model saved to: models/ddos_detector.keras")
    print(f"Preprocessor saved to: models/ddos_preprocessor.pkl\n")

if __name__ == "__main__":
    main()
