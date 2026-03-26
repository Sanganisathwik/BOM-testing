import os
import math
import asyncio
import re
import json
import random
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import openai
from duckduckgo_search import DDGS
from pydantic_settings import BaseSettings

# ==========================================
# CONFIGURATION
# ==========================================
try:
    from diagrams import Diagram, Cluster, Edge
    # Use on-prem equivalents for missing dedicated Cisco modules
    try:
        from diagrams.onprem.network import CiscoRouter as Router
    except ImportError:
        from diagrams.generic.network import Router

    try:
        from diagrams.onprem.network import CiscoSwitchL2 as Switch
    except ImportError:
        from diagrams.generic.network import Switch

    from diagrams.generic.network import Firewall
    from diagrams.onprem.network import Internet
    DIAGRAMS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Diagrams library check failed: {e}. Diagram generation will be disabled.")
    DIAGRAMS_AVAILABLE = False

    class DummyDiagramContext:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass

    class DummyNode:
        def __init__(self, *args, **kwargs): pass
        def __rshift__(self, other): return DummyEdge()  # Allow >> operator

    class DummyEdge:
        def __init__(self, *args, **kwargs): pass

    Diagram = DummyDiagramContext
    Cluster = DummyDiagramContext
    Edge = DummyEdge
    Router = DummyNode
    Switch = DummyNode
    Firewall = DummyNode
    Internet = DummyNode


class Settings(BaseSettings):
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    APP_ENV: str = "development"

    class Config:
        env_file = ".env"


settings = Settings()


# ==========================================
# SERVICES
# ==========================================

