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

        # 1. CORE
        if is_cisco:
            items_to_add.append(("Core", "Core Switch", "Cisco Catalyst 9500", "Redundant Core Switch, L3, 10G/40G", redundancy_qty, 4500, "Core Aggregation"))
        else:
            items_to_add.append(("Core", "Core Switch", "Aruba CX 6400", "Modular Core Switch, High Availability", redundancy_qty, 5000, "Core Aggregation"))

        # 2. ACCESS
        if is_cisco:
            items_to_add.append(("Access", "Access Switch", "Cisco Catalyst 9200", "48-Port PoE+, Layer 2", sizing["switches_required_48_port"], 850, "User/Device Connectivity"))
        else:
            items_to_add.append(("Access", "Access Switch", "Aruba CX 6300M", "48-port 1GbE Class 4 PoE and 4-port SFP56", sizing["switches_required_48_port"], 1200, "User/Device Connectivity"))

        # 3. WIRELESS
        if is_cisco:
            items_to_add.append(("Wireless", "Access Point", "Cisco WiFi 6", "High Density WiFi 6 Indoor AP", wifi_aps, 500, "Wireless Coverage"))
        else:
            items_to_add.append(("Wireless", "Access Point", "Aruba AP-515", "WiFi 6 Indoor Unified AP", wifi_aps, 380, "Wireless Coverage"))

        # 4. ROUTING & SECURITY
        if is_cisco:
            items_to_add.append(("Routing", "Edge Router", "Cisco ISR 4000", "Integrated Services Router (SD-WAN Ready)", redundancy_qty, 1500, "WAN Edge"))
            if firewalls > 0:
                items_to_add.append(("Security", "Firewall", "Cisco Firepower 1010", "Next-Gen Firewall, HA Capable", max(firewalls, redundancy_qty), 900, "Network Security"))
        else:
            items_to_add.append(("Routing", "Gateway", "Aruba SD-Branch 1000", "SD-WAN Gateway & Firewall Combo", redundancy_qty, 1000, "WAN & Security"))
            if firewalls > redundancy_qty:
                items_to_add.append(("Security", "Extra Firewall", "Aruba SD-Branch 1000", "Additional Security Gateway", firewalls - redundancy_qty, 1000, "Internal Segmentation"))

        # 5. MANAGEMENT
        if is_cisco:
            items_to_add.append(("Management", "NAC Server", "Cisco ISE Virtual", "Identity Services Engine License", 1, 2500, "Policy & Auth"))
            items_to_add.append(("Infra", "UPS", "APC Smart-UPS 10kVA", "Datacenter Power Protection", 1, 3500, "Power Backup"))
        else:
            items_to_add.append(("Management", "NAC Server", "Aruba ClearPass", "Access Control Policy Manager", 1, 2800, "Policy & Auth"))
            items_to_add.append(("Infra", "UPS", "APC Smart-UPS 5000", "Rack Mount UPS", 1, 2000, "Power Backup"))

        # 6. CONNECTIVITY
        if "Fiber" in sizing["connectivity"]:
            transceiver_model = "Cisco SFP-10G-LR" if is_cisco else "HPE/Aruba J9151E SFP+"
            items_to_add.append(("Infra", "Transceiver", transceiver_model, "10G SFP+ LC LR Transceiver", sizing["uplinks_required"], 120, "Uplink Connectivity"))

        tasks = []
        for item in items_to_add:
            model_name    = item[2]
            default_price_usd = item[5]
            # Convert default price to target currency for fetching and sanity checks
            default_price_converted = default_price_usd * rate
            tasks.append(PriceService.fetch_price(model_name, default_price_converted, currency))

        # Execute all fetches
        new_prices = await asyncio.gather(*tasks)

        # Construct BOM with fetched prices
        for i, item in enumerate(items_to_add):
            category, device_type, model, description, quantity, _, remarks = item

            # Use fetched price (already in target currency)
            unit_price_converted, source = new_prices[i]

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
            })

        return bom


class OpenAIService:
    @staticmethod
    async def generate_sow_content(sizing: dict):
        try:
            if not settings.OPENAI_API_KEY:
                raise Exception("OPENAI_API_KEY is not set in .env")

            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

            prompt = f"""
You are a network engineer.

Generate a short professional SOM/SOW summary based on this sizing data:

{json.dumps(sizing, indent=2)}

Include:
1. Overview
2. Hardware Summary
3. Assumptions
4. Deliverables
5. Financial Summary (include total estimate with {sizing.get('discount_percentage', 0)}% discount applied)
Keep it concise.
"""
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert network infrastructure consultant writing formal Statements of Work.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=1500,
            )
            return response.choices[0].message.content

        except openai.AuthenticationError:
            print("OpenAI API Error: Invalid API key.")
            return "# SOW Generation Failed\n\n**Error:** Invalid OpenAI API key. Please set a valid `OPENAI_API_KEY` in your `.env` file."
        except openai.RateLimitError:
            print("OpenAI API Error: Rate limit reached.")
            return "# SOW Generation Failed\n\n**Error:** OpenAI rate limit reached. Please try again shortly."
        except Exception as e:
            print(f"OpenAI API Error (Handled): {e}")
            # Fallback content
            return f"""
# Statement of Work (Fallback Generated)

**Note:** The AI service is currently unavailable ({str(e)}). This is a designated placeholder based on your sizing inputs.

## Overview
This project involves the deployment of a robust network infrastructure for {sizing.get('users_ports', 0)} users, {sizing.get('ap_ports', 0)} WiFi Access Points, and {sizing.get('iot_ports', 0)} IoT devices.

## Hardware Summary
- **Switches:** {sizing.get('switches_required_48_port', 0)} x 48-Port Switches
- **Uplinks:** {sizing.get('uplinks_required', 0)} Uplink Connections
- **PoE Requirements:** {sizing.get('poe_ports_required', 0)} PoE Ports for APs

## Assumptions
- Standard office environment deployment.
- Cabling infrastructure is already in place or quoted separately.
- Power and cooling in the MDF/IDF are sufficient.

## Deliverables
1. Installation and configuration of network switches.
2. Deployment and tuning of {sizing.get('ap_ports', 0)} WiFi Access Points.
3. Network segmentation for IoT devices.
4. Redundancy configuration and failover testing.
5. Final documentation and handover.
"""
