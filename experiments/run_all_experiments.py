#!/usr/bin/env python3
"""
Master runner: executes all 4 experiments and compiles
a final research results report.
"""

import sys, json, time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

OUT_DIR = Path(__file__).parent / "results"
OUT_DIR.mkdir(exist_ok=True)

def run_all():
    report = {"timestamp": datetime.now().isoformat(), "experiments": {}}

    print("\n" + "█"*60)
    print("  DeceptiCloud — Full Experimental Evaluation Suite")
    print("█"*60)

    # Exp 1 — Attack Detection
    print("\n[1/4] Running Attack Detection Evaluation...")
    try:
        from experiments import attack_simulation as e1
    except ImportError:
        import importlib.util, pathlib
        spec = importlib.util.spec_from_file_location("e1",
               pathlib.Path(__file__).parent / "01_attack_simulation.py")
        e1 = importlib.util.module_from_spec(spec); spec.loader.exec_module(e1)
    r1 = e1.run()
    report["experiments"]["exp1_detection"] = r1
    time.sleep(1)

    # Exp 2 — Baseline Comparison
    print("\n[2/4] Running Baseline Comparison...")
    try:
        import importlib.util, pathlib
        spec = importlib.util.spec_from_file_location("e2",
               pathlib.Path(__file__).parent / "02_baseline_comparison.py")
        e2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(e2)
        r2 = e2.run()
        report["experiments"]["exp2_baseline"] = r2
    except Exception as ex:
        print(f"  Exp2 error: {ex}")
        report["experiments"]["exp2_baseline"] = {"error": str(ex)}
    time.sleep(1)

    # Exp 3 — GAN Quality
    print("\n[3/4] Running GAN Quality Metrics...")
    try:
        spec = importlib.util.spec_from_file_location("e3",
               pathlib.Path(__file__).parent / "03_gan_quality.py")
        e3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(e3)
        r3 = e3.run()
        report["experiments"]["exp3_gan"] = r3
    except Exception as ex:
        print(f"  Exp3 error: {ex}")
        report["experiments"]["exp3_gan"] = {"error": str(ex)}
    time.sleep(1)

    # Exp 4 — LLM Ablation
    print("\n[4/4] Running LLM Ablation Study...")
    try:
        spec = importlib.util.spec_from_file_location("e4",
               pathlib.Path(__file__).parent / "04_llm_ablation.py")
        e4 = importlib.util.module_from_spec(spec); spec.loader.exec_module(e4)
        r4 = e4.run()
        report["experiments"]["exp4_llm"] = r4
    except Exception as ex:
        print(f"  Exp4 error: {ex}")
        report["experiments"]["exp4_llm"] = {"error": str(ex)}

    # ── Final Summary ──────────────────────────────────────────────────────────
    print("\n" + "═"*60)
    print("  FINAL RESEARCH RESULTS SUMMARY")
    print("═"*60)

    e1d = report["experiments"].get("exp1_detection", {})
    e2d = report["experiments"].get("exp2_baseline", {})
    e3d = report["experiments"].get("exp3_gan", {})
    e4d = report["experiments"].get("exp4_llm", {})

    print(f"\n  ┌─ Exp 1: DeceptiCloud Detection Performance ──────────────")
    print(f"  │  Accuracy  : {e1d.get('accuracy',0)*100:.2f}%")
    print(f"  │  Precision : {e1d.get('precision',0)*100:.2f}%")
    print(f"  │  Recall    : {e1d.get('recall',0)*100:.2f}%")
    print(f"  │  F1 Score  : {e1d.get('f1_score',0)*100:.2f}%")
    print(f"  │  False Pos : {e1d.get('false_positive_rate',0)*100:.2f}%")
    print(f"  │  Latency   : {e1d.get('avg_latency_ms',0):.1f} ms avg")

    if "decepticloud_ensemble" in e2d:
        em = e2d["decepticloud_ensemble"]
        rm = e2d.get("rule_only", {})
        mm = e2d.get("ml_only", {})
        print(f"\n  ├─ Exp 2: Baseline Comparison ────────────────────────────")
        print(f"  │  Rule-Only WAF      : Acc={rm.get('accuracy',0)*100:.1f}%  F1={rm.get('f1',0)*100:.1f}%")
        print(f"  │  ML-Only            : Acc={mm.get('accuracy',0)*100:.1f}%  F1={mm.get('f1',0)*100:.1f}%")
        print(f"  │  DeceptiCloud       : Acc={em.get('accuracy',0)*100:.1f}%  F1={em.get('f1',0)*100:.1f}%")
        imp = e2d.get("improvement_over_rules", {})
        print(f"  │  vs Rules → +{imp.get('accuracy_delta',0)*100:.2f}% accuracy, +{imp.get('f1_delta',0)*100:.2f}% F1")

    if "quality_score_pct" in e3d:
        dists = e3d.get("distributions", {})
        print(f"\n  ├─ Exp 3: GAN Synthetic Data Quality ──────────────────────")
        print(f"  │  Overall Quality Score : {e3d['quality_score_pct']}%")
        for feat, key in [("Balance","balance_real_vs_gan"),("Credit Score","credit_score"),("Age","age")]:
            if key in dists:
                d = dists[key]
                print(f"  │  {feat:<14}: W-dist(norm)={d['wasserstein_norm']:.4f}  "
                      f"KS-p={d['ks_p_value']:.4f}  "
                      f"Similar={'YES' if d['ks_similar'] else 'NO'}")
        wm = dists.get("watermark", {})
        if wm:
            print(f"  │  Watermark Integrity: {wm['watermark_pct']}% (expected 30%) — {wm['status']}")

    if "dwell_improvement_pct" in e4d:
        wl = e4d.get("with_llm", {})
        nl = e4d.get("without_llm", {})
        print(f"\n  └─ Exp 4: LLM Ablation (Dwell Time) ──────────────────────")
        print(f"     With LLM    : {wl.get('dwell_mean',0):.2f}s avg dwell  "
              f"engagement={wl.get('engage_mean',0):.3f}")
        print(f"     Without LLM : {nl.get('dwell_mean',0):.2f}s avg dwell  "
              f"engagement={nl.get('engage_mean',0):.3f}")
        print(f"     LLM Dwell Improvement   : +{e4d['dwell_improvement_pct']}%")
        print(f"     LLM Engagement Improvement: +{e4d['engage_improvement_pct']}%")

    print(f"\n{'═'*60}\n")

    # Save master report
    out = OUT_DIR / "MASTER_RESULTS.json"
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print(f"  ✅ Master report saved → {out}\n")
    return report

if __name__ == "__main__":
    run_all()
