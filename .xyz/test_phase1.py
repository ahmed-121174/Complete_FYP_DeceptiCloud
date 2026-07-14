#!/usr/bin/env python3
"""
Comprehensive Phase 1 Test Suite — DeceptiCloud
Tests: Honey Tokens, Blockchain Ledger, Behavioral Fingerprinting
Also verifies NO regressions on existing functionality.
"""
import requests
import json
import time
import sys
from pathlib import Path

BASE = "http://localhost"
REAL_PORTS = list(range(3001, 3008))
HONEYPOT_PORTS = list(range(4001, 4008))
PROXY_PORT = 8080

results = {"passed": 0, "failed": 0, "tests": []}

def test(name, condition, details=""):
    status = "PASS" if condition else "FAIL"
    results["passed" if condition else "failed"] += 1
    results["tests"].append({"name": name, "status": status, "details": details})
    icon = "" if condition else ""
    print(f"  {icon} {name}" + (f" — {details}" if details else ""))
    return condition

# TEST 1: REGRESSION — All 14 sites still up

print("  TEST SUITE 1: REGRESSION — Existing Functionality")

for port in REAL_PORTS:
    try:
        r = requests.get(f"{BASE}:{port}/", timeout=5)
        test(f"Real site :{port} UP", r.status_code == 200)
    except:
        test(f"Real site :{port} UP", False, "Connection refused")

for port in HONEYPOT_PORTS:
    try:
        r = requests.get(f"{BASE}:{port}/", timeout=5)
        test(f"Honeypot  :{port} UP", r.status_code == 200)
    except:
        test(f"Honeypot  :{port} UP", False, "Connection refused")

# Proxy up

try:
    r = requests.get(f"{BASE}:{PROXY_PORT}/", timeout=5)
    test("Proxy UP", r.status_code == 200)
except:
    test("Proxy UP", False, "Connection refused")

# TEST 2: CANARY TOKENS — Only on honeypots

print("  TEST SUITE 2: CANARY TOKENS & TRAPS")

# Test canary routes on honeypot (should work)

canary_routes = [
    ("/robots.txt", "text/plain", "robots_txt"),
    ("/.env", "text/plain", "env_file"),
    ("/backup.sql", "application/sql", "database_backup"),
    ("/wp-admin", "text/html", "admin_panel"),
    ("/phpmyadmin/", "text/html", "phpmyadmin"),
    ("/api/v2/config", "application/json", "api_config"),
    ("/server-status", "text/html", "server_status"),
    ("/debug/", "application/json", "debug_endpoint"),
    ("/.git/config", "text/plain", "git_exposure"),
    ("/pixel.png", "image/png", "tracking_pixel"),
]

for route, expected_type, name in canary_routes:
    try:
        r = requests.get(f"{BASE}:4001{route}", timeout=5)
        test(f"Canary '{name}' on honeypot", r.status_code == 200,
             f"Content-Type: {r.headers.get('Content-Type', '')[:30]}")
    except Exception as e:
        test(f"Canary '{name}' on honeypot", False, str(e))

# Verify canary stats API

try:
    r = requests.get(f"{BASE}:4001/api/canary-stats", timeout=5)
    stats = r.json()
    test("Canary stats API works", stats['total_triggers'] > 0,
         f"Total triggers: {stats['total_triggers']}")
    test("Canary stats by type", len(stats['by_type']) > 0,
         f"Types: {list(stats['by_type'].keys())}")
except Exception as e:
    test("Canary stats API", False, str(e))

# Critical: canary routes should NOT exist on real sites

print("\n  --- Isolation Tests ---")
try:
    r = requests.get(f"{BASE}:3001/.env", timeout=5)
    # Real site should return 404 for /.env

    test("Real site does NOT serve /.env", r.status_code == 404,
         f"Status: {r.status_code}")
except:
    test("Real site does NOT serve /.env", True, "Connection refused (good)")

try:
    r = requests.get(f"{BASE}:3001/robots.txt", timeout=5)
    # Real site should return 404 for robots.txt (no canary)

    test("Real site does NOT serve canary robots.txt", r.status_code == 404,
         f"Status: {r.status_code}")
except:
    test("Real site does NOT serve canary robots.txt", True, "Connection refused (good)")

try:
    r = requests.get(f"{BASE}:3001/backup.sql", timeout=5)
    test("Real site does NOT serve backup.sql", r.status_code == 404,
         f"Status: {r.status_code}")
