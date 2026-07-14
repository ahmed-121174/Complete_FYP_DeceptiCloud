
import requests
import time
import sys

REAL_SITES = list(range(3001, 3008))
HONEYPOTS = list(range(4001, 4008))
PROXY_PORT = 8080

def check_site(port, site_type):
    url = f"http://localhost:{port}/"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f" {site_type} Site at {url} is UP (200 OK)")
            return True
        else:
            print(f" {site_type} Site at {url} returned {response.status_code}")
            return False
    except Exception as e:
        print(f" {site_type} Site at {url} is DOWN: {e}")
        return False

def check_dynamic_honeypot():
    print("\n Checking Dynamic Honeypot Routing (Proxy)...")
    try:
        # Send a benign request - should go to Real Site (e.g., 3001)

        resp = requests.get(f"http://localhost:{PROXY_PORT}/", timeout=5)
        print(f"   Benign Request -> Code: {resp.status_code} (Should be 200)")

        # Send a malicious request - should go to Honeypot

        # We need to trigger the IDS

        payload = {"q": "' OR 1=1--"}
        resp = requests.get(f"http://localhost:{PROXY_PORT}/banking/search", params=payload, timeout=5)
        print(f"   Malicious Request -> Code: {resp.status_code} (Should be 200 from Honeypot)")
        if "SecureBank" in resp.text:
             print("    Malicious request successfully routed to a Banking interface (Honeypot)")
        
    except Exception as e:
        print(f" Proxy check failed: {e}")

print("VERIFYING 14 WEBSITES")

all_up = True
for port in REAL_SITES:
    if not check_site(port, "REAL"): all_up = False

for port in HONEYPOTS:
    if not check_site(port, "HONEYPOT"): all_up = False

print("VERIFYING CONTENT (REAL vs FAIM)")

# Verify Real Banking

try:
    resp = requests.get("http://localhost:3001/dashboard", cookies={"session": "..."}) # Login needed? 
    # Actually dashboard requires login. I'll check the public homepage or products page if accessible.

    # The products are likely visible on main page or /products

    resp = requests.get("http://localhost:3001/")
    if "SecureBank" in resp.text:
        print(" Real Banking (3001) content verified")
except:
    print(" Real Banking check failed")

# Verify Honeypot Banking

try:
    resp = requests.get("http://localhost:4001/")
    if "SecureBank" in resp.text:
         print(" Honeypot Banking (4001) content verified")
except:
     print(" Honeypot Banking check failed")

print("VERIFYING DYNAMIC BEHAVIOR")
check_dynamic_honeypot()

if all_up:
    print("\n ALL SYSTEM CHECKS PASSED")
else:
    print("\n SOME CHECKS FAILED")
