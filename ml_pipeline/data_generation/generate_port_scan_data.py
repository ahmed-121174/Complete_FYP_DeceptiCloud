#!/usr/bin/env python3
"""
Port Scan Dataset Generator
Generates synthetic port scanning patterns for training
"""

import random
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Common ports
COMMON_PORTS = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 3306, 3389, 5432, 8080, 8443]
ALL_PORTS = list(range(1, 65536))

SCAN_USER_AGENTS = [
    'nmap', 'masscan', 'zmap', 'unicornscan', 'hping3',
    'python-nmap', 'Go-http-client', 'curl/7.68.0'
]

NORMAL_USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Chrome/91.0.4472.124', 'Safari/537.36'
]

def generate_ip():
    """Generate random IP address"""
    return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}"

def generate_sequential_scan(num_ports=50):
    """Generate sequential port scan pattern"""
    ip = generate_ip()
    user_agent = random.choice(SCAN_USER_AGENTS)
    base_time = datetime.now()
    
    # Pick starting port
    start_port = random.randint(1, 65000)
    
    accesses = []
    for i in range(num_ports):
        # Very rapid sequential access (0.01 to 0.1 seconds apart)
        time_offset = sum(random.uniform(0.01, 0.1) for _ in range(i))
        timestamp = (base_time + timedelta(seconds=time_offset)).isoformat()
        
        port = start_port + i
        if port > 65535:
            port = port - 65535
        
        accesses.append({
            'timestamp': timestamp,
            'ip': ip,
            'port': port,
            'user_agent': user_agent,
            'response_code': random.choice([200, 404, 403, 0]),  # 0 = no response
            'response_time': random.uniform(0.001, 0.05)
        })
    
    return accesses

def generate_random_scan(num_ports=50):
    """Generate random port scan pattern"""
    ip = generate_ip()
    user_agent = random.choice(SCAN_USER_AGENTS)
    base_time = datetime.now()
    
    # Random ports
    ports = random.sample(ALL_PORTS, min(num_ports, len(ALL_PORTS)))
    
    accesses = []
    for i, port in enumerate(ports):
        # Rapid random access (0.01 to 0.2 seconds apart)
        time_offset = sum(random.uniform(0.01, 0.2) for _ in range(i))
        timestamp = (base_time + timedelta(seconds=time_offset)).isoformat()
        
        accesses.append({
            'timestamp': timestamp,
            'ip': ip,
            'port': port,
            'user_agent': user_agent,
            'response_code': random.choice([200, 404, 403, 0]),
            'response_time': random.uniform(0.001, 0.05)
        })
    
    return accesses

def generate_normal_access(num_ports=5):
    """Generate normal port access pattern"""
    ip = generate_ip()
    user_agent = random.choice(NORMAL_USER_AGENTS)
    base_time = datetime.now()
    
    # Access only common ports
    ports = random.sample(COMMON_PORTS, min(num_ports, len(COMMON_PORTS)))
    
    accesses = []
    for i, port in enumerate(ports):
        # Slower access (1 to 30 seconds apart)
        time_offset = sum(random.uniform(1.0, 30.0) for _ in range(i))
        timestamp = (base_time + timedelta(seconds=time_offset)).isoformat()
        
        accesses.append({
            'timestamp': timestamp,
            'ip': ip,
            'port': port,
            'user_agent': user_agent,
            'response_code': random.choice([200, 301, 302, 404]),
            'response_time': random.uniform(0.05, 0.5)
        })
    
    return accesses

def extract_features_from_sequence(accesses):
    """Extract features from port access sequence"""
    if not accesses:
        return None
    
    # Time-based features
    timestamps = [datetime.fromisoformat(a['timestamp']) for a in accesses]
    time_diffs = [(timestamps[i+1] - timestamps[i]).total_seconds() 
                  for i in range(len(timestamps)-1)]
    
    # Port features
    ports = [a['port'] for a in accesses]
    port_diffs = [abs(ports[i+1] - ports[i]) for i in range(len(ports)-1)]
    
    # Calculate features
    features = {
        'num_ports_accessed': len(ports),
        'unique_ports': len(set(ports)),
        'avg_time_between_accesses': sum(time_diffs) / len(time_diffs) if time_diffs else 0,
        'min_time_between_accesses': min(time_diffs) if time_diffs else 0,
        'max_time_between_accesses': max(time_diffs) if time_diffs else 0,
        'avg_port_diff': sum(port_diffs) / len(port_diffs) if port_diffs else 0,
        'sequential_pattern': 1 if port_diffs and sum(1 for d in port_diffs if d == 1) / len(port_diffs) > 0.5 else 0,
        'ports_per_second': len(ports) / ((timestamps[-1] - timestamps[0]).total_seconds()) if len(timestamps) > 1 else 0,
        'has_scan_ua': 1 if any(ua in accesses[0]['user_agent'].lower() 
                                for ua in ['nmap', 'masscan', 'scan', 'zmap']) else 0,
        'avg_response_time': sum(a['response_time'] for a in accesses) / len(accesses),
        'common_ports_ratio': sum(1 for p in ports if p in COMMON_PORTS) / len(ports),
        'high_port_ratio': sum(1 for p in ports if p > 1024) / len(ports),
    }
    
    return features

def generate_dataset(num_samples=10000):
    """Generate port scan detection dataset"""
    dataset = []
    
    # Generate malicious samples (50%)
    num_malicious = num_samples // 2
    print(f"Generating {num_malicious} port scan samples...")
    
    for i in range(num_malicious):
        # Mix of sequential and random scans
        if random.random() < 0.6:
            # Sequential scan
            num_ports = random.randint(20, 100)
            sequence = generate_sequential_scan(num_ports)
        else:
            # Random scan
            num_ports = random.randint(20, 100)
            sequence = generate_random_scan(num_ports)
        
        features = extract_features_from_sequence(sequence)
        
        if features:
            features['label'] = 1  # Malicious
            features['type'] = 'port_scan'
            dataset.append(features)
        
        if (i + 1) % 1000 == 0:
            print(f"  Generated {i + 1}/{num_malicious} malicious samples")
    
    # Generate benign samples (50%)
    num_benign = num_samples - num_malicious
    print(f"Generating {num_benign} normal access samples...")
    
    for i in range(num_benign):
        # Normal access
        num_ports = random.randint(1, 10)
        sequence = generate_normal_access(num_ports)
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
    output_path = Path(__file__).parent.parent / 'data' / 'port_scan_dataset.json'
    save_dataset(dataset, output_path)
    
    # Print sample
    print("\nSample malicious:")
    malicious = [d for d in dataset if d['label'] == 1][:2]
    for sample in malicious:
        print(f"  Ports: {sample['num_ports_accessed']}, Rate: {sample['ports_per_second']:.2f}/sec, Sequential: {sample['sequential_pattern']}")
    
    print("\nSample benign:")
    benign = [d for d in dataset if d['label'] == 0][:2]
    for sample in benign:
        print(f"  Ports: {sample['num_ports_accessed']}, Rate: {sample['ports_per_second']:.2f}/sec, Common: {sample['common_ports_ratio']:.2f}")
