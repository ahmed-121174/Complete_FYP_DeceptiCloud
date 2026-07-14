#!/usr/bin/env python3
"""
XSS Detector Training Script
Trains a CNN-based text classifier for XSS detection
"""

import json
import numpy as np
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def load_dataset(data_path):
    """Load XSS dataset"""
    with open(data_path) as f:
        data = json.load(f)
    
    texts = [d['text'] for d in data]
    labels = [d['label'] for d in data]
    
    return texts, labels

def train_xss_detector():
    """Train XSS detector model"""
    print("=" * 60)
    print("XSS DETECTOR TRAINING")
    print("=" * 60)
    
    # Load dataset
    data_path = Path(__file__).parent.parent / 'data' / 'xss_dataset.json'
    print(f"\nLoading dataset from {data_path}...")
    texts, labels = load_dataset(data_path)
    print(f"Loaded {len(texts)} samples")
    print(f"  Malicious: {sum(labels)}")
    print(f"  Benign: {len(labels) - sum(labels)}")
    
    # Split dataset
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )
    print(f"\nTrain samples: {len(X_train)}")
    print(f"Test samples: {len(X_test)}")
    
    # Feature extraction using TF-IDF (reduced features to prevent overfitting)
    print("\nExtracting features with TF-IDF...")
    vectorizer = TfidfVectorizer(
        max_features=300,  # Reduced from 1000
        ngram_range=(1, 2),  # Reduced from (1, 3)
        analyzer='char',
        lowercase=True,
        min_df=2,  # Ignore rare patterns
        max_df=0.95  # Ignore too common patterns
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    print(f"Feature vector shape: {X_train_vec.shape}")
    
    # Train Random Forest with regularization to prevent overfitting
    print("\nTraining Random Forest classifier with regularization...")
    model = RandomForestClassifier(
        n_estimators=50,  # Reduced from 100
        max_depth=8,  # Reduced from 20
        min_samples_split=10,  # Increased from 5
        min_samples_leaf=5,  # Added constraint
        max_features='sqrt',  # Added feature sampling
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train_vec, y_train)
    print("Training complete!")
    
    # Evaluate
    print("\nEvaluating model...")
    y_pred = model.predict(X_test_vec)
    
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
    print(classification_report(y_test, y_pred, target_names=['Benign', 'XSS']))
    
    # Save model
    models_dir = Path(__file__).parent.parent / 'models'
    models_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = models_dir / 'xss_detector.pkl'
    vectorizer_path = models_dir / 'xss_vectorizer.pkl'
    metadata_path = models_dir / 'xss_metadata.json'
    
    print(f"\nSaving model to {model_path}...")
    joblib.dump(model, model_path)
    joblib.dump(vectorizer, vectorizer_path)
    
    # Save metadata
    metadata = {
        'model_type': 'Random Forest',
        'accuracy': float(accuracy),
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1),
        'num_features': X_train_vec.shape[1],
        'train_samples': len(X_train),
        'test_samples': len(X_test),
        'attack_type': 'XSS',
    }
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Model saved successfully!")
    print(f"  Model: {model_path}")
    print(f"  Vectorizer: {vectorizer_path}")
    print(f"  Metadata: {metadata_path}")
    
    return model, vectorizer, metadata

if __name__ == '__main__':
    train_xss_detector()
