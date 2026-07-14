"""
DDoS V1 - Prediction Pipeline
Single-request prediction for honeypot integration.
"""

import joblib
import numpy as np
import pandas as pd
from pathlib import Path

class DDoSPredictor:
    """Production-ready DDoS detector for honeypot routing."""

    def __init__(self, models_dir="DDoS/V1/models"):
        models_path = Path(models_dir)

        self.model = joblib.load(models_path / "best_model.pkl")
        self.scaler = joblib.load(models_path / "scaler.pkl")
        self.features = joblib.load(models_path / "selected_features.pkl")

        print(f" DDoS Predictor loaded ({len(self.features)} features)")

    def predict(self, features_dict):
        """
        Predict if traffic is DDoS.

        Args:
            features_dict: dict of feature_name -> value

        Returns:
            dict with 'is_ddos' (bool), 'confidence' (float), 'action' (str)
        """
        # Build feature vector in correct order

        row = []
        for feat in self.features:
            row.append(features_dict.get(feat, 0))

        X = pd.DataFrame([row], columns=self.features)
        X_scaled = self.scaler.transform(X)

        # Predict

        prob = self.model.predict_proba(X_scaled)[0]
        is_ddos = prob[1] >= 0.5

        return {
            'is_ddos': bool(is_ddos),
            'confidence': float(prob[1]),
            'action': 'ROUTE_TO_HONEYPOT' if is_ddos else 'FORWARD_TO_SERVER',
            'benign_prob': float(prob[0]),
            'attack_prob': float(prob[1])
        }

    def predict_batch(self, df):
        """Predict on a DataFrame with the required feature columns."""
        X = df[self.features]
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)
        probabilities = self.model.predict_proba(X_scaled)[:, 1]
        return predictions, probabilities

if __name__ == "__main__":
    print("DDoS V1 Prediction Module")
    print("Usage: predictor = DDoSPredictor(); result = predictor.predict(features)")
