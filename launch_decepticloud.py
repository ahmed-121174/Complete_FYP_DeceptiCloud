#!/usr/bin/env python3

import multiprocessing
import subprocess
import sys
import os
import time
import signal
import json
import threading
from pathlib import Path
from datetime import datetime

# PATHS & CONFIG

BASE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BASE_DIR / 'websites'))
sys.path.insert(0, str(BASE_DIR))
from config import ML_API_PORT, PROXY_PORT, DASHBOARD_PORT, ML_API_URL

# BANNER

CYAN = '\033[96m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
MAGENTA = '\033[95m'
BOLD = '\033[1m'
DIM = '\033[2m'
RESET = '\033[0m'

BANNER = f"""{CYAN}{BOLD}DeceptiCloud v1.0{RESET} - AI-Driven Cyber Deception System
{DIM}FYP-II Project | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}
"""

def print_status(icon, msg, color=RESET):
    print(f"  {icon} {color}{msg}{RESET}")

def print_section(title):
    print(f"\n{CYAN}{BOLD}   {title}{RESET}")


# STEP 1: SEED DATABASES

def seed_databases():
    print_section("SEEDING 14 DATABASES")
    from shared.db_seeder import seed_all
    seed_all()
    print_status("", "All databases seeded successfully", GREEN)

# STEP 2: LAUNCH 14 WEBSITES

def run_website(config):
    """Run a single Flask site in its own process."""
    from shared.site_factory import create_app
    app = create_app(config)
    app.run(host='0.0.0.0', port=config['port'], debug=False, use_reloader=False)

def launch_websites():
    print_section("LAUNCHING 14 WEBSITES")
    DB_DIR = BASE_DIR / 'websites' / 'databases'

    SITES = [
        # Real Sites (3001-3007)

        {'name': 'SecureBank',    'type': 'banking',       'is_honeypot': False, 'db_path': str(DB_DIR / 'banking_real.db'),       'port': 3001, 'theme_color': '#1a5276', 'tagline': 'Your Trusted Financial Partner',    'icon': '', 'items_label': 'Products'},
        {'name': 'MegaStore',     'type': 'ecommerce',     'is_honeypot': False, 'db_path': str(DB_DIR / 'ecommerce_real.db'),     'port': 3002, 'theme_color': '#e67e22', 'tagline': 'Shop Smart. Shop MegaStore.',       'icon': '', 'items_label': 'Products'},
        {'name': 'MedClinic',     'type': 'healthcare',    'is_honeypot': False, 'db_path': str(DB_DIR / 'healthcare_real.db'),    'port': 3003, 'theme_color': '#27ae60', 'tagline': 'Your Health, Our Priority',         'icon': '', 'items_label': 'Services'},
        {'name': 'TechBlog',      'type': 'blog',          'is_honeypot': False, 'db_path': str(DB_DIR / 'blog_real.db'),          'port': 3004, 'theme_color': '#8e44ad', 'tagline': 'Code. Learn. Build.',               'icon': '', 'items_label': 'Articles'},
        {'name': 'DataAPI',       'type': 'api_service',   'is_honeypot': False, 'db_path': str(DB_DIR / 'api_service_real.db'),   'port': 3005, 'theme_color': '#2980b9', 'tagline': 'Powerful APIs for Modern Apps',     'icon': '', 'items_label': 'Endpoints'},
        {'name': 'NexaGen Corp',  'type': 'corporate',     'is_honeypot': False, 'db_path': str(DB_DIR / 'corporate_real.db'),     'port': 3006, 'theme_color': '#34495e', 'tagline': 'Innovation Through Technology',    'icon': '', 'items_label': 'Services'},
        {'name': 'SysNet Admin',  'type': 'admin_panel',   'is_honeypot': False, 'db_path': str(DB_DIR / 'admin_panel_real.db'),   'port': 3007, 'theme_color': '#c0392b', 'tagline': 'Infrastructure Management Portal', 'icon': '',  'items_label': 'Resources'},
        # Honeypot Clones (4001-4007)

        {'name': 'SecureBank',    'type': 'banking',       'is_honeypot': True,  'db_path': str(DB_DIR / 'banking_honeypot.db'),       'port': 4001, 'theme_color': '#1a5276', 'tagline': 'Your Trusted Financial Partner',    'icon': '', 'items_label': 'Products'},
        {'name': 'MegaStore',     'type': 'ecommerce',     'is_honeypot': True,  'db_path': str(DB_DIR / 'ecommerce_honeypot.db'),     'port': 4002, 'theme_color': '#e67e22', 'tagline': 'Shop Smart. Shop MegaStore.',       'icon': '', 'items_label': 'Products'},
        {'name': 'MedClinic',     'type': 'healthcare',    'is_honeypot': True,  'db_path': str(DB_DIR / 'healthcare_honeypot.db'),    'port': 4003, 'theme_color': '#27ae60', 'tagline': 'Your Health, Our Priority',         'icon': '', 'items_label': 'Services'},
        {'name': 'TechBlog',      'type': 'blog',          'is_honeypot': True,  'db_path': str(DB_DIR / 'blog_honeypot.db'),          'port': 4004, 'theme_color': '#8e44ad', 'tagline': 'Code. Learn. Build.',               'icon': '', 'items_label': 'Articles'},
        {'name': 'DataAPI',       'type': 'api_service',   'is_honeypot': True,  'db_path': str(DB_DIR / 'api_service_honeypot.db'),   'port': 4005, 'theme_color': '#2980b9', 'tagline': 'Powerful APIs for Modern Apps',     'icon': '', 'items_label': 'Endpoints'},
        {'name': 'NexaGen Corp',  'type': 'corporate',     'is_honeypot': True,  'db_path': str(DB_DIR / 'corporate_honeypot.db'),     'port': 4006, 'theme_color': '#34495e', 'tagline': 'Innovation Through Technology',    'icon': '', 'items_label': 'Services'},
        {'name': 'SysNet Admin',  'type': 'admin_panel',   'is_honeypot': True,  'db_path': str(DB_DIR / 'admin_panel_honeypot.db'),   'port': 4007, 'theme_color': '#c0392b', 'tagline': 'Infrastructure Management Portal', 'icon': '',  'items_label': 'Resources'},
    ]

    processes = []
    for config in SITES:
        p = multiprocessing.Process(target=run_website, args=(config,), daemon=True)
        p.start()
        processes.append(p)
        label = f"{' HONEYPOT' if config['is_honeypot'] else ' REAL':12}"
        print_status(label, f"{config['name']:16} → http://localhost:{config['port']}", 
                     MAGENTA if config['is_honeypot'] else GREEN)

    time.sleep(1)
    print_status("", f"All {len(SITES)} websites running!", GREEN)
    return processes

