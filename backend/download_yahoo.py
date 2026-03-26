import requests
import json
import urllib.parse
from bs4 import BeautifulSoup
import os

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

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}

def get_image_yahoo(query):
    url = f"https://images.search.yahoo.com/search/images?p={urllib.parse.quote(query)}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        # Yahoo stores image details in a data attribute
        imgs = soup.find_all('li', class_='ld')
        if imgs:
            for img in imgs:
                try:
                    data = json.loads(img.get('data'))
                    return data.get('iurl') # realistic direct image url
                except:
                    continue
    except Exception as e:
        print(f"Error fetching {query}: {e}")
    return None

import time

for comp in COMPONENTS:
    filename = comp.replace(" ", "_").replace("/", "_").replace("-", "_").lower() + ".png"
    filepath = os.path.join(STATIC_DIR, filename)
    if os.path.exists(filepath):
        print(f"[SKIP] {comp}")
        continue
        
    print(f"Searching for {comp} via Yahoo...")
    img_url = get_image_yahoo(comp + " network switch")
    if not img_url:
        img_url = get_image_yahoo(comp)

    if img_url:
        try:
            r = requests.get(img_url, headers=HEADERS, timeout=5)
            if r.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(r.content)
                print(f"[OK] Downloaded {comp} -> {img_url}")
            else:
                print(f"[WARN] Failed to download {img_url}")
        except Exception as e:
            print(f"[ERROR] Failed to download {img_url}: {e}")
    else:
        print(f"[FAIL] Could not find {comp}")
    time.sleep(1.0)
    
print("Done!")
