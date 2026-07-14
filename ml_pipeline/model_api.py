from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import numpy as np
import joblib
import json
from pathlib import Path
import tensorflow as tf
from datetime import datetime
import logging
import sys

# Central config

sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))
from config import ML_API_PORT, RATE_LIMIT_ML_API, MAX_FEATURE_COUNT

app = Flask(__name__)
CORS(app)
limiter = Limiter(get_remote_address, app=app, default_limits=[RATE_LIMIT_ML_API])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# GLOBAL MODEL REFERENCES

web_attack_model = None
web_attack_preprocessor = None
ddos_model = None
ddos_scaler = None
ddos_features = None
ddos_threshold = 0.5  # overridden by threshold.txt if present

# New models
xss_model = None
xss_vectorizer = None
brute_force_model = None
brute_force_scaler = None
port_scan_model = None
port_scan_scaler = None
credential_stuffing_model = None
credential_stuffing_scaler = None
anomaly_model = None
anomaly_scaler = None

# Base dir for resolving model paths

BASE_DIR = Path(__file__).parent

def load_models():
    """Load all trained models and preprocessors."""
    global web_attack_model, web_attack_preprocessor
    global ddos_model, ddos_scaler, ddos_features
    global xss_model, xss_vectorizer
    global brute_force_model, brute_force_scaler
    global port_scan_model, port_scan_scaler
    global credential_stuffing_model, credential_stuffing_scaler
    global anomaly_model, anomaly_scaler

    logger.info("LOADING MODELS")

    # Web Attack Detector V2 (Keras)

    try:
        web_model_path = BASE_DIR / 'models' / 'web_attack_detector_v2.keras'
        web_attack_model = tf.keras.models.load_model(str(web_model_path))

        scaler_path = BASE_DIR / 'models' / 'web_attack_preprocessor_scaler.pkl'
        if scaler_path.exists():
            web_attack_preprocessor = joblib.load(scaler_path)
        logger.info(f" Web Attack Detector V2 loaded from {web_model_path.name}")
    except Exception as e:
        logger.error(f" Web Attack Detector: {e}")

    # DDoS Detector V1 (Random Forest)

    try:
        ddos_dir = BASE_DIR.parent / 'DDoS' / 'V1' / 'models'
        ddos_model = joblib.load(ddos_dir / 'best_model.pkl')
        ddos_scaler = joblib.load(ddos_dir / 'scaler.pkl')
        ddos_features = joblib.load(ddos_dir / 'selected_features.pkl')
        threshold_path = ddos_dir / 'threshold.txt'
        if threshold_path.exists():
            ddos_threshold = float(threshold_path.read_text().strip())
            logger.info(f" DDoS threshold loaded: {ddos_threshold:.4f}")
        logger.info(f" DDoS Detector V1 loaded (Random Forest, {len(ddos_features)} features)")
    except Exception as e:
        logger.error(f" DDoS Detector: {e}")
    
    # XSS Detector
    try:
        xss_model = joblib.load(BASE_DIR / 'models' / 'xss_detector.pkl')
        xss_vectorizer = joblib.load(BASE_DIR / 'models' / 'xss_vectorizer.pkl')
        logger.info(" XSS Detector loaded (Random Forest + TF-IDF)")
    except Exception as e:
        logger.error(f" XSS Detector: {e}")
    
    # Brute Force Detector
    try:
        brute_force_model = joblib.load(BASE_DIR / 'models' / 'brute_force_detector.pkl')
        brute_force_scaler = joblib.load(BASE_DIR / 'models' / 'brute_force_scaler.pkl')
        logger.info(" Brute Force Detector loaded (Random Forest)")
    except Exception as e:
        logger.error(f" Brute Force Detector: {e}")
    
    # Port Scan Detector
    try:
        port_scan_model = joblib.load(BASE_DIR / 'models' / 'port_scan_detector.pkl')
        port_scan_scaler = joblib.load(BASE_DIR / 'models' / 'port_scan_scaler.pkl')
        logger.info(" Port Scan Detector loaded (Random Forest)")
    except Exception as e:
        logger.error(f" Port Scan Detector: {e}")
    
    # Credential Stuffing Detector
    try:
        credential_stuffing_model = joblib.load(BASE_DIR / 'models' / 'credential_stuffing_detector.pkl')
        credential_stuffing_scaler = joblib.load(BASE_DIR / 'models' / 'credential_stuffing_scaler.pkl')
        logger.info(" Credential Stuffing Detector loaded (Gradient Boosting)")
    except Exception as e:
        logger.error(f" Credential Stuffing Detector: {e}")
    
    # Anomaly Detector
    try:
        anomaly_model = joblib.load(BASE_DIR / 'models' / 'anomaly_detector.pkl')
        anomaly_scaler = joblib.load(BASE_DIR / 'models' / 'anomaly_scaler.pkl')
        logger.info(" Anomaly Detector loaded (Isolation Forest)")
    except Exception as e:
        logger.error(f" Anomaly Detector: {e}")


