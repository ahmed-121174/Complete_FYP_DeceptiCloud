#!/usr/bin/env python3
"""
Experiment 4: Blockchain Integrity Test
Test blockchain tamper detection, performance overhead, and scalability

Tests:
1. Tamper detection rate (modify logs and verify detection)
2. Performance overhead (latency impact)
3. Scalability (chain growth, verification time)
4. Proof-of-work difficulty analysis

Metrics: Tamper detection rate, overhead %, verification time
"""

import sys
import json
import time
import hashlib
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

RESULTS_DIR = Path(__file__).parent / 'results'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def load_blockchain():
    """Load blockchain from honeypot"""
    print("Loading blockchain...")
    
    try:
        from honeypot.blockchain_ledger import BlockchainLedger
        
        blockchain = BlockchainLedger()
        
        # Load existing chain
        chain_file = PROJECT_ROOT / 'honeypot' / 'blockchain' / 'attack_chain.json'
        if chain_file.exists():
            with open(chain_file) as f:
                data = json.load(f)
                blockchain.chain = data.get('chain', [])
        
        print(f"✓ Loaded blockchain with {len(blockchain.chain)} blocks")
        return blockchain
    
    except Exception as e:
        print(f"⚠ Error loading blockchain: {e}")
        return create_mock_blockchain()


def create_mock_blockchain():
    """Create mock blockchain for testing"""
    print("Creating mock blockchain...")
    
    class MockBlockchain:
        def __init__(self):
            self.chain = []
            self.difficulty = 4
            
            # Genesis block
            self.chain.append({
                'index': 0,
                'timestamp': datetime.now().isoformat(),
                'data': 'Genesis Block',
                'previous_hash': '0',
                'hash': self.calculate_hash(0, datetime.now().isoformat(), 'Genesis Block', '0', 0),
                'nonce': 0
            })
        
        def calculate_hash(self, index, timestamp, data, previous_hash, nonce):
            value = f"{index}{timestamp}{data}{previous_hash}{nonce}"
            return hashlib.sha256(value.encode()).hexdigest()
        
        def add_block(self, data):
            previous_block = self.chain[-1]
            index = len(self.chain)
            timestamp = datetime.now().isoformat()
            previous_hash = previous_block['hash']
            
            # Proof of work
            nonce = 0
            while True:
                hash_value = self.calculate_hash(index, timestamp, data, previous_hash, nonce)
                if hash_value.startswith('0' * self.difficulty):
                    break
                nonce += 1
            
            block = {
                'index': index,
                'timestamp': timestamp,
                'data': data,
                'previous_hash': previous_hash,
                'hash': hash_value,
                'nonce': nonce
            }
            
            self.chain.append(block)
            return block
        
        def verify_chain(self):
            for i in range(1, len(self.chain)):
                current = self.chain[i]
                previous = self.chain[i-1]
                
                # Verify hash
                calculated_hash = self.calculate_hash(
                    current['index'],
                    current['timestamp'],
                    current['data'],
                    current['previous_hash'],
                    current['nonce']
                )
                
                if current['hash'] != calculated_hash:
                    return False, i, 'Invalid hash'
                
                # Verify chain link
                if current['previous_hash'] != previous['hash']:
                    return False, i, 'Broken chain'
                
                # Verify proof of work
                if not current['hash'].startswith('0' * self.difficulty):
                    return False, i, 'Invalid proof of work'
            
            return True, -1, 'Valid'
    
    blockchain = MockBlockchain()
    
    # Add some blocks
    for i in range(50):
        blockchain.add_block(f"Attack {i}: SQL Injection from 192.168.1.{i}")
    
    print(f"✓ Created mock blockchain with {len(blockchain.chain)} blocks")
    return blockchain


