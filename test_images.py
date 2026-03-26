from duckduckgo_search import DDGS
import json

try:
    with DDGS() as ddgs:
        results = list(ddgs.images("Cisco Catalyst 9300", max_results=2))
        print(json.dumps(results, indent=2))
except Exception as e:
    print(f"Error: {e}")
