import requests
import json
from bs4 import BeautifulSoup

def attempt_url(url):
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=5)
        print(f"[{r.status_code}] {url[:80]}...")
        return r.status_code == 200
    except Exception as e:
        print(f"[ERROR] {url[:80]}: {e}")
        return False

# reliable domains test
test_urls = [
    "https://m.media-amazon.com/images/I/41K-sSjP-1L._AC_SX679_.jpg",
    "https://i.ebayimg.com/images/g/9XwAAOSw6vxgHkU1/s-l1600.jpg",
    "https://www.router-switch.com/media/catalog/product/cache/1/image/9df78eab33525d08d6e5fb8d27136e95/a/r/aruba-j9150d.jpg",
    "https://itprice.com/images/cisco/C9300-48P-A.jpg",
    "https://mcscom.co.uk/content/images/thumbs/0064366_aruba-j9150d-10gbase-sr-m-s-sfp-tr_550.jpeg",
    "https://www.hardware-corner.net/wp-content/uploads/2022/10/Cisco-Catalyst-9300.jpg"
]

for t in test_urls:
    attempt_url(t)
