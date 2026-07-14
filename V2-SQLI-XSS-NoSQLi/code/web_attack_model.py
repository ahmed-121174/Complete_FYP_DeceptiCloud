"""
Web Attack Detection Model (SQLi, NoSQLi, XSS)
Multi-Layer Perceptron (MLP) for binary classification
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models, callbacks
from tensorflow.keras.optimizers import Adam
import numpy as np
import matplotlib.pyplot as plt
import json
from pathlib import Path
from datetime import datetime

class WebAttackDetector:
    """
    ANN-based Web Attack Detection Model
    Detects: SQL Injection, NoSQL Injection, and XSS attacks
    """
    
    def __init__(self, input_dim, config=None):
        """
        Initialize the Web Attack Detector
        
        Args:
            input_dim: Number of input features
            config: Model configuration dictionary
        """
        self.input_dim = input_dim
        self.config = config or self.default_config()
        self.model = None
        self.history = None
        
    @staticmethod
    def default_config():
        """Default model configuration"""
        return {
            'hidden_layer_1': 128,
            'hidden_layer_2': 64,
            'dropout_rate': 0.3,
            'learning_rate': 0.001,
            'activation': 'relu',
            'output_activation': 'sigmoid',
            'loss': 'binary_crossentropy',
            'metrics': ['accuracy', 'precision', 'recall']
        }
    
    def build_model(self):
        """Build the MLP architecture"""
        print("BUILDING WEB ATTACK DETECTION MODEL")
        
        model = models.Sequential([
            # Input layer

            layers.Input(shape=(self.input_dim,), name='input_layer'),
            
            # Hidden Layer 1

            layers.Dense(
                self.config['hidden_layer_1'],
                activation=self.config['activation'],
                name='hidden_layer_1',
                kernel_initializer='he_normal'
            ),
            layers.Dropout(self.config['dropout_rate'], name='dropout_1'),
            layers.BatchNormalization(name='batch_norm_1'),
            
            # Hidden Layer 2

            layers.Dense(
                self.config['hidden_layer_2'],
                activation=self.config['activation'],
                name='hidden_layer_2',
                kernel_initializer='he_normal'
            ),
            layers.Dropout(self.config['dropout_rate'], name='dropout_2'),
            layers.BatchNormalization(name='batch_norm_2'),
            
            # Output Layer (Binary Classification)

            layers.Dense(
                1,
                activation=self.config['output_activation'],
                name='output_layer'
            )
        ], name='WebAttackDetector')
        
        # Compile model

        model.compile(
            optimizer=Adam(learning_rate=self.config['learning_rate']),
            loss=self.config['loss'],
            metrics=[
                'accuracy',
                keras.metrics.Precision(name='precision'),
                keras.metrics.Recall(name='recall'),
                keras.metrics.AUC(name='auc')
            ]
        )
        
        self.model = model
        
        # Print model summary

        print("\n Model Architecture:")
        self.model.summary()
        
        print(f"\n Model built successfully!")
        print(f"   Input dimension: {self.input_dim}")
        print(f"   Hidden layers: {self.config['hidden_layer_1']} → {self.config['hidden_layer_2']}")
        print(f"   Output: Binary (0=Benign, 1=Attack)")
        print(f"   Total parameters: {self.model.count_params():,}")
        
        return self.model
    
    def train(self, X_train, y_train, X_val, y_val, epochs=50, batch_size=32, class_weight=None):
        """
        Train the model
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features
            y_val: Validation labels
            epochs: Number of training epochs
            batch_size: Batch size
            class_weight: Optional class weights dict for imbalanced data
        
        Returns:
            Training history
        """
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")
        
        print("TRAINING WEB ATTACK DETECTION MODEL")
        
        print(f"\nTraining set: {X_train.shape[0]:,} samples")
        print(f"Validation set: {X_val.shape[0]:,} samples")
        print(f"Epochs: {epochs}, Batch size: {batch_size}")
        if class_weight:
            print(f"Using class weights: {class_weight}")
        
        # Callbacks

        callback_list = [
            # Early stopping

            callbacks.EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True,
                verbose=1
            ),
            
            # Reduce learning rate on plateau

            callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-7,
                verbose=1
            ),
            
            # Model checkpoint

            callbacks.ModelCheckpoint(
                'models/web_attack_best_model.keras',
                monitor='val_accuracy',
                save_best_only=True,
                verbose=1
            )
        ]
        
        # Create models directory

        Path('models').mkdir(exist_ok=True)
        
        # Train the model

        print("\n Starting training...")
        
        self.history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            class_weight=class_weight,
            callbacks=callback_list,
            verbose=1
        )
        
        print("\n Training complete!")
        
        return self.history
    
    def evaluate(self, X_test, y_test):
        """
        Evaluate the model on test data
        
        Args:
            X_test: Test features
            y_test: Test labels
        
        Returns:
            Dictionary of evaluation metrics
        """
        print("EVALUATING WEB ATTACK DETECTION MODEL")
        
        print(f"\nTest set: {X_test.shape[0]:,} samples")
        
        # Evaluate

        results = self.model.evaluate(X_test, y_test, verbose=0)
        
        metrics = {
            'loss': results[0],
            'accuracy': results[1],
            'precision': results[2],
            'recall': results[3],
            'auc': results[4]
        }
        
        # Calculate F1 score

        if metrics['precision'] + metrics['recall'] > 0:
            metrics['f1_score'] = 2 * (metrics['precision'] * metrics['recall']) / \
                                  (metrics['precision'] + metrics['recall'])
        else:
            metrics['f1_score'] = 0.0
        
        # Print results

        print(f"\n Test Results:")
        print(f"   Loss:      {metrics['loss']:.4f}")
        print(f"   Accuracy:  {metrics['accuracy']*100:.2f}%")
        print(f"   Precision: {metrics['precision']*100:.2f}%")
        print(f"   Recall:    {metrics['recall']*100:.2f}%")
        print(f"   F1-Score:  {metrics['f1_score']*100:.2f}%")
        print(f"   AUC:       {metrics['auc']:.4f}")
        
        # Predictions for confusion matrix

        y_pred = self.predict(X_test)
        y_pred_binary = (y_pred >= 0.5).astype(int).flatten()
        
        # Confusion matrix

        from sklearn.metrics import confusion_matrix, classification_report
        
        cm = confusion_matrix(y_test, y_pred_binary)
        print(f"\n Confusion Matrix:")
        print(f"                Predicted")
        print(f"              Benign  Attack")
        print(f"   Benign    {cm[0][0]:6d}  {cm[0][1]:6d}")
        print(f"   Attack    {cm[1][0]:6d}  {cm[1][1]:6d}")
        
        print(f"\n Classification Report:")
        print(classification_report(y_test, y_pred_binary, 
                                   target_names=['Benign', 'Attack']))
        
        return metrics
    
    def predict(self, X):
        """
        Make predictions
        
        Args:
            X: Input features
        
        Returns:
            Predictions (probabilities)
        """
        return self.model.predict(X, verbose=0)
    
    def predict_binary(self, X, threshold=0.5):
        """
        Make binary predictions
        
        Args:
            X: Input features
            threshold: Classification threshold
        
        Returns:
            Binary predictions (0 or 1)
        """
        probabilities = self.predict(X)
        return (probabilities >= threshold).astype(int).flatten()
    
    def plot_training_history(self, save_path='plots/web_attack_training.png'):
        """Plot training history"""
        if self.history is None:
            print("No training history available")
            return
        
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Web Attack Detection Model - Training History', fontsize=16, fontweight='bold')
        
        # Accuracy

        axes[0, 0].plot(self.history.history['accuracy'], label='Train', linewidth=2)
        axes[0, 0].plot(self.history.history['val_accuracy'], label='Validation', linewidth=2)
        axes[0, 0].set_title('Model Accuracy')
        axes[0, 0].set_xlabel('Epoch')
        axes[0, 0].set_ylabel('Accuracy')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # Loss

        axes[0, 1].plot(self.history.history['loss'], label='Train', linewidth=2)
        axes[0, 1].plot(self.history.history['val_loss'], label='Validation', linewidth=2)
        axes[0, 1].set_title('Model Loss')
        axes[0, 1].set_xlabel('Epoch')
        axes[0, 1].set_ylabel('Loss')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # Precision

        axes[1, 0].plot(self.history.history['precision'], label='Train', linewidth=2)
        axes[1, 0].plot(self.history.history['val_precision'], label='Validation', linewidth=2)
        axes[1, 0].set_title('Model Precision')
        axes[1, 0].set_xlabel('Epoch')
        axes[1, 0].set_ylabel('Precision')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        
        # Recall

        axes[1, 1].plot(self.history.history['recall'], label='Train', linewidth=2)
        axes[1, 1].plot(self.history.history['val_recall'], label='Validation', linewidth=2)
        axes[1, 1].set_title('Model Recall')
        axes[1, 1].set_xlabel('Epoch')
        axes[1, 1].set_ylabel('Recall')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"\n Training history plot saved to: {save_path}")
        plt.close()
    
    def save_model(self, filepath='models/web_attack_detector.keras'):
        """Save the trained model"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        self.model.save(filepath)
        
        # Save config and metadata

        metadata = {
            'input_dim': self.input_dim,
            'config': self.config,
            'trained_at': datetime.now().isoformat(),
            'model_type': 'WebAttackDetector'
        }
        
        metadata_path = Path(filepath).with_suffix('.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n Model saved to: {filepath}")
        print(f" Metadata saved to: {metadata_path}")
    
    @classmethod
    def load_model(cls, filepath='models/web_attack_detector.keras'):
        """Load a trained model"""
        model = keras.models.load_model(filepath)
        
        # Load metadata

        metadata_path = Path(filepath).with_suffix('.json')
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        instance = cls(metadata['input_dim'], metadata['config'])
        instance.model = model
        
        print(f" Model loaded from: {filepath}")
        
        return instance

if __name__ == "__main__":
    print("Web Attack Detection Model Module")
    print("ANN/MLP architecture for detecting SQLi, NoSQLi, and XSS attacks")
