#!/usr/bin/env python3
"""
Quick Setup Verification - Check if all experiments are ready
"""

import sys
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


def main():
    print("\n" + "="*80)
    print(f"{Fore.CYAN}{Style.BRIGHT}DECEPTICLOUD JOURNAL EXPERIMENTS - SETUP VERIFICATION")
    print("="*80 + Style.RESET_ALL + "\n")
    
    # Check Python version
    print(f"Python Version: {sys.version.split()[0]}")
    
    # Check dependencies
    print("\nChecking Dependencies...")
    try:
        import numpy
        import pandas
        import matplotlib
        import seaborn
        import scipy
        import sklearn
        import colorama
        print(f"{Fore.GREEN}✓ All core dependencies installed{Style.RESET_ALL}")
    except ImportError as e:
        print(f"{Fore.RED}✗ Missing dependency: {e}{Style.RESET_ALL}")
        print(f"\nInstall with: pip install -r requirements.txt")
        return 1
    
    # Check experiment scripts
    print("\nChecking Experiment Scripts...")
    all_present = True
    
    for exp_id, exp_name in EXPERIMENTS:
        script_path = BASE_DIR / exp_id / 'run.py'
        results_dir = BASE_DIR / exp_id / 'results'
        
        if script_path.exists():
            print(f"{Fore.GREEN}✓{Style.RESET_ALL} {exp_name:<30} {exp_id}/run.py")
            # Create results directory if it doesn't exist
            results_dir.mkdir(parents=True, exist_ok=True)
        else:
            print(f"{Fore.RED}✗{Style.RESET_ALL} {exp_name:<30} MISSING")
            all_present = False
    
    # Check master scripts
    print("\nChecking Master Scripts...")
    master_scripts = [
        ('run_all_experiments.py', 'Master Experiment Runner'),
        ('generate_final_report.py', 'Final Report Generator'),
    ]
    
    for script, description in master_scripts:
        script_path = BASE_DIR / script
        if script_path.exists():
            print(f"{Fore.GREEN}✓{Style.RESET_ALL} {description:<30} {script}")
        else:
            print(f"{Fore.RED}✗{Style.RESET_ALL} {description:<30} MISSING")
            all_present = False
    
    # Summary
    print("\n" + "="*80)
    if all_present:
        print(f"{Fore.GREEN}{Style.BRIGHT}✓ ALL EXPERIMENTS READY TO RUN!{Style.RESET_ALL}\n")
        print("Next steps:")
        print("  1. Run all experiments:")
        print(f"     {Fore.CYAN}python3 run_all_experiments.py{Style.RESET_ALL}")
        print("\n  2. Generate final report:")
        print(f"     {Fore.CYAN}python3 generate_final_report.py{Style.RESET_ALL}")
        print("\n  3. View results:")
        print(f"     {Fore.CYAN}cat final_report/SUMMARY.txt{Style.RESET_ALL}")
        print()
        return 0
    else:
        print(f"{Fore.RED}✗ Some components are missing{Style.RESET_ALL}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
