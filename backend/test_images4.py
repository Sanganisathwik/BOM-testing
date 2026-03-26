from duckduckgo_search import DDGS
import time
import random

items = ["Cisco Catalyst 9300", "Aruba CX 6400", "Aruba AP-515", "Cisco 9120AXI"]

for product in items:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(product, max_results=1))
            if results:
                print(f"{product}: {results[0].get('image')}")
            else:
                 print(f"{product}: No image")
    except Exception as e:
         print(f"{product}: Error: {e}")
    
    # Sleep between scrapes
    sleep_time = 1 + random.uniform(0.5, 1.5)
    print(f"Sleeping {sleep_time:.2f}s...")
    time.sleep(sleep_time)
