#!/usr/bin/env python3
"""
Anomaly Detection Dataset Generator
Generates synthetic normal and anomalous request patterns for training
"""

import random
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

NORMAL_PATHS = [
    '/', '/index.html', '/about', '/contact', '/products', '/services',
    '/login', '/register', '/dashboard', '/profile', '/settings',
    '/api/users', '/api/products', '/api/orders', '/search', '/blog'
]

ANOMALOUS_PATHS = [
    '/admin/config', '/backup.sql', '/.env', '/phpMyAdmin', '/wp-admin',
    '/.git/config', '/server-status', '/api/internal', '/../../../etc/passwd',
    '/debug', '/console', '/actuator', '/swagger-ui.html', '/.aws/credentials'
]

NORMAL_USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X)',
]

ANOMALOUS_USER_AGENTS = [
    'sqlmap/1.5', 'nikto/2.1.6', 'Nmap Scripting Engine', 'masscan/1.0',
    'python-requests/2.28.0', 'curl/7.68.0', 'Wget/1.20.3', 'Go-http-client/1.1'
]

def generate_ip():
    """Generate random IP address"""
    return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}"

def generate_normal_request():
    """Generate a normal HTTP request"""
    return {
        'timestamp': datetime.now().isoformat(),
        'ip': generate_ip(),
        'method': random.choice(['GET', 'POST', 'PUT', 'DELETE']),
        'path': random.choice(NORMAL_PATHS),
        'query_length': random.randint(0, 50),
        'body_length': random.randint(0, 1000),
        'num_headers': random.randint(5, 15),
        'user_agent': random.choice(NORMAL_USER_AGENTS),
        'has_auth': random.choice([0, 1]),
        'response_code': random.choice([200, 201, 301, 302, 404]),
        'response_time': random.uniform(0.05, 0.5),
        'num_params': random.randint(0, 5),
        'special_chars_count': random.randint(0, 10),
        'path_depth': random.randint(1, 4),
    }

def generate_anomalous_request():
    """Generate an anomalous HTTP request"""
    anomaly_type = random.choice([
        'suspicious_path', 'suspicious_ua', 'high_frequency',
        'unusual_method', 'large_payload', 'many_params'
    ])
    
    request = {
        'timestamp': datetime.now().isoformat(),
        'ip': generate_ip(),
        'method': 'GET',
        'path': '/',
        'query_length': 0,
        'body_length': 0,
        'num_headers': 10,
        'user_agent': random.choice(NORMAL_USER_AGENTS),
        'has_auth': 0,
        'response_code': 200,
        'response_time': 0.2,
        'num_params': 0,
        'special_chars_count': 0,
        'path_depth': 1,
    }
    
    # Apply anomaly
    if anomaly_type == 'suspicious_path':
        request['path'] = random.choice(ANOMALOUS_PATHS)
        request['path_depth'] = random.randint(5, 10)
    elif anomaly_type == 'suspicious_ua':
        request['user_agent'] = random.choice(ANOMALOUS_USER_AGENTS)
    elif anomaly_type == 'high_frequency':
        request['response_time'] = random.uniform(0.001, 0.05)
    elif anomaly_type == 'unusual_method':
        request['method'] = random.choice(['TRACE', 'OPTIONS', 'CONNECT', 'HEAD'])
    elif anomaly_type == 'large_payload':
        request['body_length'] = random.randint(10000, 100000)
        request['query_length'] = random.randint(1000, 5000)
    elif anomaly_type == 'many_params':
        request['num_params'] = random.randint(20, 50)
        request['special_chars_count'] = random.randint(50, 200)
    
    return request

def extract_features(request):
    """Extract features from request"""
    ua = request['user_agent']
    
    features = {
        'method_is_get': 1 if request['method'] == 'GET' else 0,
        'method_is_post': 1 if request['method'] == 'POST' else 0,
        'method_is_unusual': 1 if request['method'] in ['TRACE', 'OPTIONS', 'CONNECT', 'HEAD'] else 0,
        'query_length': request['query_length'],
        'body_length': request['body_length'],
        'num_headers': request['num_headers'],
        'has_auth': request['has_auth'],
        'response_code': request['response_code'],
        'response_time': request['response_time'],
        'num_params': request['num_params'],
        'special_chars_count': request['special_chars_count'],
        'path_depth': request['path_depth'],
        'path_length': len(request['path']),
        'has_suspicious_ua': 1 if any(t in ua.lower() for t in 
            ['sqlmap', 'nikto', 'nmap', 'scan', 'curl', 'wget', 'python']) else 0,
        'ua_length': len(ua),
        'has_suspicious_path': 1 if any(p in request['path'].lower() for p in 
            ['admin', 'config', 'backup', '.env', 'phpmyadmin', '.git', 'debug']) else 0,
        'has_traversal': 1 if '..' in request['path'] or '%2e' in request['path'].lower() else 0,
        'response_is_error': 1 if request['response_code'] >= 400 else 0,
        'response_is_redirect': 1 if 300 <= request['response_code'] < 400 else 0,
        'fast_response': 1 if request['response_time'] < 0.05 else 0,
        'slow_response': 1 if request['response_time'] > 1.0 else 0,
    }
    
    return features

def generate_dataset(num_samples=20000):
    """Generate anomaly detection dataset"""
    dataset = []
    
    # Generate normal samples (90%)
    num_normal = int(num_samples * 0.9)
    print(f"Generating {num_normal} normal request samples...")
    
    for i in range(num_normal):
        request = generate_normal_request()
        features = extract_features(request)
        features['label'] = 0  # Normal
        features['type'] = 'normal'
        dataset.append(features)
        
        if (i + 1) % 2000 == 0:
            print(f"  Generated {i + 1}/{num_normal} normal samples")
    
    # Generate anomalous samples (10%)
    num_anomalous = num_samples - num_normal
    print(f"Generating {num_anomalous} anomalous request samples...")
    
    for i in range(num_anomalous):
        request = generate_anomalous_request()
        features = extract_features(request)
        features['label'] = 1  # Anomalous
        features['type'] = 'anomaly'
        dataset.append(features)
        
        if (i + 1) % 200 == 0:
            print(f"  Generated {i + 1}/{num_anomalous} anomalous samples")
    
    # Shuffle dataset
    random.shuffle(dataset)
    
    return dataset

def save_dataset(dataset, output_path):
    """Save dataset to JSON file"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(dataset, f, indent=2)
    
    print(f"\nDataset saved to {output_path}")
    print(f"Total samples: {len(dataset)}")
    print(f"Normal: {sum(1 for d in dataset if d['label'] == 0)}")
    print(f"Anomalous: {sum(1 for d in dataset if d['label'] == 1)}")

if __name__ == '__main__':
    # Generate dataset
    dataset = generate_dataset(num_samples=20000)
    
    # Save to file
    output_path = Path(__file__).parent.parent / 'data' / 'anomaly_dataset.json'
    save_dataset(dataset, output_path)
    
    # Print sample
    print("\nSample normal:")
    normal = [d for d in dataset if d['label'] == 0][:2]
    for sample in normal:
        print(f"  Path depth: {sample['path_depth']}, Params: {sample['num_params']}, Suspicious: {sample['has_suspicious_path']}")
    
    print("\nSample anomalous:")
    anomalous = [d for d in dataset if d['label'] == 1][:2]
    for sample in anomalous:
        print(f"  Path depth: {sample['path_depth']}, Params: {sample['num_params']}, Suspicious: {sample['has_suspicious_path']}")