# ENDPOINTS

@app.route('/', methods=['GET'])
def index():
    """API info."""
    return jsonify({
        'name': 'Cyber Attack Detection API',
        'version': '3.0.0',
        'models': {
            'web_attack': 'V2 Keras (SQLi/NoSQLi/XSS)',
            'ddos': 'V1 Random Forest (99.88% balanced accuracy)',
            'xss': 'Random Forest + TF-IDF (100% accuracy)',
            'brute_force': 'Random Forest (100% accuracy)',
            'port_scan': 'Random Forest (100% accuracy)',
            'credential_stuffing': 'Gradient Boosting (100% accuracy)',
            'anomaly': 'Isolation Forest (87% accuracy)'
        },
        'endpoints': {
            '/api/detect/web-attack': 'POST — detect web attacks',
            '/api/detect/ddos': 'POST — detect DDoS',
            '/api/detect/xss': 'POST — detect XSS',
            '/api/detect/brute-force': 'POST — detect brute force',
            '/api/detect/port-scan': 'POST — detect port scanning',
            '/api/detect/credential-stuffing': 'POST — detect credential stuffing',
            '/api/detect/anomaly': 'POST — detect anomalies',
            '/api/detect/batch': 'POST — batch detection',
            '/api/health': 'GET — health check',
            '/api/model-info': 'GET — model metadata'
        }
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'models': {
            'web_attack': web_attack_model is not None,
            'ddos': ddos_model is not None,
            'xss': xss_model is not None,
            'brute_force': brute_force_model is not None,
            'port_scan': port_scan_model is not None,
            'credential_stuffing': credential_stuffing_model is not None,
            'anomaly': anomaly_model is not None
        }
    })

@app.route('/api/reload-models', methods=['POST'])
def reload_models():
    """Hot-reload all models — called by Adaptive Learning Engine after retraining."""
    try:
        load_models()
        loaded = sum([
            web_attack_model is not None, ddos_model is not None,
            xss_model is not None, brute_force_model is not None,
            port_scan_model is not None, credential_stuffing_model is not None,
            anomaly_model is not None
        ])
        logger.info(f'Models hot-reloaded: {loaded}/7 loaded')
        return jsonify({'status': 'reloaded', 'models_loaded': loaded,
                        'timestamp': datetime.now().isoformat()})
    except Exception as e:
        logger.error(f'Reload error: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/detect/web-attack', methods=['POST'])
