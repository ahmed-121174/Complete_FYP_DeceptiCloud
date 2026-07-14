#!/usr/bin/env python3
"""
Quick Test Script - Verify all experiments can start
Tests each experiment for 10 seconds to catch import/syntax errors
"""

import sys
import subprocess
import time
from pathlib import Path
from colorama import Fore, Style, init

init(autoreset=True)

BASE_DIR = Path(__file__).parent

EXPERIMENTS = [
    ('01_baseline_comparison', 'Baseline Comparison'),
    ('02_ablation_study', 'Ablation Study'),
    ('03_gan_realism_test', 'GAN Realism Test'),
    ('04_blockchain_integrity', 'Blockchain Integrity'),
    ('05_zero_day_detection', 'Zero-Day Detection'),
    ('06_adversarial_evasion', 'Adversarial Evasion'),
    ('07_long_term_deployment', 'Long-Term Deployment'),
    ('08_scalability_test', 'Scalability Test'),
    ('10_cost_benefit_analysis', 'Cost-Benefit Analysis'),
]


def test_experiment(exp_id, exp_name):
    """Test if experiment can start without errors"""
    script_path = BASE_DIR / exp_id / 'run.py'
    
    if not script_path.exists():
        return False, 'Script not found'
    
    print(f"\n{Fore.CYAN}Testing: {exp_name}...{Style.RESET_ALL}", end=' ')
    
    try:
        # Run for 10 seconds to catch startup errors
        process = subprocess.Popen(
            [sys.executable, str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(BASE_DIR)
        )
        
        # Wait 10 seconds
        time.sleep(10)
        
        # Check if still running or completed successfully
        if process.poll() is None:
            # Still running - kill it
            process.terminate()
            process.wait(timeout=5)
            print(f"{Fore.GREEN}✓ Started successfully{Style.RESET_ALL}")
            return True, 'Running'
        elif process.poll() == 0:
            # Completed successfully
            print(f"{Fore.GREEN}✓ Completed successfully{Style.RESET_ALL}")
            return True, 'Completed'
        else:
            # Failed
            stderr = process.stderr.read().decode()
            print(f"{Fore.RED}✗ Failed{Style.RESET_ALL}")
            return False, stderr[:200]
    
    except Exception as e:
        print(f"{Fore.RED}✗ Error{Style.RESET_ALL}")
        return False, str(e)


def main():
    print("\n" + "="*80)
    print(f"{Fore.CYAN}{Style.BRIGHT}EXPERIMENT QUICK TEST")
    print("="*80 + Style.RESET_ALL)
    print("\nTesting each experiment for 10 seconds to verify they can start...\n")
    
    results = []
    
    for exp_id, exp_name in EXPERIMENTS:
        success, message = test_experiment(exp_id, exp_name)
        results.append((exp_name, success, message))
    
    # Summary
    print("\n" + "="*80)
    print(f"{Fore.CYAN}{Style.BRIGHT}TEST SUMMARY")
    print("="*80 + Style.RESET_ALL + "\n")
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for name, success, message in results:
        status = f"{Fore.GREEN}✓ PASS{Style.RESET_ALL}" if success else f"{Fore.RED}✗ FAIL{Style.RESET_ALL}"
        print(f"{status} - {name}")
        if not success:
            print(f"  Error: {message}")
    
    print(f"\n{Fore.CYAN}Results: {passed}/{total} experiments passed{Style.RESET_ALL}")
    
    if passed == total:
        print(f"\n{Fore.GREEN}{Style.BRIGHT}✓ ALL EXPERIMENTS READY TO RUN!{Style.RESET_ALL}")
        return 0
    else:
        print(f"\n{Fore.YELLOW}⚠ Some experiments need attention{Style.RESET_ALL}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