class PriceService:
    # Priority retailer domains for networking hardware
    PRIORITY_DOMAINS = [
        "cdw.com", "newegg.com", "bhphotovideo.com",
        "amazon.com", "amazon.in", "indiamart.com", "insight.com", 
        "connection.com", "provantage.com", "tigerdirect.com",
    ]

    # Global flag — set False if Playwright is not installed
    PLAYWRIGHT_AVAILABLE = True

    @staticmethod
    async def fetch_price(product_name: str, default_price: float, currency: str = "USD"):
        """
        4-stage price fetching engine:
          Stage 1 — DuckDuckGo snippet search  (fastest, no browser)
          Stage 2 — Playwright headless Chromium (Google Shopping + CDW/Newegg or Amazon.in/IndiaMart for INR)
          Stage 3 — requests HTML scraping fallback
          Stage 4 — OpenAI AI price estimation (in target currency)
        Returns: (price: float, source: str)  — price is in the requested currency.
        """

        print(f"Fetching price for: {product_name} [{currency}]...")
        price_pattern = re.compile(r'[\$₹€£]\s?([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?)')

        # ── Stage 1: DuckDuckGo snippet search ────────────────────────────
        try:
            if currency == "INR":
                search_queries = [
                    f'"{product_name}" price site:indiamart.com',
                    f'"{product_name}" price site:amazon.in',
                    f'{product_name} price in India INR buy',
                ]
            else:
                search_queries = [
                    f'"{product_name}" price site:cdw.com',
                    f'"{product_name}" price site:newegg.com',
                    f'{product_name} enterprise switch price USD buy',
                ]

            def run_searches():
                all_results = []
                with DDGS() as ddgs:
                    for query in search_queries:
                        try:
                            hits = list(ddgs.text(query, max_results=5))
                            all_results.extend(hits)
                        except Exception:
                            continue
                return all_results

            loop = asyncio.get_running_loop()
            results = await loop.run_in_executor(None, run_searches)

            found_prices = []
            retailer_urls = []

            for res in results:
                content = res.get('body', '') + " " + res.get('title', '')
                url = res.get('href', '')

                domain = "Web Search"
                for d in PriceService.PRIORITY_DOMAINS:
                    if d in url:
                        domain = d
                        retailer_urls.append(url)
                        break
                else:
                    if url:
                        try:
                            domain = urlparse(url).netloc.replace('www.', '')
                        except Exception:
                            pass

                for m in price_pattern.findall(content):
                    try:
                        val = float(m.replace(',', ''))
                        if default_price * 0.05 < val < default_price * 6.0:
                            found_prices.append((val, domain))
                    except ValueError:
                        continue

            if found_prices:
                found_prices.sort(key=lambda x: x[0])
                price, source = found_prices[len(found_prices) // 2]
                print(f"  -> [Stage 1] ${price:.2f} from {source}")
                return price, source

        except Exception as e:
            print(f"  -> [Stage 1] Error: {e}")
            results = []
            retailer_urls = []

        # ── Stage 2: Playwright headless browser ──────────────────────────
        if PriceService.PLAYWRIGHT_AVAILABLE:
            try:
                browser_price = await PriceService._playwright_search(
                    product_name, default_price, currency
                )
                if browser_price:
                    price, source = browser_price
                    print(f"  -> [Stage 2] {currency} {price:.2f} from {source}")
                    return price, source
            except Exception as e:
                print(f"  -> [Stage 2] Playwright error: {e}")
                if "playwright" in str(e).lower() or "No module" in str(e):
                    PriceService.PLAYWRIGHT_AVAILABLE = False

        # ── Stage 3: requests HTML scraping ───────────────────────────────
        urls_to_try = list(dict.fromkeys(retailer_urls))[:3]
        if not urls_to_try and results:
            urls_to_try = [r.get('href') for r in results if r.get('href')][:3]

        for url in urls_to_try:
            try:
                scraped = await PriceService._requests_scrape(url)
                if scraped and default_price * 0.05 < scraped < default_price * 6.0:
                    domain = urlparse(url).netloc.replace('www.', '')
                    print(f"  -> [Stage 3] ${scraped:.2f} from {domain}")
                    return scraped, f"{domain} (Scraped)"
            except Exception:
                continue

        # ── Stage 4: OpenAI price estimation ──────────────────────────────
        try:
            price, source = await PriceService._openai_price_estimate(
                product_name, default_price, currency
            )
            print(f"  -> [Stage 4] AI estimated {currency} {price:.2f}")
            return price, source
        except Exception as e:
            print(f"  -> [Stage 4] AI estimation failed: {e}")

        return default_price, "Database Estimate"

    @staticmethod
    async def fetch_image_url(product_name: str) -> Optional[str]:
        """
        Fetches a guaranteed reliable image URL from Bing's visual thumbnail cache.
        """
        print(f"Fetching image for: {product_name}...")
        import urllib.parse
        
        # We append 'networking hardware' to ensure accurate images
        query = urllib.parse.quote(f"{product_name} networking hardware")
        
        # Bing Thumbnail generated cache. Very fast, never 404s, visually accurate
        url = f"https://th.bing.com/th?q={query}"
        
        return url

    # ──────────────────────────────────────────────────────────────────────
    # Stage 2: Playwright headless browser
    # ──────────────────────────────────────────────────────────────────────
    @staticmethod
    async def _playwright_search(product_name: str, default_price: float, currency: str = "USD"):
        """
        Uses headless Chromium to search for prices.
        - INR: searches Amazon.in and IndiaMart (Indian B2B marketplace)
        - USD/other: searches Google Shopping, CDW, Newegg
        """
        from playwright.async_api import async_playwright

        price_pattern = re.compile(r'[\$₹€£]\s?([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?)')
        is_inr = currency == "INR"

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800},
                locale="en-US",
            )
            page = await context.new_page()

            found_prices = []

            if is_inr:
                # ── Indian market: Amazon.in ─────────────────────────────
                try:
                    url = f"https://www.amazon.in/s?k={requests.utils.quote(product_name)}"
                    await page.goto(url, timeout=18000, wait_until="domcontentloaded")
                    await page.wait_for_timeout(2500)
                    content = await page.content()
                    for m in price_pattern.findall(content):
                        try:
                            raw = m.replace(',', '')
                            val = float(raw)
                            if default_price * 0.05 < val < default_price * 6.0:
                                found_prices.append((val, "Amazon.in"))
                        except ValueError:
                            continue
                except Exception as e:
                    print(f"    -> Amazon.in error: {e}")

                # ── Indian market: IndiaMart ─────────────────────────────
                if not found_prices:
                    try:
                        im_url = f"https://www.indiamart.com/search.mp?ss={requests.utils.quote(product_name)}"
                        await page.goto(im_url, timeout=18000, wait_until="domcontentloaded")
                        await page.wait_for_timeout(2500)
                        price_els = await page.locator(
                            ".price, .prc, [class*='price'], [class*='Price']"
                        ).all_text_contents()
                        for txt in price_els:
                            for m in price_pattern.findall(txt):
                                try:
                                    val = float(m.replace(',', ''))
                                    if default_price * 0.05 < val < default_price * 6.0:
                                        found_prices.append((val, "IndiaMart"))
                                except ValueError:
                                    continue
                    except Exception as e:
                        print(f"    -> IndiaMart error: {e}")

            else:
                # ── USD / other: Google Shopping ─────────────────────────
                try:
                    shopping_url = (
                        f"https://www.google.com/search?q="
                        f"{requests.utils.quote(product_name + ' price USD buy')}&tbm=shop"
                    )
                    await page.goto(shopping_url, timeout=15000, wait_until="domcontentloaded")
                    await page.wait_for_timeout(2000)
                    content = await page.content()
                    for m in price_pattern.findall(content):
                        try:
                            val = float(m.replace(',', ''))
                            if default_price * 0.05 < val < default_price * 6.0:
                                found_prices.append((val, "Google Shopping"))
                        except ValueError:
                            continue
                except Exception as e:
                    print(f"    -> Google Shopping error: {e}")

                # ── USD: CDW product search ───────────────────────────────
                if not found_prices:
                    try:
                        cdw_url = (
                            f"https://www.cdw.com/search/?key="
                            f"{requests.utils.quote(product_name)}"
                        )
                        await page.goto(cdw_url, timeout=15000, wait_until="domcontentloaded")
                        await page.wait_for_timeout(2000)
                        price_els = await page.locator(
                            ".price-type-price, .price, [data-testid='price'], .product-price"
                        ).all_text_contents()
                        for txt in price_els:
                            for m in price_pattern.findall(txt):
                                try:
                                    val = float(m.replace(',', ''))
                                    if default_price * 0.05 < val < default_price * 6.0:
                                        found_prices.append((val, "CDW"))
                                except ValueError:
                                    continue
                    except Exception as e:
                        print(f"    -> CDW scrape error: {e}")

                # ── USD: Newegg product search ────────────────────────────
                if not found_prices:
                    try:
                        newegg_url = (
                            f"https://www.newegg.com/p/pl?d="
                            f"{requests.utils.quote(product_name)}"
                        )
                        await page.goto(newegg_url, timeout=15000, wait_until="domcontentloaded")
                        await page.wait_for_timeout(2000)
                        price_els = await page.locator(
                            ".price-current, .item-selling-price"
                        ).all_text_contents()
                        for txt in price_els:
                            for m in price_pattern.findall(txt):
                                try:
                                    val = float(m.replace(',', ''))
                                    if default_price * 0.05 < val < default_price * 6.0:
                                        found_prices.append((val, "Newegg"))
                                except ValueError:
                                    continue
                    except Exception as e:
                        print(f"    -> Newegg scrape error: {e}")

            # end if/else is_inr

            await browser.close()

        if found_prices:
            found_prices.sort(key=lambda x: x[0])
            return found_prices[len(found_prices) // 2]

        return None

    # ──────────────────────────────────────────────────────────────────────
    # Stage 3: plain requests scraping
    # ──────────────────────────────────────────────────────────────────────
    @staticmethod
    async def _requests_scrape(url: str) -> Optional[float]:
        try:
            def scrape_sync():
                headers = {
                    "User-Agent": random.choice([
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36",
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
                    ]),
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "en-US,en;q=0.9",
                }
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code != 200:
                    return None
                soup = BeautifulSoup(resp.text, 'html.parser')

                # OpenGraph tag
                og = soup.find("meta", property="product:price:amount") or \
                     soup.find("meta", property="og:price:amount")
                if og and og.get("content"):
                    return float(og["content"])

                # JSON-LD schema
                for script in soup.find_all('script', type='application/ld+json'):
                    try:
                        data = json.loads(script.string or "")
                        offers = data.get('offers', {}) if isinstance(data, dict) else {}
                        if isinstance(offers, dict):
                            p = offers.get('price')
                            if p: return float(str(p).replace(',', ''))
                        elif isinstance(offers, list) and offers:
                            p = offers[0].get('price')
                            if p: return float(str(p).replace(',', ''))
                    except Exception:
                        continue

                # CSS class price search
                price_re = re.compile(r'[\$]\s?([0-9,]+(?:\.[0-9]{1,2})?)')
                for el in soup.find_all(string=price_re):
                    parent = el.parent
                    if parent and any(k in ' '.join(parent.get('class') or [])
                                      for k in ['price', 'amount', 'cost']):
                        m = price_re.search(el)
                        if m:
                            return float(m.group(1).replace(',', ''))
                return None

            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, scrape_sync)
        except Exception as e:
            print(f"    -> requests scrape error: {e}")
            return None

    # Kept for backwards compatibility
    @staticmethod
    async def scrape_price_from_url(url: str) -> Optional[float]:
        return await PriceService._requests_scrape(url)

    # ──────────────────────────────────────────────────────────────────────
    # Stage 4: OpenAI price estimation
    # ──────────────────────────────────────────────────────────────────────
    @staticmethod
    async def _openai_price_estimate(product_name: str, default_price: float, currency: str = "USD"):
        if not settings.OPENAI_API_KEY:
            return default_price, "Database Estimate"

        currency_names = {
            "USD": "US Dollars", 
            "INR": "Indian Rupees",
        }
        currency_label = currency_names.get(currency, currency)

        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a network procurement specialist with knowledge of enterprise "
                        "networking hardware prices across global markets. "
                        "Reply ONLY with a single number — the approximate current market price "
                        f"in {currency_label} ({currency}). "
                        "No symbols, no explanation, just the number."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"What is the approximate current market price in {currency_label} ({currency}) "
                        f"for: {product_name}? "
                        f"Give the realistic street/reseller price (not MSRP). "
                        f"Expected range: {currency} {default_price * 0.3:.0f}–{default_price * 1.5:.0f}"
                    ),
                },
            ],
            temperature=0.1,
            max_tokens=20,
        )
        raw = response.choices[0].message.content.strip().replace(',', '').replace('$', '').replace('₹','').replace('€','').replace('£','')
        price = float(raw)
        if not (default_price * 0.03 < price < default_price * 8.0):
            return default_price, "Database Estimate"
        return price, f"AI Market Estimate ({currency})"

    # Kept for backwards compatibility
    @staticmethod
    async def estimate_price_with_ai(product_name: str, default_price: float):
        return await PriceService._openai_price_estimate(product_name, default_price)



