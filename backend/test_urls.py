import requests

urls = [
    "https://www.arubanetworks.com/assets/images/products/6400-series/aruba-6400-series-angle.png",
    "https://www.swsg-inc.com/media/catalog/product/cache/1/image/1200x/040ec09b1e35df139433887a97daa66f/r/0/r0x31a.png",
    "https://www.cisco.com/c/dam/en/us/products/switches/catalyst-9500-series-switches/catalyst-9500-switch-family.png",
]

for url in urls:
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        print(f"[{r.status_code}] {url}")
    except Exception as e:
        print(f"[ERROR] {url}: {e}")
