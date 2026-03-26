import os
import time
import requests
from duckduckgo_search import DDGS

COMPONENTS = [
    "Aruba CX 6400",
    "Aruba CX 6400 Management",
    "Aruba CX 6300M",
    "Aruba 50G Stacking Cable",
    "Aruba AP-515",
    "Aruba 7010",
    "Aruba SD-Branch 1000",
    "Aruba J9150D SFP+",
    "Cisco Catalyst 9500",
    "C9500 10G Module",
    "C9500 Power Supply",
    "Cisco Catalyst 9300-48P",
    "StackWise-480",
    "715W PSU",
    "Cisco 9120AXI",
    "Cisco 9800-L",
    "DNA Licenses",
    "Cisco Firepower 1140",
    "Threat/URL Filtering",
    "Cisco 8841",
    "CUCM / Webex",
    "User Licenses",
    "Cisco ISR 4331",
    "Cisco DNA",
    "Cisco SFP-10G-SR",
    "Cat6 24-Port",
    "Cat6 Ethernet",
    "42U Equipment Rack",
    "APC Smart-UPS"
]

STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static', 'components')
os.makedirs(STATIC_DIR, exist_ok=True)

def download_image(name, url):
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        if r.status_code == 200:
            filename = name.replace(" ", "_").replace("/", "_").replace("-", "_").lower() + ".png"
            filepath = os.path.join(STATIC_DIR, filename)
            with open(filepath, 'wb') as f:
                f.write(r.content)
            print(f"[OK] Saved {name} -> {filename}")
            return True
        return False
    except:
        return False

with DDGS() as ddgs:
    for comp in COMPONENTS:
        filename = comp.replace(" ", "_").replace("/", "_").replace("-", "_").lower() + ".png"
        if os.path.exists(os.path.join(STATIC_DIR, filename)):
            print(f"[SKIP] {comp} already exists")
            continue
            
        print(f"Searching for {comp}...")
        try:
            hits = list(ddgs.images(comp + " networking", max_results=3))
            if not hits:
                hits = list(ddgs.images(comp, max_results=2))
            
            success = False
            for hit in hits:
                url = hit.get('image')
                if url and download_image(comp, url):
                    success = True
                    break
                    
            if not success:
               print(f"[FAIL] Could not download image for {comp}")
               
            time.sleep(1.0) # avoid ratelimit on DDGS
        except Exception as e:
            print(f"[ERROR] {comp}: {e}")
            time.sleep(2.0)
