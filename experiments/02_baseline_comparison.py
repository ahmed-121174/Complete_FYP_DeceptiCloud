#!/usr/bin/env python3
"""
Experiment 2: Baseline Comparison
Compares DeceptiCloud (ML ensemble) vs Rule-Only system.
Uses the ML API directly to isolate each component.
"""

import requests, json, time, re
from pathlib import Path
from datetime import datetime

ML_API  = "http://localhost:5000"
PROXY   = "http://localhost:8080"
OUT_DIR = Path(__file__).parent / "results"
OUT_DIR.mkdir(exist_ok=True)

# ── Rule-only detector (mimic classic WAF pattern matching) ──────────────────

SQLI_PATTERNS  = re.compile(r"(union\s+select|or\s+1=1|drop\s+table|insert\s+into|sleep\s*\(|waitfor\s+delay|'--|;--|\bor\b.*=.*|having\s+1=1)", re.I)
XSS_PATTERNS   = re.compile(r"(<script|onerror=|onload=|javascript:|<svg|<iframe|<img\s+src=x|document\.cookie|alert\s*\()", re.I)
LFI_PATTERNS   = re.compile(r"(\.\./|\.\.\\|%2e%2e%2f|%252e%252e|/etc/passwd|/etc/shadow|windows/system)", re.I)
CMD_PATTERNS   = re.compile(r"(;\s*(ls|cat|whoami|id|ping|curl|wget|nc|bash)|`[^`]+`|\$\([^)]+\)|\|\||\bexec\b)", re.I)
SCAN_PATTERNS  = re.compile(r"(sqlmap|nikto|nmap|masscan|\.env|backup\.sql|phpmyadmin|wp-admin|\.git/)", re.I)

def rule_only_detect(url: str, ua: str = "", payload: str = "") -> bool:
    combined = url + " " + payload
    if SQLI_PATTERNS.search(combined): return True
    if XSS_PATTERNS.search(combined):  return True
    if LFI_PATTERNS.search(combined):  return True
    if CMD_PATTERNS.search(combined):  return True
    if SCAN_PATTERNS.search(ua + " " + combined): return True
    return False

# ── ML-only detector (calls API, no rules) ──────────────────────────────────

def ml_only_detect(url: str, ua: str = "", payload: str = "") -> bool:
    combined = url + " " + payload
    threshold = 0.55
    try:
        # XSS model
        r = requests.post(f"{ML_API}/api/detect/xss",
                          json={"payload": combined}, timeout=4)
        if r.status_code == 200:
            p = r.json().get("probability", r.json().get("confidence", 0))
            if p > threshold: return True
    except Exception:
        pass
    try:
        # Brute force
        r = requests.post(f"{ML_API}/api/detect/brute-force",
                          json={"attempts": 1, "ua": ua, "payload": payload}, timeout=4)
        if r.status_code == 200:
            p = r.json().get("confidence", 0)
            if p > threshold: return True
    except Exception:
        pass
    return False

# ── Test dataset (labelled) ──────────────────────────────────────────────────

LABELLED = [
    # (url, ua, payload, true_label, attack_type)
    ("/banking/search?q=1' OR 1=1--",                    "Mozilla/5.0", "", 1, "SQLi"),
    ("/banking/search?q=1 UNION SELECT username,password FROM users--", "sqlmap/1.7", "", 1, "SQLi"),
    ("/banking/search?q='; DROP TABLE users--",           "sqlmap/1.7", "", 1, "SQLi"),
    ("/banking/search?q=<script>alert(1)</script>",       "Mozilla/5.0", "", 1, "XSS"),
    ("/banking/search?q=<img src=x onerror=alert(1)>",    "Mozilla/5.0", "", 1, "XSS"),
    ("/banking/search?q=<svg onload=alert(1)>",           "Mozilla/5.0", "", 1, "XSS"),
    ("/banking/search?q=../../../etc/passwd",             "Mozilla/5.0", "", 1, "LFI"),
    ("/banking/search?q=%2e%2e%2fetc%2fpasswd",           "Mozilla/5.0", "", 1, "LFI"),
    ("/banking/search?q=; cat /etc/passwd",               "Mozilla/5.0", "", 1, "CMDi"),
    ("/banking/search?q=`whoami`",                        "Mozilla/5.0", "", 1, "CMDi"),
    ("/.env",                                             "Nikto/2.1",  "", 1, "Scanner"),
    ("/phpmyadmin",                                       "Nikto/2.1",  "", 1, "Scanner"),
    ("/.git/config",                                      "sqlmap/1.7", "", 1, "Scanner"),
    ("/wp-admin",                                         "Nikto/2.1",  "", 1, "Scanner"),
    ("/backup.sql",                                       "curl/7.8",   "", 1, "Scanner"),
    # -- Benign --
    ("/banking/",                                         "Mozilla/5.0", "", 0, "Benign"),
    ("/banking/search?q=savings",                         "Mozilla/5.0", "", 0, "Benign"),
    ("/ecommerce/search?q=headphones",                    "Mozilla/5.0", "", 0, "Benign"),
    ("/healthcare/search?q=checkup",                      "Mozilla/5.0", "", 0, "Benign"),
    ("/blog/search?q=python+tutorial",                    "Mozilla/5.0", "", 0, "Benign"),
    ("/blog/search?q=docker+guide",                       "Mozilla/5.0", "", 0, "Benign"),
    ("/ecommerce/items",                                  "Mozilla/5.0", "", 0, "Benign"),
    ("/banking/item/1",                                   "Mozilla/5.0", "", 0, "Benign"),
    ("/corporate/search?q=consulting",                    "Mozilla/5.0", "", 0, "Benign"),
    ("/api_service/items",                                "Mozilla/5.0", "", 0, "Benign"),
    # -- Edge / Ambiguous --
    ("/banking/search?q=select+savings+account",          "Mozilla/5.0", "", 0, "Benign-edge"),
    ("/blog/search?q=javascript+tutorial",                "Mozilla/5.0", "", 0, "Benign-edge"),
    ("/banking/search?q=union+bank+rates",                "Mozilla/5.0", "", 0, "Benign-edge"),
    ("/healthcare/search?q=drop+in+clinic",               "Mozilla/5.0", "", 0, "Benign-edge"),
    ("/blog/search?q=script+writing+tips",                "Mozilla/5.0", "", 0, "Benign-edge"),
]