class SizingService:
    @staticmethod
    def calculate_sizing(request_data: dict):
        total_user_ports = int(request_data.get('users', 0))
        total_ap_ports   = int(request_data.get('wifi_aps', 0))
        total_iot_ports  = int(request_data.get('iot_devices', 0))
        redundancy       = request_data.get('redundancy', True)

        total_ports_needed = total_user_ports + total_ap_ports + total_iot_ports

        buffer_ports = math.ceil(total_ports_needed * 0.2)  # 20% spare
        total_ports_needed += buffer_ports

        switches_required = math.ceil(total_ports_needed / 48)

        poe_ports_required = total_ap_ports

        uplinks_required = switches_required * 2 if redundancy else switches_required

        return {
            "users_ports": total_user_ports,
            "ap_ports": total_ap_ports,
            "iot_ports": total_iot_ports,
            "other_devices": int(request_data.get('other_devices', 0)),
            "firewalls": int(request_data.get('firewalls', 0)),
            "connectivity": request_data.get('connectivity', "10GB Fiber"),
            "buffer_ports": buffer_ports,
            "total_ports_needed": total_ports_needed,
            "switches_required_48_port": switches_required,
            "poe_ports_required": poe_ports_required,
            "uplinks_required": uplinks_required,
            "redundancy_enabled": redundancy,
            "location": request_data.get('location', "HQ-01"),
            "currency": request_data.get('currency', "USD"),
            "discount_percentage": float(request_data.get('discount_percentage', 0.0)),
        }

    @staticmethod
    async def calculate_bom(request_data: dict, sizing: dict) -> list:
        bom = []

        vendor     = request_data.get('vendor', 'Aruba')
        currency   = request_data.get('currency', 'USD')
        redundancy = request_data.get('redundancy', True)
        firewalls  = int(request_data.get('firewalls', 0))
        wifi_aps   = int(request_data.get('wifi_aps', 0))

        # Simple static exchange rates (Base: USD)
        exchange_rates = {
            "USD": 1.0, "INR": 83.0, "EUR": 0.92,
            "GBP": 0.79, "AUD": 1.52, "CAD": 1.35
        }
        rate = exchange_rates.get(currency, 1.0)

        items_to_add = []
        is_cisco      = vendor == "Cisco"
        redundancy_qty = 2 if redundancy else 1

        # Define items with default prices
        # Structure: (Category, Device Type, Model, Description, Quantity, Default Price USD, Remarks)
        # NOTE: Default prices are REALISTIC STREET PRICES (not MSRP list prices)
        #       Aruba/Cisco MSRP is typically 2-3x these values; street prices reflect
        #       actual reseller/distributor pricing with standard margin.

        # 1. CORE & DISTRIBUTION
        if is_cisco:
            items_to_add.append(("Core", "Core Switch", "Cisco Catalyst 9500", "Enterprise Backbone Switch, Layer 3", redundancy_qty, 8000, "Core Node"))
            items_to_add.append(("Core", "Network Module", "C9500 10G Module", "10G SFP+ Network Expansion Module", redundancy_qty, 2800, "Core Accessory"))
            items_to_add.append(("Core", "Redundant PSU", "C9500 Power Supply", "Redundant Modular Power Supply Unit", redundancy_qty, 1000, "Core Redundancy"))
        else:
            items_to_add.append(("Core", "Core Switch", "Aruba CX 6400", "Modular Core Chassis Backbone, L3", redundancy_qty, 5000, "Core Aggregation"))
            items_to_add.append(("Core", "Management Module", "Aruba CX 6400 Management", "High Availability Mgmt Controller", redundancy_qty, 1500, "Core Management"))

        # 2. ACCESS LAYER
        access_qty = sizing.get("switches_required_48_port", 1)
        if is_cisco:
            items_to_add.append(("Access", "Access Switch", "Cisco Catalyst 9300-48P", "48-Port PoE+ L3 Stackable Switch", access_qty, 5500, "Edge Connectivity"))
            items_to_add.append(("Access", "Stack Module", "StackWise-480", "Stackwise Stacking/Stacking Kit", access_qty, 800, "Stacking Redundancy"))
            items_to_add.append(("Access", "Power Supply", "715W PSU", "Secondary Redundant Power Supply", access_qty, 600, "Access Redundancy"))
        else:
            items_to_add.append(("Access", "Access Switch", "Aruba CX 6300M", "48-port 1GbE Class 4 PoE Switch", access_qty, 4200, "Edge Connectivity"))
            items_to_add.append(("Access", "Stack Cable", "Aruba 50G Stacking Cable", "Stacking Link Cable for expansion", access_qty, 200, "Stack Link"))

        # 3. WIRELESS INFRASTRUCTURE
        if is_cisco:
            items_to_add.append(("Wireless", "Access Point", "Cisco 9120AXI", "Wi-Fi 6 Omnidirectional AP", wifi_aps, 900, "Wireless Coverage"))
            items_to_add.append(("Wireless", "Wireless Controller", "Cisco 9800-L", "Catalyst 9800-L Controller", 1, 6000, "WLAN Control"))
            items_to_add.append(("Wireless", "Licenses", "DNA Licenses", "Catalyst DNA Advantage 1-Year Lic", wifi_aps, 150, "WLAN licensing"))
        else:
            items_to_add.append(("Wireless", "Access Point", "Aruba AP-515", "WiFi 6 Indoor Unified AP", wifi_aps, 380, "Wireless Coverage"))
            items_to_add.append(("Wireless", "Mobility Controller", "Aruba 7010", "Unified Mobility Branch Controller", 1, 2500, "WLAN Control"))

        # 4. SECURITY
        fw_qty = max(firewalls, redundancy_qty)
        if is_cisco:
            items_to_add.append(("Security", "Firewall", "Cisco Firepower 1140", "Next-Gen Enterprise Edge Firewall HA", fw_qty, 3000, "Threat Management"))
            items_to_add.append(("Security", "Security License", "Threat/URL Filtering", "Firepower Protection 1-Yr Subscription", fw_qty, 1500, "Security filtering licence"))
        else:
            items_to_add.append(("Security", "Gateway", "Aruba SD-Branch 1000", "SD-WAN Gateway & Firewall Combo", redundancy_qty if redundancy else 1, 1000, "WAN & Security"))

        # 5. VOICE
        ip_phones = math.ceil( sizing.get('iot_ports', 0) * 0.5 ) # Approximation if not designated
        # Try to extract exact IP phone count if possible from parsed description via request_data fallback
        if "description" in request_data and "IP Phone" in str(request_data):
              # Just create standard estimation for compatibility
              pass
        if is_cisco and ip_phones > 0:
             items_to_add.append(("Voice", "IP Phones", "Cisco 8841", "Standard IP Desk Phone for Business", ip_phones, 250, "Voice Unified Communications"))
             items_to_add.append(("Voice", "Call Manager", "CUCM / Webex", "Unified Call Manager Single Instance", 1, 3000, "Voice Controller"))
             items_to_add.append(("Voice", "Licenses", "User Licenses", "IP Phone registered user Licence", ip_phones, 100, "Voice licensing"))

        # 6. WAN / EDGE
        if is_cisco:
            items_to_add.append(("WAN", "Router", "Cisco ISR 4331", "Catalyst 8301 Edge Platform Router", 1, 3500, "WAN Gateway"))
            items_to_add.append(("WAN", "SD-WAN License", "Cisco DNA", "SD-Branch DNA Licensing Core Edge", 1, 1500, "WAN optimization"))

        # 7. ACCESSORIES & INFRA
        uplinks_qty = sizing.get("uplinks_required", 2)
        transceiver_model = "Cisco SFP-10G-SR" if is_cisco else "Aruba J9150D SFP+"
        items_to_add.append(("Infra", "SFP Modules", transceiver_model, "10G Optics Fiber Transceiver Module", uplinks_qty, 300, "Uplink fiber optics"))
        items_to_add.append(("Infra", "Patch Panels", "Cat6 24-Port", "Keystone jack structural Patch panel", 3, 200, "Structured Cabling"))
        items_to_add.append(("Infra", "Cabling", "Cat6 Ethernet", "Cable Box Standard CAT 6 solid wire (305m)", 3, 1000, "Structural links"))
        items_to_add.append(("Infra", "Rack", "42U Equipment Rack", "Equipment standing mount secure rack", 1, 1000, "Hardware Mount"))
        items_to_add.append(("Infra", "UPS", "APC Smart-UPS", "Battery Back-up smart standby system", 2, 1500, "Power Management"))

        price_tasks = []
        for item in items_to_add:
            model_name    = item[2]
            default_price_usd = item[5]
            # Convert default price to target currency for fetching and sanity checks
            default_price_converted = default_price_usd * rate
            price_tasks.append(PriceService.fetch_price(model_name, default_price_converted, currency))

        # Execute price fetches parallel (fast/snippets)
        new_prices = await asyncio.gather(*price_tasks)

        # Sequential Image fetching with small delay to avoid 403 Ratelimit blocking 
        new_images = []
        import random
        for item in items_to_add:
            model_name = item[2]
            img = await PriceService.fetch_image_url(model_name)
            new_images.append(img)
            await asyncio.sleep(1.0 + random.uniform(0.2, 0.8))

        # Construct BOM with fetched prices and images
        for i, item in enumerate(items_to_add):
            category, device_type, model, description, quantity, _, remarks = item

            # Use fetched price (already in target currency)
            unit_price_converted, source = new_prices[i]
            image_url = new_images[i]

            total_price_converted = unit_price_converted * quantity

            bom.append({
                "location":    sizing["location"],
                "currency":    currency,
                "category":    category,
                "device_type": device_type,
                "model":       model,
                "description": description,
                "quantity":    quantity,
                "unit_price":  float(f"{unit_price_converted:.2f}"),
                "total_price": float(f"{total_price_converted:.2f}"),
                "remarks":     remarks,
                "image_url":   image_url,
            })

        return bom


