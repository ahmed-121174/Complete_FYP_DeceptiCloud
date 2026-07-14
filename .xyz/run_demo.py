#!/usr/bin/env python3
"""
DeceptiCloud Phase 2 Demo Launcher
==================================

This script launches the full DeceptiCloud system with all Phase 2 features enabled:
- 14 Website Instances (7 Real, 7 Honeypot)
- Generative AI (GAN) Synthetic Data
- LLM Adaptive Response Engine
- Behavioral Fingerprinting
- Real-time Threat Dashboard

Usage:
    ./run_demo.py
"""

import os
import sys
import subprocess
import time

def main():
    print("  DECEPTICLOUD PHASE 2 — DEMONSTRATION LAUNCHER")
    print("\n[+] Checking environment...")

    # Check for venv

    venv_python = os.path.join(os.getcwd(), 'venv', 'bin', 'python')
    if not os.path.exists(venv_python):
        print("[-] Virtual environment not found. Please run ./setup.sh first.")
        sys.exit(1)
    
    print("[+] Environment OK. Launching system with AI modules...")
    print("    - Generative Adversarial Networks (GANs): ENABLED")
    print("    - Large Language Models (LLMs): ENABLED")
    print("    - Behavioral Fingerprinting: ENABLED")
    print("\n[!] Press Ctrl+C to stop all services.\n")
    time.sleep(2)

    try:
        # Launch browser in background after 15 seconds

        import threading
        import webbrowser
        def open_browser():
            time.sleep(15)
            print("[+] Opening Dashboard and SecureBank in browser...")
            webbrowser.open('http://localhost:9000')
            webbrowser.open('http://localhost:3001')
        
        threading.Thread(target=open_browser, daemon=True).start()

        # Run the main launcher with --gan flag

        subprocess.run([venv_python, 'launch_decepticloud.py', '--gan'], check=True)
    except KeyboardInterrupt:
        print("\n\n[!] Stopping DeceptiCloud...")
    except Exception as e:
        print(f"\n[-] Error: {e}")

if __name__ == '__main__':
    main()
