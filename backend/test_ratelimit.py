import asyncio
from duckduckgo_search import DDGS
import random
import time

async def fetch_image(product_name):
    print(f"Fetching image for: {product_name}...")
    try:
        def run_search():
            with DDGS() as ddgs:
                hits = list(ddgs.images(product_name, max_results=1))
                if hits:
                    return hits[0].get('image')
            return None

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, run_search)
    except Exception as e:
        print(f"  -> Image fetch error for {product_name}: {e}")
        return None

async def main():
    items = ["Aruba CX 6400", "Aruba CX 6300M", "Aruba AP-515", "Aruba SD-Branch 1000", "Aruba 7010", "Catalyst 9300", "Cisco OSPF", "Fortinet Firewall"]
    for item in items:
        img = await fetch_image(item)
        print(f"{item} -> {img}")
        await asyncio.sleep(1.0 + random.uniform(0.2, 0.8))

asyncio.run(main())
