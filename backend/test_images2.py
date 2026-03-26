import asyncio
import os
from api.services import PriceService, SizingService

async def test():
    # Test typical model
    img = await PriceService.fetch_image_url("Cisco Catalyst 9300")
    print(f"Cisco Catalyst 9300 - Image: {img}")
    
    img2 = await PriceService.fetch_image_url("Aruba AP-515")
    print(f"Aruba AP-515 - Image: {img2}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test())