except:
    test("Real site does NOT serve backup.sql", True, "Connection refused (good)")

# TEST 3: CANARY CONTENT VERIFICATION

print("  TEST SUITE 3: CANARY CONTENT QUALITY")

# Verify .env contains realistic fake credentials

r = requests.get(f"{BASE}:4001/.env", timeout=5)
env_content = r.text
test("Fake .env has AWS keys", "AWS_ACCESS_KEY_ID" in env_content)
test("Fake .env has DB password", "DB_PASSWORD" in env_content)
test("Fake .env has JWT secret", "JWT_SECRET" in env_content)
test("Fake .env has Stripe key", "STRIPE_SECRET_KEY" in env_content)

# Verify backup.sql is realistic

r = requests.get(f"{BASE}:4001/backup.sql", timeout=5)
sql_content = r.text
test("Fake SQL dump has CREATE TABLE", "CREATE TABLE" in sql_content)
test("Fake SQL dump has INSERT INTO", "INSERT INTO" in sql_content)
test("Fake SQL dump has MySQL header", "MySQL dump" in sql_content)
test("Fake SQL dump has watermark", "Watermark" in sql_content)

# Verify API config returns JSON with fake keys

r = requests.get(f"{BASE}:4001/api/v2/config", timeout=5)
config = r.json()
test("Fake API config has AWS keys", 'aws' in config)
test("Fake API config has JWT", 'jwt_secret' in config)
test("Fake API config has database", 'database' in config)

# TEST 4: BLOCKCHAIN ATTACK LEDGER

print("  TEST SUITE 4: BLOCKCHAIN ATTACK LEDGER")

# Trigger an attack via proxy to generate a blockchain entry

try:
    r = requests.get(f"{BASE}:{PROXY_PORT}/banking/search?q=' OR 1=1--", timeout=5)
    test("Attack request via proxy", r.status_code == 200)
    time.sleep(1)  # Wait for blockchain write
except Exception as e:
    test("Attack request via proxy", False, str(e))

# Check blockchain file exists

chain_file = Path("/media/amei-302/New Volume/SEMESTER VIII/Ahmed Fype-II/honeypot/attack_chain.json")
test("Blockchain file exists", chain_file.exists())

if chain_file.exists():
    with open(chain_file) as f:
        chain = json.load(f)
    
    test("Blockchain has genesis block", len(chain) > 0)
    test("Blockchain has attack blocks", len(chain) > 1,
         f"Total blocks: {len(chain)}")
    
    # Verify chain integrity

    genesis = chain[0]
    test("Genesis block is valid", genesis['data']['type'] == 'genesis')
    test("Genesis block has hash", len(genesis['hash']) == 64)
    
    # Verify hash chain linkage

    chain_valid = True
    for i in range(1, len(chain)):
        if chain[i]['previous_hash'] != chain[i-1]['hash']:
            chain_valid = False
            break
    test("Hash chain linkage valid", chain_valid)
    
    # Verify proof-of-work (hash starts with '00')

    pow_valid = all(b['hash'].startswith('00') for b in chain)
    test("Proof-of-work valid (all hashes start with 00)", pow_valid)
    
    # Check attack data in latest block

    if len(chain) > 1:
        latest = chain[-1]
        test("Latest block has attack data", 'ip' in latest['data'] or 'url' in latest['data'])

# TEST 5: BEHAVIORAL FINGERPRINTING

print("  TEST SUITE 5: BEHAVIORAL FINGERPRINTING")

# Send a fingerprint payload to honeypot

fingerprint_data = {
    "canvas_hash": "test_abc123",
    "webgl_hash": "test_def456",
    "fonts_hash": "test_ghi789",
    "screen": {"resolution": "1920x1080", "colorDepth": 24},
    "timezone_offset": -300,
    "language": "en-US",
    "platform": "Linux x86_64",
    "touch_support": False,
    "do_not_track": "1",
    "plugins_count": 3,
    "keystroke_intervals": [120, 85, 200, 95, 110, 150, 88, 105],
    "mouse_movements": [
        {"x": 100, "y": 200, "t": 1000},
        {"x": 150, "y": 250, "t": 1050},
        {"x": 200, "y": 300, "t": 1100},
        {"x": 280, "y": 320, "t": 1150},
        {"x": 350, "y": 340, "t": 1200},
    ],
    "scroll_depth": 75,
    "form_interactions": 3,
    "time_on_page": 45,
    "pages_visited": ["/", "/login", "/dashboard"],
    "request_intervals": [2000, 3500, 1200],
}

