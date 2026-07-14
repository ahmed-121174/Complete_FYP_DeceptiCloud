#!/usr/bin/env python3
"""
Brute Force Attack Dataset Generator
Generates synthetic login attempt patterns for training
"""

import random
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Common usernames and passwords for brute force patterns
COMMON_USERNAMES = [
    'admin', 'root', 'user', 'test', 'administrator', 'guest', 'demo',
    'webmaster', 'support', 'info', 'sales', 'contact', 'service',
    'john', 'jane', 'mike', 'sarah', 'david', 'mary', 'robert', 'linda'
]

COMMON_PASSWORDS = [
    'password', '123456', '12345678', 'qwerty', 'abc123', 'password123',
    'admin', 'letmein', 'welcome', 'monkey', '1234567890', 'password1',
    'qwerty123', 'admin123', 'root', 'toor', 'pass', 'test', '123123'
]

BRUTE_FORCE_USER_AGENTS = [
    'Hydra/9.0', 'Medusa/2.2', 'Ncrack/0.7', 'THC-Hydra',
    'python-requests/2.28.0', 'curl/7.68.0', 'Wget/1.20.3',
    'Go-http-client/1.1', 'Java/1.8.0', 'Ruby/2.7.0'
]

NORMAL_USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X)',
    'Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X)'
]

def generate_ip():
    """Generate random IP address"""
    return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}"

def generate_brute_force_sequence(num_attempts=50):
    """Generate a brute force attack sequence"""
    ip = generate_ip()
    user_agent = random.choice(BRUTE_FORCE_USER_AGENTS)
    base_time = datetime.now()
    
    attempts = []
    for i in range(num_attempts):
        # Rapid attempts (0.1 to 2 seconds apart)
        time_offset = sum(random.uniform(0.1, 2.0) for _ in range(i))
        timestamp = (base_time + timedelta(seconds=time_offset)).isoformat()
        
        # Try different username/password combinations
        username = random.choice(COMMON_USERNAMES)
        password = random.choice(COMMON_PASSWORDS)
        
        # Most attempts fail, occasional success
        success = random.random() < 0.02  # 2% success rate
        
        attempts.append({
            'timestamp': timestamp,
            'ip': ip,
            'user_agent': user_agent,
            'username': username,
            'password_length': len(password),
            'success': success,
            'response_time': random.uniform(0.05, 0.2),
            'path': '/login',
            'method': 'POST'
        })
    
    return attempts

def generate_normal_login_sequence(num_attempts=5):
    """Generate normal login behavior"""
    ip = generate_ip()
    user_agent = random.choice(NORMAL_USER_AGENTS)
    base_time = datetime.now()
    
    attempts = []
    for i in range(num_attempts):
        # Slower attempts (5 to 60 seconds apart)
        time_offset = sum(random.uniform(5.0, 60.0) for _ in range(i))
        timestamp = (base_time + timedelta(seconds=time_offset)).isoformat()
        
        # Usually same username, few password attempts
        username = f"user{random.randint(1000, 9999)}"
        password_length = random.randint(8, 20)
        
        # Higher success rate for normal users
        success = random.random() < 0.7  # 70% success rate
        
        attempts.append({
            'timestamp': timestamp,
            'ip': ip,
            'user_agent': user_agent,
            'username': username,
            'password_length': password_length,
            'success': success,
            'response_time': random.uniform(0.1, 0.5),
            'path': '/login',
            'method': 'POST'
        })
    
    return attempts

def extract_features_from_sequence(attempts):
    """Extract features from a sequence of login attempts"""
    if not attempts:
        return None
    
    # Time-based features
    timestamps = [datetime.fromisoformat(a['timestamp']) for a in attempts]
    time_diffs = [(timestamps[i+1] - timestamps[i]).total_seconds() 
                  for i in range(len(timestamps)-1)]
    
    # Calculate features
    features = {
        'num_attempts': len(attempts),
        'avg_time_between_attempts': sum(time_diffs) / len(time_diffs) if time_diffs else 0,
        'min_time_between_attempts': min(time_diffs) if time_diffs else 0,
        'max_time_between_attempts': max(time_diffs) if time_diffs else 0,
        'unique_usernames': len(set(a['username'] for a in attempts)),
        'success_rate': sum(1 for a in attempts if a['success']) / len(attempts),
        'avg_response_time': sum(a['response_time'] for a in attempts) / len(attempts),
        'has_brute_force_ua': 1 if any(ua in attempts[0]['user_agent'] 
                                       for ua in ['Hydra', 'Medusa', 'Ncrack', 'THC']) else 0,
        'attempts_per_minute': len(attempts) / ((timestamps[-1] - timestamps[0]).total_seconds() / 60) if len(timestamps) > 1 else 0,
        'password_length_variance': sum((a['password_length'] - 8) ** 2 for a in attempts) / len(attempts),
    }
    
    return features

def generate_dataset(num_samples=10000):
    """Generate brute force detection dataset"""
    dataset = []
    
    # Generate malicious samples (50%)
    num_malicious = num_samples // 2
    print(f"Generating {num_malicious} brute force attack samples...")
    
    for i in range(num_malicious):
        # Generate attack sequence
        num_attempts = random.randint(20, 100)
        sequence = generate_brute_force_sequence(num_attempts)
        features = extract_features_from_sequence(sequence)
        
        if features:
            features['label'] = 1  # Malicious
            features['type'] = 'brute_force'
            dataset.append(features)
        
        if (i + 1) % 1000 == 0:
            print(f"  Generated {i + 1}/{num_malicious} malicious samples")
    
    # Generate benign samples (50%)
    num_benign = num_samples - num_malicious
    print(f"Generating {num_benign} normal login samples...")
    
    for i in range(num_benign):
        # Generate normal sequence
        num_attempts = random.randint(1, 10)
        sequence = generate_normal_login_sequence(num_attempts)
        features = extract_features_from_sequence(sequence)
        
        if features:
            features['label'] = 0  # Benign
            features['type'] = 'normal'
            dataset.append(features)
        
        if (i + 1) % 1000 == 0:
            print(f"  Generated {i + 1}/{num_benign} benign samples")
    
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
    print(f"Malicious: {sum(1 for d in dataset if d['label'] == 1)}")
    print(f"Benign: {sum(1 for d in dataset if d['label'] == 0)}")

if __name__ == '__main__':
    # Generate dataset
    dataset = generate_dataset(num_samples=10000)
    
    # Save to file
    output_path = Path(__file__).parent.parent / 'data' / 'brute_force_dataset.json'
    save_dataset(dataset, output_path)
    
    # Print sample
    print("\nSample malicious:")
    malicious = [d for d in dataset if d['label'] == 1][:2]
    for sample in malicious:
        print(f"  Attempts: {sample['num_attempts']}, Rate: {sample['attempts_per_minute']:.2f}/min")
    
    print("\nSample benign:")
    benign = [d for d in dataset if d['label'] == 0][:2]
    for sample in benign:
        print(f"  Attempts: {sample['num_attempts']}, Rate: {sample['attempts_per_minute']:.2f}/min")
