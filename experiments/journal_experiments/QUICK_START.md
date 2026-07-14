# Quick Start Guide - Journal Experiments

## TL;DR

```bash
# 1. Install dependencies
cd experiments/journal_experiments
pip install -r requirements.txt

# 2. Run all experiments (~27 hours)
python3 run_all_experiments.py

# 3. Generate final report
python3 generate_final_report.py

# 4. View results
cat final_report/SUMMARY.txt
```

---

## Step-by-Step Guide

### Step 1: Verify System (Optional)

Some experiments work better with the DeceptiCloud system running:

```bash
# Start system (optional)
python3 launch_decepticloud_v2.py

# In another terminal, verify it's running
curl http://localhost:8080/proxy/status
```

### Step 2: Install Dependencies

```bash
cd experiments/journal_experiments
pip install -r requirements.txt
```

**Dependencies include**:
- numpy, pandas, scipy (data analysis)
- scikit-learn (ML models)
- tensorflow (neural networks)
- matplotlib, seaborn (visualization)
- colorama (terminal colors)

### Step 3: Run Experiments

#### Option A: Run All Experiments (Recommended)

```bash
python3 run_all_experiments.py
```

This will:
- Run experiments 1-8 and 10 sequentially
- Skip experiment 9 (manual user study)
- Save results to each experiment's `results/` directory
- Generate a run log with timestamps
- Handle errors gracefully
- Show progress with colored output

**Expected Runtime**: ~27 hours

**Tip**: Run overnight or over a weekend

#### Option B: Run Individual Experiments

```bash
# Baseline comparison (~4 hours)
python3 01_baseline_comparison/run.py

# Ablation study (~6 hours)
python3 02_ablation_study/run.py

# GAN realism test (~2 hours)
python3 03_gan_realism_test/run.py

# Blockchain integrity (~1 hour)
python3 04_blockchain_integrity/run.py

# Zero-day detection (~3 hours)
python3 05_zero_day_detection/run.py

# Adversarial evasion (~8 hours)
python3 06_adversarial_evasion/run.py

# Long-term deployment (~1 hour simulated)
python3 07_long_term_deployment/run.py

# Scalability test (~4 hours)
python3 08_scalability_test/run.py

# Cost-benefit analysis (~1 hour)
python3 10_cost_benefit_analysis/run.py
```

### Step 4: Generate Final Report

After experiments complete:

```bash
python3 generate_final_report.py
```

This creates:
- `final_report/consolidated_report.json` - All results
- `final_report/tables.tex` - LaTeX tables
- `final_report/paper_sections.tex` - Results text
- `final_report/SUMMARY.txt` - Human-readable summary

### Step 5: Review Results

```bash
# View summary
cat final_report/SUMMARY.txt

# View detailed results
cat final_report/consolidated_report.json | jq .

# View LaTeX tables
cat final_report/tables.tex

# View paper sections
cat final_report/paper_sections.tex
```

### Step 6: View Plots

All experiments generate publication-quality plots:

```bash
# View all plots
ls -lh */results/*.png

# Example: View baseline comparison
xdg-open 01_baseline_comparison/results/baseline_comparison_plot.png

# Or use your preferred image viewer
eog 01_baseline_comparison/results/baseline_comparison_plot.png
```

---

## What Each Experiment Does

| Experiment | Purpose | Runtime | Output |
|------------|---------|---------|--------|
| 01 | Compare with baselines | 4h | Accuracy comparison |
| 02 | Component importance | 6h | Ablation analysis |
| 03 | GAN data quality | 2h | Realism metrics |
| 04 | Blockchain security | 1h | Tamper detection |
| 05 | Zero-day attacks | 3h | Novel attack detection |
| 06 | Adversarial robustness | 8h | Evasion resistance |
| 07 | Long-term stability | 1h | Drift analysis |
| 08 | Performance scaling | 4h | Throughput metrics |
| 09 | User evaluation | Manual | Deception effectiveness |
| 10 | Economic analysis | 1h | ROI calculation |

