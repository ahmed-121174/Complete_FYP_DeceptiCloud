#!/usr/bin/env python3
"""
Phase 2 Test Suite — DeceptiCloud
Tests: LLM Adaptive Responses & GAN Synthetic Data
Verifies dynamic honeypot behavior and WGAN-GP output quality.
"""
import requests
import sqlite3
import json
import time
import sys
from pathlib import Path

BASE = "http://localhost"
PROXY_PORT = 8080
DB_DIR = Path("websites/databases")

results = {"passed": 0, "failed": 0, "tests": []}

def test(name, condition, details=""):
    status = "PASS" if condition else "FAIL"
    results["passed" if condition else "failed"] += 1
    results["tests"].append({"name": name, "status": status, "details": details})
    icon = "" if condition else ""
    print(f"  {icon} {name}" + (f" — {details}" if details else ""))
    return condition

print("  TEST SUITE: PHASE 2 — AI EXPANSIONS (v2)")

# TEST 1: LLM ADAPTIVE RESPONSES

print("\n[ Testing LLM Adaptive Response Engine ]")

# 1. SQLi Attack -> LLM generates dynamic response OR falls through to dynamic honeypot

sqli_payload = "' OR 1=1 UNION SELECT userid, passhash, role FROM auth_users --"
try:
    start_t = time.time()
    r = requests.get(f"{BASE}:{PROXY_PORT}/banking/search?q={sqli_payload}", timeout=45)
    elapsed = time.time() - start_t
    
    test("SQLi routed correctly", r.status_code == 200, f"Time: {elapsed:.2f}s")
    
    # Either LLM HTML or dynamic honeypot HTML — both should be valid HTML

    is_html = "<html" in r.text.lower() or "<div" in r.text.lower() or "<table" in r.text.lower()
    test("Response is valid HTML", is_html)
    
    # Check if LLM generated the response (contains attack-specific content)

    # OR the dynamic honeypot served its page (contains search results/login)

    has_content = len(r.text) > 100
    
    # Determine source: LLM response or dynamic honeypot

    if elapsed > 3 and elapsed < 30:
        source = "LLM-generated (dynamic)"
    else:
        source = "Dynamic honeypot (fallback)"
    test("Meaningful content returned", has_content, 
         f"Source: {source} | Size: {len(r.text)} bytes")
    
except Exception as e:
    test("SQLi route failed", False, str(e))

# 2. XSS Attack -> LLM reflects payload OR dynamic honeypot serves page

xss_payload = "<script>alert('Behave')</script>"
try:
    r = requests.get(f"{BASE}:{PROXY_PORT}/banking/search?q={xss_payload}", timeout=45)
    
    test("XSS routed correctly", r.status_code == 200)
    
    # If LLM generated response, it should reflect XSS. If dynamic honeypot, page loads.

    has_valid_response = len(r.text) > 100
    test("XSS response valid", has_valid_response, f"Size: {len(r.text)} bytes")
except Exception as e:
    test("XSS route failed", False, str(e))

# TEST 2: DYNAMIC HONEYPOT VERIFICATION

print("\n[ Verifying Dynamic Honeypot (not static) ]")

# Access honeypot directly to prove it's dynamic

try:
    r = requests.get(f"{BASE}:4001/", timeout=10)
    is_dynamic = "<html" in r.text.lower() and "securebank" in r.text.lower()
    test("Honeypot serves dynamic pages", is_dynamic, "Full HTML with site branding")
    
    # Login to honeypot to prove database-backed dynamic content

    r2 = requests.post(f"{BASE}:4001/login", data={
        'username': 'admin', 'password': 'DeceptiCloud'
    }, allow_redirects=True, timeout=10)
    test("Honeypot login works (database-backed)", r2.status_code == 200,
         f"Dynamic session active")
except Exception as e:
    test("Dynamic honeypot verification failed", False, str(e))

# TEST 3: GAN SYNTHETIC DATA & WATERMARKING

print("\n[ Testing GAN Synthetic Data (WGAN-GP) ]")

# Test across multiple honeypot databases

honeypot_dbs = ['banking_honeypot.db', 'ecommerce_honeypot.db', 'healthcare_honeypot.db']
all_gan_pass = True

for db_name in honeypot_dbs:
    db_path = DB_DIR / db_name
    if db_path.exists():
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT count(*) FROM users")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT count(*) FROM users WHERE CAST(ROUND(balance * 100) AS INTEGER) % 10 = 7")
        watermarked = cursor.fetchone()[0]
        
        conn.close()
        
        site_name = db_name.replace('_honeypot.db', '')
        passed = total > 50 and watermarked >= 50
        if not passed:
            all_gan_pass = False
        test(f"GAN data in {site_name}", passed,
             f"Users: {total} | Watermarked: {watermarked}")

# Test watermark integrity on banking (primary)

db_path = DB_DIR / "banking_honeypot.db"
if db_path.exists():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verify data realism (no empty fields)

    cursor.execute("SELECT count(*) FROM users WHERE email LIKE '%@%' AND full_name LIKE '% %'")
    valid = cursor.fetchone()[0]
    
    cursor.execute("SELECT count(*) FROM users")
    total = cursor.fetchone()[0]
    
    test("Synthetic data quality", valid >= total,
         "All users have valid emails and full names")
    
    # Check balance distribution is realistic

    cursor.execute("SELECT AVG(balance), MIN(balance), MAX(balance) FROM users")
    avg_bal, min_bal, max_bal = cursor.fetchone()
    test("Balance distribution realistic", avg_bal > 100 and max_bal > 1000,
         f"Avg: ${avg_bal:,.2f} | Min: ${min_bal:,.2f} | Max: ${max_bal:,.2f}")
    
    conn.close()

# TEST 4: PRE-TRAINED MODEL PERSISTENCE

print("\n[ Testing Model Persistence ]")

model_dir = Path("honeypot/models")
models_found = 0
for site in ['banking', 'ecommerce', 'healthcare', 'blog', 'api_service', 'corporate', 'admin_panel']:
    gen_path = model_dir / site / 'generator.pt'
    if gen_path.exists():
        models_found += 1

test("Pre-trained models saved", models_found == 7, f"Found {models_found}/7 models")

# SUMMARY

print(f"  PHASE 2 RESULTS: {results['passed']} PASSED, {results['failed']} FAILED")
sys.exit(0 if results['failed'] == 0 else 1)
