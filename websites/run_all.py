#!/usr/bin/env python3
"""
Launch all 14 websites (7 real + 7 honeypot clones) on localhost.
Each site uses the same UI but different databases.

Real sites:     ports 3001–3007
Honeypot sites: ports 4001–4007
"""

import multiprocessing
import sys
import os
from pathlib import Path

# Add parent to path for shared imports

sys.path.insert(0, str(Path(__file__).parent))
from shared.site_factory import create_app
from shared.db_seeder import seed_all

# SITE CONFIGURATIONS

DB_DIR = Path(__file__).parent / 'databases'

SITES = [
    # REAL SITES (ports 3001–3007)

    {
        'name': 'SecureBank',
        'type': 'banking',
        'is_honeypot': False,
        'db_path': str(DB_DIR / 'banking_real.db'),
        'port': 3001,
        'theme_color': '#1a5276',
        'tagline': 'Your Trusted Financial Partner',
        'icon': '',
        'items_label': 'Products',
    },
    {
        'name': 'MegaStore',
        'type': 'ecommerce',
        'is_honeypot': False,
        'db_path': str(DB_DIR / 'ecommerce_real.db'),
        'port': 3002,
        'theme_color': '#e67e22',
        'tagline': 'Shop Smart. Shop MegaStore.',
        'icon': '',
        'items_label': 'Products',
    },
    {
        'name': 'MedClinic',
        'type': 'healthcare',
        'is_honeypot': False,
        'db_path': str(DB_DIR / 'healthcare_real.db'),
        'port': 3003,
        'theme_color': '#27ae60',
        'tagline': 'Your Health, Our Priority',
        'icon': '',
        'items_label': 'Services',
    },
    {
        'name': 'TechBlog',
        'type': 'blog',
        'is_honeypot': False,
        'db_path': str(DB_DIR / 'blog_real.db'),
        'port': 3004,
        'theme_color': '#8e44ad',
        'tagline': 'Code. Learn. Build.',
        'icon': '',
        'items_label': 'Articles',
    },
    {
        'name': 'DataAPI',
        'type': 'api_service',
        'is_honeypot': False,
        'db_path': str(DB_DIR / 'api_service_real.db'),
        'port': 3005,
        'theme_color': '#2980b9',
        'tagline': 'Powerful APIs for Modern Apps',
        'icon': '',
        'items_label': 'Endpoints',
    },
    {
        'name': 'NexaGen Corp',
        'type': 'corporate',
        'is_honeypot': False,
        'db_path': str(DB_DIR / 'corporate_real.db'),
        'port': 3006,
        'theme_color': '#34495e',
        'tagline': 'Innovation Through Technology',
        'icon': '',
        'items_label': 'Services',
    },
    {
        'name': 'SysNet Admin',
        'type': 'admin_panel',
        'is_honeypot': False,
        'db_path': str(DB_DIR / 'admin_panel_real.db'),
        'port': 3007,
        'theme_color': '#c0392b',
        'tagline': 'Infrastructure Management Portal',
        'icon': '',
        'items_label': 'Resources',
    },

    # HONEYPOT CLONES (ports 4001–4007)

    {
        'name': 'SecureBank',
        'type': 'banking',
        'is_honeypot': True,
        'db_path': str(DB_DIR / 'banking_honeypot.db'),
        'port': 4001,
        'theme_color': '#1a5276',
        'tagline': 'Your Trusted Financial Partner',
        'icon': '',
        'items_label': 'Products',
    },
    {
        'name': 'MegaStore',
        'type': 'ecommerce',
        'is_honeypot': True,
        'db_path': str(DB_DIR / 'ecommerce_honeypot.db'),
        'port': 4002,
        'theme_color': '#e67e22',
        'tagline': 'Shop Smart. Shop MegaStore.',
        'icon': '',
        'items_label': 'Products',
    },
    {
        'name': 'MedClinic',
        'type': 'healthcare',
        'is_honeypot': True,
        'db_path': str(DB_DIR / 'healthcare_honeypot.db'),
        'port': 4003,
        'theme_color': '#27ae60',
        'tagline': 'Your Health, Our Priority',
        'icon': '',
        'items_label': 'Services',
    },
    {
        'name': 'TechBlog',
        'type': 'blog',
        'is_honeypot': True,
        'db_path': str(DB_DIR / 'blog_honeypot.db'),
        'port': 4004,
        'theme_color': '#8e44ad',
        'tagline': 'Code. Learn. Build.',
        'icon': '',
        'items_label': 'Articles',
    },
    {
        'name': 'DataAPI',
        'type': 'api_service',
        'is_honeypot': True,
        'db_path': str(DB_DIR / 'api_service_honeypot.db'),
        'port': 4005,
        'theme_color': '#2980b9',
        'tagline': 'Powerful APIs for Modern Apps',
        'icon': '',
        'items_label': 'Endpoints',
    },
    {
        'name': 'NexaGen Corp',
        'type': 'corporate',
        'is_honeypot': True,
        'db_path': str(DB_DIR / 'corporate_honeypot.db'),
        'port': 4006,
        'theme_color': '#34495e',
        'tagline': 'Innovation Through Technology',
        'icon': '',
        'items_label': 'Services',
    },
    {
        'name': 'SysNet Admin',
        'type': 'admin_panel',
        'is_honeypot': True,
        'db_path': str(DB_DIR / 'admin_panel_honeypot.db'),
        'port': 4007,
        'theme_color': '#c0392b',
        'tagline': 'Infrastructure Management Portal',
        'icon': '',
        'items_label': 'Resources',
    },
]

def run_site(config):
    """Run a single Flask site in its own process."""
    app = create_app(config)
    label = " HONEYPOT" if config['is_honeypot'] else " REAL"
    print(f"  {label} {config['name']:20s} ({config['type']:15s}) → http://localhost:{config['port']}")
    app.run(host='0.0.0.0', port=config['port'], debug=False, use_reloader=False)

def main():
    print("  AI-DRIVEN CYBER DECEPTION SYSTEM — LAUNCHING ALL WEBSITES")

    # Step 1: Seed databases

    print("\n Seeding databases...")
    seed_all()

    # Step 2: Launch all sites

    print(f"\n Launching {len(SITES)} websites...\n")
    print(f"  {'Label':28s} {'Site':20s} {'Type':15s}   URL")
    print(f"  {''*28} {''*20} {''*15}   {''*25}")

    processes = []
    for config in SITES:
        p = multiprocessing.Process(target=run_site, args=(config,))
        p.daemon = True
        p.start()
        processes.append(p)

    print(f"\n{'='*70}")
    print(f"  ALL {len(SITES)} SITES RUNNING!")
    print(f"  Real sites:     http://localhost:3001 — http://localhost:3007")
    print(f"  Honeypot clones: http://localhost:4001 — http://localhost:4007")
    print(f"  Press Ctrl+C to stop all sites")
    print(f"{'='*70}\n")

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        print("\n Shutting down all websites...")
        for p in processes:
            p.terminate()
        print(" All sites stopped.")

if __name__ == '__main__':
    main()