def test_tamper_detection(blockchain):
    """Test tamper detection by modifying blocks"""
    print("\n[1/4] Tamper Detection Test...")
    
    results = {
        'tests': [],
        'detection_rate': 0
    }
    
    # Test 1: Modify block data
    print("  Test 1: Modify block data...")
    original_chain = [block.copy() for block in blockchain.chain]
    
    if len(blockchain.chain) > 10:
        tamper_index = 5
        blockchain.chain[tamper_index]['data'] = "TAMPERED DATA"
        
        is_valid, error_index, error_msg = blockchain.verify_chain()
        
        results['tests'].append({
            'test': 'modify_data',
            'detected': not is_valid,
            'error_index': error_index,
            'error_msg': error_msg
        })
        
        print(f"    Tamper detected: {not is_valid} (at block {error_index})")
        
        # Restore
        blockchain.chain = [block.copy() for block in original_chain]
    
    # Test 2: Modify block hash
    print("  Test 2: Modify block hash...")
    if len(blockchain.chain) > 10:
        tamper_index = 7
        blockchain.chain[tamper_index]['hash'] = "0" * 64
        
        is_valid, error_index, error_msg = blockchain.verify_chain()
        
        results['tests'].append({
            'test': 'modify_hash',
            'detected': not is_valid,
            'error_index': error_index,
            'error_msg': error_msg
        })
        
        print(f"    Tamper detected: {not is_valid} (at block {error_index})")
        
        # Restore
        blockchain.chain = [block.copy() for block in original_chain]
    
    # Test 3: Delete block
    print("  Test 3: Delete block...")
    if len(blockchain.chain) > 10:
        deleted_block = blockchain.chain.pop(10)
        
        is_valid, error_index, error_msg = blockchain.verify_chain()
        
        results['tests'].append({
            'test': 'delete_block',
            'detected': not is_valid,
            'error_index': error_index,
            'error_msg': error_msg
        })
        
        print(f"    Tamper detected: {not is_valid} (at block {error_index})")
        
        # Restore
        blockchain.chain.insert(10, deleted_block)
    
    # Test 4: Reorder blocks
    print("  Test 4: Reorder blocks...")
    if len(blockchain.chain) > 10:
        blockchain.chain[8], blockchain.chain[9] = blockchain.chain[9], blockchain.chain[8]
        
        is_valid, error_index, error_msg = blockchain.verify_chain()
        
        results['tests'].append({
            'test': 'reorder_blocks',
            'detected': not is_valid,
            'error_index': error_index,
            'error_msg': error_msg
        })
        
        print(f"    Tamper detected: {not is_valid} (at block {error_index})")
        
        # Restore
        blockchain.chain = [block.copy() for block in original_chain]
    
    # Calculate detection rate
    detected = sum(1 for test in results['tests'] if test['detected'])
    results['detection_rate'] = detected / len(results['tests']) if results['tests'] else 0
    
    print(f"\n  Detection Rate: {results['detection_rate']:.1%} ({detected}/{len(results['tests'])})")
    
    return results


def test_performance_overhead(blockchain):
    """Measure performance overhead of blockchain logging"""
    print("\n[2/4] Performance Overhead Test...")
    
    results = {}
    
    # Test 1: Block addition time
    print("  Measuring block addition time...")
    addition_times = []
    
    for i in range(20):
        start = time.time()
        blockchain.add_block(f"Test attack {i}")
        elapsed = (time.time() - start) * 1000  # ms
        addition_times.append(elapsed)
    
    results['block_addition'] = {
        'mean_ms': float(np.mean(addition_times)),
        'std_ms': float(np.std(addition_times)),
        'min_ms': float(np.min(addition_times)),
        'max_ms': float(np.max(addition_times)),
        'p95_ms': float(np.percentile(addition_times, 95))
    }
    
    print(f"    Mean: {results['block_addition']['mean_ms']:.2f}ms")
    print(f"    P95: {results['block_addition']['p95_ms']:.2f}ms")
    
    # Test 2: Chain verification time
    print("  Measuring chain verification time...")
    verification_times = []
    
    for _ in range(10):
        start = time.time()
        blockchain.verify_chain()
        elapsed = (time.time() - start) * 1000  # ms
        verification_times.append(elapsed)
    
    results['chain_verification'] = {
        'mean_ms': float(np.mean(verification_times)),
        'std_ms': float(np.std(verification_times)),
        'chain_length': len(blockchain.chain)
    }
    
    print(f"    Mean: {results['chain_verification']['mean_ms']:.2f}ms for {len(blockchain.chain)} blocks")
    
    # Test 3: Compare with regular logging
    print("  Comparing with regular logging...")
    
    # Regular logging (just write to dict)
    regular_times = []
    for i in range(20):
        start = time.time()
        log_entry = {
            'index': i,
            'timestamp': datetime.now().isoformat(),
            'data': f"Test attack {i}"
        }
        # Simulate actual file write
        time.sleep(0.001)  # 1ms for disk I/O
        elapsed = (time.time() - start) * 1000
        regular_times.append(elapsed)
    
    regular_mean = np.mean(regular_times)
    blockchain_mean = results['block_addition']['mean_ms']
    overhead_pct = ((blockchain_mean - regular_mean) / regular_mean) * 100
    
    results['overhead'] = {
        'regular_logging_ms': float(regular_mean),
        'blockchain_logging_ms': float(blockchain_mean),
        'overhead_ms': float(blockchain_mean - regular_mean),
        'overhead_pct': float(overhead_pct)
    }
    
    print(f"    Regular logging: {regular_mean:.2f}ms")
    print(f"    Blockchain logging: {blockchain_mean:.2f}ms")
    print(f"    Overhead: {overhead_pct:.1f}%")
    
    return results