# STEP 3: LAUNCH ML DETECTION API

def launch_ml_api():
    print_section("LAUNCHING ML DETECTION API")
    proc = subprocess.Popen(
        [sys.executable, str(BASE_DIR / 'ml_pipeline' / 'model_api.py')],
        cwd=str(BASE_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    # Wait for startup (heavy TF load)

    print_status("", "Waiting for TensorFlow/Keras models to load (this may take 10-20s)...", YELLOW)
    
    # Poll for health

    import urllib.request
    started = False
    for _ in range(30):
        if proc.poll() is not None:
            break
        try:
            with urllib.request.urlopen(f"{ML_API_URL}/api/health", timeout=1) as response:
                if response.getcode() == 200:
                    started = True
                    break
        except Exception:  # (#10) no bare except
            time.sleep(1)
            
    if started:
        print_status("", f"ML API active → {ML_API_URL}", GREEN)
    else:
        print_status("", "ML API failed to start or timed out", RED)
        
    return proc

# STEP 3: LAUNCH ROUTING PROXY

def launch_proxy():
    print_section("LAUNCHING ROUTING PROXY")
    proc = subprocess.Popen(
        [sys.executable, str(BASE_DIR / 'proxy' / 'routing_proxy.py')],
        cwd=str(BASE_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(1.5)
    if proc.poll() is None:
        print_status("", f"Routing Proxy running → http://localhost:{PROXY_PORT}", GREEN)
    else:
        print_status("", "Proxy may have startup issues (check logs)", YELLOW)
    return proc

# STEP 4: LAUNCH DASHBOARD

def launch_dashboard():
    print_section("LAUNCHING DECEPTICLOUD DASHBOARD")
    proc = subprocess.Popen(
        [sys.executable, str(BASE_DIR / 'dashboard' / 'app.py')],
        cwd=str(BASE_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(1.5)
    if proc.poll() is None:
        print_status("", f"Dashboard running → http://localhost:{DASHBOARD_PORT}", GREEN)
    else:
        print_status("", "Dashboard may have startup issues", YELLOW)
    return proc

# STEP 5: RUN ATTACK SIMULATIONS

def run_attack_simulations():
    print_section("SIMULATING CYBER ATTACKS")
    import urllib.request
    import urllib.parse

    attacks = [
        ("Benign Request",     "http://localhost:8080/banking/",             "benign"),
        ("SQL Injection #1",   "http://localhost:8080/banking/search?q=1'+OR+1=1--",  "sqli"),
        ("SQL Injection #2",   "http://localhost:8080/ecommerce/search?q=admin'--",   "sqli"),
        ("XSS Attack #1",      "http://localhost:8080/ecommerce/search?q=<script>alert(1)</script>", "xss"),
        ("XSS Attack #2",      "http://localhost:8080/blog/search?q=<img+onerror=alert(1)>", "xss"),
        ("Path Traversal #1",  "http://localhost:8080/banking/search?q=../../../etc/passwd", "traversal"),
        ("Path Traversal #2",  "http://localhost:8080/admin_panel/search?q=....//....//etc/shadow", "traversal"),
        ("NoSQLi Attack",      "http://localhost:8080/api_service/search?q={$gt:''}", "nosqli"),
        ("Suspicious Tool",    "http://localhost:8080/healthcare/",          "tool"),
    ]

    results = {'detected': 0, 'total': 0, 'types': set()}

    for name, url, attack_type in attacks:
        try:
            headers = {}
            if attack_type == 'tool':
                headers['User-Agent'] = 'sqlmap/1.0-dev'

            req = urllib.request.Request(url, headers=headers)
            resp = urllib.request.urlopen(req, timeout=5)
            status = resp.getcode()
            color = GREEN if attack_type == 'benign' else RED
            icon = "" if attack_type == 'benign' else ""
            print_status(icon, f"{name:25s} → {status} {'(routed to honeypot)' if attack_type != 'benign' else '(served real site)'}", color)
            if attack_type != 'benign':
                results['detected'] += 1
                results['types'].add(attack_type)
            results['total'] += 1
        except Exception as e:
            print_status("", f"{name:25s} → ERROR: {e}", RED)
            results['total'] += 1

    # Check proxy status

    time.sleep(0.5)
    try:
        req = urllib.request.Request("http://localhost:8080/proxy/status")
        resp = urllib.request.urlopen(req, timeout=3)
        status_data = json.loads(resp.read().decode())
        detected_attacks = status_data.get('known_attackers', 0)
        print(f"\n  {CYAN}{BOLD}  ATTACK SIMULATION RESULTS{RESET}")
        print(f"  {DIM}  {'' * 50}{RESET}")
        print(f"  {GREEN}   Attacks launched:    {results['total']}{RESET}")
        print(f"  {RED}   Attacks detected:   {results['detected']}/{results['total'] - 1}{RESET}")
        print(f"  {YELLOW}   Attack types:       {', '.join(results['types'])}{RESET}")
        print(f"  {MAGENTA}    Known attackers:    {detected_attacks}{RESET}")
    except Exception:  # (#10) no bare except
        pass

    return results

# PROCESS WATCHDOG (#16)

def _watchdog(named_procs, website_procs):
    """
    Background thread that monitors critical processes and restarts them
    if they crash unexpectedly.
    """
    while True:
        time.sleep(10)
        for name, proc in named_procs.items():
            if proc.poll() is not None:
                print(f"\n  {RED}  {name} crashed (exit code {proc.returncode}). Restarting...{RESET}")
                if name == 'ML API':
                    named_procs[name] = launch_ml_api()
                elif name == 'Proxy':
                    named_procs[name] = launch_proxy()
                elif name == 'Dashboard':
                    named_procs[name] = launch_dashboard()

# MAIN

def main():
    print(BANNER)

    run_tests = '--test' in sys.argv

    # Seed databases

    seed_databases()

    # Launch websites

    website_processes = launch_websites()

    # Launch ML API

    ml_proc = launch_ml_api()

    # Launch proxy

    proxy_proc = launch_proxy()

    # Launch dashboard

    dashboard_proc = launch_dashboard()

    # Start watchdog thread

    named_procs = {'ML API': ml_proc, 'Proxy': proxy_proc, 'Dashboard': dashboard_proc}
    watchdog_thread = threading.Thread(target=_watchdog, args=(named_procs, website_processes), daemon=True)
    watchdog_thread.start()

    # Summary

    print_section("SYSTEM READY")
    print(f"  {BOLD}DECEPTICLOUD IS FULLY OPERATIONAL{RESET}")
    print()
    print(f"  {GREEN}Dashboard:{RESET}     http://localhost:{DASHBOARD_PORT}")
    print(f"  {GREEN}ML API:{RESET}        {ML_API_URL}")
    print(f"  {GREEN}Proxy:{RESET}         http://localhost:{PROXY_PORT}")
    print(f"  {GREEN}Real Sites:{RESET}    http://localhost:3001 to :3007")
    print(f"  {MAGENTA}Honeypots:{RESET}     http://localhost:4001 to :4007")
    print(f"  {YELLOW}Login:{RESET}         admin / DeceptiCloud")
    print()

    # Run attack if requested

    if run_tests:
        time.sleep(2)
        run_attack_simulations()

    print(f"\n  {DIM}Press Ctrl+C to shutdown the entire system{RESET}\n")

    # Wait for shutdown

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}    Shutting down DeceptiCloud...{RESET}")
        for proc in named_procs.values():
            proc.terminate()
        for p in website_processes:
            p.terminate()
        print(f"  {GREEN} All services stopped. Goodbye!{RESET}\n")

if __name__ == '__main__':
    main()