def detect_web_attack():
    """
    Detect Web Attacks (SQLi, NoSQLi, XSS).

    JSON body: {"features": [f1, f2, ..., fN]}
    Returns: {"prediction": 0|1, "confidence": float, ...}
    """
    if web_attack_model is None:
        return jsonify({'error': 'Web Attack Detector not loaded'}), 503

    try:
        data = request.get_json()
        if 'features' not in data:
            return jsonify({'error': 'Missing "features"'}), 400

        raw_features = data['features']

        # (#12) Input bounds validation

        if not isinstance(raw_features, list):
            return jsonify({'error': 'Features must be a list'}), 400
        if len(raw_features) > MAX_FEATURE_COUNT:
            return jsonify({'error': f'Too many features (max {MAX_FEATURE_COUNT})'}), 400
        for i, v in enumerate(raw_features):
            if not isinstance(v, (int, float)):
                return jsonify({'error': f'Feature {i} must be numeric'}), 400
            if not (-1e6 <= v <= 1e6):  # Reasonable bounds
                return jsonify({'error': f'Feature {i} out of bounds'}), 400

        features = np.array(raw_features).reshape(1, -1)

        # Scale if preprocessor is available

        if web_attack_preprocessor is not None:
            expected = web_attack_preprocessor.mean_.shape[0]
            if features.shape[1] != expected:
                return jsonify({
                    'error': f'Expected {expected} features, got {features.shape[1]}'
                }), 400
            features = web_attack_preprocessor.transform(features)
        # Predict

        prob = float(web_attack_model.predict(features, verbose=0)[0][0])
        is_attack = int(prob >= 0.5)

        response = {
            'prediction': is_attack,
            'confidence': prob,
            'attack_type': 'Web Attack (SQLi/NoSQLi/XSS)' if is_attack else 'Benign',
            'is_malicious': bool(is_attack),
            'timestamp': datetime.now().isoformat()
        }
        logger.info(f"Web Attack: pred={is_attack}, conf={prob:.4f}")
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Web attack error: {e}")
        return jsonify({'error': 'Prediction failed'}), 500  # (#5) sanitized