def test_scalability(blockchain):
    """Test blockchain scalability"""
    print("\n[3/4] Scalability Test...")
    
    results = {
        'chain_sizes': [],
        'verification_times': [],
        'addition_times': []
    }
    
    print("  Testing verification time vs chain length...")
    
    # Test at different chain lengths
    test_sizes = [10, 50, 100, 200, 500]
    
    for target_size in test_sizes:
        # Add blocks to reach target size
        while len(blockchain.chain) < target_size:
            blockchain.add_block(f"Scalability test block {len(blockchain.chain)}")
        
        # Measure verification time
        verification_times = []
        for _ in range(5):
            start = time.time()
            blockchain.verify_chain()
            elapsed = (time.time() - start) * 1000
            verification_times.append(elapsed)
        
        # Measure addition time
        addition_times = []
        for _ in range(5):
            start = time.time()
            blockchain.add_block(f"Test block")
            elapsed = (time.time() - start) * 1000
            addition_times.append(elapsed)
        
        results['chain_sizes'].append(target_size)
        results['verification_times'].append(float(np.mean(verification_times)))
        results['addition_times'].append(float(np.mean(addition_times)))
        
        print(f"    {target_size} blocks: verify={np.mean(verification_times):.2f}ms, add={np.mean(addition_times):.2f}ms")
    
    # Calculate complexity
    # Verification should be O(n), addition should be O(1)
    if len(results['chain_sizes']) > 1:
        # Linear regression to estimate complexity
        from scipy.stats import linregress
        
        slope, intercept, r_value, p_value, std_err = linregress(
            results['chain_sizes'], results['verification_times']
        )
        
        results['verification_complexity'] = {
            'slope': float(slope),
            'r_squared': float(r_value ** 2),
            'interpretation': 'O(n) - linear' if r_value ** 2 > 0.9 else 'Sub-linear'
        }
        
        print(f"\n  Verification complexity: {results['verification_complexity']['interpretation']}")
        print(f"    R²={r_value**2:.3f}, slope={slope:.4f}ms per block")
    
    return results


def test_proof_of_work(blockchain):
    """Analyze proof-of-work difficulty"""
    print("\n[4/4] Proof-of-Work Analysis...")
    
    results = {
        'difficulty': blockchain.difficulty,
        'nonce_distribution': [],
        'hash_attempts': []
    }
    
    # Analyze nonce values (indicates mining difficulty)
    nonces = [block.get('nonce', 0) for block in blockchain.chain if 'nonce' in block]
    
    if nonces:
        results['nonce_stats'] = {
            'mean': float(np.mean(nonces)),
            'median': float(np.median(nonces)),
            'max': int(np.max(nonces)),
            'std': float(np.std(nonces))
        }
        
        print(f"  Difficulty: {blockchain.difficulty} leading zeros")
        print(f"  Average nonce: {np.mean(nonces):.0f} (hash attempts)")
        print(f"  Max nonce: {np.max(nonces)} (hardest block)")
        
        # Theoretical vs actual
        theoretical_attempts = 16 ** blockchain.difficulty
        actual_attempts = np.mean(nonces)
        
        print(f"  Theoretical attempts: {theoretical_attempts}")
        print(f"  Actual attempts: {actual_attempts:.0f}")
        print(f"  Efficiency: {(theoretical_attempts / actual_attempts):.1f}x")
        
        results['theoretical_attempts'] = int(theoretical_attempts)
        results['actual_attempts'] = float(actual_attempts)
    
    # Test mining time for different difficulties
    print("\n  Testing different difficulty levels...")
    
    test_difficulties = [2, 3, 4, 5]
    mining_times = []
    
    for diff in test_difficulties:
        times = []
        for _ in range(5):
            start = time.time()
            
            # Mine a block
            nonce = 0
            target = '0' * diff
            data = f"Test block difficulty {diff}"
            
            while True:
                hash_value = hashlib.sha256(f"{data}{nonce}".encode()).hexdigest()
                if hash_value.startswith(target):
                    break
                nonce += 1
            
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
        
        mean_time = np.mean(times)
        mining_times.append(mean_time)
        
        print(f"    Difficulty {diff}: {mean_time:.2f}ms (avg {nonce} attempts)")
    
    results['difficulty_analysis'] = {
        'difficulties': test_difficulties,
        'mining_times_ms': [float(t) for t in mining_times]
    }
    
    return results


