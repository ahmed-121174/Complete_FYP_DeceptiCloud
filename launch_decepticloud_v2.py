#!/usr/bin/env python3
"""
DeceptiCloud v2.0 - Enhanced Launch Script
Includes database initialization and optional Wazuh integration
"""

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

# Import database service
from database.db_service import get_db_service

# BANNER
CYAN = '\033[96m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
MAGENTA = '\033[95m'
BOLD = '\033[1m'
DIM = '\033[2m'
RESET = '\033[0m'

BANNER = f"""{CYAN}{BOLD}
╔══════════════════════════════════════════════════════════════╗
║                  DeceptiCloud v2.0                           ║
║         AI-Driven Cyber Deception Platform                   ║
╚══════════════════════════════════════════════════════════════╝
{RESET}{DIM}FYP-II Project | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}
"""

def print_status(icon, msg, color=RESET):
    print(f"  {icon} {color}{msg}{RESET}")

def print_section(title):
    print(f"\n{CYAN}{BOLD}═══ {title} ═══{RESET}")


# STEP 0: INITIALIZE DATABASE
def initialize_database():
    print_section("INITIALIZING DATABASE")
    try:
        db = get_db_service()
        print_status("✓", "Database initialized successfully", GREEN)
        
        # Check if migration is needed
        attack_log = BASE_DIR / 'proxy' / 'logs' / 'proxy_attacks.jsonl'
        if attack_log.exists():
            stats = db.get_attack_stats()
            if stats['total'] == 0:
                print_status("ℹ", "Migrating existing attack data...", YELLOW)
                subprocess.run([sys.executable, str(BASE_DIR / 'database' / 'migrate_existing_data.py')])
            else:
                print_status("ℹ", f"Database contains {stats['total']} attacks", GREEN)
        
        return True
    except Exception as e:
        print_status("✗", f"Database initialization failed: {e}", RED)
        return False


# STEP 1: SEED DATABASES
def seed_databases():
    print_section("SEEDING WEBSITE DATABASES")
    try:
        from shared.db_seeder import seed_all
        seed_all()
        print_status("✓", "All website databases seeded successfully", GREEN)
    except Exception as e:
        print_status("⚠", f"Database seeding warning: {e}", YELLOW)


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
        {'name': 'SecureBank',    'type': 'banking',       'is_honeypot': False, 'db_path': str(DB_DIR / 'banking_real.db'),       'port': 3001, 'theme_color': '#1a5276', 'tagline': 'Your Trusted Financial Partner',    'icon': '🏦', 'items_label': 'Products'},
        {'name': 'MegaStore',     'type': 'ecommerce',     'is_honeypot': False, 'db_path': str(DB_DIR / 'ecommerce_real.db'),     'port': 3002, 'theme_color': '#e67e22', 'tagline': 'Shop Smart. Shop MegaStore.',       'icon': '🛒', 'items_label': 'Products'},
        {'name': 'MedClinic',     'type': 'healthcare',    'is_honeypot': False, 'db_path': str(DB_DIR / 'healthcare_real.db'),    'port': 3003, 'theme_color': '#27ae60', 'tagline': 'Your Health, Our Priority',         'icon': '🏥', 'items_label': 'Services'},
        {'name': 'TechBlog',      'type': 'blog',          'is_honeypot': False, 'db_path': str(DB_DIR / 'blog_real.db'),          'port': 3004, 'theme_color': '#8e44ad', 'tagline': 'Code. Learn. Build.',               'icon': '📝', 'items_label': 'Articles'},
        {'name': 'DataAPI',       'type': 'api_service',   'is_honeypot': False, 'db_path': str(DB_DIR / 'api_service_real.db'),   'port': 3005, 'theme_color': '#2980b9', 'tagline': 'Powerful APIs for Modern Apps',     'icon': '🔌', 'items_label': 'Endpoints'},
        {'name': 'NexaGen Corp',  'type': 'corporate',     'is_honeypot': False, 'db_path': str(DB_DIR / 'corporate_real.db'),     'port': 3006, 'theme_color': '#34495e', 'tagline': 'Innovation Through Technology',    'icon': '🏢', 'items_label': 'Services'},
        {'name': 'SysNet Admin',  'type': 'admin_panel',   'is_honeypot': False, 'db_path': str(DB_DIR / 'admin_panel_real.db'),   'port': 3007, 'theme_color': '#c0392b', 'tagline': 'Infrastructure Management Portal', 'icon': '⚙️',  'items_label': 'Resources'},
        # Honeypot Clones (4001-4007)
        {'name': 'SecureBank',    'type': 'banking',       'is_honeypot': True,  'db_path': str(DB_DIR / 'banking_honeypot.db'),       'port': 4001, 'theme_color': '#1a5276', 'tagline': 'Your Trusted Financial Partner',    'icon': '🏦', 'items_label': 'Products'},
        {'name': 'MegaStore',     'type': 'ecommerce',     'is_honeypot': True,  'db_path': str(DB_DIR / 'ecommerce_honeypot.db'),     'port': 4002, 'theme_color': '#e67e22', 'tagline': 'Shop Smart. Shop MegaStore.',       'icon': '🛒', 'items_label': 'Products'},
        {'name': 'MedClinic',     'type': 'healthcare',    'is_honeypot': True,  'db_path': str(DB_DIR / 'healthcare_honeypot.db'),    'port': 4003, 'theme_color': '#27ae60', 'tagline': 'Your Health, Our Priority',         'icon': '🏥', 'items_label': 'Services'},
        {'name': 'TechBlog',      'type': 'blog',          'is_honeypot': True,  'db_path': str(DB_DIR / 'blog_honeypot.db'),          'port': 4004, 'theme_color': '#8e44ad', 'tagline': 'Code. Learn. Build.',               'icon': '📝', 'items_label': 'Articles'},
        {'name': 'DataAPI',       'type': 'api_service',   'is_honeypot': True,  'db_path': str(DB_DIR / 'api_service_honeypot.db'),   'port': 4005, 'theme_color': '#2980b9', 'tagline': 'Powerful APIs for Modern Apps',     'icon': '🔌', 'items_label': 'Endpoints'},
        {'name': 'NexaGen Corp',  'type': 'corporate',     'is_honeypot': True,  'db_path': str(DB_DIR / 'corporate_honeypot.db'),     'port': 4006, 'theme_color': '#34495e', 'tagline': 'Innovation Through Technology',    'icon': '🏢', 'items_label': 'Services'},
        {'name': 'SysNet Admin',  'type': 'admin_panel',   'is_honeypot': True,  'db_path': str(DB_DIR / 'admin_panel_honeypot.db'),   'port': 4007, 'theme_color': '#c0392b', 'tagline': 'Infrastructure Management Portal', 'icon': '⚙️',  'items_label': 'Resources'},
    ]

    processes = []
    for config in SITES:
        p = multiprocessing.Process(target=run_website, args=(config,), daemon=True)
        p.start()
        processes.append(p)
        label = f"{'🍯 HONEYPOT' if config['is_honeypot'] else '✓ REAL':12}"
        print_status(label, f"{config['name']:16} → http://localhost:{config['port']}", 
                     MAGENTA if config['is_honeypot'] else GREEN)

    time.sleep(1)
    print_status("✓", f"All {len(SITES)} websites running!", GREEN)
    return processes


