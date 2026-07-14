#!/usr/bin/env python3
"""
Credential Stuffing Dataset Generator
Generates synthetic credential stuffing attack patterns for training
"""

import random
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Leaked credential patterns (simulated)
LEAKED_USERNAMES = [
    'john.doe@gmail.com', 'jane.smith@yahoo.com', 'mike.jones@hotmail.com',
    'sarah.wilson@outlook.com', 'david.brown@gmail.com', 'mary.johnson@yahoo.com',
    'robert.davis@gmail.com', 'linda.miller@hotmail.com', 'james.garcia@gmail.com',
    'patricia.rodriguez@yahoo.com', 'michael.martinez@gmail.com', 'jennifer.hernandez@hotmail.com'
]

# User agents that rotate (credential stuffing characteristic)
STUFFING_USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X)',
]

NORMAL_USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/537.36',
]

def generate_ip_pool(size=10):
    """Generate a pool of IPs for rotation"""
    return [f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}" 
            for _ in range(size)]

def generate_credential_stuffing_sequence(num_attempts=100):
    """Generate credential stuffing attack sequence"""
    # Rotate IPs and user agents
    ip_pool = generate_ip_pool(random.randint(5, 20))
    base_time = datetime.now()
    
    attempts = []
    for i in range(num_attempts):
        # Very rapid attempts (0.1 to 1 second apart)
        time_offset = sum(random.uniform(0.1, 1.0) for _ in range(i))
        timestamp = (base_time + timedelta(seconds=time_offset)).isoformat()
        
        # Rotate IP and user agent
        ip = random.choice(ip_pool)
        user_agent = random.choice(STUFFING_USER_AGENTS)
        
        # Use leaked credentials
        username = random.choice(LEAKED_USERNAMES)
        password_length = random.randint(8, 16)
        
        # Low success rate (most credentials don't work)
        success = random.random() < 0.05  # 5% success rate
        
        attempts.append({
            'timestamp': timestamp,
            'ip': ip,
            'user_agent': user_agent,
            'username': username,
            'password_length': password_length,
            'success': success,
            'response_time': random.uniform(0.05, 0.15),
            'path': '/login',
            'method': 'POST'
        })
    
    return attempts

def generate_normal_login_sequence(num_attempts=10):
    """Generate normal login behavior"""
    # Usually same IP
    ip = f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}"
    user_agent = random.choice(NORMAL_USER_AGENTS)
    base_time = datetime.now()
    
    # Usually same username
    username = f"user{random.randint(1000, 9999)}@example.com"
    
    attempts = []
    for i in range(num_attempts):
        # Slower attempts (10 to 120 seconds apart)
        time_offset = sum(random.uniform(10.0, 120.0) for _ in range(i))
        timestamp = (base_time + timedelta(seconds=time_offset)).isoformat()
        
        password_length = random.randint(8, 20)
        
        # Higher success rate for normal users
        success = random.random() < 0.6  # 60% success rate
        
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
    """Extract features from login attempt sequence"""
    if not attempts:
        return None
    
    # Time-based features
    timestamps = [datetime.fromisoformat(a['timestamp']) for a in attempts]
    time_diffs = [(timestamps[i+1] - timestamps[i]).total_seconds() 
                  for i in range(len(timestamps)-1)]
    
    # IP and UA rotation
    unique_ips = len(set(a['ip'] for a in attempts))
    unique_uas = len(set(a['user_agent'] for a in attempts))
    unique_usernames = len(set(a['username'] for a in attempts))
    
    # Calculate features
    features = {
        'num_attempts': len(attempts),
        'avg_time_between_attempts': sum(time_diffs) / len(time_diffs) if time_diffs else 0,
        'min_time_between_attempts': min(time_diffs) if time_diffs else 0,
        'attempts_per_minute': len(attempts) / ((timestamps[-1] - timestamps[0]).total_seconds() / 60) if len(timestamps) > 1 else 0,
        'unique_ips': unique_ips,
        'unique_user_agents': unique_uas,
        'unique_usernames': unique_usernames,
        'ip_rotation_rate': unique_ips / len(attempts),
        'ua_rotation_rate': unique_uas / len(attempts),
        'username_rotation_rate': unique_usernames / len(attempts),
        'success_rate': sum(1 for a in attempts if a['success']) / len(attempts),
        'avg_response_time': sum(a['response_time'] for a in attempts) / len(attempts),
    }
    
    return features

def generate_dataset(num_samples=10000):
    """Generate credential stuffing detection dataset"""
    dataset = []
    
    # Generate malicious samples (50%)
    num_malicious = num_samples // 2
    print(f"Generating {num_malicious} credential stuffing samples...")
    
    for i in range(num_malicious):
        # Generate attack sequence
        num_attempts = random.randint(50, 200)
        sequence = generate_credential_stuffing_sequence(num_attempts)
        features = extract_features_from_sequence(sequence)
        
        if features:
            features['label'] = 1  # Malicious
            features['type'] = 'credential_stuffing'
            dataset.append(features)
        
        if (i + 1) % 1000 == 0:
            print(f"  Generated {i + 1}/{num_malicious} malicious samples")
    
    # Generate benign samples (50%)
    num_benign = num_samples - num_malicious
    print(f"Generating {num_benign} normal login samples...")
    
    for i in range(num_benign):
        # Generate normal sequence
        num_attempts = random.randint(1, 15)
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
    output_path = Path(__file__).parent.parent / 'data' / 'credential_stuffing_dataset.json'
    save_dataset(dataset, output_path)
    
    # Print sample
    print("\nSample malicious:")
    malicious = [d for d in dataset if d['label'] == 1][:2]
    for sample in malicious:
        print(f"  Attempts: {sample['num_attempts']}, IPs: {sample['unique_ips']}, Rate: {sample['attempts_per_minute']:.2f}/min")
    
    print("\nSample benign:")
    benign = [d for d in dataset if d['label'] == 0][:2]
    for sample in benign:
        print(f"  Attempts: {sample['num_attempts']}, IPs: {sample['unique_ips']}, Rate: {sample['attempts_per_minute']:.2f}/min")
