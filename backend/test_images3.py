from duckduckgo_search import DDGS
import json

try:
    with DDGS() as ddgs:
        results = list(ddgs.images("Aruba AP-515", max_results=1))
        print(results[0].get('image'))
except Exception as e:
     print(f"Error: {e}")