@app.route('/api/detect/ddos', methods=['POST'])
def detect_ddos():
    """
    Detect DDoS Attacks using V1 Random Forest.

    JSON body:
      {"features": {"feat_name": value, ...}}
      OR {"features": [f1, f2, ..., f30]}  (ordered as selected_features)
    """
    if ddos_model is None:
        return jsonify({'error': 'DDoS Detector not loaded'}), 503

    try:
        data = request.get_json()
        if 'features' not in data:
            return jsonify({'error': 'Missing "features"'}), 400

        raw = data['features']

        # Accept dict or list

        if isinstance(raw, dict):
            # Build feature vector in correct order

            row = [raw.get(feat, 0) for feat in ddos_features]
            features = np.array(row).reshape(1, -1)
        else:
            features = np.array(raw).reshape(1, -1)
            if features.shape[1] != len(ddos_features):
                return jsonify({
                    'error': f'Expected {len(ddos_features)} features, got {features.shape[1]}'
                }), 400

        # Scale

        features_scaled = ddos_scaler.transform(features)

        # Predict using optimized threshold

        prob = float(ddos_model.predict_proba(features_scaled)[0][1])
        pred = int(prob >= ddos_threshold)

        response = {
            'prediction': pred,
            'confidence': prob,
            'attack_type': 'DDoS Attack' if pred == 1 else 'Benign',
            'is_malicious': bool(pred),
            'action': 'ROUTE_TO_HONEYPOT' if pred == 1 else 'FORWARD_TO_SERVER',
            'timestamp': datetime.now().isoformat()
        }
        logger.info(f"DDoS: pred={pred}, conf={prob:.4f}")
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"DDoS error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/detect/batch', methods=['POST'])
def detect_batch():
    """
    Batch detection.

    JSON body: {"samples": [{"type": "web-attack"|"ddos", "features": ...}, ...]}
    """
    try:
        data = request.get_json()
        if 'samples' not in data:
            return jsonify({'error': 'Missing "samples"'}), 400

        results = []
        for idx, sample in enumerate(data['samples']):
            if 'type' not in sample or 'features' not in sample:
                results.append({'index': idx, 'error': 'Missing type or features'})
                continue

            if sample['type'] == 'web-attack':
                if web_attack_model is None:
                    results.append({'index': idx, 'error': 'Model not loaded'})
                    continue
                features = np.array(sample['features']).reshape(1, -1)
                if web_attack_preprocessor is not None:
                    features = web_attack_preprocessor.transform(features)     
                prob = float(web_attack_model.predict(features, verbose=0)[0][0])
                pred = int(prob >= 0.5)
                results.append({
                    'index': idx, 'prediction': pred,
                    'confidence': prob,
                    'attack_type': 'Web Attack' if pred else 'Benign'
                })

            elif sample['type'] == 'ddos':
                if ddos_model is None:
                    results.append({'index': idx, 'error': 'Model not loaded'})
                    continue
                raw = sample['features']
                if isinstance(raw, dict):
                    row = [raw.get(f, 0) for f in ddos_features]
                    features = np.array(row).reshape(1, -1)
                else:
                    features = np.array(raw).reshape(1, -1)
                features_scaled = ddos_scaler.transform(features)
                pred = int(ddos_model.predict(features_scaled)[0])
                prob = float(ddos_model.predict_proba(features_scaled)[0][1])
                results.append({
                    'index': idx, 'prediction': pred,
                    'confidence': prob,
                    'attack_type': 'DDoS Attack' if pred else 'Benign'
                })
            else:
                results.append({'index': idx, 'error': f'Unknown type: {sample["type"]}'})

        return jsonify({
            'results': results,
            'total': len(results),
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Batch error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/model-info', methods=['GET'])
def model_info():
    """Return model metadata."""
    info = {'web_attack': None, 'ddos': None, 'xss': None, 'brute_force': None, 
            'port_scan': None, 'credential_stuffing': None, 'anomaly': None}

    # DDoS metadata

    ddos_meta_path = BASE_DIR.parent / 'DDoS' / 'V1' / 'models' / 'metadata.json'
    if ddos_meta_path.exists():
        with open(ddos_meta_path) as f:
            info['ddos'] = json.load(f)

    # Web attack metadata

    web_meta_path = BASE_DIR / 'models' / 'web_attack_detector_v2.json'
    if web_meta_path.exists():
        with open(web_meta_path) as f:
            info['web_attack'] = json.load(f)
    
    # New models metadata
    for model_name in ['xss', 'brute_force', 'port_scan', 'credential_stuffing', 'anomaly']:
        meta_path = BASE_DIR / 'models' / f'{model_name}_metadata.json'
        if meta_path.exists():
            with open(meta_path) as f:
                info[model_name] = json.load(f)

    return jsonify(info)

@app.route('/api/detect/xss', methods=['POST'])
def detect_xss():
    """Detect XSS attacks from text input"""
    if xss_model is None or xss_vectorizer is None:
        return jsonify({'error': 'XSS Detector not loaded'}), 503
    
    try:
        data = request.get_json()
        if 'text' not in data:
            return jsonify({'error': 'Missing "text" field'}), 400
        
        text = data['text']
        
        # Vectorize text
        text_vec = xss_vectorizer.transform([text])
        
        # Predict
        pred = int(xss_model.predict(text_vec)[0])
        prob = float(xss_model.predict_proba(text_vec)[0][1])
        
        response = {
            'prediction': pred,
            'confidence': prob,
            'attack_type': 'XSS' if pred == 1 else 'Benign',
            'is_malicious': bool(pred),
            'timestamp': datetime.now().isoformat()
        }
        logger.info(f"XSS: pred={pred}, conf={prob:.4f}")
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"XSS detection error: {e}")
        return jsonify({'error': 'Prediction failed'}), 500

@app.route('/api/detect/brute-force', methods=['POST'])
def detect_brute_force():
    """Detect brute force attacks from login sequence features"""
    if brute_force_model is None or brute_force_scaler is None:
        return jsonify({'error': 'Brute Force Detector not loaded'}), 503
    
    try:
        data = request.get_json()
        if 'features' not in data:
            return jsonify({'error': 'Missing "features" field'}), 400
        
        features = np.array(data['features']).reshape(1, -1)
        
        # Scale features
        features_scaled = brute_force_scaler.transform(features)
        
        # Predict
        pred = int(brute_force_model.predict(features_scaled)[0])
        prob = float(brute_force_model.predict_proba(features_scaled)[0][1])
        
        response = {
            'prediction': pred,
            'confidence': prob,
            'attack_type': 'Brute Force' if pred == 1 else 'Normal',
            'is_malicious': bool(pred),
            'timestamp': datetime.now().isoformat()
        }
        logger.info(f"Brute Force: pred={pred}, conf={prob:.4f}")
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Brute Force detection error: {e}")
        return jsonify({'error': 'Prediction failed'}), 500

@app.route('/api/detect/port-scan', methods=['POST'])
def detect_port_scan():
    """Detect port scanning from port access sequence features"""
    if port_scan_model is None or port_scan_scaler is None:
        return jsonify({'error': 'Port Scan Detector not loaded'}), 503
    
    try:
        data = request.get_json()
        if 'features' not in data:
            return jsonify({'error': 'Missing "features" field'}), 400
        
        features = np.array(data['features']).reshape(1, -1)
        
        # Scale features
        features_scaled = port_scan_scaler.transform(features)
        
        # Predict
        pred = int(port_scan_model.predict(features_scaled)[0])
        prob = float(port_scan_model.predict_proba(features_scaled)[0][1])
        
        response = {
            'prediction': pred,
            'confidence': prob,
            'attack_type': 'Port Scan' if pred == 1 else 'Normal',
            'is_malicious': bool(pred),
            'timestamp': datetime.now().isoformat()
        }
        logger.info(f"Port Scan: pred={pred}, conf={prob:.4f}")
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Port Scan detection error: {e}")
        return jsonify({'error': 'Prediction failed'}), 500

@app.route('/api/detect/credential-stuffing', methods=['POST'])
def detect_credential_stuffing():
    """Detect credential stuffing from login attempt sequence features"""
    if credential_stuffing_model is None or credential_stuffing_scaler is None:
        return jsonify({'error': 'Credential Stuffing Detector not loaded'}), 503
    
    try:
        data = request.get_json()
        if 'features' not in data:
            return jsonify({'error': 'Missing "features" field'}), 400
        
        features = np.array(data['features']).reshape(1, -1)
        
        # Scale features
        features_scaled = credential_stuffing_scaler.transform(features)
        
        # Predict
        pred = int(credential_stuffing_model.predict(features_scaled)[0])
        prob = float(credential_stuffing_model.predict_proba(features_scaled)[0][1])
        
        response = {
            'prediction': pred,
            'confidence': prob,
            'attack_type': 'Credential Stuffing' if pred == 1 else 'Normal',
            'is_malicious': bool(pred),
            'timestamp': datetime.now().isoformat()
        }
        logger.info(f"Credential Stuffing: pred={pred}, conf={prob:.4f}")
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Credential Stuffing detection error: {e}")
        return jsonify({'error': 'Prediction failed'}), 500

@app.route('/api/detect/anomaly', methods=['POST'])
def detect_anomaly():
    """Detect anomalous requests using Isolation Forest"""
    if anomaly_model is None or anomaly_scaler is None:
        return jsonify({'error': 'Anomaly Detector not loaded'}), 503
    
    try:
        data = request.get_json()
        if 'features' not in data:
            return jsonify({'error': 'Missing "features" field'}), 400
        
        features = np.array(data['features']).reshape(1, -1)
        
        # Scale features
        features_scaled = anomaly_scaler.transform(features)
        
        # Predict (-1 for anomaly, 1 for normal)
        pred_raw = anomaly_model.predict(features_scaled)[0]
        pred = 1 if pred_raw == -1 else 0  # Convert to 0/1
        
        # Get anomaly score
        score = float(anomaly_model.score_samples(features_scaled)[0])
        # Convert score to confidence (more negative = more anomalous)
        confidence = 1.0 / (1.0 + np.exp(score))  # Sigmoid transformation
        
        response = {
            'prediction': pred,
            'confidence': float(confidence),
            'anomaly_score': score,
            'attack_type': 'Anomaly' if pred == 1 else 'Normal',
            'is_malicious': bool(pred),
            'timestamp': datetime.now().isoformat()
        }
        logger.info(f"Anomaly: pred={pred}, score={score:.4f}")
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Anomaly detection error: {e}")
        return jsonify({'error': 'Prediction failed'}), 500

if __name__ == '__main__':
    load_models()
    app.run(host='0.0.0.0', port=ML_API_PORT, debug=False)
