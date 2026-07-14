#!/usr/bin/env python3
"""
Simple Usage Demo for Web Attack Detector V2
This script shows how to use the correct model (web_attack_detector_v2.keras)
"""

import tensorflow as tf
import numpy as np
import sys
from pathlib import Path

# Add ml_pipeline to path for imports

sys.path.insert(0, str(Path(__file__).parent / "ml_pipeline"))
from feature_engineering import WebAttackFeatureExtractor

def detect_web_attack(query, model, extractor, threshold=0.5):
    """
    Detect if a query is a web attack
    
    Args:
        query: The SQL/web query to check
        model: Loaded TensorFlow model
        extractor: Feature extractor instance
        threshold: Classification threshold (default 0.5)
    
    Returns:
        tuple: (is_attack: bool, confidence: float)
    """
    features = extractor.extract_features(query)
    features_array = np.array([list(features.values())])
    
    prediction = model.predict(features_array, verbose=0)[0][0]
    is_attack = prediction >= threshold
    
    return is_attack, prediction

def main():
    print("WEB ATTACK DETECTOR V2 - USAGE DEMO")
    
    # Load model

    print("\n Loading model...")
    model_path = "ml_pipeline/models/web_attack_detector_v2.keras"
    model = tf.keras.models.load_model(model_path)
    print(f" Model loaded: {model.count_params():,} parameters")
    print(f"   Architecture: 52 → 128 → 64 → 1")
    print(f"   Balanced Accuracy (documented): 93.97%")
    
    # Create feature extractor

    print("\n Initializing feature extractor...")
    extractor = WebAttackFeatureExtractor()
    print(" 52-feature extractor ready")
    
    # Test queries

    test_queries = [
        ("SELECT * FROM users WHERE id = 1", False, "Normal query"),
        ("SELECT * FROM users WHERE id = 1 OR 1=1", True, "SQL Injection"),
        ("SELECT * FROM users WHERE id = 1 UNION SELECT password FROM admin", True, "UNION-based SQLi"),
        ("<script>alert('XSS')</script>", True, "Cross-Site Scripting"),
        ("{$ne: null}", True, "NoSQL Injection"),
        ("SELECT name FROM products WHERE category = 'books'", False, "Benign query"),
    ]
    
    print("TESTING QUERIES")
    
    for i, (query, expected_attack, description) in enumerate(test_queries, 1):
        is_attack, confidence = detect_web_attack(query, model, extractor)
        
        status = " ATTACK" if is_attack else " BENIGN"
        result_match = "" if is_attack == expected_attack else ""
        
        print(f"\n{i}. {description}")
        print(f"   Query: {query}")
        print(f"   Result: {status} ({confidence:.2%} confidence) {result_match}")
    
    print(" DEMO COMPLETE")
    print("\nModel Details:")
    print(f"   File: {model_path}")
    print(f"   Version: V2 (Feature Engineered)")
    print(f"   Features: 52 engineered patterns")
    print(f"   Documented Performance:")
    print(f"      - Balanced Accuracy: 93.97%")
    print(f"      - Overall Accuracy: 89.69%")
    print(f"      - Attack Recall: 89.09%")
    print(f"      - Benign Recall: 98.85%")

if __name__ == "__main__":
    main()