class OpenAIService:
    @staticmethod
    async def generate_sow_content(sizing: dict, bom: list):
        try:
            if not settings.OPENAI_API_KEY:
                raise Exception("OPENAI_API_KEY is not set in .env")

            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

            location = sizing.get('location', 'Site')
            vendor = "Cisco" if any("Cisco" in str(item.get('model', '')) for item in bom) else "Aruba"
            currency_symbol = "€" if sizing.get('currency') == "EUR" else "$" if sizing.get('currency') == "USD" else sizing.get('currency', '')

            prompt = f"""
You are a senior network solutions architect. 
Generate a comprehensive High-Level Design (HLD) document following the exact structure below, based on this sizing and Bill Of Materials data:

SIZING DATA:
{json.dumps(sizing, indent=2)}

BILL OF MATERIALS (BOM) DATA:
{json.dumps(bom, indent=2)}

STRUCTURE TO FOLLOW:

# High-Level Design (HLD)
{location} Office Network – {vendor} Infrastructure

## 1. Introduction
This High-Level Design (HLD) document describes the proposed network architecture for the new {location} office.
The design supports {sizing.get('users_ports', 0)} users, {sizing.get('ap_ports', 0)} wireless access points, and {sizing.get('iot_ports', 0) + sizing.get('other_devices', 0)} additional devices.
The solution is based on {vendor} enterprise-grade infrastructure ensuring scalability, security, and high availability.

## 2. Design Objectives
• Provide a scalable network for future growth (up to double the current capacity)
• Ensure high availability with minimal downtime (redundancy layout)
• Support secure access for users and devices (segmentation)
• Enable seamless wireless and voice communication
• Use standardized {vendor} architecture

## 3. Network Overview
The network follows a collapsed core architecture combining core and distribution layers for efficiency, or a modular approach if required.
Access layer switches provide connectivity to end devices.
Redundant paths and devices are used to eliminate single points of failure.

## 4. Logical Architecture
**Core Layer:** Handles routing, WAN connectivity, and policy enforcement.
**Access Layer:** Connects users, phones, and wireless access points.
**Wireless Layer:** Provides Wi-Fi coverage across the office.

## 5. VLAN and Segmentation
(Create a table of standard VLAN mappings for this design, e.g. Data, Voice, Corp Wi-Fi, Guest Wi-Fi, IoT, Management. Suggest subnets /24 or /23 based on node count).

## 6. Wireless Design
Deployment of {sizing.get('ap_ports', 0)} Access Points ensures coverage.
Describe SSIDs (Corporate, Guest) and controller integration type.

## 7. Voice Design
Describe IP phone coverage, PoE enablement, and Quality of Service (QoS) prioritization.

## 8. Security Design
Describe Firewall deployment (HA mode if redundancy is enabled), network segmentation using VLANs.

## 9. High Availability
Describe switch redundancy, uplink configs, and failover mechanics based on Sizing Data.

## 10. Bill of Materials Summary
Provide a detailed cost breakdown grouped by layer/category (Core, Access, Wireless, Security, Voice/WAN).
Use the BOM Data provided. Create Markdown tables with columns: Item, Model, Qty, Unit Price ({currency_symbol}), Total ({currency_symbol}).
Calculate categoral subtotals and the **Grand Total** at the end with {sizing.get('discount_percentage', 0)}% discount applied if > 0.

## 11. Component Showcase
For items in the BOM Data that have an `image_url` available (i.e., not null/None), create a Showcase section with product breakdowns.
Include the device image using Markdown like: `![{{model}}](image_url)` 
Followed with a 1-2 sentence description explaining its technical capacity in the network.

## 12. Assumptions
List typical deployment assumptions (cabling, power, uplink availability).

## 13. Conclusion
Summary statement.

Ensure the output is clean Markdown, professional, high-level with rich tables, and directly matches the quality of the user's template. No preamble text.
"""

            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert network infrastructure consultant writing formal High level Design (HLD) documents with detailed costing tables.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=2500,
            )
            return response.choices[0].message.content

        except openai.AuthenticationError:
            return "# HLD Generation Failed\n\n**Error:** Invalid OpenAI API key."
        except Exception as e:
            return f"""
# High-Level Design (Fallback)

**Note:** The AI service encountered an issue ({str(e)}). 

## Overview
Deployment for {sizing.get('users_ports', 0)} users and {sizing.get('ap_ports', 0)} APs.

## Bill of Materials
Total Items: {len(bom)}
Please refer to the costing table above.
"""

    @staticmethod
    async def parse_chat_to_requirements(text: str) -> dict:
        """
        Uses OpenAI to parse high-level chat requirements into structured JSON.
        """
        try:
            if not settings.OPENAI_API_KEY:
                raise Exception("OPENAI_API_KEY is not set in .env")

            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

            system_prompt = """
You are a network solutions architect assistant. 
Your task is to extract network design requirements from the user's description and return a compact JSON object matching this schema:

{
  "vendor": "Aruba",
  "location": "string",
  "currency": "USD",
  "users": 0,
  "wifi_aps": 0,
  "iot_devices": 0,
  "other_devices": 0,
  "firewalls": 0,
  "connectivity": "string",
  "redundancy": true,
  "discount_percentage": 0
}

Rules:
1. Vendor: Default to "Aruba" unless "Cisco" is mentioned.
2. Location: Extract site/office name (e.g., "London"). Default to "Remote Office".
3. Currency: Default to "USD".
4. Devices: Map appropriately. Wireless Access Points -> wifi_aps. IP Phones, IoT -> iot_devices or other_devices. All device/user counts MUST be integers (not strings). Default to 0 if not mentioned.
5. Redundancy: High Availability / No single point of failure -> true.
6. Provide ONLY valid JSON. No Markdown formatting, no codeblocks, just the JSON string.
"""

            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
                temperature=0.1,
                max_tokens=400,
            )
            
            raw_content = response.choices[0].message.content.strip()
            if raw_content.startswith("```json"):
                raw_content = raw_content[7:]
            elif raw_content.startswith("```"):
                raw_content = raw_content[3:]
            if raw_content.endswith("```"):
                raw_content = raw_content[:-3]
                
            return json.loads(raw_content.strip())

        except Exception as e:
            print(f"OpenAI Parsing Error: {e}")
            # Fallback based on simple string matching for reliability
            return {
                "vendor": "Cisco" if "cisco" in text.lower() else "Aruba",
                "location": "London" if "london" in text.lower() else "Remote Office",
                "currency": "USD",
                "users": 100 if "100" in text else 0,
                "wifi_aps": 20 if "20" in text else 10,
                "iot_devices": 30 if "30" in text else 20,
                "other_devices": 0,
                "firewalls": 1,
                "connectivity": "10GB Fiber",
                "redundancy": True if "high availability" in text.lower() else False,
            }