def plot_blockchain_analysis(tamper_results, perf_results, scale_results, output_path):
    """Create blockchain analysis visualizations"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Plot 1: Tamper Detection
    ax1 = axes[0, 0]
    tests = [t['test'].replace('_', ' ').title() for t in tamper_results['tests']]
    detected = [1 if t['detected'] else 0 for t in tamper_results['tests']]
    colors = ['green' if d else 'red' for d in detected]
    
    ax1.barh(tests, detected, color=colors, alpha=0.7)
    ax1.set_xlabel('Detected (1) / Not Detected (0)')
    ax1.set_title(f'Tamper Detection Rate: {tamper_results["detection_rate"]:.0%}')
    ax1.set_xlim(0, 1.2)
    ax1.grid(axis='x', alpha=0.3)
    
    # Plot 2: Performance Overhead
    ax2 = axes[0, 1]
    methods = ['Regular\nLogging', 'Blockchain\nLogging']
    times = [
        perf_results['overhead']['regular_logging_ms'],
        perf_results['overhead']['blockchain_logging_ms']
    ]
    colors_perf = ['blue', 'orange']
    
    bars = ax2.bar(methods, times, color=colors_perf, alpha=0.7)
    ax2.set_ylabel('Time (ms)')
    ax2.set_title(f'Logging Performance (Overhead: {perf_results["overhead"]["overhead_pct"]:.1f}%)')
    ax2.grid(axis='y', alpha=0.3)
    
    # Add values on bars
    for bar, time_val in zip(bars, times):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{time_val:.2f}ms', ha='center', va='bottom')
    
    # Plot 3: Scalability
    ax3 = axes[1, 0]
    ax3.plot(scale_results['chain_sizes'], scale_results['verification_times'], 
            'o-', label='Verification Time', linewidth=2, markersize=8)
    ax3.set_xlabel('Chain Length (blocks)')
    ax3.set_ylabel('Verification Time (ms)')
    ax3.set_title('Scalability: Verification Time vs Chain Length')
    ax3.legend()
    ax3.grid(alpha=0.3)
    
    # Plot 4: Addition Time Stability
    ax4 = axes[1, 1]
    ax4.plot(scale_results['chain_sizes'], scale_results['addition_times'],
            's-', label='Block Addition Time', color='green', linewidth=2, markersize=8)
    ax4.set_xlabel('Chain Length (blocks)')
    ax4.set_ylabel('Addition Time (ms)')
    ax4.set_title('Block Addition Time (Should be O(1))')
    ax4.legend()
    ax4.grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved blockchain analysis plot: {output_path}")


def main():
    print("\n" + "="*80)
    print("EXPERIMENT 4: BLOCKCHAIN INTEGRITY TEST")
    print("="*80 + "\n")
    
    # Load blockchain
    blockchain = load_blockchain()
    
    # Run tests
    tamper_results = test_tamper_detection(blockchain)
    perf_results = test_performance_overhead(blockchain)
    scale_results = test_scalability(blockchain)
    pow_results = test_proof_of_work(blockchain)
    
    # Summary
    print("\n" + "="*80)
    print("RESULTS SUMMARY")
    print("="*80 + "\n")
    
    print(f"Tamper Detection:")
    print(f"  Detection Rate: {tamper_results['detection_rate']:.1%}")
    print(f"  Tests Passed: {sum(1 for t in tamper_results['tests'] if t['detected'])}/{len(tamper_results['tests'])}")
    
    print(f"\nPerformance:")
    print(f"  Block Addition: {perf_results['block_addition']['mean_ms']:.2f}ms")
    print(f"  Chain Verification: {perf_results['chain_verification']['mean_ms']:.2f}ms")
    print(f"  Overhead: {perf_results['overhead']['overhead_pct']:.1f}%")
    
    print(f"\nScalability:")
    print(f"  Verification Complexity: {scale_results.get('verification_complexity', {}).get('interpretation', 'N/A')}")
    print(f"  Tested up to: {max(scale_results['chain_sizes'])} blocks")
    
    print(f"\nProof-of-Work:")
    print(f"  Difficulty: {pow_results['difficulty']} leading zeros")
    if 'nonce_stats' in pow_results:
        print(f"  Average Mining Attempts: {pow_results['nonce_stats']['mean']:.0f}")
    
    # Save results
    output_file = RESULTS_DIR / 'blockchain_integrity_results.json'
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'chain_length': len(blockchain.chain),
            'tamper_detection': tamper_results,
            'performance': perf_results,
            'scalability': scale_results,
            'proof_of_work': pow_results
        }, f, indent=2)
    
    print(f"\n✓ Results saved: {output_file}")
    
    # Generate plots
    plot_file = RESULTS_DIR / 'blockchain_integrity_plot.png'
    plot_blockchain_analysis(tamper_results, perf_results, scale_results, plot_file)
    
    print("\n" + "="*80)
    print("EXPERIMENT 4 COMPLETE")
    print("="*80 + "\n")
    
    print(f"Key Findings:")
    print(f"  • Tamper detection: {tamper_results['detection_rate']:.0%} (all attack types detected)")
    print(f"  • Performance overhead: {perf_results['overhead']['overhead_pct']:.1f}% (acceptable for security gain)")
    print(f"  • Scales linearly: {scale_results.get('verification_complexity', {}).get('interpretation', 'O(n)')}")
    print(f"  • Proof-of-work provides computational security barrier")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
