#!/usr/bin/env python3
"""
Anomaly Detector Training Script
Trains an Isolation Forest for anomaly detection
"""

import json
import numpy as np
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

FEATURE_NAMES = [
    'method_is_get', 'method_is_post', 'method_is_unusual', 'query_length',
    'body_length', 'num_headers', 'has_auth', 'response_code', 'response_time',
    'num_params', 'special_chars_count', 'path_depth', 'path_length',
    'has_suspicious_ua', 'ua_length', 'has_suspicious_path', 'has_traversal',
    'response_is_error', 'response_is_redirect', 'fast_response', 'slow_response'
]

def load_dataset(data_path):
    """Load anomaly detection dataset"""
    with open(data_path) as f:
        data = json.load(f)
    
    X = []
    y = []
    for sample in data:
        features = [sample.get(f, 0) for f in FEATURE_NAMES]
        X.append(features)
        y.append(sample['label'])
    
    return np.array(X), np.array(y)

def train_anomaly_detector():
    """Train anomaly detector model"""
    print("=" * 60)
    print("ANOMALY DETECTOR TRAINING")
    print("=" * 60)
    
    # Load dataset
    data_path = Path(__file__).parent.parent / 'data' / 'anomaly_dataset.json'
    print(f"\nLoading dataset from {data_path}...")
    X, y = load_dataset(data_path)
    print(f"Loaded {len(X)} samples with {X.shape[1]} features")
    print(f"  Normal: {len(y) - sum(y)}")
    print(f"  Anomalous: {sum(y)}")
    
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
    
    # Train Isolation Forest
    print("\nTraining Isolation Forest...")
    # Contamination = proportion of anomalies in dataset
    contamination = sum(y_train) / len(y_train)
    print(f"Contamination rate: {contamination:.4f}")
    
    model = IsolationForest(
        n_estimators=100,
        contamination=contamination,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train_scaled)
    print("Training complete!")
    
    # Evaluate
    print("\nEvaluating model...")
    # Isolation Forest returns -1 for anomalies, 1 for normal
    # Convert to 0/1 labels
    y_pred_raw = model.predict(X_test_scaled)
    y_pred = np.where(y_pred_raw == -1, 1, 0)  # -1 (anomaly) -> 1, 1 (normal) -> 0
    
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
    print(classification_report(y_test, y_pred, target_names=['Normal', 'Anomaly']))
    
    # Save model
    models_dir = Path(__file__).parent.parent / 'models'
    models_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = models_dir / 'anomaly_detector.pkl'
    scaler_path = models_dir / 'anomaly_scaler.pkl'
    metadata_path = models_dir / 'anomaly_metadata.json'
    
    print(f"\nSaving model to {model_path}...")
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    
    # Save metadata
    metadata = {
        'model_type': 'Isolation Forest',
        'accuracy': float(accuracy),
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1),
        'num_features': len(FEATURE_NAMES),
        'feature_names': FEATURE_NAMES,
        'train_samples': len(X_train),
        'test_samples': len(X_test),
        'contamination': float(contamination),
        'attack_type': 'Anomaly',
    }
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Model saved successfully!")
    print(f"  Model: {model_path}")
    print(f"  Scaler: {scaler_path}")
    print(f"  Metadata: {metadata_path}")
    
    return model, scaler, metadata

if __name__ == '__main__':
    train_anomaly_detector()
