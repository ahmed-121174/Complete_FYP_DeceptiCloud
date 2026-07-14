# DeceptiCloud Journal Experiments

This directory contains all experiments for the journal paper submission.

## Experiment Structure

```
journal_experiments/
├── 01_baseline_comparison/       # Compare with Snort, Kitsune, single-model
├── 02_ablation_study/            # Remove components, measure impact
├── 03_gan_realism_test/          # Evaluate synthetic data quality
├── 04_blockchain_integrity/      # Tamper-proof verification
├── 05_zero_day_detection/        # Test on unseen attacks
├── 06_adversarial_evasion/       # Robustness against evasion
├── 07_long_term_deployment/      # 30-day continuous operation
├── 08_scalability_test/          # Load testing, concurrent attackers
├── 09_user_study/                # Attacker & defender studies
├── 10_cost_benefit_analysis/     # ROI calculation
├── run_all_experiments.py        # Master script
└── generate_final_report.py      # Compile results into paper-ready format
```

## Quick Start

```bash
# Run all experiments (takes ~48 hours)
python3 experiments/journal_experiments/run_all_experiments.py

# Generate final report
python3 experiments/journal_experiments/generate_final_report.py

# Output: experiments/journal_experiments/FINAL_REPORT.pdf
```

## Individual Experiments

Each experiment can be run independently:

```bash
python3 experiments/journal_experiments/01_baseline_comparison/run.py
python3 experiments/journal_experiments/02_ablation_study/run.py
# ... etc
```

## Requirements

```bash
pip install -r experiments/journal_experiments/requirements.txt
```

## Expected Runtime

- Baseline Comparison: 4 hours
- Ablation Study: 6 hours
- GAN Realism Test: 2 hours
- Blockchain Integrity: 1 hour
- Zero-Day Detection: 3 hours
- Adversarial Evasion: 8 hours
- Long-Term Deployment: 30 days (background)
- Scalability Test: 4 hours
- User Study: Manual (1 week)
- Cost-Benefit: 1 hour

**Total Automated Runtime**: ~28 hours + 30 days background monitoring