---

## Expected Outputs

### JSON Results (per experiment)

```json
{
  "timestamp": "2026-05-04T10:30:00",
  "experiment": "baseline_comparison",
  "results": [
    {
      "name": "DeceptiCloud Ensemble",
      "accuracy": 0.989,
      "precision": 0.991,
      "recall": 0.987,
      "f1": 0.989,
      "fpr": 0.008
    }
  ]
}
```

### Plots (per experiment)

- High-resolution PNG (300 DPI)
- Colorblind-friendly palettes
- Publication-ready formatting
- Clear labels and legends

### Final Report

- **consolidated_report.json**: All results in structured format
- **tables.tex**: Ready to copy into LaTeX paper
- **paper_sections.tex**: Results section text
- **SUMMARY.txt**: Executive summary

---

## Monitoring Progress

### During Execution

The master script shows:
- ✓ Completed experiments (green)
- ✗ Failed experiments (red)
- ⊘ Skipped experiments (yellow)
- Progress indicators
- Estimated time remaining

### Check Logs

```bash
# View experiment run log
cat results/experiment_run_*.json

# View individual experiment output
cat 01_baseline_comparison/results/baseline_comparison_results.json
```

---

## Troubleshooting

### Experiment Fails

```bash
# Check if system is running (if needed)
curl http://localhost:8080/proxy/status

# Restart system
python3 launch_decepticloud_v2.py

# Re-run failed experiment
python3 01_baseline_comparison/run.py
```

### Out of Memory

```bash
# Check memory usage
free -h

# Reduce batch sizes (edit experiment script)
# Look for n_samples or batch_size variables
```

### Missing Dependencies

```bash
# Reinstall
pip install -r requirements.txt --force-reinstall

# Check Python version (requires 3.8+)
python3 --version
```

### Plots Not Generating

```bash
# Set matplotlib backend (for headless servers)
export MPLBACKEND=Agg

# Re-run experiment
python3 01_baseline_comparison/run.py
```

---

## Tips for Best Results

1. **Run on a dedicated machine**: Experiments are CPU-intensive
2. **Use a stable network**: Some experiments may fetch data
3. **Monitor disk space**: Results and plots require ~500MB
4. **Check logs regularly**: Catch errors early
5. **Run overnight**: Total runtime is ~27 hours
6. **Keep system running**: Some experiments benefit from live system

---

## After Experiments Complete

### 1. Validate Results

```bash
# Check all experiments completed
ls -d */results/*.json | wc -l  # Should be 9 (excluding manual user study)

# Check all plots generated
ls -d */results/*.png | wc -l  # Should be 9
```

### 2. Review Key Findings

```bash
cat final_report/SUMMARY.txt
```

Look for:
- Detection accuracy > 95%
- False positive rate < 1%
- Zero-day detection > 70%
- ROI > 500%
- Scalability > 100 req/s

### 3. Prepare for Paper

```bash
# Copy LaTeX tables to paper
cp final_report/tables.tex ~/paper/tables/

# Copy paper sections
cp final_report/paper_sections.tex ~/paper/sections/

# Copy plots
cp */results/*.png ~/paper/figures/
```

### 4. Write Remaining Sections

- Introduction
- Related Work
- Methodology (reference experiments)
- Results (use generated sections)
- Discussion
- Conclusion
- References

---

## Need Help?

1. Check `README.md` for detailed documentation
2. Check `IMPLEMENTATION_COMPLETE.md` for implementation details
3. Review individual experiment `run.py` files
4. Check error logs in `results/` directories

---

## Success Criteria

✅ All 9 automated experiments complete
✅ All JSON results generated
✅ All plots created (300 DPI)
✅ Final report generated
✅ Statistical significance established
✅ LaTeX tables formatted
✅ Paper sections drafted

**You're ready to write the paper!**

---

**Last Updated**: May 4, 2026
**Status**: Ready for execution