# STEP 3: LAUNCH ML DETECTION API
def launch_ml_api():
    print_section("LAUNCHING ML DETECTION API")
    
    # Use venv Python if available
    venv_python = BASE_DIR / 'venv' / 'bin' / 'python3'
    python_exec = str(venv_python) if venv_python.exists() else sys.executable
    
    if venv_python.exists():
        print_status("ℹ", "Using virtual environment Python", DIM)
    
    proc = subprocess.Popen(
        [python_exec, str(BASE_DIR / 'ml_pipeline' / 'model_api.py')],
        cwd=str(BASE_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    print_status("ℹ", "Waiting for TensorFlow/Keras models to load (10-20s)...", YELLOW)
    
    import urllib.request
    started = False
    for _ in range(30):
        if proc.poll() is not None:
            # Process died, check stderr
            stderr = proc.stderr.read().decode('utf-8', errors='ignore')
            if 'Address already in use' in stderr:
                print_status("⚠", "Port 5000 already in use, waiting...", YELLOW)
                time.sleep(2)
                return None  # Don't restart immediately
            break
        try:
            with urllib.request.urlopen(f"{ML_API_URL}/api/health", timeout=1) as response:
                if response.getcode() == 200:
                    started = True
                    break
        except Exception:
            time.sleep(1)
            
    if started:
        print_status("✓", f"ML API active → {ML_API_URL}", GREEN)
    else:
        if proc.poll() is not None:
            stderr = proc.stderr.read().decode('utf-8', errors='ignore')
            if stderr:
                print_status("⚠", f"ML API failed: {stderr[:100]}", RED)
        else:
            print_status("⚠", "ML API failed to start or timed out", RED)
        
    return proc


# STEP 4: LAUNCH ROUTING PROXY
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
        print_status("✓", f"Routing Proxy running → http://localhost:{PROXY_PORT}", GREEN)
    else:
        print_status("⚠", "Proxy may have startup issues (check logs)", YELLOW)
    return proc


# STEP 5: LAUNCH DASHBOARD
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
        print_status("✓", f"Dashboard running → http://localhost:{DASHBOARD_PORT}", GREEN)
    else:
        print_status("⚠", "Dashboard may have startup issues", YELLOW)
    return proc


# STEP 6: LAUNCH WAZUH LOG INGESTION (OPTIONAL)
def launch_wazuh_ingestion():
    print_section("WAZUH LOG INGESTION (OPTIONAL)")
    
    # Check if Wazuh Docker stack is running
    try:
        import subprocess as _sp
        result = _sp.run(
            ['sg', 'docker', '-c', 'docker ps --format {{.Names}}'],
            capture_output=True, text=True, timeout=5
        )
        wazuh_running = 'single-node-wazuh.manager' in result.stdout
    except Exception:
        wazuh_running = False
    
    if not wazuh_running:
        print_status("ℹ", "Wazuh Docker stack not running - skipping log ingestion", YELLOW)
        print_status("ℹ", "Start with: bash wazuh-docker/start_wazuh.sh", DIM)
        return None
    
    # Start log ingestion service
    proc = subprocess.Popen(
        [sys.executable, str(BASE_DIR / 'wazuh' / 'log_ingestion_service.py')],
        cwd=str(BASE_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(1)
    if proc.poll() is None:
        print_status("✓", "Wazuh log ingestion service started", GREEN)
    else:
        print_status("⚠", "Wazuh log ingestion failed to start", YELLOW)
    
    return proc


# STEP 7: LAUNCH ADAPTIVE LEARNING ENGINE
def launch_adaptive_engine():
    print_section("LAUNCHING ADAPTIVE LEARNING ENGINE")
    
    venv_python = BASE_DIR / 'venv' / 'bin' / 'python3'
    python_exec = str(venv_python) if venv_python.exists() else sys.executable
    
    proc = subprocess.Popen(
        [python_exec, str(BASE_DIR / 'adaptive_engine' / 'engine.py')],
        cwd=str(BASE_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(2)
    if proc.poll() is None:
        print_status("✓", "Adaptive Learning Engine running", GREEN)
        print_status("ℹ", "Wazuh consumer + drift detection + auto-retraining active", DIM)
    else:
        print_status("⚠", "Adaptive Engine startup issue (non-critical)", YELLOW)
    return proc


# PROCESS WATCHDOG
def _watchdog(named_procs, website_procs):
    """Background thread that monitors critical processes and restarts them if they crash"""
    restart_cooldown = {}  # Track last restart time for each process
    
    while True:
        time.sleep(10)
        current_time = time.time()
        
        for name, proc in list(named_procs.items()):
            if proc and proc.poll() is not None:
                # Check cooldown to avoid rapid restarts
                last_restart = restart_cooldown.get(name, 0)
                if current_time - last_restart < 30:  # 30 second cooldown
                    continue
                
                print(f"\n  {RED}⚠ {name} crashed (exit code {proc.returncode}). Restarting...{RESET}")
                restart_cooldown[name] = current_time
                
                if name == 'ML API':
                    named_procs[name] = launch_ml_api()
                elif name == 'Proxy':
                    named_procs[name] = launch_proxy()
                elif name == 'Dashboard':
                    named_procs[name] = launch_dashboard()
                elif name == 'Adaptive Engine':
                    named_procs[name] = launch_adaptive_engine()
                elif name == 'Wazuh Ingestion':
                    named_procs[name] = launch_wazuh_ingestion()


# MAIN
def main():
    print(BANNER)

    # Initialize database
    if not initialize_database():
        print(f"\n{RED}✗ Database initialization failed. Exiting.{RESET}\n")
        sys.exit(1)

    # Seed website databases
    seed_databases()

    # Launch websites
    website_processes = launch_websites()

    # Launch ML API
    ml_proc = launch_ml_api()

    # Launch proxy
    proxy_proc = launch_proxy()

    # Launch dashboard
    dashboard_proc = launch_dashboard()

    # Launch Wazuh ingestion (optional)
    wazuh_proc = launch_wazuh_ingestion()

    # Launch Adaptive Learning Engine
    ale_proc = launch_adaptive_engine()

    # Start watchdog thread
    named_procs = {
        'ML API': ml_proc,
        'Proxy': proxy_proc,
        'Dashboard': dashboard_proc,
        'Wazuh Ingestion': wazuh_proc,
        'Adaptive Engine': ale_proc,
    }
    watchdog_thread = threading.Thread(target=_watchdog, args=(named_procs, website_processes), daemon=True)
    watchdog_thread.start()

    # Summary
    print_section("SYSTEM READY")
    print(f"  {BOLD}✓ DECEPTICLOUD IS FULLY OPERATIONAL{RESET}")
    print()
    print(f"  {GREEN}Dashboard:{RESET}     http://localhost:{DASHBOARD_PORT}")
    print(f"  {GREEN}ML API:{RESET}        {ML_API_URL}")
    print(f"  {GREEN}Proxy:{RESET}         http://localhost:{PROXY_PORT}")
    print(f"  {GREEN}Real Sites:{RESET}    http://localhost:3001 to :3007")
    print(f"  {MAGENTA}Honeypots:{RESET}     http://localhost:4001 to :4007")
    print(f"  {YELLOW}Login:{RESET}         admin / DeceptiCloud")
    print()
    print(f"  {CYAN}Database:{RESET}      {BASE_DIR / 'database' / 'decepticloud.db'}")
    if wazuh_proc:
        print(f"  {CYAN}Wazuh:{RESET}         Integrated ✓")
    print()
    print(f"\n  {DIM}Press Ctrl+C to shutdown the entire system{RESET}\n")

    # Wait for shutdown
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}⚠ Shutting down DeceptiCloud...{RESET}")
        for proc in named_procs.values():
            if proc:
                proc.terminate()
        for p in website_processes:
            p.terminate()
        print(f"  {GREEN}✓ All services stopped. Goodbye!{RESET}\n")


if __name__ == '__main__':
    main()
