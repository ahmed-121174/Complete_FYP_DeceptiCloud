#!/usr/bin/env python3
"""
Master Experiment Runner for Journal Paper
Runs all experiments sequentially and collects results
"""

import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

BASE_DIR = Path(__file__).parent
RESULTS_DIR = BASE_DIR / 'results'
RESULTS_DIR.mkdir(exist_ok=True)

EXPERIMENTS = [
    {
        'id': '01',
        'name': 'Baseline Comparison',
        'script': '01_baseline_comparison/run.py',
        'duration': '4 hours',
        'critical': True
    },
    {
        'id': '02',
        'name': 'Ablation Study',
        'script': '02_ablation_study/run.py',
        'duration': '6 hours',
        'critical': True
    },
    {
        'id': '03',
        'name': 'GAN Realism Test',
        'script': '03_gan_realism_test/run.py',
        'duration': '2 hours',
        'critical': True
    },
    {
        'id': '04',
        'name': 'Blockchain Integrity',
        'script': '04_blockchain_integrity/run.py',
        'duration': '1 hour',
        'critical': True
    },
    {
        'id': '05',
        'name': 'Zero-Day Detection',
        'script': '05_zero_day_detection/run.py',
        'duration': '3 hours',
        'critical': True
    },
    {
        'id': '06',
        'name': 'Adversarial Evasion',
        'script': '06_adversarial_evasion/run.py',
        'duration': '8 hours',
        'critical': False
    },
    {
        'id': '07',
        'name': 'Long-Term Deployment',
        'script': '07_long_term_deployment/run.py',
        'duration': '30 days (background)',
        'critical': False
    },
    {
        'id': '08',
        'name': 'Scalability Test',
        'script': '08_scalability_test/run.py',
        'duration': '4 hours',
        'critical': True
    },
    {
        'id': '10',
        'name': 'Cost-Benefit Analysis',
        'script': '10_cost_benefit_analysis/run.py',
        'duration': '1 hour',
        'critical': False
    },
]


def print_banner():
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}{Style.BRIGHT}DeceptiCloud Journal Experiments")
    print(f"{Fore.CYAN}Comprehensive Evaluation for Research Paper")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")


def print_experiment_header(exp):
    print(f"\n{Fore.YELLOW}{'─'*80}")
    print(f"{Fore.YELLOW}{Style.BRIGHT}[{exp['id']}] {exp['name']}")
    print(f"{Fore.YELLOW}Expected Duration: {exp['duration']}")
    print(f"{Fore.YELLOW}Critical: {'Yes' if exp['critical'] else 'No'}")
    print(f"{Fore.YELLOW}{'─'*80}{Style.RESET_ALL}\n")


def run_experiment(exp):
    """Run a single experiment and capture results"""
    script_path = BASE_DIR / exp['script']
    
    if not script_path.exists():
        print(f"{Fore.RED}✗ Script not found: {script_path}{Style.RESET_ALL}")
        return {'status': 'skipped', 'reason': 'script_not_found'}
    
    print(f"{Fore.CYAN}▶ Starting experiment...{Style.RESET_ALL}")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=36000  # 10 hour timeout
        )
        
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            print(f"{Fore.GREEN}✓ Completed in {elapsed/60:.1f} minutes{Style.RESET_ALL}")
            return {
                'status': 'success',
                'elapsed_seconds': elapsed,
                'stdout': result.stdout[-1000:],  # Last 1000 chars
                'stderr': result.stderr[-1000:] if result.stderr else ''
            }
        else:
            print(f"{Fore.RED}✗ Failed with exit code {result.returncode}{Style.RESET_ALL}")
            print(f"{Fore.RED}Error: {result.stderr[:500]}{Style.RESET_ALL}")
            return {
                'status': 'failed',
                'exit_code': result.returncode,
                'elapsed_seconds': elapsed,
                'error': result.stderr[:1000]
            }
    
    except subprocess.TimeoutExpired:
        print(f"{Fore.RED}✗ Timeout after 10 hours{Style.RESET_ALL}")
        return {'status': 'timeout'}
    
    except Exception as e:
        print(f"{Fore.RED}✗ Exception: {e}{Style.RESET_ALL}")
        return {'status': 'error', 'exception': str(e)}


def main():
    print_banner()
    
    # Check if system is running
    print(f"{Fore.CYAN}Checking DeceptiCloud system status...{Style.RESET_ALL}")
    system_running = False
    try:
        import requests
        resp = requests.get('http://localhost:8080/proxy/status', timeout=5)
        if resp.status_code == 200:
            print(f"{Fore.GREEN}✓ System is running{Style.RESET_ALL}")
            system_running = True
        else:
            print(f"{Fore.YELLOW}⚠ System may not be fully operational{Style.RESET_ALL}")
    except:
        print(f"{Fore.YELLOW}⚠ System not running - experiments will use simulated data{Style.RESET_ALL}")
        print(f"{Fore.CYAN}  (This is normal - most experiments work without live system){Style.RESET_ALL}")
    
    # Run experiments
    results = {
        'start_time': datetime.now().isoformat(),
        'experiments': {}
    }
    
    total_experiments = len(EXPERIMENTS)
    completed = 0
    failed = 0
    skipped = 0
    
    for i, exp in enumerate(EXPERIMENTS, 1):
        print_experiment_header(exp)
        print(f"{Fore.CYAN}Progress: {i}/{total_experiments}{Style.RESET_ALL}")
        
        exp_result = run_experiment(exp)
        results['experiments'][exp['id']] = {
            'name': exp['name'],
            'result': exp_result,
            'timestamp': datetime.now().isoformat()
        }
        
        if exp_result['status'] == 'success':
            completed += 1
        elif exp_result['status'] == 'skipped':
            skipped += 1
        else:
            failed += 1
            if exp['critical']:
                print(f"\n{Fore.RED}⚠ Critical experiment failed!{Style.RESET_ALL}")
                response = input(f"{Fore.YELLOW}Continue with remaining experiments? (y/n): {Style.RESET_ALL}")
                if response.lower() != 'y':
                    break
    
    results['end_time'] = datetime.now().isoformat()
    results['summary'] = {
        'total': total_experiments,
        'completed': completed,
        'failed': failed,
        'skipped': skipped
    }
    
    # Save results
    results_file = RESULTS_DIR / f'experiment_run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}{Style.BRIGHT}EXPERIMENT RUN COMPLETE")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
    
    print(f"{Fore.GREEN}✓ Completed: {completed}/{total_experiments}{Style.RESET_ALL}")
    if failed > 0:
        print(f"{Fore.RED}✗ Failed: {failed}/{total_experiments}{Style.RESET_ALL}")
    if skipped > 0:
        print(f"{Fore.YELLOW}⊘ Skipped: {skipped}/{total_experiments}{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}Results saved to: {results_file}{Style.RESET_ALL}")
    print(f"\n{Fore.YELLOW}Next step: Generate final report")
    print(f"{Fore.YELLOW}  python3 experiments/journal_experiments/generate_final_report.py{Style.RESET_ALL}\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Experiment run interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