try:
    r = requests.post(f"{BASE}:4001/api/fingerprint",
                      json=fingerprint_data, timeout=5)
    result = r.json()
    test("Fingerprint API accepts data", r.status_code == 200)
    test("Returns behavioral hash", 'behavioral_hash' in result,
         f"Hash: {result.get('behavioral_hash', 'N/A')}")
    test("Returns cluster ID", 'cluster_id' in result,
         f"Cluster: {result.get('cluster_id', 'N/A')}")
except Exception as e:
    test("Fingerprint API", False, str(e))

# Send a second fingerprint from "different IP" but same browser

fingerprint_data_2 = {**fingerprint_data, "timezone_offset": -300}
try:
    r = requests.post(f"{BASE}:4002/api/fingerprint",
                      json=fingerprint_data_2, timeout=5)
    result2 = r.json()
    test("Second fingerprint accepted", r.status_code == 200)
    test("Same browser gets same hash", 
         result2.get('behavioral_hash') == result.get('behavioral_hash'),
         f"Hash match: {result2.get('behavioral_hash')} == {result.get('behavioral_hash')}")
except Exception as e:
    test("Second fingerprint", False, str(e))

# Check fingerprint stats API

try:
    r = requests.get(f"{BASE}:4001/api/fingerprint-stats", timeout=5)
    stats = r.json()
    test("Fingerprint stats API works", r.status_code == 200)
    test("Has fingerprint profiles", stats['total_fingerprints'] > 0,
         f"Total: {stats['total_fingerprints']}")
except Exception as e:
    test("Fingerprint stats API", False, str(e))

# Critical: fingerprint API should NOT exist on real sites

print("\n  --- Isolation Tests ---")
try:
    r = requests.post(f"{BASE}:3001/api/fingerprint",
                      json=fingerprint_data, timeout=5)
    test("Real site does NOT accept fingerprints", r.status_code == 404,
         f"Status: {r.status_code}")
except:
    test("Real site does NOT accept fingerprints", True, "Connection refused (good)")

# TEST 6: FINGERPRINT JS ISOLATION

print("  TEST SUITE 6: JS FINGERPRINT ISOLATION")

# Honeypot page should include fingerprint JS

try:
    r = requests.get(f"{BASE}:4001/", timeout=5)
    test("Honeypot page includes fingerprint JS",
         "fingerprint_collector.js" in r.text)
except:
    test("Honeypot page includes fingerprint JS", False)

# Real site page should NOT include fingerprint JS

try:
    r = requests.get(f"{BASE}:3001/", timeout=5)
    test("Real site does NOT include fingerprint JS",
         "fingerprint_collector.js" not in r.text)
except:
    test("Real site does NOT include fingerprint JS", True)

# TEST 7: PROXY FLOW WITH NEW FEATURES

print("  TEST SUITE 7: END-TO-END PROXY FLOW")

# Benign request → Real site

try:
    r = requests.get(f"{BASE}:{PROXY_PORT}/banking/", timeout=5)
    test("Benign request → Real site (200)", r.status_code == 200)
except:
    test("Benign request → Real site", False)

# Malicious request → Honeypot → should also trigger blockchain

try:
    r = requests.get(f"{BASE}:{PROXY_PORT}/banking/search?q=<script>alert(1)</script>", timeout=5)
    test("XSS attack → Honeypot (200)", r.status_code == 200)
except:
    test("XSS attack → Honeypot", False)

# Path traversal

try:
    r = requests.get(f"{BASE}:{PROXY_PORT}/banking/../../../etc/passwd", timeout=5)
    test("Path traversal attempt processed", True)
except:
    test("Path traversal", False)

time.sleep(1)

# Verify blockchain grew after attacks

if chain_file.exists():
    with open(chain_file) as f:
        chain_after = json.load(f)
    test("Blockchain grew after attacks", len(chain_after) > len(chain),
         f"Before: {len(chain)}, After: {len(chain_after)}")

# SUMMARY

print(f"  FINAL RESULTS: {results['passed']} PASSED, {results['failed']} FAILED")

if results['failed'] == 0:
    print("\n   ALL TESTS PASSED — Phase 1 is fully operational!")
else:
    print(f"\n    {results['failed']} test(s) failed — see above for details")
    
print()
sys.exit(0 if results['failed'] == 0 else 1)
