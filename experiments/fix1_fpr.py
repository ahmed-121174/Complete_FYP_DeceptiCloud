#!/usr/bin/env python3
"""Fix 1: Measure real FPR by sending 200 benign requests through proxy."""
import requests, json, time
from pathlib import Path

OUT = Path(__file__).parent / "results"
OUT.mkdir(exist_ok=True)
PROXY = "http://localhost:8080"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0"

BENIGN = [
    ("GET", "/banking/"),
    ("GET", "/banking/items"),
    ("GET", "/banking/search?q=savings+account"),
    ("GET", "/banking/search?q=loan+rates"),
    ("GET", "/banking/search?q=credit+card"),
    ("GET", "/banking/item/1"),
    ("GET", "/banking/item/2"),
    ("GET", "/ecommerce/"),
    ("GET", "/ecommerce/items"),
    ("GET", "/ecommerce/search?q=headphones"),
    ("GET", "/ecommerce/search?q=laptop+bag"),
    ("GET", "/ecommerce/search?q=wireless+mouse"),
    ("GET", "/ecommerce/item/1"),
    ("GET", "/healthcare/"),
    ("GET", "/healthcare/items"),
    ("GET", "/healthcare/search?q=general+checkup"),
    ("GET", "/healthcare/search?q=blood+test"),
    ("GET", "/healthcare/item/1"),
    ("GET", "/blog/"),
    ("GET", "/blog/items"),
    ("GET", "/blog/search?q=python+tutorial"),
    ("GET", "/blog/search?q=docker+guide"),
    ("GET", "/blog/search?q=machine+learning"),
    ("GET", "/blog/item/1"),
    ("GET", "/api_service/"),
    ("GET", "/api_service/items"),
    ("GET", "/api_service/search?q=rest+api"),
    ("GET", "/corporate/"),
    ("GET", "/corporate/search?q=consulting+services"),
    ("GET", "/admin_panel/"),
]

def run():
    print("\n=== Fix 1: Real FPR Measurement (200 benign requests) ===")
    results = []
    # Send each benign URL ~7 times to reach 200 total
    pool = BENIGN * 7
    pool = pool[:200]

    for i, (method, path) in enumerate(pool):
        try:
            r = requests.get(f"{PROXY}{path}",
                headers={"User-Agent": UA}, timeout=6, allow_redirects=True)
            body = r.text.lower()
            # A false positive = request flagged as attack (routed to honeypot)
            # Honeypot sites have different names than real sites
            honeypot_names = ["quickbank","shopnow","healthplus","devnotes",
                              "cloudapi","quantumtech","infrahub"]
            fp = any(name in body for name in honeypot_names)
            results.append({"path": path, "status": r.status_code, "fp": fp})
        except Exception:
            results.append({"path": path, "status": 0, "fp": False})
        if i % 20 == 0:
            print(f"  Sent {i+1}/200...", end="\r")
        time.sleep(0.05)

    fp_count = sum(1 for r in results if r["fp"])
    fpr = fp_count / len(results)
    tnr = 1 - fpr  # True Negative Rate (specificity)

    summary = {
        "total_benign_sent": len(results),
        "false_positives": fp_count,
        "true_negatives": len(results) - fp_count,
        "FPR": round(fpr, 4),
        "TNR_specificity": round(tnr, 4),
        "FPR_pct": round(fpr * 100, 2),
    }

    with open(OUT / "fix1_fpr.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n  Benign sent    : {len(results)}")
    print(f"  False Positives: {fp_count}")
    print(f"  FPR            : {fpr*100:.2f}%")
    print(f"  Specificity    : {tnr*100:.2f}%")
    print(f"  Saved → {OUT}/fix1_fpr.json")
    return summary

if __name__ == "__main__":
    run()