def metrics(results):
    TP = sum(1 for r in results if r["true"]==1 and r["pred"]==1)
    FP = sum(1 for r in results if r["true"]==0 and r["pred"]==1)
    TN = sum(1 for r in results if r["true"]==0 and r["pred"]==0)
    FN = sum(1 for r in results if r["true"]==1 and r["pred"]==0)
    acc  = (TP+TN)/len(results) if results else 0
    prec = TP/(TP+FP) if (TP+FP)>0 else 0
    rec  = TP/(TP+FN) if (TP+FN)>0 else 0
    f1   = 2*prec*rec/(prec+rec) if (prec+rec)>0 else 0
    fpr  = FP/(FP+TN) if (FP+TN)>0 else 0
    return {"TP":TP,"FP":FP,"TN":TN,"FN":FN,
            "accuracy":round(acc,4),"precision":round(prec,4),
            "recall":round(rec,4),"f1":round(f1,4),"fpr":round(fpr,4)}

def run():
    print(f"\n{'='*60}")
    print("  Experiment 2: Baseline Comparison")
    print(f"{'='*60}\n")

    rule_results = []
    ml_results   = []

    for url, ua, payload, true_label, atype in LABELLED:
        rule_pred = 1 if rule_only_detect(url, ua, payload) else 0
        ml_pred   = 1 if ml_only_detect(url, ua, payload)   else 0

        rule_results.append({"true": true_label, "pred": rule_pred, "type": atype})
        ml_results.append(  {"true": true_label, "pred": ml_pred,   "type": atype})
        time.sleep(0.1)

    rm = metrics(rule_results)
    mm = metrics(ml_results)

    # DeceptiCloud ensemble (rule 40% + ML 60%) — approximate
    ensemble_results = []
    for r, m in zip(rule_results, ml_results):
        ensemble_score = 0.4 * r["pred"] + 0.6 * m["pred"]
        ensemble_pred  = 1 if ensemble_score >= 0.4 else 0
        ensemble_results.append({"true": r["true"], "pred": ensemble_pred, "type": r["type"]})
    em = metrics(ensemble_results)

    output = {
        "timestamp": datetime.now().isoformat(),
        "dataset_size": len(LABELLED),
        "rule_only":     rm,
        "ml_only":       mm,
        "decepticloud_ensemble": em,
        "improvement_over_rules": {
            "accuracy_delta":  round(em["accuracy"]  - rm["accuracy"],  4),
            "f1_delta":        round(em["f1"]        - rm["f1"],        4),
            "fpr_delta":       round(em["fpr"]       - rm["fpr"],       4),
        },
        "improvement_over_ml_only": {
            "accuracy_delta":  round(em["accuracy"]  - mm["accuracy"],  4),
            "f1_delta":        round(em["f1"]        - mm["f1"],        4),
        }
    }

    out = OUT_DIR / "exp2_baseline_comparison.json"
    with open(out, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  {'System':<30} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1':>10} {'FPR':>8}")
    print(f"  {'─'*78}")
    for name, m in [("Rule-Only (WAF)", rm), ("ML-Only", mm), ("DeceptiCloud Ensemble", em)]:
        print(f"  {name:<30} {m['accuracy']*100:>9.2f}% {m['precision']*100:>9.2f}% "
              f"{m['recall']*100:>9.2f}% {m['f1']*100:>9.2f}% {m['fpr']*100:>7.2f}%")

    print(f"\n  Ensemble vs Rules  → Accuracy +{output['improvement_over_rules']['accuracy_delta']*100:.2f}%  "
          f"F1 +{output['improvement_over_rules']['f1_delta']*100:.2f}%")
    print(f"  Ensemble vs ML-Only→ Accuracy +{output['improvement_over_ml_only']['accuracy_delta']*100:.2f}%  "
          f"F1 +{output['improvement_over_ml_only']['f1_delta']*100:.2f}%")
    print(f"\n  Saved → {out}\n")
    return output

if __name__ == "__main__":
    run()
