"""
Honeypot Web Application
Flask-based deceptive web application that mimics various services
Logs all requests and integrates with ML detection models
"""

from flask import Flask, request, render_template, jsonify, redirect, url_for
import requests
import json
import os
from datetime import datetime
from pathlib import Path
import logging

# Import logger

from logger import HoneypotLogger

app = Flask(__name__)

# Configuration

ML_API_URL = os.getenv('ML_API_URL', 'http://localhost:5000')
HONEYPOT_TYPE = os.getenv('HONEYPOT_TYPE', 'deceptive')  # 'legitimate' or 'deceptive'
HONEYPOT_SERVICE = os.getenv('HONEYPOT_SERVICE', 'ecommerce')  # Type of service to mimic

# Initialize logger

logger = HoneypotLogger(honeypot_type=HONEYPOT_TYPE, service=HONEYPOT_SERVICE)

# Configure Flask logging

logging.basicConfig(level=logging.INFO)
app_logger = logging.getLogger(__name__)

def analyze_request(request_data):
    """
    Send request data to ML API for analysis
    """
    try:
        # Determine attack type based on request

        if 'sql' in str(request_data).lower() or 'union' in str(request_data).lower():
            endpoint = f"{ML_API_URL}/api/detect/web-attack"
        else:
            # For now, default to web attack detection

            endpoint = f"{ML_API_URL}/api/detect/web-attack"
        
        # In production, extract actual features from request

        # For now, just log

        app_logger.info(f"Would analyze with: {endpoint}")
        
        return {'is_attack': False, 'confidence': 0.0}
    except Exception as e:
        app_logger.error(f"Error in ML analysis: {e}")
        return None

@app.before_request
def log_request():
    """Log all incoming requests"""
    request_info = {
        'timestamp': datetime.now().isoformat(),
        'remote_addr': request.remote_addr,
        'method': request.method,
        'path': request.path,
        'user_agent': request.user_agent.string,
        'args': dict(request.args),
        'form': dict(request.form) if request.form else {},
        'headers': dict(request.headers),
    }
    
    logger.log_request(request_info)
    
    # Check for suspicious patterns

    suspicious_patterns = [
        'union', 'select', 'drop', 'insert', 'update', 'delete',
        '<script>', 'javascript:', 'onerror=', 'onload=',
        '../', '..\\', '/etc/passwd', 'cmd.exe'
    ]
    
    request_str = str(request_info).lower()
    for pattern in suspicious_patterns:
        if pattern in request_str:
            logger.log_attack({
                'pattern_detected': pattern,
                'request': request_info
            })
            break

# E-Commerce Site Routes

@app.route('/')
def index():
    """Homepage"""
    return render_template(f'{HONEYPOT_SERVICE}/index.html',
                         honeypot_type=HONEYPOT_TYPE)

@app.route('/products')
def products():
    """Products listing"""
    return render_template(f'{HONEYPOT_SERVICE}/products.html')

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Product detail page"""
    return render_template(f'{HONEYPOT_SERVICE}/product_detail.html',
                         product_id=product_id)

@app.route('/search')
def search():
    """Search functionality - common target for SQLi"""
    query = request.args.get('q', '')
    
    # Log search query

    logger.log_interaction({
        'action': 'search',
        'query': query,
        'timestamp': datetime.now().isoformat()
    })
    
    return render_template(f'{HONEYPOT_SERVICE}/search.html',
                         query=query)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page - common attack target"""
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        # Log login attempt

        logger.log_interaction({
            'action': 'login_attempt',
            'username': username,
            'timestamp': datetime.now().isoformat()
        })
        
        # Always fail for deceptive honeypot

        if HONEYPOT_TYPE == 'deceptive':
            return render_template(f'{HONEYPOT_SERVICE}/login.html',
                                 error='Invalid credentials')
        else:
            # Legitimate site would check credentials

            return redirect(url_for('dashboard'))
    
    return render_template(f'{HONEYPOT_SERVICE}/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if request.method == 'POST':
        logger.log_interaction({
            'action': 'registration_attempt',
            'data': dict(request.form),
            'timestamp': datetime.now().isoformat()
        })
        
        return redirect(url_for('login'))
    
    return render_template(f'{HONEYPOT_SERVICE}/register.html')

@app.route('/dashboard')
def dashboard():
    """User dashboard"""
    return render_template(f'{HONEYPOT_SERVICE}/dashboard.html')

@app.route('/api/products')
def api_products():
    """API endpoint - target for injection attacks"""
    product_id = request.args.get('id', '')
    
    # Fake product data

    products = {
        '1': {'name': 'Laptop', 'price': 999},
        '2': {'name': 'Phone', 'price': 699},
        '3': {'name': 'Tablet', 'price': 499}
    }
    
    if product_id:
        return jsonify(products.get(product_id, {'error': 'Not found'}))
    
    return jsonify(products)

@app.route('/api/submit-review', methods=['POST'])
def submit_review():
    """Submit product review - XSS target"""
    data = request.get_json()
    
    logger.log_interaction({
        'action': 'review_submission',
        'data': data,
        'timestamp': datetime.now().isoformat()
    })
    
    return jsonify({'status': 'success', 'message': 'Review submitted'})

@app.route('/admin')
def admin():
    """Admin panel - high-value target"""
    logger.log_interaction({
        'action': 'admin_access_attempt',
        'timestamp': datetime.now().isoformat(),
        'ip': request.remote_addr
    })
    
    # Always deny for deceptive honeypot

    if HONEYPOT_TYPE == 'deceptive':
        return "Access Denied", 403
    
    return render_template(f'{HONEYPOT_SERVICE}/admin.html')

# Health check

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'honeypot_type': HONEYPOT_TYPE,
        'service': HONEYPOT_SERVICE,
        'timestamp': datetime.now().isoformat()
    })

# Error handlers

@app.errorhandler(404)
def not_found(error):
    logger.log_interaction({
        'action': '404_error',
        'path': request.path,
        'timestamp': datetime.now().isoformat()
    })
    return render_template(f'{HONEYPOT_SERVICE}/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    logger.log_interaction({
        'action': '500_error',
        'path': request.path,
        'error': str(error),
        'timestamp': datetime.now().isoformat()
    })
    return render_template(f'{HONEYPOT_SERVICE}/500.html'), 500

if __name__ == '__main__':
    # Create logs directory

    Path('logs').mkdir(exist_ok=True)
    
    # Runflask app

    port = int(os.getenv('PORT', 8080))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    )
