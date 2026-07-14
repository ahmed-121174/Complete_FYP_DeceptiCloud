#!/usr/bin/env python3
"""
Credential Stuffing Detector Training Script
Trains a Gradient Boosting classifier for credential stuffing detection
"""

import json
import numpy as np
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

FEATURE_NAMES = [
    'num_attempts', 'avg_time_between_attempts', 'min_time_between_attempts',
    'attempts_per_minute', 'unique_ips', 'unique_user_agents', 'unique_usernames',
    'ip_rotation_rate', 'ua_rotation_rate', 'username_rotation_rate',
    'success_rate', 'avg_response_time'
]

def load_dataset(data_path):
    """Load credential stuffing dataset"""
    with open(data_path) as f:
        data = json.load(f)
    
    X = []
    y = []
    for sample in data:
        features = [sample.get(f, 0) for f in FEATURE_NAMES]
        X.append(features)
        y.append(sample['label'])
    
    return np.array(X), np.array(y)

def train_credential_stuffing_detector():
    """Train credential stuffing detector model"""
    print("=" * 60)
    print("CREDENTIAL STUFFING DETECTOR TRAINING")
    print("=" * 60)
    
    # Load dataset
    data_path = Path(__file__).parent.parent / 'data' / 'credential_stuffing_dataset.json'
    print(f"\nLoading dataset from {data_path}...")
    X, y = load_dataset(data_path)
    print(f"Loaded {len(X)} samples with {X.shape[1]} features")
    print(f"  Malicious: {sum(y)}")
    print(f"  Benign: {len(y) - sum(y)}")
    
    # Split dataset
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\nTrain samples: {len(X_train)}")
    print(f"Test samples: {len(X_test)}")
    
    # Scale features
    print("\nScaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train Gradient Boosting with regularization to prevent overfitting
    print("\nTraining Gradient Boosting classifier with regularization...")
    model = GradientBoostingClassifier(
        n_estimators=50,  # Reduced from 100
        max_depth=3,  # Reduced from 5
        learning_rate=0.05,  # Reduced from 0.1
        min_samples_split=10,  # Added constraint
        min_samples_leaf=5,  # Added constraint
        subsample=0.8,  # Added sampling
        random_state=42
    )
    model.fit(X_train_scaled, y_train)
    print("Training complete!")
    
    # Evaluate
    print("\nEvaluating model...")
    y_pred = model.predict(X_test_scaled)
    
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    
    print(f"\nPerformance Metrics:")
    print(f"  Accuracy:  {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"  Precision: {precision:.4f}")
    print(f"  Recall:    {recall:.4f}")
    print(f"  F1-Score:  {f1:.4f}")
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Normal', 'Credential Stuffing']))
    
    # Feature importance
    print("\nTop 5 Most Important Features:")
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1][:5]
    for i, idx in enumerate(indices, 1):
        print(f"  {i}. {FEATURE_NAMES[idx]}: {importances[idx]:.4f}")
    
    # Save model
    models_dir = Path(__file__).parent.parent / 'models'
    models_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = models_dir / 'credential_stuffing_detector.pkl'
    scaler_path = models_dir / 'credential_stuffing_scaler.pkl'
    metadata_path = models_dir / 'credential_stuffing_metadata.json'
    
    print(f"\nSaving model to {model_path}...")
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    
    # Save metadata
    metadata = {
        'model_type': 'Gradient Boosting',
        'accuracy': float(accuracy),
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1),
        'num_features': len(FEATURE_NAMES),
        'feature_names': FEATURE_NAMES,
        'train_samples': len(X_train),
        'test_samples': len(X_test),
        'attack_type': 'Credential Stuffing',
    }
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Model saved successfully!")
    print(f"  Model: {model_path}")
    print(f"  Scaler: {scaler_path}")
    print(f"  Metadata: {metadata_path}")
    
    return model, scaler, metadata

if __name__ == '__main__':
    train_credential_stuffing_detector()
